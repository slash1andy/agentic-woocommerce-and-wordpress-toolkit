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

## Invocation policy

Each skill ships `agents/openai.yaml` with the minimal native policy
`allow_implicit_invocation: true` under `policy:`, so Codex may select the skill when a task matches
and you can still invoke it explicitly. The repository validator accepts only that exact two-line file.

This metadata controls skill discovery and selection. It is not approval enforcement: the approval
gates in these skills are instructions to the model, and Codex does not enforce them. Keep
sandbox and approval settings in your Codex configuration.

## Local, disposable Codex probe

Use an isolated `CODEX_HOME` so this probe cannot affect your normal Codex state.

The probe commands below need Codex CLI >= 0.147.0, the minimum tooling version for this probe. That
minimum does not establish compatibility with any specific later release; record the actual `codex --version` you probed.

Set `CODEX_HOME` to a disposable directory, then run:

1. `codex plugin marketplace add /absolute/path/to/agentic-woocommerce-and-wordpress-toolkit --json`
1. `codex plugin marketplace list --json`
1. `codex plugin list --marketplace <marketplace-name> --available --json`

Run `codex plugin add agentic-woocommerce-toolkit@<marketplace-name> --json` and confirm:

- the plugin install result includes one installed `agentic-woocommerce-toolkit` entry,
- the plugin source path is `/absolute/path/to/agentic-woocommerce-and-wordpress-toolkit`,
- `codex plugin list --json` includes that plugin as installed. When that entry reports
  `installedPath`, it must be a nonempty string that matches the install result path. The list may omit
  `installedPath`; do not infer one. The installed manifest and skill files are checked on the filesystem
  separately, so they do not corroborate the list entry.

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
