#!/usr/bin/env python3
"""Prepare and collect paired evaluation packets. Never launches models, picks settings, or judges."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ARMS = ("treatment", "control")
PLUGIN = "claude-woocommerce-toolkit"
SHORT = {"woocommerce-plugin-dev": "dev", "woocommerce-upgrade-safety": "upgrade", "woocommerce-finalize": "finalize"}
SKIP = {".git", "__pycache__", ".DS_Store"}
HEX = re.compile(r"[0-9a-f]{64}")
PIN_KEYS = {"model", "harness", "effort", "budget", "tools"}
GRADE_KEYS = {
    "candidate_digest", "expectations_total", "expectations_passed", "route", "judge_session_id",
    "scenario", "arm", "record_sha256",
}
TOKEN_KEYS = ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens")
GRADE_COUNTS = ("recall", "false_positives")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{path.name}: not a regular file")
    raw = path.read_bytes()
    try:
        return json.loads(raw.decode("utf-8")), sha(raw)
    except ValueError as exc:
        raise ValueError(f"{path.name}: invalid JSON") from exc


def load_json(path):
    return read_json(path)[0]


def write_results(path, value):
    """Atomic sibling replace; assumes the packet directory itself is owned by the trusted controller."""
    if path.is_symlink():
        raise ValueError("results.json is a symlink")
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".results-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.lexists(tmp):
            os.unlink(tmp)
        raise


def inventory(root, skip=False):
    if os.path.islink(root) or not os.path.isdir(root):
        raise ValueError(f"inventory root is not an existing non-symlink directory: {root}")

    def refuse(exc):
        raise ValueError(f"inventory traversal failed: {exc}") from exc

    items = []
    for base, dirs, files in os.walk(root, onerror=refuse):
        dirs[:] = sorted(d for d in dirs if not (skip and d in SKIP))
        files = [f for f in files if not (skip and (f in SKIP or f.endswith(".pyc")))]
        for name in dirs + files:
            if os.path.islink(os.path.join(base, name)):
                raise ValueError(f"symlink refused: {name}")
        items += [{"path": Path(base, f).relative_to(root).as_posix(), "sha256": sha(Path(base, f).read_bytes())} for f in files]
    return sorted(items, key=lambda item: item["path"])


def as_map(items):
    return {item["path"]: item["sha256"] for item in items}


def projected(rel):
    p = rel.split("/")
    return rel == ".claude-plugin/plugin.json" or (
        p[0] == "skills" and len(p) >= 3 and (p[2:] == ["SKILL.md"] or p[2:] == ["agents", "openai.yaml"] or (p[2] == "references" and len(p) > 3))
    )


def copy_into(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def bad_model_pin(settings):
    return isinstance(settings, dict) and "model" in settings and not (
        isinstance(settings["model"], str) and settings["model"].strip()
    )


def prepare(candidate, out, settings=None):
    candidate = Path(candidate).resolve()
    settings = {} if settings is None else settings
    if not isinstance(settings, dict):
        raise ValueError("settings must be a JSON object")
    if bad_model_pin(settings):
        raise ValueError("model pin must be a nonempty string")
    if ".." in Path(out).parts:
        raise ValueError("output path must not contain '..'")
    out = Path(out).resolve()
    if out == candidate or candidate in out.parents or out in candidate.parents:
        raise ValueError("output must be outside the candidate")
    if os.path.lexists(out):
        raise FileExistsError(f"output exists: {out}")
    inv = inventory(candidate, skip=True)
    out.mkdir(parents=True)
    snap = out / "candidate"
    for item in inv:
        copy_into(candidate / item["path"], snap / item["path"])
    if inventory(snap) != inv:
        raise ValueError("candidate changed while it was being snapshotted")
    proj = [item for item in inv if projected(item["path"])]
    for item in proj:
        copy_into(snap / item["path"], out / "projection" / item["path"])
    by_path = as_map(inv)
    cand_digest = digest(inv)
    (out / "oracles").mkdir()
    scenarios = []
    for skill in sorted(SHORT):
        for ev in load_json(snap / "skills" / skill / "evals/evals.json")["evals"]:
            sid = f"{SHORT[skill]}-{ev['id']}"
            names = [Path(f).name for f in ev["files"]]
            if len(set(names)) != len(names):
                raise ValueError(f"{sid}: duplicate fixture basename")
            sources = {Path(f).name: f"skills/{skill}/{f}" for f in ev["files"]}
            if not set(sources.values()) <= set(by_path):
                raise ValueError(f"{sid}: fixture missing from candidate")
            oracle = out / "oracles" / f"{sid}.json"
            write_json(oracle, {"scenario": sid, "candidate_digest": cand_digest, "expected_output": ev["expected_output"], "expectations": ev["expectations"]})
            text = ev["prompt"] + (f"\n\nAttached files in the working directory: {', '.join(names)}." if names else "")
            prompts = {"treatment": f"/{PLUGIN}:{skill} {text}", "control": text}
            arms = {}
            for arm in ARMS:
                workspace = out / "workspaces" / sid / arm
                workspace.mkdir(parents=True)
                for name, rel in sources.items():
                    copy_into(snap / rel, workspace / name)
                arms[arm] = {"workspace": str(workspace), "prompt": prompts[arm], "settings": dict(settings)}
            scenarios.append({
                "id": sid, "skill": skill, "arms": arms, "oracle_sha256": sha(oracle.read_bytes()),
                "multi_turn": bool(re.search(r"after approval", ev["expected_output"], re.I)),
                "fixtures": {name: by_path[rel] for name, rel in sources.items()}, "fixture_sources": sources,
            })
    manifest = {
        "schema": 1, "candidate_digest": cand_digest, "projection_digest": digest(proj), "settings": settings,
        "candidate_inventory": inv, "projection_inventory": proj, "scenarios": scenarios,
    }
    write_json(out / "manifest.json", manifest)
    return manifest


def verify_packet(out, manifest=None):
    manifest = load_json(out / "manifest.json") if manifest is None else manifest
    try:
        inv, proj = manifest["candidate_inventory"], manifest["projection_inventory"]
        if inventory(out / "candidate") != inv or digest(inv) != manifest["candidate_digest"]:
            raise ValueError("candidate snapshot altered")
        if proj != [i for i in inv if projected(i["path"])] or inventory(out / "projection") != proj or digest(proj) != manifest["projection_digest"]:
            raise ValueError("treatment projection altered")
        by_path = as_map(inv)
        for s in manifest["scenarios"]:
            if sha((out / "oracles" / f"{s['id']}.json").read_bytes()) != s["oracle_sha256"]:
                raise ValueError(f"{s['id']}: oracle altered")
            if s["fixtures"].keys() != s["fixture_sources"].keys() or any(
                s["fixtures"][n] != by_path.get(rel) for n, rel in s["fixture_sources"].items()
            ):
                raise ValueError(f"{s['id']}: fixtures differ from candidate")
    except (KeyError, TypeError, AttributeError, OSError) as exc:
        raise ValueError(f"packet structure invalid: {exc!r}") from exc
    return manifest


def usage_problem(stats):
    count = lambda v: isinstance(v, int) and not isinstance(v, bool) and v >= 0
    if not all(k not in stats or count(stats[k]) for k in TOKEN_KEYS):
        return "token fields must be nonnegative integers"
    if not stats.get("outputTokens", 0) > 0:
        return "no output tokens"
    if not sum(stats.get(k, 0) for k in TOKEN_KEYS[:1] + TOKEN_KEYS[2:]) > 0:
        return "no input or cache tokens"
    return None


def turn_problems(turn, settings):
    if not isinstance(turn, dict):
        return ["turn is not an object"]
    bad = []
    pin_invalid = bad_model_pin(settings)
    if pin_invalid:
        bad.append("model pin invalid")
    if not (isinstance(turn.get("session_id"), str) and turn["session_id"]):
        bad.append("session_id missing")
    if turn.get("is_error") is not False:
        bad.append("is_error is not false")
    if turn.get("terminal_reason") != "completed":
        bad.append("terminal_reason is not completed")
    if turn.get("permission_denials") != []:
        bad.append("permission denials present")
    usage = turn.get("modelUsage")
    if not (isinstance(usage, dict) and usage and all(isinstance(v, dict) for v in usage.values())):
        bad.append("modelUsage empty or invalid")
    elif not pin_invalid and "model" in settings and set(usage) != {settings["model"]}:
        bad.append("modelUsage must contain exactly the pinned model")
    elif any(usage_problem(v) for v in usage.values()):
        bad.append("modelUsage is not completed inference")
    if not isinstance(turn.get("result"), str):
        bad.append("result missing")
    return bad


def valid_files(value):
    return isinstance(value, dict) and all(isinstance(v, str) and HEX.fullmatch(v) for v in value.values())


def judge_record(scenario, record, settings):
    if not isinstance(record, dict):
        return "failed", ["record is not an object"]
    initial, approval, resumed = record.get("initial"), record.get("approval"), record.get("resumed")
    bad = turn_problems(initial, settings)
    after, final, fixtures = record.get("workspace_after_initial"), record.get("workspace_final"), scenario["fixtures"]
    if not (valid_files(after) and valid_files(final)):
        bad.append("workspace inventories invalid")
    else:
        if after != fixtures:
            bad.append("workspace mutated before approval")
        if final != fixtures and not (scenario["multi_turn"] and approval is not None and resumed is not None):
            bad.append("workspace mutated without approved resumed turn")
    incomplete = False
    if not scenario["multi_turn"]:
        if approval is not None or resumed is not None:
            bad.append("approval or resumed turn on a single-turn scenario")
    elif approval is None and resumed is None:
        incomplete = True
    elif resumed is None:
        incomplete = True
    elif approval is None:
        bad.append("resumed turn without approval")
    else:
        sid = initial.get("session_id") if isinstance(initial, dict) else None
        if not (isinstance(approval, dict) and approval.get("approved") is True and approval.get("session_id") == sid):
            bad.append("approval is not bound to the initial session")
        bad += ["resumed: " + p for p in turn_problems(resumed, settings)]
        if isinstance(resumed, dict) and resumed.get("session_id") != sid:
            bad.append("resumed turn is not the original session")
    if bad:
        return "failed", bad
    return ("incomplete", ["approval or resumed turn missing"]) if incomplete else ("complete", [])


def check_grade(label, grade, total, cand_digest, run_sessions, binding):
    if not isinstance(grade, dict):
        raise ValueError(f"grade {label}: not an object")
    count = lambda v, hi=None: isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= (hi if hi is not None else v)
    bad = [f"unknown key {k}" for k in set(grade) - GRADE_KEYS - set(GRADE_COUNTS)]
    bad += [f"missing {k}" for k in GRADE_KEYS - set(grade)]
    if grade.get("candidate_digest") != cand_digest:
        bad.append("not bound to this candidate")
    bad += [f"{k} does not match this row" for k, v in binding.items() if grade.get(k) != v or v is None]
    if grade.get("expectations_total") != total:
        bad.append(f"expectations_total must be {total}")
    if not count(grade.get("expectations_passed"), total):
        bad.append("expectations_passed out of range")
    if not isinstance(grade.get("route"), bool):
        bad.append("route must be a boolean")
    judge = grade.get("judge_session_id")
    if not isinstance(judge, str) or not judge or judge in run_sessions:
        bad.append("judge_session_id must be a fresh session")
    bad += [f"{k} invalid" for k in GRADE_COUNTS if k in grade and not count(grade[k])]
    if bad:
        raise ValueError(f"grade {label}: " + "; ".join(bad))


def reject_strays(root, expected):
    if root.is_dir():
        for path in root.rglob("*.json"):
            rel = path.relative_to(root).parts
            if len(rel) != 2 or (rel[0], rel[1][:-5]) not in expected:
                raise ValueError(f"unexpected file: {path.relative_to(root)}")


def collect(out, records, grades=None, *, manifest_sha256):
    """manifest_sha256 is the SHA printed by prepare, retained by the controller outside OUT.

    It binds settings, prompts, scenario inventory, approval policy and oracle hashes to the trusted
    preparation. It does not authenticate manually forged model records.
    """
    out, records = Path(out), Path(records)
    grades = Path(grades) if grades else None
    if not (isinstance(manifest_sha256, str) and HEX.fullmatch(manifest_sha256)):
        raise ValueError("manifest_sha256 must be a 64-character lowercase hex pin from prepare")
    manifest, actual = read_json(out / "manifest.json")
    if actual != manifest_sha256:
        raise ValueError("manifest.json does not match the supplied manifest_sha256 pin")
    manifest = verify_packet(out, manifest)
    results_path = out / "results.json"
    if results_path.is_symlink():
        raise ValueError("results.json is a symlink")
    expected = {(s["id"], arm) for s in manifest["scenarios"] for arm in ARMS}
    reject_strays(records, expected)
    if grades:
        reject_strays(grades, expected)
    loaded, run_sessions = {}, set()
    for s in manifest["scenarios"]:
        for arm in ARMS:
            path = records / s["id"] / f"{arm}.json"
            if not path.is_symlink() and not path.exists():
                loaded[s["id"], arm] = (None, None, None)
                continue
            try:
                record, record_sha = read_json(path)
                loaded[s["id"], arm] = (record, record_sha, None)
                if isinstance(record, dict):
                    run_sessions |= {t["session_id"] for t in (record.get("initial"), record.get("resumed"))
                                     if isinstance(t, dict) and isinstance(t.get("session_id"), str)}
            except ValueError as exc:
                loaded[s["id"], arm] = (None, None, str(exc))
    rows, tally = [], {"accepted": 0, "rejected": 0, "unresolved": 0}
    for s in manifest["scenarios"]:
        total = len(load_json(out / "oracles" / f"{s['id']}.json")["expectations"])
        for arm in ARMS:
            record, record_sha, error = loaded[s["id"], arm]
            if error:
                status, reasons = "failed", [error]
            elif record_sha is None:
                status, reasons = "incomplete", ["no record"]
            else:
                status, reasons = judge_record(s, record, manifest["settings"])
            live = as_map(inventory(out / "workspaces" / s["id"] / arm))
            final = record.get("workspace_final") if isinstance(record, dict) else None
            expected_live = final if valid_files(final) else (s["fixtures"] if record is None else None)
            if expected_live is not None and live != expected_live:
                raise ValueError(f"{s['id']}/{arm}: live workspace differs from {'recorded final' if record else 'original fixtures'}")
            generated = sorted(p for p, h in final.items() if s["fixtures"].get(p) != h) if valid_files(final) else []
            grade = grade_sha = None
            gpath = grades / s["id"] / f"{arm}.json" if grades else None
            if gpath and (gpath.exists() or gpath.is_symlink()):
                grade, grade_sha = read_json(gpath)
                binding = {"scenario": s["id"], "arm": arm, "record_sha256": record_sha}
                check_grade(f"{s['id']}/{arm}", grade, total, manifest["candidate_digest"], run_sessions, binding)
            acceptance = "unresolved"
            if grade is not None and status == "failed":
                acceptance = "rejected"
            elif grade is not None and status == "complete":
                full = grade["route"] and grade["expectations_passed"] == total and not grade.get("false_positives")
                acceptance = "accepted" if full else "rejected"
            tally[acceptance] += 1
            rows.append({
                "scenario": s["id"], "arm": arm, "status": status, "reasons": reasons, "record_sha256": record_sha,
                "generated": generated, "grade": grade, "grade_sha256": grade_sha, "acceptance": acceptance,
            })
    done = sum(row["status"] == "complete" for row in rows)
    result = {
        "candidate_digest": manifest["candidate_digest"], "projection_digest": manifest["projection_digest"],
        "manifest_sha256": manifest_sha256, "settings": manifest["settings"],
        "coverage": {"expected": len(rows), "complete": done}, "complete": done == len(rows),
        "acceptance": tally, "results": rows,
    }
    write_results(results_path, result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("candidate")
    prep.add_argument("out")
    prep.add_argument("--settings", required=True, help="JSON object pinning " + ", ".join(sorted(PIN_KEYS)))
    coll = sub.add_parser("collect")
    coll.add_argument("out")
    coll.add_argument("records")
    coll.add_argument("--grades")
    coll.add_argument("--manifest-sha256", required=True, help="manifest SHA printed by prepare, kept outside OUT")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            settings = json.loads(args.settings)
            missing = PIN_KEYS - set(settings) if isinstance(settings, dict) else PIN_KEYS
            if missing:
                raise ValueError("settings must pin " + ", ".join(sorted(missing)))
            manifest = prepare(args.candidate, args.out, settings)
            summary = {k: manifest[k] for k in ("candidate_digest", "projection_digest")}
            summary["manifest_sha256"] = sha((Path(args.out) / "manifest.json").read_bytes())
            print(json.dumps(summary, indent=2))
            return 0
        result = collect(args.out, args.records, args.grades, manifest_sha256=args.manifest_sha256)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({k: result[k] for k in ("coverage", "complete", "acceptance")}, indent=2))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    sys.exit(main())
