---
name: woocommerce-upgrade-safety
description: >
  Pre-release upgrade safety review for WooCommerce plugins. Validates database migrations,
  settings compatibility, payment token preservation, hook deprecation, rollback safety, and
  merchant communication for version upgrades. Use before any minor or major version release,
  when a release includes database schema changes, settings restructuring, new feature
  declarations (HPOS, blocks), deprecated hooks/filters, or payment flow changes. Also trigger
  when reviewing a diff that shows install class changes, dbDelta calls, payment token
  modifications, hook removals, or minimum version bumps. Skip for patch releases that contain
  only bug fixes with no structural changes.
---

# WooCommerce Plugin Upgrade Safety Review

You are performing an upgrade safety review for a WooCommerce plugin that is about
to ship a new version to existing merchants. This skill is concerned exclusively
with what happens to **existing installations** during and after the upgrade -- not
with the quality of the new code itself (that is covered by code review skills).

## Foundation References

Read these before starting -- they define the patterns you are auditing against:

- **`references/woocommerce-apis.md`** -- HPOS, CRUD, data stores, Payment Token API,
  feature compatibility declarations
- **`references/security.md`** -- Database patterns, Options API, prepared statements
- **`references/plugin-architecture.md`** -- Plugin lifecycle hooks, activation/deactivation

## When to Use

- Before any **minor version** (1.x -> 1.y) or **major version** (1.x -> 2.0) release
- When a release includes **database schema changes**, **settings restructuring**,
  **new feature declarations** (HPOS, blocks), or **deprecated hooks/filters**
- When a release **changes the payment flow** (new tokenization method, new API
  version, hosted fields migration)
- Skip for **patch releases** (1.0.x -> 1.0.y) that contain only bug fixes with no
  structural changes

## How to Detect When This Skill Is Needed

Scan the diff between the old and new version for these high-risk patterns:

| Pattern | Why It's Risky |
|---|---|
| Changes to `*-install.php`, `*-activator.php`, `*Install*` classes | Database migration code changed |
| New/modified `dbDelta()` calls or `$wpdb->query("ALTER TABLE")` | Schema migration |
| Changes to `WC_Payment_Token*` classes or `wc_payment_token` meta | Payment token schema |
| Removed `add_action`/`add_filter` calls | Hook removal |
| Changes to `process_payment()`, `process_refund()` | Core payment flow |
| New/changed `delete_option()` calls | Settings migration |
| Changed `Requires at least`, `WC requires at least`, `Requires PHP` headers | Minimum version bump |

If any of these patterns appear, run this skill.

---

## Step 0: Establish Upgrade Context

1. Identify the **current released version** (what merchants have today)
2. Identify the **target version** (what is about to ship)
3. Produce a diff summary:
   - Files added, modified, deleted
   - Database schema changes (new tables, altered columns, new meta keys)
   - Settings fields added, removed, or renamed
   - Hooks/filters added, removed, or signature-changed
   - Payment Token schema changes
   - Minimum version requirements changed (PHP, WP, WC)

If both versions are in git:
```bash
git diff v<old>..v<new> --stat
git diff v<old>..v<new> -- src/Data/ includes/class-*-install.php
```

---

## Step 1: Database Migration Safety

### 1.1 Schema Migrations

- [ ] All schema changes use `dbDelta()` or equivalent safe migration pattern
- [ ] Migrations are **idempotent** -- running the upgrade routine twice produces the
      same result (merchants may trigger activation multiple times)
- [ ] Column type changes are backwards-compatible (e.g., widening a VARCHAR, not
      narrowing it)
- [ ] New required columns have sensible defaults so existing rows are valid
- [ ] No `DROP TABLE` or `DROP COLUMN` without a preceding version that stopped
      writing to that table/column (two-release deprecation pattern)
- [ ] Migration runs on `admin_init` or `plugins_loaded` with a version check gate,
      NOT on every page load
- [ ] Schema version is stored in `wp_options` and checked before running migrations

**Severity:**

| Issue | Level |
|-------|-------|
| Data loss (DROP without migration) | Critical |
| Non-idempotent migration | High |
| Missing version gate (runs on every load) | High |
| No schema version tracking | Medium |

### 1.2 Data Migrations

- [ ] Existing order meta is preserved or migrated to new keys (not silently orphaned)
- [ ] If meta keys are renamed: old keys are read as fallback during a transition
      period, not immediately deleted
- [ ] If data format changes (e.g., serialized -> JSON, or flat -> structured):
      migration converts existing records, does not assume new format
