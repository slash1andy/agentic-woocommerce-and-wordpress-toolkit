# Agentic WooCommerce and WordPress toolkit

This repository packages Claude Code skills and a read-only UX agent under the preserved
`claude-woocommerce-toolkit` plugin namespace. The toolkit starts from the target repository, uses
official platform APIs, and instructs its components to require explicit approval before writes and
release actions.

## What's included

### Skills

- **[WooCommerce plugin development](skills/woocommerce-plugin-dev/SKILL.md)** — explicit,
  approval-gated implementation guidance with 10 focused references.
- **[WooCommerce finalization](skills/woocommerce-finalize/SKILL.md)** — read-only pre-release code
  health and traceability review.
- **[WooCommerce upgrade safety](skills/woocommerce-upgrade-safety/SKILL.md)** — read-only review of
  migrations, commerce continuity, compatibility, and recovery.

Each skill includes manual evaluation scenarios following the current `skill-creator` schema under
its `evals/evals.json` path.
These are unexecuted scenarios, not benchmark results; see [evaluation status](docs/evaluation-status.md).

### UX agent

- **[WooCommerce UX reviewer](agents/woocommerce-ux-reviewer.md)** — focused review of shopper and
  merchant flows across storefront, checkout, payment, admin, accessibility, mobile, and recovery.

This release contains **3 skills and 1 read-only UX agent**. The repository validator checks that
inventory before release.

## Why this fork

The upstream project supplied the three WooCommerce skills and original UX reviewer. This fork
packages those components as a project-scoped native Claude Code plugin, narrows automatic and
mutating behavior, removes generic reviewer overlap, and adds a standard-library Python validation
entry point for package, safety, link, evaluation fixture, and release contracts.

## Install the native plugin

After `claude-woocommerce-toolkit--v1.0.0` is published from the reviewed release commit, use Claude
Code 2.1.163 or later and install that tag for one project. Plugin components are scoped by the
preserved `claude-woocommerce-toolkit` namespace, so standalone skills and agents keep their own identities.
From a shell in the target project's root:

```bash
set -eu
claude plugin marketplace add https://github.com/slash1andy/agentic-woocommerce-and-wordpress-toolkit.git#claude-woocommerce-toolkit--v1.0.0 --scope project
claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project
```

These commands write the marketplace source and enabled plugin to the target repository's
`.claude/settings.json`, where collaborators can review and accept them. Run `/reload-plugins` in
Claude Code afterward. See the [installation guide](docs/installation.md) for verification details.

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
