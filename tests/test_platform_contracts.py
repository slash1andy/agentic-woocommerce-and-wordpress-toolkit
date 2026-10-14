"""Platform-contract regressions for the WordPress 7.1 / MCP Adapter 0.7 / WooCommerce 11.1-11.2 refresh.

Wording checks (paragraph-level needles over packaged Markdown) and fixture/eval-shape checks are
STRUCTURAL: they prove the guidance and scenarios exist and are version-scoped. They are not proof
that any model or harness behaves correctly; behavior evidence comes only from paired runs.

Source data: official WordPress/WooCommerce release notes dated 2026-10-07/08.
"""

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
DEV = SKILLS / "woocommerce-plugin-dev"
ABILITIES = DEV / "references/abilities-and-mcp.md"
MIGRATION_GUIDE = "https://github.com/WordPress/mcp-adapter/blob/v0.7.0/docs/migration/v0.7.0.md"
MAINTENANCE = ROOT / "docs/maintenance-and-evaluation.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_evals(skill: str) -> list:
    return json.loads(read(SKILLS / skill / "evals/evals.json"))["evals"]


def scenario_text(scenario: dict) -> str:
    return json.dumps(scenario).lower()


def packaged_markdown() -> str:
    paths = sorted(SKILLS.rglob("*.md")) + sorted((ROOT / "docs").glob("*.md")) + [ROOT / "README.md"]
    return "\n\n".join(read(path) for path in paths if path.name != MAINTENANCE.name)


def paragraphs(text: str) -> list:
    return [" ".join(chunk.split()).lower() for chunk in re.split(r"\n\s*\n", text)]