- [ ] Migration handles large datasets without hitting PHP memory/timeout limits
      (batch processing with `LIMIT` + offset, or Action Scheduler)
- [ ] HPOS compatibility: if migrating order meta, works with both `wp_postmeta` and
      `wc_orders_meta` tables (use `$order->get_meta()` / `$order->update_meta_data()`,
      never raw SQL against a specific table)

### 1.3 Options / Settings Migrations

- [ ] If settings keys are renamed or restructured: old settings are read and migrated
      on upgrade, not lost
- [ ] If settings are moved between storage backends (options -> custom table, or
      vice versa): migration runs before any code reads from the new location
- [ ] Autoloaded option size is checked -- migrations should not create large
      autoloaded options (>100KB triggers performance degradation)
- [ ] Default values for new settings are set during migration, not left to
      `get_option()` fallback (avoids race conditions where code reads before
      migration runs)

---

## Step 2: Payment Continuity

This section applies only to payment gateway plugins. Skip for non-payment plugins.

### 2.1 Saved Payment Tokens

- [ ] Existing saved payment tokens (`WC_Payment_Token_CC`, custom token types)
      remain valid and usable after upgrade
- [ ] If the token storage schema changes: migration converts existing tokens
- [ ] If switching from custom token storage to the WC Payment Token API (or vice
      versa): migration preserves all existing tokens
- [ ] If switching payment processor API versions: existing tokens are compatible or
      migrated (e.g., Stripe Sources -> PaymentMethods migration)
- [ ] Merchants' customers can check out using saved cards immediately after upgrade
      without re-entering payment details

**Severity:** Any token loss or breakage is **Critical** -- merchants' customers lose
saved payment methods, increasing checkout friction and abandoned carts.

### 2.2 Active Subscriptions

- [ ] If the plugin supports WooCommerce Subscriptions: active subscription renewal
      payments will continue to process correctly after upgrade
- [ ] If the API integration changes: existing subscription payment profiles /
      mandates are compatible with the new flow
- [ ] Renewal hooks (`scheduled_subscription_payment_{gateway_id}`) are still
      registered with the same callback signature

### 2.3 Pending Transactions

- [ ] Orders in `pending` or `on-hold` status with this payment method can still be
      completed after upgrade
- [ ] Webhook/IPN handlers still accept callbacks for transactions initiated before
      the upgrade (old API format, old webhook signature scheme)
- [ ] If the webhook endpoint URL changes: old URL still routes to a handler (or
      returns a meaningful error, not a 404)

---

## Step 3: Hook and Filter Compatibility

### 3.1 Removed or Renamed Hooks

- [ ] List all hooks/filters present in the current version but absent in the target
- [ ] For each removed hook: is there a replacement? Is the old hook deprecated with
      a notice before removal? (Should follow two-release deprecation: deprecate in
      release N, remove in release N+2)
- [ ] `_deprecated_hook()` or `_deprecated_function()` called for any removed or
      renamed hooks/functions
- [ ] Third-party plugins or themes hooking into removed hooks will not fatal error

### 3.2 Changed Signatures

- [ ] List all hooks/filters where the number or type of parameters changed
- [ ] Changed signatures documented in the changelog
- [ ] If a filter return type changed: existing filter callbacks returning the old
      type will not cause a fatal error or data corruption

### 3.3 New Feature Declarations

- [ ] If the plugin newly declares HPOS compatibility: verified that the upgrade path
      from non-HPOS-aware to HPOS-aware does not break existing order access
- [ ] If the plugin newly declares block checkout compatibility: existing classic
      checkout integrations still work (do not remove classic support when adding
      blocks support)
- [ ] New `FeaturesUtil::declare_compatibility()` calls are accurate (the plugin
      actually works with the feature, not just declaring it)

---

## Step 4: Rollback Safety

### 4.1 Downgrade Resilience

- [ ] If a merchant downgrades to the previous version after upgrading: the plugin
      does not fatal error
- [ ] Database schema changes are forward-compatible: columns added by v2 do not
      break v1's queries (v1 ignores unknown columns)
- [ ] Settings added by v2 do not break v1's `get_option()` calls (v1 ignores
      unknown settings)
- [ ] If the migration is destructive (cannot be reversed): this is documented in the
      changelog and release notes with a "backup before upgrading" warning

### 4.2 WordPress Auto-Update Safety

