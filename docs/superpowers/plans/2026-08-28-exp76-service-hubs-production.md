# Exp76.ru Service Hubs Production Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Превратить восемь старых услуг exp76.ru в полноценные SEO-хабы с доказанными коммерческими подуслугами, отдельными информационными статьями, реальными работами и безопасным выпуском в production без перестройки шести уже готовых направлений.

**Architecture:** Восемь действующих URL S1–S8 сохраняются как публичные хабы и используют уже подготовленный новый `service-v2`-шаблон. Коммерческие интенты, которые подтверждены семантикой и выдачей, получают отдельные WordPress-записи на общем шаблоне `inc/newservicepost.php`; информационные интенты получают отдельные записи категории 72 на `inc/seoblogpost.php`; геостраницы создаются только при наличии реального объекта и локальных фактов. Единый идемпотентный импортёр создаёт или обновляет только перечисленные в manifest сущности, ничего не удаляет, а реестр контента и автоматические проверки не позволяют опубликовать заглушки, вымышленные работы, дубли владельцев запросов или неподтверждённые города.

**Tech Stack:** Python 3.10+ (`csv`, `json`, `dataclasses`, `unittest`, `urllib`), PHP 7.4+/WordPress, ACF, существующие шаблоны темы `land76wp`, Яндекс Search API и Вебмастер только для доказательств и мониторинга, Git.

**Spec:** `docs/superpowers/specs/2026-08-20-exp76-semantic-strategy-design.md`

## Global Constraints

- Сохранять URL, ID, parent и template восьми страниц S1–S8; это публичные хабы, а не временные посадочные страницы.
- Не менять категории 87–92, их дочерние услуги, статьи и геостраницы; все пересечения с ними получают `frozen_owner`.
- Новый коммерческий URL создаётся только при самостоятельном интенте, SERP-доказательстве и возможности дать отдельные состав работ, факторы цены и реальные фотографии или кейс.
- Информационный кластер публикуется отдельной статьёй и ссылается на один главный коммерческий владелец; статья не дублирует коммерческий title/H1.
- К каждому хабу и каждой подуслуге привязывать только существующие кейсы и фотографии, прослеживаемые до WordPress URL/ID; вымышленные объекты, цены, сроки, гарантии и адреса запрещены.
- Подготовленный import JSON не считать доказательством публикации: фактическое наличие статьи, подуслуги или кейса проверять по live URL и WordPress ID; сейчас в JSON подготовлено 37 статей шести старых направлений, а live подтверждено 27.
- Кейсы с достаточной фактурой получают SEO-поля и двустороннюю перелинковку через существующий `import-case-seo.php`; исходные фотографии не переименовывать и не удалять.
- Геостраница создаётся только при доказанном спросе и локальном факте: кейсе, фотографии, условиях выезда, сроках или особенностях работ в конкретном городе.
- Восемь хабов обязательно выводят кликабельные карточки подуслуг, статьи, релевантные работы, цены/факторы цены, FAQ и ссылки на защищённые смежные направления.
- Подуслуги и статьи публикуются только с финальными текстами; пустые секции, шаблонные фразы и заглушки запрещены.
- Импортёр по умолчанию работает в preview-режиме, не удаляет записи и не меняет сущности вне release manifest.
- Секреты, API-ключи, cookies, FTP-пароли и WordPress-пароли не сохранять в проекте и не включать в команды, логи или commit.
- Все текстовые файлы — UTF-8; имена файлов, модулей, функций, классов и JSON-ключей — ASCII.
- Любое изменение кода или данных начинается с падающего теста; каждый логический task заканчивается проверками, отдельным commit и push.
- Перед production-запуском создать резервные копии только изменяемых удалённых файлов и экспорт ID/slug затрагиваемых WordPress-записей; массовые удаления, force-push и переписывание истории запрещены.

---

## File Map

### Семантика и архитектура

- `tools/seo_semantics/architecture.py` — модели решений, построение дерева страниц и строгая проверка владельцев кластеров.
- `tools/test_semantic_architecture.py` — тесты состояния `pending`, правил split/merge и полноты карты.
- `seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv` — неизменяемый evidence-слой из 1 044 пар, включая 263 пары для ручной проверки.
- `seo-data/2026-08-exp76-services/reviews/serp_pair_reviews.csv` — отдельные окончательные решения ровно по 263 `pair_id`.
- `seo-data/2026-08-exp76-services/reviews/cluster_page_decisions.csv` — явное назначение каждого кластера в hub/child/article/frozen/exclude.
- `seo-data/2026-08-exp76-services/processed/clusters.csv` — окончательные решения по 164 кластерам.
- `seo-data/2026-08-exp76-services/processed/url_map.csv` — один владелец каждого кластера.
- `seo-data/2026-08-exp76-services/processed/page_architecture.csv` — единый реестр destinations для хабов, подуслуг, статей и допустимых геостраниц.
- `seo-data/2026-08-exp76-services/processed/content_briefs.csv` — самостоятельный production-бриф каждой публичной страницы.
- `seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx` — обновлённая проверяемая книга.

### Контент и доказательства

- `tools/site_content/__init__.py` — публичные экспорты контентного пакета.
- `tools/site_content/contracts.py` — загрузка и строгая проверка hub/service/article/geo JSON.
- `tools/site_content/cases.py` — сбор каталога реальных кейсов и изображений.
- `tools/site_content/release.py` — release manifest, link graph и проверки готовности.
- `tools/test_site_content_contracts.py` — тесты обязательных секций, уникальности и отсутствия заглушек.
- `tools/test_site_content_cases.py` — тесты прослеживаемости кейсов и изображений.
- `tools/test_site_content_release.py` — тесты полноты релиза, ссылок и frozen-границ.
- `seo-content/service-hubs/case-catalog.json` — нормализованный каталог только существующих работ и фотографий.
- `seo-content/service-hubs/hubs/*.json` — финальные данные восьми хабов.
- `seo-content/service-hubs/services/<service-id>/*.json` — финальные коммерческие подуслуги.
- `seo-content/service-hubs/articles/<service-id>/*.json` — финальные информационные статьи.
- `seo-content/service-hubs/geo/<service-id>/*.json` — только подтверждённые локальные страницы.
- `seo-content/service-hubs/release-manifest.json` — точный список создаваемых/обновляемых сущностей и их владельцев.
- `seo-content/service-hubs/link-graph.csv` — все обязательные внутренние ссылки.
- `seo-content/service-hubs/content-inventory.csv` — проверяемый объём контента по типам и направлениям.

