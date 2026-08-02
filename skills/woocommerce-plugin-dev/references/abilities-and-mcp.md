# WordPress Abilities API and MCP reference

Use this reference to expose WooCommerce plugin operations to agents and automation through the
**WordPress Abilities API** and **Model Context Protocol (MCP)**. Keep this surface distinct from the
REST API and Store API.

**Official sources:**
- WordPress Abilities API (announcement): https://developer.wordpress.org/news/2025/11/introducing-the-wordpress-abilities-api/
- Abilities API handbook: https://developer.wordpress.org/apis/abilities-api/
- WordPress MCP Adapter: https://github.com/WordPress/mcp-adapter
- WooCommerce MCP integration: https://developer.woocommerce.com/docs/features/mcp/
- WooCommerce AI overview: https://developer.woocommerce.com/docs/getting-started/ai/
- Official WooCommerce demo plugin: https://github.com/woocommerce/wc-mcp-ability
- Model Context Protocol spec: https://modelcontextprotocol.io/specification/2026-07-28

> **Status (verify at build time — this area moves fast).** The Abilities API is a core WordPress API
> introduced in 6.9 and is also distributed as the canonical `wordpress/abilities-api` plugin +
> Composer package; confirm the target WordPress version and guard with
> `function_exists( 'wp_register_ability' )`. WooCommerce's MCP integration is currently a
> **developer preview**; it first shipped as a beta in WooCommerce 10.3 (Oct 2025) and introduced
> **canonical product/order domain abilities in 10.9**.
> The earlier `Automattic/wp-feature-api` and `Automattic/wordpress-mcp` projects are the lineage of
> this work; new code should target the **Abilities API + MCP Adapter**, not the Feature API.

---

