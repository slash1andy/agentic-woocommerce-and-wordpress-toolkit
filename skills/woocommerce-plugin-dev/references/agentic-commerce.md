# Agentic Commerce Readiness Reference

This reference covers what a WooCommerce commerce or payment extension should consider so that it
works well when **AI agents shop, operate, or buy** on a store. It is forward-looking and the
ecosystem is moving quickly, so treat specific endpoint names, feature flags, and protocol versions
as *verify-at-build-time* and confirm them against the official WooCommerce changelog and the
protocol specs before relying on them.

**Official sources:**
- WooCommerce AI & agentic commerce overview: https://developer.woocommerce.com/docs/getting-started/ai/
- WooCommerce MCP integration: https://developer.woocommerce.com/docs/features/mcp/
- WordPress Abilities API + MCP (see the companion reference): `references/abilities-and-mcp.md`
- Model Context Protocol: https://modelcontextprotocol.io/
- Agentic Commerce Protocol (ACP): https://www.agenticcommerce.dev/
- Store API (the headless/programmatic surface): https://github.com/woocommerce/woocommerce/tree/trunk/plugins/woocommerce/src/StoreApi

---

## Two distinct tracks (don't conflate them)

"Agentic commerce" covers two different problems with different protocols. Decide which one(s) the
plugin needs:

| Track | Question it answers | Mechanism |
|-------|--------------------|-----------|
| **1. Agent *operation / visibility*** | "Can an AI agent read and operate this store/extension safely?" | **WordPress Abilities API + MCP** (WordPress-native, first-party in WooCommerce). See `references/abilities-and-mcp.md`. |
| **2. Agent *purchasing*** | "Can a shopper complete a purchase from inside an AI assistant?" | **Agentic checkout protocols** layered on the store's programmatic checkout. |

Track 1 is the WordPress-native, in-platform path and is the one most extensions can act on today
(register read-only abilities, expose them through MCP). Track 2 is an emerging, payments-centric
layer driven by external protocols and platform partners.

---

## Track 1 — Agent operation via Abilities + MCP

This is fully covered in `references/abilities-and-mcp.md`. In short: register your extension's safe
operations as **Abilities** (`wp_register_ability` on `wp_abilities_api_init`), gate each with a real
`permission_callback`, default to read-only, and opt commerce abilities into the **WooCommerce MCP
server** (`woocommerce_mcp_include_ability`). WooCommerce shipped MCP as a beta in 10.3 and introduced
canonical product/order abilities in 10.9; extension-owned read abilities (subscriptions, payments,
shipping, etc.) build on the same pattern.

---

## Track 2 — Agentic checkout protocols

When a shopper buys from inside an AI assistant, the agent needs three things from the store: a
**machine-readable product feed** to discover items, a **programmatic (sessionless) checkout** to
place the order without driving the browser UI, and a **delegated payment** mechanism so the agent
can pay on the shopper's behalf without handling raw card data. Two open protocols address this; they
are **different efforts** and should not be merged in a developer's mind:

| Protocol | Backers | Notes |
|----------|---------|-------|
| **ACP — Agentic Commerce Protocol** | OpenAI + Stripe | Powers ChatGPT "Instant Checkout." Defines a product feed, an Agentic Checkout session, and delegated/"shared" payment tokens. The business remains **merchant of record** and keeps the customer relationship. |
| **AP2 — Agent Payments Protocol** | Google (and a broad set of partners) | A separate protocol centered on cryptographically-signed payment *mandates*. Not the same as ACP. |

For WooCommerce specifically:
- **Stripe's Agentic Commerce Suite** launched with **WooCommerce named as a launch partner**; the
  supported route reaches a Woo store through the official Stripe extension rather than a bespoke
  per-store integration. Verify current availability and the exact integration path in the Stripe and
  WooCommerce docs before building against it.
- A **community ecosystem of ACP plugins** also exists on WordPress.org. These let a store publish a
  feed and a checkout endpoint today; evaluate them like any third-party extension (security, support,
  merchant-of-record implications).

Because these protocols and WooCommerce's native endpoints are evolving, **do not hard-code protocol
endpoints or assume a native gateway feature flag exists** without confirming it in the current
WooCommerce release notes.

---

## Agentic-readiness checklist for a commerce / payment extension

The toolkit already teaches the primitives below — this checklist assembles them into the
agent-facing pattern. Adopt the items that fit the plugin's role:

- [ ] **Discoverability.** Expose a machine-readable, structured view of the relevant catalog/data —
      via the Store API (`wc/store/v1`), the REST API, and/or registered read-only Abilities (Track 1).
- [ ] **Programmatic checkout.** Where the plugin touches checkout, keep the **Store API** path correct
      and stateless (it does not fire classic checkout PHP hooks — see `references/woocommerce-apis.md`).
      A sessionless, headless checkout is the substrate every agentic-checkout protocol builds on.
- [ ] **Delegated payment.** For payment gateways, understand how your gateway participates in delegated
      / shared-payment-token flows (e.g. via the partner suite for ACP) and that the merchant stays
      merchant of record. Never expose raw PAN/credentials to an agent.
- [ ] **Real-time, machine-readable inventory & availability** so an agent doesn't sell what isn't there.
- [ ] **Safe operations as Abilities (Track 1)**, read-only first, each behind a `permission_callback`.
- [ ] **Feature declaration.** If/when WooCommerce exposes a gateway-level agentic feature flag, declare
      it via `FeaturesUtil::declare_compatibility()` only after verifying the flag name in the changelog
      and testing the integration — the same discipline used for `custom_order_tables` and
      `cart_checkout_blocks`.

## How this maps to what the toolkit already covers

| Agentic need | Existing toolkit material |
|--------------|---------------------------|
| Discovery feed / programmatic reads | `references/woocommerce-apis.md` — Store API, REST API v3, custom endpoints |
| Sessionless checkout | `references/woocommerce-apis.md` — Store API & block checkout extensibility |
| Capability registration for agents | `references/abilities-and-mcp.md` |
| Feature compatibility flags | `references/plugin-architecture.md` — `FeaturesUtil::declare_compatibility()` |
| Privileged-surface security | `references/security.md` — capability checks, permission callbacks, secret handling |

The gap agentic readiness fills is not new plumbing — it is **connecting the plumbing the plugin
already has to agent-facing discovery, checkout, and operation**, and doing so behind the same
permission and secret-handling rules the rest of this toolkit enforces.