### WordPress

- `ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json` — восемь hub payloads schema v2.
- `ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/rendered/*.html` — восемь предварительно отрендеренных хабов.
- `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json` — production payload подуслуг, статей, категорий и геостраниц.
- `ftp_dump_minimal/wp-content/themes/land76wp/import/acf-service-hub-relations.json` — переносимая ACF-схема `selected_works_posts` и `selected_real_projects`, которых нет в текущем repo-export.
- `ftp_dump_minimal/wp-content/themes/land76wp/import/cases-seo-import.json` — расширенная карта существующих кейсов и связей.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/import-service-hubs.php` — безопасный preview/apply upsert без удаления.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2.php` — загрузка hub schema v2 и SEO metadata.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2-template.php` — кликабельные подуслуги, статьи и кейсы.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/newservicepost.php` — явный topic key и реальные изображения для новых подуслуг.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/seoblogpost.php` — явный topic key и обратные ссылки статей.
- `seo-content/blog/acf-seo-blog-post-fields.json` — relationship статьи к коммерческому владельцу типа post или page.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/import-drenazh-blog.php` — общий resolver связанных услуг для post и page.
- `ftp_dump_minimal/wp-content/themes/land76wp/inc/seo-category-indexing.php` — точное правило для внутренних категорий новых хабов.
- `ftp_dump_minimal/wp-content/themes/land76wp/functions.php` — подключение импортёра и безопасный роутинг.
- `ftp_dump_minimal/wp-content/themes/land76wp/css/service-v2.css` — стили карточек-ссылок, статей и доказательств.
- `tools/test_service_hubs_php.py` — статические тесты импортёра, маршрутизации, canonical и отсутствия удаления.

---

### Task 1: Correct the Semantic Decision State Machine

**Files:**
- Create: `tools/seo_semantics/architecture.py`
- Create: `tools/test_semantic_architecture.py`
- Modify: `tools/seo_semantics/serp.py`
- Modify: `tools/seo_semantics/cli.py`

**Interfaces:**
- Consumes: `ScopeConfig`, `clusters.csv`, `candidate_cluster_map.csv`, `serp_ambiguous_pairs.csv`, the two review CSV files
- Produces: `PairReview`, `ClusterPageDecision`, `PageDestination`, `ArchitectureBuild`
- Produces: `resolve_pair_action(pair: PairReview) -> str`
- Produces: `build_pair_review_queue(ambiguous_rows: Sequence[Mapping[str, str]]) -> list[dict[str, str]]`
- Produces: `load_pair_reviews(path: Path) -> dict[str, PairReview]`
- Produces: `validate_pair_review_coverage(ambiguous_rows, reviews) -> list[str]`
- Produces: `load_cluster_page_decisions(path: Path) -> dict[str, ClusterPageDecision]`
- Produces: `resolve_url_architecture(scope, clusters, candidates, ambiguous_pairs, pair_reviews, cluster_decisions) -> ArchitectureBuild`
- Produces: `validate_architecture(build: ArchitectureBuild, *, release: bool = False) -> list[str]`
- Produces: `build_destination_briefs(architecture, candidates) -> list[dict[str, str]]`
- Produces: CLI `review-queue` and `resolve-architecture`

- [ ] **Step 1: Write failing tests for unresolved decisions**

```python
def test_pending_pair_cannot_become_keep_enhance():
    pair = PairReview(
        pair_id="PAIR-1",
        decision="manual_review",
        owner_action="hold_current_url",
        review_status="pending",
        reviewer="",
        rationale="",
    )
    with self.assertRaisesRegex(ArchitectureError, "PAIR-1 remains pending"):
        resolve_pair_action(pair)


def test_every_accepted_commercial_cluster_has_exactly_one_owner():
    destinations = (
        PageDestination("S5-HUB", "S5", "hub", "", "https://exp76.ru/services/planirovka-territorii/", ("C1",)),
        PageDestination("S5-CHILD-1", "S5", "child_service", "S5-HUB", "https://exp76.ru/vertikalnaya-planirovka-uchastka/", ("C1",)),
    )
    build = ArchitectureBuild(destinations=destinations, commercial_cluster_ids=frozenset({"C1"}))
    self.assertIn("cluster C1 has 2 owners", validate_architecture(build))
```

- [ ] **Step 2: Run the tests and observe the missing module failure**

Run: `python -m unittest tools.test_semantic_architecture -v`

Expected: FAIL because `tools.seo_semantics.architecture` does not exist.

- [ ] **Step 3: Implement explicit decision states**

Use these exact enums in `architecture.py`:

```python
COMMERCIAL_ACTIONS = {"hub", "child", "merge", "exclude", "frozen", "unresolved"}
INFORMATIONAL_ACTIONS = {"article", "merge", "exclude", "frozen"}
FINAL_REVIEW_STATUSES = {"reviewed", "approved"}
```

Use these exact dataclass fields: `PairReview(pair_id, decision, review_status, reviewer, rationale, evidence_note)`, `ClusterPageDecision(cluster_id, service_id, destination_id, page_role, parent_destination_id, current_url, proposed_url, proposed_slug, url_action, publication_status, business_offer_confirmed, evidence_refs, review_status, reviewer, rationale)`, `PageDestination(destination_id, service_id, page_role, parent_destination_id, canonical_url, source_cluster_ids)`, and `ArchitectureBuild(destinations, commercial_cluster_ids, informational_cluster_ids=(), errors=())`.

Draft processing may emit `url_action=unresolved` only with a blank target/destination. Release validation must reject `pending`, `unresolved`, a blank reviewer, a blank rationale, or `hold_current_url`. SERP evidence status never chooses a page owner by itself. Existing S1–S8 URLs are the only valid `hub` URLs; a `child` URL must be internal HTTPS, unique and different from all hub/frozen URLs.