class PlatformGuidanceStructuralTest(unittest.TestCase):
    """STRUCTURAL: guidance wording and version scoping, not behavior proof."""

    def assertParagraph(self, text, all_of, any_of=()):
        needles = [item.lower() for item in all_of]
        options = [item.lower() for item in any_of]
        for paragraph in paragraphs(text):
            if all(item in paragraph for item in needles) and (
                not options or any(item in paragraph for item in options)
            ):
                return
        self.fail(f"no single paragraph contains {all_of} and one of {any_of or '(n/a)'}")

    def test_wp71_public_is_a_default_and_explicit_channel_false_is_retained(self):
        text = read(ABILITIES)

        self.assertParagraph(text, ["meta.public", "WordPress 7.1", "show_in_rest"], ["default"])
        self.assertParagraph(
            text,
            ["explicit", "show_in_rest", "false"],
            ["wins", "precedence", "authoritative", "retained", "overrides"],
        )
        self.assertParagraph(text, ["meta.mcp.public"], ["before wordpress 7.1", "earlier than", "prior to"])

    def test_exposure_flags_never_replace_permission_callback(self):
        self.assertParagraph(
            read(ABILITIES),
            ["meta.public", "permission_callback"],
            ["not authorization", "not authorisation", "does not replace", "not a security boundary"],
        )

    def test_ability_validation_hooks_and_schema_callbacks_are_distinguished(self):
        text = read(ABILITIES)

        self.assertIn("wp_ability_validate_input", text)
        self.assertIn("wp_ability_validate_output", text)
        self.assertParagraph(
            text,
            ["validate_callback", "sanitize_callback"],
            ["not executed", "not runtime validation", "do not run"],
        )

    def test_canonical_server_schema_is_kept_and_client_copy_is_prepared(self):
        self.assertParagraph(
            read(ABILITIES),
            ["wp_prepare_json_schema_for_client", "canonical"],
            ["copy", "do not replace"],
        )

    def test_mcp_adapter_07_guidance_is_optional_canonical_and_not_destructive(self):
        text = read(ABILITIES)

        self.assertParagraph(text, ["0.7", "canonical", "plugin"], ["optional"])
        self.assertParagraph(text, ["^0.3.0", "woocommerce", "bundled"], ["do not", "not blindly", "verify"])
        self.assertIn(MIGRATION_GUIDE, text)
        self.assertNotRegex(
            text,
            r"(?i)\b(?:rm\s+-[a-z]*r|composer\s+(?:remove|update)|wp\s+plugin\s+(?:deactivate|delete|uninstall)"
            r"|git\s+(?:reset\s+--hard|clean)|--force)\b",
        )
        for paragraph in paragraphs(text):
            if "jetpack autoloader" in paragraph:
                self.assertTrue(
                    any(word in paragraph for word in ("legacy", "bundled", "before 0.7", "deprecated")),
                    paragraph,
                )

    def test_woo112_cart_date_and_removal_contracts_are_version_scoped(self):
        text = packaged_markdown()

        self.assertParagraph(text, ["11.2", "Cart-Token", "missing", "unavailable", "new cart"])
        self.assertParagraph(text, ["11.2", "timezone", "HPOS", "legacy"], ["wc_get_orders", "date"])
        for path in (SKILLS / "woocommerce-upgrade-safety/SKILL.md", DEV / "references/woocommerce-apis.md"):
            with self.subTest(date_uncertainty=str(path.relative_to(ROOT))):
                scoped = read(path)
                self.assertParagraph(scoped, ["legacy", "date-only"], ["retained", "retain", "remains", "keep", "kept"])
                self.assertParagraph(
                    scoped,
                    ["hpos", "utc"],
                    ["not prove", "does not prove", "doesn't prove", "no proof"],
                )
                self.assertParagraph(scoped, ["unverified"], ["versioned source", "boundary test"])
                self.assertParagraph(scoped, ["boundary test"], ["versioned source"])
                claim = re.compile(r"\b(?:differ\w*|diverg\w*|utc)\b")
                evidence = re.compile(
                    r"unverified|not prove|does not prove|versioned source|boundary test|until|without|if |when "
                )
                candidates = paragraphs(scoped) + [
                    " ".join(line.lower().split())
                    for line in scoped.splitlines()
                    if line.startswith("#") or line.lower().startswith(("summary", "tl;dr", "- **summary"))
                ]
                for candidate in candidates:
                    if "date" in candidate and "hpos" in candidate and claim.search(candidate):
                        self.assertRegex(candidate, evidence, candidate)
        self.assertParagraph(text, ["11.2", "wc/agentic/v1", "removed", "no replacement"])
        self.assertParagraph(text, ["11.2", "wc_email_unsubscribes"], ["recovery", "abandoned"])
        for paragraph in paragraphs(text):
            if "wc/agentic/v1" in paragraph:
                self.assertRegex(paragraph, r"removed|no longer|not available", paragraph)

    def test_woo111_data_store_and_block_registration_guards(self):
        text = packaged_markdown()

        self.assertParagraph(text, ["11.1", "woocommerce_should_register_blocks"], ["rest", "store api", "non-rendering"])
        self.assertParagraph(text, ["11.1", "get_item_ids", "delete_items_by_ids"], ["data store"])

    def test_security_and_scheduling_advisories_are_scoped_to_affected_surfaces(self):
        text = packaged_markdown()
        scope_words = ("if ", "when ", "only ")

        for needles in (
            ["11.2", "download", "malformed"],
            ["11.2", "woocommerce_shop_manager_editable_roles"],
            ["11.2", "multisite", "blueprint", "super admin"],
            ["11.2", "cc", "bcc", "reset password"],
            ["11.2", "action scheduler", "load order"],
        ):
            with self.subTest(needles=needles):
                self.assertParagraph(text, needles, scope_words)

    def test_released_versus_preview_and_unreleased_are_not_blurred(self):
        text = packaged_markdown()

        self.assertParagraph(text, ["settings ui", "experimental", "opt-in"])
        self.assertParagraph(text, ["developer preview", "mcp"])
        self.assertParagraph(text, ["wordpress 7.2"], ["not released", "unreleased"])
        for paragraph in paragraphs(text):
            if "wordpress 7.2" in paragraph:
                self.assertRegex(paragraph, r"not released|unreleased|beta|watch", paragraph)

    def test_no_global_platform_floor_raise(self):
        text = packaged_markdown()

        self.assertParagraph(text, ["do not raise", "minimum"], ["wordpress", "woocommerce"])
        manifest_headers = re.compile(
            r"(?im)^\s*\*?\s*(?:Requires at least|WC requires at least)\s*:\s*(?:7\.[1-9]|11\.\d)"
        )
        for path in list(SKILLS.rglob("*.php")) + list(SKILLS.rglob("*.md")):
            self.assertNotRegex(read(path), manifest_headers, str(path.relative_to(ROOT)))
        fixture = read(DEV / "evals/fixtures/existing-plugin.php")
        self.assertIn("WC requires at least: 8.0", fixture)
        self.assertIn("Requires PHP: 7.4", fixture)


