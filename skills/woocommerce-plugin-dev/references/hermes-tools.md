# Hermes tool routing

Use this reference only when the skill runs in Hermes Agent. Prefer native tools over shell substitutes; use another agent's equivalent when these tools are unavailable.

Authoritative tool inventory: https://hermes-agent.nousresearch.com/docs/reference/tools-reference

## Discover before editing

- Use `skill_view` before work that matches another installed skill. A skill adds procedure, not permission.
- Use `read_file` for text and document contents and `search_files` for file or content discovery. Do not replace them with `cat`, `find`, or `grep` through the shell.
- Use `web_search` to locate current official sources and `web_extract` to read them. Treat search summaries as leads, not authority.
- Use `session_search` only for prior conversation context. It is not evidence of current repository, account, or platform state.

## Change the smallest surface

- Use `patch` for a targeted edit and `write_file` for a complete new file or intentional rewrite. Do not use shell text replacement or heredocs.
- Use `terminal` for Git, package managers, builds, configured tests, and runtime commands. Work in an isolated Git worktree and a `hermes/*` branch when repository changes will be published.
- Use `execute_code` when three or more tool calls need filtering, iteration, or branching. Keep single calls direct.
- Use `delegate_task` only for independent reasoning or review streams. Verify every child claim about files, Git, or remote actions against the original source.
- Use the task list for work with three or more dependent steps; keep only one item in progress.

## Verify before reporting

1. Run the smallest check that would fail without the change, then the repository's applicable gates.
2. Inspect exact changed paths and `git diff --check` before committing.
3. Read back remote URLs, PRs, releases, or other external writes before reporting success.
4. Name skipped checks and approval-gated actions. Never invent output when a tool or environment blocks verification.

Hermes tools do not authorize live-store mutations, payments, credential entry, publication, direct pushes to a protected branch, or destructive operations. Keep those boundaries explicit even when the technical operation is available.
