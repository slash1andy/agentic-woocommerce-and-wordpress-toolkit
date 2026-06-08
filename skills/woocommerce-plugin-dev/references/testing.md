# Testing Standards for WooCommerce Plugins

This reference covers the complete testing strategy for WooCommerce plugins, including unit tests,
integration tests, end-to-end tests, and security-specific tests. Every feature must have
corresponding tests before it is considered complete.

**Official sources:**
- WooCommerce Testing Guide: https://developer.woocommerce.com/testing-extensions-and-maintaining-quality-code/
- WooCommerce E2E with Playwright: https://github.com/woocommerce/woocommerce/tree/trunk/plugins/woocommerce/tests/e2e-pw
- WooCommerce QIT: https://qit.woo.com/docs/
- WordPress PHPUnit Testing: https://make.wordpress.org/core/handbook/testing/automated-testing/phpunit/

---

## Table of Contents
1. [Testing Pyramid](#testing-pyramid)
2. [PHPUnit Setup](#phpunit-setup)
3. [Unit Tests](#unit-tests)
4. [Integration Tests](#integration-tests)
5. [End-to-End Tests with Playwright](#end-to-end-tests-with-playwright)
6. [Security Testing](#security-testing)
7. [Financial / Fintech Testing](#financial--fintech-testing)
8. [Code Coverage Requirements](#code-coverage-requirements)
9. [CI Integration](#ci-integration)

---

## Testing Pyramid

Every WooCommerce plugin should have tests at three levels:

```
         /  E2E Tests  \           ~10% — User flows, critical paths
        / Integration    \         ~30% — WordPress/WooCommerce hooks, DB, APIs
       /  Unit Tests      \        ~60% — Business logic, data transforms, utilities
```

The ratio is approximate — the important thing is that unit tests form the base (fast, numerous,
isolated) and E2E tests are focused on critical user journeys.

---

## PHPUnit Setup

### phpunit.xml.dist

```xml
<?xml version="1.0"?>
<phpunit
	bootstrap="tests/bootstrap.php"
	backupGlobals="false"
	colors="true"
	convertErrorsToExceptions="true"
	convertNoticesToExceptions="true"
	convertWarningsToExceptions="true"
>
	<testsuites>
		<testsuite name="unit">
			<directory suffix="Test.php">./tests/Unit</directory>
		</testsuite>
		<testsuite name="integration">
			<directory suffix="Test.php">./tests/Integration</directory>
		</testsuite>
	</testsuites>
	<coverage>
		<include>
			<directory suffix=".php">./src</directory>
		</include>
		<exclude>
			<directory>./vendor</directory>
			<directory>./tests</directory>
		</exclude>
	</coverage>
</phpunit>
```

### tests/bootstrap.php

```php
<?php
/**
 * PHPUnit bootstrap file.
 *
 * @package PluginSlug\Tests
 */

// Load Composer autoloader.
require_once dirname( __DIR__ ) . '/vendor/autoload.php';

// Determine whether to load WordPress test framework.
$_tests_dir = getenv( 'WP_TESTS_DIR' );

if ( $_tests_dir ) {
	// Integration tests — load WordPress.
	$_core_dir = getenv( 'WP_CORE_DIR' ) ?: $_tests_dir . '/../../';

	require_once $_tests_dir . '/includes/functions.php';

	tests_add_filter( 'muplugins_loaded', function () {
		require dirname( __DIR__ ) . '/plugin-slug.php';
	} );

	require $_tests_dir . '/includes/bootstrap.php';
}
```

---

## Unit Tests

Unit tests verify isolated business logic with no WordPress or WooCommerce dependencies.
They should be fast (milliseconds per test) and numerous.

### What to Unit Test

- Data transformation and formatting functions
- Validation logic
- Calculation engines (prices, taxes, discounts, shipping rates)
- State machines and workflow logic
- Utility/helper functions
- API request/response serialization

### Example Unit Test

```php
<?php

namespace PluginSlug\Tests\Unit;

use PHPUnit\Framework\TestCase;
use PluginSlug\Utilities\Price_Calculator;

/**
 * Tests for the Price_Calculator class.
 *
 * @covers \PluginSlug\Utilities\Price_Calculator
 */
class Price_Calculator_Test extends TestCase {

	/**
	 * @dataProvider discount_provider
	 */
	public function test_calculate_discount( float $price, float $percent, float $expected ): void {
		$calculator = new Price_Calculator();
		$result     = $calculator->calculate_discount( $price, $percent );

		$this->assertSame( $expected, $result );
	}

	public function discount_provider(): array {
		return array(
			'10% off $100'   => array( 100.00, 10.0, 90.00 ),
			'25% off $49.99' => array( 49.99, 25.0, 37.49 ),
			'0% off $50'     => array( 50.00, 0.0, 50.00 ),
			'100% off $75'   => array( 75.00, 100.0, 0.00 ),
		);
	}

	public function test_negative_discount_throws(): void {
		$calculator = new Price_Calculator();

		$this->expectException( \InvalidArgumentException::class );
		$calculator->calculate_discount( 100.00, -5.0 );
	}
}
```

### Patterns

- Use `@dataProvider` for testing multiple inputs against the same logic
- Use `@covers` annotations to maintain code coverage mapping
- Mock external dependencies with PHPUnit mocks or libraries like Mockery
- Test edge cases: empty inputs, zero values, maximum values, Unicode, special characters

---

## Integration Tests

Integration tests verify that the plugin works correctly within the WordPress and WooCommerce
environment — hooks fire, data persists, APIs respond correctly.

### What to Integration Test

- WordPress hooks and filters registration and execution
- WooCommerce data store interactions (orders, products, customers)
- Custom REST API endpoints
- Database operations (custom tables, meta, options)
- Admin page rendering and form processing
- WooCommerce settings integration
- Cron/Action Scheduler tasks

### Example Integration Test

```php
<?php

namespace PluginSlug\Tests\Integration;

use WP_UnitTestCase;
use PluginSlug\Data\Order_Repository;

/**
 * Tests for the Order_Repository integration with WooCommerce.
 *
 * @covers \PluginSlug\Data\Order_Repository
 */
class Order_Repository_Integration_Test extends WP_UnitTestCase {

	private Order_Repository $repository;

	public function set_up(): void {
		parent::set_up();
		$this->repository = new Order_Repository();
	}

	public function test_saves_and_retrieves_custom_order_meta(): void {
		$order = wc_create_order();
		$order->save();

		$this->repository->save_tracking_number( $order->get_id(), 'TRACK123' );

		$retrieved = $this->repository->get_tracking_number( $order->get_id() );
		$this->assertSame( 'TRACK123', $retrieved );
	}

	public function test_hpos_compatible_query(): void {
		// Create test orders with custom meta.
		$order1 = wc_create_order();
		$order1->update_meta_data( '_plugin_slug_status', 'pending' );
		$order1->save();

		$order2 = wc_create_order();
		$order2->update_meta_data( '_plugin_slug_status', 'complete' );
		$order2->save();

		$pending_orders = $this->repository->get_orders_by_status( 'pending' );

		$this->assertCount( 1, $pending_orders );
		$this->assertEquals( $order1->get_id(), $pending_orders[0]->get_id() );
	}

	public function test_rest_endpoint_requires_authentication(): void {
		// Unauthenticated request should fail.
		$request  = new \WP_REST_Request( 'GET', '/plugin-slug/v1/settings' );
		$response = rest_do_request( $request );

		$this->assertEquals( 401, $response->get_status() );
	}
}
```

---

## End-to-End Tests with Playwright

E2E tests simulate real user interactions in a browser. They test critical flows end to end —
from clicking buttons to verifying database state changes.

### Setup

Use `@wordpress/env` (wp-env) to spin up a test WordPress environment with WooCommerce,
and Playwright as the test runner.

```json
// package.json
{
	"devDependencies": {
		"@playwright/test": "^1.60",
		"@wordpress/env": "^11.0",
		"@wordpress/e2e-test-utils-playwright": "^1.0",
		"@woocommerce/e2e-utils-playwright": "^0.4"
	},
	"scripts": {
		"env:start": "wp-env start",
		"env:stop": "wp-env stop",
		"test:e2e": "playwright test",
		"test:e2e:ui": "playwright test --ui"
	}
}
```

> **Use the modern Playwright fixtures, not the Puppeteer-era utilities.** `@woocommerce/e2e-utils`
> (and `e2e-environment`) are deprecated; prefer the `@wordpress/e2e-test-utils-playwright` fixtures
> (`admin`, `editor`, `pageUtils`, `requestUtils`) plus the Woo-specific
> `@woocommerce/e2e-utils-playwright`. Verify these versions against npm and WooCommerce core's
> `package.json` at setup — the Woo package is pre-1.0 and may introduce breaking changes. If you target
> PHPUnit 10, also update `phpunit.xml.dist` to the 10 schema (the `convert*` root attributes are removed
> and coverage `<include>` moves under `<source>`). For a Docker-free environment, `@wordpress/env` can
> run on WordPress Playground, and `@wp-playground/cli` provides ephemeral throwaway sites. For
> **WooCommerce Marketplace** distribution, package custom E2E as a QIT Test Package and pass the QIT
> managed test suite — see `references/marketplace-submission.md`.

### playwright.config.ts

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
	testDir: './tests/E2E',
	timeout: 60000,
	retries: 1,
	use: {
		baseURL: 'http://localhost:8889',
		storageState: './tests/E2E/.auth/admin.json',
		screenshot: 'only-on-failure',
		trace: 'on-first-retry',
	},
	projects: [
		{
			name: 'setup',
			testMatch: /global-setup\.ts/,
		},
		{
			name: 'admin',
			testMatch: /admin\/.*\.spec\.ts/,
			dependencies: ['setup'],
		},
		{
			name: 'storefront',
			testMatch: /storefront\/.*\.spec\.ts/,
			dependencies: ['setup'],
		},
	],
});
```

### What to E2E Test

- Plugin activation and deactivation
- Admin settings page: save, validate, error states
- Onboarding flow (if applicable)
- Customer checkout flow with the plugin active
- Order management in wp-admin with plugin functionality
- REST API endpoints (via Playwright API testing)

### Example E2E Test

```typescript
import { test, expect } from '@playwright/test';

test.describe('Plugin Settings', () => {
	test('admin can save API key in settings', async ({ page }) => {
		await page.goto('/wp-admin/admin.php?page=wc-settings&tab=plugin_slug');

		await page.fill('#plugin_slug_api_key', 'test_key_12345');
		await page.click('button[name="save"]');

		await expect(page.locator('.updated')).toContainText('Settings saved');
		await expect(page.locator('#plugin_slug_api_key')).toHaveValue('test_key_12345');
	});

	test('shows validation error for invalid API key', async ({ page }) => {
		await page.goto('/wp-admin/admin.php?page=wc-settings&tab=plugin_slug');

		await page.fill('#plugin_slug_api_key', '');
		await page.click('button[name="save"]');

		await expect(page.locator('.error')).toBeVisible();
	});
});

test.describe('Checkout Flow', () => {
	test('customer can complete checkout with plugin feature', async ({ page }) => {
		// Add product to cart.
		await page.goto('/shop');
		await page.click('text=Add to cart');
		await page.goto('/checkout');

		// Fill checkout form...
		// Verify plugin's additions to checkout work correctly.
	});
});
```

---

## Security Testing

### Automated Security Tests

Write explicit test cases for each security control:

```php
public function test_settings_form_requires_nonce(): void {
	// Attempt to save without a nonce.
	$_POST['plugin_slug_api_key'] = 'test';
	// Should not save and should return an error.
}

public function test_settings_require_manage_woocommerce_capability(): void {
	// Log in as subscriber (no woocommerce capabilities).
	wp_set_current_user( $this->factory->user->create( array( 'role' => 'subscriber' ) ) );

	// Attempt to access settings page.
	// Should be denied.
}

public function test_sql_injection_in_search_parameter(): void {
	$malicious_input = "'; DROP TABLE wp_options; --";
	$result = $this->repository->search_orders( $malicious_input );

	// Should return empty results, not cause an error.
	$this->assertIsArray( $result );
}

public function test_xss_in_settings_output(): void {
	// Save a setting with XSS payload.
	update_option( 'plugin_slug_title', '<script>alert("xss")</script>' );

	// Render the settings page.
	ob_start();
	$this->settings_page->output();
	$output = ob_get_clean();

	// The script tag should be escaped.
	$this->assertStringNotContainsString( '<script>', $output );
}
```

### Static Analysis

Run PHPStan or Psalm at level 6+ to catch type errors, null reference issues, and other
bugs statically. Higher levels (7-8) are better.

```bash
vendor/bin/phpstan analyse src/ --level 6
```

---

## Financial / Fintech Testing

For plugins that handle money, these additional tests are mandatory:

### Idempotency Tests

```php
public function test_duplicate_payment_processing_is_idempotent(): void {
	$order = wc_create_order();
	$order->set_total( '99.99' );
	$order->save();

	// Process payment twice with same idempotency key.
	$result1 = $this->gateway->process_payment( $order->get_id() );
	$result2 = $this->gateway->process_payment( $order->get_id() );

	// Should succeed once, second call should recognize duplicate.
	$this->assertTrue( $result1['result'] === 'success' );
	$this->assertTrue( $result2['result'] === 'success' );

	// Only one charge should exist.
	$charges = $this->get_charges_for_order( $order->get_id() );
	$this->assertCount( 1, $charges );
}
```

### Precision Tests

```php
public function test_financial_precision_at_boundaries(): void {
	$calc = new Price_Calculator();

	// IEEE 754 floating-point edge case: 0.1 + 0.2 ≠ 0.3 in float.
	$this->assertSame( '0.30', $calc->add( '0.10', '0.20' ) );

	// Large amounts.
	$this->assertSame( '999999.99', $calc->add( '999999.00', '0.99' ) );

	// Very small amounts.
	$this->assertSame( '0.01', $calc->subtract( '0.02', '0.01' ) );
}
```

### Race Condition Tests

```php
public function test_concurrent_stock_reduction(): void {
	$product = new \WC_Product_Simple();
	$product->set_stock_quantity( 1 );
	$product->set_manage_stock( true );
	$product->save();

	// Simulate two concurrent orders for the last item.
	// Only one should succeed.
}
```

### Audit Trail Tests

```php
public function test_payment_operations_are_logged(): void {
	$order = wc_create_order();
	$order->set_total( '50.00' );
	$order->save();

	$this->gateway->process_payment( $order->get_id() );

	$logs = $this->get_logs_for_order( $order->get_id() );
	$this->assertNotEmpty( $logs );
	$this->assertStringContainsString( 'payment_initiated', $logs[0]['action'] );
}
```

---

## Code Coverage Requirements

- **Overall:** Aim for 80%+ line coverage on business logic (`src/`)
- **Critical paths:** 100% coverage on payment processing, data mutation, and security code
- **Excluded from coverage:** WordPress/WooCommerce core wrappers that are pure pass-throughs

Generate coverage reports with:
```bash
XDEBUG_MODE=coverage vendor/bin/phpunit --coverage-html coverage-report/
```

---

## CI Integration

### GitHub Actions Workflow

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        php: ['8.1', '8.2', '8.3', '8.4']
        wp: ['6.7', '6.9', 'latest']
        wc: ['9.0', '10.8', 'latest']
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
          tools: composer, phpcs, phpstan
          coverage: xdebug

      - run: composer install --no-progress
      - run: vendor/bin/phpcs
      - run: vendor/bin/phpstan analyse --level 6
      - run: vendor/bin/phpunit --testsuite unit
      - run: vendor/bin/phpunit --testsuite integration

  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run env:start
      - run: npm run test:e2e
```

> **Also exercise HPOS in CI.** HPOS is the default order backend for new stores (since WC 8.2) and is
> this toolkit's #1 non-negotiable, so the matrix should validate it: enable High-Performance Order
> Storage with compatibility mode **off** in at least one E2E run and assert that order reads/writes via
> CRUD still work. Before submitting to the WooCommerce Marketplace, also run the QIT managed tests
> locally (`references/marketplace-submission.md`) — QIT is the gate that the listing and every update
> must pass.