- [ ] **Step 4: Remove the unsafe fallback in `serp.py`**

Replace the branch that maps every unresolved commercial cluster to `target_url=current_url` and `url_action=keep_enhance` with `url_action=unresolved`, blank `target_url`, blank destination and rationale naming all unresolved pair IDs. Preserve automatic `frozen_owner`, policy exclusion and already reviewed cross-service boundaries.

- [ ] **Step 5: Add the architecture command**

Run contract:

```powershell
python -m tools.seo_semantics.cli review-queue --ambiguous seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv --output seo-data/2026-08-exp76-services/reviews/serp_pair_reviews.csv
python -m tools.seo_semantics.cli resolve-architecture --scope seo-data/2026-08-exp76-services/scope.json --clusters seo-data/2026-08-exp76-services/processed/clusters.csv --candidate-map seo-data/2026-08-exp76-services/processed/candidate_cluster_map.csv --ambiguous seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv --pair-reviews seo-data/2026-08-exp76-services/reviews/serp_pair_reviews.csv --cluster-decisions seo-data/2026-08-exp76-services/reviews/cluster_page_decisions.csv --url-map-output seo-data/2026-08-exp76-services/processed/url_map.csv --page-architecture-output seo-data/2026-08-exp76-services/processed/page_architecture.csv --briefs-output seo-data/2026-08-exp76-services/processed/content_briefs.csv
```

The command exits non-zero and names every unresolved pair or cluster; it never silently selects a hub.

- [ ] **Step 6: Run focused and regression tests**

Run:

```powershell
python -m unittest tools.test_semantic_architecture tools.test_semantic_serp -v
git diff --check
```

Expected: all tests pass and `git diff --check` prints nothing.

- [ ] **Step 7: Commit and push**

```powershell
git add tools/seo_semantics/architecture.py tools/seo_semantics/serp.py tools/seo_semantics/cli.py tools/test_semantic_architecture.py
git commit -m "fix: require reviewed semantic page decisions"
git push origin codex/semantic-core
```

---

### Task 2: Finish All SERP Reviews and Freeze the Page Tree

**Files:**
- Create: `seo-data/2026-08-exp76-services/reviews/serp_pair_reviews.csv`
- Create: `seo-data/2026-08-exp76-services/reviews/cluster_page_decisions.csv`
- Preserve: `seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv`
- Modify: `seo-data/2026-08-exp76-services/processed/clusters.csv`
- Modify: `seo-data/2026-08-exp76-services/processed/url_map.csv`
- Create: `seo-data/2026-08-exp76-services/processed/page_architecture.csv`
- Modify: `seo-data/2026-08-exp76-services/processed/content_briefs.csv`
- Modify: `seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx`
- Modify: `seo-data/2026-08-exp76-services/README.md`

**Interfaces:**
- Consumes: Task 1 `architecture` command and all 141 stored representative-query SERPs
- Produces: zero pending pair reviews, one final action per cluster and one complete page tree
- Produces fields: `destination_id,service_id,page_role,parent_destination_id,current_url,proposed_url,canonical_url,primary_cluster_id,source_cluster_ids,url_action,publication_status,evidence_refs,review_status,reviewer,rationale`

- [ ] **Step 1: Add a failing completeness test**

```python
def test_production_semantic_files_have_no_pending_decisions():
    evidence = read_csv(PROCESSED / "serp_ambiguous_pairs.csv")
    reviews = read_csv(REVIEWS / "serp_pair_reviews.csv")
    required = {row["pair_id"] for row in evidence if row["decision"] == "manual_review"}
    self.assertEqual(1044, len(evidence))
    self.assertEqual(263, len(required))
    self.assertEqual(required, {row["pair_id"] for row in reviews})
    self.assertTrue(all(row["review_status"] == "reviewed" for row in reviews))
    architecture = read_csv(PROCESSED / "page_architecture.csv")
    self.assertEqual({f"S{i}" for i in range(1, 9)}, {row["service_id"] for row in architecture if row["page_role"] == "hub"})
```

- [ ] **Step 2: Run the test and confirm all 263 pending pair IDs are reported**

Run: `python -m unittest tools.test_semantic_architecture.SemanticProductionDataTest -v`

Expected: FAIL listing 263 pending pair decisions.

- [ ] **Step 3: Review every pending same-service pair**

For each required `pair_id` write one overlay row with fields `pair_id,decision,review_status,reviewer,rationale,evidence_note`. Use the stored top results, query intent and service composition. Pair decision is exactly one of:

- `same_destination` — same need and same page format;
- `separate_destinations` — different need or page format.

Set `review_status=reviewed`, `reviewer=codex-2026-08-28`, and write a concrete rationale containing overlap count and result-format observation. Validate exact set coverage, duplicates, unknown IDs and transitive contradictions before page assignment.

- [ ] **Step 4: Collect only missing SERP evidence**

First run `serp-api-plan` and use existing `yandex-api-Q*.jsonl`. Submit an additional API request only for a proposed child/article whose representative query lacks a successful result file. Credentials come only from process environment; cumulative additional spend must remain within the user-approved 50-ruble limit.

```powershell
python -m tools.seo_semantics.cli serp-api-plan --queue seo-data/2026-08-exp76-services/raw/serp/serp-queue.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp
```

- [ ] **Step 5: Record cluster-to-page decisions**

Write `cluster_page_decisions.csv` with fields `cluster_id,service_id,destination_id,page_role,parent_destination_id,current_url,proposed_url,proposed_slug,url_action,publication_status,business_offer_confirmed,evidence_refs,review_status,reviewer,rationale`. `page_role` is `hub|child_service|article|special|frozen|none`; `publication_status` is `ready|blocked_facts|backlog`. A child may be `ready` only with `business_offer_confirmed=yes` and non-empty evidence refs.

- [ ] **Step 6: Rebuild clusters and freeze the architecture**

Run the existing `cluster` command, then Task 1 `architecture`. Assign every one of the 115 commercial clusters to `hub`, `child`, `merge`, `exclude` or `frozen`; assign every informational cluster to `article`, `merge`, `exclude` or `frozen`. The number of public pages is the evidence-backed result, not a preset quota.

