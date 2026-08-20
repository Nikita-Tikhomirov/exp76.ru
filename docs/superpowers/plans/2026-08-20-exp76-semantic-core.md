# Exp76.ru Semantic Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Собрать, очистить и SERP-кластеризовать региональное семантическое ядро для восьми утверждённых услуг exp76.ru и выпустить проверяемую карту `кластер → URL` без изменений живого сайта.

**Architecture:** Все исходные данные сохраняются неизменными в `seo-data/2026-08-exp76-services/raw`, а воспроизводимый Python-конвейер нормализует их, размечает интенты и защищённые пересечения, рассчитывает SERP-overlap и формирует CSV/XLSX-артефакты. Решения о новых страницах принимаются только в итоговом `url_map` после ручной проверки пограничных кластеров; WordPress, FTP и настройки Вебмастера остаются read-only.

**Tech Stack:** Python 3.10+, стандартная библиотека Python (`csv`, `json`, `dataclasses`, `hashlib`, `urllib.parse`, `unittest`), `openpyxl` из bundled workspace runtime, Яндекс Вебмастер, Wordstat, Wordcraft, органическая выдача Яндекса, Git.

**Spec:** `docs/superpowers/specs/2026-08-20-exp76-semantic-strategy-design.md`

## Global Constraints

- Рабочий объём — только восемь URL S1–S8 из спецификации.
- Шесть готовых направлений и все их дочерние URL неизменяемы и получают статус `frozen`.
- Не публиковать страницы, не менять WordPress, FTP, canonical, robots, редиректы или настройки Яндекс Вебмастера.
- Секреты, cookies, пароли и API-ключи не сохранять в проекте, CSV, XLSX, логах или commit.
- Все текстовые файлы сохранять в UTF-8; имена модулей, функций, классов и файлов — только ASCII.
- Исходные выгрузки не переписывать; повторная обработка всегда создаёт новые производные файлы.
- Существующий URL сохраняется по умолчанию; новый URL требует отдельного интента, SERP-доказательства и самостоятельного содержания.
- Геостраница не создаётся только заменой названия города.
- Проверки выполнять через `python -m unittest`; финально запускать `C:\Users\user\.codex\scripts\harness.cmd smoke`.
- Коммиты содержат только файлы текущей задачи и не включают посторонние untracked-файлы пользователя.

---

## File Map

### Конфигурация и данные

- `seo-data/2026-08-exp76-services/scope.json` — единственный источник истины по восьми услугам, географии и защищённым кластерам.
- `seo-data/2026-08-exp76-services/seeds.json` — проверяемые seed-маски по услугам.
- `seo-data/2026-08-exp76-services/raw/source-manifest.json` — контрольные суммы, даты и происхождение исходных выгрузок.
- `seo-data/2026-08-exp76-services/raw/webmaster/*.csv` — неизменённые выгрузки Вебмастера.
- `seo-data/2026-08-exp76-services/raw/wordstat/*.csv` — неизменённые выгрузки Wordstat.
- `seo-data/2026-08-exp76-services/raw/wordcraft/*.csv` — выгрузки или нормализованные read-only снимки Wordcraft.
- `seo-data/2026-08-exp76-services/raw/serp/*.jsonl` — органический топ Яндекса с регионом, устройством и датой.
- `seo-data/2026-08-exp76-services/processed/keywords_raw.csv` — объединённые исходные фразы.
- `seo-data/2026-08-exp76-services/processed/keywords_clean.csv` — нормализация, интент, релевантность и исключения.
- `seo-data/2026-08-exp76-services/processed/minus_words.csv` — глобальные и сервисные минус-слова с причиной.
- `seo-data/2026-08-exp76-services/processed/serp_results.csv` — канонические результаты выдачи.
- `seo-data/2026-08-exp76-services/processed/clusters.csv` — итоговые кластеры.
- `seo-data/2026-08-exp76-services/processed/url_map.csv` — решение по URL.
- `seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx` — итоговая рабочая книга.
- `seo-data/2026-08-exp76-services/README.md` — происхождение данных, команды воспроизведения и ограничения.

### Код

- `tools/seo_semantics/__init__.py` — публичные экспорты пакета.
- `tools/seo_semantics/models.py` — dataclass-модели и фиксированные поля.
- `tools/seo_semantics/scope.py` — чтение и проверка `scope.json`.
- `tools/seo_semantics/normalize.py` — нормализация фраз и единиц измерения.
- `tools/seo_semantics/ingest.py` — импорт CSV разных источников в единый формат.
- `tools/seo_semantics/classify.py` — интенты, исключения и `frozen_collision`.
- `tools/seo_semantics/manifest.py` — SHA-256 и регистрация исходных файлов.
- `tools/seo_semantics/serp.py` — канонизация результатов и расчёт overlap.
- `tools/seo_semantics/workbook.py` — создание CSV/XLSX и QA-листов.
- `tools/seo_semantics/cli.py` — команды `validate-scope`, `register-source`, `ingest`, `classify`, `cluster`, `export`, `qa`.

### Тесты

- `tools/test_semantic_scope.py`;
- `tools/test_semantic_normalize.py`;
- `tools/test_semantic_ingest.py`;
- `tools/test_semantic_classify.py`;
- `tools/test_semantic_manifest.py`;
- `tools/test_semantic_serp.py`;
- `tools/test_semantic_workbook.py`.

---

### Task 1: Scope Manifest and Safety Boundary

**Files:**
- Create: `seo-data/2026-08-exp76-services/scope.json`
- Create: `seo-data/2026-08-exp76-services/README.md`
- Create: `tools/seo_semantics/__init__.py`
- Create: `tools/seo_semantics/scope.py`
- Create: `tools/test_semantic_scope.py`

