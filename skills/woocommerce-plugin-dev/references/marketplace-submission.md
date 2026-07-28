# Marketplace Submission & Distribution Reference

This reference covers what it takes to **distribute** a WooCommerce plugin — passing automated
quality testing, the WooCommerce Marketplace submission/review process, and the WordPress.org
plugin-directory rules — as opposed to *building* the plugin (covered by the other references).
Confirm current specifics against the official docs at build time; programs and thresholds change.

**Official sources:**
- WooCommerce QIT live index: https://qit.woo.com/docs/llms.txt
- WooCommerce QIT getting started: https://qit.woo.com/docs/getting-started/
- WooCommerce Marketplace / "Sell on WooCommerce.com": https://woocommerce.com/document/marketplace-overview/
- WordPress.org detailed plugin guidelines: https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/
- WordPress Accessibility Coding Standards: https://make.wordpress.org/accessibility/handbook/

---

## Table of Contents
1. [QIT — Quality Insights Toolkit](#qit--quality-insights-toolkit)
2. [WooCommerce Marketplace submission](#woocommerce-marketplace-submission)
3. [WordPress.org distribution rules](#wordpressorg-distribution-rules)
4. [Licensing and human accountability](#licensing-and-human-accountability)
5. [Pre-submission checklist](#pre-submission-checklist)

---

## QIT — Quality Insights Toolkit

QIT test types, options, and install commands change. Use the current QIT documentation and live
`llms.txt` index above instead of copying a broad managed-test catalog into project instructions.
The PHP compatibility command is:

```bash
qit run:phpcompatibility my-plugin
```

Use the current QIT docs for every other command and for test-package guidance. QIT complements,
rather than replaces, the project's own focused test suite (`references/testing.md`).

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

## Licensing and human accountability

WordPress.org's detailed plugin guidelines do not require an AI-assistance disclosure. Regardless of
tooling, ensure submitted code and assets are GPL-compatible, preserve truthful license provenance,
and keep a human accountable for correctness, security, and licensing.

---

## Pre-submission checklist

Preparing artifacts and findings is read-only. Obtain explicit approval before you authenticate,
upload, submit, or publish to a marketplace or directory.

- [ ] Current applicable QIT tests pass using commands from the official QIT docs.
- [ ] The project's own applicable tests pass; use a QIT Test Package only when the project needs one.
- [ ] HPOS + Cart/Checkout Blocks compatibility declared **and tested**.
- [ ] `readme.txt` accurate: `Requires at least`, `Requires PHP`, `WC requires at least`, `WC tested up to`
      current; changelog + upgrade notice present (`references/plugin-architecture.md`, upgrade-safety skill).
- [ ] Meets the **WordPress Accessibility Coding Standards** (WCAG 2.1 AA baseline; see `references/ux-guidelines.md`).
- [ ] Distribution channel chosen; for .org, serviceware (not trialware); licensing provenance verified.
- [ ] Security review complete (`references/security.md`), including PCI script-management where payments
      are involved (`references/pci-script-management.md`).