- [ ] **Step 7: Regenerate briefs and workbook**

Each page brief must include its own primary query, secondary queries, intent, section list, price factors, internal links and evidence state. `case_ids` and `photo_ids` may be blank at this point only with `status=needs_case_mapping`; production content cannot retain that status.

- [ ] **Step 8: Run semantic QA**

```powershell
python -m tools.seo_semantics.cli qa --scope seo-data/2026-08-exp76-services/scope.json --processed-dir seo-data/2026-08-exp76-services/processed --workbook seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
python -m unittest tools.test_semantic_architecture tools.test_semantic_serp tools.test_semantic_workbook -v
```

Expected: 263/263 reviewed pairs, all 115 commercial clusters assigned exactly once, exactly eight hubs, zero unresolved release rows, zero duplicate owners and all tests pass.

- [ ] **Step 9: Commit and push**

```powershell
git add seo-data/2026-08-exp76-services tools/test_semantic_architecture.py
git commit -m "feat: approve service hub page architecture"
git push origin codex/semantic-core
```

---

### Task 3: Build the Traceable Case and Photo Catalog

**Files:**
- Create: `tools/site_content/__init__.py`
- Create: `tools/site_content/cases.py`
- Create: `tools/test_site_content_cases.py`
- Create: `seo-content/service-hubs/case-catalog.json`
- Modify: `seo-content/cases/import/cases-seo-import.json`

**Interfaces:**
- Consumes: `cases_by_category.json`, `acf_selected_works_map.json`, `seo-content/cases/import/cases-seo-import.json`, existing service-v2 case/image data
- Produces: `build_case_catalog(root: Path) -> tuple[CaseEvidence, ...]`
- Produces: `validate_case_reference(case_id: int, image_url: str, catalog: Sequence[CaseEvidence]) -> list[str]`

- [ ] **Step 1: Write failing traceability tests**

```python
def test_catalog_rejects_unknown_case_and_unowned_photo():
    catalog = (CaseEvidence(101, "https://exp76.ru/portfolio/real/", ("https://exp76.ru/wp-content/uploads/real.webp",), ("S5",), "Ярославль"),)
    self.assertIn("unknown case 999", validate_case_reference(999, "https://exp76.ru/wp-content/uploads/fake.webp", catalog))


def test_catalog_keeps_location_and_work_facts():
    catalog = build_case_catalog(ROOT)
    self.assertTrue(all(item.url and item.work_types for item in catalog))
```

- [ ] **Step 2: Run the tests and observe the missing module failure**

Run: `python -m unittest tools.test_site_content_cases -v`

- [ ] **Step 3: Normalize the existing 35 case records**

`CaseEvidence` must contain `page_id`, `url`, `title`, `location`, `work_types`, `service_ids`, `image_urls`, `source_files`, `seo_ready`. Resolve duplicates by canonical URL. A case may support several services only when its existing description or ACF scope explicitly names those works.

- [ ] **Step 4: Audit every selected image URL read-only**

Accept only internal `https://exp76.ru/wp-content/uploads/...` URLs that return an image content type. Save status, content type and checked date in `case-catalog.json`; never download or replace the source file during this task.

- [ ] **Step 5: Extend case SEO mappings without inventing facts**

For cases used by the new architecture populate existing `cs87_*` fields from current page facts, set `cs87_service_url` to the strongest relevant commercial page, and add related case URLs only when the work type or location genuinely overlaps. Preserve unrelated existing case fields.

- [ ] **Step 6: Run tests and catalog validation**

```powershell
python -m unittest tools.test_site_content_cases -v
python -m tools.site_content.cases --root . --output seo-content/service-hubs/case-catalog.json --validate
```

Expected: every referenced case and image resolves; unsupported mappings are absent.

- [ ] **Step 7: Commit and push**

```powershell
git add tools/site_content tools/test_site_content_cases.py seo-content/service-hubs/case-catalog.json seo-content/cases/import/cases-seo-import.json
git commit -m "feat: map real cases to service hubs"
git push origin codex/semantic-core
```

---

### Task 4: Define the Production Content Contract

**Files:**
- Create: `tools/site_content/contracts.py`
- Create: `tools/test_site_content_contracts.py`
- Create: `seo-content/service-hubs/release-manifest.json`
- Modify: `tools/service_v2.py`
- Modify: `tools/test_service_v2.py`

**Interfaces:**
- Consumes: `page_architecture.csv`, `content_briefs.csv`, `case-catalog.json`
- Produces: `load_content_page(path: Path) -> ContentPage`
- Produces: `validate_content_page(page: ContentPage, architecture: Mapping[str, PageDestination], cases: Mapping[int, CaseEvidence]) -> list[str]`
- Produces: hub schema version 2 with linked services, articles and cases

- [ ] **Step 1: Write failing contract tests**

```python
def test_service_page_requires_complete_unique_content():
    page = fixture_service_page()
    page["sections"] = []
    errors = validate_content_page_dict(page, ARCHITECTURE, CASES)
    self.assertIn("sections must contain at least 5 items", errors)


def test_hub_cards_require_approved_child_urls():
    hub = fixture_hub()
    hub["services"]["items"][0]["url"] = "https://exp76.ru/not-approved/"
    errors = validate_content_page_dict(hub, ARCHITECTURE, CASES)
    self.assertIn("service card URL is absent from page architecture", errors)
```

- [ ] **Step 2: Run the tests and observe failures**

```powershell
python -m unittest tools.test_site_content_contracts tools.test_service_v2 -v
```

- [ ] **Step 3: Implement the shared contract**

Every commercial child requires: `page_key`, `service_id`, `page_type=service`, `slug`, `canonical`, unique `seo.title`, unique `seo.description`, `hero`, `problem`, `solution`, at least five substantive sections, price factors, process, at least five FAQ items, at least one verified case or an explicitly verified hub-level case fallback, a real main image, related commercial links and related article links.

Every article requires: `page_type=article`, one informational primary query, at least four substantive sections, a real main image, at least one commercial owner link, FAQ only when questions are supported by the cluster, and no commercial CTA claim beyond the facts already used on service pages.