**Interfaces:**
- Produces: `load_scope(path: Path) -> ScopeConfig`
- Produces: `ScopeConfig.services: tuple[ServiceScope, ...]`
- Produces: `ScopeConfig.frozen_urls: frozenset[str]`
- Produces: `ScopeConfig.regions: tuple[RegionScope, ...]`
- Consumes: no earlier task interfaces

- [ ] **Step 1: Write the failing scope tests**

```python
import unittest
from pathlib import Path

from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT / "seo-data/2026-08-exp76-services/scope.json"


class SemanticScopeTest(unittest.TestCase):
    def test_scope_contains_exactly_the_approved_services(self):
        scope = load_scope(SCOPE)
        self.assertEqual(
            {service.service_id for service in scope.services},
            {"S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"},
        )
        self.assertEqual(len(scope.services), 8)

    def test_scope_freezes_the_six_existing_category_hubs(self):
        scope = load_scope(SCOPE)
        self.assertEqual(len(scope.frozen_urls), 6)
        self.assertIn("https://exp76.ru/category/drenazh-uchastka/", scope.frozen_urls)
        self.assertIn("https://exp76.ru/category/avtopoliv-na-uchastke/", scope.frozen_urls)

    def test_scope_rejects_duplicate_urls(self):
        scope = load_scope(SCOPE)
        urls = [service.current_url for service in scope.services]
        self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and confirm the missing-module failure**

Run:

```powershell
python -m unittest tools.test_semantic_scope -v
```

Expected: `ModuleNotFoundError: No module named 'tools.seo_semantics'`.

- [ ] **Step 3: Create the exact scope configuration**

`scope.json` must use this structure and these exact service IDs/URLs:

```json
{
  "site": "https://exp76.ru/",
  "services": [
    {"service_id": "S1", "name": "Ландшафтное проектирование", "current_url": "https://exp76.ru/services/landshaftnoe-proektirovanie/"},
    {"service_id": "S2", "name": "Газон посевной и рулонный", "current_url": "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/"},
    {"service_id": "S3", "name": "Посадка деревьев и кустарников", "current_url": "https://exp76.ru/services/posadka-derevev-i-kustarnikov/"},
    {"service_id": "S4", "name": "Уход за садом", "current_url": "https://exp76.ru/services/ukhod-za-sadom/"},
    {"service_id": "S5", "name": "Планировка территории", "current_url": "https://exp76.ru/services/planirovka-territorii/"},
    {"service_id": "S6", "name": "Подпорные стенки", "current_url": "https://exp76.ru/services/podpornye-stenki/"},
    {"service_id": "S7", "name": "Уличное и ландшафтное освещение участка", "current_url": "https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/"},
    {"service_id": "S8", "name": "Въезд и заезд на участок через канаву", "current_url": "https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/"}
  ],
  "frozen_urls": [
    "https://exp76.ru/category/drenazh-uchastka/",
    "https://exp76.ru/category/otmostka-vokrug-doma/",
    "https://exp76.ru/category/ukladka-trotuarnoy-plitki/",
    "https://exp76.ru/category/osushenie-uchastka/",
    "https://exp76.ru/category/livnevaya-kanalizatsiya/",
    "https://exp76.ru/category/avtopoliv-na-uchastke/"
  ],
  "regions": [
    {"name": "Ярославль", "wordstat_id": 16, "priority": 1},
    {"name": "Ярославская область", "wordstat_id": 10841, "priority": 2},
    {"name": "Рыбинск", "wordstat_id": null, "priority": 3},
    {"name": "Тутаев", "wordstat_id": null, "priority": 4},
    {"name": "Углич", "wordstat_id": null, "priority": 5},
    {"name": "Переславль-Залесский", "wordstat_id": null, "priority": 6}
  ]
}
```

`scope.py` must define immutable `ServiceScope`, `RegionScope`, and `ScopeConfig` dataclasses, require exactly S1–S8, reject duplicate URLs, require HTTPS URLs ending in `/`, and require exactly the six frozen category URLs.

- [ ] **Step 4: Document the read-only boundary**

In `README.md`, record:

- the exact eight services;
- the six frozen category hubs;
- that raw files are immutable;
- that the phase never writes to WordPress, FTP or Yandex settings;
- the commands that later tasks add to the CLI;
- that secrets are prohibited in the directory.

- [ ] **Step 5: Run the scope tests**

Run:

```powershell
python -m unittest tools.test_semantic_scope -v
```

Expected: three tests pass.

- [ ] **Step 6: Commit Task 1**

```powershell
git add seo-data/2026-08-exp76-services/scope.json seo-data/2026-08-exp76-services/README.md tools/seo_semantics/__init__.py tools/seo_semantics/scope.py tools/test_semantic_scope.py
git commit -m "feat: define semantic core scope"
```

---

### Task 2: Normalized Keyword Model and Source Ingestion

**Files:**
- Create: `tools/seo_semantics/models.py`
- Create: `tools/seo_semantics/normalize.py`
- Create: `tools/seo_semantics/ingest.py`
- Create: `tools/test_semantic_normalize.py`
- Create: `tools/test_semantic_ingest.py`
- Create: `seo-data/2026-08-exp76-services/raw/.gitkeep`
- Create: `seo-data/2026-08-exp76-services/processed/.gitkeep`

**Interfaces:**
- Consumes: `ScopeConfig` from Task 1
- Produces: `normalize_query(value: str) -> str`
- Produces: `KeywordRecord`
- Produces: `load_source_csv(path: Path, source: str, column_map: dict[str, str]) -> list[KeywordRecord]`
- Produces: `merge_records(records: Iterable[KeywordRecord]) -> list[KeywordRecord]`

- [ ] **Step 1: Write failing normalization tests**

```python
import unittest

