# WooCommerce APIs reference

Use WooCommerce APIs and data stores instead of direct database access. These patterns preserve HPOS
compatibility and follow supported extension contracts.

**Official sources:**
- WooCommerce REST API: https://woocommerce.github.io/woocommerce-rest-api-docs/
- Store API: https://developer.woocommerce.com/docs/apis/store-api/
- WooCommerce Developer Docs: https://developer.woocommerce.com/docs/
- HPOS Recipe Book: https://developer.woocommerce.com/docs/features/orders/high-performance-order-storage/recipe-book/

---

## Table of contents
1. [Order CRUD (HPOS-compatible)](#order-crud-hpos-compatible)
2. [Product CRUD](#product-crud)
3. [Customer data](#customer-data)
4. [WooCommerce hooks](#woocommerce-hooks)
5. [REST API extensions](#rest-api-extensions)
6. [WooCommerce REST API v3 authentication](#woocommerce-rest-api-v3-authentication)
7. [Store API and Block checkout extensibility](#store-api-and-block-checkout-extensibility)
8. [Action Scheduler](#action-scheduler)
9. [WooCommerce Settings API](#woocommerce-settings-api)

---

## Order CRUD (HPOS-compatible)

Always use the WooCommerce CRUD API for orders. Never access `wp_posts` or `wp_postmeta` directly.

### Reading orders

```php
// Get an order by ID.
$order = wc_get_order( $order_id );

// Query orders — HPOS-compatible.
$orders = wc_get_orders( array(
	'status'     => 'processing',
	'limit'      => 20,
	'orderby'    => 'date',
	'order'      => 'DESC',
	'meta_key'   => '_plugin_slug_status',
	'meta_value' => 'pending',
) );

// HPOS supports meta_query for complex meta lookups (per HPOS Recipe Book).
$orders = wc_get_orders( array(
	'status'     => 'processing',
	'limit'      => 20,
	'meta_query' => array(
		'relation' => 'AND',
		array(
			'key'     => '_plugin_slug_status',
			'value'   => 'pending',
			'compare' => '=',
		),
		array(
			'key'     => '_plugin_slug_priority',
			'value'   => 5,
			'compare' => '>=',
			'type'    => 'NUMERIC',
		),
	),
) );
```

### Writing order data

```php
$order = wc_get_order( $order_id );

// Set standard properties.
$order->set_status( 'completed' );

// Custom meta — the HPOS-compatible way.
$order->update_meta_data( '_plugin_slug_tracking', $tracking_number );
$order->update_meta_data( '_plugin_slug_processed_at', current_time( 'mysql' ) );

// Always call save() after modifications.
$order->save();
```

### Order notes

```php
// Add a note visible to the admin.
$order->add_order_note(
	__( 'Payment captured successfully via Plugin Name.', 'plugin-slug' )
);

// Add a note visible to the customer.
$order->add_order_note(
	__( 'Your order has been shipped!', 'plugin-slug' ),
	1  // is_customer_note.
);
```

### HPOS-aware queries

Prefer `wc_get_orders()`. If repository evidence requires a custom query, branch on the active order
storage:

```php
use Automattic\WooCommerce\Utilities\OrderUtil;

if ( OrderUtil::custom_orders_table_usage_is_enabled() ) {
	// Query the wc_orders table.
	global $wpdb;
	$results = $wpdb->get_results(
		$wpdb->prepare(
			"SELECT id FROM {$wpdb->prefix}wc_orders WHERE status = %s",
			'wc-processing'
		)
	);
} else {
	// Fallback for legacy post-based storage.
	$results = get_posts( array(
		'post_type'   => 'shop_order',
		'post_status' => 'wc-processing',
		'fields'      => 'ids',
	) );
}
```

---

## Product CRUD

```php
// Get a product.
$product = wc_get_product( $product_id );

// Read properties.
$name  = $product->get_name();
$price = $product->get_price();
$sku   = $product->get_sku();
$stock = $product->get_stock_quantity();

// Modify properties.
$product->set_regular_price( '29.99' );
$product->update_meta_data( '_plugin_slug_custom_field', $value );
$product->save();

// Query products.
$products = wc_get_products( array(
	'status'   => 'publish',
	'limit'    => 10,
	'category' => array( 'clothing' ),
	'orderby'  => 'date',
	'order'    => 'DESC',
) );
```

---

## Customer data

```php
// Get customer.
$customer = new \WC_Customer( $user_id );

$email   = $customer->get_email();
$country = $customer->get_billing_country();

// Update customer meta.
$customer->update_meta_data( '_plugin_slug_loyalty_points', 150 );
$customer->save();
```

---

## WooCommerce hooks

### Essential action hooks

| Hook | When It Fires | Common Use |
|------|--------------|------------|
| `woocommerce_init` | WooCommerce is initialized | Register custom data stores |
| `woocommerce_loaded` | WooCommerce is fully loaded | Check WC version, load integrations |
| `woocommerce_checkout_order_processed` | Order created from checkout | Post-checkout processing |
| `woocommerce_payment_complete` | Payment is marked complete | Trigger fulfillment |
| `woocommerce_order_status_changed` | Order status changes | Status-based automations |
| `woocommerce_new_order` | New order created | Initialize order meta |
| `woocommerce_before_cart` | Before cart renders | Add notices, modify cart display |
| `woocommerce_after_checkout_validation` | After checkout validation | Custom validation |
| `woocommerce_thankyou` | Thank you page | Display custom order info |

### Essential filter hooks

| Hook | What It Filters | Common Use |
|------|----------------|------------|
| `woocommerce_cart_calculate_fees` | Cart fees | Add surcharges or discounts |
| `woocommerce_package_rates` | Shipping rates | Modify available shipping |
| `woocommerce_available_payment_gateways` | Payment options | Conditionally show/hide gateways |
| `woocommerce_checkout_fields` | Classic checkout fields — does NOT fire in block checkout | Modify fields on classic shortcode checkout only (to *add* fields, use the Additional Checkout Fields API) |
| `woocommerce_order_actions` | Order actions dropdown | Add custom order actions |
| `woocommerce_product_data_tabs` | Product data tabs | Add custom product tabs |
| `woocommerce_get_settings_pages` | Settings pages | Add settings tabs |

---

## REST API extensions

### Registering custom endpoints

```php
namespace PluginSlug\API;

class Orders_Controller extends \WP_REST_Controller {

	protected $namespace = 'plugin-slug/v1';
	protected $rest_base = 'orders';

	public function register_routes(): void {
		register_rest_route( $this->namespace, '/' . $this->rest_base, array(
			array(
				'methods'             => \WP_REST_Server::READABLE,
				'callback'            => array( $this, 'get_items' ),
				'permission_callback' => array( $this, 'get_items_permissions_check' ),
				'args'                => $this->get_collection_params(),
			),
		) );

		register_rest_route( $this->namespace, '/' . $this->rest_base . '/(?P<id>[\d]+)', array(
			array(
				'methods'             => \WP_REST_Server::READABLE,
				'callback'            => array( $this, 'get_item' ),
				'permission_callback' => array( $this, 'get_item_permissions_check' ),
				'args'                => array(
					'id' => array(
						'description' => __( 'Unique identifier for the order.', 'plugin-slug' ),
						'type'        => 'integer',
						'required'    => true,
					),
				),
			),
		) );
	}

	public function get_items_permissions_check( $request ): bool {
		return current_user_can( 'edit_shop_orders' );
	}

	public function get_item_permissions_check( $request ): bool {
		return current_user_can( 'edit_shop_orders' );
	}
}
```

---

## WooCommerce REST API v3 authentication

The WooCommerce REST API v3 (`/wp-json/wc/v3/`) is the standard API for external system
integration. Understanding its authentication model is essential when building endpoints that
external systems consume.

**API base URL:** `https://example.com/wp-json/wc/v3/`

### Authentication methods

**1. HTTP Basic Auth (HTTPS only — recommended for server-to-server):**

Store credentials in a protected netrc file outside the repository, provisioned by the deployment's
secret broker where available. Restrict the file to the current user and pass only its path to curl;
do not put credentials in the URL, process arguments, command history, or repository.

```bash
chmod 600 "${WC_NETRC_FILE}"
curl --netrc-file "${WC_NETRC_FILE}" "${WC_API_BASE}/orders"
```

Use a dedicated integration identity and grant only the REST API permissions it needs.

**2. OAuth 1.0a (for HTTP sites — rare but supported):**

Uses HMAC-SHA1 or HMAC-SHA256 signature method. Required parameters:
`oauth_consumer_key`, `oauth_timestamp`, `oauth_nonce`, `oauth_signature`,
`oauth_signature_method`, `oauth_version`.

### Consumer key permissions

When generating API keys, WooCommerce offers three permission levels:
- **Read** — GET access only
- **Write** — POST, PUT, DELETE access only
- **Read/Write** — Full access

Always generate keys with the minimum permission level your integration needs.

### Extending WC REST API responses

When adding custom data to existing WC REST API endpoints, use the
`woocommerce_rest_prepare_{object}_object` filter:

```php
// Add custom data to the orders endpoint.
add_filter( 'woocommerce_rest_prepare_shop_order_object', function ( $response, $order ) {
	$response->data['plugin_slug_tracking'] = $order->get_meta( '_plugin_slug_tracking' );
	$response->data['plugin_slug_status']   = $order->get_meta( '_plugin_slug_status' );
	return $response;
}, 10, 2 );
```

Declare schemas for custom fields and validate values against those schemas at the request boundary.
Return native JSON strings, numbers, booleans, arrays, and objects. Do not HTML-escape JSON values;
escape only when a consumer later renders a value into an HTML, attribute, URL, or JavaScript context.

---

## Store API and Block checkout extensibility

The Store API is WooCommerce's REST surface for block-based Cart and Checkout. Use it for block
checkout changes instead of relying on classic checkout hooks.

The Store API does not fire classic checkout PHP hooks. Choose one state model for
Cart and Checkout requests: preserve the cookie-based customer session and send a current `Nonce` on
write requests, or send the Store API's `Cart-Token` instead of cookies; Cart-Token requests do not
require a Nonce. Follow the current Store API authentication documentation for the chosen client flow.

The Store API is namespaced **`wc/store/v1`** (e.g. `/wp-json/wc/store/v1/cart`). `v1` is currently
the only version; a breaking change would force a new namespace version. It is also the canonical
surface for headless / front-end and programmatic clients — including the agentic-checkout work in
`references/agentic-commerce.md`.

### Adding checkout fields (Additional Checkout Fields API)

To **add a field** to the checkout, use the Additional Checkout Fields API
(`woocommerce_register_additional_checkout_field()`, WooCommerce 8.9+) — **not** the classic
`woocommerce_checkout_fields` filter, which does not fire in block checkout. Register on
`woocommerce_init`; each field lives in exactly one of three locations:

```php
add_action( 'woocommerce_init', function () {
	woocommerce_register_additional_checkout_field(
		array(
			'id'       => 'plugin-slug/marketing-opt-in', // Namespaced.
			'label'    => __( 'Subscribe to our newsletter?', 'plugin-slug' ),
			'location' => 'contact', // 'contact' | 'address' | 'order'.
			'type'     => 'checkbox', // 'text' | 'select' | 'checkbox'.
			'required' => false,
		)
	);
} );
```

- **`contact`** — renders in the contact section; saved to the customer account and the order.
- **`address`** — renders in shipping *and* billing; saved per-address to the customer and order.
- **`order`** — renders in the "Order information" inner block; saved to the order only.

Read saved values with the WooCommerce helper methods rather than raw meta keys. See the official
guide: https://developer.woocommerce.com/docs/block-development/tutorials/how-to-additional-checkout-fields-guide/

Use **`ExtendSchema`** (below) for the lower-level case of attaching arbitrary custom *data* to Store
API responses, rather than registering a user-facing field.

### ExtendSchema API

Use `ExtendSchema` to add custom data to Store API responses:

```php
use Automattic\WooCommerce\StoreApi\Schemas\V1\CartSchema;
use Automattic\WooCommerce\StoreApi\StoreApi;
use Automattic\WooCommerce\StoreApi\Schemas\ExtendSchema;

add_action( 'woocommerce_blocks_loaded', function () {
	$extend = StoreApi::container()->get( ExtendSchema::class );

	$extend->register_endpoint_data(
		array(
			'endpoint'        => CartSchema::IDENTIFIER,
			'namespace'       => 'plugin-slug',
			'data_callback'   => function () {
				return array(
					'loyalty_points' => get_current_user_loyalty_points(),
				);
			},
			'schema_callback' => function () {
				return array(
					'loyalty_points' => array(
						'description' => __( 'Customer loyalty points', 'plugin-slug' ),
						'type'        => 'integer',
						'context'     => array( 'view', 'edit' ),
						'readonly'    => true,
					),
				);
			},
			'schema_type'     => ARRAY_A,
		)
	);
} );
```

### Slot and Fill pattern for Block checkout UI

For adding custom UI elements to the block-based checkout, use the Slot and Fill pattern
with `@woocommerce/blocks-checkout`:

```javascript
// In your block's JavaScript:
import { ExperimentalOrderMeta } from '@woocommerce/blocks-checkout';
import { registerPlugin } from '@wordpress/plugins';

const PluginSlugOrderMeta = () => {
	return (
		<ExperimentalOrderMeta>
			<div className="plugin-slug-loyalty-info">
				{/* Your custom checkout UI */}
			</div>
		</ExperimentalOrderMeta>
	);
};

registerPlugin( 'plugin-slug-blocks', {
	render: PluginSlugOrderMeta,
	scope: 'woocommerce-checkout',
} );
```

### Inner Blocks pattern

For more complex checkout integrations, register custom inner blocks:

```php
// Register block type.
add_action( 'init', function () {
	register_block_type( PLUGIN_SLUG_PATH . 'assets/blocks/checkout-loyalty' );
} );

// Allow the block as an inner block in checkout.
add_filter( 'woocommerce_blocks_register_checkout_inner_block', function ( $blocks ) {
	$blocks[] = 'plugin-slug/checkout-loyalty';
	return $blocks;
} );
```

### When to use each API

| Scenario | Use |
|----------|-----|
| External system integration (ERPs, CRMs) | WC REST API v3 |
| Adding data to block-based checkout | Store API + ExtendSchema |
| Adding UI to block checkout | Slot and Fill / Inner Blocks |
| Custom admin endpoints | Custom WP REST API (plugin-slug/v1) |
| Customer-facing AJAX on classic pages | WP AJAX API + nonces |

---

## Action Scheduler

For background processing, use Action Scheduler (bundled with WooCommerce) instead of WP-Cron.

```php
// Schedule a single action.
as_schedule_single_action(
	time() + 300,  // 5 minutes from now.
	'plugin_slug_process_order',
	array( 'order_id' => $order_id ),
	'plugin-slug'
);

// Schedule a recurring action.
if ( false === as_has_scheduled_action( 'plugin_slug_daily_sync' ) ) {
	as_schedule_recurring_action(
		strtotime( 'tomorrow midnight' ),
		DAY_IN_SECONDS,
		'plugin_slug_daily_sync',
		array(),
		'plugin-slug'
	);
}

// Handle the action.
add_action( 'plugin_slug_process_order', function ( int $order_id ) {
	$order = wc_get_order( $order_id );
	if ( ! $order ) {
		return;
	}
	// Process the order...
} );
```

---

## WooCommerce Settings API

Integrate settings into WooCommerce > Settings by extending `WC_Settings_Page`:

```php
namespace PluginSlug\Admin;

class Settings_Page extends \WC_Settings_Page {

	public function __construct() {
		$this->id    = 'plugin_slug';
		$this->label = __( 'Plugin Name', 'plugin-slug' );

		parent::__construct();
	}

	public function get_settings_for_default_section(): array {
		return array(
			array(
				'title' => __( 'General Settings', 'plugin-slug' ),
				'type'  => 'title',
				'id'    => 'plugin_slug_general',
			),
			array(
				'title'    => __( 'Enable Plugin', 'plugin-slug' ),
				'desc'     => __( 'Enable the plugin functionality.', 'plugin-slug' ),
				'id'       => 'plugin_slug_enabled',
				'type'     => 'checkbox',
				'default'  => 'yes',
			),
			array(
				'title'    => __( 'Checkout Label', 'plugin-slug' ),
				'desc'     => __( 'Label shown to customers at checkout.', 'plugin-slug' ),
				'id'       => 'plugin_slug_checkout_label',
				'type'     => 'text',
				'desc_tip' => true,
			),
			array(
				'type' => 'sectionend',
				'id'   => 'plugin_slug_general',
			),
		);
	}
}
```

Register the settings page:

```php
add_filter( 'woocommerce_get_settings_pages', function ( $settings ) {
	$settings[] = new \PluginSlug\Admin\Settings_Page();
	return $settings;
} );
```
