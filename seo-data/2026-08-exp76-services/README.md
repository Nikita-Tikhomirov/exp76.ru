# Semantic-core scope

This directory defines the read-only scope for semantic collection for exp76.ru.

## Approved services

| ID | Service | Existing URL |
| --- | --- | --- |
| S1 | Ландшафтное проектирование | https://exp76.ru/services/landshaftnoe-proektirovanie/ |
| S2 | Газон посевной и рулонный | https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/ |
| S3 | Посадка деревьев и кустарников | https://exp76.ru/services/posadka-derevev-i-kustarnikov/ |
| S4 | Уход за садом | https://exp76.ru/services/ukhod-za-sadom/ |
| S5 | Планировка территории | https://exp76.ru/services/planirovka-territorii/ |
| S6 | Подпорные стенки | https://exp76.ru/services/podpornye-stenki/ |
| S7 | Уличное и ландшафтное освещение участка | https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/ |
| S8 | Въезд и заезд на участок через канаву | https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/ |

## Frozen category hubs

These six existing directions and their child content are immutable in this phase:

- https://exp76.ru/category/drenazh-uchastka/
- https://exp76.ru/category/otmostka-vokrug-doma/
- https://exp76.ru/category/ukladka-trotuarnoy-plitki/
- https://exp76.ru/category/osushenie-uchastka/
- https://exp76.ru/category/livnevaya-kanalizatsiya/
- https://exp76.ru/category/avtopoliv-na-uchastke/

Raw source files are immutable. This phase never writes to WordPress, FTP, Yandex settings, or published URLs. Secrets, credentials, and tokens are prohibited in this directory.

Later tasks add these read-only CLI commands, which must preserve this boundary:

- `validate-scope`
- `register-source`
- `ingest`
- `classify`
- `cluster`
- `export`
- `qa`

## Source registration

`seeds.json` contains the initial search masks for every approved service. Keep its hypotheses, including seasonal garden care, large-tree planting, and retaining-wall materials, until Wordstat, SERP, and business evidence are evaluated.

Register each raw source without changing the source file:

```powershell
python -m tools.seo_semantics.cli validate-scope --scope seo-data/2026-08-exp76-services/scope.json
python -m tools.seo_semantics.cli register-source --file <path> --source webmaster --collected-at <ISO-8601> --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json
```

The manifest records a relative POSIX path, SHA-256 digest, byte count, source, and collection timestamp. It rejects filenames that look like secrets.

## 2026-08-20 collection

The authenticated Yandex collection was performed read-only with the in-app browser. No Webmaster settings, site files, Cloud products, billing, or terms were changed.

### Yandex Webmaster

Native query CSV exports are stored in `raw/webmaster/`:

- `site-12mo-2026-08-20.csv`: 2025-08-20 through 2026-08-18;
- `site-90d-2026-08-20.csv`: 2026-05-21 through 2026-08-18;
- `site-30d-2026-08-20.csv`: 2026-07-20 through 2026-08-18.

The three exports contain 3,794 source rows before period deduplication. The extended URL-analysis daily balance was exhausted and its preparation control was disabled, so no new S1-S8 URL reports could be generated. The only existing downloadable URL report covered a frozen storm-sewer URL and was intentionally excluded from raw data, the manifest, and the processed core.

### Wordcraft

The collection used `region=10841` (Yaroslavl Oblast) and all devices for each principal S1-S8 seed and each current S1-S8 URL. Separate mobile-and-tablet seed passes were run for S2, S5, and S8. The main seed pass returned 96 visible rows, the URL pass returned one S8 row, and the mobile pass returned 66 rows.

The native XLSX export succeeded for S1 and is preserved unchanged. For the other runs, the visible XLS control did not deliver a file. Their visible result tables were therefore captured into the `*-dom.csv` files with the required columns and full source URL, region, device, and capture time. `raw/wordcraft/coverage.csv` records all 19 requested runs, including zero-result runs and the capture method. The ten non-empty DOM files contain 163 rows.

### Wordstat

Native CSV exports and complete request routing are stored in `raw/wordstat/`:

- broad: all 45 seeds for Yaroslavl and Yaroslavl Oblast, 90 requests, 74 exports, 16 routes without a suggestion-table export;
- phrase and exact: eight principal heads in both regions, 32 requests, 28 exports, four routes without a suggestion-table export;
- dynamics: eight principal heads in both regions, 16 exports covering August 2024 through July 2026;
- explicit Rybinsk, Tutayev, Uglich, and Pereslavl-Zalessky variants: all 45 seeds, 180 requests, four exports and 176 routes without a suggestion-table export;
- Russia discovery: eight principal heads, eight exports, routed as `Russia_discovery`.

The 114 top-query exports contain 6,220 source rows. The 16 dynamics exports contain 384 monthly rows and are retained for later seasonality work; they are not ingested as keywords. `coverage.csv` and `dynamics-coverage.csv` provide the seed, service, region, mode, source URL, status, and raw filename for every request.

The immutable `coverage.csv` uses the historical status `zero_results` when the UI produced no suggestion table/export. It does not mean that the queried head had zero demand: `row_hint` is the observed head frequency. In particular, 22 of the 180 city-route heads have positive demand, including 18 routes without an export. Ingestion emits all city-route heads from `query_expr` plus `row_hint`, and emits every phrase/exact head from the same fields. Counts inside native export bodies describe broad suggestions, so they remain broad observations rather than phrase/exact frequencies.

All 147 raw files have exactly one entry in `raw/source-manifest.json`. The source URLs in coverage files are the current capture URLs. No cookies, passwords, tokens, competitor snippets, or page content are stored.

## Unified ingestion

Run the stable UTF-8 ingestion from the project root:

```powershell
python -m tools.seo_semantics.cli ingest --scope seo-data/2026-08-exp76-services/scope.json --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json --output seo-data/2026-08-exp76-services/processed/keywords_raw.csv
```

The command verifies every registered byte count and SHA-256, applies explicit source schemas, uses Wordstat coverage only for operator/city head observations, ignores dynamics/XLSX evidence as keyword rows, and writes 7,818 rows sorted by normalized query, region, device, and current URL. It does not sum metrics from incompatible methodologies.

The 250-query paid SERP/API decision gate remains provisional until Task 5 cleaning and frozen routing determine how many candidates actually require SERP checks. No paid API or Yandex Cloud product was activated.