from tools.seo_semantics.normalize import normalize_query


class SemanticNormalizeTest(unittest.TestCase):
    def test_normalizes_case_yo_spacing_and_square_meters(self):
        self.assertEqual(
            normalize_query("  Цена Ёлочного газона 100 м²  "),
            "цена елочного газона 100 м2",
        )

    def test_preserves_numbers_cities_and_commercial_modifiers(self):
        self.assertEqual(
            normalize_query("Въезд 6 метров под ключ — Ярославль"),
            "въезд 6 метров под ключ ярославль",
        )

    def test_collapses_equivalent_area_notation(self):
        self.assertEqual(normalize_query("газон 50 кв. м"), "газон 50 м2")
```

- [ ] **Step 2: Write failing ingestion tests**

```python
import csv
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.ingest import load_source_csv, merge_records


class SemanticIngestTest(unittest.TestCase):
    def test_preserves_raw_query_and_source_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "webmaster.csv"
            with path.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["query", "shows", "clicks", "url"])
                writer.writeheader()
                writer.writerow({"query": "Въезд через канаву", "shows": "60", "clicks": "12", "url": "https://exp76.ru/services/x/"})
            records = load_source_csv(
                path,
                source="webmaster",
                column_map={"query": "query", "impressions": "shows", "clicks": "clicks", "current_url": "url"},
            )
            self.assertEqual(records[0].query_raw, "Въезд через канаву")
            self.assertEqual(records[0].impressions, 60)
            self.assertEqual(records[0].clicks, 12)
            self.assertEqual(records[0].source, "webmaster")

    def test_merge_keeps_one_normalized_row_and_all_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = []
            for index, (source, query) in enumerate(
                (("webmaster", "Газон под ключ"), ("wordstat", "газон  под ключ")),
                start=1,
            ):
                path = Path(tmp) / f"source-{index}.csv"
                with path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["query"])
                    writer.writeheader()
                    writer.writerow({"query": query})
                records.extend(
                    load_source_csv(path, source=source, column_map={"query": "query"})
                )
            merged = merge_records(records)
            self.assertEqual(len(merged), 1)
            self.assertEqual(merged[0].sources, ("webmaster", "wordstat"))
```

- [ ] **Step 3: Run both test modules and confirm failures**

Run:

```powershell
python -m unittest tools.test_semantic_normalize tools.test_semantic_ingest -v
```

Expected: imports fail because the modules do not exist.

- [ ] **Step 4: Implement the immutable record model**

`models.py` must define:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class KeywordRecord:
    query_raw: str
    query_normalized: str
    source: str
    seed: str = ""
    region: str = ""
    device: str = "all"
    broad_frequency: int | None = None
    phrase_frequency: int | None = None
    exact_frequency: int | None = None
    impressions: int | None = None
    clicks: int | None = None
    ctr: float | None = None
    avg_position: float | None = None
    current_url: str = ""
    collected_at: str = ""
    sources: tuple[str, ...] = field(default_factory=tuple)
```

`normalize.py` must use `unicodedata.normalize("NFKC", value)`, lowercase text, replace `ё` with `е`, normalize `м²`, `м2`, `кв. м` to `м2`, replace punctuation with spaces, and collapse whitespace. It must not remove digits, city names or commercial modifiers.

`ingest.py` must:

- accept UTF-8 and UTF-8 BOM CSV;
- reject a missing query column with a message naming the file and expected column;
- parse empty metrics as `None`;
- reject negative impressions/clicks/frequencies;
- retain `query_raw` and calculate `query_normalized`;
- merge exact normalized duplicates while preserving sorted unique `sources`;
- never add metrics from different source methodologies together.

- [ ] **Step 5: Run the normalization and ingestion tests**

Run:

```powershell
python -m unittest tools.test_semantic_normalize tools.test_semantic_ingest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 2**

```powershell
git add tools/seo_semantics/models.py tools/seo_semantics/normalize.py tools/seo_semantics/ingest.py tools/test_semantic_normalize.py tools/test_semantic_ingest.py seo-data/2026-08-exp76-services/raw/.gitkeep seo-data/2026-08-exp76-services/processed/.gitkeep
git commit -m "feat: add semantic keyword ingestion"
```

---

### Task 3: Seed Matrix and Raw Source Manifest

**Files:**
- Create: `seo-data/2026-08-exp76-services/seeds.json`
- Create: `tools/seo_semantics/manifest.py`
- Create: `tools/seo_semantics/cli.py`
- Create: `tools/test_semantic_manifest.py`
- Modify: `seo-data/2026-08-exp76-services/README.md`

**Interfaces:**
- Consumes: `ScopeConfig` from Task 1
- Produces: `register_source(path: Path, source: str, collected_at: str, manifest_path: Path) -> SourceManifestEntry`
- Produces: CLI `validate-scope` and `register-source`

- [ ] **Step 1: Write the failing manifest test**

```python
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.seo_semantics.manifest import register_source