class NativeEvaluationGapGuidanceTest(unittest.TestCase):
    """STRUCTURAL: governing SKILL.md wording for gaps seen in real native evaluation runs."""

    assertParagraph = PlatformGuidanceStructuralTest.assertParagraph

    def test_finalize_requires_provider_and_amount_verification_on_every_mutation_entrypoint(self):
        text = read(SKILLS / "woocommerce-finalize/SKILL.md")

        self.assertParagraph(
            text, ["every mutation entrypoint", "provider confirmation", "amount", "currency"], ["separate"]
        )
        self.assertParagraph(text, ["source-proven", "status", "replay"], ["guess", "inferred", "assumed"])
        self.assertParagraph(text, ["postimage", "symbol", "diff"], ["invent", "fabricat"])
        self.assertParagraph(
            text,
            ["synthetic", "boundary", "provider", "distributed", "classic", "blocks", "hpos"],
            ["exclude", "not verified", "out of scope"],
        )

    def test_finalize_payment_safeguards_and_negative_tests_are_scoped_to_applicable_entrypoints(self):
        text = read(SKILLS / "woocommerce-finalize/SKILL.md")

        self.assertParagraph(
            text,
            ["payment-affecting", "entrypoint", "provider", "amount", "currency", "replay"],
            ["applicable", "applies"],
        )
        self.assertParagraph(
            text,
            ["settings", "product", "payment-affecting"],
            ["not require", "do not require", "does not require", "unrelated"],
        )
        self.assertParagraph(
            text,
            ["negative", "applicable", "payment-affecting", "entrypoint"],
            ["map", "mapping"],
        )

    def test_finalize_citation_requires_supplied_numbered_line_anchors_with_honest_fallback(self):
        text = read(SKILLS / "woocommerce-finalize/SKILL.md")
        required = (
            r"\bcite\b",
            r"\bdiff\b",
            r"numbered|line numbers? (?:that )?(?:are )?(?:supplied|provided|available|shown)",
            r"\bfile\b.{0,80}\bline\b|\bline\b.{0,80}\bfile\b",
            r"\bsymbols?\b",
            r"\bhunk\b",
            r"supplement|in addition|alongside|not (?:a )?(?:replace|substitute)\w*|rather than replac\w+",
            r"(?:not|un)\s?available|absent|missing|not (?:supplied|provided|shown)|without",
            r"\b(?:invent|fabricat)\w*",
            r"post-?image",
        )
        for paragraph in paragraphs(text):
            if "cite" in paragraph and "hunk" in paragraph:
                for pattern in required:
                    with self.subTest(pattern=pattern):
                        self.assertRegex(paragraph, pattern)
                return
        self.fail("no finalize citation paragraph mentions cite and hunk")

    def test_finalize_and_upgrade_state_callback_auth_and_checkpoint_qualifications(self):
        finalize = read(SKILLS / "woocommerce-finalize/SKILL.md")
        upgrade = read(SKILLS / "woocommerce-upgrade-safety/SKILL.md")

        self.assertParagraph(
            finalize,
            ["nonce", "capability", "external", "provider", "callback", "inappropriate", "impossible"],
            ["not the same", "distinguish", "rather than", "instead of"],
        )
        self.assertParagraph(
            finalize,
            ["provider", "callback", "authentication", "nonce"],
            ["substitut", "not a replacement", "does not replace", "cannot replace"],
        )

        self.assertParagraph(
            upgrade,
            ["checkpoint", "crash", "window", "migration", "idempotency", "order", "visibility", "concurrency"],
            ["not overall", "does not prove", "not prove", "not establish", "does not establish"],
        )
        self.assertParagraph(
            upgrade,
            ["insertion", "overlap", "new", "before", "cursor", "unvisited", "existing rows"],
            ["even when", "even if", "even where"],
        )
        self.assertParagraph(
            upgrade,
            ["closed", "growing", "population"],
            ["distinguish", "separate", "whether"],
        )
        self.assertParagraph(
            upgrade,
            ["heading", "summar", "same", "evidence", "body"],
            ["qualif", "caveat", "limit"],
        )

        self.assertParagraph(
            finalize,
            ["missing", "explicit", "callback", "response", "provider", "retry"],
            ["does not establish", "not establish", "does not prove", "not prove"],
        )
        self.assertParagraph(
            finalize,
            ["provider", "contract", "outcome", "evidence"],
            ["require", "actual"],
        )
        self.assertParagraph(
            finalize,
            ["rest", "response", "construction", "readback", "getter", "core", "side"],
            ["independent", "unverified"],
        )
        self.assertParagraph(
            upgrade,
            ["lost", "checkpoint", "unmigrated", "rows", "identif"],
            ["does not mean", "not mean", "does not imply", "not imply"],
        )
        self.assertParagraph(
            upgrade,
            ["durable", "per-record", "migration", "marker", "candidate", "reconcil", "recovery"],
            ["inspect", "before"],
        )
        self.assertParagraph(
            upgrade,
            ["marker", "presence", "exactly-once"],
            ["not proof", "does not prove", "not prove", "not establish", "does not establish"],
        )
        self.assertParagraph(
            upgrade,
            ["continuation", "skip", "permanent", "loss", "retry", "reconcil", "reset"],
            ["does not prove", "not prove", "does not establish", "not establish", "does not mean", "not mean"],
        )
        self.assertParagraph(
            upgrade,
            ["permanent", "loss", "actual", "proof"],
            ["allow", "may conclude", "can conclude", "when", "if"],
        )
        self.assertParagraph(
            upgrade,
            ["repeated", "save", "side effect", "installed version", "source", "run evidence"],
            ["does not prove", "not prove", "does not establish", "not establish", "without"],
        )
        self.assertParagraph(
            upgrade,
            ["side effect", "actual", "installed version", "source", "run evidence"],
            ["may conclude", "can conclude", "allow", "when", "if"],
        )

    def test_audit_skills_state_evidence_limits_and_finalize_maps_payment_test_gaps(self):
        finalize = read(SKILLS / "woocommerce-finalize/SKILL.md")
        upgrade = read(SKILLS / "woocommerce-upgrade-safety/SKILL.md")

        for name, text in (("finalize", finalize), ("upgrade-safety", upgrade)):
            with self.subTest(skill=name):
                self.assertParagraph(text, ["tests", "pass"], ["reading", "read the test", "static"])
                self.assertParagraph(
                    text, ["absent", "source", "unknown"], ["migration", "contract"]
                )
                self.assertParagraph(
                    text,
                    ["pagination", "concurrency", "trace"],
                    ["insertion", "overlap"],
                )
                self.assertParagraph(
                    text,
                    ["skipp", "duplicat", "current page", "later page"],
                    ["distinguish", "separate"],
                )
                self.assertParagraph(
                    text,
                    ["order", "save", "version", "source"],
                    ["run evidence", "executed", "observed"],
                )
                self.assertParagraph(text, ["order", "save", "webhook", "date"], ["unconditional", "without"])

        self.assertParagraph(
            finalize,
            ["authorization", "provider", "amount", "currency", "replay", "negative", "repeated"],
            ["missing test", "test evidence", "no test", "gap"],
        )
        self.assertParagraph(finalize, ["404", "test"], ["only", "broken", "failing"])
        self.assertParagraph(
            finalize,
            ["coverage", "run evidence", "absent", "failing", "broken", "skipped", "unverified"],
            ["inspect", "classify"],
        )
        self.assertParagraph(
            finalize,
            ["coverage", "run evidence", "passing", "scope"],
            ["verified", "established", "supported"],
        )
        self.assertParagraph(
            finalize,
            ["missing guard", "404", "coverage"],
            ["do not infer", "not infer", "cannot establish", "does not establish", "never infer"],
        )

    def test_testing_new_project_baseline_keeps_manual_default_for_small_changes(self):
        text = read(DEV / "references/testing.md")
        section = text.split("## New projects", 1)[1].split("\n## ", 1)[0]

        self.assertParagraph(
            section,
            ["small", "no test runner", "manual", "ad-hoc"],
            ["default", "keep"],
        )
        self.assertParagraph(
            section,
            ["phpunit", "behavior", "request", "smaller check", "inadequate"],
            ["only", "add"],
        )

    def test_plugin_dev_headers_rest_schema_and_real_integration_guidance(self):
        text = read(DEV / "SKILL.md")

        self.assertParagraph(
            text,
            ["main-file", "headers", "wordpress", "php", "woocommerce", "dependenc"],
            ["resolve", "report"],
        )
        self.assertParagraph(text, ["rest", "parameter", "schema", "positive", "bound"], ["coerc"])
        self.assertParagraph(text, ["rest", "checkout", "integration", "stub"], ["real"])
        self.assertParagraph(
            text,
            ["abilities", "meta.public", "wordpress 7.1", "false", "null", "floor"],
            ["default"],
        )

    def test_plugin_dev_distinguishes_schema_integer_validation_from_raw_canonical_id_strings(self):
        text = read(DEV / "SKILL.md")

        self.assertParagraph(
            text,
            ["rest_is_integer", "minimum", "raw", "canonical", "decimal", "string", "before sanitiz"],
            ["numeric", "integral"],
        )
        self.assertParagraph(
            text,
            ["raw", "canonical", "decimal", "string", "id", "positive"],
            ["scientific notation", "exponent"],
        )
        self.assertParagraph(
            text,
            ["raw", "canonical", "decimal", "string", "decimals", "signs", "coerc"],
            ["reject"],
        )
        self.assertParagraph(
            text,
            ["decoded", "json", "positive", "integer"],
            ["do not reject", "still valid", "remain valid", "accept"],
        )
        self.assertParagraph(text, ["schema", "type", "integer", "minimum"], ["keep", "retain", "still"])
        self.assertParagraph(text, ["request boundary", "raw", "string"], ["check", "validate"])

        self.assertIn(r"\A[1-9][0-9]*\z", text)
        for match in re.finditer(re.escape("[1-9][0-9]*"), text):
            self.assertEqual(
                r"\A", text[max(0, match.start() - 2) : match.start()], "canonical ID pattern must be anchored"
            )
            self.assertEqual(r"\z", text[match.end() : match.end() + 2], "canonical ID pattern must be end-anchored")
        self.assertParagraph(
            text,
            [r"\A[1-9][0-9]*\z", "full-string", "raw", "before", "coerc"],
            ["match"],
        )
        self.assertParagraph(
            text,
            [r"\A[1-9][0-9]*\z", "1e3", "+1", "1.0"],
            ["reject"],
        )
        self.assertParagraph(text, [r"\A[1-9][0-9]*\z", "supported", "integer", "range"])

    def test_native_rest_testing_guidance_covers_auth_hook_and_canonical_discovery(self):
        skill = read(DEV / "SKILL.md")
        testing = read(DEV / "references/testing.md")
        singular = "application_password_is_api_request"
        plural = "application_passwords_is_api_request"

        self.assertParagraph(skill, ["native rest", "testing.md"], ["read", "must", "before"])
        self.assertParagraph(testing, [singular], ["authenticat", "application password"])
        for name, text in (("SKILL.md", skill), ("testing.md", testing)):
            for paragraph in paragraphs(text):
                if plural in paragraph:
                    with self.subTest(file=name):
                        self.assertTrue(
                            any(word in paragraph for word in ("do not", "incorrect", "wrong", "erroneous", "never")),
                            paragraph,
                        )
        self.assertParagraph(testing, [plural], ["do not", "incorrect", "wrong", "erroneous", "never"])
        self.assertParagraph(
            testing,
            ["native", "authenticat", "application password"],
            ["without replacing", "do not replace", "not replace", "do not bypass", "do not stub"],
        )
        self.assertParagraph(
            testing,
            ["phpunit", "canonical", "discovery", "hpos", "legacy"],
            ["both", "every", "all intended"],
        )
        self.assertParagraph(
            testing,
            ["supplemental", "class", "canonical coverage"],
            ["not", "does not", "never"],
        )
        self.assertParagraph(
            testing,
            ["hpos", "legacy", "fresh", "isolated", "database", "fixture", "crud", "cleanup", "before", "switch"],
            ["storage mode", "storage-mode"],
        )
        self.assertParagraph(
            testing,
            ["synchronization", "guard", "hpos", "legacy"],
            ["retain", "keep", "preserve"],
        )
        self.assertParagraph(
            testing,
            ["synchronization", "guard", "green"],
            ["never bypass", "do not bypass", "must not bypass", "never disable", "do not disable"],
        )

    def test_removed_endpoint_recovery_options_are_distinguished_and_unverified_by_default(self):
        text = read(SKILLS / "woocommerce-upgrade-safety/SKILL.md")

        self.assertParagraph(
            text,
            ["removed", "no replacement", "rollback", "backup", "verified", "mitigation", "fail-closed"],
            ["not the only", "not only", "do not conclude", "does not mean", "never conclude"],
        )
        self.assertParagraph(
            text,
            ["rollback", "backup", "mitigation", "disable", "supported flow", "designed"],
            ["separate", "distinct", "distinguish"],
        )
        self.assertParagraph(
            text,
            ["rollback", "dropped data", "unverified"],
            ["does not restore", "do not restore", "cannot restore", "not restore"],
        )


