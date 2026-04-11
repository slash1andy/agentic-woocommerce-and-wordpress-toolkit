# WooCommerce UX Guidelines

This reference covers the UX and design standards for WooCommerce extensions. Following these
guidelines ensures your plugin integrates seamlessly with the WooCommerce admin and storefront
experience.

**Official sources:**
- WooCommerce UX Guidelines: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/
- UX Best Practices: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/best-practices/
- Settings Guidelines: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/settings
- Navigation: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/navigation/
- Onboarding: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/onboarding/

---

## Table of Contents
1. [Navigation & Placement](#navigation--placement)
2. [Settings Design](#settings-design)
3. [Onboarding](#onboarding)
4. [Colors & Styling](#colors--styling)
5. [Copy & Messaging](#copy--messaging)
6. [Admin Notices](#admin-notices)
7. [Mobile & Responsive](#mobile--responsive)

---

## Navigation & Placement

### The Golden Rule: Live Within WooCommerce

Per the official WooCommerce UX guidelines, **there is a 99.9% chance your product's navigation
and settings should live within the WooCommerce navigation, NOT as a separate top-level menu
item.** Merchants expect to find everything WooCommerce-related under the WooCommerce menu.

### Where to Put Your Plugin's UI

Place your plugin's navigation within the existing WooCommerce taxonomy. The goal is for
merchants to find your functionality where they expect it, not hunt for a new top-level menu.

**Good placement examples:**
- Extending orders → Add a tab/panel to the order edit screen
- Extending products → Add a tab in the Product Data meta box
- Plugin settings → Add a tab under WooCommerce > Settings
- Reports/analytics → Add to WooCommerce > Analytics
- Shipping methods → Register as a WooCommerce shipping method
- Payment gateways → Register as a WooCommerce payment gateway
- Store management tools → Add as a submenu under WooCommerce

**Avoid:**
- Adding top-level admin menu items unless your plugin is a complete standalone system
- Creating dashboard widgets unless they provide genuinely useful at-a-glance data
- Adding admin bar items
- Duplicating navigation — settings should be in ONE place, not scattered

### WooCommerce Admin Navigation

If your plugin needs its own navigation section, register it within the WooCommerce admin:

```php
add_action( 'admin_menu', function () {
	add_submenu_page(
		'woocommerce',
		__( 'Plugin Name', 'plugin-slug' ),
		__( 'Plugin Name', 'plugin-slug' ),
		'manage_woocommerce',
		'plugin-slug',
		array( $this, 'render_admin_page' )
	);
} );
```

### Store Management Links

For quick actions that merchants use frequently, you can add links to the WooCommerce
Home / Store Management section:

```php
add_filter( 'woocommerce_navigation_menu_items', function ( $items ) {
	$items[] = array(
		'id'         => 'plugin-slug',
		'title'      => __( 'Plugin Name', 'plugin-slug' ),
		'capability' => 'manage_woocommerce',
		'url'        => 'admin.php?page=plugin-slug',
	);
	return $items;
} );
```

---

## Settings Design

### Principles

1. **Use smart defaults.** Every setting should have a sensible default so the plugin works
   out of the box with zero configuration.
2. **Minimize options.** Only expose settings that are crucial to functionality. Move advanced
   or rarely used options to a separate section or behind a "Show advanced" toggle.
3. **Group logically.** Related settings go together. Frequently used settings at the top,
   destructive or advanced settings at the bottom.
4. **Use WooCommerce Settings API.** Integrate into WooCommerce > Settings rather than creating
   standalone settings pages. This provides a consistent UX and free validation/saving.

### Setting Types to Use

Use the WooCommerce settings field types — merchants are already familiar with them:

- `text` — Short text input
- `textarea` — Longer text
- `checkbox` — Boolean toggles
- `select` — Dropdown choices
- `multiselect` — Multiple selections
- `radio` — Mutually exclusive choices
- `number` — Numeric input with min/max
- `password` — Sensitive text (API keys)
- `color` — Color picker
- `title` — Section header
- `sectionend` — Section divider

### Setting Field Best Practices

```php
array(
	'title'       => __( 'Maximum Retries', 'plugin-slug' ),
	'desc'        => __( 'Number of times to retry failed API calls.', 'plugin-slug' ),
	'desc_tip'    => true,  // Show description as a tooltip, not inline.
	'id'          => 'plugin_slug_max_retries',
	'type'        => 'number',
	'default'     => '3',
	'custom_attributes' => array(
		'min'  => '1',
		'max'  => '10',
		'step' => '1',
	),
),
```

- Always provide a `default` value
- Use `desc_tip => true` for helper text — keeps the UI clean
- Use `custom_attributes` for HTML5 input constraints

---

## Onboarding

If your plugin requires initial setup (API key, account connection, configuration), provide a
guided onboarding experience.

### WooCommerce Task List Integration (Recommended)

The preferred onboarding mechanism is integrating with the WooCommerce Home Task List. This
puts your setup task alongside other WooCommerce setup tasks, providing a consistent
experience for merchants.

```php
use Automattic\WooCommerce\Admin\Features\OnboardingTasks\TaskLists;

add_action( 'init', function () {
	if ( class_exists( TaskLists::class ) ) {
		TaskLists::add_task(
			'extended', // The task list ID ('setup' for core, 'extended' for extensions).
			new \PluginSlug\Admin\Setup_Task()
		);
	}
} );
```

Your task class extends `Automattic\WooCommerce\Admin\Features\OnboardingTasks\Task`:

```php
namespace PluginSlug\Admin;

use Automattic\WooCommerce\Admin\Features\OnboardingTasks\Task;

class Setup_Task extends Task {

	public function get_id(): string {
		return 'plugin-slug-setup';
	}

	public function get_title(): string {
		return __( 'Set up Plugin Name', 'plugin-slug' );
	}

	public function get_content(): string {
		return __( 'Connect your account and configure settings.', 'plugin-slug' );
	}

	public function get_time(): string {
		return __( '2 minutes', 'plugin-slug' );
	}

	public function is_complete(): bool {
		return 'yes' === get_option( 'plugin_slug_setup_complete' );
	}

	public function get_action_url(): string {
		return admin_url( 'admin.php?page=plugin-slug-setup' );
	}
}
```

### Onboarding Principles

1. **Use the WooCommerce Task List** when possible — it's the standard onboarding mechanism
2. **Fall back to a setup wizard** if the Task List API isn't sufficient
3. **Make it skippable** — never force the merchant through onboarding
4. **Minimize steps** — aim for 3 steps or fewer
5. **Show progress** — indicate which step the merchant is on
6. **Provide a "Setup Later" link** — store that they've seen the wizard and show a reminder notice

### Setup Notice Pattern

```php
add_action( 'admin_notices', function () {
	if ( 'yes' === get_option( 'plugin_slug_setup_complete' ) ) {
		return;
	}

	$setup_url = admin_url( 'admin.php?page=plugin-slug-setup' );
	$dismiss_url = wp_nonce_url(
		admin_url( 'admin.php?plugin-slug-dismiss-setup=1' ),
		'plugin_slug_dismiss_setup'
	);
	?>
	<div class="notice notice-info is-dismissible">
		<p>
			<?php
			printf(
				/* translators: %s: Setup wizard URL */
				wp_kses(
					__( '<strong>Plugin Name</strong> is almost ready! <a href="%s">Complete setup</a> to get started.', 'plugin-slug' ),
					array(
						'strong' => array(),
						'a'      => array( 'href' => array() ),
					)
				),
				esc_url( $setup_url )
			);
			?>
		</p>
	</div>
	<?php
} );
```

---

## Colors & Styling

### Admin Color Scheme

Respect the merchant's chosen WordPress admin color scheme. Never hard-code admin colors.

```css
/* Good — uses CSS custom properties that respect the admin color scheme */
.plugin-slug-status-badge {
	background-color: var(--wp-admin-theme-color, #007cba);
	color: #fff;
}

/* Bad — hard-coded color that ignores the admin scheme */
.plugin-slug-status-badge {
	background-color: #0073aa;  /* Don't do this */
}
```

### Use WordPress Components

For admin UI, use existing WordPress and WooCommerce CSS classes:

- `.button`, `.button-primary`, `.button-secondary` — Buttons
- `.regular-text`, `.large-text`, `.small-text` — Text inputs
- `.widefat` — Full-width tables
- `.notice`, `.notice-success`, `.notice-error`, `.notice-warning` — Notices
- `.woocommerce-table` — WooCommerce-styled tables

### Accessibility

All admin UI must meet WCAG 2.0 AA standards:

- Color contrast ratio of at least 4.5:1 for normal text
- All interactive elements must be keyboard accessible
- Form labels must be associated with their inputs
- Error messages must be descriptive and visible

---

## Copy & Messaging

### Writing Style

- Keep copy short and direct — limit interface text to 120-140 characters
- Use sentence case for headings and labels ("Order settings" not "Order Settings")
- Use active voice ("Save settings" not "Settings will be saved")
- Avoid jargon — write for merchants, not developers
- Be consistent with WooCommerce terminology (e.g., "orders" not "purchases")

### Error Messages

- Describe what went wrong in plain language
- Tell the merchant what to do about it
- Don't show raw error codes or stack traces

```php
// Good
__( 'Could not connect to the API. Please check your API key in Settings.', 'plugin-slug' )

// Bad
__( 'Error: HTTP 401 Unauthorized. cURL error 6: Could not resolve host.', 'plugin-slug' )
```

---

## Admin Notices

Use admin notices sparingly. Merchants are already overwhelmed with notices from dozens of plugins.

### Rules

- Only show notices that require action
- Make all notices dismissible
- Don't show notices on every admin page — target relevant pages only
- Use the correct notice type: `notice-success`, `notice-error`, `notice-warning`, `notice-info`
- Never use notices for advertising, upselling, or review requests on activation

---

## Mobile & Responsive

Build all admin interfaces responsively. Many merchants manage their stores from tablets and phones.

- Use CSS flexbox or grid, not fixed widths
- Test at 768px and 1024px breakpoints
- Ensure touch targets are at least 44x44px
- Stack form fields vertically on narrow screens
- Use WooCommerce's existing responsive patterns as reference
