# WooCommerce Plugin Architecture

Use the target repository's bootstrap, lifecycle, dependency wiring, and source layout. Add structure
only for behavior being built; this reference defines Woo-specific boundaries rather than a canonical
tree.

**Official sources:**
- WordPress Plugin Handbook: https://developer.wordpress.org/plugins/
- WooCommerce extension best practices: https://developer.woocommerce.com/docs/extensions/best-practices-extensions/
- HPOS recipe book: https://developer.woocommerce.com/docs/features/orders/high-performance-order-storage/recipe-book/

## Bootstrap and Dependencies

Keep the main plugin file small: plugin metadata, direct-access guard, required dependency checks,
feature declarations that have evidence, and delegation to the project's existing bootstrap. Match
version requirements to the project's tested support matrix and distribution needs.

Load code only after required plugins/APIs are available. Prefer the repository's current autoloading
and object construction. Do not introduce Composer, a singleton, dependency container, or a new folder
layout unless current behavior needs it and no existing project pattern holds.

## Lifecycle

Keep activation, routine loading, deactivation, upgrade, and uninstall distinct:

- Activation performs only required, idempotent setup; expensive data migration should be resumable.
- Routine requests gate schema/data upgrades by committed version or progress state.
- Deactivation unschedules plugin work and releases temporary resources without deleting merchant data.
- Flush rewrite rules only when the plugin owns rewrite changes.
- Dependency failures should fail clearly without loading code that can fatal.

## WooCommerce Compatibility

### HPOS

Use WooCommerce CRUD objects and data stores for orders and order metadata. Query with
`wc_get_orders()` or project data stores instead of assuming `wp_posts`, `wp_postmeta`, or a specific
HPOS table. Test order behavior with HPOS enabled and disabled when both modes are supported.

Declare `custom_order_tables` compatibility only after the implementation and applicable tests support
it. Existing plugins should preserve the repository's declaration pattern.

### Cart and Checkout Blocks

Blocks compatibility is conditional. Classic hooks do not prove Store API or Cart/Checkout Blocks
behavior. If the plugin touches cart or checkout, implement and test each claimed surface through its
public extension API, then declare `cart_checkout_blocks` compatibility. Otherwise do not add the
declaration merely as scaffold.

### Other Features

Treat every WooCommerce feature declaration the same way: identify affected behavior, use its public
API, test the installed target, and declare only what the evidence supports.

## Storage and Background Work

Use core/Woo data APIs for shared entities. Add a custom table only for a demonstrated query,
consistency, or scale need. Version schema changes and make retry safe. Use Action Scheduler for
bounded resumable work when a request cannot finish safely in one execution.

## Uninstall Handler

Keep retained plugin data by default when the plugin is uninstalled. Destructive cleanup requires an
explicit opt-in that identifies exactly which plugin-owned data may be removed.

For approved cleanup:

- verify ownership of options, transients, scheduled actions, files, and custom records;
- preserve orders, payments, customer data, and shared records unless separately and explicitly owned;
- process order metadata through WooCommerce CRUD in bounded, resumable work for both storage modes;
- test interruption/resume and read back completion; and
- keep deactivation non-destructive.

## Verification

Exercise only changed lifecycle and compatibility surfaces, plus the repository's configured checks.
A declaration, migration, or cleanup claim is complete only when implementation evidence matches it.