class SemanticManifestTest(unittest.TestCase):
    def test_register_source_records_relative_path_sha_and_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_file = root / "raw.csv"
            source_file.write_text("query\nгазон\n", encoding="utf-8")
            manifest = root / "manifest.json"
            entry = register_source(source_file, "wordstat", "2026-08-20T12:00:00+03:00", manifest)
            expected_sha = hashlib.sha256(source_file.read_bytes()).hexdigest()
            self.assertEqual(entry.sha256, expected_sha)
            self.assertEqual(entry.source, "wordstat")
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(saved["files"][0]["sha256"], expected_sha)

    def test_register_source_rejects_secret_like_filenames(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "yandex-password.csv"
            path.write_text("query\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret-like filename"):
                register_source(path, "wordstat", "2026-08-20T12:00:00+03:00", root / "manifest.json")
```

- [ ] **Step 2: Run the manifest test and confirm failure**

Run:

```powershell
python -m unittest tools.test_semantic_manifest -v
```

Expected: import failure for `tools.seo_semantics.manifest`.

- [ ] **Step 3: Create the complete seed matrix**

`seeds.json` must map every service ID to these initial masks:

```json
{
  "S1": ["ландшафтное проектирование участка", "ландшафтный дизайн участка", "проект благоустройства участка", "дизайн проект участка"],
  "S2": ["газон под ключ", "рулонный газон", "укладка рулонного газона", "посевной газон", "устройство газона", "восстановление газона"],
  "S3": ["посадка деревьев", "посадка кустарников", "посадка хвойных", "озеленение участка", "посадка крупномеров"],
  "S4": ["уход за садом", "садовник на участок", "обслуживание сада", "обрезка деревьев", "обрезка кустарников", "сезонный уход за садом"],
  "S5": ["планировка участка", "планировка территории", "выравнивание участка", "вертикальная планировка участка", "поднять участок грунтом", "планировка грунта"],
  "S6": ["подпорная стенка на участке", "строительство подпорной стенки", "устройство подпорной стенки", "подпорная стенка из бетона", "подпорная стенка из блоков", "подпорная стенка из габионов"],
  "S7": ["освещение участка", "ландшафтное освещение", "уличное освещение частного дома", "монтаж освещения участка", "подсветка дорожек", "подсветка участка"],
  "S8": ["въезд через канаву", "заезд через канаву", "заезд на участок", "въезд на участок", "труба в канаву для заезда", "обустройство въезда на участок"]
}
```

Do not remove `посадка крупномеров`, materials for retaining walls, or seasonal garden care during collection. They are hypotheses and must remain until Wordstat, SERP and business evidence are evaluated.

- [ ] **Step 4: Implement manifest registration and CLI commands**

`manifest.py` must calculate SHA-256, store relative POSIX paths, source, byte count and ISO-8601 timestamp, sort entries by path, and reject filenames containing `password`, `passwd`, `secret`, `token`, `cookie`, `credential`, `пароль` or `токен` case-insensitively.

`cli.py` must expose:

```powershell
python -m tools.seo_semantics.cli validate-scope --scope seo-data/2026-08-exp76-services/scope.json
python -m tools.seo_semantics.cli register-source --file <path> --source webmaster --collected-at <ISO-8601> --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json
```

Both commands must return exit code 0 on success and a non-zero code with a concise stderr message on invalid input.

- [ ] **Step 5: Run manifest and scope tests**

Run:

```powershell
python -m unittest tools.test_semantic_scope tools.test_semantic_manifest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit Task 3**

```powershell
git add seo-data/2026-08-exp76-services/seeds.json seo-data/2026-08-exp76-services/README.md tools/seo_semantics/manifest.py tools/seo_semantics/cli.py tools/test_semantic_manifest.py
git commit -m "feat: add semantic source manifest"
```

---

### Task 4: Read-Only Yandex Data Acquisition and Unified Ingestion

**Files:**
- Create: `seo-data/2026-08-exp76-services/raw/webmaster/`
- Create: `seo-data/2026-08-exp76-services/raw/wordstat/`
- Create: `seo-data/2026-08-exp76-services/raw/wordcraft/`
- Create: `seo-data/2026-08-exp76-services/raw/source-manifest.json`
- Modify: `tools/seo_semantics/cli.py`
- Modify: `seo-data/2026-08-exp76-services/README.md`
- Create: `seo-data/2026-08-exp76-services/processed/keywords_raw.csv`

**Interfaces:**
- Consumes: `load_source_csv`, `merge_records`, `register_source`, `scope.json`, `seeds.json`
- Produces: CLI `ingest`
- Produces: UTF-8 CSV `processed/keywords_raw.csv`

- [ ] **Step 1: Load the Browser skill and select the existing authenticated Yandex browser**

Read `browser:control-in-app-browser` before browser interaction. Reuse the existing Yandex session if it is still authenticated. If authentication expired, stop at the Yandex sign-in page and ask the user to complete the code challenge; do not inspect cookies or browser storage.

- [ ] **Step 2: Export actual site queries from Yandex Webmaster**

For `https://exp76.ru/`, collect read-only CSV exports for:

- the longest available whole-site period;
- the last 90 days;
- the last 30 days;
- each of the eight S1–S8 URLs where the interface supports URL filtering.

Required metrics: query, URL, date or period, region when available, device when available, impressions, clicks, CTR and average position. Save each downloaded file unchanged under `raw/webmaster/` with ASCII filenames such as `site-90d-2026-08-20.csv` and `s8-90d-2026-08-20.csv`.

- [ ] **Step 3: Collect Wordcraft query suggestions**

Run Wordcraft for each of the eight current URLs and for the principal seed of each service. Use Ярославская область and all devices for the main pass; record a separate mobile pass only for the highest-priority commercial groups S8, S5 and S2. If the UI offers an export, save it unchanged. If it does not, capture the visible table into a CSV with columns `query,demand,clicks,competition,yandex_cluster,source_url,region,device,collected_at`; do not copy snippets or competitor content.

- [ ] **Step 4: Collect Wordstat exports**

For every seed in `seeds.json`, collect:

- region Ярославль;
- region Ярославская область;
- all devices;
- broad results;
- phrase and exact checks for the commercially relevant head terms;
- dynamics for every principal service head term.

Run explicit geographic variants for Рыбинск, Тутаев, Углич and Переславль-Залесский. Use Russia only to discover missing synonyms and seasonal patterns; mark those rows `region=Russia_discovery` so they cannot drive a local page by themselves.

If manual collection exceeds 250 cleaned candidate queries requiring SERP checks, stop before paid/API activation, report the count, and request a separate user decision on Yandex Cloud. Do not accept Cloud terms or enable billing autonomously.

- [ ] **Step 5: Register every raw source**

For every downloaded or captured file run:

```powershell
python -m tools.seo_semantics.cli register-source --file <raw-file> --source <webmaster|wordstat|wordcraft> --collected-at 2026-08-20T00:00:00+03:00 --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json
```

Replace the example timestamp with the real capture time. Verify that each raw file has exactly one manifest entry and that no filename contains secret-like words.

- [ ] **Step 6: Add and run the unified ingest command**

`cli.py ingest` must read the registered source files using explicit per-source column maps and write stable, sorted UTF-8 CSV with these columns:

```text
keyword_id,query_raw,query_normalized,sources,seed,region,device,broad_frequency,phrase_frequency,exact_frequency,impressions,clicks,ctr,avg_position,current_url,collected_at
```

Run:

```powershell
python -m tools.seo_semantics.cli ingest --scope seo-data/2026-08-exp76-services/scope.json --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json --output seo-data/2026-08-exp76-services/processed/keywords_raw.csv
```

Expected: exit code 0; no exact duplicate `query_normalized + region + device + current_url` rows; every row has at least one source.

- [ ] **Step 7: Run ingestion regression tests**

Run:

```powershell
python -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit Task 4**

```powershell
git add seo-data/2026-08-exp76-services/raw seo-data/2026-08-exp76-services/processed/keywords_raw.csv seo-data/2026-08-exp76-services/README.md tools/seo_semantics/cli.py
git commit -m "feat: collect raw semantic demand"
```

---

### Task 5: Intent Classification and Frozen-Collision Protection

**Files:**
- Create: `tools/seo_semantics/classify.py`
- Create: `tools/test_semantic_classify.py`
- Modify: `tools/seo_semantics/cli.py`
- Create: `seo-data/2026-08-exp76-services/processed/keywords_clean.csv`
- Create: `seo-data/2026-08-exp76-services/processed/frozen_collisions.csv`
- Create: `seo-data/2026-08-exp76-services/processed/minus_words.csv`

**Interfaces:**
- Consumes: `KeywordRecord`, `ScopeConfig`, `keywords_raw.csv`
- Produces: `classify_query(query: str, service_hint: str, scope: ScopeConfig) -> QueryClassification`
- Produces: `QueryClassification(intent, service_id, relevance, exclusion_reason, frozen_collision, geo, entities)`
- Produces: CLI `classify`

- [ ] **Step 1: Write failing classification tests**

```python
import unittest
from pathlib import Path

from tools.seo_semantics.classify import classify_query
from tools.seo_semantics.scope import load_scope


ROOT = Path(__file__).resolve().parents[1]
SCOPE = load_scope(ROOT / "seo-data/2026-08-exp76-services/scope.json")


class SemanticClassifyTest(unittest.TestCase):
    def test_assigns_commercial_service_query(self):
        result = classify_query("въезд через канаву под ключ ярославль", "S8", SCOPE)
        self.assertEqual(result.intent, "transactional")
        self.assertEqual(result.service_id, "S8")
        self.assertFalse(result.frozen_collision)

    def test_protects_existing_autopoliv_cluster(self):
        result = classify_query("монтаж автополива газона", "S2", SCOPE)
        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.owner_url, "https://exp76.ru/category/avtopoliv-na-uchastke/")

    def test_protects_existing_livnevka_cluster(self):
        result = classify_query("ливневка под въездом на участок", "S8", SCOPE)
        self.assertTrue(result.frozen_collision)
        self.assertEqual(result.owner_url, "https://exp76.ru/category/livnevaya-kanalizatsiya/")

    def test_marks_jobs_as_irrelevant(self):
        result = classify_query("работа садовником вакансии", "S4", SCOPE)
        self.assertEqual(result.intent, "irrelevant")
        self.assertEqual(result.exclusion_reason, "jobs")
