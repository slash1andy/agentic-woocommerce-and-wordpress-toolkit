# Maintenance and evaluation standards

These standards are portable lessons from maintaining this toolkit. They apply to any harness. They
describe how to change and evaluate the packaged skills; they are not an executed process, and a
candidate stays unevaluated until real runs exist (see [evaluation status](evaluation-status.md)).

## Bind evidence to an exact candidate

- Record the exact candidate as a digest of its bytes (for example the SHA-256 of an immutable diff or
  archive) and attach every result to that digest. If the bytes change, earlier results describe a
  different candidate and must be rerun or labeled historical.
- Record the resolved model, harness, and version for each run, not just a family name.
- Preserve historical results unchanged. Do not merge packets from different candidates into one benchmark.

## Compare like with like

- Run paired with-skill and without-skill arms in the same runtime: same model, harness, tools, effort,
  fixtures, and context. A comparison across different runtimes is a runtime-bundle comparison, not a model benchmark.
- Isolate the no-skill arm: it must not see the skill, its references, the grader oracle, or the
  expectations. Give it only the user prompt and fixtures.
- Start with one paired smoke run per scenario, and repeat unstable or critical cases before claiming reliability.

## Test the full turn shape

- For write-gated work, record the approval turn and then the actual resumed turn, and keep the generated
  artifact. A reply that says tests passed is not proof; run the retained artifact.
- Read-only questions and audits need no approval turn. Do not require unapproved implementation from them.
- Test denial: with write tools present, a refused action must have zero effect and must not be retried
  through another tool.

## Grade with oracles

- Give each planted-defect scenario an explicit expected-defect list and a clean control. Score recall,
  false positives, and incorrect verified claims separately from presentation and scope compliance.
- Keep the oracle on the grader side only.
- A control states its boundary. A single-process fixture does not prove distributed replay safety;
  anything outside the boundary stays unverified.
- Structural checks, such as wording and file-shape tests, show that guidance exists. They are not behavior proof.

## Evaluation packet helper

`scripts/evaluate.py` is a stdlib-only packet preparer and collector. It never launches a model or CLI,
retrieves authentication, selects a fallback or alias, or grades. A controller runs the exact pinned
harness directly, an independent judge grades, and the helper only snapshots, validates, and aggregates.
The pipeline is prepare, controller initial turn, controller approved resume where required, judge, collect.

Commands: `python3 -B scripts/evaluate.py prepare CANDIDATE OUT --settings JSON` and
`python3 -B scripts/evaluate.py collect OUT RECORDS --manifest-sha256 PIN [--grades GRADES]`.

**Trust boundary.** Prepare prints `manifest_sha256`. The controller retains that value outside `OUT`
and the records, and passes it to collect (`manifest_sha256=` in the API). Collect refuses to trust or
write anything unless `manifest.json` matches the supplied pin; it never derives the pin from the file
or from a sidecar in the packet. The pin binds settings, prompts, scenario inventory, approval policy, and
oracle hashes to the trusted preparation. It does not authenticate model records: a manually forged record
or grade still passes structural checks, so the controller audits transcripts independently. `OUT` is
assumed to be in a directory owned by the trusted controller; this is not a cross-user or cross-host sandbox.

**Prepare.**
- `OUT` must not exist, must not contain `..`, and must be outside the candidate. Symlinks anywhere in the
  candidate or fixtures are refused. Prepare writes only into `OUT`; it never reuses or overwrites a packet.
- `--settings` is a JSON object that must pin `model`, `harness`, `effort`, `budget`, and `tools`. Pin a
  resolved model and harness version, not a movable alias; the helper records the object and cannot check
  this. The same object is copied to both arms.
- `OUT/candidate` is the full candidate minus only `.git`, `__pycache__`, `.pyc`, and `.DS_Store`.
  `manifest.json` holds the ordered path and sha256 inventory, `candidate_digest`, `projection_digest`,
  `settings`, and the scenarios.
- `OUT/projection` is the treatment plugin tree: `.claude-plugin/plugin.json` plus each skill's
  `SKILL.md`, `references/`, and `agents/openai.yaml`. It contains no evals, tests, docs, or oracles.
- Scenario ids are `dev-N`, `upgrade-N`, and `finalize-N` (15 in total, each with a `treatment` and a
  `control` arm). A scenario is multi-turn when its expected output says it proceeds after approval
  (`dev-2`, `dev-3`).
- `OUT/workspaces/ID/ARM` holds only the fixtures, copied byte for byte under their original basenames.
  The prompt names those basenames. The treatment prompt starts with `/claude-woocommerce-toolkit:SKILL`;
  the control prompt is the same text without it. Each packet workspace starts as the pristine fixtures.
  The controller runs an arm in it, or in a fresh copy, and records the final inventory; collect treats the
  live workspace as a result that must match the recorded `workspace_final`. Altering the candidate,
  projection, oracles, or declared fixtures invalidates the packet.
- `OUT/oracles/ID.json` holds `expectations` for the judge only. Never expose `OUT/oracles`,
  `OUT/candidate`, or `manifest.json` to either arm.

**Records.** For each scenario and arm the controller writes `RECORDS/ID/ARM.json` containing the raw
CLI result object as `initial` and, for multi-turn scenarios after approval, `resumed`, plus:
- `workspace_after_initial` and `workspace_final`: maps of relative path to sha256 for the run copy,
  taken by the controller before approval and at the end.