Every hub requires: all schema v1 fields plus `schema_version=2`, `services.items[].page_key/url`, `articles.items[].page_key/url/title/text/image`, and verified `proof.cases`. Hub service cards are rendered as anchors; empty article and case blocks are forbidden in a production manifest.

- [ ] **Step 4: Add cross-page validation**

Reject duplicate canonical, title or H1; a cluster owned by two pages; an architecture page absent from manifest; a manifest page absent from architecture; an internal link outside the manifest/frozen set; a case/photo not in catalog; blank text; repeated paragraph fingerprints; replacement-character corruption; and claims containing numeric price/term/guarantee values without a matching evidence field.

- [ ] **Step 5: Upgrade the service-v2 generator to schema 2**

Keep the exact eight owner IDs and slugs. Require linked service/article items and verified cases, render semantic `<a>` cards, preserve the current canonical and hero metadata, and make generation atomic through a temporary output directory followed by file replacement only after all eight payloads pass.

- [ ] **Step 6: Run focused tests**

```powershell
python -m unittest tools.test_site_content_contracts tools.test_service_v2 -v
git diff --check
```

- [ ] **Step 7: Commit and push**

```powershell
git add tools/site_content/contracts.py tools/test_site_content_contracts.py tools/service_v2.py tools/test_service_v2.py seo-content/service-hubs/release-manifest.json
git commit -m "feat: enforce production service content contract"
git push origin codex/semantic-core
```

---

### Task 5: Add an Idempotent WordPress Import and Safe Routing

**Files:**
- Create: `ftp_dump_minimal/wp-content/themes/land76wp/inc/import-service-hubs.php`
- Create: `tools/test_service_hubs_php.py`
- Create: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`
- Create: `ftp_dump_minimal/wp-content/themes/land76wp/import/acf-service-hub-relations.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/functions.php`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/newservicepost.php`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/seoblogpost.php`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/seo-category-indexing.php`
- Modify: `seo-content/blog/acf-seo-blog-post-fields.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/import-drenazh-blog.php`

**Interfaces:**
- Consumes: release manifest and validated content JSON
- Produces: `land76wp_service_hubs_build_plan(array $payload) -> array`
- Produces: `land76wp_run_service_hubs_import($json_path = '', $apply = false) -> array`
- Produces: exact post meta `_land76_page_key`, `_land76_service_id`, `_land76_topic_key`, `_land76_canonical`

- [ ] **Step 1: Write failing static safety tests**

```python
def test_importer_defaults_to_preview_and_contains_no_delete_call():
    source = IMPORTER.read_text(encoding="utf-8")
    self.assertIn("$apply = false", source)
    self.assertNotIn("wp_delete_post", source)
    self.assertNotIn("wp_delete_term", source)


def test_new_topic_resolution_uses_explicit_post_meta():
    service = NEW_SERVICE.read_text(encoding="utf-8")
    article = SEO_BLOG.read_text(encoding="utf-8")
    self.assertIn("_land76_topic_key", service)
    self.assertIn("_land76_topic_key", article)
```

- [ ] **Step 2: Run the test and confirm importer absence**

Run: `python -m unittest tools.test_service_hubs_php -v`

- [ ] **Step 3: Implement preview/apply upsert**

The importer must:

- validate `schema_version=1` and an exact `release_id` before any write;
- ensure eight internal grouping categories by fixed ASCII slug, store the corresponding hub URL in term meta and never expose them as competing indexable hubs;
- upsert commercial posts by exact slug and `_land76_page_key`, assign categories `[74, grouping_term_id]`, set ACF and SEO metadata;
- upsert article posts by exact slug and `_land76_page_key`, assign categories `[72, grouping_term_id]`, set ACF and related commercial IDs;
- upsert only approved geo pages with explicit template, region, local evidence and canonical;
- update selected real project ACF fields only with resolved existing case IDs;
- return `planned`, `created`, `updated`, `unchanged`, `unresolved_cases`, `errors` and `rollback_snapshot`;
- perform no mutation when `$apply=false` or when any validation error exists.

Before upsert, import or register the exact ACF relationship fields `selected_works_posts` for category context and `selected_real_projects` for category-74 posts. Both fields restrict selection to existing case/page objects and preserve current live values. Abort apply when ACF is unavailable or the field schema cannot be verified.

Expand `blogseo_related_services` to accept `post` and `page`, and resolve `blogseo_related_service_slugs` against both types with an exact canonical check. This allows an informational article to point either to an accepted child post or directly to one of the eight existing hub pages; do not create a duplicate hidden post only to satisfy the relationship field.

- [ ] **Step 4: Guard the apply action**

Register an admin-only Tools page. Preview requires `manage_options`; apply additionally requires a WordPress nonce, the exact release ID typed into a confirmation field and a clean preview generated in the same request. Do not add a public query-string runner.

- [ ] **Step 5: Make topic/image handling explicit**

`newservicepost.php` and `seoblogpost.php` must read `_land76_topic_key` first. For new service IDs they must use the main image and alt supplied by ACF/import data; the old drainage fallback remains only for historical posts without the new meta. Articles must render their related service links; services must render related article links.

- [ ] **Step 6: Redirect only internal grouping archives**

For the exact eight new grouping category slugs, redirect archive requests to the mapped existing `/services/.../` hub and filter canonical/sitemap ownership accordingly. Leave categories 87–92 unchanged. Unknown categories follow existing WordPress behavior.

- [ ] **Step 7: Run PHP and static tests**

```powershell
python -m unittest tools.test_service_hubs_php -v
Get-ChildItem ftp_dump_minimal\wp-content\themes\land76wp\inc\*.php,ftp_dump_minimal\wp-content\themes\land76wp\functions.php | ForEach-Object { php -l $_.FullName }
```

Expected: tests pass and every PHP file reports no syntax errors.

- [ ] **Step 8: Commit and push**

```powershell
git add ftp_dump_minimal/wp-content/themes/land76wp tools/test_service_hubs_php.py
git commit -m "feat: add safe service hub importer"
git push origin codex/semantic-core
```

---