```

- [ ] **Step 2: Run the classification test and confirm failure**

Run:

```powershell
python -m unittest tools.test_semantic_classify -v
```

Expected: import failure for `tools.seo_semantics.classify`.

- [ ] **Step 3: Implement deterministic first-pass classification**

`classify.py` must use explicit keyword sets for:

- transactional: `цена`, `стоимость`, `заказать`, `под ключ`, `монтаж`, `устройство`, `строительство`, `услуги`;
- informational: `как`, `своими руками`, `схема`, `нормы`, `ошибки`, `инструкция`;
- jobs: `вакансия`, `работа`, `зарплата`, `резюме`;
- training: `курс`, `обучение`, `диплом`;
- frozen drainage/dewatering: `дренаж`, `грунтовые воды`, `осушение`, `заболоченный`;
- frozen storm sewer: `ливневка`, `ливневая канализация`, `дождеприемник`, `линейный водоотвод`;
- frozen blind area: `отмостка`;
- frozen paving: `тротуарная плитка`, `брусчатка`, `мощение`;
- frozen irrigation: `автополив`, `автоматический полив`, `капельный полив`.

The classifier must preserve ambiguous mixed queries for manual review instead of excluding them. Example: `планировка участка с уклоном и дренажом` gets `service_id=S5`, `frozen_collision=true`, `relevance=manual_review`, and the drainage owner URL.

- [ ] **Step 4: Add and run the classify command**

Run:

```powershell
python -m tools.seo_semantics.cli classify --scope seo-data/2026-08-exp76-services/scope.json --input seo-data/2026-08-exp76-services/processed/keywords_raw.csv --output seo-data/2026-08-exp76-services/processed/keywords_clean.csv --frozen-output seo-data/2026-08-exp76-services/processed/frozen_collisions.csv --minus-output seo-data/2026-08-exp76-services/processed/minus_words.csv
```

Required clean columns:

```text
keyword_id,query_raw,query_normalized,service_id,intent,relevance,exclusion_reason,geo,entities,frozen_collision,owner_url,sources,region,device,broad_frequency,phrase_frequency,exact_frequency,impressions,clicks,avg_position,current_url
```

Expected: every input row appears in exactly one of `keywords_clean.csv` or `frozen_collisions.csv`; exclusions retain an explicit reason.

The same command must also write `processed/minus_words.csv` with fields `scope,service_id,word,reason,source_query_ids,status`. Global exclusions such as jobs and training use `scope=global`; service-specific exclusions retain their service ID. A word is never added only because it appeared in one ambiguous query.

- [ ] **Step 5: Manually review all clicked and ambiguous queries**

Review 100% of rows where `clicks > 0`, `relevance=manual_review`, or `frozen_collision=true`. Record the final decision in the CSV without deleting the original query or source columns. No clicked query may remain unassigned.

- [ ] **Step 6: Run classification regression tests**

Run:

```powershell
python -m unittest tools.test_semantic_classify tools.test_semantic_normalize tools.test_semantic_ingest -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit Task 5**