class SharedGuidanceGapStructuralTest(unittest.TestCase):
    """STRUCTURAL: concept-level wording for three shared guidance gaps; not behavior proof."""

    def assertParagraphMatches(self, text, *patterns):
        for paragraph in paragraphs(text):
            if all(re.search(pattern, paragraph) for pattern in patterns):
                return
        self.fail(f"no single paragraph matches all of {patterns}")

    def test_finalize_payment_complete_call_is_not_paid_outcome_and_missing_notes_need_qualifiers(self):
        text = read(SKILLS / "woocommerce-finalize/SKILL.md")

        self.assertParagraphMatches(
            text,
            r"payment_complete",
            r"authori[sz]ed|unauthenticated|untrusted|any caller|a caller",
            r"\b(?:invok\w*|call\w*|reach\w*)\b",
            r"not (?:confirm|prove|establish|mean)\w*|does not (?:confirm|prove|establish|mean)|neither",
            r"\b(?:order )?(?:is |as |being )?paid\b",
        )
        self.assertParagraphMatches(
            text,
            r"payment_complete",
            r"order notes?|audit notes?",
            r"\bcore\b",
            r"\b(?:absence|missing|no explicit|without an explicit|not (?:prove|establish))\b",
            r"failure[- ]mode",
            r"\bimpact\b",
            r"qualif",
        )

    def test_plugin_dev_approved_files_are_not_blanket_feature_approval(self):
        text = read(DEV / "SKILL.md")

        self.assertParagraphMatches(
            text,
            r"approved (?:files?|scope|write scope)",
            r"not (?:a )?(?:blanket )?(?:feature|approval)|blanket",
            r"reconcil\w+",
            r"merchant[- ]facing|merchant",
            r"settings?",
            r"form[- ]?fields?|fields?",
            r"feature",
        )
        self.assertParagraphMatches(
            text,
            r"reconcil\w+",
            r"title",
            r"native|default",
            r"approv\w+",
            r"constant|fixed|hard-?coded",
            r"label",
        )

    def test_abilities_reference_states_runtime_input_output_validation_with_qualification(self):
        text = read(ABILITIES)

        self.assertNotRegex(text.lower(), r"contract for discovery|discovery[- ]only")
        self.assertParagraphMatches(
            text,
            r"input_schema",
            r"output_schema",
            r"\bnormal\b",
            r"\bruntime\b",
            r"input.{0,160}before.{0,40}(?:execute_)?callback|before.{0,40}(?:execute_)?callback.{0,160}input",
            r"output.{0,160}before.{0,40}(?:return|returned)|before.{0,40}return.{0,160}output",
            r"supplement|in addition|additional",
            r"validate_callback.{0,120}(?:not (?:run|executed)|do not run)|(?:not (?:run|executed)|do not run).{0,120}validate_callback",
        )
        self.assertParagraphMatches(
            text,
            r"wp_pre_execute_ability",
            r"7\.1\.3",
            r"short[- ]?circuit",
            r"not (?:every|all|any) path|normal path|qualif|only (?:the )?normal",
        )

    def test_finalize_routes_out_of_scope_review_before_audit_boundary_even_without_inputs(self):
        text = read(SKILLS / "woocommerce-finalize/SKILL.md")
        self.assertIn("\n## Audit boundary", text)
        self.assertIn("\n## 1. Establish evidence", text)
        opening = text.split("\n## Audit boundary", 1)[0]

        self.assertParagraphMatches(
            opening,
            r"generic correctness",
            r"/code-review",
            r"security",
            r"\bux\b",
            r"dedicated",
            r"\b(?:route|routes|routing|refer|refers|referral|redirect\w*)\b",
            r"(?:even if|even when|regardless).{0,80}(?:missing|absent|not (?:supplied|provided)|unavailable)",
            r"plugin",
            r"diff",
            r"(?:do not|never) offer",
            r"yourself",
        )


