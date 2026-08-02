# Installation guide

Install the toolkit as a project-scoped native Claude Code plugin under the preserved
`claude-woocommerce-toolkit` plugin namespace. Use the reviewed `v1.0.0` release commit after that tag
is published at the release gate. The plugin installs all 3 skills, one read-only UX agent, shared
references, evals, manifests, and the repository validator together.

## Prerequisites

- [Claude Code](https://code.claude.com/docs/en/discover-plugins) with plugin marketplace support
- A target project where you can choose **Project** installation scope

## 1. Preflight legacy overrides

A user- or project-level file with the packaged agent name shadows that plugin agent. Run this
from the target project's root:

```bash
python3 - <<'PY'
from pathlib import Path

names = {"woocommerce-ux-reviewer"}
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
                raw_value = value.split("#", 1)[0].strip()
                if separator and key.strip().strip("\"'") == "name":
                    if raw_value.lower() not in {"", "null", "~"}:
                        identity = raw_value.strip("\"'")
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
claude plugin marketplace add https://github.com/slash1andy/agentic-woocommerce-and-wordpress-toolkit.git#v1.0.0 --scope project
claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project
```

The commands write the marketplace source and enabled plugin to the target repository's
`.claude/settings.json`. Collaborators review and accept those entries when they trust the project.
The marketplace source is pinned to `v1.0.0`; do not replace it with a mutable branch. Start Claude
Code from the project root and run `/reload-plugins` after installation.

## 3. Verify the installation

Open `/plugin`, select the installed plugin, and confirm it reports:

- skills: `woocommerce-plugin-dev`, `woocommerce-finalize`, `woocommerce-upgrade-safety`
- agent: `woocommerce-ux-reviewer`

For generic correctness review, use Claude Code's explicit `/code-review` command.

Then invoke a packaged skill by its namespaced command:

```text
/claude-woocommerce-toolkit:woocommerce-plugin-dev Build a WooCommerce shipping extension
```

The skill should begin repository-first discovery and stop at its write-approval gate. Invoke the
other explicit-only skills with:

```text
/claude-woocommerce-toolkit:woocommerce-finalize Review this release candidate
/claude-woocommerce-toolkit:woocommerce-upgrade-safety Review this upgrade path
```

## Fallback: copy the complete reviewed plugin

Use this only when marketplace installation is unavailable. Copy the entire reviewed repository into the project's skills directory as one skills-directory plugin; do not copy individual skills, agents, or references.

```bash
(
set -eu
project_root="$(pwd -P)"
for path in .claude .claude/skills; do
  if [ -L "$path" ]; then
    printf 'Refusing symlinked installation path: %s\n' "$path" >&2
    exit 1
  fi
done
mkdir -p .claude/skills
skills_root="$(cd .claude/skills && pwd -P)"
if [ "$skills_root" != "$project_root/.claude/skills" ]; then
  printf 'Refusing installation outside project skills directory\n' >&2
  exit 1
fi
target="$skills_root/claude-woocommerce-toolkit"
if [ -e "$target" ] || [ -L "$target" ]; then
  printf 'Refusing to overwrite existing path: %s\n' "$target" >&2
  exit 1
fi

work="$(mktemp -d "$project_root/.claude/skills/.claude-woocommerce-toolkit.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT
source="$work/source"
plugin="$work/plugin"
archive="$work/plugin.tar"

git clone --branch v1.0.0 --depth 1 \
  https://github.com/slash1andy/agentic-woocommerce-and-wordpress-toolkit.git "$source"
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

Run `/reload-plugins`, then repeat the namespaced invocation check above. Launch Claude Code from the project root and accept workspace trust if discovery is empty so the skills-directory plugin can load.

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
