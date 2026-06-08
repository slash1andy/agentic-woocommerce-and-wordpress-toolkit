# Claude WooCommerce Toolkit

A collection of Claude Code skills and agents for building, reviewing, and maintaining WordPress and WooCommerce plugins. These tools encode professional development standards, security best practices, and UX guidelines drawn from the official WordPress Plugin Handbook, WooCommerce developer documentation, and fintech-grade security practices.

## What's Included

### Skills

**[WooCommerce Plugin Development](skills/woocommerce-plugin-dev/SKILL.md)** — A comprehensive skill that guides you through building WooCommerce Marketplace-ready plugins from scratch. It operates in two phases:

1. **Project Discovery** — structured interview to produce a project brief
2. **Development Execution** — scaffold and build following all standards

Includes 10 reference documents covering every aspect of plugin development:

| Reference | What It Covers |
|-----------|---------------|
| [Coding Standards](skills/woocommerce-plugin-dev/references/coding-standards.md) | WordPress PHP/JS/CSS standards, WPCS 3.3.0+, PSR-4 autoloading |
| [Security](skills/woocommerce-plugin-dev/references/security.md) | Input sanitization, output escaping, nonces, CSRF, SQL injection prevention, PCI-DSS |
| [Testing](skills/woocommerce-plugin-dev/references/testing.md) | PHPUnit, Playwright E2E, security tests, financial precision tests, CI/CD |
| [Plugin Architecture](skills/woocommerce-plugin-dev/references/plugin-architecture.md) | File structure, bootstrapping, HPOS declaration, uninstall handlers |
| [WooCommerce APIs](skills/woocommerce-plugin-dev/references/woocommerce-apis.md) | Order/Product CRUD, hooks, REST API, Store API, Additional Checkout Fields, Action Scheduler |
| [UX Guidelines](skills/woocommerce-plugin-dev/references/ux-guidelines.md) | Navigation, settings design, onboarding, admin notices, accessibility |
| [Abilities & MCP](skills/woocommerce-plugin-dev/references/abilities-and-mcp.md) | Exposing operations to AI agents via the WordPress Abilities API + MCP Adapter |
| [Agentic Commerce](skills/woocommerce-plugin-dev/references/agentic-commerce.md) | AI-agent discovery & checkout readiness (Abilities/MCP, ACP, AP2) |
| [PCI Script Management](skills/woocommerce-plugin-dev/references/pci-script-management.md) | PCI DSS v4.0.1 payment-page script requirements (6.4.3 / 11.6.1) |
| [Marketplace Submission](skills/woocommerce-plugin-dev/references/marketplace-submission.md) | QIT managed tests, Marketplace + WordPress.org distribution |

Also includes [evaluation benchmarks](skills/woocommerce-plugin-dev/evals/evals.json) with 3 test scenarios.

**[WooCommerce Finalization](skills/woocommerce-finalize/SKILL.md)** — Pre-release code health and traceability audit. Runs after code review to catch structural issues that checklists miss:

- **Code Health** — dead code detection, duplication analysis, structural complexity (god classes, deep nesting)
- **Traceability Analysis** — end-to-end verification tracing every UI interaction through AJAX/REST handlers, business logic, data access, and database. Includes 5 payment-gateway-specific trace paths (payment, refund, settings, token, webhook flows)

**[WooCommerce Upgrade Safety](skills/woocommerce-upgrade-safety/SKILL.md)** — Pre-release upgrade safety review that validates what happens when existing merchants upgrade between versions:

- **Database Migration Safety** — idempotency, batching, version gates, HPOS dual-table compatibility
- **Payment Continuity** — saved token preservation, active subscription safety, pending transaction handling, webhook backward compatibility
- **Hook/Filter Compatibility** — removed hooks, changed signatures, deprecation notices
- **Rollback Safety** — downgrade resilience, WordPress auto-update safety
- **Changelog Quality** — upgrade notices, breaking change documentation, version metadata

### Agents

**[WooCommerce UX Reviewer](agents/woocommerce-ux-reviewer.md)** — An expert UX review agent specialized in WordPress, WooCommerce, and payment system interfaces. Reviews checkout flows, payment gateway integrations, admin UI, onboarding experiences, and error states against dimensions including clarity, trust signals, accessibility (WCAG 2.1 AA), mobile responsiveness, and conversion impact.

**[Code Reviewer](agents/code-reviewer.md)** — A general-purpose code review agent that evaluates code across six dimensions: correctness, security, performance, code quality, test coverage, and project standards alignment. Not WordPress-specific, but works well in any WooCommerce project context.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and configured

## Installation

See the [Installation Guide](docs/installation.md) for detailed setup instructions.

### Quick Start

Clone this repository:

```bash
git clone https://github.com/Automattic/claude-woocommerce-toolkit.git
```

**Install skills** (copy or symlink into your Claude Code skills directory):

```bash
# Global installation (available in all projects)
cp -r claude-woocommerce-toolkit/skills/woocommerce-plugin-dev ~/.claude/skills/
cp -r claude-woocommerce-toolkit/skills/woocommerce-finalize ~/.claude/skills/
cp -r claude-woocommerce-toolkit/skills/woocommerce-upgrade-safety ~/.claude/skills/

# Project-level installation (available only in one project)
cp -r claude-woocommerce-toolkit/skills/* /path/to/your/project/.claude/skills/
```

**Install the agents** (copy or symlink into your Claude Code agents directory):

```bash
# Global installation
cp claude-woocommerce-toolkit/agents/*.md ~/.claude/agents/

# Project-level installation
cp claude-woocommerce-toolkit/agents/*.md /path/to/your/project/.claude/agents/
```

## Usage

### WooCommerce Plugin Dev Skill

The skill triggers automatically when you mention building a WooCommerce plugin. You can also invoke it directly:

```
> I want to build a WooCommerce plugin that adds a loyalty points system

Claude will conduct a project discovery interview before writing any code,
then scaffold and build following all standards in the reference docs.
```

Example trigger phrases:
- "Build a WooCommerce plugin..."
- "Create a payment gateway extension..."
- "Start a new Woo extension for..."
- "Scaffold a shipping method plugin..."

### UX Payments Reviewer Agent

The agent is invoked automatically when you complete UX-critical work, or you can request a review:

```
> Can you review the checkout flow I just built?

Claude will launch the UX reviewer agent to assess clarity, trust signals,
error handling, accessibility, mobile responsiveness, and conversion impact.
```

### Code Reviewer Agent

Triggered after completing a logical chunk of code:

```
> I've finished the payment gateway class, can you review it?

Claude will launch the code reviewer agent to check correctness, security,
performance, code quality, test coverage, and standards alignment.
```

## Non-Negotiable Standards

The WooCommerce plugin dev skill enforces these rules on every file:

1. **HPOS compatibility is mandatory** — use WooCommerce CRUD, never `get_post_meta()` for orders
2. **All user input is hostile** — sanitize on input, escape on output, prepared statements for DB
3. **Nonces and capability checks on every form and AJAX handler**
4. **Every public function has a PHPDoc block** with `@since`, `@param`, `@return`
5. **No direct database queries** when WooCommerce/WordPress provides an API
6. **All strings are translatable** using the plugin's text domain
7. **Tests exist for every feature** — unit, integration, and E2E for user-facing flows
8. **Prefix everything** — functions, hooks, options, meta keys, REST routes
9. **WordPress enqueue system** for all scripts and styles
10. **Declare all WooCommerce feature compatibility** via `FeaturesUtil`

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on proposing changes, adding reference docs, and submitting evals.

## License

This project is licensed under the GPL v2 or later — see the [LICENSE](LICENSE) file for details.
