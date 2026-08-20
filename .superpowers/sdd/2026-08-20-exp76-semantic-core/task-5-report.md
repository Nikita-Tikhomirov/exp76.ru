# Task 5 Report: Intent Classification and Frozen-Collision Protection

## Status

Implemented and verified in `codex/semantic-core`. The containing commit is identified by the message `feat: classify semantic search intent`; its exact SHA is reported by the Task 5 handoff because a commit cannot embed its own content-derived SHA.

The implementation is limited to S1–S8 and the six immutable frozen owners. It performs no live-site, browser, Yandex, FTP, WordPress, canonical, redirect, robots, or paid-API writes. Raw source files remain unchanged.

## Files

- `tools/seo_semantics/classify.py`
- `tools/seo_semantics/cli.py`
- `tools/test_semantic_classify.py`
- `seo-data/2026-08-exp76-services/processed/keywords_clean.csv`
- `seo-data/2026-08-exp76-services/processed/frozen_collisions.csv`
- `seo-data/2026-08-exp76-services/processed/minus_words.csv`
- `.superpowers/sdd/2026-08-20-exp76-semantic-core/task-5-report.md`

## TDD evidence

1. The initial classification test was written first and failed with the expected `ModuleNotFoundError: tools.seo_semantics.classify`.
2. The first GREEN implemented the public dataclass/function, boundary-aware token/phrase matching, explicit priority, CLI partition, and repeated-evidence minus rules.
3. Four further RED-to-GREEN cycles reproduced issues found during the mandatory review:
   - Russian inflections and exact reviewed service phrases;
   - first-mentioned frozen owner with an explicit tie priority;
   - contextual outdoor paving without matching indoor tile queries;
   - reviewed brand/garden phrases;
   - frozen-owner queries incorrectly defaulting to `irrelevant`.
4. Final Task 5 suite: 15 behavior tests. Tests use real CSV files in temporary directories and assert observable outputs, not mocks.

The classifier normalizes with the existing Task 2 interface, splits into tokens, and matches complete token sequences. It does not classify with naive substring checks. Frozen multi-owner routing chooses the earliest complete matching phrase; the declared frozen-owner order breaks equal-position ties. Jobs and training exclusions have higher priority. Mixed S1–S8 plus frozen phrases retain the S1–S8 service, `frozen_collision=true`, `relevance=manual_review`, and the immutable owner URL.

## Output counts

Input: 7,818 rows. Output: 7,263 clean rows and 555 frozen-collision rows.

| service | total | transactional | commercial_research | informational | product_only | brand_navigation | irrelevant | relevant | manual_review | frozen_collision | excluded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 633 | 43 | 529 | 35 | 1 | 11 | 14 | 614 | 5 | 0 | 14 |
| S2 | 339 | 149 | 144 | 17 | 29 | 0 | 0 | 335 | 4 | 0 | 0 |
| S3 | 1,496 | 14 | 1,330 | 96 | 53 | 0 | 3 | 1,492 | 1 | 0 | 3 |
| S4 | 982 | 27 | 881 | 20 | 50 | 0 | 4 | 978 | 0 | 0 | 4 |
| S5 | 2,550 | 111 | 2,337 | 88 | 13 | 0 | 1 | 2,546 | 3 | 0 | 1 |
| S6 | 78 | 21 | 46 | 9 | 2 | 0 | 0 | 78 | 0 | 0 | 0 |
| S7 | 227 | 4 | 198 | 19 | 6 | 0 | 0 | 226 | 1 | 0 | 0 |
| S8 | 437 | 51 | 311 | 57 | 18 | 0 | 0 | 430 | 7 | 0 | 0 |
| Unassigned non-clicked exclusions or frozen owner | 1,076 | 148 | 357 | 28 | 1 | 0 | 542 | 0 | 0 | 534 | 542 |

Global intent totals: `transactional=568`, `commercial_research=6,133`, `informational=369`, `product_only=173`, `brand_navigation=11`, `irrelevant=564`.

Global relevance totals: `relevant=6,699`, `manual_review=21`, `frozen_collision=534`, `excluded=564`. Exclusion reasons are `out_of_scope=550`, `jobs=11`, and `training=3`; every excluded row has a reason.

Frozen-owner routing:

- drainage: 156;
- blind area: 78;
- paving: 258;
- dewatering: 10;
- storm sewer: 34;
- irrigation: 19.

## Mandatory review and audit evidence

The reviewed set was selected from the final two output files with this union predicate:

