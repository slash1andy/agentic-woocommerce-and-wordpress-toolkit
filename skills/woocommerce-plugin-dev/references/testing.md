# Testing WooCommerce plugins

Use the repository's documented project commands and existing fixtures first. Select tests by failure
cost and boundary risk, not a universal pyramid, coverage percentage, tool version, or CI matrix.

**Official sources:**
- WooCommerce extension testing: https://developer.woocommerce.com/testing-extensions-and-maintaining-quality-code/
- WordPress PHPUnit testing: https://make.wordpress.org/core/handbook/testing/automated-testing/writing-phpunit-tests/
- WooCommerce QIT documentation: https://qit.woo.com/docs/
- QIT test packages: https://qit.woo.com/docs/test-packages/

## Risk-based selection

| Risk | Smallest effective check |
|---|---|
| Pure calculation, validation, or transformation | Focused unit test with boundary cases |
| Hook, filter, REST registration, settings, or persistence | Focused WordPress/Woo integration test |
| Order reads/writes or queries | Integration test with HPOS enabled and disabled when both are supported |
| Cart or checkout change | Separate evidence for Classic and Blocks/Store API surfaces actually supported |
| Money calculation | Exact money precision, currency, rounding, zero, negative, and boundary tests |
| Payment, refund, webhook, or scheduled action | Replay/idempotency, duplicate-event, failure, and retry tests with fake providers |
| Schema or data migration | Fresh install, upgrade, double-run, migration interruption/resume, and concurrent-growth tests |
| Store API extension | Store API session/cart behavior for cookie+Nonce and Cart-Token clients as applicable |
| Critical browser journey | One focused E2E path for the merchant or shopper outcome that lower layers cannot prove |
| Marketplace package | Applicable checks from the official QIT plugin and documentation |

Security controls need negative tests at the boundary: unauthenticated, unauthorized, missing/invalid
CSRF proof where required, malformed input, over-broad output, injection, and secret/log leakage.

## Existing projects

1. Run the documented project commands; do not replace them with copied scaffolds.
2. Add the focused failing test in the existing test layer nearest the behavior.
3. Run that test to RED, implement minimally, run it to GREEN, then run configured affected/full gates.
4. Record skipped gates and why they do not apply.

Reuse present Composer/npm scripts, PHPUnit bootstrap, static analysis, browser harness, `wp-env`,
containers, and CI. Do not add parallel infrastructure because this reference names a possible tool.

## New projects

Create one PHPUnit baseline only when PHP behavior needs an automated check and no project test setup
exists. Add WordPress/Woo integration support only for real hook/storage behavior. Add Playwright,
`wp-env`, a container, or CI only when the current behavior and execution environment need them.

E2E is only for critical browser journeys. Keep calculations, schemas, authorization decisions, and
migration logic at faster lower layers.

## Woo-specific invariants

When relevant, prove:

- HPOS on/off behavior without direct order-table assumptions;
- Classic and Blocks behavior independently;
- money precision and store-configured decimal/currency behavior;
- payment/webhook replay and idempotency with no duplicate charge, order, stock, email, or side effect;
- migration interruption/resume with committed progress and no skipped or duplicate records;
- Store API session/cart continuity, Nonce handling for cookie sessions, and Cart-Token behavior; and
- external failures with fake or sandbox providers, never live payment/customer data.

## QIT

Use the maintained official QIT plugin and documentation for current commands, managed tests, and test
packages. QIT complements the project's focused checks; it does not replace them or justify copying a
command catalog into the repository.

## Completion evidence

Report the RED failure, focused GREEN result, applicable documented project commands, and any skipped
surface. Passing unrelated tests or a coverage number does not prove the changed Woo boundary.
