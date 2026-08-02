# Local release checklist

Run this checklist from the reviewed candidate tree. It is local-only and does not depend on hosted workflows.

## Freeze and validate

- [ ] Freeze the intended candidate as an immutable diff and record its SHA-256; restart review if the bytes change.
- [ ] Run every local gate:

```bash
python3 -B scripts/validate.py
python3 -B scripts/validate.py --check-urls
python3 -B -m unittest discover -s tests -p 'test_*.py'
claude plugin validate .claude-plugin/plugin.json --strict
claude plugin validate .claude-plugin/marketplace.json --strict
reviewed_base="$(git rev-parse "${REVIEWED_BASE:?Set REVIEWED_BASE to the approved base commit}^{commit}")"
candidate="$(git rev-parse 'HEAD^{commit}')"
git diff --check "$reviewed_base" "$candidate"
```

- [ ] Prove a copied-cache installation from the complete reviewed artifact, not a symlink or live checkout. Confirm the installed cache contains both manifests, all three skills, every skill/reference route, the agent, and `scripts/validate.py`, with no `.git` directory.

## Rehearse risk

- [ ] On disposable staging, perform a risk-appropriate upgrade rehearsal from the prior supported version when the delta affects persisted data, hooks, dependencies, compatibility declarations, payments, or recovery.
- [ ] Prove backup restore and perform runtime readback of affected state.
- [ ] Perform risk-appropriate failure injection for interruption, retry, replay, and rollback conditions; retain evidence of recovery and convergence.
- [ ] Use fake or sandbox providers for all payment, webhook, refund, renewal, and ambiguous-outcome checks. Never use live payments or customer data.

## Evaluation and approval

- [ ] Keep response-level evals blocked when `skill-creator` authentication fails; record the blocker and do not convert manual scenarios or deterministic tests into a pass.
- [ ] Obtain explicit approval before changing repository settings, creating or pushing a tag, publishing a release, or submitting to a marketplace. Recheck the immutable diff after approval and before any approved action.
