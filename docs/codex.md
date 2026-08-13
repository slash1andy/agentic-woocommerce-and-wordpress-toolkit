# Codex adapter usage

This repository ships a separate Codex adapter that points the existing canonical
`skills/` tree through `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`.
It is intentionally skills-only: only `woocommerce-plugin-dev`, `woocommerce-finalize`,
and `woocommerce-upgrade-safety` are exposed through Codex.

## Canonical source and exclusion rules

- The canonical portable skill tree is `skills/` in this repository.
- Do not duplicate or move those skill directories for Codex distribution.
- The Codex manifest does not include MCP servers, hooks, apps, scheduler behavior,
  credentials, or installation shell automation.
- The Codex adapter does not expose the UX reviewer skill; that capability remains in the
  Claude-only adapter.

## Local, disposable Codex probe

Use an isolated `CODEX_HOME` so this probe cannot affect your normal Codex state.

Set `CODEX_HOME` to a disposable directory, then run:

1. `codex plugin marketplace add /absolute/path/to/agentic-woocommerce-and-wordpress-toolkit --json`
1. `codex plugin marketplace list --json`
1. `codex plugin list --marketplace <marketplace-name> --available --json`

Run `codex plugin add agentic-woocommerce-toolkit@<marketplace-name> --json` and confirm:

- the plugin install result includes one installed `agentic-woocommerce-toolkit` entry,
- the plugin source path is `/absolute/path/to/agentic-woocommerce-and-wordpress-toolkit`,
- `codex plugin list --json` includes that plugin as installed.

Then run a **manual post-install acceptance step** with that same `CODEX_HOME` to confirm each
canonical namespace can be used:

1. Open a fresh Codex session using `CODEX_HOME=<that temporary directory>`
2. Run each skill command with the expected namespaces:

- `/agentic-woocommerce-toolkit:woocommerce-plugin-dev`
- `/agentic-woocommerce-toolkit:woocommerce-finalize`
- `/agentic-woocommerce-toolkit:woocommerce-upgrade-safety`

This acceptance step is required but is intentionally not executed by the deterministic test suite.

Keep project code updates, authentication, publishing, release operations, and live-store actions
under existing approval gates.