### Task 6: Upgrade the Eight Existing Pages into Navigable Hubs

**Files:**
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2.php`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2-template.php`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/css/service-v2.css`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/rendered/*.html`
- Test: `tools/test_service_v2.py`

**Interfaces:**
- Consumes: Task 4 hub schema v2 and Task 2 page tree
- Produces: eight complete hub pages with child/article/case navigation

- [ ] **Step 1: Add failing hub-output tests**

```python
def test_every_hub_links_all_approved_children_articles_and_cases():
    architecture = load_architecture()
    for service_id, path in SERVICE_FILES.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        approved = {row.target_url for row in architecture if row.service_id == service_id and row.parent_key == f"{service_id}-HUB"}
        rendered = render_service(payload)
        for url in approved:
            self.assertIn(f'href="{url}"', rendered)
```

- [ ] **Step 2: Run the tests and confirm schema-v1 pages fail**

Run: `python -m unittest tools.test_service_v2 -v`

- [ ] **Step 3: Populate all eight schema-v2 hub payloads**

Reuse and edit the existing final hub text instead of discarding it. Replace each inline service card with its accepted child URL, add all accepted article cards, attach the strongest verified cases/photos from Task 3, and ensure the hub retains the broad head cluster while child pages own narrower intents.

- [ ] **Step 4: Render accessible cards and breadcrumbs**

Use real `<a>` elements with visible focus, meaningful link text and responsive card layout. Add hub → child/article/case links and child/article breadcrumb targets without JavaScript navigation. Preserve forms and current CTA behavior.

- [ ] **Step 5: Regenerate and validate all eight hubs**

```powershell
python tools/service_v2.py validate ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2
python tools/service_v2.py build ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2 ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/rendered
python -m unittest tools.test_service_v2 -v
```

Expected: exactly eight hub payloads and renders pass schema 2; every approved child/article URL is linked once or more.

- [ ] **Step 6: Commit and push**

```powershell
git add ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2.php ftp_dump_minimal/wp-content/themes/land76wp/inc/service-v2-template.php ftp_dump_minimal/wp-content/themes/land76wp/css/service-v2.css ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2 tools/test_service_v2.py
git commit -m "feat: turn legacy services into SEO hubs"
git push origin codex/semantic-core
```

---

### Task 7: Produce S5 Planning and S8 Site-Entrance Content

**Files:**
- Create/Modify: `seo-content/service-hubs/services/S5/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S5/*.json`
- Create/Modify: `seo-content/service-hubs/services/S8/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S8/*.json`
- Modify: `seo-content/service-hubs/hubs/S5.json`
- Modify: `seo-content/service-hubs/hubs/S8.json`
- Modify: `seo-content/service-hubs/release-manifest.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`

**Interfaces:**
- Consumes: accepted S5/S8 architecture, content briefs and case catalog
- Produces: every approved S5/S8 service and article in publishable form

- [ ] **Step 1: Add failing manifest coverage tests for S5 and S8**

```python
def test_s5_s8_manifest_matches_architecture():
    self.assertEqual(approved_page_keys({"S5", "S8"}), manifest_page_keys({"S5", "S8"}))
```

- [ ] **Step 2: Run the test and confirm missing page keys**

Run: `python -m unittest tools.test_site_content_release.ServiceWaveCoverageTest.test_s5_s8_manifest_matches_architecture -v`

- [ ] **Step 3: Write all approved S5 commercial pages and articles**

Give each page unique title/H1, problem, scope, technology, price factors, process, FAQ, real evidence and links. Keep drainage, stormwater and dewatering intents owned by frozen categories; link to them when water management is part of the job instead of duplicating their pages.

- [ ] **Step 4: Write all approved S8 commercial pages and articles**

Separate construction/service intents proven by the architecture, such as pipe/culvert, headwalls, ditch crossing, load-bearing entrance and repair, only when each has its own accepted page key. Product-only pipe queries remain excluded. Use only actual entrance/roadwork cases and photos.

- [ ] **Step 5: Validate content and generate import records**

```powershell
python -m tools.site_content.release validate --services S5,S8 --root seo-content/service-hubs
python -m tools.site_content.release build-import --services S5,S8 --root seo-content/service-hubs --output ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json
```

Expected: all accepted page keys are present, no placeholders or unsupported facts, and every page has commercial/article/case links.

- [ ] **Step 6: Commit and push**

```powershell
git add seo-content/service-hubs ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json tools/test_site_content_release.py
git commit -m "feat: add planning and site entrance content hubs"
git push origin codex/semantic-core
```

---

### Task 8: Produce S2 Lawn and S3 Planting Content

**Files:**
- Create/Modify: `seo-content/service-hubs/services/S2/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S2/*.json`
- Create/Modify: `seo-content/service-hubs/services/S3/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S3/*.json`
- Modify: `seo-content/service-hubs/hubs/S2.json`
- Modify: `seo-content/service-hubs/hubs/S3.json`
- Modify: `seo-content/service-hubs/release-manifest.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`

**Interfaces:**
- Consumes: accepted S2/S3 architecture and verified horticultural cases/photos
- Produces: every approved S2/S3 service and article in publishable form

- [ ] **Step 1: Add and run failing S2/S3 coverage test**

```python
def test_s2_s3_manifest_matches_architecture():
    self.assertEqual(approved_page_keys({"S2", "S3"}), manifest_page_keys({"S2", "S3"}))
```

Run: `python -m unittest tools.test_site_content_release.ServiceWaveCoverageTest.test_s2_s3_manifest_matches_architecture -v`

- [ ] **Step 2: Write all approved S2 pages**

Separate rolled lawn, seeded lawn, ground preparation and aftercare only according to accepted page keys. Avoid duplicating S4 recurring garden-care intent; cross-link it where appropriate.

- [ ] **Step 3: Write all approved S3 pages**

Separate trees, conifers, shrubs, large specimens, soil preparation and aftercare only where accepted. Every claim about season, survival or planting technology must be phrased from current company practice or reliable general facts without fabricated guarantee percentages.

- [ ] **Step 4: Validate and rebuild import payload**

