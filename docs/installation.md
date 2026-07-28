# Installation Guide

The supported installation is a project-scoped native Claude Code plugin from the reviewed `v1.0.0`
release commit. These commands become usable after that tag is published at the release gate. The
plugin installs all 3 skills, both current agents, shared references, evals, manifests, and the
repository validator together.

## Prerequisites

- [Claude Code](https://code.claude.com/docs/en/discover-plugins) with plugin marketplace support
- A target project where you can choose **Project** installation scope

## 1. Preflight legacy overrides

A user- or project-level file with either packaged agent name shadows that plugin agent. Run this
from the target project's root:

```bash
python3 - <<'PY'
from pathlib import Path

names = {"code-reviewer", "woocommerce-ux-reviewer"}
collisions = []
for root in (Path.home() / ".claude/agents", Path(".claude/agents")):
    for path in root.rglob("*.md") if root.is_dir() else ():
        try:
            parts = path.read_text(encoding="utf-8").split("---", 2)
        except OSError as exc:
            raise SystemExit(f"Cannot inspect {path}: {exc}") from exc
        identity = path.stem
        if len(parts) == 3 and not parts[0].strip():
            for line in parts[1].splitlines():
                key, separator, value = line.partition(":")
                value = value.split("#", 1)[0].strip().strip("\"'")
                if separator and key.strip().strip("\"'") == "name":
                    identity = value
                    break
        if identity in names:
            collisions.append(path)

if collisions:
    print("Resolve existing agent overrides before install:")
    print(*collisions, sep="\n")
    raise SystemExit(1)
PY
```

If any path is reported, stop and deliberately rename or remove that legacy override before
continuing. Do not overwrite it as part of installation. Standalone skills do not shadow the
plugin's namespaced skill commands.

## 2. Add and install the reviewed plugin

From a shell in the target project's root, declare both the pinned marketplace and plugin at
project scope:

```bash
claude plugin marketplace add https://github.com/slash1andy/claude-woocommerce-toolkit.git#v1.0.0 --scope project
claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project
```

The commands write the marketplace source and enabled plugin to the target repository's
`.claude/settings.json`. Collaborators review and accept those entries when they trust the project.
The marketplace source is pinned to `v1.0.0`; do not replace it with a mutable branch. Start Claude
Code from the project root and run `/reload-plugins` after installation.

## 3. Verify the installation

Open `/plugin`, select the installed plugin, and confirm it reports:

- skills: `woocommerce-plugin-dev`, `woocommerce-finalize`, `woocommerce-upgrade-safety`
- agents: `woocommerce-ux-reviewer`, `code-reviewer`

Then invoke a packaged skill by its namespaced command:

```text
/claude-woocommerce-toolkit:woocommerce-plugin-dev Build a WooCommerce shipping extension
```

The skill should begin its approval-gated Project Discovery phase. Invoke the other explicit-only skills with:

```text
/claude-woocommerce-toolkit:woocommerce-finalize Review this release candidate
/claude-woocommerce-toolkit:woocommerce-upgrade-safety Review this upgrade path
```

## Fallback: copy the complete reviewed plugin

Use this only when marketplace installation is unavailable. Copy the entire reviewed repository into the project's skills directory as one skills-directory plugin; do not copy individual skills, agents, or references.

```bash
(
set -eu
target=".claude/skills/claude-woocommerce-toolkit"
if [ -e "$target" ] || [ -L "$target" ]; then
  printf 'Refusing to overwrite existing path: %s\n' "$target" >&2
  exit 1
fi

mkdir -p .claude/skills
project_root="$(pwd -P)"
work="$(mktemp -d "$project_root/.claude/skills/.claude-woocommerce-toolkit.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT
source="$work/source"
plugin="$work/plugin"
archive="$work/plugin.tar"

git clone --branch v1.0.0 --depth 1 \
  https://github.com/slash1andy/claude-woocommerce-toolkit.git "$source"
git -C "$source" show-ref --verify --quiet refs/tags/v1.0.0
test "$(git -C "$source" rev-parse HEAD)" = \
  "$(git -C "$source" rev-parse 'refs/tags/v1.0.0^{commit}')"

mkdir "$plugin"
git -C "$source" archive --format=tar --output="$archive" refs/tags/v1.0.0
tar -xf "$archive" -C "$plugin"
test ! -e "$plugin/.git"

python3 -B "$plugin/scripts/validate.py"
claude plugin validate "$plugin/.claude-plugin/plugin.json" --strict
claude plugin validate "$plugin/.claude-plugin/marketplace.json" --strict
mv "$plugin" "$target"
)
```

Run `/reload-plugins`, then repeat the namespaced invocation check above. Launch Claude Code from the project root so the skills-directory plugin is discovered.

## Release validation

From a reviewed source checkout, run the offline repository gate and Claude's strict manifest validators:

```bash
python3 -B scripts/validate.py
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

URL checks are separate and networked:

```bash
python3 -B scripts/validate.py --check-urls
```

A future release should be installed only after its tag and contents receive the same review and validation. Do not update an installation from a mutable checkout.