```powershell
git add tools/seo_semantics/classify.py tools/seo_semantics/cli.py tools/test_semantic_classify.py seo-data/2026-08-exp76-services/processed/keywords_clean.csv seo-data/2026-08-exp76-services/processed/frozen_collisions.csv seo-data/2026-08-exp76-services/processed/minus_words.csv
git commit -m "feat: classify semantic search intent"
```

---

### Task 6: SERP Capture and Page-Level Clustering

**Files:**
- Create: `tools/seo_semantics/serp.py`
- Create: `tools/test_semantic_serp.py`
- Modify: `tools/seo_semantics/cli.py`
- Create: `seo-data/2026-08-exp76-services/raw/serp/`
- Create: `seo-data/2026-08-exp76-services/processed/serp_results.csv`
- Create: `seo-data/2026-08-exp76-services/processed/clusters.csv`
- Create: `seo-data/2026-08-exp76-services/processed/url_map.csv`

**Interfaces:**
- Consumes: `keywords_clean.csv`, `ScopeConfig`
- Produces: `canonicalize_serp_url(url: str) -> str`
- Produces: `overlap_count(left: Sequence[str], right: Sequence[str]) -> int`
- Produces: `decide_cluster(overlap: int, same_intent: bool) -> Literal["merge", "manual_review", "split"]`
- Produces: CLI `cluster`

- [ ] **Step 1: Write failing SERP tests**

```python
import unittest

from tools.seo_semantics.serp import canonicalize_serp_url, decide_cluster, overlap_count


class SemanticSerpTest(unittest.TestCase):
    def test_canonicalizes_protocol_www_query_and_fragment(self):
        self.assertEqual(
            canonicalize_serp_url("http://www.example.ru/path/?utm_source=x#part"),
            "https://example.ru/path/",
        )

    def test_overlap_uses_unique_canonical_urls(self):
        left = ["https://a.ru/x", "https://b.ru/y", "https://c.ru/z", "https://d.ru/q"]
        right = ["http://www.a.ru/x/", "https://b.ru/y?x=1", "https://c.ru/z", "https://d.ru/q#x"]
        self.assertEqual(overlap_count(left, right), 4)

    def test_cluster_thresholds_follow_the_spec(self):
        self.assertEqual(decide_cluster(4, True), "merge")
        self.assertEqual(decide_cluster(3, True), "manual_review")
        self.assertEqual(decide_cluster(1, True), "split")
        self.assertEqual(decide_cluster(5, False), "manual_review")
```

- [ ] **Step 2: Run the SERP test and confirm failure**

Run:

```powershell
python -m unittest tools.test_semantic_serp -v
```

Expected: import failure for `tools.seo_semantics.serp`.

- [ ] **Step 3: Implement URL canonicalization and thresholds**

`canonicalize_serp_url` must:

- lowercase the hostname;
- remove `www.`;
- normalize scheme to `https` for comparison only;
- remove query strings and fragments;
- collapse duplicate slashes;
- preserve the path and add one trailing slash;
- reject non-HTTP(S) URLs.

`decide_cluster` must return:

- `merge` for overlap at least 4 and matching intent;
- `manual_review` for overlap 2–3;
- `manual_review` for overlap at least 4 with differing intent;
- `split` for overlap 0–1.

- [ ] **Step 4: Build the representative-query queue**

For every tentative service group select:

- the most frequent commercial head query;
- the strongest `цена/стоимость` query;
- the strongest `под ключ/заказать` query;
- the strongest Yaroslavl geographic query;
- every query that already has clicks;
- every phrase proposed as a separate new page.

Write the queue to `raw/serp/serp-queue.csv` with columns:

```text
query_id,query,service_id,intent,region,device,reason,status
```

Use `region=Yaroslavl`, `device=desktop` for the main pass. Add mobile checks for S8, S5 and S2 head clusters.

- [ ] **Step 5: Capture organic Yandex results read-only**

For each queue row, save one JSONL record:

```json
{"query_id":"Q000001","query":"въезд через канаву под ключ","region":"Yaroslavl","device":"desktop","checked_at":"2026-08-20T12:00:00+03:00","results":[{"rank":1,"url":"https://example.ru/path/","title":"Example"}]}
```