- [ ] The plugin does not break WordPress auto-update compatibility
- [ ] If the upgrade requires manual steps (e.g., re-entering API credentials):
      an admin notice clearly communicates this after auto-update
- [ ] Post-upgrade tasks that require admin attention are surfaced via
      `WC_Admin_Notices` or WordPress admin notices (not just changelog text)

---

## Step 5: Changelog and Merchant Communication

### 5.1 Changelog Quality

- [ ] Changelog entry exists for this release
- [ ] Format follows "Keep a Changelog" or WordPress conventions
- [ ] Breaking changes are called out explicitly (not buried in a list)
- [ ] Migration steps (if any) are documented with clear instructions
- [ ] Deprecated features are listed with their replacement

### 5.2 Upgrade Notice

- [ ] `readme.txt` includes an `== Upgrade Notice ==` section for this version
- [ ] If the upgrade requires action: the notice says so clearly
- [ ] If the upgrade has breaking changes: severity is communicated ("backup your
      site before upgrading")

### 5.3 Version Metadata

- [ ] Plugin header `Version:` matches the release tag
- [ ] `WC tested up to` is updated to the latest WooCommerce release
- [ ] `Requires at least` is updated if minimum requirements changed
- [ ] `Requires PHP` is updated if minimum PHP version changed
- [ ] If minimum requirements increased: changelog documents this and the upgrade
      notice warns merchants on older versions

---

## Step 6: Synthesize Upgrade Safety Report

### Deliverable: `upgrade-safety-report.md`

```markdown
# Upgrade Safety Report
## Plugin: [name] v[current] -> v[target]
## Date: [date]

### Upgrade Risk Level: [LOW / MEDIUM / HIGH / CRITICAL]

| Risk Level | Definition |
|------------|------------|
| LOW | No schema changes, no breaking changes, patch-level fixes |
| MEDIUM | New settings or meta keys, new feature declarations, minor hook changes |
| HIGH | Database schema changes, payment flow changes, deprecated hooks |
| CRITICAL | Data migration required, payment token schema change, minimum version bump |

Note: Major version bumps (X.0.0) start at HIGH minimum regardless of content.

### Database Migrations
| Migration | Idempotent | Batched | Reversible | Status |
|-----------|-----------|---------|------------|--------|
| [description] | Yes/No | Yes/No | Yes/No | PASS/FAIL |

### Payment Continuity
| Check | Status | Notes |
|-------|--------|-------|
| Saved tokens preserved | PASS/FAIL/N/A | [details] |
| Active subscriptions safe | PASS/FAIL/N/A | [details] |
| Pending transactions safe | PASS/FAIL/N/A | [details] |
| Webhook backward compat | PASS/FAIL/N/A | [details] |

### Hook Compatibility
| Hook/Filter | Change | Deprecated? | Replacement | Status |
|-------------|--------|-------------|-------------|--------|
| [hook name] | Removed/Renamed/Signature | Yes/No | [replacement] | PASS/FAIL |

### Rollback Assessment
- Downgrade safe: [Yes / No / Partial]
- Auto-update safe: [Yes / No -- requires manual steps]
- Manual steps required: [list, or "None"]

### Changelog Review
- Breaking changes documented: [Yes / No / N/A]
- Upgrade notice present: [Yes / No]
- Version metadata current: [Yes / No]

### Prioritized Upgrade Issues

## Critical
### UPG-001: [Brief description]
- **Category:** [Database / Payment / Hooks / Rollback / Changelog]
- **File:** [path]
- **Lines:** [N-M]
- **Issue:** [What is wrong]
- **Merchant Impact:** [What breaks for existing merchants]
- **Fix:** [What to change, with before/after code]
- **Status:** [ ] Not started

## High
[...]

## Medium
[...]
```

---

## Step 7: Save and Present

1. Save the report
2. Present a one-paragraph risk summary
3. If Critical or High issues exist: recommend blocking the release until resolved
4. If the upgrade risk level is HIGH or CRITICAL: recommend the partner include a
   "backup before upgrading" notice in the release

## Important Notes

- This skill does NOT evaluate code quality, security, or UX -- those are handled by
  other review skills
- Focus exclusively on the **delta between versions**, not absolute quality
- Payment token preservation is the highest-stakes item -- verify thoroughly
- Database migrations that work on 10 test orders may fail on 10,000 production
  orders due to memory/timeout -- always check for batching
- WordPress auto-updates mean merchants may upgrade without reading the changelog --
  surface breaking changes via admin notices, not just documentation
