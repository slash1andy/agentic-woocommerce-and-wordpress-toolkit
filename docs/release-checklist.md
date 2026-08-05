# Local release checklist

Run this checklist from the reviewed candidate tree. It is local-only and does not depend on hosted workflows.

## Freeze and validate

- [ ] Freeze the intended candidate as an immutable diff and record its SHA-256; restart review if the bytes change.
- [ ] Run every local gate:

```bash
set -eu
python3 -B scripts/validate.py
python3 -B scripts/validate.py --check-urls
python3 -B -m unittest discover -s tests -p 'test_*.py'
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
status="$(git status --porcelain=v1)"
test -z "$status"
reviewed_base="$(git rev-parse "${REVIEWED_BASE:?Set REVIEWED_BASE to the approved base commit}^{commit}")"
candidate="$(git rev-parse 'HEAD^{commit}')"
git diff --check "$reviewed_base" "$candidate"
release_diff="$(mktemp "${TMPDIR:-/tmp}/claude-woocommerce-toolkit.release.XXXXXX")"
trap 'rm -f -- "$release_diff"' EXIT
git diff --binary "$reviewed_base" "$candidate" > "$release_diff"
release_diff_sha256="$(shasum -a 256 "$release_diff" | cut -d' ' -f1)"
test "$release_diff_sha256" = "${REVIEWED_DIFF_SHA256:?Set REVIEWED_DIFF_SHA256 to the approved diff digest}"
claude plugin tag --dry-run
```

- [ ] Prove a copied-cache installation from the complete reviewed artifact, not a symlink or live checkout. Confirm the installed cache contains both manifests, all three skills, every skill/reference route, the agent, and `scripts/validate.py`, with no `.git` directory.

## Rehearse risk

- [ ] On disposable staging, perform a risk-appropriate upgrade rehearsal from the prior supported version when the delta affects persisted data, hooks, dependencies, compatibility declarations, payments, or recovery.
- [ ] Prove backup restore and perform runtime readback of affected state.
- [ ] Perform risk-appropriate failure injection for interruption, retry, replay, and rollback conditions; retain evidence of recovery and convergence.
- [ ] Use fake or sandbox providers for all payment, webhook, refund, renewal, and ambiguous-outcome checks. Never use live payments or customer data.

## Evaluation and approval

- [ ] Run every manual scenario in fresh with-skill and without-skill sessions, retain actual outputs and failures, and keep deterministic contract results separate from response-quality claims.
- [ ] Protect `main` and the `claude-woocommerce-toolkit--v*` release-tag pattern from force updates before publishing the first release.
- [ ] Obtain explicit approval before changing repository settings, creating or pushing a tag, publishing a release, or submitting to a marketplace. Recheck the immutable diff after approval and before any approved action.
