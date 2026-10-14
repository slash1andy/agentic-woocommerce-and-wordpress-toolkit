"""Contract tests for scripts/evaluate.py, an eval-packet preparer and collector.

The runner never launches models, picks fallbacks, fetches auth, or judges. These tests pin the
packet contract: prepare(candidate, out, settings=None) -> manifest dict, and
collect(out, records, grades=None, *, manifest_sha256) -> aggregate dict, also written to
out/results.json. manifest_sha256 is the prepare-time SHA, retained outside the packet.
Records live at records/<scenario>/<arm>.json; grades at grades/<scenario>/<arm>.json.
"complete" is coverage only; per-row acceptance is separate and unresolved without a grade.
"""

import contextlib
import copy
import hashlib
import io
import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARMS = ("treatment", "control")


def load_module():
    spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts/evaluate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(directory: Path) -> dict:
    return {str(p.relative_to(directory)): sha(p) for p in sorted(directory.rglob("*")) if p.is_file()}


def good_record(scenario: dict, arm: dict) -> dict:
    files = inventory(Path(arm["workspace"]))
    turn = {
        "session_id": "s-" + scenario["id"],
        "is_error": False,
        "terminal_reason": "completed",
        "permission_denials": [],
        "modelUsage": {"pinned-model": {"inputTokens": 1, "outputTokens": 1}},
        "result": "text",
    }
    record = {"initial": turn, "workspace_after_initial": files, "workspace_final": files}
    if scenario["multi_turn"]:
        record["approval"] = {"session_id": turn["session_id"], "approved": True}
        record["resumed"] = copy.deepcopy(turn)
    return record


class EvaluationPacketTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev = load_module()

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.out = self.tmp / "packet"
        self.manifest = self.ev.prepare(ROOT, self.out, {"tools": "Read", "effort": "high", "budget": 5})
        self.pin = sha(self.out / "manifest.json")
        self.records = self.tmp / "records"
        self.scenarios = {s["id"]: s for s in self.manifest["scenarios"]}
        for sid, scenario in self.scenarios.items():
            for name in ARMS:
                self.write_record(sid, name, good_record(scenario, scenario["arms"][name]))

    def write_record(self, sid, arm, record):
        path = self.records / sid / f"{arm}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record), encoding="utf-8")

    def collect(self, grades=None):
        return self.ev.collect(self.out, self.records, grades, manifest_sha256=self.pin)

    def status(self, sid, arm, result=None):
        result = result or self.collect()
        row = next(r for r in result["results"] if r["scenario"] == sid and r["arm"] == arm)
        return row["status"]

    def mutate(self, sid, arm, fn):
        record = good_record(self.scenarios[sid], self.scenarios[sid]["arms"][arm])
        fn(record)
        self.write_record(sid, arm, record)

    def test_prepare_covers_fifteen_paired_scenarios_with_multi_turn_classes(self):
        self.assertEqual(len(self.scenarios), 15)
        self.assertEqual({sid for sid, s in self.scenarios.items() if s["multi_turn"]}, {"dev-2", "dev-3"})
        for scenario in self.scenarios.values():
            self.assertEqual(set(scenario["arms"]), set(ARMS))
            self.assertTrue(scenario["arms"]["treatment"]["prompt"].startswith("/claude-woocommerce-toolkit:"))
            self.assertEqual(scenario["arms"]["control"]["settings"], scenario["arms"]["treatment"]["settings"])
        self.assertEqual(self.manifest["settings"], {"tools": "Read", "effort": "high", "budget": 5})

    def test_candidate_digest_is_deterministic_and_excludes_git_metadata(self):
        again = self.ev.prepare(ROOT, self.tmp / "packet2")
        self.assertEqual(again["candidate_digest"], self.manifest["candidate_digest"])
        self.assertEqual(again["projection_digest"], self.manifest["projection_digest"])
        paths = [item["path"] for item in self.manifest["candidate_inventory"]]
        self.assertEqual(paths, sorted(paths))
        self.assertFalse(any(p.startswith(".git/") or "__pycache__" in p for p in paths))
        self.assertIn("skills/woocommerce-finalize/evals/evals.json", paths)

    def test_projection_excludes_evals_tests_docs_and_oracles(self):
        projected = set(inventory(self.out / "projection"))
        self.assertIn(".claude-plugin/plugin.json", projected)
        self.assertIn("skills/woocommerce-finalize/SKILL.md", projected)
        self.assertIn("skills/woocommerce-finalize/agents/openai.yaml", projected)
        for path in projected:
            self.assertFalse(path.startswith(("tests/", "docs/")) or "/evals/" in path, path)

    def test_prompts_and_workspaces_do_not_leak_oracles_or_candidate_paths(self):
        oracles = [e for s in self.scenarios.values() for e in json.loads(
            (self.out / "oracles" / f"{s['id']}.json").read_text(encoding="utf-8"))["expectations"]]
        self.assertTrue(oracles)
        for scenario in self.scenarios.values():
            for arm in scenario["arms"].values():
                prompt = arm["prompt"]
                self.assertNotIn(str(ROOT), prompt)
                self.assertNotIn("evals/", prompt)
                self.assertNotIn("Grader oracle", prompt)
                self.assertFalse(any(e in prompt for e in oracles))
                for path in inventory(Path(arm["workspace"])):
                    self.assertNotIn("evals", path)
                self.assertFalse(str(self.out / "oracles") in arm["workspace"])

    def test_both_arms_get_identical_fixture_bytes(self):
        fixtured = [s for s in self.scenarios.values() if s["fixtures"]]
        self.assertTrue(fixtured)
        for scenario in fixtured:
            treatment = inventory(Path(scenario["arms"]["treatment"]["workspace"]))
            control = inventory(Path(scenario["arms"]["control"]["workspace"]))
            self.assertEqual(treatment, control)
            self.assertEqual(treatment, scenario["fixtures"])

    def test_prepare_refuses_unsafe_outputs(self):
        with self.assertRaises(ValueError):
            self.ev.prepare(ROOT, ROOT / "tmp-packet")
        with self.assertRaises(ValueError):
            self.ev.prepare(ROOT, self.tmp / "sub" / ".." / "traversal")
        with self.assertRaises(FileExistsError):
            self.ev.prepare(ROOT, self.out)
        existing = self.tmp / "occupied"
        existing.mkdir()
        with self.assertRaises(FileExistsError):
            self.ev.prepare(ROOT, existing)

    def test_complete_records_pass_and_results_are_written(self):
        result = self.collect()
        self.assertEqual(result["manifest_sha256"], self.pin)
        self.assertEqual(result["candidate_digest"], self.manifest["candidate_digest"])
        self.assertEqual(result["coverage"], {"expected": 30, "complete": 30})
        self.assertTrue(result["complete"])
        self.assertEqual(json.loads((self.out / "results.json").read_text(encoding="utf-8")), result)
        self.assertTrue(all(r["grade"] is None for r in result["results"]))

    def test_missing_record_stays_incomplete(self):
        (self.records / "finalize-1" / "control.json").unlink()
        result = self.collect()
        self.assertEqual(self.status("finalize-1", "control", result), "incomplete")
        self.assertFalse(result["complete"])
        self.assertEqual(result["coverage"]["complete"], 29)

    def test_failed_runs_do_not_pass(self):
        cases = {
            "denied": lambda r: r["initial"].update(permission_denials=[{"tool_name": "Write"}]),
            "error": lambda r: r["initial"].update(is_error=True),
            "uncompleted": lambda r: r["initial"].update(terminal_reason="max_turns"),
            "empty_model_usage": lambda r: r["initial"].update(modelUsage={}),
        }
        for name, fn in cases.items():
            with self.subTest(name):
                self.mutate("finalize-1", "treatment", fn)
                self.assertEqual(self.status("finalize-1", "treatment"), "failed")

    def test_mutation_before_approval_fails_closed(self):
        def write_early(record):
            record["workspace_after_initial"] = {**record["workspace_after_initial"], "src/new.php": "0" * 64}
        self.mutate("dev-2", "treatment", write_early)
        self.assertEqual(self.status("dev-2", "treatment"), "failed")

    def test_required_approval_omitted_or_unbound_is_not_complete(self):
        self.mutate("dev-3", "control", lambda r: (r.pop("approval"), r.pop("resumed")))
        self.assertEqual(self.status("dev-3", "control"), "incomplete")
        self.mutate("dev-2", "control", lambda r: r["approval"].update(session_id="other"))
        self.assertEqual(self.status("dev-2", "control"), "failed")
        self.mutate("dev-2", "treatment", lambda r: r["resumed"].update(session_id="other"))
        self.assertEqual(self.status("dev-2", "treatment"), "failed")

    def live_write(self, sid, arm):
        """Return (record, live path): record snapshots fixtures first, then a real file is generated."""
        scenario = self.scenarios[sid]
        record = good_record(scenario, scenario["arms"][arm])
        path = Path(scenario["arms"][arm]["workspace"]) / "generated-feature.php"
        path.write_text("<?php // generated\n", encoding="utf-8")
        record["workspace_final"] = inventory(path.parent)
        return record, path

    def outcome(self, sid, arm):
        try:
            return self.status(sid, arm)
        except ValueError:
            return "raised"

    def test_actual_generated_file_after_approved_resume_collects_complete(self):
        record, _ = self.live_write("dev-2", "treatment")
        self.write_record("dev-2", "treatment", record)
        result = self.collect()
        row = next(r for r in result["results"] if r["scenario"] == "dev-2" and r["arm"] == "treatment")
        self.assertEqual(row["status"], "complete", row["reasons"])
        self.assertEqual(row["generated"], ["generated-feature.php"])
        self.assertEqual(row["acceptance"], "unresolved")

    def test_actual_generated_file_without_approved_resume_does_not_complete(self):
        record, _ = self.live_write("dev-2", "control")
        record.pop("approval")
        record.pop("resumed")
        self.write_record("dev-2", "control", record)
        self.assertIn(self.outcome("dev-2", "control"), ("failed", "raised"))
        record, _ = self.live_write("finalize-1", "treatment")
        self.write_record("finalize-1", "treatment", record)
        self.assertIn(self.outcome("finalize-1", "treatment"), ("failed", "raised"))

    def test_native_pre_approval_mutation_with_valid_grade_is_failed_and_rejected_with_inventory(self):
        record, _ = self.live_write("dev-2", "treatment")
        record["workspace_after_initial"] = record["workspace_final"]
        self.write_record("dev-2", "treatment", record)
        grades = self.tmp / "grades"
        path = grades / "dev-2" / "treatment.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.grade_for("dev-2", "treatment")), encoding="utf-8")
        result = self.collect(grades)
        rows = {(r["scenario"], r["arm"]): r for r in result["results"]}
        row = rows[("dev-2", "treatment")]
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["acceptance"], "rejected")
        self.assertEqual(row["generated"], ["generated-feature.php"])
        self.assertIn("rejected", {k for k, v in result["acceptance"].items() if v})
        control = rows[("dev-2", "control")]
        self.assertEqual((control["status"], control["acceptance"], control["generated"]), ("complete", "unresolved", []))

    def test_actual_write_reported_before_approval_still_fails(self):
        record, _ = self.live_write("dev-2", "treatment")
        record["workspace_after_initial"] = record["workspace_final"]
        self.write_record("dev-2", "treatment", record)
        self.assertIn(self.outcome("dev-2", "treatment"), ("failed", "raised"))

    def test_record_final_inventory_disagreeing_with_live_workspace_does_not_complete(self):
        record, _ = self.live_write("dev-2", "treatment")
        forged = {**record["workspace_final"], "generated-feature.php": "0" * 64}
        record["workspace_final"] = forged
        self.write_record("dev-2", "treatment", record)
        self.assertIn(self.outcome("dev-2", "treatment"), ("failed", "raised"))
        record["workspace_final"] = {k: v for k, v in forged.items() if k != "generated-feature.php"}
        self.write_record("dev-2", "treatment", record)
        self.assertIn(self.outcome("dev-2", "treatment"), ("failed", "raised"))

    def test_extra_fallback_model_usage_fails_the_single_model_contract(self):
        out = self.tmp / "pinned"
        settings = {"model": "pinned-model", "tools": "Read", "effort": "high", "budget": 5}
        manifest = self.ev.prepare(ROOT, out, settings)
        scenario = next(s for s in manifest["scenarios"] if s["id"] == "finalize-1")
        records = self.tmp / "pinned-records"
        used = {"inputTokens": 1, "outputTokens": 1}
        for arm, usage in (("treatment", {"pinned-model": used}), ("control", {"pinned-model": used, "fallback-model": used})):
            record = good_record(scenario, scenario["arms"][arm])
            record["initial"]["modelUsage"] = usage
            path = records / "finalize-1" / f"{arm}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record), encoding="utf-8")
        pin = sha(out / "manifest.json")
        rows = {r["arm"]: r for r in self.ev.collect(out, records, manifest_sha256=pin)["results"]
                if r["scenario"] == "finalize-1"}
        self.assertEqual(rows["treatment"]["status"], "complete", rows["treatment"]["reasons"])
        self.assertEqual(rows["control"]["status"], "failed")

    def test_grades_are_validated_not_fabricated(self):
        # Grades must bind to the candidate digest and the full expectations count; an unbound
        # grade could be replayed against a different candidate.
        grades = self.tmp / "grades"
        path = grades / "finalize-1" / "treatment.json"
        path.parent.mkdir(parents=True)
        total = self.oracle_total("finalize-1")
        grade = self.grade_for("finalize-1", "treatment", recall=4, false_positives=0)
        path.write_text(json.dumps(grade), encoding="utf-8")
        result = self.collect(grades)
        row = next(r for r in result["results"] if r["scenario"] == "finalize-1" and r["arm"] == "treatment")
        self.assertEqual(row["grade"], grade)
        self.assertEqual(row["acceptance"], "accepted")
        others = [r for r in result["results"] if r is not row]
        self.assertTrue(all(r["grade"] is None and r["acceptance"] == "unresolved" for r in others))
        self.assertEqual(result["acceptance"], {"accepted": 1, "rejected": 0, "unresolved": 29})
        invalid = {
            "empty": {},
            "string_route": {**grade, "route": "yes"},
            "negative_recall": {**grade, "recall": -1},
            "other_candidate": {**grade, "candidate_digest": "0" * 64},
            "partial_count": {**grade, "expectations_total": total - 1},
            "judge_is_run_session": {**grade, "judge_session_id": "s-finalize-1"},
            "wrong_scenario": {**grade, "scenario": "finalize-2"},
            "wrong_arm": {**grade, "arm": "control"},
            "wrong_record_sha": {**grade, "record_sha256": "0" * 64},
            "missing_scenario": {k: v for k, v in grade.items() if k != "scenario"},
            "missing_arm": {k: v for k, v in grade.items() if k != "arm"},
            "missing_record_sha": {k: v for k, v in grade.items() if k != "record_sha256"},
        }
        for name, bad in invalid.items():
            with self.subTest(name):
                path.write_text(json.dumps(bad), encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.collect(grades)

    def test_failed_expectations_are_rejected_and_stray_files_refused(self):
        grades = self.tmp / "grades"
        path = grades / "finalize-1" / "control.json"
        path.parent.mkdir(parents=True)
        total = self.oracle_total("finalize-1")
        path.write_text(json.dumps(self.grade_for("finalize-1", "control", expectations_passed=total - 1)), encoding="utf-8")
        row = next(r for r in self.collect(grades)["results"]
                   if r["scenario"] == "finalize-1" and r["arm"] == "control")
        self.assertEqual(row["acceptance"], "rejected")
        (self.records / "bogus").mkdir()
        (self.records / "bogus" / "treatment.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.collect(grades)

    def test_altered_candidate_projection_or_fixture_invalidates_packet(self):
        targets = [
            self.out / "projection" / "skills/woocommerce-finalize/SKILL.md",
            self.out / "candidate" / "README.md",
        ]
        fixture = next(s for s in self.scenarios.values() if s["fixtures"])
        targets.append(next(Path(fixture["arms"]["control"]["workspace"]).iterdir()))
        for target in targets:
            with self.subTest(target=target.name):
                original = target.read_bytes()
                target.write_bytes(original + b"\nextra")
                with self.assertRaises(ValueError):
                    self.collect()
                target.write_bytes(original)
        self.assertTrue(self.collect()["complete"])

    # Integrity regressions. Fixtures are synthetic metadata/record shapes, never model results.

    def oracle_total(self, sid):
        return len(json.loads((self.out / "oracles" / f"{sid}.json").read_text(encoding="utf-8"))["expectations"])

    def grade_for(self, sid, arm, **override):
        grade = {
            "candidate_digest": self.manifest["candidate_digest"], "expectations_total": self.oracle_total(sid),
            "expectations_passed": self.oracle_total(sid), "route": True, "judge_session_id": "judge-1",
            "scenario": sid, "arm": arm, "record_sha256": sha(self.records / sid / f"{arm}.json"),
        }
        grade.update(override)
        return grade

    def write_grade(self, root, sid, arm, grade):
        path = root / sid / f"{arm}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(grade), encoding="utf-8")

    def test_post_prepare_manifest_tampering_cannot_yield_complete_result(self):
        self.assertTrue(self.collect()["complete"])
        manifest_path = self.out / "manifest.json"
        original_manifest = manifest_path.read_bytes()
        oracle_path = self.out / "oracles" / "finalize-1.json"
        original_oracle = oracle_path.read_bytes()
        backup = self.tmp / "records-backup"
        shutil.copytree(self.records, backup)

        def edit(fn):
            manifest = json.loads(original_manifest)
            fn(manifest)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        def scenario(manifest, sid):
            return next(s for s in manifest["scenarios"] if s["id"] == sid)

        def approve_read_only(manifest):
            scenario(manifest, "finalize-1")["multi_turn"] = True
            for arm in ARMS:
                forged = {**self.scenarios["finalize-1"], "multi_turn": True}
                self.write_record("finalize-1", arm, good_record(forged, forged["arms"][arm]))

        def waive_approval(manifest):
            scenario(manifest, "dev-2")["multi_turn"] = False
            for arm in ARMS:
                self.mutate("dev-2", arm, lambda r: (r.pop("approval"), r.pop("resumed")))

        def omit_scenario(manifest):
            manifest["scenarios"] = [s for s in manifest["scenarios"] if s["id"] != "finalize-1"]
            shutil.rmtree(self.records / "finalize-1")

        def rewrite_prompt(manifest):
            scenario(manifest, "finalize-1")["arms"]["treatment"]["prompt"] = "rewritten prompt"

        def rewrite_settings(manifest):
            manifest["settings"] = {}

        def rewrite_oracle(manifest):
            oracle = json.loads(original_oracle)
            oracle["expectations"] = oracle["expectations"][:1]
            oracle_path.write_text(json.dumps(oracle), encoding="utf-8")
            scenario(manifest, "finalize-1")["oracle_sha256"] = sha(oracle_path)

        cases = {
            "read_only_scenario_given_approval_policy": approve_read_only,
            "approval_policy_waived": waive_approval,
            "scenario_omitted_with_matching_records": omit_scenario,
            "prompt_rewritten": rewrite_prompt,
            "settings_rewritten": rewrite_settings,
            "oracle_rewritten_and_rehashed": rewrite_oracle,
        }
        for name, fn in cases.items():
            with self.subTest(name):
                try:
                    edit(fn)
                    with self.assertRaises(ValueError):
                        self.collect()
                finally:
                    manifest_path.write_bytes(original_manifest)
                    oracle_path.write_bytes(original_oracle)
                    shutil.rmtree(self.records)
                    shutil.copytree(backup, self.records)

    def test_results_symlink_is_rejected_and_target_untouched(self):
        sentinel = self.tmp / "sentinel.txt"
        sentinel.write_text("sentinel", encoding="utf-8")
        (self.out / "results.json").symlink_to(sentinel)
        with self.assertRaises(ValueError):
            self.collect()
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel")

    def test_results_write_replaces_without_following_symlink_and_leaves_no_temp_files(self):
        self.collect()
        results = self.out / "results.json"
        sentinel = self.tmp / "sentinel.txt"
        sentinel.write_text("sentinel", encoding="utf-8")
        real_replace = self.ev.os.replace

        def swap_then_replace(src, dst):
            Path(dst).unlink()
            Path(dst).symlink_to(sentinel)
            real_replace(src, dst)

        self.ev.os.replace = swap_then_replace
        try:
            self.collect()
        finally:
            self.ev.os.replace = real_replace
        self.assertFalse(results.is_symlink())
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel")
        self.assertEqual([p.name for p in self.out.glob(".results-*")], [])

        def fail(src, dst):
            raise OSError("boom")

        self.ev.os.replace = fail
        try:
            with self.assertRaises(OSError):
                self.collect()
        finally:
            self.ev.os.replace = real_replace
        self.assertEqual([p.name for p in self.out.glob(".results-*")], [])

    def test_external_manifest_pin_is_required_and_exact(self):
        with self.assertRaises(TypeError):
            self.ev.collect(self.out, self.records)
        for name, pin in {"empty": "", "short": self.pin[:10], "upper": self.pin.upper(), "other": "0" * 64, "none": None}.items():
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    self.ev.collect(self.out, self.records, manifest_sha256=pin)
        self.assertFalse((self.out / "results.json").exists())
        manifest = json.loads((self.out / "manifest.json").read_text(encoding="utf-8"))
        manifest["settings"] = {}
        (self.out / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.collect()
        self.assertFalse((self.out / "results.json").exists())

    def test_cli_requires_and_honours_manifest_pin(self):
        with self.assertRaises(SystemExit):
            self.ev.main(["collect", str(self.out), str(self.records)])
        self.assertEqual(self.ev.main(["collect", str(self.out), str(self.records), "--manifest-sha256", "0" * 64]), 1)
        self.assertEqual(self.ev.main(["collect", str(self.out), str(self.records), "--manifest-sha256", self.pin]), 0)

    def test_grade_judge_must_be_independent_of_every_run_session(self):
        self.mutate("finalize-1", "control", lambda r: r["initial"].update(session_id="s-finalize-1-control"))
        grades = self.tmp / "grades"
        self.write_grade(grades, "finalize-1", "treatment", self.grade_for("finalize-1", "treatment"))
        row = next(r for r in self.collect(grades)["results"]
                   if r["scenario"] == "finalize-1" and r["arm"] == "treatment")
        self.assertEqual(row["acceptance"], "accepted")
        for name, judge in {"other_case_session": "s-finalize-2", "other_arm_session": "s-finalize-1-control"}.items():
            with self.subTest(name):
                self.write_grade(grades, "finalize-1", "treatment",
                                 self.grade_for("finalize-1", "treatment", judge_session_id=judge))
                with self.assertRaises(ValueError):
                    self.collect(grades)

    def test_grade_from_another_row_with_same_expectation_count_is_refused(self):
        totals = {sid: self.oracle_total(sid) for sid in sorted(self.scenarios)}
        sid_a, sid_b = next((a, b) for a in totals for b in totals if a < b and totals[a] == totals[b])
        source = self.grade_for(sid_a, "treatment")
        grades = self.tmp / "grades"
        self.write_grade(grades, sid_a, "treatment", source)
        self.assertEqual(self.collect(grades)["acceptance"]["accepted"], 1)
        shutil.rmtree(grades)
        for name, (sid, arm) in {"other_arm": (sid_a, "control"), "other_scenario": (sid_b, "treatment")}.items():
            with self.subTest(name):
                self.write_grade(grades, sid, arm, source)
                with self.assertRaises(ValueError):
                    self.collect(grades)
                shutil.rmtree(grades)

    def test_grade_is_bound_to_the_exact_record_bytes(self):
        grades = self.tmp / "grades"
        self.write_grade(grades, "finalize-1", "treatment", self.grade_for("finalize-1", "treatment"))
        self.mutate("finalize-1", "treatment", lambda r: r["initial"].update(session_id="s-finalize-1-rerun"))
        with self.assertRaises(ValueError):
            self.collect(grades)

    def test_completed_record_must_claim_actual_inference(self):
        empty = {"inputTokens": 0, "outputTokens": 0, "cacheReadInputTokens": 0, "cacheCreationInputTokens": 0}
        refused = {
            "empty_stats": {"pinned-model": {}},
            "zero_tokens": {"pinned-model": {"inputTokens": 0, "outputTokens": 0}},
            "zero_tokens_and_cache": {"pinned-model": empty},
            "cost_only": {"pinned-model": {"costUSD": 0.01}},
            "output_only": {"pinned-model": {**empty, "outputTokens": 2}},
            "input_only": {"pinned-model": {**empty, "inputTokens": 2}},
            "cache_input_without_output": {"pinned-model": {**empty, "cacheReadInputTokens": 5}},
            "negative_input": {"pinned-model": {**empty, "inputTokens": -1, "outputTokens": 1}},
            "negative_output": {"pinned-model": {**empty, "inputTokens": 1, "outputTokens": -1}},
            "negative_cache": {"pinned-model": {**empty, "cacheReadInputTokens": -1, "outputTokens": 1}},
            "boolean_input": {"pinned-model": {**empty, "inputTokens": True, "outputTokens": 1}},
            "boolean_output": {"pinned-model": {**empty, "inputTokens": 1, "outputTokens": True}},
            "boolean_cache": {"pinned-model": {**empty, "cacheCreationInputTokens": True, "outputTokens": 1}},
        }
        allowed = {
            "input_and_output": {"pinned-model": {**empty, "inputTokens": 1, "outputTokens": 1}},
            "cache_read_input_with_output": {"pinned-model": {**empty, "cacheReadInputTokens": 5, "outputTokens": 1}},
            "cache_creation_input_with_output": {"pinned-model": {**empty, "cacheCreationInputTokens": 3, "outputTokens": 1}},
        }
        for name, usage in refused.items():
            with self.subTest(name, turn="initial"):
                self.mutate("finalize-1", "treatment", lambda r: r["initial"].update(modelUsage=usage))
                self.assertEqual(self.status("finalize-1", "treatment"), "failed")
            with self.subTest(name, turn="resumed"):
                self.mutate("dev-2", "treatment", lambda r: r["resumed"].update(modelUsage=usage))
                self.assertEqual(self.status("dev-2", "treatment"), "failed")
        for name, usage in allowed.items():
            with self.subTest(name):
                self.mutate("finalize-1", "treatment", lambda r: r["initial"].update(modelUsage=usage))
                self.assertEqual(self.status("finalize-1", "treatment"), "complete")

    INVALID_MODEL_PINS = {
        "null": None,
        "empty": "",
        "whitespace": "   ",
        "bool_false": False,
        "bool_true": True,
        "number_zero": 0,
        "number": 7,
        "list": ["pinned-model"],
        "empty_list": [],
        "object": {"name": "pinned-model"},
        "empty_object": {},
    }

    def cli_prepare(self, settings, out):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.ev.main(["prepare", str(ROOT), str(out), "--settings", json.dumps(settings)])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_cli_prepare_rejects_explicitly_invalid_model_pins(self):
        base = {"harness": "claude-code", "tools": "Read", "effort": "high", "budget": 5}
        self.assertEqual(set(base) | {"model"}, self.ev.PIN_KEYS)
        for name, pin in self.INVALID_MODEL_PINS.items():
            with self.subTest(name):
                out = self.tmp / f"cli-{name}"
                code, stdout, stderr = self.cli_prepare({**base, "model": pin}, out)
                self.assertNotEqual(code, 0)
                self.assertNotIn("manifest_sha256", stdout)
                self.assertTrue(stderr.startswith("error:"), stderr)
                self.assertFalse((out / "manifest.json").exists())
        code, stdout, _ = self.cli_prepare({**base, "model": "pinned-model"}, self.tmp / "cli-valid")
        self.assertEqual(code, 0)
        self.assertIn("manifest_sha256", stdout)

    def test_api_prepare_rejects_explicitly_invalid_model_pins_but_allows_omission(self):
        for name, pin in self.INVALID_MODEL_PINS.items():
            with self.subTest(name):
                out = self.tmp / f"api-{name}"
                with self.assertRaises(ValueError):
                    self.ev.prepare(ROOT, out, {"model": pin, "tools": "Read"})
                self.assertFalse((out / "manifest.json").exists())
        self.assertNotIn("model", self.manifest["settings"])
        self.ev.prepare(ROOT, self.tmp / "api-valid", {"model": "pinned-model", "tools": "Read"})

    def test_turn_and_record_validation_never_skip_an_invalid_model_pin(self):
        scenario = self.scenarios["dev-2"]
        turn = good_record(scenario, scenario["arms"]["treatment"])["initial"]
        self.assertEqual(self.ev.turn_problems(turn, {}), [])
        self.assertEqual(self.ev.turn_problems(turn, {"model": "pinned-model"}), [])
        self.assertTrue(self.ev.turn_problems(turn, {"model": "other-model"}))
        for name, pin in self.INVALID_MODEL_PINS.items():
            with self.subTest(name):
                self.assertTrue(self.ev.turn_problems(turn, {"model": pin}))
                for arm in ARMS:
                    record = good_record(scenario, scenario["arms"][arm])
                    status, reasons = self.ev.judge_record(scenario, record, {"model": pin})
                    self.assertEqual(status, "failed")
                    self.assertTrue(reasons)

    # Inventory root and traversal regressions. All data below is synthetic unit metadata, not benchmark evidence.

    def test_inventory_accepts_valid_empty_directory(self):
        empty = self.tmp / "empty-root"
        empty.mkdir()
        self.assertEqual(self.ev.inventory(empty), [])

    def test_inventory_refuses_missing_non_directory_and_symlink_roots(self):
        real_empty = self.tmp / "real-empty"
        real_empty.mkdir()
        a_file = self.tmp / "a-file"
        a_file.write_text("x", encoding="utf-8")
        link = self.tmp / "link-root"
        link.symlink_to(real_empty, target_is_directory=True)
        roots = {"missing": self.tmp / "no-such-root", "file": a_file, "symlink": link}
        for name, root in roots.items():
            with self.subTest(name):
                with self.assertRaises(ValueError):
                    self.ev.inventory(root)

    def test_inventory_traversal_errors_raise_value_error(self):
        # Inject OSError into the real os.walk scandir for one directory. A swallowed error (no onerror
        # handler) returns a result instead of raising; setup failures are asserted separately.
        for name, depth in {"root": 0, "nested": 1}.items():
            with self.subTest(name):
                root = self.tmp / f"walk-{name}"
                nested = root / "sub"
                nested.mkdir(parents=True)
                (root / "a.txt").write_text("a", encoding="utf-8")
                (nested / "b.txt").write_text("b", encoding="utf-8")
                target = os.fspath(root if depth == 0 else nested)
                real_scandir, hits = os.scandir, []

                def faulty(path=".", *args, **kwargs):
                    if os.fspath(path) == target:
                        hits.append(target)
                        raise PermissionError(13, "injected traversal fault", target)
                    return real_scandir(path, *args, **kwargs)

                os.scandir = faulty
                try:
                    try:
                        outcome = self.ev.inventory(root)
                    except ValueError:
                        outcome = "value-error"
                    except Exception as exc:
                        outcome = f"unexpected {type(exc).__name__}"
                finally:
                    os.scandir = real_scandir
                self.assertTrue(hits, "injected fault was never reached by inventory traversal")
                self.assertEqual(outcome, "value-error", f"traversal error was not refused: {outcome!r}")

    def test_collect_refuses_deleted_empty_workspace_with_valid_synthetic_grade(self):
        sid = next(s for s, sc in sorted(self.scenarios.items()) if not sc["fixtures"])
        arm = "treatment"
        workspace = Path(self.scenarios[sid]["arms"][arm]["workspace"])
        self.assertTrue(workspace.is_dir())
        self.assertEqual(self.ev.inventory(workspace), [])
        self.assertTrue(self.collect()["complete"])
        grades = self.tmp / "grades"
        self.write_grade(grades, sid, arm, self.grade_for(sid, arm))
        self.assertEqual(self.collect(grades)["acceptance"]["accepted"], 1)
        (self.out / "results.json").unlink()
        shutil.rmtree(workspace)
        result = None
        try:
            result = self.collect(grades)
        except ValueError:
            pass
        self.assertIsNone(result, "deleted workspace was collected instead of refused")
        self.assertFalse((self.out / "results.json").exists())


if __name__ == "__main__":
    unittest.main()
