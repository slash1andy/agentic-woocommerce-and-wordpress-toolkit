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

For a small change in a project with no test runner, keep a manual or ad-hoc check as the default. Create
one PHPUnit baseline only when the requested behavior or suite requires an automated PHP check, no project
test setup exists, and a smaller check is inadequate. Add WordPress/Woo integration support only for real hook/storage behavior. Add Playwright,
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
- external failures with fake or sandbox providers, never live payment/customer data; and
- version-scoped WooCommerce 11.1/11.2 behavior (missing Cart-Token headers failing closed,
  store-timezone date queries on HPOS and legacy storage, data-store and block-registration changes)
  from `woocommerce-apis.md`, only against targets that run those versions.

## Native REST tests

Apply this section only when full native REST integration tests are explicitly requested. Keep small
requests on the minimal-check default; minimum versions, approval requirements, and runtime claims do
not change.

Verify native authentication against the installed WordPress source and a real authentication response.
Check the hook name and context in the installed `wp-includes/user.php`; for example, WordPress 7.1.3
applies the singular filter `application_password_is_api_request` there. Do not use
`application_passwords_is_api_request` (plural): it is an incorrect name that core never applies, so
the filter silently does nothing. Application password authentication depends on that API-request
context, so confirm the real response (for example, a 200 versus a 401) rather than assuming it.

Keep native application password authentication real: do not replace it with replacement
authentication functions, do not bypass it, override the controller, or edit immutable generated tests
to hide an authentication failure. When a test deliberately simulates an API request,
add the real documented hook scoped to that test and remove it in teardown or cleanup. This is fixture
context, not an authentication bypass or production configuration.

Prove canonical discovery and execution for every intended HPOS and legacy class. Run
`phpunit --list-tests` (or the equivalent for the runner) and then the canonical test command, and
confirm that each class is both listed and executed. If the runner ignores additional classes in one
file, use one discoverable file per concrete class. Supplemental exact-class runs are separate evidence
and do not count as canonical coverage.

HPOS and legacy tests need a fresh, isolated database fixture for each storage mode, or verified real
WooCommerce CRUD cleanup and synchronization of orders before any storage mode switch. Do not assume
generic WordPress test rollback clears WooCommerce custom tables. Resetting the storage option in
teardown is a real mode transition, not harmless cleanup. A refusal from the native synchronization
guard is a fixture failure to fix, not a product defect.

Keep and preserve the synchronization guard in both HPOS and legacy runs; do not remove its filter,
alter the controller, or change authentication to get past it.

Never bypass the synchronization guard to turn a run green: do not force pending counts to zero, do not
disable the guard, and do not report a bypassed run as passing evidence.

## QIT

Use the maintained official QIT plugin and documentation for current commands, managed tests, and test
packages. QIT complements the project's focused checks; it does not replace them or justify copying a
command catalog into the repository.

## Completion evidence

Report the RED failure, focused GREEN result, applicable documented project commands, and any skipped
surface. Passing unrelated tests or a coverage number does not prove the changed Woo boundary.