Keep only organic HTTP(S) results. Do not include ads, maps, snippets, page text, cookies or account data. If more than 250 queue rows remain, stop and request Yandex Cloud/API activation rather than scraping at uncontrolled scale.

- [ ] **Step 6: Run clustering and generate the URL map**

Run:

```powershell
python -m tools.seo_semantics.cli cluster --scope seo-data/2026-08-exp76-services/scope.json --keywords seo-data/2026-08-exp76-services/processed/keywords_clean.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp --serp-output seo-data/2026-08-exp76-services/processed/serp_results.csv --clusters-output seo-data/2026-08-exp76-services/processed/clusters.csv --url-map-output seo-data/2026-08-exp76-services/processed/url_map.csv
```

`clusters.csv` fields:

```text
cluster_id,service_id,cluster_name,head_query,query_ids,intent,geo_scope,broad_frequency,phrase_frequency,exact_frequency,seasonality,webmaster_impressions,webmaster_clicks,serp_cohesion,target_url,url_action,priority,confidence,rationale
```

`url_action` is one of `keep_enhance`, `new_child_candidate`, `merge_candidate`, `article_candidate`, `exclude`, `frozen_owner`. No redirect or indexation action is executed.

- [ ] **Step 7: Manually review every non-automatic decision**

Review:

- all `manual_review` overlap decisions;
- all `new_child_candidate` rows;
- all clusters with clicked queries;
- all potential city pages;
- all clusters touching S5, S6 or S8 and a frozen water-management topic.

Record the final decision, reviewer and reasoning in `clusters.csv` and `url_map.csv`.

- [ ] **Step 8: Run SERP and classification regression tests**

Run:

```powershell
python -m unittest tools.test_semantic_serp tools.test_semantic_classify -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit Task 6**

```powershell
git add tools/seo_semantics/serp.py tools/seo_semantics/cli.py tools/test_semantic_serp.py seo-data/2026-08-exp76-services/raw/serp seo-data/2026-08-exp76-services/processed/serp_results.csv seo-data/2026-08-exp76-services/processed/clusters.csv seo-data/2026-08-exp76-services/processed/url_map.csv
git commit -m "feat: cluster semantic search results"
```

---

### Task 7: Verified XLSX Deliverable and Content Briefs

**Files:**
- Create: `tools/seo_semantics/workbook.py`
- Create: `tools/test_semantic_workbook.py`
- Modify: `tools/seo_semantics/cli.py`
- Create: `seo-data/2026-08-exp76-services/processed/scope_urls.csv`
- Create: `seo-data/2026-08-exp76-services/processed/content_briefs.csv`
- Create: `seo-data/2026-08-exp76-services/processed/launch_monitoring.csv`
- Create: `seo-data/2026-08-exp76-services/processed/qa_log.csv`
- Create: `seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx`

**Interfaces:**
- Consumes: all processed CSV files from Tasks 4–6
- Produces: `build_workbook(data_dir: Path, output_path: Path) -> None`
- Produces: `validate_workbook(path: Path) -> list[str]`
- Produces: CLI `export` and `qa`

- [ ] **Step 1: Load the Spreadsheets skill and bundled dependencies**

Read `spreadsheets:Spreadsheets`, then call the workspace dependency loader to obtain the supported Python and `openpyxl` runtime. Do not install a new dependency when the bundled runtime already provides it.

- [ ] **Step 2: Write the failing workbook test**

```python
import tempfile
import unittest
from pathlib import Path

from openpyxl import load_workbook

from tools.seo_semantics.workbook import build_workbook, validate_workbook


class SemanticWorkbookTest(unittest.TestCase):
    def test_workbook_contains_required_sheets_and_freeze_panes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture_dir = root / "processed"
            fixture_dir.mkdir()
            for name in (
                "scope_urls", "keywords_raw", "keywords_clean", "minus_words",
                "frozen_collisions", "serp_results", "clusters", "url_map",
                "content_briefs", "launch_monitoring", "qa_log"
            ):
                (fixture_dir / f"{name}.csv").write_text("id,value\n1,test\n", encoding="utf-8")
            output = root / "semantic.xlsx"
            build_workbook(fixture_dir, output)
            workbook = load_workbook(output, read_only=False)
            self.assertEqual(
                set(workbook.sheetnames),
                {"scope_urls", "keywords_raw", "keywords_clean", "minus_words", "frozen_collisions", "serp_results", "clusters", "url_map", "content_briefs", "launch_monitoring", "qa_log"},
            )
            self.assertEqual(workbook["clusters"].freeze_panes, "A2")
            self.assertEqual(validate_workbook(output), [])
