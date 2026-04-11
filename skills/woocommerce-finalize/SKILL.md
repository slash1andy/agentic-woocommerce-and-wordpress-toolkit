---
name: woocommerce-finalize
description: >
  Pre-release code health and traceability audit for WooCommerce plugins. Runs after
  code review -- focuses on dead code, duplication, structural complexity, and full-stack
  traceability analysis. Use when finalizing, auditing, or preparing a WooCommerce plugin
  for release. Also trigger when the user mentions "finalize", "pre-release audit",
  "code health check", "traceability analysis", or "ready to ship". This skill
  complements security and UX review by catching structural issues and broken data paths
  that checklist-based reviews miss.
---

# WooCommerce Plugin Finalization Review

You are performing a pre-release code health and traceability audit of a WooCommerce
plugin. This skill focuses on structural concerns that static checklists do not catch.

**This skill runs after code review.** UX compliance and security auditing are handled
by separate review checklists. Do not duplicate that work here.

## Foundation References

Read these before starting -- they define the standards you are auditing against:

- **`references/coding-standards.md`** -- WordPress PHP coding standards, naming, structure
- **`references/security.md`** -- Security baseline, database patterns
- **`references/woocommerce-apis.md`** -- HPOS, CRUD, data stores, payment gateway patterns
- **`references/ux-guidelines.md`** -- UX/copy conventions

## Overview

This skill runs two review tracks, then synthesizes findings into a machine-readable
task list.

**The two tracks:**
1. **Code Health** -- Dead code, duplication, structural complexity
2. **Traceability Analysis** -- End-to-end verification through every code layer

---

## Step 0: Locate and Inventory the Plugin

1. Find the plugin root (main PHP file with `Plugin Name:` header)
2. Build complete file inventory (PHP, JS, CSS, templates, assets, config)
3. Identify architecture (classic PHP+jQuery, React+REST, or hybrid)
4. Map WooCommerce integration points (settings API, product tabs, checkout, payment, shipping)
5. Check for custom post types, taxonomies, tables, REST endpoints, AJAX handlers

## Step 0.5: Verify Testing

**Finalization should not begin until tests pass.** If a testing report exists in the
plugin root (`testing-report.md`), verify:

1. Report is recent (within 12 hours)
2. Overall status is passing
3. PHPStan ran at level 7 or higher

If no testing report exists, recommend the user run their test suite first.

---

## Step 1: Run Review Tracks

### Track 1: Code Health

Sweep the entire codebase for structural and maintenance issues that accumulate
over time and are not caught by standards enforcement during development.

#### Dead Code

- Uncalled functions (defined but never referenced anywhere in the codebase)
- Unused imports, `use` statements, and variables
- Commented-out code blocks (more than 3 lines)
- Unreachable code after unconditional `return`, `throw`, `exit`, `die`
- Unused class methods (especially private/protected with no internal callers)

#### Duplication

- Functions or methods with >80% similar logic (candidates for extraction)
- Copy-pasted blocks across files (especially validation, sanitization, or API call patterns)
- Repeated inline SQL or query patterns that should be a shared method
- Identical or near-identical AJAX/REST handler implementations

#### Structural Complexity

- Functions longer than 50 lines (candidates for decomposition)
- Nesting deeper than 3 levels (if/foreach/try stacking)
- God classes with >10 public methods or >300 lines
- Classes with mixed responsibilities (e.g., a gateway class that also handles admin UI rendering)
- Circular dependencies between classes

For each finding: category, file/line, impact description, suggested fix.

**Severity:**

| Issue | Level |
|-------|-------|
| Unreachable code hiding a bug | High |
| God class / circular dependency | High |
| >80% duplicated logic across files | Medium |
| Functions >50 lines | Medium |
| Commented-out code blocks | Low |
| Unused private methods | Low |

### Track 2: Traceability Analysis

Trace every UI interaction through the full stack:

```
UI (HTML/JS) -> AJAX/REST Handler -> Business Logic -> Data Access -> Database
```

For each layer boundary:
- Map all connections (caller -> callee with arguments)
- Verify connections exist and signatures match
- Check parameter naming consistency between layers
- Verify data transformations are symmetric (serialize <-> deserialize)
- Confirm null/empty handling at every boundary

#### Payment Gateway Trace Paths (required for payment plugins)

These specific paths must be fully traced if the plugin is a payment gateway:

1. **Payment flow:** `checkout form (JS) -> process_payment() -> payment API call -> webhook/IPN handler -> order status update`
2. **Refund flow:** `admin refund button -> process_refund() -> refund API call -> order note + status`
3. **Settings flow:** `settings form (admin) -> process_admin_options() / save -> get_option() -> checkout form display`
4. **Token flow:** `tokenize (JS/API) -> WC_Payment_Token creation -> saved token display -> token reuse at checkout`
5. **Webhook flow:** `incoming webhook -> signature verification -> event routing -> order lookup -> status update`

For each path: document the full chain of calls, flag any broken links, missing
error handling, or data that crosses a boundary without validation.

Report: verified paths, broken paths, suspicious paths.

---

## Step 2: Synthesize Task List

### Deliverable: `finalization-tasks.md`

Machine-readable task list for agents or developers:

```markdown
# Finalization Tasks for [Plugin Name]

## Critical Priority
### TASK-OPT-001: [Brief description]
- **File:** [path]
- **Lines:** [N-M]
- **Issue:** [What's wrong]
- **Fix:** [What to do, with before/after code]
- **Status:** [ ] Not started

## High Priority
### TASK-TRC-001: [Brief description]
...
```

Task ID scheme: `TASK-OPT-###` (code health), `TASK-TRC-###` (traceability).

---

## Step 3: Save and Present

1. Save `finalization-tasks.md` to the plugin's output folder
2. Present a concise summary: count of findings per track, top 3 highest-priority items
3. Offer to start on highest-priority items

## Important Notes

- Be thorough but honest -- flag false positives as uncertain
- Give credit for things done well (clean trace paths, well-structured code)
- Context matters -- admin-only vs customer-facing code changes severity weighting
- Traceability analysis is the crown jewel -- most hidden bugs live at layer boundaries
- Do not duplicate UX or security findings -- those are covered by other review skills
