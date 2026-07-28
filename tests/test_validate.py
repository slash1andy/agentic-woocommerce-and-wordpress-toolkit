import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = {
    "name": "claude-woocommerce-toolkit",
    "version": "1.0.0",
    "description": "Claude Code skills and agents for WooCommerce plugin development and review.",
    "author": {
        "name": "Andrew Wikel",
        "url": "https://github.com/slash1andy",
    },
    "repository": "https://github.com/slash1andy/claude-woocommerce-toolkit",
    "license": "GPL-2.0-or-later",
}
MARKETPLACE = {
    "name": "claude-woocommerce-toolkit",
    "description": "Claude Code skills and agents for WooCommerce plugin development and review.",
    "owner": {
        "name": "Andrew Wikel",
        "url": "https://github.com/slash1andy",
    },
    "plugins": [{"name": "claude-woocommerce-toolkit", "source": "./"}],
}


class ValidateRepositoryTest(unittest.TestCase):
    def run_after(self, mutate=lambda repo: None):
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir) / "repo"
            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )
            mutate(repo)
            return subprocess.run(
                [sys.executable, "-B", "scripts/validate.py"],
                cwd=repo,
                check=False,
                capture_output=True,
                text=True,
            )

    def test_clean_repository_passes(self):
        result = self.run_after()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Validation passed.", result.stdout)

    def test_missing_manifest_or_component_fails(self):
        for relative in (".claude-plugin/plugin.json", "agents/code-reviewer.md"):
            with self.subTest(relative=relative):
                result = self.run_after(
                    lambda repo, path=relative: (repo / path).unlink(missing_ok=True)
                )

                self.assertNotEqual(0, result.returncode)
                self.assertIn(relative, result.stderr)

    def test_invalid_or_duplicated_version_fails(self):
        def invalid_version(repo):
            path = repo / ".claude-plugin/plugin.json"
            data = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else PLUGIN.copy()
            )
            data["version"] = "v1"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")

        def duplicated_version(repo):
            path = repo / ".claude-plugin/marketplace.json"
            data = (
                json.loads(path.read_text(encoding="utf-8"))
                if path.exists()
                else MARKETPLACE.copy()
            )
            data["plugins"][0]["version"] = "1.0.0"
            path.parent.mkdir(exist_ok=True)
            path.write_text(json.dumps(data), encoding="utf-8")

        for mutate in (invalid_version, duplicated_version):
            with self.subTest(mutate=mutate.__name__):
                result = self.run_after(mutate)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("version", result.stderr)

    def test_unsafe_install_guidance_fails(self):
        for command in (
            "rm -rf .claude/skills",
            "git clone https://github.com/slash1andy/claude-woocommerce-toolkit.git",
            "env git clone https://github.com/slash1andy/claude-woocommerce-toolkit.git",
            "true; git clone https://github.com/slash1andy/claude-woocommerce-toolkit.git",
        ):
            with self.subTest(command=command):
                def add_unsafe_guidance(repo, value=command):
                    path = repo / "docs/installation.md"
                    path.write_text(
                        path.read_text(encoding="utf-8") + f"\n```bash\n{value}\n```\n",
                        encoding="utf-8",
                    )

                result = self.run_after(add_unsafe_guidance)

                self.assertNotEqual(0, result.returncode)
                self.assertIn("unsafe installation guidance", result.stderr)

    def test_safe_install_warning_does_not_false_positive(self):
        def add_safe_warning(repo):
            path = repo / "docs/installation.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + "\nDo not use global installation or symlinks for this plugin.\n",
                encoding="utf-8",
            )

        result = self.run_after(add_safe_warning)

        self.assertEqual(0, result.returncode, result.stderr)

    def test_install_contract_is_fail_closed_and_checks_all_agent_collisions(self):
        docs = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
        combined = docs + (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "claude plugin marketplace add "
            "https://github.com/slash1andy/claude-woocommerce-toolkit.git#v1.0.0 "
            "--scope project",
            combined,
        )
        self.assertIn(
            "claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit "
            "--scope project",
            combined,
        )
        self.assertIn("set -eu", docs)
        self.assertIn("git -C \"$source\" archive", docs)
        self.assertIn('project_root="$(pwd -P)"', docs)
        self.assertIn('[ -L "$target" ]', docs)
        self.assertIn("show-ref --verify --quiet refs/tags/v1.0.0", docs)
        self.assertIn("rev-parse 'refs/tags/v1.0.0^{commit}'", docs)
        self.assertIn('rglob("*.md")', combined)
        self.assertNotIn('cp -R "$reviewed_copy"', docs)
        for marker in (
            'Path.home() / ".claude/agents"',
            'Path(".claude/agents")',
            'names = {"code-reviewer", "woocommerce-ux-reviewer"}',
        ):
            self.assertIn(marker, combined)

    def test_agent_collision_preflight_finds_nested_frontmatter_names(self):
        docs = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
        section = docs.split("## 1. Preflight legacy overrides", 1)[1]
        script = re.search(r"```bash\n(.*?)\n```", section, re.DOTALL).group(1)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            project = root / "project"
            home = root / "home"
            project.mkdir()
            nested = home / ".claude/agents/nested/custom-name.md"
            nested.parent.mkdir(parents=True)
            nested.write_text("---\nname: code-reviewer\n---\n", encoding="utf-8")
            direct = project / ".claude/agents/woocommerce-ux-reviewer.md"
            direct.parent.mkdir(parents=True)
            direct.write_text("No frontmatter.\n", encoding="utf-8")
            result = subprocess.run(
                ["/bin/bash", "-c", script],
                cwd=project,
                env={**os.environ, "HOME": str(home)},
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("custom-name.md", result.stdout)
        self.assertIn("woocommerce-ux-reviewer.md", result.stdout)

    def test_fallback_installs_tag_archive_and_rejects_branch_or_dangling_target(self):
        docs = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
        section = docs.split("## Fallback: copy the complete reviewed plugin", 1)[1]
        template = re.search(r"```bash\n(.*?)\n```", section, re.DOTALL).group(1)
        remote = "https://github.com/slash1andy/claude-woocommerce-toolkit.git"

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            claude = fake_bin / "claude"
            claude.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            claude.chmod(0o755)
            env = {**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"}

            def source_repo(path, ref_kind):
                shutil.copytree(
                    ROOT,
                    path,
                    ignore=shutil.ignore_patterns(".git", "__pycache__"),
                )
                subprocess.run(["git", "init", "-q"], cwd=path, check=True)
                subprocess.run(["git", "add", "."], cwd=path, check=True)
                subprocess.run(
                    ["git", "-c", "user.name=Test", "-c", "user.email=test@example.test", "commit", "-qm", "fixture"],
                    cwd=path,
                    check=True,
                )
                subprocess.run(["git", ref_kind, "v1.0.0"], cwd=path, check=True)

            tagged = root / "tagged"
            source_repo(tagged, "tag")
            project = root / "project"
            project.mkdir()
            result = subprocess.run(
                ["/bin/bash", "-c", template.replace(remote, str(tagged))],
                cwd=project,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            installed = project / ".claude/skills/claude-woocommerce-toolkit"
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((installed / "scripts/validate.py").is_file())
            self.assertFalse((installed / ".git").exists())

            branch = root / "branch"
            source_repo(branch, "branch")
            branch_project = root / "branch-project"
            branch_project.mkdir()
            result = subprocess.run(
                ["/bin/bash", "-c", template.replace(remote, str(branch))],
                cwd=branch_project,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertFalse(
                (branch_project / ".claude/skills/claude-woocommerce-toolkit").exists()
            )

            link_project = root / "link-project"
            target = link_project / ".claude/skills/claude-woocommerce-toolkit"
            target.parent.mkdir(parents=True)
            target.symlink_to(link_project / "missing")
            result = subprocess.run(
                ["/bin/bash", "-c", template.replace(remote, str(tagged))],
                cwd=link_project,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(target.is_symlink())
            self.assertIn("Refusing to overwrite", result.stderr)

    def test_marketplace_description_is_required(self):
        def remove_description(repo):
            path = repo / ".claude-plugin/marketplace.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data.pop("description", None)
            path.write_text(json.dumps(data), encoding="utf-8")

        result = self.run_after(remove_description)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("exact manifest contract", result.stderr)

    def test_duplicate_json_keys_fail(self):
        def duplicate_version(repo):
            path = repo / ".claude-plugin/plugin.json"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    '"version": "1.0.0",',
                    '"version": "1.0.0",\n  "version": "1.0.0",',
                    1,
                ),
                encoding="utf-8",
            )

        result = self.run_after(duplicate_version)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("duplicate key", result.stderr)

    def test_exact_component_inventory_frontmatter_and_symlinks(self):
        def extra_skill(repo):
            path = repo / "skills/extra/SKILL.md"
            path.parent.mkdir()
            path.write_text("---\nname: extra\n---\n", encoding="utf-8")

        def extra_agent(repo):
            (repo / "agents/extra.md").write_text("---\nname: extra\n---\n", encoding="utf-8")

        def duplicate_skill_policy(repo):
            path = repo / "skills/woocommerce-finalize/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "disable-model-invocation: true",
                    '"disable-model-invocation" : false\n'
                    "disable-model-invocation: true",
                    1,
                ),
                encoding="utf-8",
            )

        def wrong_agent_name(repo):
            path = repo / "agents/code-reviewer.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "name: code-reviewer", "name: another-reviewer", 1
                ),
                encoding="utf-8",
            )

        def escaped_agent_symlink(repo):
            outside = repo.parent / "outside-agent.md"
            outside.write_text("---\nname: code-reviewer\n---\n", encoding="utf-8")
            path = repo / "agents/code-reviewer.md"
            path.unlink()
            path.symlink_to(outside)

        def parent_directory_symlink(repo):
            path = repo / "skills/woocommerce-finalize"
            real = repo.parent / "woocommerce-finalize-real"
            path.rename(real)
            path.symlink_to(real, target_is_directory=True)

        def malformed_frontmatter(repo):
            path = repo / "skills/woocommerce-finalize/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "disable-model-invocation: true",
                    "disable-model-invocation true\ndisable-model-invocation: true",
                    1,
                ),
                encoding="utf-8",
            )

        for mutate in (
            extra_skill,
            extra_agent,
            duplicate_skill_policy,
            wrong_agent_name,
            escaped_agent_symlink,
            parent_directory_symlink,
            malformed_frontmatter,
        ):
            with self.subTest(mutate=mutate.__name__):
                result = self.run_after(mutate)
                self.assertNotEqual(0, result.returncode)
                self.assertRegex(result.stderr, r"inventory|frontmatter|symlink")

    def test_credential_urls_fail_offline_without_echoing_the_secret(self):
        secret = "do-not-print-this-value"

        def add_credential_url(repo):
            path = repo / "README.md"
            path.write_text(
                path.read_text(encoding="utf-8")
                + f"\nhttps://example.test/path?consumer_secret={secret}\n",
                encoding="utf-8",
            )

        result = self.run_after(add_credential_url)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("URL contains credentials", result.stderr)
        self.assertNotIn(secret, result.stderr)

    def test_invalid_paths_and_urls_fail_without_tracebacks(self):
        def manifest_directory(repo):
            path = repo / ".claude-plugin/plugin.json"
            path.unlink()
            path.mkdir()

        def malformed_url(repo):
            path = repo / "README.md"
            path.write_text(
                path.read_text(encoding="utf-8") + "\nhttps://[invalid\n",
                encoding="utf-8",
            )

        def markdown_directory(repo):
            (repo / "docs/ambiguous.md").mkdir()

        for mutate, expected in (
            (manifest_directory, 1),
            (malformed_url, 1),
            (markdown_directory, 0),
        ):
            with self.subTest(mutate=mutate.__name__):
                result = self.run_after(mutate)
                self.assertEqual(expected, int(result.returncode != 0), result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_invalid_utf8_fails_with_path_without_traceback(self):
        for relative in (
            ".claude-plugin/plugin.json",
            "skills/woocommerce-finalize/SKILL.md",
            "README.md",
        ):
            with self.subTest(relative=relative):
                def invalid_utf8(repo, path=relative):
                    (repo / path).write_bytes(b"\xff")

                result = self.run_after(invalid_utf8)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(f"{relative}: invalid UTF-8", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_broken_cross_reference_fails(self):
        def break_reference(repo):
            path = repo / "skills/woocommerce-finalize/SKILL.md"
            path.write_text(
                path.read_text(encoding="utf-8").replace(
                    "${CLAUDE_SKILL_DIR}/../woocommerce-plugin-dev/references/security.md",
                    "${CLAUDE_SKILL_DIR}/../woocommerce-plugin-dev/references/missing.md",
                ),
                encoding="utf-8",
            )

        result = self.run_after(break_reference)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("broken cross-reference", result.stderr)


if __name__ == "__main__":
    unittest.main()
