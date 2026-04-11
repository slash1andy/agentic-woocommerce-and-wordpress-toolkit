---
name: woocommerce-plugin-dev
description: >
  Comprehensive WooCommerce plugin development skill that enforces WordPress and WooCommerce
  coding standards, security best practices, and end-to-end testing for every file created.
  Use this skill whenever the user wants to create, scaffold, build, or start a WooCommerce plugin,
  WooCommerce extension, or WordPress plugin that integrates with WooCommerce. Also trigger when
  the user mentions "WooCommerce plugin", "Woo extension", "WooCommerce add-on", "payment gateway
  plugin", "shipping method plugin", or any plugin that touches orders, products, carts, checkout,
  or the WooCommerce REST API. Even if the user just says "start a new plugin" in the context of a
  WooCommerce project, use this skill. This skill should be the first thing consulted before writing
  any code for a WooCommerce plugin project.
---

# WooCommerce Plugin Development Skill

This skill ensures that every WooCommerce plugin you build meets professional, marketplace-ready
standards from day one. It covers architecture, coding standards, security, testing, and UX —
drawing from the official WordPress Plugin Handbook, WooCommerce developer documentation, and
fintech-grade security practices.

## How This Skill Works

This skill operates in two phases:

1. **Project Discovery** — gather requirements via a structured interview and save them as a
   project brief
2. **Development Execution** — scaffold and build the plugin following all standards defined in
   the reference files

Every coding decision, file structure choice, and architectural pattern is governed by the
reference documents bundled with this skill. Read them before writing any code.

---

## Phase 1: Project Discovery

Before writing a single line of code, conduct a structured interview with the user. The goal is
to produce a `PROJECT_BRIEF.md` file that lives in the plugin's root directory and serves as the
single source of truth for all future development work.

### Required Interview Questions

Ask these questions conversationally, grouping related ones together. Don't dump them all at once —
have a dialogue.

**Market & Business Context:**
- What is the target market for this plugin? (e.g., small merchants, enterprise, specific industry)
- Will this be sold on the WooCommerce Marketplace, WordPress.org, or distributed privately?
- Are there competing plugins? What makes this one different?
- What WooCommerce and WordPress version minimums should we target?

**Plugin Purpose & Scope:**
- Describe the core purpose of this plugin in one or two sentences.
- What specific WooCommerce functionality does it extend or modify? (orders, products, checkout,
  shipping, payments, subscriptions, etc.)
- Does it need to integrate with any external APIs or third-party services?
- Does it handle any financial transactions, sensitive customer data, or PCI-relevant information?

**Customer/User-Facing Features:**
- What will the shopper/customer see or experience differently?
- Does it modify the cart, checkout, or my-account pages?
- Does it add any frontend blocks or shortcodes?
- What does the customer-facing UX flow look like, step by step?

**Admin/Merchant Features:**
- What settings or configuration options does the admin need?
- Does it add any WooCommerce admin pages, tabs, or panels?
- Does it add columns to order/product lists?
- Does it need reporting or analytics dashboards?
- What does the admin setup/onboarding flow look like?

**Technical Architecture:**
- Does it need custom database tables, or can it use post meta / order meta / options?
- Does it need background processing or scheduled tasks (WP-Cron / Action Scheduler)?
- Does it expose or consume REST API endpoints?
- Does it need to work with the block-based Cart and Checkout? (If it touches cart/checkout: yes.)
- Does it add product data panels? (If yes: must support the Product Block Editor.)
- Does it provide frontend templates or blocks? (If yes: must work with the Site Editor.)
- HPOS (High-Performance Order Storage) compatibility is mandatory — always declare it.
- Does it need to extend the Store API for block checkout integration?

**Data & Compliance:**
- What user/customer data does the plugin collect, store, or transmit?
- Are there GDPR, PCI-DSS, or other compliance requirements?
- Does it process payments directly or integrate with a payment gateway?

