# Installation guide

Install the toolkit as a project-scoped native Claude Code plugin under the preserved
`claude-woocommerce-toolkit` plugin namespace. Use the reviewed `claude-woocommerce-toolkit--v1.0.0` release commit after that tag
is published at the release gate. The plugin installs all 3 skills, one read-only UX agent, shared
references, evals, manifests, and the repository validator together.

## Prerequisites

- [Claude Code](https://code.claude.com/docs/en/discover-plugins) 2.1.163 or later with plugin marketplace and `--strict` manifest support
- Git CLI for local release and diff-fixture verification
- PHP CLI for syntax-checking packaged PHP evaluation fixtures
- A target project where you can choose **Project** installation scope

## 1. Add and install the reviewed plugin

Claude Code scopes plugin skills and agents by plugin name. The packaged agent appears as
`claude-woocommerce-toolkit:woocommerce-ux-reviewer`; standalone agents keep their own identities.

From a shell in the target project's root, declare both the pinned marketplace and plugin at
project scope:

```bash
set -eu
claude plugin marketplace add https://github.com/slash1andy/agentic-woocommerce-and-wordpress-toolkit.git#claude-woocommerce-toolkit--v1.0.0 --scope project
claude plugin install claude-woocommerce-toolkit@claude-woocommerce-toolkit --scope project
```

The commands write the marketplace source and enabled plugin to the target repository's
`.claude/settings.json`. Collaborators review and accept those entries when they trust the project.
The marketplace source is pinned to `claude-woocommerce-toolkit--v1.0.0`; do not replace it with a mutable branch. Start Claude
Code from the project root and run `/reload-plugins` after installation.

## 2. Verify the installation

Open `/plugin`, select the installed plugin, and confirm it reports:

- skills: `woocommerce-plugin-dev`, `woocommerce-finalize`, `woocommerce-upgrade-safety`
- agent: `woocommerce-ux-reviewer`

These are local inventory labels. Runtime invocations remain scoped by the plugin namespace. For
generic correctness review, use Claude Code's explicit `/code-review` command.

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

## Release validation

From a reviewed source checkout with PHP CLI and Claude Code 2.1.163 or later, run the offline
repository gate and Claude's strict manifest validators:

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
