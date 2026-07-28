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

        self.assertNotIn("qit run:", text)
        self.assertNotIn("run:php-compatibility", text)
        self.assertNotIn("--php_version", text)
        self.assertIn("https://qit.woo.com/docs/llms.txt", text)
        self.assertIn("maintained QIT plugin and documentation", text)
        self.assertNotIn("Woo E2E / Woo API", text)
        self.assertNotIn("AI-assisted code disclosure", text)
        self.assertRegex(text, r"(?i)do(?:es)? not require.{0,80}AI-assistance disclosure")
        self.assertRegex(text, r"(?i)explicit approval.{0,120}(?:authenticate|upload|submit|publish)")

    def test_pr3_guidance_is_repository_first_and_risk_based(self):
        dev = read(DEV / "SKILL.md")
        coding = read(CODING)
        architecture = read(ARCHITECTURE)
        testing = read(TESTING)
        security = read(SECURITY)
        ux = read(UX)
        marketplace = read(MARKETPLACE)
        finalize = read(FINALIZE)
        upgrade = read(UPGRADE)

        self.assertRegex(
            dev,
            r"(?is)existing plugin.{0,300}inspect the repository.{0,300}ask only for blockers",
        )
        self.assertRegex(
            dev,
            r"(?is)new plugin.{0,400}unresolved high-impact.{0,600}exact save scope is approved",
        )
        self.assertRegex(
            dev,
            r"(?is)reuse existing Composer, npm, test, and static-analysis setup.{0,250}only when the requested behavior needs",
        )
        self.assertIn("smallest effective risk-based check", dev)
        self.assertRegex(
            coding,
            r"(?is)prefix global identifiers.{0,300}namespaced classes.{0,300}@throws only",
        )
        self.assertRegex(
            architecture,
            r"(?is)Blocks compatibility is conditional.{0,900}retain(?:ed)? plugin data by default.{0,300}explicit opt-in",
        )
        for marker in (
            "risk | smallest effective check",
            "HPOS enabled and disabled",
            "Classic and Blocks",
            "money precision",
            "replay/idempotency",
            "migration interruption/resume",
            "Store API session/cart",
            "official QIT plugin and documentation",
        ):
            self.assertIn(marker.lower(), testing.lower())
        self.assertRegex(
            security,
            r"(?is)`permission_callback` on every REST route.{0,400}cookie-authenticated REST mutations require a REST nonce.{0,400}Application Passwords, Basic Authentication, and OAuth do not use REST nonces",
        )
        self.assertRegex(
            security,
            r"(?is)capabilities do not replace CSRF protection.{0,300}nonce.{0,200}does not replace authentication",
        )
        self.assertRegex(
            security,
            r"(?is)Log event IDs, outcomes, and masked metadata.{0,120}never raw bodies or secrets",
        )
        self.assertRegex(
            ux,
            r"(?is)onboarding is optional.{0,400}prefer public APIs.{0,500}installed target version.{0,400}settings page or admin notice.{0,800}WCAG 2\.2 AA",
        )
        self.assertRegex(
            marketplace,
            r"(?is)shipped code cannot be payment-locked.{0,300}substantive external service may charge.{0,500}license-only validation",
        )
        self.assertIn("Generic correctness belongs in `/code-review`", finalize)
        self.assertIn("Use project configuration and evidence", finalize)
        self.assertRegex(
            finalize,
            r"(?is)Complexity is evidence-based.{0,300}configured analyzer finding",
        )
        self.assertRegex(
            upgrade,
            r"(?is)stable monotonic cursor or Action Scheduler.{0,300}committed progress.{0,500}concurrent-growth tests.{0,300}no skipped or duplicate",
        )
        self.assertRegex(
            upgrade,
            r"(?is)installed, licensed official source and version.{0,300}exact accepted arguments.{0,300}blocked/unknown",
        )
        self.assertRegex(
            upgrade,
            r"(?is)fake or sandbox providers.{0,120}never use live payments or customer data",
        )

        combined = "\n".join(
            (dev, coding, architecture, testing, security, ux, marketplace, finalize, upgrade)
        )
        self.assertNotRegex(
            combined,
            r"(?i)minimum PHP version: 8\.1|service container pattern|testing pyramid|within 12 hours|level 7|functions longer than 50 lines|batch processing with `LIMIT` \+ offset|major version bumps \(x\.0\.0\) start at high|WCAG 2\.[01] AA",
        )

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
        upgrade = read(UPGRADE)

        self.assertRegex(uninstall, r"(?i)retain(?:ed)? (?:plugin )?data by default")
        self.assertRegex(uninstall, r"(?i)explicit opt-in")
        self.assertNotIn("DELETE FROM", uninstall)
        self.assertNotIn("DROP TABLE", uninstall)
        self.assertNotRegex(
            uninstall,
            r"(?is)\b(?:delete|remove|purge)\b.{0,80}\b(?:without|before|regardless of)\b.{0,80}\b(?:opt-in|approval)\b",
        )
        self.assertRegex(security, r"(?i)password[- ]type fields do not encrypt")
        self.assertRegex(security, r"(?i)never render (?:a )?stored secret")
        self.assertRegex(security, r"(?i)environment|brokered secret")
        self.assertNotRegex(
            security,
            r"(?i)(?:REST )?nonces?\s+(?:are|is)\s+(?:optional|unnecessary)",
        )
        self.assertNotRegex(
            upgrade,
            r"(?is)(?<!never )(?<!do not )\b(?:prefer|use|test with)\b.{0,60}\b(?:live payments?|live providers?|customer data)\b",
        )
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