- `approval` (multi-turn only): `{"approved": true, "session_id": ...}`, where `session_id` equals the
  initial turn's. Retain the approval text beside the record.
- Each turn needs a non-empty `session_id`, `is_error` false, `terminal_reason` `completed`, empty
  `permission_denials`, a non-empty `modelUsage` (containing `settings.model` when pinned), and a string
  `result`. Normalize other harness values before recording; anything else fails closed.
- Each `modelUsage` entry must show real inference: any of `inputTokens`, `outputTokens`,
  `cacheReadInputTokens`, `cacheCreationInputTokens` that are present must be nonnegative integers (not
  booleans), `outputTokens` must be positive, and at least one of input, cache-read, or cache-creation
  tokens must be positive. Empty, zero, or cost-only usage fails.

**Collect.** It first checks the manifest pin, then re-hashes the candidate, projection, oracles, and declared fixtures and raises on
any difference, and it refuses unexpected record or grade files. Live workspaces are mutable results: with
a record, the live workspace must equal the recorded `workspace_final`; with no record, it must equal the
original fixtures. Any difference raises. Only an approved resumed turn may change the workspace, and
`modelUsage` must contain exactly the pinned model. Per-row `status`: `complete`,
`incomplete` (no record, or a required approval or resumed turn is missing), or `failed` (invalid turn,
error, denial, wrong session, or any workspace change before approval or outside an approved resumed turn).
Generated files, meaning recorded final files that differ from the fixtures, are listed under `generated` for
every row with a valid recorded inventory, including `failed` rows. `coverage` and `complete` describe status only and never imply
a pass. Rows carry the sha256 of the record and grade files so results cannot silently diverge from the
retained raw files. `OUT/results.json` is replaced atomically on every collect through a sibling temporary
file; an existing `results.json` symlink is refused. Keep raw records outside the repository.

**Grades.** The judge, in a fresh session separate from the run, writes `GRADES/ID/ARM.json` with
`candidate_digest`, `scenario`, `arm`, `record_sha256` (the sha256 of that row's record file),
`expectations_total` (the full oracle count), `expectations_passed`, `route` (boolean),
`judge_session_id`, and optional non-negative `recall` and `false_positives`. The judge session must
differ from every initial and resumed session in all records, not only the graded row; a session ID is not
proof of authorship, so audit transcripts independently. A grade with a wrong or missing row binding
raises. A malformed, unbound, or partial grade raises. Without a grade, `acceptance` is `unresolved`, and a row
whose status is `incomplete` stays `unresolved` even with a grade. A valid grade on a `failed` row is
`rejected`, whatever its scores. On a `complete` row a valid grade is `accepted` only with a true route, all
expectations passed, and no false positives; otherwise `rejected`. The helper never creates a grade.

**Exit codes.** `0` means every row is complete, `2` means incomplete or failed rows remain, and `1` means
invalid input or a tampered packet. Exit `0` is not acceptance; read `acceptance`.

**Harness lessons.** A scenario's `multi_turn` setting alone defines its allowed approval resumes; a
planning-only scenario gets no extra approval phase. Metadata approval must resolve missing values
explicitly rather than force guesses. Native runtime fixtures derive settings, routes, meta, and schema
from the generated contract, use distinguishing inputs and short database prefixes, and run separate fresh
legacy and HPOS installs; never bypass core synchronization. Do not loosen graders or oracles to fit a
result. Existing structural tests plus preserved failing native criterion judgments are the red evidence
for a guidance fix; rerun all scenarios against the final candidate bytes.

## Qualify every claim

- Make evidence-qualified claims: state what was run, on which candidate, and what was not run. Mark
  missing or stale evidence unverified.
- Separate released, experimental, planned, and withdrawn platform changes, and cite the official source,
  version, and date beside each substantive update. Do not raise a platform floor for everyone because one
  release changed a surface; scope each note to the affected version and surface.
- When a platform note gives a source link, prefer the official page over a summary.

## Publish only with approval

- Do not publish anything without approval: no push, pull request, tag, release, marketplace
  submission, repository-setting change, or security-channel change. Local implementation and evaluation
  are separate from publication, and an approval covers only its stated scope.
- Recheck the immutable candidate after approval and before acting.

## Keep changes native and minimal

- Prefer the host's native controls, the repository's existing tooling, and the smallest change that
  meets the need. Do not add a framework, agent role, or orchestration layer without a measured gap.
- Have an independent review of the frozen candidate by a reviewer who did not author it, and rerun
  affected cases after each edit.

## Promote local learnings with care

- Promote a learning into this repository only when it is reusable, verified, and phrased
  without names, providers, preferences, or local setup. Promote it by editing the relevant canonical
  document, test, or scenario in a reviewed change.
- Do not include secrets, private paths, customer data, or licensed material in a promoted learning,
  fixture, or log.
- There is no automatic sharing. This document is not a memory system and has no authority over any
  user's or host's own memory or preferences; maintainers decide what is promoted.

## Reuse the official WordPress skill library

For generic WordPress core, REST, block, theme, performance, and Abilities guidance, link to the
[official WordPress agent-skills library](https://github.com/WordPress/agent-skills) rather than copying it.
Check its current license before reusing any of its text; when it differs from this repository's
GPL-2.0-or-later, link instead of copying. Keep this toolkit focused on WooCommerce integration and
commerce continuity.
