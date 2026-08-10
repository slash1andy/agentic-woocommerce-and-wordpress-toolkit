# Evaluation status

## Version 1.1.0 response evaluation

Iteration 4 completed one with-skill and one without-skill Claude response run for each of the 12
manual scenarios (24 response runs total) with zero response failures. Eight cases received a Claude
judge grade in that iteration. Four `woocommerce-upgrade-safety` judge calls hit the Claude Pro session
limit; their saved with-skill responses were independently re-graded as reused iteration-4 evidence and
all expectations passed.

One remaining iteration-4 failure in `woocommerce-plugin-dev` case 3 omitted a REST response schema.
After the narrow REST-rule fix, the final candidate received a fresh focused recertification of that
case: 2/2 response arms completed, one judge completed, and the with-skill response passed all 8/8
case expectations.

The published evidence asset is
`agentic-woocommerce-toolkit-1.1.0-evaluation-results.json` with SHA-256
`fa84d988150c87e7cdd524eddbf41a157e939345fa733ce597cbcf5b74e572e8`.
It contains sanitized prompts, responses, completed grades, reused upgrade-safety re-grades, and the
focused REST recertification.

Methodology and limits: one run per arm is not a variance benchmark. The full final candidate was not
freshly rerun after the one-line REST-rule fix; iteration 4 plus the focused final-candidate
recertification are the release evidence. Deterministic schema and repository tests remain separate
from response-level evaluation.
