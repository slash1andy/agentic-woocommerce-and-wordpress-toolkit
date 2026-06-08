# PCI DSS Payment-Page Script Management Reference

This reference covers the **PCI DSS v4.0.1 e-commerce script-management requirements** that became
mandatory on **31 March 2025** — the single biggest e-commerce change in recent PCI DSS revisions —
and what they mean for a WooCommerce payment plugin. It complements the general
`references/security.md`; that file covers sanitization, escaping, nonces, capabilities, and secret
handling, while this one covers the payment-page integrity requirements specifically.

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

How much of this lands on the *merchant* vs. the *plugin* depends on the integration model — but the
plugin's design heavily influences which model is even available:

| Integration model | Card data touches the merchant page? | Typical SAQ | Script-management exposure |
|-------------------|--------------------------------------|-------------|----------------------------|
| **Hosted payment page / full redirect** | No | SAQ A (lowest) | Minimal — the PAN is entered off-site |
| **iframe to the provider (PCI-compliant)** | No (entered inside the provider's iframe) | SAQ A | Low — keep the surrounding page clean |
| **Direct post / fields rendered by the plugin** | Yes | SAQ A-EP / D | High — 6.4.3 / 11.6.1 squarely apply |

**Design implication:** prefer an integration that keeps the PAN out of the merchant's DOM (a
provider-hosted field/iframe or tokenization in the browser via the provider's SDK). This is both the
more secure design and the one that minimizes the merchant's script-management burden. A gateway that
renders raw card fields on the checkout page pushes its merchants into the strictest scope.

> Note on SAQ A: recent SAQ A revisions changed how 6.4.3 / 11.6.1 apply to fully-outsourced
> (iframe/redirect) merchants and added eligibility attestations about not being susceptible to
> script-based attacks. Always work from the **current** SAQ A and confirm with your QSA/acquirer —
> do not assume an older SAQ's scope.

---

## Practical guidance for the plugin

A WooCommerce payment plugin should make its merchants' compliance *easier*, not harder:

- **Keep the PAN off the merchant page.** Use the provider's hosted fields / iframe / browser SDK so
  card data is entered in the provider's context, not your plugin's DOM.
- **Load only what's needed on checkout, from trusted origins.** Don't pull analytics, A/B, chat, or
  other third-party scripts onto the payment page. Enqueue your own checkout scripts through the
  WordPress enqueue system with a pinned, versioned source.
- **Support script integrity.** Where you load a script on the payment page, make it integrity-checkable
  (e.g. Subresource Integrity / a Content Security Policy the merchant can adopt) and document exactly
  which scripts your plugin adds and why — that inventory + justification is the merchant's 6.4.3
  evidence for your part of the page.
- **Document your checkout script footprint** in your plugin docs: the list of scripts you enqueue on
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
