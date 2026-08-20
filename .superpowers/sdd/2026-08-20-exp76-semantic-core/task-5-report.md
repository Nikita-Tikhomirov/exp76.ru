# Task 5 Report: Intent Classification and Frozen-Collision Protection

## Status

`DONE`. Task 5 and review round 1 are implemented on `codex/semantic-core`.
The original implementation is commit `8b29151` (`feat: classify semantic search intent`);
the review fixes are in the separate `fix: refine semantic classification review`
commit reported in the handoff (a commit cannot contain its own content-derived SHA).

The implementation is limited to S1-S8 and the six immutable frozen owners. It
performs no live-site, browser, Yandex, FTP, WordPress, canonical, redirect,
robots, SERP capture, or paid-API writes. Raw source files remain unchanged.

## Files

- `tools/seo_semantics/classify.py`
- `tools/seo_semantics/cli.py`
- `tools/test_semantic_classify.py`
- `seo-data/2026-08-exp76-services/processed/keywords_clean.csv`
- `seo-data/2026-08-exp76-services/processed/frozen_collisions.csv`
- `seo-data/2026-08-exp76-services/processed/minus_words.csv`
- `.superpowers/sdd/2026-08-20-exp76-semantic-core/task-5-report.md`

## TDD and review-round evidence

The review fixes were implemented through additional RED-to-GREEN cycles:

1. Bare `работа` initially reproduced false jobs exclusions for
   K000212/K004787/K006311/K006554. It is no longer an employment marker; jobs
   require complete-token vacancy, salary, or resume evidence and their observed
   inflections.
2. Frozen morphology regressions initially failed for `дренажными`,
   `водоотводы ливневые`, `отмостке`, `ливневкой`, `ливневку`,
   `ливневых колодцев`, and `заболоченных`. Explicit complete-token/phrase forms
   now route to the immutable owner. Mixed S8/S3 examples remain
   `manual_review` with that owner URL.
3. Configuration-driven seed tests initially exposed missing exact ownership for
   `монтаж освещения участка` and `обустройство въезда на участок`. The CLI now
   loads exact normalized ownership from `seeds.json`; a test iterates every
   configured seed.
4. CLI regressions proved that clicked noise was assigned to an arbitrary S1
   fallback. The fallback was removed and persistent `review_status`,
   `final_decision`, and `review_reason` columns were added.
5. Source-hint tests initially showed unrelated and municipal queries as
   relevant. Query evidence is now required. Legal/municipal planning is
   separated from real site grading and site zoning with boundary-aware context.
6. The former S4 `корчевание` phrases now fail into explicit `out_of_scope`.
7. A final review caught automotive `автосалон` noise and generic `проектные
   работы`; both were reproduced in tests before being excluded.

Final Task 5 suite: 21 behavior tests, including real CSV CLI tests. Matching is
performed on normalized complete tokens and complete phrases, never naive
substrings. The frozen contract is documented accurately: the earliest complete
phrase owns, with declaration order used only for an equal-position tie.

## Output counts

Input: 7,818 rows. Output: 7,259 clean rows and 559 frozen rows.

| service | total | transactional | commercial_research | informational | product_only | brand_navigation | irrelevant | relevant | manual_review | frozen_collision | excluded |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | 580 | 43 | 453 | 32 | 1 | 11 | 40 | 534 | 6 | 0 | 40 |
| S2 | 347 | 149 | 152 | 17 | 29 | 0 | 0 | 342 | 5 | 0 | 0 |
| S3 | 1,540 | 15 | 1,330 | 94 | 53 | 0 | 48 | 1,490 | 2 | 0 | 48 |
| S4 | 970 | 24 | 859 | 20 | 50 | 0 | 17 | 953 | 0 | 0 | 17 |
| S5 | 2,556 | 110 | 1,839 | 86 | 13 | 0 | 508 | 2,045 | 3 | 0 | 508 |
| S6 | 79 | 21 | 45 | 9 | 2 | 0 | 2 | 77 | 0 | 0 | 2 |
| S7 | 231 | 8 | 189 | 16 | 6 | 0 | 12 | 218 | 1 | 0 | 12 |
| S8 | 457 | 58 | 320 | 57 | 18 | 0 | 4 | 445 | 8 | 0 | 4 |
| Unassigned | 1,058 | 147 | 357 | 29 | 1 | 0 | 524 | 0 | 0 | 534 | 524 |

Global intent totals: `transactional=575`, `commercial_research=5,544`,
`informational=360`, `product_only=173`, `brand_navigation=11`, and
`irrelevant=1,155`.

Global relevance totals: `relevant=6,104`, `manual_review=25`,
`frozen_collision=534`, and `excluded=1,155`. Exclusion reasons are
`out_of_scope=786`, `legal_municipal_planning=365`, `training=3`, and `jobs=1`.
Every excluded row has a reason.

Frozen-owner totals are drainage 157, blind area 79, paving 260, dewatering 10,
storm sewer 36, and irrigation 17.

## S5 sense audit and disputed legacy exclusions

