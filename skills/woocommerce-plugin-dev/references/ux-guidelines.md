# WooCommerce UX Guidelines

Match the installed WooCommerce experience and the repository's existing UI before adding a new
surface. Use public WordPress/WooCommerce APIs and native components wherever they cover the behavior.

**Official sources:**
- WooCommerce UX Guidelines: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/
- UX best practices: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/best-practices/
- Settings: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/settings
- Navigation: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/navigation/
- Onboarding: https://developer.woocommerce.com/docs/extensions/ux-guidelines-extensions/onboarding/
- WordPress Accessibility Coding Standards: https://make.wordpress.org/accessibility/handbook/

## Placement and Settings

- Put order, product, shipping, payment, analytics, and settings behavior in the Woo surface merchants
  already use. Add a top-level menu only when the product is genuinely independent.
- Prefer the WooCommerce Settings API or the project's existing settings screen. Expose only settings
  required for current behavior, with safe defaults, clear labels, constraints, and recovery guidance.
- Do not duplicate navigation or settings across screens. Show notices only when action is needed, on
  relevant pages, and make dismissible notices persist their dismissal safely.
- Reuse WordPress/Woo components, styles, wording, and responsive patterns before custom JavaScript or
  design systems.

## Onboarding

Onboarding is optional. Add it only when setup cannot be made obvious in the normal settings or feature
flow. Keep it skippable, resumable, and limited to decisions required before the plugin can work.

Prefer public APIs. If no public extension point covers a required integration and an internal API is
the only viable option, feature-detect it and verify its contract against the installed target version;
otherwise use a settings page or admin notice. Do not copy internal onboarding implementations into a
plugin as a presumed stable contract.

Never block normal admin access, hide destructive defaults, collect unrelated data, or require account
connection before explaining why it is needed.

## Copy and Feedback

- Use concise sentence-case merchant language and WooCommerce terminology.
- State what happened, the affected object, and the safe next action. Do not expose stack traces,
  credentials, raw provider errors, or internal IDs that do not help the merchant.
- Preserve entered non-secret values after validation errors. Never redisplay stored secrets.
- Show progress for genuinely long work and make retry/interruption states truthful.

## Accessibility and Responsive Behavior

Meet WCAG 2.2 AA for every new or changed surface: semantic structure, programmatic labels and names,
keyboard operation, visible focus, appropriate contrast, non-color status cues, announced errors,
accessible authentication, and target sizing. Preserve zoom/reflow and avoid motion without a reduced-
motion path.

Use responsive native layouts, not fixed desktop widths. Verify the critical flow with keyboard and a
narrow viewport; test assistive-technology behavior when custom controls or dynamic updates make it
necessary.

## Completion Evidence

Exercise the smallest merchant/shopper journey affected, including validation and failure feedback.
Confirm placement, permissions, persistence, responsive behavior, and WCAG 2.2 AA basics with the
repository's existing checks before adding a browser harness solely for this reference.
