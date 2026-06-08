# Marketplace Submission & Distribution Reference

This reference covers what it takes to **distribute** a WooCommerce plugin — passing automated
quality testing, the WooCommerce Marketplace submission/review process, and the WordPress.org
plugin-directory rules — as opposed to *building* the plugin (covered by the other references).
Confirm current specifics against the official docs at build time; programs and thresholds change.

**Official sources:**
- WooCommerce QIT (Quality Insights Toolkit): https://qit.woo.com/docs/
- WooCommerce Marketplace / "Sell on WooCommerce.com": https://woocommerce.com/document/marketplace-overview/
- WordPress.org detailed plugin guidelines: https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/
- WordPress.org AI guidelines (AI hub): https://make.wordpress.org/ai/
- WordPress Accessibility Coding Standards: https://make.wordpress.org/accessibility/handbook/

---

## Table of Contents
1. [QIT — Quality Insights Toolkit](#qit--quality-insights-toolkit)
2. [WooCommerce Marketplace submission](#woocommerce-marketplace-submission)
3. [WordPress.org distribution rules](#wordpressorg-distribution-rules)
4. [AI-assisted code disclosure](#ai-assisted-code-disclosure)
5. [Pre-submission checklist](#pre-submission-checklist)

---

## QIT — Quality Insights Toolkit

**QIT is the automated quality gate for WooCommerce Marketplace products.** Run it *before* you
submit (and before every update) so review is a formality, not a discovery surface. QIT runs a suite
of managed tests Woo executes against your extension; the suite includes (confirm the current list at
qit.woo.com):

| Managed test | Catches |
|--------------|---------|
| **Activation** | Fatal errors / warnings on install + activate against supported WP/WC/PHP |
| **Security** | Common vulnerability classes (injection, missing auth, unsafe output) |
| **PHPStan** | Static-analysis defects |
| **PHP Compatibility** | Incompatibilities across the supported PHP range |
| **Malware** | Known-bad code signatures |
| **Woo E2E / Woo API** | Storefront/admin flows and REST behavior against a live store |

Run them locally with the QIT CLI:

```bash
# Install the CLI (see qit.woo.com/docs for the current install method).
composer global require woocommerce/qit-cli

# Run a managed test against your plugin.
qit run:activation   my-plugin
qit run:security     my-plugin
qit run:phpstan      my-plugin
qit run:php-compatibility my-plugin --php_version=8.3
```

These complement, not replace, your own PHPUnit/Playwright suites (`references/testing.md`). For
custom end-to-end coverage that QIT can run and combine across plugins, package Playwright specs as a
**QIT Test Package** (see qit.woo.com/docs) rather than the older e2e boilerplate.

---

## WooCommerce Marketplace submission

Submitting to the Marketplace is both a **technical** gate (QIT + the standards in this toolkit) and a
**business** review (product fit, support commitment, listing quality). Expect:

- A clean QIT pass and compliance with WP/WC coding, security, and UX standards.
- Declared compatibility for the relevant WooCommerce features — HPOS (`custom_order_tables`) and
  Cart/Checkout Blocks (`cart_checkout_blocks`) — actually tested, not just declared
  (`references/plugin-architecture.md`).
- A human review that can take **several weeks**; plan releases accordingly.

Decide the distribution channel during Phase 1 discovery, because it changes the requirements: the
**WooCommerce Marketplace** (QIT + business review), **WordPress.org** (directory guidelines below),
or **private/self-distributed** (your own update server, fewer external gates).

---

## WordPress.org distribution rules

If the plugin is listed on WordPress.org, the directory guidelines apply. The rule that most often
trips up commercial and payment plugins is the **trialware prohibition**:

- **No trialware.** A plugin may not lock its hosted functionality behind a payment/upgrade, disable
  itself after a trial or quota, or require a paid key to do anything useful. "Sandbox-only until you
  pay" generally counts as a disallowed trial.
- **Serviceware is allowed.** Ship the plugin's code fully open; premium value can live behind a
  **hosted service** the plugin talks to (this is the standard model for a payment gateway: the gateway
  integration code is open; the processing happens on the provider's service). Off-directory premium
  add-ons are also fine.
- Standard hygiene applies: GPL-compatible license, no obfuscated/"phone-home"-without-disclosure code,
  a truthful `readme.txt`, and no tracking without consent.

A payment gateway is usually a natural fit for serviceware: the connector is open-source on .org; the
money movement and any premium features run on the provider's hosted service.

---

## AI-assisted code disclosure

Because this toolkit *generates* plugin code with an AI assistant, follow WordPress.org's guidance on
AI-assisted contributions when distributing there (see the AI hub, make.wordpress.org/ai):

- **Disclose** meaningful AI assistance in the plugin where required.
- Ensure AI-generated code and assets are **GPL-compatible** and that you have the right to license them.
- Keep a **human accountable** for the submitted result — AI assistance does not transfer responsibility
  for correctness, security, or licensing.

---

## Pre-submission checklist

- [ ] QIT managed tests (activation, security, PHPStan, PHP compatibility, malware) pass locally.
- [ ] Own PHPUnit + Playwright/E2E suites green; custom E2E packaged as a QIT Test Package if applicable.
- [ ] HPOS + Cart/Checkout Blocks compatibility declared **and tested**.
- [ ] `readme.txt` accurate: `Requires at least`, `Requires PHP`, `WC requires at least`, `WC tested up to`
      current; changelog + upgrade notice present (`references/plugin-architecture.md`, upgrade-safety skill).
- [ ] Meets the **WordPress Accessibility Coding Standards** (WCAG 2.1 AA baseline; see `references/ux-guidelines.md`).
- [ ] Distribution channel chosen; for .org, serviceware (not trialware); AI-assistance disclosure handled.
- [ ] Security review complete (`references/security.md`), including PCI script-management where payments
      are involved (`references/pci-script-management.md`).
