# WordPress and WooCommerce coding standards

The repository is the executable standard. Read its compatibility declarations, lockfiles, lint and
static-analysis configuration, neighboring code, and documented commands before changing style or
tooling. Do not paste a generic WPCS setup into an established project.

**Official sources:**
- WordPress Coding Standards: https://developer.wordpress.org/coding-standards/
- WordPress PHP Standards: https://developer.wordpress.org/coding-standards/wordpress-coding-standards/php/
- WooCommerce Coding Standards: https://developer.woocommerce.com/docs/best-practices/coding-standards/
- WPCS 3.4.0 release: https://github.com/WordPress/WordPress-Coding-Standards/releases/tag/3.4.0

## Repository-first rules

- Align syntax and tooling to the project's tested PHP floor and its declared WordPress/WooCommerce
  support. For a new project, choose and test a floor from product/distribution requirements rather
  than this reference.
- Run the repository's configured formatter, linter, compatibility checker, and static analyzer with
  its existing rules and versions. Add configuration only when the project needs that tool and has no
  equivalent.
- Follow the repository's established convention for files, namespaces, imports, method names,
  arrays, types, and documentation unless an applicable official rule or failing configured check
  requires a focused change.
- Keep changes consistent with adjacent maintained code; avoid formatting unrelated files.

## WPCS / PHPCS updates

Before adding or upgrading WPCS, inspect `composer.json`, `composer.lock`, `phpcs.xml*`, and the canonical lint script. Record the installed WPCS, PHP_CodeSniffer, PHPCSUtils, and supported WordPress version. Do not upgrade a repository's lint dependencies or run a broad `phpcbf` pass by default.

For WPCS 3.4.0, PHP_CodeSniffer must be >=3.13.5 and PHPCSUtils >=1.2.2. Its default `minimum_wp_version` is 6.7, so set that property explicitly whenever the repository supports an older WordPress version. If configured, replace the deprecated `WordPress.Arrays.ArrayDeclarationSpacing` property `allow_single_item_single_line_associative_arrays` with `allow_single_item_single_line_explicit_key_arrays`; this is a name-only migration. `WordPress.PHP.NoSilencedErrors` no longer permits `@parse_url()`: make failure handling explicit and test the affected behavior rather than suppressing the diagnostic.

Run the configured PHPCS command and `vendor/bin/phpcs -i` after a tooling update. Classify new findings by supported version and real behavior. A lint pass does not establish security, checkout, database, or runtime correctness.

## Names and documentation

- Prefix global identifiers: functions, constants, hooks, option/meta/transient keys, cron hooks,
  script/style handles, REST namespaces, CSS selectors, and JavaScript globals.
- Namespaced classes already have collision protection. Follow project naming and autoloading for
  them instead of adding a redundant plugin prefix.
- Document public contracts and extension hooks to the level the project requires. Keep `@param`,
  `@return`, and signatures synchronized.
- Use @throws only when a function or method can really throw that exception; do not add ceremonial
  tags to every PHPDoc block.
- Comments explain non-obvious intent, invariants, or compatibility constraints, not line-by-line code.

## Output and platform conventions

- Validate canonical input, sanitize for storage, and escape once for the final HTML, attribute, URL,
  CSS, or JavaScript context. Validate JSON with schemas/types rather than HTML-escaping its values.
- Use translation functions and the project's text domain for user-facing strings.
- Use WordPress and WooCommerce APIs before direct filesystem, HTTP, SQL, order-table, or environment
  assumptions. Prepare unavoidable custom SQL.
- Use WooCommerce CRUD/data stores for order data so HPOS and legacy storage remain supported.

## Verification

Run the smallest configured check for touched files, then the documented project gate that owns those
files. A style change is complete when project commands pass without copied dependencies, unrelated
format churn, or a newly invented compatibility floor.
