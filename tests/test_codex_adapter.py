import json
import re
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILLS = (
    "woocommerce-plugin-dev",
    "woocommerce-finalize",
    "woocommerce-upgrade-safety",
)


class CodexAdapterAcceptanceTest(unittest.TestCase):
    @unittest.skipIf(shutil.which("codex") is None, "codex CLI is unavailable")
    def test_local_disposable_probe_discovers_and_installs_codex_plugin(self):
        with tempfile.TemporaryDirectory() as temporary_root:
            workspace = Path(temporary_root)
            repo = workspace / "repo"
            env = os.environ.copy()
            code_path = workspace / "codex-home"
            (code_path / "cache").mkdir(parents=True, exist_ok=True)
            (code_path / "config").mkdir(parents=True, exist_ok=True)
            env["CODEX_HOME"] = str(code_path)

            codex_version = subprocess.run(
                ["codex", "--version"],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, codex_version.returncode, codex_version.stderr)
            version_output = (codex_version.stdout or codex_version.stderr).strip()
            self.assertTrue(
                version_output,
                "codex --version should emit version metadata",
            )
            match = re.search(r"(\d+)\.(\d+)\.(\d+)", version_output)
            self.assertIsNotNone(match, f"Unable to parse Codex version from: {version_output!r}")
            codex_version_tuple = tuple(map(int, match.groups()))
            self.assertGreaterEqual(codex_version_tuple, (0, 147, 0))
            codex_help = subprocess.run(
                ["codex", "--help"],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, codex_help.returncode, codex_help.stderr)
            self.assertTrue(
                (codex_help.stdout or codex_help.stderr).strip(),
                "codex --help should emit command usage",
            )
            plugin_marketplace_add_help = subprocess.run(
                [
                    "codex",
                    "plugin",
                    "marketplace",
                    "add",
                    "--help",
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, plugin_marketplace_add_help.returncode, plugin_marketplace_add_help.stderr)
            self.assertTrue(
                (plugin_marketplace_add_help.stdout or plugin_marketplace_add_help.stderr).strip(),
                "codex plugin marketplace add --help should emit command usage",
            )
            plugin_add_help = subprocess.run(
                [
                    "codex",
                    "plugin",
                    "add",
                    "--help",
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, plugin_add_help.returncode, plugin_add_help.stderr)
            self.assertTrue(
                (plugin_add_help.stdout or plugin_add_help.stderr).strip(),
                "codex plugin add --help should emit command usage",
            )

            shutil.copytree(
                ROOT,
                repo,
                ignore=shutil.ignore_patterns(".git", "__pycache__"),
            )

            add_marketplace = subprocess.run(
                [
                    "codex",
                    "plugin",
                    "marketplace",
                    "add",
                    str(repo),
                    "--json",
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, add_marketplace.returncode, add_marketplace.stderr)
            marketplace_payload = json.loads(add_marketplace.stdout)
            marketplace_name = marketplace_payload.get("marketplaceName")
            self.assertIsInstance(marketplace_name, str)
            self.assertEqual(str(repo.resolve()), marketplace_payload.get("installedRoot"))

            plugin_list = subprocess.run(
                [
                    "codex",
                    "plugin",
                    "list",
                    "--marketplace",
                    marketplace_name,
                    "--available",
                    "--json",
                ],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, plugin_list.returncode, plugin_list.stderr)
            available = json.loads(plugin_list.stdout)
            candidates = [
                plugin
                for plugin in available.get("available", [])
                if plugin.get("pluginId") == f"agentic-woocommerce-toolkit@{marketplace_name}"
            ]
            self.assertEqual(1, len(candidates))
            candidate = candidates[0]
            self.assertEqual("agentic-woocommerce-toolkit", candidate.get("name"))
            self.assertEqual(str(repo.resolve()), candidate.get("source", {}).get("path"))
            self.assertEqual("AVAILABLE", candidate.get("installPolicy"))
            self.assertEqual("ON_INSTALL", candidate.get("authPolicy"))

            plugin_id = candidate["pluginId"]
            install = subprocess.run(
                ["codex", "plugin", "add", plugin_id, "--json"],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, install.returncode, install.stderr)
            install_payload = json.loads(install.stdout)
            self.assertEqual("agentic-woocommerce-toolkit", install_payload.get("name"))
            self.assertEqual(marketplace_name, install_payload.get("marketplaceName"))
            self.assertIn("installedPath", install_payload)
            installed_path = Path(install_payload["installedPath"])

            codex_docs = (ROOT / "docs/codex.md").read_text(encoding="utf-8").lower()
            self.assertIn("manual post-install acceptance step", codex_docs)
            self.assertIn("not executed by the deterministic test suite", codex_docs)

            installed = subprocess.run(
                ["codex", "plugin", "list", "--json"],
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, installed.returncode, installed.stderr)
            installed_payload = json.loads(installed.stdout)
            installed_plugins = installed_payload.get("installed", [])
            self.assertTrue(
                any(plugin.get("pluginId") == plugin_id for plugin in installed_plugins),
                installed_payload,
            )
            installed_entry = next(
                plugin for plugin in installed_plugins if plugin.get("pluginId") == plugin_id
            )
            self.assertEqual(
                str(installed_path.resolve()),
                str(Path(installed_entry.get("installedPath")).resolve())
                if installed_entry.get("installedPath")
                else str(installed_path.resolve()),
            )

            installed_manifest = json.loads(
                (
                    installed_path
                    / ".codex-plugin"
                    / "plugin.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual("agentic-woocommerce-toolkit", installed_manifest.get("name"))
            self.assertEqual("./skills/", installed_manifest.get("skills"))
            self.assertNotIn("mcpServers", installed_manifest)
            self.assertNotIn("hooks", installed_manifest)
            self.assertNotIn("apps", installed_manifest)

            installed_skill_root = installed_path / "skills"
            self.assertTrue(installed_skill_root.is_dir(), installed_skill_root)
            installed_skills = {
                entry.name
                for entry in installed_skill_root.iterdir()
                if entry.is_dir() and not entry.name.startswith(".")
            }
            self.assertEqual(set(CANONICAL_SKILLS), installed_skills)

            for skill in CANONICAL_SKILLS:
                canonical_skill = (repo / "skills" / skill / "SKILL.md").resolve()
                installed_skill = (installed_path / "skills" / skill / "SKILL.md").resolve()
                self.assertTrue(canonical_skill.is_file(), canonical_skill)
                self.assertTrue(installed_skill.is_file(), installed_skill)
                self.assertEqual(
                    canonical_skill.read_bytes(),
                    installed_skill.read_bytes(),
                    f"SKILL.md mismatch in installed cache for {skill}",
                )
