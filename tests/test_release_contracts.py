import json
import re
import subprocess
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
        evidence_cases = 0
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
                    self.assertIsInstance(scenario["files"], list)
                    for relative in scenario["files"]:
                        fixture = ROOT / "skills" / skill / relative
                        self.assertTrue(fixture.is_file(), relative)
                        evidence_cases += 1
                    self.assertGreaterEqual(len(scenario["expectations"]), 2)
                corpora[skill] = json.dumps(data)

        self.assertIn("Does not invoke this skill", corpora["woocommerce-plugin-dev"])
        for marker in ("REST", "Store API", "MCP"):
            self.assertIn(marker, corpora["woocommerce-plugin-dev"])
        for stale in (
            "PROJECT_BRIEF.md",
            "Uses PSR-4 autoloading via Composer",
            "Creates PHPUnit and Playwright test configuration files",
        ):
            self.assertNotIn(stale, corpora["woocommerce-plugin-dev"])
        self.assertIn("repository", corpora["woocommerce-plugin-dev"].lower())
        for marker in ("read-only", "Does not edit", "/code-review"):
            self.assertIn(marker, corpora["woocommerce-finalize"])
        for marker in (
            "stable monotonic cursor",
            "replay",
            "installed, licensed official source",
            "blocked/unknown",
            "Does not invoke this skill",
        ):
            self.assertIn(marker, corpora["woocommerce-upgrade-safety"])
        self.assertGreaterEqual(evidence_cases, 3)

    def test_evaluation_status_is_truthful(self):
        readme = read(ROOT / "README.md")
        status = read(ROOT / "docs/evaluation-status.md")
        combined = f"{readme}\n{status}"
        normalized_status = " ".join(status.split())

        self.assertIn("manual evaluation scenarios", readme.lower())
        self.assertNotIn("evaluation benchmarks", readme.lower())
        self.assertIn("official `skill-creator` plugin", status)
        self.assertIn("Claude Code 2.1.170", status)
        self.assertIn("source discovery and invocation", status)
        self.assertIn("have not been executed", normalized_status)
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
            'status="$(git status --porcelain=v1)"',
            'test -z "$status"',
            'git diff --check "$reviewed_base" "$candidate"',
            'release_diff="$(mktemp "${TMPDIR:-/tmp}/claude-woocommerce-toolkit.release.XXXXXX")"',
            'test "$release_diff_sha256" = "${REVIEWED_DIFF_SHA256:',
            "claude plugin tag --dry-run",
        ):
            self.assertIn(command, checklist)
        release_commands = re.search(
            r"```bash\n(.*?)\n```",
            checklist,
            re.DOTALL,
        ).group(1)
        syntax = subprocess.run(
            ["/bin/bash", "-n"],
            input=release_commands,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, syntax.returncode, syntax.stderr)
        self.assertTrue(release_commands.startswith("set -eu\n"))
        self.assertIn("REVIEWED_BASE", release_commands)
        self.assertIn("REVIEWED_DIFF_SHA256", release_commands)
        self.assertNotIn('test -z "$(git status', release_commands)
        for marker in (
            "copied-cache installation",
            "explicit approval",
            "repository settings",
            "tag",
            "release",
            "marketplace",
            "fake or sandbox providers",
            "claude-woocommerce-toolkit--v*",
        ):
            self.assertIn(marker, checklist)
        self.assertFalse((ROOT / ".github/workflows").exists())

    def test_repository_brand_and_urls_are_current(self):
        expected_name = "Agentic WooCommerce and WordPress toolkit"
        expected_display_name = "Agentic WooCommerce and WordPress Toolkit"
        expected_slug = "slash1andy/agentic-woocommerce-and-wordpress-toolkit"
        stale_slug = "slash1andy/" + "claude-woocommerce-toolkit"
        expected_description = (
            "Claude Code skills and a read-only UX agent for WordPress and WooCommerce plugin work."
        )
        readme = read(ROOT / "README.md")

        self.assertTrue(readme.startswith(f"# {expected_name}\n"))
        self.assertIn(
            "preserved `claude-woocommerce-toolkit` plugin namespace",
            " ".join(readme.split()),
        )
        plugin = json.loads(read(ROOT / ".claude-plugin/plugin.json"))
        self.assertEqual(f"https://github.com/{expected_slug}", plugin["repository"])
        marketplace = json.loads(read(ROOT / ".claude-plugin/marketplace.json"))
        self.assertEqual(expected_display_name, plugin["displayName"])
        self.assertEqual(expected_description, plugin["description"])
        self.assertEqual(expected_description, marketplace["description"])
        contributing = read(ROOT / "CONTRIBUTING.md")
        self.assertIn("## Voice and style", contributing)
        self.assertIn("Use sentence case for headings.", contributing)
        for path in ROOT.rglob("*"):
            if path.is_file() and ".git" not in path.parts and path.suffix in {".md", ".py", ".json"}:
                self.assertNotIn(stale_slug, read(path), str(path.relative_to(ROOT)))

    def test_contributor_source_checkout_smoke_path_is_documented(self):
        contributing = read(ROOT / "CONTRIBUTING.md")

        for marker in (
            "claude --plugin-dir .",
            "/reload-plugins",
            "/claude-woocommerce-toolkit:woocommerce-plugin-dev",
            "claude-woocommerce-toolkit:woocommerce-ux-reviewer",
        ):
            self.assertIn(marker, contributing)

    def test_ability_example_has_a_discoverable_output_contract(self):
        reference = read(
            ROOT / "skills/woocommerce-plugin-dev/references/abilities-and-mcp.md"
        )

        self.assertIn("developer preview", reference.lower())
        self.assertNotIn("order counts", reference)
        for field in ("store_name", "currency", "woocommerce_version"):
            self.assertGreaterEqual(reference.count(field), 2)

    def test_license_identifier_is_consistent(self):
        plugin = json.loads(read(ROOT / ".claude-plugin/plugin.json"))
        self.assertEqual("GPL-2.0-or-later", plugin["license"])
        self.assertIn("GPL-2.0-or-later", read(ROOT / "README.md"))
        self.assertIn("GPL-2.0-or-later", read(ROOT / "CONTRIBUTING.md"))
        self.assertIn("either version 2 of the License, or", read(ROOT / "LICENSE"))


if __name__ == "__main__":
    unittest.main()
