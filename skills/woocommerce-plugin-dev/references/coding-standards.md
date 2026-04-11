# WordPress & WooCommerce Coding Standards

This reference covers the coding standards that must be applied to every file in the plugin.
These are drawn from the official WordPress Coding Standards Handbook and WooCommerce coding
standards documentation.

**Official sources:**
- WordPress Coding Standards: https://developer.wordpress.org/coding-standards/
- WooCommerce Coding Standards: https://developer.woocommerce.com/docs/best-practices/coding-standards/
- WordPress PHP Standards: https://developer.wordpress.org/coding-standards/wordpress-coding-standards/php/

---

## Table of Contents
1. [PHP Standards](#php-standards)
2. [Naming Conventions](#naming-conventions)
3. [Documentation](#documentation)
4. [JavaScript Standards](#javascript-standards)
5. [CSS Standards](#css-standards)
6. [Autoloading & Namespaces](#autoloading--namespaces)

---

## PHP Standards

### Formatting

- **Indentation:** Use tabs, not spaces. Each level of indentation = one tab.
- **Braces:** Opening brace on the same line as the control structure. Closing brace on its own line.
- **Spacing:** A single space after control structure keywords (`if`, `for`, `foreach`, `while`).
  A single space on either side of comparison and assignment operators.
- **Line length:** Keep lines under 120 characters where practical. Break long function calls
  across multiple lines.
- **Yoda conditions:** Use Yoda conditions for comparisons: `if ( true === $var )` not
  `if ( $var === true )`.
- **String quoting:** Use single quotes for strings that don't need variable interpolation. Use
  double quotes when interpolation is needed.

### Example: Properly Formatted PHP

```php
<?php
/**
 * Process a refund for an order.
 *
 * @since 1.0.0
 *
 * @param int   $order_id The order ID.
 * @param float $amount   The refund amount.
 *
 * @return bool True on success, false on failure.
 *
 * @throws \InvalidArgumentException If the amount is negative.
 */
public function process_refund( int $order_id, float $amount ): bool {
	if ( $amount < 0 ) {
		throw new \InvalidArgumentException(
			esc_html__( 'Refund amount cannot be negative.', 'plugin-slug' )
		);
	}

	$order = wc_get_order( $order_id );

	if ( ! $order instanceof \WC_Order ) {
		return false;
	}

	$result = $order->update_meta_data( '_refund_processed', 'yes' );
	$order->save();

	/**
	 * Fires after a refund has been processed.
	 *
	 * @since 1.0.0
	 *
	 * @param int   $order_id The order ID.
	 * @param float $amount   The refund amount.
	 */
	do_action( 'plugin_slug_refund_processed', $order_id, $amount );

	return true;
}
```

### Type Declarations (PHP 8.0+)

Use PHP type declarations (parameter types and return types) for all new code. The plugin requires
PHP 8.0+ so union types, named arguments, match expressions, and constructor property promotion
are available.

**Per WPCS 3.3.0 and the WordPress PHP Coding Standards:**
- Use type declarations for all function parameters and return types
- Use union types where appropriate: `int|string`, `array|null`
- Use `mixed` only when the type truly cannot be narrowed
- Prefer `?Type` (nullable) syntax over `Type|null` for single-type nullable params
- Use `void` return type for functions that don't return a value
- Use `never` return type for functions that always throw or exit
- Use constructor property promotion for value objects and DTOs

```php
// Standard type declarations.
public function get_order_total( int $order_id ): float {
	// ...
}

public function find_orders( array $args = [] ): array {
	// ...
}

// Union types (PHP 8.0+).
public function get_order( int|string $order_id ): ?WC_Order {
	// ...
}

// Constructor property promotion for DTOs.
final class Shipping_Rate {
	public function __construct(
		private readonly string $method_id,
		private readonly float $cost,
		private readonly string $label,
	) {}
}
```

### Pre/Post Increment Operators

Per WPCS 3.3.0, use pre-increment (`++$i`) and pre-decrement (`--$i`) rather than post-increment
(`$i++`) and post-decrement (`$i--`) when the return value is not used:

```php
// Correct — pre-increment when return value is unused.
for ( $i = 0; $i < $count; ++$i ) {
	// ...
}

// Post-increment is fine when the return value IS used.
$items[ $i++ ] = $value;
```

---

## Naming Conventions

### Functions and Methods
- **Global functions:** `plugin_slug_function_name()` (snake_case with plugin prefix)
- **Class methods:** `snake_case` (e.g., `$this->process_payment()`)
- **Never use camelCase** for PHP functions or methods in WordPress context

### Classes
- **PSR-4 namespaced:** `PluginSlug\Admin\Settings_Page`
- **Class names:** `Upper_Snake_Case` (WordPress convention) or `PascalCase` within namespaced code
- **File names match class names:** `class-settings-page.php` or `Settings_Page.php` (PSR-4)

### Hooks (Actions and Filters)
- **Prefix all custom hooks:** `plugin_slug_action_name`
- **Use descriptive names:** `plugin_slug_before_process_payment` not `plugin_slug_bpp`
- **Document every hook** with a PHPDoc block above the `do_action` or `apply_filters` call

### Database Keys
- **Option names:** `plugin_slug_option_name`
- **Meta keys:** `_plugin_slug_meta_key` (underscore prefix hides from custom fields UI)
- **Transient names:** `plugin_slug_transient_name` (max 172 chars total)

### Constants
- **Plugin constants:** `PLUGIN_SLUG_VERSION`, `PLUGIN_SLUG_PATH`, `PLUGIN_SLUG_URL`
- **Class constants:** `self::API_VERSION`, `self::MAX_RETRIES`

### REST API Routes
- **Namespace:** `plugin-slug/v1`
- **Routes:** `/plugin-slug/v1/resource-name`

---

## Documentation

Every public and protected function, method, class, and file needs PHPDoc documentation.

### File Header

```php
<?php
/**
 * Settings page for Plugin Name.
 *
 * Handles the admin settings interface including saving and validation.
 *
 * @package PluginSlug
 * @since   1.0.0
 */

namespace PluginSlug\Admin;
```

### Class Documentation

```php
/**
 * Manages plugin settings in the WooCommerce admin.
 *
 * Registers a settings tab under WooCommerce > Settings and handles
 * saving, validation, and display of all plugin configuration options.
 *
 * @since 1.0.0
 */
class Settings_Page extends \WC_Settings_Page {
```

### Method Documentation

Always include `@since`, `@param`, `@return`. Add `@throws` when the method can throw exceptions.
Add `@access` for private methods.

```php
/**
 * Validate the API key format before saving.
 *
 * Checks that the key matches the expected format and verifies it against
 * the external API. Stores validation result in transient cache to avoid
 * repeated API calls.
 *
 * @since 1.0.0
 * @since 1.2.0 Added transient caching for validation result.
 *
 * @param string $api_key The API key to validate.
 *
 * @return bool True if the key is valid, false otherwise.
 *
 * @throws \RuntimeException If the external API is unreachable.
 */
public function validate_api_key( string $api_key ): bool {
```

### Inline Comments

Use inline comments to explain *why*, not *what*. The code should be readable enough that it's
clear *what* it does.

```php
// Bail early if the order was placed before the plugin was activated —
// these orders don't have our metadata and would cause errors downstream.
if ( $order->get_date_created() < $this->activation_date ) {
	return;
}
```

---

## JavaScript Standards

- Follow the WordPress JavaScript Coding Standards
- Use modern ES6+ syntax (the build process transpiles for compatibility)
- Use `wp.data`, `wp.element`, and `@wordpress/components` for Gutenberg/Block integrations
- Prefix all global variables and custom events with the plugin slug
- Use `wp_localize_script` or `wp_add_inline_script` to pass PHP data to JS
- Never inline JavaScript in PHP templates

---

## CSS Standards

- Follow the WordPress CSS Coding Standards
- Prefix all selectors with the plugin slug: `.plugin-slug-wrapper`
- Use existing WordPress admin CSS variables and classes where possible
- Support the user's selected admin color scheme (don't hard-code admin colors)
- Use logical properties for RTL support

---

## Autoloading & Namespaces

Use PSR-4 autoloading via Composer. This keeps the codebase organized, avoids manual `require`
chains, and follows modern PHP best practices.

**Namespace guidance (per WordPress developer best practices 2025):**
- Top-level namespace should match the plugin slug in PascalCase
- Use sub-namespaces for logical groupings (Admin, Frontend, API, Data, etc.)
- Never use `use function` or `use const` — they're confusing in WordPress context
- Always use fully qualified global functions in namespaced code OR add explicit `use` statements
- When calling WordPress functions from namespaced code, prefix with `\` or add a `use function`
  declaration at the top of the file

### composer.json autoload configuration

```json
{
	"autoload": {
		"psr-4": {
			"PluginSlug\\": "src/"
		}
	},
	"autoload-dev": {
		"psr-4": {
			"PluginSlug\\Tests\\": "tests/"
		}
	},
	"require": {
		"php": ">=8.0"
	},
	"config": {
		"allow-plugins": {
			"dealerdirect/phpcodesniffer-composer-installer": true
		}
	},
	"require-dev": {
		"phpunit/phpunit": "^9.5 || ^10.0",
		"wp-coding-standards/wpcs": "^3.3",
		"phpcompatibility/phpcompatibility-wp": "*",
		"phpstan/phpstan": "^1.10",
		"woocommerce/woocommerce-sniffs": "*"
	}
}
```

### Namespace structure

```php
namespace PluginSlug;               // src/Plugin.php
namespace PluginSlug\Admin;         // src/Admin/Settings_Page.php
namespace PluginSlug\Frontend;      // src/Frontend/Checkout_Handler.php
namespace PluginSlug\API;           // src/API/Orders_Controller.php
namespace PluginSlug\Data;          // src/Data/Order_Repository.php
namespace PluginSlug\Blocks;        // src/Blocks/Checkout_Block.php
namespace PluginSlug\Shipping;      // src/Shipping/Custom_Method.php
namespace PluginSlug\Payments;      // src/Payments/Gateway.php
```

### Calling Global Functions in Namespaced Code

```php
namespace PluginSlug\Admin;

// Option A: Prefix with backslash.
\add_action( 'admin_init', array( $this, 'register_settings' ) );

// Option B: Import at the top (less common in WordPress ecosystem).
use function add_action;
add_action( 'admin_init', array( $this, 'register_settings' ) );
```

---

## PHPCS Configuration (WPCS 3.3.0+)

Use the WordPress Coding Standards v3.3.0+ and WooCommerce sniffs. Create `phpcs.xml.dist`.

**WPCS 3.3.0 changes to be aware of:**
- Stricter enforcement of type declarations
- Pre-increment/decrement preferred over post-increment/decrement when return value unused
- Improved handling of named arguments
- Better namespace and `use` statement detection
- Updated PHPCompatibility checks

```xml
<?xml version="1.0"?>
<ruleset name="Plugin Slug Coding Standards">
	<description>PHPCS ruleset for Plugin Slug.</description>

	<file>./src</file>
	<file>./includes</file>
	<file>./plugin-slug.php</file>
	<file>./uninstall.php</file>

	<exclude-pattern>./vendor/*</exclude-pattern>
	<exclude-pattern>./node_modules/*</exclude-pattern>
	<exclude-pattern>./tests/*</exclude-pattern>

	<arg name="extensions" value="php"/>
	<arg name="colors"/>
	<arg value="ps"/>

	<config name="minimum_wp_version" value="6.4"/>
	<config name="testVersion" value="8.0-"/>

	<rule ref="WordPress">
		<!-- PSR-4 autoloading uses PascalCase filenames (e.g. Settings_Page.php)
		     instead of the WordPress class-*.php convention. This exclusion is
		     required for PSR-4 compliance and does not weaken security checks. -->
		<exclude name="WordPress.Files.FileName.InvalidClassFileName"/>
	</rule>
	<rule ref="WooCommerce"/>
	<rule ref="WordPress-Extra"/>
	<rule ref="WordPress-Docs"/>

	<!-- PHPCompatibility checks for minimum PHP version -->
	<rule ref="PHPCompatibilityWP"/>

	<rule ref="WordPress.WP.I18n">
		<properties>
			<property name="text_domain" type="array">
				<element value="plugin-slug"/>
			</property>
		</properties>
	</rule>

	<!-- Allow short array syntax (modern PHP) -->
	<rule ref="Generic.Arrays.DisallowShortArraySyntax">
		<severity>0</severity>
	</rule>
</ruleset>
```

### Running PHPCS

```bash
# Check code quality.
vendor/bin/phpcs

# Auto-fix what can be fixed.
vendor/bin/phpcbf

# Check specific files.
vendor/bin/phpcs src/Admin/Settings_Page.php
```
