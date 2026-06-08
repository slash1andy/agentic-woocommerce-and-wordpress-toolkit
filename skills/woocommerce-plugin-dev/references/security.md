# Security Standards for WooCommerce Plugins

This reference covers security practices that must be applied to every line of code that handles
user input, database operations, file operations, or API communication. These practices are
drawn from the WordPress Plugin Handbook security chapter, OWASP guidelines, and PCI-DSS
requirements relevant to WooCommerce extensions.

**Official sources:**
- WordPress Plugin Security: https://developer.wordpress.org/plugins/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- WooCommerce Best Practices: https://developer.woocommerce.com/docs/extensions/best-practices-extensions/

---

## Table of Contents
1. [Core Security Principles](#core-security-principles)
2. [Input Sanitization](#input-sanitization)
3. [Output Escaping](#output-escaping)
4. [Nonces & CSRF Protection](#nonces--csrf-protection)
5. [Capability Checks](#capability-checks)
6. [Database Security](#database-security)
7. [File Security](#file-security)
8. [API Security](#api-security)
9. [Financial Data Security](#financial-data-security)
10. [Logging & Audit Trails](#logging--audit-trails)

---

## Core Security Principles

Per the WordPress Plugin Handbook Security chapter, these principles govern every security decision:

1. **Never trust user input.** All data from `$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`,
   `$_SERVER`, REST API request bodies, webhook payloads, and any external source is untrusted.
2. **Defense in depth.** Layer security measures. Even if one layer fails, the next catches it.
3. **Principle of least privilege.** Only request the minimum capabilities needed. Only expose
   the minimum data necessary.
4. **Validate, Sanitize, Escape.** The WordPress security model is:
   - **Validate** data to check it meets expected criteria (data validation)
   - **Sanitize** data on input before storage (securing input)
   - **Escape** data on output before rendering (securing output)
   These are three distinct operations and all three must be used together.

---

## Input Sanitization

Sanitize every piece of external input before using it in any operation. WordPress provides
purpose-built sanitization functions — use them.

### Sanitization Function Reference

| Data Type | Function | When to Use |
|-----------|----------|-------------|
| Plain text | `sanitize_text_field()` | Any single-line text input |
| Textarea | `sanitize_textarea_field()` | Multi-line text inputs |
| Email | `sanitize_email()` | Email address fields |
| URL | `esc_url_raw()` | URLs being stored in the database |
| Integer | `absint()` or `intval()` | Numeric IDs, quantities, amounts |
| Float | `floatval()` + range check | Prices, rates, percentages |
| HTML | `wp_kses()` or `wp_kses_post()` | Rich text that needs some HTML |
| File name | `sanitize_file_name()` | Uploaded file names |
| Key/slug | `sanitize_key()` | Option names, meta keys, slugs |
| Title | `sanitize_title()` | URL slugs, post titles |
| Hex color | `sanitize_hex_color()` | Color picker values |

### Example: Sanitizing Form Input

```php
$settings = array(
	'api_key'      => sanitize_text_field( wp_unslash( $_POST['api_key'] ?? '' ) ),
	'webhook_url'  => esc_url_raw( wp_unslash( $_POST['webhook_url'] ?? '' ) ),
	'max_retries'  => absint( $_POST['max_retries'] ?? 3 ),
	'tax_rate'     => max( 0, min( 100, floatval( $_POST['tax_rate'] ?? 0 ) ) ),
	'description'  => sanitize_textarea_field( wp_unslash( $_POST['description'] ?? '' ) ),
);
```

Always call `wp_unslash()` before sanitizing `$_POST` / `$_GET` data because WordPress adds
slashes to superglobals.

### Data Validation (Per Plugin Handbook)

Validation checks that data meets specific criteria BEFORE sanitizing or using it. WordPress
provides these validation functions:

```php
// Check data types.
is_numeric( $value );
is_email( $value );
is_array( $value );

// WordPress-specific validators.
wp_validate_boolean( $value );
term_exists( $term, $taxonomy );
username_exists( $username );

// Custom validation example.
if ( ! in_array( $status, array( 'pending', 'active', 'completed' ), true ) ) {
	return new \WP_Error( 'invalid_status', __( 'Invalid status value.', 'plugin-slug' ) );
}

// Range validation for numeric values.
$quantity = absint( $_POST['quantity'] ?? 0 );
if ( $quantity < 1 || $quantity > 999 ) {
	return new \WP_Error( 'invalid_quantity', __( 'Quantity must be between 1 and 999.', 'plugin-slug' ) );
}
```

---

## Output Escaping

Escape every piece of dynamic data at the point of output. Even data from the database — it
may have been compromised or injected before your plugin was installed.

### Escaping Function Reference

| Context | Function | When to Use |
|---------|----------|-------------|
| HTML body | `esc_html()` | Text content inside HTML tags |
| HTML attributes | `esc_attr()` | Inside attribute values (`value=""`, `title=""`) |
| URLs | `esc_url()` | Inside `href`, `src`, `action` attributes |
| JavaScript | `esc_js()` | Inside inline JavaScript (avoid if possible) |
| Translated HTML | `esc_html__()` / `esc_html_e()` | Translatable strings in HTML |
| Translated attr | `esc_attr__()` / `esc_attr_e()` | Translatable strings in attributes |
| CSS | Use `safecss_filter_attr()` | Dynamic inline styles |

### Escaping Pattern

```php
<input
	type="text"
	name="plugin_slug_api_key"
	value="<?php echo esc_attr( $api_key ); ?>"
	class="regular-text"
/>
<p class="description">
	<?php echo esc_html__( 'Enter your API key.', 'plugin-slug' ); ?>
</p>
<a href="<?php echo esc_url( $dashboard_url ); ?>">
	<?php echo esc_html__( 'View Dashboard', 'plugin-slug' ); ?>
</a>
```

**The rule is simple: escape late, escape once, and use the right function for the context.**

---

## Nonces & CSRF Protection

Every form submission and AJAX request must include a nonce, and the handler must verify it.
This prevents Cross-Site Request Forgery attacks.

### Form Nonces

```php
// In the form template:
wp_nonce_field( 'plugin_slug_save_settings', 'plugin_slug_nonce' );

// In the handler:
if ( ! isset( $_POST['plugin_slug_nonce'] )
	|| ! wp_verify_nonce(
		sanitize_text_field( wp_unslash( $_POST['plugin_slug_nonce'] ) ),
		'plugin_slug_save_settings'
	)
) {
	wp_die( esc_html__( 'Security check failed.', 'plugin-slug' ) );
}
```

### AJAX Nonces

```php
// Localize the nonce to JS:
wp_localize_script( 'plugin-slug-admin', 'pluginSlugAdmin', array(
	'ajax_url' => admin_url( 'admin-ajax.php' ),
	'nonce'    => wp_create_nonce( 'plugin_slug_ajax' ),
) );

// In the AJAX handler:
check_ajax_referer( 'plugin_slug_ajax', 'nonce' );
```

### REST API Nonces

WooCommerce REST API endpoints use their own authentication. For custom WordPress REST API
endpoints, use `permission_callback` with capability checks instead of nonces:

```php
register_rest_route( 'plugin-slug/v1', '/settings', array(
	'methods'             => 'POST',
	'callback'            => array( $this, 'update_settings' ),
	'permission_callback' => function () {
		return current_user_can( 'manage_woocommerce' );
	},
) );
```

---

## Capability Checks

Every admin action must verify the user has the required capability. Don't rely on menu
visibility alone — direct URL access can bypass menus.

```php
// Before processing any admin action:
if ( ! current_user_can( 'manage_woocommerce' ) ) {
	wp_die( esc_html__( 'You do not have permission to perform this action.', 'plugin-slug' ) );
}
```

### Common WooCommerce Capabilities

| Capability | Who Has It | Use For |
|-----------|-----------|---------|
| `manage_woocommerce` | Shop Manager, Admin | Plugin settings, order management |
| `edit_shop_orders` | Shop Manager, Admin | Viewing/editing orders |
| `view_woocommerce_reports` | Shop Manager, Admin | Reports and analytics |
| `manage_options` | Admin only | Site-wide configuration |

---

## Database Security

### Prepared Statements

Every custom database query must use `$wpdb->prepare()`. No exceptions.

```php
global $wpdb;

// Correct — parameterized query
$results = $wpdb->get_results(
	$wpdb->prepare(
		"SELECT * FROM {$wpdb->prefix}plugin_slug_logs WHERE order_id = %d AND status = %s",
		$order_id,
		$status
	)
);

// WRONG — direct variable interpolation (SQL injection vulnerability)
// $results = $wpdb->get_results( "SELECT * FROM ... WHERE order_id = $order_id" );
```

### Table Creation

Use `dbDelta()` for creating and updating custom tables, and always use `$wpdb->prefix`.

```php
global $wpdb;
$table_name      = $wpdb->prefix . 'plugin_slug_logs';
$charset_collate = $wpdb->get_charset_collate();

$sql = "CREATE TABLE $table_name (
	id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
	order_id bigint(20) unsigned NOT NULL,
	action varchar(50) NOT NULL,
	details longtext,
	created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY  (id),
	KEY order_id (order_id),
	KEY created_at (created_at)
) $charset_collate;";

require_once ABSPATH . 'wp-admin/includes/upgrade.php';
dbDelta( $sql );
```

---

## File Security

- Validate file types by checking MIME type, not just extension
- Use `wp_handle_upload()` for any file uploads
- Store uploaded files outside the web root when possible
- Add index.php files to all plugin directories to prevent directory browsing
- Check file permissions before writing

---

## API Security

### REST Endpoint Authorization

- **Never** use `'permission_callback' => '__return_true'` on any route that returns or mutates
  merchant, customer, order, or payment data — an open `permission_callback` is a leading cause of
  WordPress plugin REST vulnerabilities. Gate reads on an appropriate `current_user_can()` capability,
  and gate admin writes on **both** a capability check and nonce verification.
- The same rule applies to WordPress Abilities exposed to AI agents: every executable ability needs a
  real `permission_callback` and MCP discovery does not bypass it (see `references/abilities-and-mcp.md`).

### Outbound API Calls

- Use `wp_remote_get()` / `wp_remote_post()` (never `cURL` directly)
- Validate SSL certificates (don't disable SSL verification)
- Implement timeouts (default is 5 seconds, set explicitly)
- Don't log sensitive data (API keys, tokens) — mask in logs
- Store API credentials in the options table, never in code

### Inbound Webhooks

- Verify webhook signatures with a **timing-safe** comparison (`hash_equals()`), never `==` / `===`
- Protect against replay: reject stale timestamps and de-duplicate on the provider's event ID (idempotency)
- Validate the payload schema before processing
- Respond with 200 quickly, then process asynchronously via Action Scheduler
- Rate-limit incoming webhooks

```php
// Timing-safe HMAC verification over the raw request body.
$payload   = file_get_contents( 'php://input' );
$signature = isset( $_SERVER['HTTP_X_SIGNATURE'] )
	? sanitize_text_field( wp_unslash( $_SERVER['HTTP_X_SIGNATURE'] ) )
	: '';
$expected  = base64_encode( hash_hmac( 'sha256', $payload, $webhook_secret, true ) );

if ( ! hash_equals( $expected, $signature ) ) {
	status_header( 401 );
	exit;
}

// Replay / idempotency: skip if this event was already processed.
if ( get_transient( 'plugin_slug_evt_' . $event_id ) ) {
	status_header( 200 );
	exit;
}
set_transient( 'plugin_slug_evt_' . $event_id, 1, DAY_IN_SECONDS );
```

> For webhooks WooCommerce itself sends, note that WooCommerce passes the configured secret through
> `wp_specialchars_decode()` before signing, and the `X-WC-Webhook-Signature` header is a base64
> HMAC-SHA256 of the payload.

---

## Financial Data Security

For plugins that handle prices, payments, or financial transactions:

### Decimal Precision
- Use `wc_format_decimal()` for all price calculations
- Store prices as strings in meta to avoid floating-point errors
- Never use `round()` on financial amounts without specifying precision
- Match the store's configured decimal precision (`wc_get_price_decimals()`)

### Idempotency
- Every payment operation must be idempotent
- Use unique transaction IDs / idempotency keys
- Check for duplicate processing before executing

### PCI-DSS Considerations
- Never store raw credit card numbers, CVVs, or full magnetic stripe data
- Use tokenization through payment gateways
- Transmit payment data only over HTTPS
- Log access to payment-related functionality
- Meet the PCI DSS v4.0.1 payment-page **script-management** requirements — 6.4.3 (script
  authorization, integrity, and inventory) and 11.6.1 (payment-page tamper detection), mandatory since
  31 March 2025. Keep the PAN out of the merchant DOM and minimize scripts on checkout. See
  `references/pci-script-management.md`.

---

## WordPress Core Security Baseline

Build on the platform's primitives rather than reimplementing weaker equivalents:

- WordPress core hashes passwords with **bcrypt** (and application passwords / reset keys with BLAKE2b)
  in recent releases — use the core auth APIs rather than rolling your own credential hashing.
- Prefer the WordPress core **HTML API** over hand-rolled HTML string manipulation for safer output.
- Store gateway secrets in a `WC_Payment_Gateway` password-type field (or an option with `autoload=no`),
  never in code and never in logs.

---

## Logging & Audit Trails

Use the WooCommerce logger for all plugin logging:

```php
$logger = wc_get_logger();
$context = array( 'source' => 'plugin-slug' );

$logger->info( 'Payment processed successfully for order #' . $order_id, $context );
$logger->error( 'API request failed: ' . $response_message, $context );
$logger->debug( 'Webhook payload received', $context );
```

### What to Log

- All API requests and responses (with sensitive data masked)
- All payment operations (initiate, complete, fail, refund)
- All admin configuration changes
- All errors and exceptions
- Authentication events

### What NOT to Log

- Credit card numbers, CVVs, or full account numbers
- Raw API keys or tokens
- Personally identifiable information (mask or hash)
- Full request/response bodies in production (use debug level)