class PlatformScenarioStructuralTest(unittest.TestCase):
    """STRUCTURAL: scenario shape and fixture oracle sanity; execution needs a paired run."""

    def test_existing_mcp_scenario_is_version_aware_with_channel_override(self):
        scenario = next(item for item in load_evals("woocommerce-plugin-dev") if item["id"] == 4)
        text = scenario_text(scenario)

        self.assertIn("meta.public", text)
        self.assertIn("meta.mcp.public", text)
        self.assertRegex(text, r"7\.1.{0,400}meta\.public|meta\.public.{0,400}7\.1")
        self.assertRegex(text, r"explicit.{0,120}(?:channel|show_in_rest).{0,120}false|false.{0,120}(?:override|retain)")
        self.assertIn("permission_callback", text)

    def test_at_most_three_new_scenarios_were_added(self):
        baseline = {"woocommerce-plugin-dev": 5, "woocommerce-finalize": 3, "woocommerce-upgrade-safety": 4}
        counts = {skill: len(load_evals(skill)) for skill in baseline}

        for skill, base in baseline.items():
            self.assertEqual(base + 1, counts[skill], skill)
        self.assertEqual(15, sum(counts.values()))

    def test_wp71_exposure_and_validation_boundary_scenario(self):
        cases = [
            item for item in load_evals("woocommerce-plugin-dev")
            if item["id"] != 4 and "wp_ability_validate_input" in scenario_text(item)
        ]
        self.assertEqual(1, len(cases))
        text = scenario_text(cases[0])
        for marker in (
            "show_in_rest",
            "permission_callback",
            "wp_ability_validate_output",
            "validate_callback",
            "canonical",
            "wp_prepare_json_schema_for_client",
        ):
            self.assertIn(marker, text)
        self.assertRegex(text, r"explicit.{0,160}false")

    def test_woo112_removed_cart_and_date_scenario(self):
        cases = [
            item for item in load_evals("woocommerce-upgrade-safety")
            if "wc/agentic/v1" in scenario_text(item)
        ]
        self.assertEqual(1, len(cases))
        text = scenario_text(cases[0])
        for marker in ("cart-token", "timezone", "hpos", "legacy", "wc_email_unsubscribes", "no replacement"):
            self.assertIn(marker, text)
        self.assertRegex(text, r"missing.{0,200}(?:unavailable|fail)")
        self.assertRegex(text, r"(?:do not|does not|no).{0,80}(?:raise|global).{0,80}(?:minimum|floor)")

    def test_finalize_planted_defect_oracle_scores_recall_and_false_positives(self):
        scenarios = [
            item for item in load_evals("woocommerce-finalize")
            if "checkout-payment-release.diff" in json.dumps(item["files"])
        ]
        oracle = " ".join(scenario_text(item) for item in scenarios)

        for name, pattern in {
            "unauthenticated callback": r"callback.{0,120}(?:signature|authenticat)",
            "no amount or currency verification": r"amount.{0,60}currency|currency.{0,60}amount",
            "replay or duplicate delivery": r"replay|idempoten|duplicate",
            "payment_complete without provider proof": r"payment_complete",
            "tests cover only the 404 path": r"404|only.{0,40}missing.{0,20}order",
            "recall": r"recall",
            "false positives": r"false.positive",
            "no false verified claims": r"(?:incorrect|false).{0,30}verified",
        }.items():
            with self.subTest(oracle=name):
                self.assertRegex(oracle, pattern)

    def test_planted_defect_fixture_lacks_the_safeguards_the_oracle_names(self):
        diff = read(SKILLS / "woocommerce-finalize/evals/fixtures/checkout-payment-release.diff")

        self.assertIn("->payment_complete()", diff)
        self.assertIn("update_status('processing')", diff)
        self.assertIn("$_POST", diff)
        for safeguard in (r"hash_equals", r"get_total\(", r"get_currency\(", r"is_paid\(|needs_payment\(|has_status\("):
            self.assertNotRegex(diff, safeguard)

    def test_clean_payment_control_scenario_and_fixture(self):
        controls = [
            item for item in load_evals("woocommerce-finalize")
            if any("clean" in name.lower() for name in item["files"])
        ]
        self.assertEqual(1, len(controls))
        control = controls[0]
        text = scenario_text(control)
        self.assertRegex(text, r"no (?:release )?blockers|zero (?:release )?blockers|no findings")
        self.assertRegex(text, r"false.positive")
        self.assertRegex(text, r"(?:do not|does not|never).{0,60}(?:invent|fabricat)")

        diff = read(SKILLS / "woocommerce-finalize" / control["files"][0])
        for name, safeguard in {
            "signature check": r"hash_equals",
            "amount check": r"get_total\(",
            "currency check": r"get_currency\(",
            "replay guard": r"is_paid\(|needs_payment\(|has_status\(",
        }.items():
            with self.subTest(safeguard=name):
                self.assertRegex(diff, safeguard)
        self.assertNotIn("$_POST['order_id']", diff)
        self.assertRegex(diff, r"function test_\w*(?:invalid_signature|bad_signature)")
        self.assertRegex(diff, r"function test_\w*(?:replay|duplicate)")
        self.assertRegex(diff, r"function test_\w*(?:amount|currency)")


