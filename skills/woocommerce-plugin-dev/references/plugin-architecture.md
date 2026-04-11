# WooCommerce Plugin Architecture

This reference covers the canonical file structure, bootstrapping patterns, and architectural
decisions for building a well-structured WooCommerce plugin.

**Official sources:**
- WordPress Plugin Handbook: https://developer.wordpress.org/plugins/
- WooCommerce Extension Development: https://developer.woocommerce.com/docs/extensions/best-practices-extensions/

---

## Table of Contents
1. [Main Plugin File](#main-plugin-file)
2. [Plugin Bootstrap Class](#plugin-bootstrap-class)
3. [HPOS Compatibility Declaration](#hpos-compatibility-declaration)
4. [Dependency Checking](#dependency-checking)
5. [Activation & Deactivation](#activation--deactivation)
6. [Uninstall Handler](#uninstall-handler)
7. [Service Container Pattern](#service-container-pattern)

---

## Main Plugin File

The main plugin file is the entry point. It should be minimal — define constants, check
dependencies, and delegate to the Plugin bootstrap class.

```php
<?php
/**
 * Plugin Name:       Plugin Display Name
 * Plugin URI:        https://example.com/plugin-slug
 * Description:       A brief description of what the plugin does.
 * Version:           1.0.0
 * Requires at least: 6.4
 * Requires PHP:      8.0
 * Author:            Author Name
 * Author URI:        https://example.com
 * License:           GPL v2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       plugin-slug
 * Domain Path:       /languages
 * WC requires at least: 8.5
 * WC tested up to:      9.4
 *
 * @package PluginSlug
 */

defined( 'ABSPATH' ) || exit;

// Plugin constants.
define( 'PLUGIN_SLUG_VERSION', '1.0.0' );
define( 'PLUGIN_SLUG_FILE', __FILE__ );
define( 'PLUGIN_SLUG_PATH', plugin_dir_path( __FILE__ ) );
define( 'PLUGIN_SLUG_URL', plugin_dir_url( __FILE__ ) );
define( 'PLUGIN_SLUG_BASENAME', plugin_basename( __FILE__ ) );

// Composer autoloader.
if ( file_exists( __DIR__ . '/vendor/autoload.php' ) ) {
	require __DIR__ . '/vendor/autoload.php';
}

/**
 * Declare WooCommerce feature compatibility.
 *
 * All new plugins MUST declare compatibility with these WooCommerce features:
 * - custom_order_tables (HPOS) — mandatory for all new plugins
 * - cart_checkout_blocks — required if plugin touches cart/checkout
 * - product_block_editor — required if plugin adds product data panels
 *
 * @see https://developer.woocommerce.com/docs/extensions/best-practices-extensions/
 */
add_action( 'before_woocommerce_init', function () {
	if ( class_exists( \Automattic\WooCommerce\Utilities\FeaturesUtil::class ) ) {
		// HPOS compatibility — mandatory for ALL new plugins.
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
			'custom_order_tables',
			__FILE__,
			true
		);

		// Cart & Checkout Blocks compatibility.
		// Set to true if your plugin works with the block-based checkout.
		// Test thoroughly with the Checkout Block before declaring true.
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
			'cart_checkout_blocks',
			__FILE__,
			true
		);

		// Product Block Editor compatibility.
		// Set to true if your plugin works with the new product editor.
		// Required if your plugin adds product data tabs or panels.
		\Automattic\WooCommerce\Utilities\FeaturesUtil::declare_compatibility(
			'product_block_editor',
			__FILE__,
			true
		);
	}
} );

/**
 * Initialize the plugin after all plugins are loaded.
 */
add_action( 'plugins_loaded', function () {
	// Check WooCommerce dependency.
	if ( ! class_exists( 'WooCommerce' ) ) {
		add_action( 'admin_notices', function () {
			echo '<div class="error"><p>';
			echo esc_html__(
				'Plugin Display Name requires WooCommerce to be installed and active.',
				'plugin-slug'
			);
			echo '</p></div>';
		} );
		return;
	}

	// Check minimum WooCommerce version.
	if ( version_compare( WC_VERSION, '8.5', '<' ) ) {
		add_action( 'admin_notices', function () {
			echo '<div class="error"><p>';
			printf(
				/* translators: %s: Required WooCommerce version */
				esc_html__( 'Plugin Display Name requires WooCommerce %s or higher.', 'plugin-slug' ),
				'8.5'
			);
			echo '</p></div>';
		} );
		return;
	}

	// Boot the plugin.
	\PluginSlug\Plugin::instance();
}, 10 );

// Activation and deactivation hooks.
register_activation_hook( __FILE__, array( \PluginSlug\Plugin::class, 'activate' ) );
register_deactivation_hook( __FILE__, array( \PluginSlug\Plugin::class, 'deactivate' ) );
```

---

## Plugin Bootstrap Class

The main Plugin class uses the singleton pattern and wires up all components.

```php
<?php
/**
 * Main plugin class.
 *
 * @package PluginSlug
 * @since   1.0.0
 */

namespace PluginSlug;

defined( 'ABSPATH' ) || exit;

/**
 * Plugin bootstrap class.
 *
 * Initializes all plugin components and manages the plugin lifecycle.
 *
 * @since 1.0.0
 */
final class Plugin {

	/**
	 * Plugin instance.
	 *
	 * @var self|null
	 */
	private static ?self $instance = null;

	/**
	 * Get the singleton instance.
	 *
	 * @since 1.0.0
	 *
	 * @return self
	 */
	public static function instance(): self {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	/**
	 * Constructor — wire up all components.
	 *
	 * @since 1.0.0
	 */
	private function __construct() {
		$this->init_hooks();

		if ( is_admin() ) {
			$this->init_admin();
		}

		$this->init_frontend();
		$this->init_api();
	}

	/**
	 * Register core hooks.
	 */
	private function init_hooks(): void {
		add_action( 'init', array( $this, 'load_textdomain' ) );
	}

	/**
	 * Initialize admin-only components.
	 */
	private function init_admin(): void {
		new Admin\Settings_Page();
		// Add more admin components here.
	}

	/**
	 * Initialize frontend components.
	 */
	private function init_frontend(): void {
		// Add frontend components here.
	}

	/**
	 * Initialize REST API endpoints.
	 */
	private function init_api(): void {
		add_action( 'rest_api_init', function () {
			// Register REST routes here.
		} );
	}

	/**
	 * Load plugin text domain for translations.
	 *
	 * @since 1.0.0
	 */
	public function load_textdomain(): void {
		load_plugin_textdomain(
			'plugin-slug',
			false,
			dirname( PLUGIN_SLUG_BASENAME ) . '/languages'
		);
	}

	/**
	 * Plugin activation callback.
	 *
	 * @since 1.0.0
	 */
	public static function activate(): void {
		// Create custom tables, set default options, schedule cron events.
		// Check PHP and WordPress version requirements.
		if ( version_compare( PHP_VERSION, '8.0', '<' ) ) {
			deactivate_plugins( PLUGIN_SLUG_BASENAME );
			wp_die(
				esc_html__( 'This plugin requires PHP 8.0 or higher.', 'plugin-slug' ),
				'Plugin activation error',
				array( 'back_link' => true )
			);
		}

		// Set a flag for first-run setup.
		update_option( 'plugin_slug_version', PLUGIN_SLUG_VERSION );
		update_option( 'plugin_slug_activation_time', time() );

		// Flush rewrite rules if the plugin registers custom post types or endpoints.
		flush_rewrite_rules();
	}

	/**
	 * Plugin deactivation callback.
	 *
	 * @since 1.0.0
	 */
	public static function deactivate(): void {
		// Clear scheduled events.
		wp_clear_scheduled_hook( 'plugin_slug_daily_cron' );

		// Flush rewrite rules.
		flush_rewrite_rules();

		// Do NOT delete data on deactivation — that's for uninstall.php.
	}

	/**
	 * Prevent cloning.
	 */
	private function __clone() {}

	/**
	 * Prevent unserialization.
	 */
	public function __wakeup() {
		throw new \RuntimeException( 'Cannot unserialize singleton.' );
	}
}
```

---

## WooCommerce Feature Compatibility

### HPOS (High-Performance Order Storage) — MANDATORY

HPOS is mandatory for all new WooCommerce plugins. It stores orders in custom tables instead
of the wp_posts table.

**Key rules:**
- Never use `get_post_meta()` / `update_post_meta()` for order data
- Always use `$order->get_meta()` / `$order->update_meta_data()` / `$order->save()`
- Use `wc_get_orders()` with proper arguments instead of `WP_Query` for order queries
- Use `OrderUtil::custom_orders_table_usage_is_enabled()` if you need to check HPOS status
- Use the WooCommerce CRUD API (`WC_Order`, `WC_Product`, etc.) for all data operations
- HPOS supports `meta_query` in `wc_get_orders()` — use it instead of raw SQL

### Cart & Checkout Blocks Compatibility

If your plugin modifies the cart or checkout experience, it MUST be tested with the
block-based Cart and Checkout. Key compatibility points:

- Classic checkout hooks (`woocommerce_checkout_fields`, etc.) do NOT fire in block checkout
- Use the Store API and `ExtendSchema` API to add data to block checkout
- Use `Inner Blocks` and `Slot and Fill` patterns for custom block checkout UI
- Declare `cart_checkout_blocks` compatibility only after thorough testing

### Product Block Editor Compatibility

If your plugin adds product data panels or tabs, it must work with the new product editor:

- Declare `product_block_editor` compatibility via FeaturesUtil
- Test that product data panels render correctly in the block editor
- Use the product editor extensibility API for custom product fields

### Site Editor Compatibility

If your plugin provides frontend templates or blocks, ensure they work with the Site Editor:

- Templates should be compatible with block themes
- Custom blocks should be registered with `block.json`
- Avoid relying on classic theme functions for layout

---

## Uninstall Handler

`uninstall.php` runs when the plugin is deleted (not just deactivated). It should clean up
all plugin data.

```php
<?php
/**
 * Plugin uninstall handler.
 *
 * Removes all plugin data when the plugin is deleted via WordPress admin.
 *
 * @package PluginSlug
 * @since   1.0.0
 */

// Exit if not called by WordPress.
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

global $wpdb;

// Delete options.
$wpdb->query(
	$wpdb->prepare(
		"DELETE FROM {$wpdb->options} WHERE option_name LIKE %s",
		$wpdb->esc_like( 'plugin_slug_' ) . '%'
	)
);

// Delete order meta.
// Use HPOS-compatible approach.
if ( class_exists( 'WooCommerce' ) ) {
	$wpdb->query(
		$wpdb->prepare(
			"DELETE FROM {$wpdb->prefix}wc_orders_meta WHERE meta_key LIKE %s",
			$wpdb->esc_like( '_plugin_slug_' ) . '%'
		)
	);
}

// Drop custom tables.
$wpdb->query( "DROP TABLE IF EXISTS {$wpdb->prefix}plugin_slug_logs" );

// Delete transients.
$wpdb->query(
	$wpdb->prepare(
		"DELETE FROM {$wpdb->options} WHERE option_name LIKE %s OR option_name LIKE %s",
		$wpdb->esc_like( '_transient_plugin_slug_' ) . '%',
		$wpdb->esc_like( '_transient_timeout_plugin_slug_' ) . '%'
	)
);

// Clear any scheduled hooks.
wp_clear_scheduled_hook( 'plugin_slug_daily_cron' );

// Flush rewrite rules.
flush_rewrite_rules();
```

---

## Service Container Pattern

For larger plugins, use a simple service container to manage dependencies.

```php
namespace PluginSlug;

class Container {
	private array $services = [];
	private array $instances = [];

	public function register( string $id, callable $factory ): void {
		$this->services[ $id ] = $factory;
	}

	public function get( string $id ): mixed {
		if ( ! isset( $this->instances[ $id ] ) ) {
			if ( ! isset( $this->services[ $id ] ) ) {
				throw new \RuntimeException( "Service not found: {$id}" );
			}
			$this->instances[ $id ] = ( $this->services[ $id ] )( $this );
		}
		return $this->instances[ $id ];
	}
}
```

This keeps class instantiation centralized and makes testing easier (swap real services for
mocks in tests).
