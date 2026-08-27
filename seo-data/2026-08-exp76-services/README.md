# Семантическое ядро exp76.ru для восьми старых услуг

Этот каталог содержит воспроизводимый read-only срез спроса и карту
`кластер → URL` для восьми существующих услуг. В рамках этапа не менялись
WordPress, FTP, Яндекс Вебмастер, опубликованные URL, canonical, robots,
sitemap, редиректы или индексация.

## Scope

| ID | Услуга | Существующий URL |
| --- | --- | --- |
| S1 | Ландшафтное проектирование | https://exp76.ru/services/landshaftnoe-proektirovanie/ |
| S2 | Газон посевной и рулонный | https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/ |
| S3 | Посадка деревьев и кустарников | https://exp76.ru/services/posadka-derevev-i-kustarnikov/ |
| S4 | Уход за садом | https://exp76.ru/services/ukhod-za-sadom/ |
| S5 | Планировка территории | https://exp76.ru/services/planirovka-territorii/ |
| S6 | Подпорные стенки | https://exp76.ru/services/podpornye-stenki/ |
| S7 | Уличное и ландшафтное освещение участка | https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/ |
| S8 | Въезд и заезд на участок через канаву | https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/ |

Шесть уже переработанных направлений защищены и не перестраиваются:

- https://exp76.ru/category/drenazh-uchastka/
- https://exp76.ru/category/otmostka-vokrug-doma/
- https://exp76.ru/category/ukladka-trotuarnoy-plitki/
- https://exp76.ru/category/osushenie-uchastka/
- https://exp76.ru/category/livnevaya-kanalizatsiya/
- https://exp76.ru/category/avtopoliv-na-uchastke/

## Источники

Исходные файлы в `raw/` неизменяемы. `raw/source-manifest.json` хранит
относительный путь, SHA-256, размер, тип источника и время сбора. Секреты,
cookies, пароли и API-ключи в проект не сохраняются.

Срез включает:

- Яндекс Вебмастер: три нативных query CSV за 12 месяцев, 90 и 30 дней;
- Wordcraft: 19 запусков по seed и текущим URL, включая mobile-проверки S2,
  S5 и S8;
- Wordstat: broad, phrase, exact, 24-месячную динамику, Ярославль,
  Ярославскую область, Рыбинск, Тутаев, Углич и Переславль-Залесский;
- органическую выдачу Яндекса: 141 запрос и 1 410 результатов.

Финальный manifest содержит 383 записи:

- Webmaster — 3;
- Wordcraft — 12;
- Wordstat — 132;
- SERP JSONL — 121;
- Yandex Search API operation records — 115.

Первые 26 выдач собраны browser read-only control pass. Недостающие 115
получены официальным deferred Yandex Search API. Расчётная стоимость по
зафиксированному тарифу — 3,5075 ₽ из разрешённого лимита 50 ₽. Collector
больше не сохраняет полные XML-ответы, сниппеты и тексты страниц: в Git и
manifest входят только санитизированные top-10 JSONL и записи операций.
Ранее полученные локальные recovery XML оставлены на диске вне Git, поскольку
удаление не входило в разрешённые действия. Повторно платить для
воспроизведения обработки не нужно.

## Итоговые объёмы

- `keywords_raw.csv`: 7 818 строк;
- `keywords_clean.csv`: 7 258 строк;
- релевантные observations для графа: 6 085;
- уникальные candidates: 4 236;
- `serp_results.csv`: 141 QID и 1 410 строк;
- `clusters.csv`: 164 кластера;
- `url_map.csv`: 164 URL-решения;
- `serp_ambiguous_pairs.csv`: 1 044 пограничные пары, из них 263 manual
  pending и 781 policy-reviewed;
- `content_briefs.csv`: 8 агрегированных брифов, по одному на S1–S8;
- frozen: 560 observations, 558 distinct queries и 6 owners.

В `content_briefs.csv` поля `title_intent` и `h1_intent` являются
редакторскими формулировками. `source_cluster_ids` содержит фактические
`keep_enhance`-кластеры того же service/URL, а `primary_query` и каждый
элемент `secondary_queries` дословно взяты из `candidate_cluster_map.csv` и
принадлежат одному из этих кластеров; это соответствие проверяет команда
`qa`.

Cluster actions:

- 115 `keep_enhance` — коммерческие запросы на существующих S1-S8 URL;
- 23 `article_candidate` — информационный backlog без публикации;
- 18 `exclude` — товарный и внешний шум;
- 6 `frozen_owner`;
- 2 `keep_special_owner` — главная и существующий калькулятор.

Новых URL, city pages, redirects и index actions нет. Ложный cross-owner
компонент S1/S5 и остальные пограничные межсервисные пары разделены по
утверждённой карте владельцев S1–S8. 23 чистых calculator candidates
закреплены за `/kalkuljator-uslug/`; семь clicked brand QID — за главной.
Варианты Techno Niki, маркетплейсы и внешние contaminant-формулировки
исключены. Внутрисервисные пограничные пары не скрыты: 263 решения требуют
редакторской проверки до публикации или изменения структуры. Ещё 27
внутрисервисных пар закрыты явными правилами калькулятора и исключений.

## Воспроизведение без сети

Команды запускаются из корня проекта. Рекомендуется bundled Python из Codex;
обычный Python 3.10+ подходит для CSV-этапов.

```powershell
python -m tools.seo_semantics.cli validate-scope --scope seo-data/2026-08-exp76-services/scope.json

python -m tools.seo_semantics.cli ingest --scope seo-data/2026-08-exp76-services/scope.json --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json --output seo-data/2026-08-exp76-services/processed/keywords_raw.csv

python -m tools.seo_semantics.cli classify --scope seo-data/2026-08-exp76-services/scope.json --input seo-data/2026-08-exp76-services/processed/keywords_raw.csv --output seo-data/2026-08-exp76-services/processed/keywords_clean.csv --frozen-output seo-data/2026-08-exp76-services/processed/frozen_collisions.csv --minus-output seo-data/2026-08-exp76-services/processed/minus_words.csv

python -m tools.seo_semantics.cli serp-api-verify --queue seo-data/2026-08-exp76-services/raw/serp/serp-queue.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp

python -m tools.seo_semantics.cli cluster --scope seo-data/2026-08-exp76-services/scope.json --keywords seo-data/2026-08-exp76-services/processed/keywords_clean.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp --serp-output seo-data/2026-08-exp76-services/processed/serp_results.csv --clusters-output seo-data/2026-08-exp76-services/processed/clusters.csv --url-map-output seo-data/2026-08-exp76-services/processed/url_map.csv --candidate-map-output seo-data/2026-08-exp76-services/processed/candidate_cluster_map.csv --ambiguous-output seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv

python -m tools.seo_semantics.cli export --processed-dir seo-data/2026-08-exp76-services/processed --output seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx

python -m tools.seo_semantics.cli qa --scope seo-data/2026-08-exp76-services/scope.json --processed-dir seo-data/2026-08-exp76-services/processed --workbook seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
```

`export` использует только bundled `@oai/artifact-tool`. В версии 2.8.6
документированный `freezeRows(1)` не попадает в экспортированный XLSX, а
native hyperlink API отсутствует. Поэтому фильтры, стили и синие URL
сохранены, но закрепление строки и гарантированная кликабельность ссылок не
заявляются. Альтернативный writer не применялся.

## Полные проверки

```powershell
python -m unittest tools.test_semantic_scope tools.test_semantic_normalize tools.test_semantic_ingest tools.test_semantic_manifest tools.test_semantic_classify tools.test_semantic_serp tools.test_yandex_search_api tools.test_semantic_workbook -v
C:\Users\user\.codex\scripts\harness.cmd smoke
git diff --check
```

## Добавление нового месячного экспорта Вебмастера

1. Сохранить новый CSV под новым датированным именем в `raw/webmaster/`.
2. Не заменять предыдущий файл.
3. Зарегистрировать новый файл:

```powershell
python -m tools.seo_semantics.cli register-source --file <new-csv> --source webmaster --collected-at <ISO-8601> --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json
```

4. Повторить `ingest`, `classify`, `cluster`, `export` и `qa`.
5. Сравнивать периоды отдельно; не суммировать overlapping Webmaster windows.

Сетевые `serp-api-submit` и `serp-api-poll` не нужны для текущего полного
корпуса. Они требуют credentials только через process environment и сохраняют
immutable operation records и санитизированные JSONL без сниппетов и текстов
страниц. API-ключи никогда не передаются CLI-аргументами и не печатаются.