RELEASE_DIFF = SKILLS / "woocommerce-finalize/evals/fixtures/checkout-payment-release.diff"
STATUS = ROOT / "docs/evaluation-status.md"


def diff_postimages(text: str) -> dict:
    """Return {path: postimage text} for creation-only fixture diffs (added lines only)."""
    images, current = {}, None
    for line in text.splitlines():
        if line.startswith("diff --git "):
            current = None
        elif line.startswith("+++ b/"):
            current = line[len("+++ b/"):]
            images[current] = []
        elif current is not None and line.startswith("+"):
            images[current].append(line[1:])
    return {path: "\n".join(lines) + "\n" for path, lines in images.items()}


class ReleaseFixtureAndStatusStructuralTest(unittest.TestCase):
    """STRUCTURAL: fixture postimage syntax, oracle scope, and status wording; not behavior proof."""

    def postimages(self):
        images = diff_postimages(read(RELEASE_DIFF))
        self.assertEqual({"src/CheckoutGateway.php", "tests/CheckoutGatewayTest.php"}, set(images))
        return images

    def test_release_diff_postimages_pass_php_lint(self):
        php = shutil.which("php")
        self.assertIsNotNone(php, "PHP CLI is required to lint fixture postimages")
        with tempfile.TemporaryDirectory(prefix="release-postimage-") as directory:
            for name, body in self.postimages().items():
                with self.subTest(postimage=name):
                    target = Path(directory) / Path(name).name
                    target.write_text(body, encoding="utf-8")
                    result = subprocess.run(
                        [php, "-n", "-l", str(target)],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_missing_order_branch_constructs_global_wp_error(self):
        source = self.postimages()["src/CheckoutGateway.php"]

        self.assertRegex(source, r"new\s+\\WP_Error\(\s*'missing_order'")
        self.assertNotRegex(source, r"new\s+WP_Error\(")
        self.assertNotRegex(source, r"new\s+\\?FixtureCommerce\\WP_Error")
        self.assertNotRegex(source, r"new\s+FixtureCommerce\b")

    def test_release_postimages_keep_exactly_the_four_planted_defects(self):
        source = self.postimages()["src/CheckoutGateway.php"]
        for safeguard in (
            r"hash_equals", r"wp_verify_nonce", r"get_total\(", r"get_currency\(", r"get_transaction_id\(",
            r"is_paid\(", r"needs_payment\(", r"has_status\(", r"get_date_paid\(", r"HTTP_X_",
        ):
            with self.subTest(safeguard=safeguard):
                self.assertNotRegex(source, safeguard)
        self.assertEqual(1, source.count("->payment_complete()"))
        self.assertEqual(1, source.count("->update_status('processing')"))
        self.assertEqual(1, source.count("$_POST"))

        case = next(item for item in load_evals("woocommerce-finalize") if item["id"] == 1)
        defects = [text for text in case["expectations"] if text.startswith("Grader oracle, planted defect")]
        self.assertEqual(4, len(defects))
        for number, text in enumerate(defects, 1):
            self.assertIn(f"planted defect {number} of 4", text)
        self.assertNotRegex(json.dumps(case), r"of (?:5|6|7|8)\b|fifth|five planted")

    def test_upgrade_oracle_scopes_order_timezone_change_to_legacy_and_leaves_hpos_unverified(self):
        case = next(item for item in load_evals("woocommerce-upgrade-safety") if item["id"] == 5)
        output = " ".join(case["expected_output"].lower().split())
        expectations = [" ".join(text.lower().split()) for text in case["expectations"]]
        combined = output + " " + " ".join(expectations)

        self.assertRegex(output, r"orders?.{0,160}(?:legacy|post storage|stores? keeping orders as posts)")
        self.assertRegex(output, r"products?.{0,80}(?:all|every) stores?")
        self.assertRegex(output, r"hpos.{0,200}unverified|unverified.{0,200}hpos")
        self.assertRegex(output, r"versioned source.{0,120}boundary test|boundary test.{0,120}versioned source")
        self.assertNotRegex(
            output,
            r"(?:hpos and legacy|legacy and hpos)[^.]{0,60}(?:read|interpreted|parsed) in the store timezone",
        )
        self.assertTrue(
            any(re.search(r"hpos", item) and re.search(r"legacy", item) and "separate" in item for item in expectations)
            or re.search(r"separate.{0,80}boundary tests?", output),
            "HPOS and legacy tests must remain separate",
        )
        for demand in ("no replacement", "wc_email_unsubscribes", "cart-token", "fail closed", "global minimum"):
            with self.subTest(unchanged=demand):
                self.assertIn(demand, combined)

    def test_status_distinguishes_historical_packet_failure_from_new_source_awaiting_acceptance(self):
        text = read(STATUS)
        match = re.search(r"(?ms)^## Current candidate\s*$(.*?)(?=^## |\Z)", text)
        self.assertIsNotNone(match, "Current candidate section is required")
        section = " ".join(match.group(1).lower().split())

        self.assertNotRegex(section, r"no packet (?:has|had|ever)|never (?:been )?run|no packet was")
        self.assertRegex(section, r"historical.{0,200}(?:completed|complete).{0,200}packet|completed.{0,80}packet.{0,200}historical")
        self.assertRegex(section, r"remaining (?:failure|failed)")
        self.assertRegex(section, r"new source.{0,200}(?:awaiting|awaits|pending).{0,80}fresh acceptance")
        self.assertRegex(section, r"(?:rerun|re-run).{0,80}(?:all|every).{0,40}behavior|not reuse.{0,80}(?:old|prior|earlier) grades")

    def test_status_awaiting_claims_are_a_dated_pre_run_snapshot_not_live_state(self):
        text = read(STATUS)
        match = re.search(r"(?ms)^## Current candidate\s*$(.*?)(?=^## |\Z)", text)
        self.assertIsNotNone(match, "Current candidate section is required")
        section = " ".join(match.group(1).lower().split())
        sentences = re.split(r"(?<=[.!?])\s+(?=[a-z\[`])", section)

        boundary = [item for item in sentences if "2026-10-12" in item]
        self.assertTrue(boundary, "an explicit 2026-10-12 snapshot date is required")
        self.assertTrue(
            any(
                re.search(r"source[- ]snapshot|snapshot of (?:the )?(?:new )?source", item)
                and re.search(r"pre-run|before (?:any|the|a) (?:\w+ )?(?:run|evaluation)", item)
                and re.search(r"awaiting|awaits|pending", item)
                and re.search(r"no (?:response-level )?results?", item)
                for item in boundary
            ),
            "the dated sentence must bound the awaiting-acceptance and no-results claims as a pre-run source snapshot",
        )
        self.assertRegex(
            section,
            r"(?:not|neither|does not|do not)\b.{0,120}\b(?:live|current) (?:state|status|repository|checkout)"
            r"|(?:live|current) (?:state|status|repository|checkout).{0,120}(?:may differ|can differ|not (?:described|claimed|asserted))",
        )
        self.assertRegex(
            section,
            r"(?:actual|response-level) (?:outcomes?|results?).{0,160}retained.{0,60}exact candidate.{0,40}packet"
            r"|retained.{0,60}exact candidate.{0,40}packet.{0,160}(?:actual|response-level) (?:outcomes?|results?)",
        )


class MaintenanceStandardsStructuralTest(unittest.TestCase):
    """STRUCTURAL: the portable maintenance document states each standard; it is not an executed process."""

    def test_maintenance_document_states_each_reusable_standard(self):
        self.assertTrue(MAINTENANCE.is_file())
        text = " ".join(read(MAINTENANCE).split()).lower()

        for name, pattern in {
            "exact candidate binding": r"exact candidate.{0,200}(?:digest|bytes)",
            "same-runtime paired arms": r"same[- ]runtime.{0,200}paired|paired.{0,200}same[- ]runtime",
            "approval plus resumed artifact": r"approval.{0,200}resumed.{0,200}artifact",
            "control-only no-skill isolation": r"no-skill.{0,200}isolat|isolat.{0,200}no-skill",
            "evidence-qualified claims": r"evidence-qualified",
            "no unapproved publication": r"(?:no|never|do not).{0,80}(?:unapproved )?publi",
            "native minimal changes": r"native.{0,120}minimal|minimal.{0,120}native",
            "independent review": r"independent review",
            "learnings promotion": r"promot\w+.{0,200}learning|learning\w*.{0,200}promot",
        }.items():
            with self.subTest(standard=name):
                self.assertRegex(text, pattern)
        self.assertRegex(text, r"(?:exclude|never include|do not include).{0,300}secrets")
        self.assertRegex(text, r"(?:exclude|never include|do not include).{0,300}private paths")
        self.assertRegex(text, r"(?:exclude|never include|do not include).{0,300}customer")
        self.assertRegex(text, r"(?:exclude|never include|do not include).{0,300}licensed")

    def test_maintenance_document_is_portable_and_linked(self):
        text = read(MAINTENANCE)

        self.assertNotRegex(text, r"/Users/|/home/|\.hermes|sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}")
        self.assertIn("docs/maintenance-and-evaluation.md", read(ROOT / "README.md"))


if __name__ == "__main__":
    unittest.main()