```text
clicks > 0 OR relevance == manual_review OR frozen_collision == true
```

The rows were sorted by `keyword_id` and inspected in batches showing ID, S1–S8 assignment, relevance, owner, clicks, and normalized query. Every classification issue found during inspection was converted into a failing regression test before the matcher changed, after which the files were regenerated and the selection re-audited.

- clicked rows reviewed: 157/157;
- clicked clean: 68;
- clicked frozen: 89;
- clicked without either `service_id` or `owner_url`: 0;
- mixed `manual_review` rows reviewed and routed: 21/21;
- frozen rows reviewed and routed: 555/555;
- union reviewed: 623 unique rows;
- overlap `clicked AND manual_review`: 1 (`K007571`);
- canonical audit digest (`keyword_id|service_id|intent|relevance|exclusion_reason|owner_url`, sorted): `9222d43871b735523288a9a2a0063bcfb3d0aab6981d50e5bbc6ddea9dca1182`.

The value `manual_review` is retained as the decision class required by the plan; these rows are resolved, not pending. Each has an S1–S8 service and an immutable frozen `owner_url`. Pure frozen rows have the final `frozen_collision` relevance and owner. Clicked clean exclusions retain both an explicit reason and an S1–S8 review assignment.

## Exact partition audit

- input rows: 7,818;
- output rows: 7,818;
- unique output IDs: 7,818;
- missing/extra IDs: 0;
- duplicate output IDs: 0;
- sorted input ID SHA-256: `dfbc1a8b57292f559c41d04e16e8bd32880b062ac3985560985078367e49af54`;
- sorted output ID SHA-256: `dfbc1a8b57292f559c41d04e16e8bd32880b062ac3985560985078367e49af54`.

Every input row is present exactly once in either `keywords_clean.csv` or `frozen_collisions.csv`. Original `query_raw`, `query_normalized`, `sources`, metrics, region/device, and current URL columns are retained in the derivative output. The raw CSV SHA-256 remained `ba83971bb51ed220eb8743d363f4334806dde1b875030712cbb039b15587267e`.

## Minus-word evidence

Only repeated, explicit exclusions were accepted:

- global `работа`, reason `jobs`, 10 source IDs: `K000212|K004787|K005981|K005982|K005983|K005984|K005985|K006306|K006311|K006554`;
- global `обучение`, reason `training`, 2 source IDs: `K002321|K002322`.

Both have status `accepted_repeated_evidence`. No word from a single ambiguous occurrence was added. No service-specific minus word had repeated evidence strong enough for acceptance.

## SERP/API gate

The gate was calculated after cleaning and frozen routing, not from the 7,818 raw rows. SERP-eligible clean rows are `relevance=relevant` with intent in `transactional`, `commercial_research`, `informational`, or `product_only`.

- eligible clean rows: 6,688;
- distinct `(service_id, query_normalized, intent)` candidates: 4,579;
- exact decision: `4,579 > 250`, so the paid API gate is crossed.

No paid API was activated and no SERP capture was performed in Task 5.

## Verification, hashes, and commit

Fresh verification on the final worktree state:

- `python -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest tools.test_semantic_classify -v`: 34 tests, 0 failures, exit 0;
- `C:\Users\user\.codex\scripts\harness.cmd smoke`: exit 0, `CLOUD_ONLY`, Ollama commands skipped;
- `git diff --check`: exit 0;
- strict UTF-8 decode: 7/7 Task 5 text/CSV files;
- trailing-whitespace scan: clean;
- secret-pattern scan: clean.

Commit branch/message: `codex/semantic-core` / `feat: classify semantic search intent`.

- `keywords_clean.csv`: `1f94bd47f9d828ed600dd83805c1e7f09e76f2a87a7a1336f75f46b5157306b2`;
- `frozen_collisions.csv`: `90d9128dacacf2ab95a5d666b7fd8cfc7de1bac614b8e17102edb815a1e14d53`;
- `minus_words.csv`: `60fb0969d4b782b6cc48823e66c234b8b4c586c148e105eea699bbb676b963b5`.

## Concerns

- The post-clean SERP candidate count remains well above 250; Task 6 must stop before any uncontrolled capture and request API activation or reduce the representative queue under its own approved rules.
- The 1,076 blank `service_id` rows are limited to non-clicked explicit exclusions (542) or pure frozen-owner rows (534). They are not S1–S8 clustering candidates; every clicked row has either an S1–S8 service or immutable owner.
