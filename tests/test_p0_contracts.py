import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / "skills/woocommerce-plugin-dev"
ABILITIES = DEV / "references/abilities-and-mcp.md"
AGENTIC = DEV / "references/agentic-commerce.md"
APIS = DEV / "references/woocommerce-apis.md"
MARKETPLACE = DEV / "references/marketplace-submission.md"
ARCHITECTURE = DEV / "references/plugin-architecture.md"
CODING = DEV / "references/coding-standards.md"
SECURITY = DEV / "references/security.md"
TESTING = DEV / "references/testing.md"
UX = DEV / "references/ux-guidelines.md"
FINALIZE = ROOT / "skills/woocommerce-finalize/SKILL.md"
UPGRADE = ROOT / "skills/woocommerce-upgrade-safety/SKILL.md"
EVALS = DEV / "evals/evals.json"
INSTALLATION = ROOT / "docs/installation.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class P0ContractsTest(unittest.TestCase):
    def test_abilities_and_mcp_use_current_core_contract(self):
        text = read(ABILITIES)

        self.assertIn("wp_abilities_api_init", text)
        self.assertNotRegex(text, r"add_action\(\s*'abilities_api_init'")
        self.assertIn("'category'", text)
        self.assertIn("'woocommerce'", text)
        self.assertIn("meta.mcp.public", text)
        self.assertRegex(
            text,
            r"(?is)(?:deprecated.{0,300}woocommerce_mcp_include_ability|woocommerce_mcp_include_ability.{0,300}deprecated)",
        )

    def test_store_api_and_rest_auth_are_safe(self):
        store_text = "\n".join((read(DEV / "SKILL.md"), read(AGENTIC), read(APIS)))
        api_text = read(APIS)

        self.assertNotRegex(store_text, r"(?i)\b(?:stateless|sessionless)\b")
        self.assertRegex(api_text, r"(?i)cookie[- ](?:based )?(?:customer )?session")
        self.assertIn("Nonce", api_text)
        self.assertIn("Cart-Token", api_text)
        self.assertRegex(api_text, r"(?is)cookie-based customer session.{0,120}Nonce")
        self.assertIn("`Cart-Token` instead of cookies", api_text)
        self.assertRegex(api_text, r"Cart-Token requests do not\s+require a Nonce")
        self.assertNotRegex(
            api_text,
            r"https?://\S+\?[^\s)]*(?:consumer_key|consumer_secret)=",
        )
        self.assertIn("--netrc-file", api_text)
        self.assertNotIn("curl --user", api_text)
        self.assertRegex(api_text, r"(?i)outside (?:the )?repository")

    def test_json_values_are_validated_not_html_escaped(self):
        api_text = read(APIS)
        evals = json.loads(read(EVALS))["evals"]
        rest_eval = next(item for item in evals if item["id"] == 3)
        rest_contract = json.dumps(rest_eval)

        self.assertIn("Do not HTML-escape JSON values", api_text)
        self.assertIn("schema", rest_contract.lower())
        self.assertNotIn("escaping", rest_contract.lower())

    def test_qit_and_directory_guidance_are_current(self):
        text = read(MARKETPLACE)

        self.assertIn("qit run:phpcompatibility", text)
        self.assertNotIn("run:php-compatibility", text)
        self.assertNotIn("--php_version", text)
        self.assertIn("https://qit.woo.com/docs/llms.txt", text)
        self.assertNotIn("Woo E2E / Woo API", text)
        self.assertNotIn("AI-assisted code disclosure", text)
        self.assertRegex(text, r"(?i)do(?:es)? not require.{0,80}AI-assistance disclosure")
        self.assertRegex(text, r"(?i)explicit approval.{0,120}(?:authenticate|upload|submit|publish)")

    def test_pr3_guidance_is_repository_first_and_risk_based(self):
        required = {
            DEV / "SKILL.md": (
                "inspect the repository and its conventions first",
                "ask only for blockers",
                "keep the brief in chat until the exact save scope is approved",
                "reuse existing composer, npm, test, and static-analysis setup",
                "smallest effective risk-based check",
                "@throws only for exceptions the code can actually throw",
                "prefix global identifiers",
                "blocks compatibility only after implementation and tests",
            ),
            CODING: (
                "align syntax and tooling to the project's tested php floor",
                "follow the repository's established convention",
                "prefix global identifiers",
                "@throws only",
            ),
            ARCHITECTURE: (
                "blocks compatibility is conditional",
                "retained plugin data by default",
                "explicit opt-in",
            ),
            TESTING: (
                "risk | smallest effective check",
                "documented project commands",
                "one phpunit baseline only when",
                "hpos enabled and disabled",
                "classic and blocks",
                "money precision",
                "replay/idempotency",
                "migration interruption/resume",
                "store api session/cart",
                "official qit plugin and documentation",
            ),
            SECURITY: (
                "`permission_callback` on every rest route",
                "cookie-authenticated rest mutations require a rest nonce",
                "application passwords, basic authentication, and oauth do not use rest nonces",
                "capabilities do not replace csrf protection",
                "wc_get_logger()",
                "event ids, outcomes, and masked metadata",
                "never raw bodies or secrets",
            ),
            UX: (
                "onboarding is optional",
                "prefer public apis",
                "feature-detect",
                "installed target version",
                "settings page or admin notice",
                "wcag 2.2 aa",
            ),
            MARKETPLACE: (
                "maintained qit plugin and documentation",
                "shipped code cannot be payment-locked",
                "substantive external service may charge",
                "license-only validation",
                "wcag 2.2 aa",
            ),
            FINALIZE: (
                "project configuration and evidence",
                "generic correctness belongs in `/code-review`",
                "woo traceability and code health",
            ),
            UPGRADE: (
                "stable monotonic cursor or action scheduler",
                "committed progress",
                "idempotency, replay, interruption-resume, and concurrent-growth tests",
                "no skipped or duplicate records",
                "installed, licensed official source and version",
                "exact accepted arguments",
                "blocked/unknown",
                "fake or sandbox providers",
                "actual change surface",
            ),
        }
        forbidden = {
            DEV / "SKILL.md": (
                "minimum php version: 8.1",
                "every woocommerce plugin follows this canonical structure",
                "level 6+ minimum",
            ),
            CODING: (
                "wpcs 3.3.0+",
                '"php": ">=8.1"',
                "never use `use function`",
            ),
            ARCHITECTURE: (
                "service container pattern",
                "wordpress is on the 7.x line",
                "all new plugins must declare compatibility",
            ),
            TESTING: (
                "testing pyramid",
                '"@playwright/test": "^1.60"',
                "overall:** aim for 80%+",
                "--level 6",
            ),
            SECURITY: (
                "use `permission_callback` with capability checks instead of nonces",
                "all api requests and responses",
            ),
            UX: ("onboardingtasks", "tasklists::add_task", "wcag 2.0 aa"),
            MARKETPLACE: ("wcag 2.1 aa baseline",),
            FINALIZE: (
                "within 12 hours",
                "level 7",
                "functions longer than 50 lines",
                "nesting deeper than 3 levels",
                "| issue | level |",
            ),
            UPGRADE: (
                "batch processing with `limit` + offset",
                "major version bumps (x.0.0) start at high",
            ),
        }

        for path, markers in required.items():
            text = read(path).lower()
            for marker in markers:
                with self.subTest(path=path, required=marker):
                    self.assertIn(marker.lower(), text)
        for path, markers in forbidden.items():
            text = read(path).lower()
            for marker in markers:
                with self.subTest(path=path, forbidden=marker):
                    self.assertNotIn(marker.lower(), text)

    def test_skills_are_explicit_and_read_only_by_default(self):
        skill_paths = (
            DEV / "SKILL.md",
            ROOT / "skills/woocommerce-finalize/SKILL.md",
            ROOT / "skills/woocommerce-upgrade-safety/SKILL.md",
        )
        for path in skill_paths:
            with self.subTest(path=path):
                frontmatter = read(path).split("---", 2)[1]
                self.assertIn("disable-model-invocation: true", frontmatter)

        dev_text = read(DEV / "SKILL.md").lower()
        for marker in ("untrusted data", "repository", "web", "tool output", "preview", "explicit approval"):
            self.assertIn(marker, dev_text)

        for path in skill_paths[1:]:
            with self.subTest(path=path):
                text = read(path).lower()
                self.assertIn("read-only", text)
                self.assertIn("do not edit", text)
                self.assertIn("findings in chat", text)
                self.assertIn("untrusted data", text)
                self.assertIn("cannot expand tool scope", text)

        usage = "\n".join((read(ROOT / "README.md"), read(INSTALLATION)))
        self.assertIn("/claude-woocommerce-toolkit:woocommerce-plugin-dev", usage)
        self.assertNotRegex(
            usage,
            r"(?i)(?:agent|skill).{0,40}(?:trigger(?:s|ed)?|invoked) automatically|automatically (?:trigger(?:s|ed)?|invoked)",
        )

    def test_cross_skill_reference_routes_exist(self):
        expected = {
            ROOT / "skills/woocommerce-finalize/SKILL.md": (
                "coding-standards.md",
                "security.md",
                "woocommerce-apis.md",
                "ux-guidelines.md",
            ),
            ROOT / "skills/woocommerce-upgrade-safety/SKILL.md": (
                "woocommerce-apis.md",
                "security.md",
                "plugin-architecture.md",
            ),
        }
        for skill, names in expected.items():
            text = read(skill)
            for name in names:
                with self.subTest(skill=skill, reference=name):
                    route = f"${{CLAUDE_SKILL_DIR}}/../woocommerce-plugin-dev/references/{name}"
                    self.assertIn(route, text)
                    self.assertTrue((skill.parent / "../woocommerce-plugin-dev/references" / name).is_file())

    def test_uninstall_and_secret_guidance_are_safe(self):
        architecture = read(ARCHITECTURE)
        uninstall = architecture.split("## Uninstall Handler", 1)[1].split("\n---", 1)[0]
        security = read(SECURITY)
        abilities = read(ABILITIES)

        self.assertRegex(uninstall, r"(?i)retain(?:ed)? (?:plugin )?data by default")
        self.assertRegex(uninstall, r"(?i)explicit opt-in")
        self.assertNotIn("DELETE FROM", uninstall)
        self.assertNotIn("DROP TABLE", uninstall)
        self.assertRegex(security, r"(?i)password[- ]type fields do not encrypt")
        self.assertRegex(security, r"(?i)never render (?:a )?stored secret")
        self.assertRegex(security, r"(?i)environment|brokered secret")
        self.assertNotIn("--user=admin", abilities)
        self.assertRegex(abilities, r"(?i)dedicated.{0,80}least-privilege")

    def test_eval_contract_and_readme_count_match(self):
        data = json.loads(read(EVALS))
        ability_eval = next(item for item in data["evals"] if item["id"] == 4)
        ability_contract = json.dumps(ability_eval)

        self.assertEqual(4, len(data["evals"]))
        self.assertIn("4 test scenarios", read(ROOT / "README.md"))
        self.assertIn("wp_abilities_api_init", ability_contract)
        self.assertIn("meta.mcp.public", ability_contract)
        self.assertRegex(
            ability_contract,
            r"(?i)woocommerce_mcp_include_ability.{0,120}deprecated",
        )

    def test_named_canonical_sources_are_current(self):
        self.assertIn("https://developer.wordpress.org/apis/abilities-api/", read(ABILITIES))
        self.assertNotIn("make.wordpress.org/ai/handbook/projects/abilities-api", read(ABILITIES))
        self.assertIn("https://developer.woocommerce.com/docs/apis/store-api/", read(AGENTIC))
        self.assertIn(
            "https://developer.woocommerce.com/docs/block-development/tutorials/how-to-additional-checkout-fields-guide/",
            read(APIS),
        )
        self.assertIn(
            "https://make.wordpress.org/core/handbook/testing/automated-testing/writing-phpunit-tests/",
            read(TESTING),
        )
        self.assertNotIn("plugins/woocommerce/tests/e2e-pw", read(TESTING))
        self.assertIn(
            "https://developer.woocommerce.com/docs/features/orders/high-performance-order-storage/recipe-book/",
            read(APIS),
        )


if __name__ == "__main__":
    unittest.main()
