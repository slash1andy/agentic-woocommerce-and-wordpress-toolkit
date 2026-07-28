import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = (
    "woocommerce-plugin-dev",
    "woocommerce-finalize",
    "woocommerce-upgrade-safety",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class ReleaseContractsTest(unittest.TestCase):
    def test_all_skills_have_official_format_manual_scenarios(self):
        corpora = {}
        for skill in SKILLS:
            path = ROOT / "skills" / skill / "evals/evals.json"
            with self.subTest(skill=skill):
                data = json.loads(read(path))
                self.assertEqual({"skill_name", "evals"}, set(data))
                self.assertEqual(skill, data["skill_name"])
                self.assertGreaterEqual(len(data["evals"]), 3)
                ids = [scenario["id"] for scenario in data["evals"]]
                self.assertEqual(len(ids), len(set(ids)))
                for scenario in data["evals"]:
                    self.assertEqual(
                        {"id", "prompt", "expected_output", "files", "expectations"},
                        set(scenario),
                    )
                    self.assertIsInstance(scenario["id"], int)
                    self.assertTrue(scenario["prompt"].strip())
                    self.assertTrue(scenario["expected_output"].strip())
                    self.assertEqual([], scenario["files"])
                    self.assertGreaterEqual(len(scenario["expectations"]), 2)
                corpora[skill] = json.dumps(data)

        self.assertIn("Does NOT invoke this skill", corpora["woocommerce-plugin-dev"])
        for marker in ("REST", "Store API", "MCP"):
            self.assertIn(marker, corpora["woocommerce-plugin-dev"])
        for marker in ("read-only", "Does NOT edit", "/code-review"):
            self.assertIn(marker, corpora["woocommerce-finalize"])
        for marker in (
            "stable monotonic cursor",
            "replay",
            "installed, licensed official source",
            "blocked/unknown",
            "Does NOT invoke this skill",
        ):
            self.assertIn(marker, corpora["woocommerce-upgrade-safety"])

    def test_evaluation_status_is_truthful(self):
        readme = read(ROOT / "README.md")
        status = read(ROOT / "docs/evaluation-status.md")
        combined = f"{readme}\n{status}"

        self.assertIn("manual evaluation scenarios", readme.lower())
        self.assertNotIn("evaluation benchmarks", readme.lower())
        self.assertIn("official `skill-creator` plugin", status)
        self.assertIn("401", status)
        self.assertIn("have not been executed", status)
        self.assertIn("with-skill/without-skill", status)
        self.assertNotIn("response-level evaluation passed", combined.lower())
        self.assertFalse(any(ROOT.rglob("benchmark.json")))
        self.assertFalse(any(ROOT.rglob("benchmark.md")))

    def test_security_policy_has_an_honest_private_reporting_gate(self):
        security = read(ROOT / "SECURITY.md").lower()

        self.assertIn("private vulnerability reporting is not currently enabled", security)
        self.assertIn("do not disclose", security)
        for marker in ("credentials", "customer data", "payment data", "public issue"):
            self.assertIn(marker, security)
        self.assertIn("gpl-2.0-or-later", security)

    def test_local_release_checklist_preserves_the_approval_gate(self):
        checklist = read(ROOT / "docs/release-checklist.md")

        for command in (
            "python3 -B scripts/validate.py",
            "python3 -B scripts/validate.py --check-urls",
            "python3 -B -m unittest discover -s tests -p 'test_*.py'",
            "claude plugin validate .claude-plugin/plugin.json --strict",
            "claude plugin validate .claude-plugin/marketplace.json --strict",
            "git diff --check",
        ):
            self.assertIn(command, checklist)
        for marker in (
            "copied-cache installation",
            "explicit approval",
            "repository settings",
            "tag",
            "release",
            "marketplace",
            "fake or sandbox providers",
        ):
            self.assertIn(marker, checklist)
        self.assertFalse((ROOT / ".github/workflows").exists())

    def test_license_identifier_is_consistent(self):
        plugin = json.loads(read(ROOT / ".claude-plugin/plugin.json"))
        self.assertEqual("GPL-2.0-or-later", plugin["license"])
        self.assertIn("GPL-2.0-or-later", read(ROOT / "README.md"))
        self.assertIn("GPL-2.0-or-later", read(ROOT / "CONTRIBUTING.md"))
        self.assertIn("either version 2 of the License, or", read(ROOT / "LICENSE"))


if __name__ == "__main__":
    unittest.main()
