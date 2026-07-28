# Claude WooCommerce Toolkit

Claude Code skills and agents for building, reviewing, and maintaining WordPress and WooCommerce plugins. The toolkit packages WooCommerce development standards, security guidance, UX review, release checks, and upgrade-safety procedures as a native Claude Code plugin.

## What's included

### Skills

- **[WooCommerce Plugin Development](skills/woocommerce-plugin-dev/SKILL.md)** — explicit, approval-gated project discovery and implementation guidance, with 10 focused references covering coding standards, security, testing, architecture, WooCommerce APIs, UX, AI-facing abilities, PCI script management, and Marketplace submission.
- **[WooCommerce Finalization](skills/woocommerce-finalize/SKILL.md)** — read-only pre-release code-health and end-to-end traceability audit.
- **[WooCommerce Upgrade Safety](skills/woocommerce-upgrade-safety/SKILL.md)** — read-only review of migrations, payment continuity, compatibility, rollback safety, and release communication.

The development skill also includes [evaluation benchmarks](skills/woocommerce-plugin-dev/evals/evals.json) with 4 test scenarios.

### Agents

- **[WooCommerce UX Reviewer](agents/woocommerce-ux-reviewer.md)** — specialized review of WordPress, WooCommerce, checkout, payment, admin, accessibility, mobile, and conversion UX.
- **[Code Reviewer](agents/code-reviewer.md)** — general code review across correctness, security, performance, maintainability, tests, and project standards.

This release contains **3 skills and 2 agents**. The repository validator checks that inventory before release.

## Install the native plugin

After `v1.0.0` is published from the reviewed release commit, install that tag for one project.
Before installing, check for user- or project-level agent overrides that would shadow a packaged agent:

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

From a shell in the target project's root, declare both the pinned marketplace and plugin at
project scope:

```bash
claude plugin marketplace add https://github.com/slash1andy/claude-woocommerce-toolkit.git#v1.0.0 --scope project
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

Request either packaged agent explicitly when you want its review, for example: “Use `claude-woocommerce-toolkit:woocommerce-ux-reviewer` to review this checkout flow.”

## Non-negotiable standards

1. Use WooCommerce CRUD for orders and declare feature compatibility, including HPOS.
2. Treat input as untrusted: sanitize input, escape output, use nonces, capability checks, and prepared queries.
3. Keep credentials out of repositories, examples, command arguments, and rendered settings.
4. Use WordPress internationalization, enqueue, naming, lifecycle, and API conventions.
5. Require tests appropriate to the behavior and explicit approval before external or production mutations.

Upstream provenance: this project originated at [Automattic/claude-woocommerce-toolkit](https://github.com/Automattic/claude-woocommerce-toolkit).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance. Run `python3 -B scripts/validate.py` and the commands documented in the [installation guide](docs/installation.md) before proposing a release.

## License

GPL-2.0-or-later. See [LICENSE](LICENSE).