```

- [ ] **Step 3: Run the workbook test and confirm failure**

Run with the bundled Python runtime:

```powershell
<bundled-python> -m unittest tools.test_semantic_workbook -v
```

Expected: import failure for `tools.seo_semantics.workbook`.

- [ ] **Step 4: Create content and monitoring tables**

`scope_urls.csv` fields:

```text
service_id,service_name,current_url,current_status,current_canonical,current_template,webmaster_impressions,webmaster_clicks,frozen,notes
```

Populate it from `scope.json`, the read-only live audit, and aggregated Webmaster metrics.

`content_briefs.csv` fields:

```text
cluster_id,target_url,page_type,primary_query,secondary_queries,title_intent,h1_intent,required_sections,price_factors,case_ids,photo_ids,internal_links,frozen_links,missing_facts,status
```

`launch_monitoring.csv` fields:

```text
cluster_id,target_url,launch_date,baseline_28d_impressions,baseline_clicks,baseline_ctr,baseline_position,day_7,day_14,day_30,day_60,day_90,leads,calls,decision
```

`qa_log.csv` fields:

```text
check_id,cluster_id,check,status,evidence,issue,resolution
```

Populate content briefs from the accepted cluster and URL map. Use only existing case/photo IDs that can be traced to WordPress; leave `missing_facts` explicit when a claim lacks evidence.

- [ ] **Step 5: Implement workbook formatting and validation**

The workbook must:

- contain exactly the eleven sheets in the test;
- freeze row 1 and enable filters on every sheet;
- use bold dark-green headers with white text;
- wrap long text columns and cap widths at 60 characters;
- apply red fill to `frozen_collision=true`, yellow fill to manual review rows, green fill to accepted clusters;
- format CTR as percentage and numeric metrics as numbers;
- keep URLs as clickable hyperlinks;
- contain no formulas that reference external workbooks;
- contain no secrets or credentials.

`validate_workbook` must report missing sheets, duplicate cluster owners, blank target URLs for accepted commercial clusters, clicked queries without cluster IDs, and frozen collisions assigned to a new URL.

- [ ] **Step 6: Generate and validate the workbook**

Run:

```powershell
<bundled-python> -m tools.seo_semantics.cli export --processed-dir seo-data/2026-08-exp76-services/processed --output seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
<bundled-python> -m tools.seo_semantics.cli qa --scope seo-data/2026-08-exp76-services/scope.json --processed-dir seo-data/2026-08-exp76-services/processed --workbook seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
```

Expected: QA exits 0 and prints `semantic QA passed`.

- [ ] **Step 7: Render or reopen the workbook for visual verification**

Use the spreadsheet skill's required verification path to inspect all sheet headers, frozen panes, filters, wrapped cells, hyperlinks and conditional formatting. Correct clipped headers, unreadable widths and broken hyperlinks before delivery.

- [ ] **Step 8: Run workbook and full semantic tests**

Run:

```powershell
<bundled-python> -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest tools.test_semantic_classify tools.test_semantic_serp tools.test_semantic_workbook -v
```

Expected: all tests pass.

- [ ] **Step 9: Commit Task 7**

```powershell
git add tools/seo_semantics/workbook.py tools/seo_semantics/cli.py tools/test_semantic_workbook.py seo-data/2026-08-exp76-services/processed/scope_urls.csv seo-data/2026-08-exp76-services/processed/content_briefs.csv seo-data/2026-08-exp76-services/processed/launch_monitoring.csv seo-data/2026-08-exp76-services/processed/qa_log.csv seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
git commit -m "feat: export clustered semantic core"
```

---

### Task 8: Final Audit, Handoff and Monitoring Baseline

**Files:**
- Modify: `seo-data/2026-08-exp76-services/README.md`
- Modify: `seo-data/2026-08-exp76-services/processed/qa_log.csv`
- Create: `docs/seo/2026-08-20-semantic-core-results.md`

**Interfaces:**
- Consumes: all Task 1–7 artifacts
- Produces: final audit report and reproducible handoff

- [ ] **Step 1: Verify specification coverage**

Check and record in `qa_log.csv`:

- all eight current URLs have a decision;
- every clicked query is manually reviewed;
- at least 95% of queries with impressions have a cluster or exclusion reason;
- one commercial cluster has one owner URL;
- all `new_child_candidate` rows include SERP evidence;
- all `frozen_collision` rows point to an existing frozen owner;
- no city page is proposed without local evidence;
- no existing URL with history is replaced only for slug aesthetics.

- [ ] **Step 2: Run all tests and the project smoke gate**

Run:

```powershell
python -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest tools.test_semantic_classify tools.test_semantic_serp tools.test_semantic_workbook -v
C:\Users\user\.codex\scripts\harness.cmd smoke
git diff --check
```

Expected: all unit tests pass, smoke exits 0, and `git diff --check` has no output.

- [ ] **Step 3: Confirm the live site was not changed**

Read-only verify that the eight current URLs still return their pre-project HTTP status and canonical, and that no new category/service URL was published by this phase. Compare Git changes and FTP/server hashes only if needed; never upload.

- [ ] **Step 4: Write the results report**

`docs/seo/2026-08-20-semantic-core-results.md` must report:

- raw and cleaned query counts;
- exclusions and frozen-collision counts;
- accepted cluster count by service;
- existing URLs retained;
- new page candidates;
- article candidates;
- unresolved manual decisions;
- first publication wave;
- exact locations of the workbook, CSV files and source manifest;
- source collection dates and regions;
- test and QA results;
- explicit statement that the live site was not modified.

- [ ] **Step 5: Update the reproduction instructions**

Add to `README.md` the exact commands for `validate-scope`, `ingest`, `classify`, `cluster`, `export`, `qa` and the full unittest suite. Explain how to add a new monthly Webmaster export without overwriting historical source files.

- [ ] **Step 6: Commit Task 8**

```powershell
git add seo-data/2026-08-exp76-services/README.md seo-data/2026-08-exp76-services/processed/qa_log.csv docs/seo/2026-08-20-semantic-core-results.md
git commit -m "docs: report semantic core results"
```

- [ ] **Step 7: Push the completed commits**

Run:

```powershell
git push origin master
```

Expected: the current master commit is present on `origin/master`. If authentication fails, retain all local commits, report the exact authentication blocker without exposing credentials, and do not rewrite history.

---

## Execution Checkpoints

1. After Task 4: report raw source counts and whether the 250-query SERP/API threshold was crossed.
2. After Task 5: report excluded, ambiguous and frozen-collision counts before SERP work.
3. After Task 6: present the proposed page tree and every new URL candidate before any content generation.
4. After Task 7: deliver the visually verified workbook and QA result.
5. No live-site implementation begins under this plan.