```powershell
python -m tools.site_content.release validate --services S2,S3 --root seo-content/service-hubs
python -m tools.site_content.release build-import --services S2,S3 --root seo-content/service-hubs --output ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json
```

- [ ] **Step 5: Commit and push**

```powershell
git add seo-content/service-hubs ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json tools/test_site_content_release.py
git commit -m "feat: add lawn and planting content hubs"
git push origin codex/semantic-core
```

---

### Task 9: Produce S4 Garden Care and S6 Retaining-Wall Content

**Files:**
- Create/Modify: `seo-content/service-hubs/services/S4/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S4/*.json`
- Create/Modify: `seo-content/service-hubs/services/S6/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S6/*.json`
- Modify: `seo-content/service-hubs/hubs/S4.json`
- Modify: `seo-content/service-hubs/hubs/S6.json`
- Modify: `seo-content/service-hubs/release-manifest.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`

**Interfaces:**
- Consumes: accepted S4/S6 architecture and verified care/construction cases
- Produces: every approved S4/S6 service and article in publishable form

- [ ] **Step 1: Add and run failing S4/S6 coverage test**

```python
def test_s4_s6_manifest_matches_architecture():
    self.assertEqual(approved_page_keys({"S4", "S6"}), manifest_page_keys({"S4", "S6"}))
```

Run: `python -m unittest tools.test_site_content_release.ServiceWaveCoverageTest.test_s4_s6_manifest_matches_architecture -v`

- [ ] **Step 2: Write all approved S4 pages and articles**

Keep seasonal maintenance, pruning, lawn care, flowerbeds and feeding separate only when accepted. Link lawn installation back to S2 and planting back to S3 instead of repeating their commercial offers.

- [ ] **Step 3: Write all approved S6 pages and articles**

Separate material/technology intents only when the company actually performs them and a real case/photo supports the page. Drainage behind retaining walls links to protected drainage content and does not claim its queries.

- [ ] **Step 4: Validate and rebuild import payload**

```powershell
python -m tools.site_content.release validate --services S4,S6 --root seo-content/service-hubs
python -m tools.site_content.release build-import --services S4,S6 --root seo-content/service-hubs --output ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json
```

- [ ] **Step 5: Commit and push**

```powershell
git add seo-content/service-hubs ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json tools/test_site_content_release.py
git commit -m "feat: add garden care and retaining wall hubs"
git push origin codex/semantic-core
```

---

### Task 10: Produce S1 Landscape Design and S7 Lighting Content

**Files:**
- Create/Modify: `seo-content/service-hubs/services/S1/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S1/*.json`
- Create/Modify: `seo-content/service-hubs/services/S7/*.json`
- Create/Modify: `seo-content/service-hubs/articles/S7/*.json`
- Modify: `seo-content/service-hubs/hubs/S1.json`
- Modify: `seo-content/service-hubs/hubs/S7.json`
- Modify: `seo-content/service-hubs/release-manifest.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`

**Interfaces:**
- Consumes: accepted S1/S7 architecture and verified design/lighting cases
- Produces: every approved S1/S7 service and article in publishable form

- [ ] **Step 1: Add and run failing S1/S7 coverage test**

```python
def test_s1_s7_manifest_matches_architecture():
    self.assertEqual(approved_page_keys({"S1", "S7"}), manifest_page_keys({"S1", "S7"}))
```

Run: `python -m unittest tools.test_site_content_release.ServiceWaveCoverageTest.test_s1_s7_manifest_matches_architecture -v`

- [ ] **Step 2: Write all approved S1 pages and articles**

Keep the hub as the broad design offer. Create separate sketch, 3D, master plan, dendroplan or engineering-coordination pages only when accepted; protected drainage/stormwater/irrigation design links to their existing owners.

- [ ] **Step 3: Write all approved S7 pages and articles**

Separate pathway, façade, garden, functional or decorative lighting only where accepted and evidenced. Do not state electrical certifications, equipment brands or warranty periods absent from source data.

- [ ] **Step 4: Validate and rebuild import payload**

```powershell
python -m tools.site_content.release validate --services S1,S7 --root seo-content/service-hubs
python -m tools.site_content.release build-import --services S1,S7 --root seo-content/service-hubs --output ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json
```

- [ ] **Step 5: Commit and push**

```powershell
git add seo-content/service-hubs ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json tools/test_site_content_release.py
git commit -m "feat: add landscape design and lighting hubs"
git push origin codex/semantic-core
```

---

### Task 11: Complete Article, Case, Geo and Link Integration

**Files:**
- Create: `tools/site_content/release.py`
- Create: `tools/test_site_content_release.py`
- Create/Modify: `seo-content/service-hubs/geo/<service-id>/*.json`
- Create: `seo-content/service-hubs/link-graph.csv`
- Create: `seo-content/service-hubs/content-inventory.csv`
- Modify: `seo-content/service-hubs/release-manifest.json`
- Modify: `seo-content/cases/import/cases-seo-import.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/cases-seo-import.json`
- Modify: `ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json`

**Interfaces:**
- Consumes: all wave content, architecture and case catalog
- Produces: `validate_release(root: Path) -> list[str]`
- Produces: `build_link_graph(root: Path) -> tuple[LinkEdge, ...]`
- Produces: `build_wordpress_payload(root: Path, output: Path) -> None`

- [ ] **Step 1: Write failing whole-release tests**

```python
def test_release_has_no_orphans_or_one_way_article_links():
    graph = build_link_graph(CONTENT_ROOT)
    self.assertEqual([], find_orphan_pages(graph, load_manifest(CONTENT_ROOT)))
    self.assertEqual([], find_articles_without_commercial_backlink(graph))


def test_geo_pages_require_real_local_evidence():
    for page in load_pages(CONTENT_ROOT, page_type="geo"):
        self.assertTrue(page.geo_evidence.case_ids or page.geo_evidence.local_facts)
```

- [ ] **Step 2: Run tests and observe incomplete graph failures**

Run: `python -m unittest tools.test_site_content_release -v`

- [ ] **Step 3: Finish article ↔ commercial linking**

Every article links to one primary commercial owner and, where relevant, one protected adjacent service. Every hub lists all its published articles. Each commercial child links back to its hub and to the most relevant article; article anchors describe the topic rather than repeating exact-match keywords unnaturally.