### Saving the Project Brief

After the interview, compile all answers into a `PROJECT_BRIEF.md` file with this structure:

```markdown
# Project Brief: [Plugin Name]

## Overview
[One-paragraph summary of the plugin]

## Target Market
[Market details, distribution channel, competitive landscape]

## Core Functionality
[Detailed description of what the plugin does]

## Customer-Facing Features
[Bulleted list of shopper-facing features with descriptions]

## Admin Features
[Bulleted list of merchant-facing features with descriptions]

## Technical Requirements
- Minimum WordPress version: X.X
- Minimum WooCommerce version: X.X
- Minimum PHP version: 8.0
- HPOS compatible: Yes (mandatory)
- Cart & Checkout Blocks compatible: [Yes/No]
- Product Block Editor compatible: [Yes/No]
- Site Editor compatible: [Yes/No]
- Store API extensions needed: [Yes/No — describe if yes]
- Custom database tables: [Yes/No — list if yes]
- External API integrations: [List]
- Background processing: [Yes/No — describe if yes]

## Data & Compliance
[What data is collected, stored, transmitted; compliance requirements]

## Out of Scope
[Explicitly list what this plugin does NOT do]
```

Save this file in the plugin root. Reference it before making any architectural decision.

---

## Phase 2: Development Execution

Once the project brief is complete, follow these steps in order. For each step, consult the
relevant reference file before proceeding.

### Step 1: Scaffold the Plugin Structure

Read `references/plugin-architecture.md` for the complete file structure template.

Every WooCommerce plugin follows this canonical structure:

```
plugin-slug/
├── plugin-slug.php              # Main plugin file (bootstrap)
├── uninstall.php                # Clean uninstall handler
├── readme.txt                   # WordPress.org readme
├── composer.json                # PHP dependencies & autoloading
├── package.json                 # JS/CSS build tooling
├── phpcs.xml.dist               # PHPCS configuration
├── phpunit.xml.dist             # PHPUnit configuration
├── playwright.config.ts         # Playwright E2E configuration
├── PROJECT_BRIEF.md             # Project brief from Phase 1
├── .github/
│   └── workflows/
│       ├── ci.yml               # Continuous integration
│       └── release.yml          # Release automation
├── src/                         # PSR-4 autoloaded PHP classes
│   ├── Plugin.php               # Main plugin class
│   ├── Admin/                   # Admin-only functionality
│   ├── Frontend/                # Frontend-only functionality
│   ├── API/                     # REST API endpoints
│   ├── Data/                    # Data stores and repositories
│   ├── Integrations/            # Third-party integrations
│   └── Utilities/               # Helper classes
├── includes/                    # Legacy-style includes (if needed)
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                   # Overridable templates
├── languages/                   # Translation files
├── tests/
│   ├── Unit/                    # PHPUnit unit tests
│   ├── Integration/             # PHPUnit integration tests
│   ├── E2E/                     # Playwright end-to-end tests
│   └── bootstrap.php            # Test bootstrap
└── vendor/                      # Composer dependencies (gitignored)
```

### Step 2: Write the Main Plugin File

The main plugin file (`plugin-slug.php`) must:

- Have a complete plugin header with all required fields
- Declare HPOS compatibility via `before_woocommerce_init`
- Check for WooCommerce activation before loading
- Use Composer autoloading (PSR-4)
- Define plugin constants (version, path, URL, basename)
- Hook into `plugins_loaded` at an appropriate priority

Read `references/coding-standards.md` for PHP formatting rules and naming conventions.

### Step 3: Implement Core Functionality

For every class and function you write:

1. **Read `references/coding-standards.md`** — Follow WordPress PHP Coding Standards, use proper
   naming conventions, document with PHPDoc blocks
2. **Read `references/security.md`** — Sanitize all input, escape all output, verify nonces and
   capabilities, use prepared statements
