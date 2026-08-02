# PCI DSS payment page script management reference

Use this reference for the **PCI DSS v4.0.1 ecommerce script management requirements** that became
mandatory on **31 March 2025**. It complements `references/security.md` by covering payment page
script authorization, integrity, inventory, and tamper detection.

> **Not legal/compliance advice.** PCI scope depends on your exact integration model and your
> acquirer's requirements. Confirm your obligations with a Qualified Security Assessor (QSA) and your
> acquiring bank, and work from the current Self-Assessment Questionnaire (SAQ) for your model.

**Official sources:**
- PCI Security Standards Council (document library, SAQs, v4.0.1): https://www.pcisecuritystandards.org/
- PCI DSS v4.0.1 standard and the SAQ A / A-EP / D documents (from the PCI SSC library).

---

## The two requirements (mandatory since 31 March 2025)

| Requirement | What it asks for |
|-------------|------------------|
| **6.4.3 — Manage payment-page scripts** | All scripts loaded and executed in the consumer's browser on a payment page are (a) **authorized**, (b) **integrity-assured**, and (c) **inventoried** with written justification for each. |
| **11.6.1 — Detect tampering** | A **change- and tamper-detection mechanism** alerts personnel to unauthorized modification of the HTTP headers and the content of payment pages as received by the consumer's browser, evaluated **at least weekly** (or at a frequency set by a targeted risk analysis). |

Together they target **digital skimming / Magecart** attacks, where injected or modified JavaScript on
a checkout page silently exfiltrates card data.

---

## What it means for a WooCommerce payment plugin

Choose the integration model first. It determines where card data enters and how much payment page
script management falls on the merchant:

| Integration model | Card data touches the merchant page? | Typical SAQ | Script-management exposure |
|-------------------|--------------------------------------|-------------|----------------------------|
| **Hosted payment page / full redirect** | No | SAQ A (lowest) | Minimal — the PAN is entered off-site |
| **iframe to the provider (PCI-compliant)** | No (entered inside the provider's iframe) | SAQ A | Low — keep the surrounding page clean |
| **Direct post / fields rendered by the plugin** | Yes | SAQ A-EP / D | High — 6.4.3 / 11.6.1 squarely apply |

Prefer provider-hosted fields, an iframe, or browser tokenization that keeps the PAN out of the
merchant DOM. A gateway that renders raw card fields on the checkout page creates the broadest scope.

> Use the current SAQ A and confirm scope with the merchant's QSA or acquirer. Do not rely on an older
> SAQ A because the eligibility criteria and application of requirements 6.4.3 and 11.6.1 changed.

---

## Practical guidance for the plugin

Reduce the merchant's compliance burden:

- **Keep the PAN off the merchant page.** Use the provider's hosted fields / iframe / browser SDK so
  card data is entered in the provider's context, not your plugin's DOM.
- **Load only what checkout needs from trusted origins.** Do not add analytics, A/B testing, chat, or
  unrelated third-party scripts to the payment page. Enqueue checkout scripts through the
  WordPress enqueue system with a pinned, versioned source.
- **Support script integrity.** Make payment page scripts integrity-checkable where possible, such as
  through Subresource Integrity or a Content Security Policy the merchant can adopt. Document exactly
  which scripts the plugin adds and why; that inventory and justification is the merchant's 6.4.3
  evidence for your part of the page.
- **Document the checkout script footprint:** list the scripts the plugin enqueues on
  cart/checkout, their origins, and their purpose, so a merchant can fold it into their 6.4.3 inventory
  and their 11.6.1 monitoring baseline.
- **Never log or transmit card data**, and never store PAN/CVV — consistent with the financial-data
  rules in `references/security.md`. Tokenize via the provider.

---

## Checklist

- [ ] Integration model keeps the PAN out of the merchant DOM where possible (hosted fields / iframe / redirect).
- [ ] No unnecessary third-party scripts loaded on cart/checkout pages.
- [ ] Checkout scripts enqueued via the WP enqueue system, from a pinned/versioned trusted source, and
      made integrity-checkable (SRI/CSP-friendly).
- [ ] Plugin documents the scripts it adds to payment pages (inventory + justification) to support
      merchant 6.4.3 / 11.6.1 evidence.
- [ ] No PAN/CVV stored, logged, or transmitted; tokenization via the provider (`references/security.md`).
- [ ] PCI scope and SAQ type confirmed for the integration model with a QSA / acquirer.