- [ ] **Step 4: Finish case ↔ service linking and case SEO**

For every used case update `cs87_service_url`, keywords, title, description, related cases and FAQ only from verified case facts. Map cases to hub categories and individual service posts through the existing importer payload. A service with no directly matching case may inherit a clearly labelled hub-level project only when its scope contains that work; otherwise the page stays out of the release.

- [ ] **Step 5: Create only proven geo pages**

Intersect accepted geo clusters with case location and local-fact evidence. Generate no page for an empty intersection. Each published city page uses its own case/photo/facts and links to the hub; simple city-name substitution fails validation.

- [ ] **Step 6: Build inventory, link graph and final payloads**

```powershell
python -m tools.site_content.release build-inventory --root seo-content/service-hubs --output seo-content/service-hubs/content-inventory.csv
python -m tools.site_content.release build-links --root seo-content/service-hubs --output seo-content/service-hubs/link-graph.csv
python -m tools.site_content.release build-import --root seo-content/service-hubs --output ftp_dump_minimal/wp-content/themes/land76wp/import/service-hubs-import.json
python -m tools.site_content.release build-case-import --source seo-content/cases/import/cases-seo-import.json --output ftp_dump_minimal/wp-content/themes/land76wp/import/cases-seo-import.json
```

- [ ] **Step 7: Run whole-release validation**

```powershell
python -m tools.site_content.release validate --root seo-content/service-hubs
python -m unittest tools.test_site_content_cases tools.test_site_content_contracts tools.test_site_content_release tools.test_service_v2 tools.test_service_hubs_php -v
```

Expected: zero orphans, zero duplicate owners, zero unverified assets/facts and zero absent architecture pages.

- [ ] **Step 8: Commit and push**

```powershell
git add tools/site_content tools/test_site_content_release.py seo-content/service-hubs seo-content/cases/import/cases-seo-import.json ftp_dump_minimal/wp-content/themes/land76wp/import
git commit -m "feat: integrate articles cases and regional evidence"
git push origin codex/semantic-core
```

---

### Task 12: Full QA, Safe Production Release and Monitoring

**Files:**
- Create: `docs/seo/2026-08-28-service-hubs-release.md`
- Create: `seo-data/2026-08-exp76-services/processed/release-url-status.csv`
- Modify: `seo-data/2026-08-exp76-services/processed/launch_monitoring.csv`
- Modify: `seo-data/2026-08-exp76-services/processed/qa_log.csv`
- Modify: `seo-data/2026-08-exp76-services/README.md`

**Interfaces:**
- Consumes: complete release package and live read-only baseline
- Produces: verified deployment, URL/status/canonical report and 7/14/30/60/90-day monitoring rows

- [ ] **Step 1: Run the complete local verification suite**

```powershell
python -m unittest discover -s tools -p "test_*.py" -v
Get-ChildItem ftp_dump_minimal\wp-content\themes\land76wp\*.php,ftp_dump_minimal\wp-content\themes\land76wp\inc\*.php | ForEach-Object { php -l $_.FullName }
C:\Users\user\.codex\scripts\harness.cmd smoke
git diff --check
```

Expected: all unit tests and PHP lint pass, smoke exits 0, diff check prints nothing.

- [ ] **Step 2: Create the pre-release live baseline**

Read-only record status, canonical, title, H1, indexability and content hash for all eight hubs and all existing URLs that the release may update. Export the exact existing post IDs/slugs/categories/modified dates. Save no cookies or credentials.

- [ ] **Step 3: Back up only changed remote files**

Download the remote versions of each theme file named in the release manifest into a timestamped local backup outside the deploy source directory. Verify the resolved remote paths belong to `/wp-content/themes/land76wp/`; do not recursively move or delete anything.

- [ ] **Step 4: Upload additions before routing changes**

Upload content JSON, rendered HTML, CSS and new importer first; verify remote hashes. Upload modified templates and `functions.php` last. If any hash or PHP syntax check fails, stop before applying the database import and restore only the individual file whose previous version was backed up.

- [ ] **Step 5: Preview and apply the WordPress imports**

Open the authenticated WordPress Tools page, run preview and require zero validation errors/unresolved cases. Apply the exact release ID once. Re-run preview and require `created=0`, `updated=0`, proving idempotence. Then apply the existing case SEO importer and confirm every referenced case resolves.

- [ ] **Step 6: Perform live desktop and mobile QA**

Check every released URL for HTTP 200, self-canonical, unique title/H1/description, correct template, real image, working form, hub breadcrumb, service/article/case links and no PHP/console error. Check grouping category URLs redirect to their hub and categories 87–92 remain unchanged. Separately verify whether each prepared legacy article is actually live so prepared JSON cannot inflate the report. Record results in `release-url-status.csv`.

- [ ] **Step 7: Submit only successful new URLs for indexing**

Add successful 200/self-canonical URLs to the sitemap/indexing workflow. Do not submit failed, redirected, noindex or duplicate URLs. Record the submission date and baseline metrics in `launch_monitoring.csv`.

- [ ] **Step 8: Write the release report**

`docs/seo/2026-08-28-service-hubs-release.md` must list: final counts by hub/service/article/geo/case; every created and updated URL; protected categories unchanged; tests; import preview/apply counts; live QA; rollback backup location; Webmaster baseline; and any page deliberately withheld with its evidence reason.

- [ ] **Step 9: Commit and push the verified release state**

```powershell
git add docs/seo/2026-08-28-service-hubs-release.md seo-data/2026-08-exp76-services/processed seo-data/2026-08-exp76-services/README.md
git commit -m "docs: record service hubs production release"
git push origin codex/semantic-core
git push origin codex/semantic-core:master
```

Expected: branch and master point to the verified release commit; no secret or backup file is tracked.

---

## Continuous Execution Rule

Execute Tasks 1–12 continuously with a fresh implementation review after each task. Pause only for a destructive action, a security boundary, an unavailable production credential at the exact deployment step, or evidence showing that the approved architecture itself must change. Content generation, tests, commits and pushes do not require another confirmation.
