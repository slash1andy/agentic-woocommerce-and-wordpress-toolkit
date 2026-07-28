# Marketplace Submission & Distribution

Use this reference when preparing distribution, not while choosing ordinary implementation structure.
Confirm program details against maintained official sources at submission time.

**Official sources:**
- WooCommerce QIT live index: https://qit.woo.com/docs/llms.txt
- WooCommerce QIT getting started: https://qit.woo.com/docs/getting-started/
- WooCommerce Marketplace / Sell on WooCommerce.com: https://woocommerce.com/document/marketplace-overview/
- WordPress.org detailed plugin guidelines: https://developer.wordpress.org/plugins/wordpress-org/detailed-plugin-guidelines/
- WordPress Accessibility Coding Standards: https://make.wordpress.org/accessibility/handbook/

## QIT

Use the maintained QIT plugin and documentation for current installation, authentication, managed-test,
and test-package commands. Do not copy a broad command catalog into project instructions. The existing
contract test expects the current PHP compatibility spelling:

```bash
qit run:phpcompatibility my-plugin
```

Recheck that command and all other options in the live QIT index before use. QIT complements the
project's focused tests; it does not replace them.

## WooCommerce Marketplace

Choose Marketplace, WordPress.org, or private distribution during discovery because each has different
technical, support, licensing, and listing gates. For Marketplace work, verify applicable QIT results,
implemented Woo feature declarations, package contents, security, accessibility, support expectations,
and truthful compatibility metadata.

Preparation and review are read-only. Obtain explicit approval before you authenticate, upload, submit,
or publish. Never infer that a passing local check authorizes a marketplace action.

## WordPress.org and Serviceware

For WordPress.org distribution, shipped code cannot be payment-locked: local plugin functionality may
not expire, become arbitrary trialware, or require payment merely to unlock code already shipped.

A substantive external service may charge for processing, storage, content, computation, or another
real hosted capability the plugin consumes. The connector remains GPL-compatible and useful for that
service, with the dependency, data flow, terms, and pricing disclosed.

License-only validation or routing arbitrary local functionality through a nominal service is not
serviceware and is not allowed. Off-directory premium add-ons may provide separate code under the
applicable directory rules; do not disguise a local feature lock as a hosted service.

## Licensing and Human Accountability

WordPress.org's detailed plugin guidelines do not require an AI-assistance disclosure. Regardless of
tooling, verify code and asset provenance, GPL compatibility, third-party notices, and generated
artifacts. A human remains accountable for correctness, security, accessibility, and licensing.

## Pre-Submission Check

- [ ] Applicable project tests and current QIT checks pass using official instructions.
- [ ] Declared HPOS, Blocks, and other Woo feature compatibility has implementation evidence.
- [ ] Package excludes secrets, development artifacts, caches, and unshipped source assumptions.
- [ ] `readme.txt`, version/support metadata, changelog, upgrade notices, screenshots, and listing claims
      match the artifact actually reviewed.
- [ ] Security/privacy review is complete, including PCI payment-page controls when applicable.
- [ ] New and changed UI meets WCAG 2.2 AA.
- [ ] Distribution terms satisfy the serviceware distinction and license provenance is recorded.
- [ ] Authentication, upload, submission, and publication remain behind explicit approval.