3. **Follow HPOS patterns** — Never access `wp_posts` / `wp_postmeta` for orders; always use
   WooCommerce CRUD methods and data stores
4. **Follow WooCommerce UX guidelines** — Use native WooCommerce UI components, respect admin
   color schemes, keep settings minimal with smart defaults

### Step 4: Write Tests

Read `references/testing.md` for the complete testing strategy.

Every feature must have corresponding tests before it's considered complete:

- **Unit tests** (PHPUnit) for all business logic, data transformations, and utility functions
- **Integration tests** (PHPUnit + WordPress test framework) for hooks, filters, database
  interactions, and WooCommerce API integration
- **E2E tests** (Playwright) for all user-facing flows — both admin and storefront
- **Security tests** for input validation, authentication, authorization, and injection resistance

For plugins that handle financial data, also include:

- **Idempotency tests** — verify that duplicate requests produce the same result
- **Race condition tests** — verify concurrent operations don't corrupt data
- **Boundary tests** — verify behavior at financial precision boundaries
- **Audit trail tests** — verify all financial operations are logged

### Step 5: Configure CI/CD

Set up GitHub Actions workflows that run:

- PHPCS with WordPress and WooCommerce coding standards
- PHPStan or Psalm for static analysis (level 6+ minimum)
- PHPUnit test suite
- Playwright E2E suite against a wp-env environment
- WooCommerce QIT compatibility checks

---

## Reference Files

These files contain detailed standards and patterns. Read the relevant file before working on
that aspect of the plugin.

| File | When to Read |
|------|-------------|
| `references/coding-standards.md` | Before writing any PHP, JS, CSS, or HTML |
| `references/security.md` | Before handling any user input, database queries, or API calls |
| `references/testing.md` | Before writing any test or configuring test infrastructure |
| `references/plugin-architecture.md` | When scaffolding the plugin or adding new components |
| `references/woocommerce-apis.md` | When integrating with WooCommerce data stores, hooks, or REST API |
| `references/ux-guidelines.md` | When building admin UI, settings pages, or frontend components |

---

## Non-Negotiable Standards

These apply to every single file in the project, no exceptions:

1. **HPOS compatibility is mandatory.** Never use `get_post_meta()` / `update_post_meta()` for
   order data. Use `$order->get_meta()` / `$order->update_meta_data()` and WooCommerce CRUD.

2. **All user input is hostile.** Sanitize on input (`sanitize_text_field`, `absint`,
   `sanitize_email`, etc.), escape on output (`esc_html`, `esc_attr`, `esc_url`, `wp_kses`),
   and use `$wpdb->prepare()` for all database queries.

3. **Nonces and capability checks on every form and AJAX handler.** No exceptions.

4. **Every public function has a PHPDoc block.** Include `@since`, `@param`, `@return`, and
   `@throws` tags.

5. **No direct database queries when WooCommerce or WordPress provides an API.** Use data stores,
   `WC_Order`, `WC_Product`, `WP_Query`, etc.

6. **All strings are translatable.** Use `__()`, `_e()`, `esc_html__()`, `esc_attr__()` with the
   plugin's text domain.

7. **Tests exist for every feature.** No feature is complete without unit and integration tests.
   User-facing features also need E2E tests.

8. **Prefix everything.** All functions, classes, hooks, options, meta keys, and REST routes use
   the plugin's unique prefix to avoid conflicts.

9. **Follow WordPress enqueue system.** Never inline scripts or styles except when absolutely
   necessary. Use `wp_enqueue_script` / `wp_enqueue_style` with proper dependencies.

10. **Declare all WooCommerce feature compatibility.** HPOS (`custom_order_tables`),
    Cart & Checkout Blocks (`cart_checkout_blocks`), and Product Block Editor
    (`product_block_editor`) — declare support for everything applicable via
    `before_woocommerce_init` using `FeaturesUtil::declare_compatibility()`. Test thoroughly
    with each feature enabled before declaring compatibility.
