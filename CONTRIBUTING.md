# Contributing

Contributions should keep the toolkit narrow, evidence-based, and useful across WordPress and
WooCommerce repositories. Start from official platform contracts and the target repository rather
than adding generic scaffolding.

## What to contribute

### Reference documents

The `skills/woocommerce-plugin-dev/references/` directory contains focused guides. Add a reference
when a recurring WooCommerce or WordPress boundary needs more detail than a core skill can carry.
Useful subjects include:

- Block development patterns (Gutenberg blocks for WooCommerce)
- WooCommerce Subscriptions integration patterns
- Multisite compatibility
- Performance optimization techniques
- Internationalization (i18n) deep dive

### Reference standards

Each reference document should:

- Cover a single, well-scoped topic
- Cite current official sources
- Include working code examples that follow WordPress Coding Standards
- Be self-contained (readable without the other reference docs)
- Match the repository's voice and structure

### Manual evaluation scenarios

Each `skills/*/evals/evals.json` file contains official-format manual evaluation scenarios, not benchmark results. Add scenarios that test:

- New reference doc coverage (does the skill apply the new standards?)
- Edge cases in existing standards
- Multi-step workflows that exercise several reference docs together

### Agent improvements

Agent definitions live in `agents/`. Keep them read-only and WooCommerce-specific. Useful changes
include:

- Additional review dimensions or checklists
- Better severity calibration
- Domain-specific expertise (e.g., WooCommerce Blocks, Subscriptions)

## Voice and style

- Use sentence case for headings.
- Write direct instructions in active voice. Prefer `Run`, `Verify`, and `Do not` over vague advice.
- Separate current facts from forward-looking guidance, and cite official sources for both.
- Use repository evidence before prescribing tools, structure, compatibility, or tests.
- Keep authentication, writes, live actions, and publication behind explicit approval.

## Test a source checkout

From the repository root, load the plugin without installing or publishing it:

```bash
claude --plugin-dir .
```

In that Claude Code session, run `/reload-plugins`, confirm `/plugin` lists all 3 skills and the
local `woocommerce-ux-reviewer` agent label (scoped as
`claude-woocommerce-toolkit:woocommerce-ux-reviewer` at runtime), then invoke the explicit
write-gated development skill through its scoped runtime identity:

```text
/claude-woocommerce-toolkit:woocommerce-plugin-dev Inspect this repository and stop before writes
```

With PHP CLI and Claude Code 2.1.163 or later, run the deterministic gates from a separate shell:

```bash
python3 -B scripts/validate.py
python3 -B -m unittest discover -s tests -p 'test_*.py'
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
```

## How to submit

1. Fork the repository
2. Create a feature branch (`git checkout -b add-blocks-reference`)
3. Make your changes
4. Test that skills and agents still load correctly in Claude Code
5. Submit a pull request with a clear description of what you added and why

## Guidelines

- Keep content generic and community-friendly. Do not include references to specific companies, internal tools, or proprietary systems.
- All code examples must follow WordPress Coding Standards.
- Reference official documentation wherever possible.
- Avoid speculation about WordPress/WooCommerce internals. Cite docs or verifiable code.

## License

By contributing, you agree that your contributions will be licensed under GPL-2.0-or-later.
