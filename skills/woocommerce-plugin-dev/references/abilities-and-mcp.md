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
4. [WordPress 7.1 exposure, validation, and schemas](#wordpress-71-exposure-validation-and-schemas)
5. [MCP Adapter 0.7 installation](#mcp-adapter-07-installation)
6. [The WooCommerce path](#the-woocommerce-path)
7. [Security and permissions](#security-and-permissions)
8. [Connecting an MCP client](#connecting-an-mcp-client)
9. [Checklist](#checklist)

---

## The three-layer model

Keep these three layers distinct — they are separate projects with separate jobs:

| Layer | What it is | Project |
|-------|-----------|---------|
| **Abilities API** | A registry where plugins, themes, and core declare *named, schema-defined capabilities* ("abilities") — each with inputs, outputs, a permission check, and an execute callback. | `wordpress/abilities-api` (core API as of WP 6.9) |
| **MCP Adapter** | The official bridge that projects registered abilities as **MCP tools, resources, and prompts** over HTTP and STDIO transports, so any MCP client can discover and invoke them. | `WordPress/mcp-adapter` |
| **MCP client / agent** | The consumer — Claude, an in-site assistant, an automation runner — that speaks the Model Context Protocol. | external |

The flow is one-directional: **register an Ability → the MCP Adapter exposes it → an agent calls it**.
On the normal core path, execution passes through the ability's permission callback; a custom
`wp_pre_execute_ability` short-circuit bypasses it and must enforce equivalent authorization. The same registered capability
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
			// Runs on every normal-path invocation, regardless of transport; a pre-execute short-circuit must enforce its own authorization. No open abilities that touch store data.
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
Set the `meta.mcp.public` channel flag (the form used by this reference's examples and by older
bundled adapters; see the WordPress 7.1 section below for `meta.public`) and the MCP Adapter's
default server makes the ability discoverable:

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
or prompts. See "MCP Adapter 0.7 installation" below for version-scoped installation guidance.

**2. Deprecated Woo endpoint compatibility only.**
The `woocommerce_mcp_include_ability` filter belongs to WooCommerce's deprecated MCP endpoint.
Use it only when intentionally maintaining compatibility with that endpoint on a verified deployed
WooCommerce version; new integrations should use the shared WordPress MCP Adapter and
`meta.mcp.public`.

---

## WordPress 7.1 exposure, validation, and schemas

These notes apply only to sites running WordPress 7.1 or later. Do not raise a plugin's minimum
WordPress or WooCommerce version to use them; keep the older registration working and guard on the
installed version.

In WordPress 7.1, `meta.public` records an ability's general exposure intent. REST resolves
`$meta['show_in_rest'] ?? $meta['public'] ?? false`, so `public => true` makes `show_in_rest` default
to true, and resolved metadata always carries a boolean `public` that defaults to `false`.
Source (August 4, 2026): https://make.wordpress.org/core/2026/08/04/a-unified-public-exposure-flag-for-abilities-in-wordpress-7-1/

An explicit channel value overrides `public`: `public => true` with `show_in_rest => false` stays
hidden from REST, and `public => false` with `show_in_rest => true` is exposed. Null-coalescing keeps an
explicit `false`; only `null` counts as unset. Existing `show_in_rest` registrations remain valid and
need no migration. An integration must not overwrite an explicit channel opt-out because `public` is true.
Source: https://make.wordpress.org/core/2026/08/04/a-unified-public-exposure-flag-for-abilities-in-wordpress-7-1/

Keep `meta.mcp.public` when the deployment may run on a WordPress release earlier than 7.1 or on an
MCP Adapter that does not yet read `meta.public`; the dev note says the adapter will respect the
unified flag starting with its next release, so verify the installed adapter version. Keep the channel
value explicit, because a channel value takes precedence over `public`.
Source: https://make.wordpress.org/core/2026/08/04/a-unified-public-exposure-flag-for-abilities-in-wordpress-7-1/

`meta.public`, `show_in_rest`, and `meta.mcp.public` control discoverability and client exposure. They
are not authorization and do not replace `permission_callback`, which must still run and check a real
capability on every normal-path invocation. Never treat an exposure flag as a security boundary.
Source: https://make.wordpress.org/core/2026/08/04/a-unified-public-exposure-flag-for-abilities-in-wordpress-7-1/

WordPress 7.1 adds the `wp_ability_validate_input` and `wp_ability_validate_output` filters for custom
ability validation. `validate_callback` and `sanitize_callback` in an ability schema are REST-style
conventions that the Abilities API runtime validation does not run, so they are not executed for
abilities: do not rely on them, and keep server-side checks in the filters or in `execute_callback`.
Source (July 31, 2026): https://make.wordpress.org/core/2026/07/31/json-schema-preparation-for-client-compatibility-in-wordpress-7-1/

On the normal runtime path, the installed WordPress 7.1.3 `WP_Ability` validates input against the
canonical `input_schema` before `execute_callback` runs and validates the result against `output_schema`
before returning it. Additional domain checks supplement this validation rather than replace it, and the
REST-style `validate_callback` and `sanitize_callback` schema keys still do not run. This describes the
core pipeline only; it does not promise that every custom filter or a rollback is covered.
Source (WordPress 7.1.3): https://github.com/WordPress/wordpress-develop/blob/7.1.3/src/wp-includes/abilities-api/class-wp-ability.php

A `wp_pre_execute_ability` short-circuit in WordPress 7.1.3 returns before input normalization,
`validate_input()`, `check_permissions()` (so before `permission_callback`), and output validation.
Qualify the guarantee: it holds for the normal path, not every path. A callback on that filter must
enforce equivalent authorization itself, and validate any `$input` it consumes, because the core
`permission_callback` is bypassed; do not return data or write from a short-circuit without that check.
This is not permission to leave abilities open: still register a real `permission_callback` for the
normal path, and do not rely on schema validation for authorization.
Source (WordPress 7.1.3): https://github.com/WordPress/wordpress-develop/blob/7.1.3/src/wp-includes/abilities-api/class-wp-ability.php

Core already prepares ability schemas for Abilities REST responses and AI Client function
declarations with `wp_prepare_json_schema_for_client()`. Keep the canonical WordPress schema stored on
the ability for server-side use and never replace it with the prepared version. Call the function
directly only on a copy, when a custom REST endpoint, JavaScript configuration, MCP tool declaration,
or other external consumer receives a WordPress-style schema.
Source (July 31, 2026): https://make.wordpress.org/core/2026/07/31/json-schema-preparation-for-client-compatibility-in-wordpress-7-1/

WordPress 7.2 is not released. Its official schedule lists Beta 1 on October 20, 2026 and the final
release on December 8, 2026; watch it, and do not target it or treat proposals as stable contracts.
Source: https://make.wordpress.org/core/7-2/

## MCP Adapter 0.7 installation

MCP Adapter 0.7.0 recommends the canonical plugin and deprecates using the adapter as a bundled
Composer library, so the canonical plugin is the optional integration to prefer for new standalone
installs, not a hard dependency every ability plugin must require. The Jetpack Autoloader approach is
legacy bundling guidance for adapters before 0.7 and is now deprecated.
Source: https://github.com/WordPress/mcp-adapter/releases/tag/v0.7.0

WooCommerce 11.2.0's own composer manifest still declares `wordpress/mcp-adapter` `^0.3.0`, so its
bundled adapter and the standalone plugin are different version boundaries. Do not blindly replace,
remove, or deduplicate WooCommerce's bundled adapter; verify the installed WooCommerce and adapter
versions on the target site first.
Source: https://github.com/woocommerce/woocommerce/blob/11.2.0/plugins/woocommerce/composer.json

For migration steps, follow the version-pinned upstream guide rather than copying its commands here:
https://github.com/WordPress/mcp-adapter/blob/v0.7.0/docs/migration/v0.7.0.md

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
  discovery does **not** bypass WordPress permissions — the callback runs on every normal-path
  invocation, and any `wp_pre_execute_ability` short-circuit must enforce equivalent authorization itself.
- **Default to read-only.** Expose read operations (query orders, read settings, inspect a gateway's
  public configuration) first. Gate any write/mutating ability behind an explicit, vetted capability
  (typically `manage_woocommerce` or `edit_shop_orders`) and treat it like an admin action.
- **Never expose secrets.** An ability that returns gateway configuration must omit API keys, tokens,
  and other credentials, exactly as you would scrub them from logs and REST responses.
- **Declare accurate `input_schema` and `output_schema`.** The normal runtime validates against them
  (see the WordPress 7.1 section), and domain checks in `execute_callback` supplement that validation.
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
- [ ] On WordPress 7.1+, an explicit channel `false` is retained over `meta.public`, and exposure never
      substitutes for `permission_callback`; the older `meta.mcp.public` form is kept where older
      bundled adapters or WordPress releases must be supported.
- [ ] Canonical server schemas stay registered; only copies are prepared for outbound clients, and
      `validate_callback`/`sanitize_callback` are not treated as runtime validation.
- [ ] WooCommerce's bundled `^0.3.0` adapter is not blindly replaced; adapter installation follows the
      version-pinned upstream guide.
- [ ] `woocommerce_mcp_include_ability` appears only when deprecated endpoint compatibility is required.
- [ ] `execute_callback` uses WooCommerce CRUD and validates inputs server-side.
- [ ] MCP-exposed operations are covered in the pre-release/finalize review.
- [ ] Target version and the Abilities API's core-bundling state verified against current release notes.