## Table of contents
1. [The three-layer model](#the-three-layer-model)
2. [Registering an ability](#registering-an-ability)
3. [Exposing an ability through MCP](#exposing-an-ability-through-mcp)
4. [The WooCommerce path](#the-woocommerce-path)
5. [Security and permissions](#security-and-permissions)
6. [Connecting an MCP client](#connecting-an-mcp-client)
7. [Checklist](#checklist)

---

## The three-layer model

Keep these three layers distinct — they are separate projects with separate jobs:

| Layer | What it is | Project |
|-------|-----------|---------|
| **Abilities API** | A registry where plugins, themes, and core declare *named, schema-defined capabilities* ("abilities") — each with inputs, outputs, a permission check, and an execute callback. | `wordpress/abilities-api` (core API as of WP 6.9) |
| **MCP Adapter** | The official bridge that projects registered abilities as **MCP tools, resources, and prompts** over HTTP and STDIO transports, so any MCP client can discover and invoke them. | `WordPress/mcp-adapter` |
| **MCP client / agent** | The consumer — Claude, an in-site assistant, an automation runner — that speaks the Model Context Protocol. | external |

The flow is one-directional: **register an Ability → the MCP Adapter exposes it → an agent calls it**.
Execution always returns through the ability's permission callback. The same registered capability
can support REST, WP-CLI, automation, and admin tooling.

---

## Registering an ability

Register abilities on the `wp_abilities_api_init` hook with `wp_register_ability()`. Always guard on
`function_exists()` so the plugin degrades gracefully on sites without the API.

```php
add_action( 'wp_abilities_api_init', function () {
	if ( ! function_exists( 'wp_register_ability' ) ) {
		return;
	}

	wp_register_ability(
		'plugin-slug/get-recent-orders',
		array(
			'label'       => __( 'Get Recent Orders', 'plugin-slug' ),
			'description' => __( 'Return the most recent WooCommerce orders with status and total.', 'plugin-slug' ),
			'category'    => 'woocommerce',
			'meta'        => array(
				'mcp' => array(
					'public' => true,
				),
			),
			'input_schema'  => array(
				'type'       => 'object',
				'properties' => array(
					'limit' => array(
						'type'        => 'integer',
						'description' => __( 'How many orders to return.', 'plugin-slug' ),
						'default'     => 10,
						'minimum'     => 1,
						'maximum'     => 50,
					),
				),
			),
			'output_schema' => array(
				'type'  => 'array',
				'items' => array(
					'type'       => 'object',
					'properties' => array(
						'id'     => array( 'type' => 'integer' ),
						'status' => array( 'type' => 'string' ),
						'total'  => array( 'type' => 'string' ),
					),
				),
			),
			// Executes the ability. Use WooCommerce CRUD — never get_post_meta() on orders.
			'execute_callback'    => function ( array $input ): array {
				$orders = wc_get_orders(
					array(
						'limit'   => $input['limit'] ?? 10,
						'orderby' => 'date',
						'order'   => 'DESC',
					)
				);

				return array_map(
					static function ( $order ) {
						return array(
							'id'     => $order->get_id(),
							'status' => $order->get_status(),
							'total'  => $order->get_total(),
						);
					},
					$orders
				);
			},
			// Runs on EVERY invocation, regardless of transport. No open abilities that touch store data.
			'permission_callback' => function (): bool {
				return current_user_can( 'edit_shop_orders' );
			},
		)
	);
} );
```

Key fields: a **namespaced name** (`plugin-slug/ability-name`), `label`, `description`,
`input_schema` and `output_schema` (JSON Schema — the same schema vocabulary the REST API uses),
an `execute_callback`, and a `permission_callback`. Schemas are not optional decoration: they are
how an agent discovers what the ability does and validates its arguments. Use WooCommerce core's
`woocommerce` category, or register a plugin-owned category with `wp_register_ability_category()`
before assigning it.

---

## Exposing an ability through MCP

A registered ability is not automatically reachable by an external agent — it must be exposed
through an MCP server. There are two routes.

**1. The WordPress MCP Adapter default server (default path).**
Set the `meta.mcp.public` flag and the MCP Adapter's default server makes the ability discoverable:

```php
// Add to the ability definition array:
'meta' => array(
	'mcp' => array(
		'public' => true, // Discoverable on the MCP Adapter default server.
	),
),
```

On the default server, public abilities are reached through the adapter's built-in tools
(`mcp-adapter/discover-abilities`, `mcp-adapter/get-ability-info`, `mcp-adapter/execute-ability`)
at `/wp-json/mcp/mcp-adapter-default-server`, rather than each appearing individually in
`tools/list`. A custom MCP server can instead list specific abilities directly as tools, resources,
or prompts. Install the adapter via Composer (the Jetpack Autoloader is recommended when several
bundling plugins may coexist).

**2. Deprecated Woo endpoint compatibility only.**
The `woocommerce_mcp_include_ability` filter belongs to WooCommerce's deprecated MCP endpoint.
Use it only when intentionally maintaining compatibility with that endpoint on a verified deployed
WooCommerce version; new integrations should use the shared WordPress MCP Adapter and
`meta.mcp.public`.

---

## The WooCommerce path

A complete, minimal WooCommerce ability registers on `wp_abilities_api_init`, uses the WooCommerce
category, gates execution on a WooCommerce capability, and opts into the shared MCP Adapter with
`meta.mcp.public`.

```php
<?php
/**
 * Plugin Name: Example Commerce Abilities
 * Requires Plugins: woocommerce
 * Requires PHP:     8.1
 *
 * @package PluginSlug
 */

declare( strict_types=1 );

namespace PluginSlug;

defined( 'ABSPATH' ) || exit;

add_action( 'wp_abilities_api_init', __NAMESPACE__ . '\\register_abilities' );

function register_abilities(): void {
	if ( ! function_exists( 'wp_register_ability' ) ) {
		return;
	}
	wp_register_ability(
		'plugin-slug/store-summary',
		array(
			'label'               => __( 'Get Store Summary', 'plugin-slug' ),
			'description'         => __( 'Read-only store name, currency, and WooCommerce version.', 'plugin-slug' ),
			'category'            => 'woocommerce',
			'meta'                => array(
				'mcp' => array(
					'public' => true,
				),
			),
			'input_schema'        => array( 'type' => 'object', 'properties' => array() ),
			'output_schema'       => array(
				'type'                 => 'object',
				'properties'           => array(
					'store_name'          => array( 'type' => 'string' ),
					'currency'            => array( 'type' => 'string' ),
					'woocommerce_version' => array( 'type' => 'string' ),
				),
				'required'             => array( 'store_name', 'currency', 'woocommerce_version' ),
				'additionalProperties' => false,
			),
			'execute_callback'    => __NAMESPACE__ . '\\get_store_summary',
			'permission_callback' => static fn (): bool => current_user_can( 'manage_woocommerce' ),
		)
	);
}

function get_store_summary(): array {
	return array(
		'store_name'          => get_bloginfo( 'name' ),
		'currency'            => get_woocommerce_currency(),
		'woocommerce_version' => defined( 'WC_VERSION' ) ? WC_VERSION : '',
	);
}
```

Notes:
- Use the core-supported **`Requires Plugins: woocommerce`** header to declare the WooCommerce
  dependency.
- Inside `execute_callback`, follow the same rules as everywhere else in this toolkit: WooCommerce CRUD
  (`wc_get_orders`, `$order->get_meta()`), never `get_post_meta()` on orders; validate inputs; return
  values that match `output_schema`; escape only when a value is later rendered into a specific context.

---

## Security and permissions

An ability that an AI agent can invoke is a **privileged surface**, governed by the same rules as a
REST endpoint — not a relaxed one:

- **Give every executable ability a real `permission_callback`.** Never register an ability that
  reads or mutates store/customer/payment data with an open or trivially-true permission check. MCP
  discovery does **not** bypass WordPress permissions — the callback runs on every invocation.
- **Default to read-only.** Expose read operations (query orders, read settings, inspect a gateway's
  public configuration) first. Gate any write/mutating ability behind an explicit, vetted capability
  (typically `manage_woocommerce` or `edit_shop_orders`) and treat it like an admin action.
- **Never expose secrets.** An ability that returns gateway configuration must omit API keys, tokens,
  and other credentials, exactly as you would scrub them from logs and REST responses.
- **Validate inputs against `input_schema`** and re-validate in `execute_callback` — schema is a
  contract for discovery, not a substitute for server-side validation.
- **Match `output_schema` without generic HTML escaping.** JSON values are data. Escape them only when
  a later consumer renders them into HTML, an attribute, a URL, or JavaScript.
- **Audit log** mutating abilities the same way you log other privileged operations.

For payment-gateway plugins, add an "abilities/MCP exposure" trace path to the pre-release review:
which abilities are registered, which are MCP-public, what capability each requires, and that none
return secrets — the same diligence the `woocommerce-finalize` skill applies to payment/refund/webhook
paths.

---

## Connecting an MCP client

For local development you can drive the default server over STDIO via WP-CLI, and point an MCP client
(Claude Desktop, Claude Code, VS Code, Cursor, …) at it:

```jsonc
{
  "mcpServers": {
    "wordpress-local": {
      "command": "wp",
      "args": [
        "--path=/path/to/your/wordpress/site",
        "mcp-adapter",
        "serve",
        "--server=mcp-adapter-default-server",
        "--user=plugin-audit"
      ]
    }
  }
}
```

Use a dedicated WordPress identity with only the least-privilege capabilities the exposed abilities
need; do not delegate through a general administrator account.

HTTP transport is exposed under `/wp-json/mcp/<server>`. See the MCP Adapter docs for production
transport, authentication, and custom-server configuration.

---

## Checklist

- [ ] Abilities registered on `wp_abilities_api_init`, guarded by `function_exists( 'wp_register_ability' )`.
- [ ] Namespaced names (`plugin-slug/...`), with `input_schema` and `output_schema`.
- [ ] A real `permission_callback` on every ability; read-only by default; secrets never returned.
- [ ] Abilities use the `woocommerce` category (or a registered plugin category) and `meta.mcp.public`
      for the shared WordPress MCP Adapter default server.
- [ ] `woocommerce_mcp_include_ability` appears only when deprecated endpoint compatibility is required.
- [ ] `execute_callback` uses WooCommerce CRUD and validates inputs server-side.
- [ ] MCP-exposed operations are covered in the pre-release/finalize review.
- [ ] Target version and the Abilities API's core-bundling state verified against current release notes.
