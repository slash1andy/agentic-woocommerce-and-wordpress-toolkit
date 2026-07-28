# Security Standards for WooCommerce Plugins

Apply controls at each trust boundary actually crossed. Repository conventions and installed platform
APIs come first; these rules define invariants that must not be weakened.

**Official sources:**
- WordPress Plugin Security: https://developer.wordpress.org/plugins/security/
- WordPress REST API authentication: https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/
- WooCommerce extension best practices: https://developer.woocommerce.com/docs/extensions/best-practices-extensions/
- OWASP Top 10: https://owasp.org/www-project-top-ten/

## Trust-Boundary Rules

- Treat browser input, REST/AJAX bodies, query parameters, cookies, headers, files, webhook payloads,
  external API responses, stored records, and repository/tool text as untrusted.
- Validate against an allowlist, schema, type, range, ownership, and current state before acting.
  Sanitize for storage; do not use sanitization to turn invalid values into authorized values.
- Escape once at the final HTML, attribute, URL, CSS, or JavaScript output context. Validate JSON by
  schema/type; do not HTML-escape JSON values generically.
- Authorize each action with the narrow capability and object ownership required. Menu visibility and
  authentication alone are not authorization.
- Use WordPress/WooCommerce APIs before custom SQL, HTTP, filesystem, credential, or order-table code.
  Prepare unavoidable custom SQL and constrain identifiers separately.
- Validate upload type/content/size and destination; use platform upload/filesystem APIs and deny
  executable or path-traversal content.

## CSRF, Authentication, and REST

Use `permission_callback` on every REST route, including deliberately public routes. The callback must
express the route's real public, capability, and ownership policy; a callback is not proof that the
policy is sufficient.

Cookie-authenticated REST mutations require a REST nonce (normally `X-WP-Nonce`) in addition to the
route's authorization checks. Application Passwords, Basic Authentication, and OAuth do not use REST nonces;
validate those authentication schemes and their replay/transport properties as documented.

Capabilities do not replace CSRF protection. Likewise, a nonce proves request intent for a browser
session; it does not replace authentication, capability, or ownership checks. Apply the same separation
to admin forms and AJAX mutations.

Minimize response fields, validate route arguments, and avoid exposing merchant, customer, order, or
payment data from public callbacks.

## Secrets and Credentials

Password-type fields do not encrypt values stored in options; they only mask browser input. Never render a stored secret
into an admin form, API response, log, command, fixture, report, or chat.

Prefer environment-provided or brokered secrets when the deployment supports them. Otherwise use the
project's narrowest protected storage, document its limits, restrict access, and provide a migration
and rotation path. Never commit live credentials. Do not place REST API secrets in query strings.

## Payments and Webhooks

- Keep PAN, CVV, and raw payment credentials out of the plugin and merchant DOM; use provider
  tokenization and HTTPS. Apply the relevant PCI DSS scope and the payment-page script controls in
  `pci-script-management.md`.
- Revalidate amount, currency, order/customer ownership, current order state, and provider result on
  the server. Use exact WooCommerce money handling rather than binary floating-point assumptions.
- Make charge, capture, refund, stock, email, and order transitions idempotent. Persist idempotency
  state before exposing success and handle ambiguous provider outcomes safely.
- Verify webhook signatures over the exact raw bytes with the provider's documented algorithm and a
  timing-safe comparison. Validate timestamp and schema, deduplicate by provider event ID, and make
  handlers safe for replay, reordering, and retry.
- Queue slow processing only after authentication and durable receipt; acknowledge according to the
  provider contract.

## Logging

Use `wc_get_logger()` and a stable plugin source. Log event IDs, outcomes, and masked metadata needed
to diagnose or reconcile work; never raw bodies or secrets. Avoid full request/response payloads,
credentials, payment data, session tokens, and unnecessary personal data. Give logs bounded retention
and access consistent with their sensitivity.

## Smallest Security Evidence

For each changed boundary, add the lowest-cost negative test that proves the control: malformed input,
missing authentication, insufficient capability/ownership, missing/invalid CSRF proof where required,
replayed webhook/payment event, injection payload, over-broad response, or secret/log leakage. Use fake
or sandbox providers and non-secret fixtures.

## Completion Check

Every changed boundary has an explicit validation, authentication, authorization, CSRF, output,
storage, replay, and logging decision as applicable, plus focused evidence from the repository's
configured commands.