Source seed/current-URL hints are retained as provenance but cannot alone make a
query relevant. The final S5 audit contains 2,045 relevant rows, 365 explicit
`legal_municipal_planning` exclusions, and 143 other `out_of_scope` exclusions.
The legal rule requires planning plus legal/municipal markers, project plus
territory, or zoning plus municipal/territory context. Genuine examples such as
`планировка участка с уклоном`, `аренда трактора для планировки участка`, and
`планировка участка зонирование` remain relevant.

All 30 observed `корч*` rows are `out_of_scope`. This includes all 14 rows in the
review cohort (K000700 and K001895-K001907); none remains in S4 or enters the
SERP queue.

## Mandatory review and persistent audit evidence

The post-fix reviewed set was selected from the final outputs with:

```text
clicks > 0 OR relevance == manual_review OR frozen_collision == true
```

Rows were sorted by `keyword_id` and inspected with ID, clicks, query, service,
relevance, owner URL, and final decision. Every selected row has persistent
`review_status=reviewed` and a non-empty `final_decision`.

- clicked rows: 157/157 reviewed (72 clean, 85 frozen);
- clicked final decisions: 52 `keep_for_clustering`, 20 `exclude`, and 85
  `frozen_owner` (one is also mixed/manual);
- mixed `manual_review`: 25/25 reviewed and resolved to an immutable owner;
- all frozen rows: 559/559 reviewed and resolved to an immutable owner;
- unique review union: 631/631; missing decisions: 0;
- union decisions: `frozen_owner=559`, `keep_for_clustering=52`, `exclude=20`;
- canonical review digest over sorted
  `keyword_id|service_id|intent|relevance|exclusion_reason|owner_url|review_status|final_decision|review_reason`:
  `8bbc030ade691a02e7ba4113a41a79326665b31dd70c76de8c64c0fbf1f12c79`.

Blank service/owner is a valid reviewed exclusion, not an unassigned decision:
20 clicked rows use it and all 20 have `final_decision=exclude`. Named reviewer
examples K000879 (freight plus irrigation), K003387 (industrial cooling-tower
drainage), and K007645 (property price) are among them. No clicked query lacks a
final decision and no synthetic S1 owner remains.

Representative mixed decisions retain both service and owner: K000212 is S1 plus
paving, K005381 is S3 plus dewatering, and K005651 is S8 plus storm sewer.

## Exact partition and source preservation

- input rows: 7,818;
- output rows: 7,818;
- unique output IDs: 7,818;
- missing, extra, or duplicate IDs: 0;
- all 16 input columns compared by `keyword_id`: 0 value mismatches;
- sorted input ID SHA-256:
  `dfbc1a8b57292f559c41d04e16e8bd32880b062ac3985560985078367e49af54`;
- sorted output ID SHA-256: the same value;
- immutable raw CSV SHA-256:
  `ba83971bb51ed220eb8743d363f4334806dde1b875030712cbb039b15587267e`.

Thus every input row is present exactly once in clean or frozen. Original raw
fields, including `seed`, `ctr`, `collected_at`, metrics, and `current_url`, are
preserved byte-for-value in the derivative row.

## Minus-word evidence

The only accepted minus word is global `обучение`, reason `training`, supported
by repeated unambiguous evidence K002321 and K002322. Status is
`accepted_repeated_evidence`.

`работа` was removed: the corpus contains service-price uses and only one clear
vacancy row (K005111), which is correctly excluded as `jobs` but is insufficient
for a repeated-evidence minus. No ambiguous single occurrence becomes a minus.

## Exact SERP/API gate

The gate is calculated after cleaning/routing. Eligible rows are clean
`relevance=relevant` with intent in `transactional`, `commercial_research`,
`informational`, or `product_only`; frozen, manual, excluded, and brand rows are
not candidates.

- eligible clean rows: 6,093;
- distinct `(service_id, query_normalized, intent)` candidates: 4,242;
- decision: `4,242 > 250`; the paid/API gate is crossed.

No paid API was activated and no SERP capture was performed.

## Verification, hashes, and commit

Fresh final verification:

- `python -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest tools.test_semantic_classify -v`: 40 tests, 0 failures;
- deterministic second regeneration: identical output hashes;
- `C:\Users\user\.codex\scripts\harness.cmd smoke`: exit 0, `CLOUD_ONLY`, no Ollama invocation;
- `git diff --check`: exit 0;
- strict UTF-8 decode, mojibake/trailing-whitespace scan, secret-pattern scan, raw immutability audit: clean.

Final derivative hashes:

- `keywords_clean.csv`: `87cc7c6ed58da9c7367453ae08bda6b4a86531218dedf7f5a1a8ad31bf7befc2`;
- `frozen_collisions.csv`: `46140e1ba5e1a984d8ace16c6d63b0e83e5514d4ffa298a13f09106327c29b40`;
- `minus_words.csv`: `0fc1e87e678022be4c3f547f70cb793396c6e6fb0b9b4638e14247f5b7f52268`.

## Concerns

- The exact cleaned candidate count is well above 250. Task 6 must stop before
  paid/API activation unless a separate user decision authorizes it or an
  approved representative queue is defined.
- The deterministic rules are deliberately conservative. `manual_review` rows
  are resolved for frozen ownership but remain labeled for downstream human
  awareness; no live destination or existing URL was changed.
