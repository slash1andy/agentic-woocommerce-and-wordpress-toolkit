# Contributing

Contributions are welcome. This toolkit aims to capture and share WordPress and WooCommerce development best practices for use with Claude Code.

## What to Contribute

### Reference Documents

The `skills/woocommerce-plugin-dev/references/` directory contains standalone guides on specific topics. Good candidates for new reference docs:

- Block development patterns (Gutenberg blocks for WooCommerce)
- WooCommerce Subscriptions integration patterns
- Multisite compatibility
- Performance optimization techniques
- Internationalization (i18n) deep dive

### Reference Doc Standards

Each reference document should:

- Cover a single, well-scoped topic
- Cite official sources (WordPress Plugin Handbook, WooCommerce developer docs, etc.)
- Include working code examples that follow WordPress Coding Standards
- Be self-contained (readable without the other reference docs)
- Use the existing docs as a template for structure and tone

### Evaluation Benchmarks

The `evals/evals.json` file contains test scenarios for the skill. Add evals that test:

- New reference doc coverage (does the skill apply the new standards?)
- Edge cases in existing standards
- Multi-step workflows that exercise several reference docs together

### Agent Improvements

Agent definitions live in `agents/`. Improvements might include:

- Additional review dimensions or checklists
- Better severity calibration
- Domain-specific expertise (e.g., WooCommerce Blocks, Subscriptions)

## How to Submit

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

By contributing, you agree that your contributions will be licensed under the GPL v2 or later.
