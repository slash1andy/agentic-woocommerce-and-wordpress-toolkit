# Hermes Agent integration

Hermes implements the Agent Skills standard and can load this repository's canonical `skills/` directory directly. Keep the repository checkout as the reviewed source instead of copying individual skill folders.

## Configure shared skill directories

Add the official WordPress skill checkout and this toolkit checkout to the active Hermes profile's `config.yaml`:

```yaml
skills:
  external_dirs:
    - /path/to/wordpress-agent-skills/skills
    - /path/to/agentic-woocommerce-and-wordpress-toolkit/skills
```

Hermes expands `~` and environment variables in these paths. A local skill under `~/.hermes/skills/` wins when it has the same name as an external skill. External directories are mutable when the Hermes process can write to them, so keep changes on a review branch and inspect the Git diff before publishing.

The WordPress repository supplies routing, project triage, core APIs, Blocks, Playground, performance, and other platform skills. This toolkit adds WooCommerce implementation, finalization, upgrade safety, and UX review guidance. Use Hermes' explicit `/code-review` command for generic correctness review.

Codex has a separate adapter path via `.codex-plugin`/`.agents/plugins/marketplace.json`; this guide remains the direct
`skills/` loading path for Hermes.

## Verify discovery

Start a new session or run `/reload-skills`, then check `hermes skills list`. The inventory should include:

- `woocommerce-plugin-dev`
- `woocommerce-finalize`
- `woocommerce-upgrade-safety`

Invoke `/woocommerce-plugin-dev` for implementation work. For finalization or upgrade review, load `woocommerce-plugin-dev` first so its shared references are available, then load `/woocommerce-finalize` or `/woocommerce-upgrade-safety`.

## Hermes execution behavior

When `woocommerce-plugin-dev` is active under Hermes, load `references/hermes-tools.md` and use the native tool routing documented there. Tool availability never expands approval scope: repository writes, installs, authentication, uploads, publication, destructive actions, and live-store mutations retain their own approval boundaries.

## Updating

Update the checked-out repositories through normal reviewed Git branches. Because Hermes reads the external directories directly, a new session sees the reviewed checkout without a separate copy step. Run `/reload-skills` only when skill files were added or removed during the current session.
