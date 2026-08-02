# Agentic WooCommerce and WordPress toolkit

This repository packages Claude Code skills and a read-only UX agent under the preserved
`claude-woocommerce-toolkit` plugin namespace. The toolkit starts from the target repository, uses
official platform APIs, and keeps writes and release actions behind explicit approval.

## What's included

### Skills

- **[WooCommerce plugin development](skills/woocommerce-plugin-dev/SKILL.md)** — explicit,
  approval-gated implementation guidance with 10 focused references.
- **[WooCommerce finalization](skills/woocommerce-finalize/SKILL.md)** — read-only pre-release code
  health and traceability review.
- **[WooCommerce upgrade safety](skills/woocommerce-upgrade-safety/SKILL.md)** — read-only review of
  migrations, commerce continuity, compatibility, and recovery.

Each skill includes official-format manual evaluation scenarios under its `evals/evals.json` path.
These are unexecuted scenarios, not benchmark results; see [evaluation status](docs/evaluation-status.md).

### UX agent

- **[WooCommerce UX reviewer](agents/woocommerce-ux-reviewer.md)** — focused review of shopper and
  merchant flows across storefront, checkout, payment, admin, accessibility, mobile, and recovery.

This release contains **3 skills and 1 read-only UX agent**. The repository validator checks that
inventory before release.

## Install the native plugin

After `v1.0.0` is published from the reviewed release commit, install that tag for one project.
Before installing, check for a user- or project-level agent override that would shadow the packaged agent:

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

From a shell in the target project's root, declare both the pinned marketplace and plugin at
project scope:

```bash
claude plugin marketplace add https://github.com/slash1andy/agentic-woocommerce-and-wordpress-toolkit.git#v1.0.0 --scope project
claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project
```

These commands write the marketplace source and enabled plugin to the target repository's
`.claude/settings.json`, where collaborators can review and accept them. Run `/reload-plugins` in
Claude Code afterward. See the [installation guide](docs/installation.md) for validation and the
single complete-copy fallback.

## Usage

All three skills require explicit invocation. Plugin skills use Claude Code's `plugin-name:skill-name` namespace:

```text
/claude-woocommerce-toolkit:woocommerce-plugin-dev Build a loyalty-points extension
/claude-woocommerce-toolkit:woocommerce-finalize Review this release candidate
/claude-woocommerce-toolkit:woocommerce-upgrade-safety Review the 1.4.0 upgrade path
```

Request the packaged agent explicitly when you want its review. For example, ask Claude Code to use
`claude-woocommerce-toolkit:woocommerce-ux-reviewer` to review a checkout flow. For generic
correctness review, use the explicit `/code-review` command.

Upstream provenance: this project originated at [Automattic/claude-woocommerce-toolkit](https://github.com/Automattic/claude-woocommerce-toolkit).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance. Run `python3 -B scripts/validate.py` and the commands documented in the [installation guide](docs/installation.md) before proposing a release.

## License

GPL-2.0-or-later. See [LICENSE](LICENSE).
