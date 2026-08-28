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
- `serp_ambiguous_pairs.csv`: 1 044 неизменяемые пограничные пары, из них
  263 требуют отдельного review-overlay и 781 закрыты policy-правилами;
- `reviews/serp_pair_reviews.csv`: ровно 263 reviewed-решения — 186
  `same_destination` и 77 `separate_destinations`. Это статический ручной
  input: каждое rationale называет обе query-потребности, exact overlap и
  фактический формат двух сохранённых top-10; генератор его проверяет, но не
  переписывает из page owners;
- `reviews/cluster_page_decisions.csv`: 164 окончательных назначения без
  пропусков и дублей;
- `page_architecture.csv`: 35 destinations — 8 хабов, 5 заблокированных
  кандидатов подуслуг, 13 backlog-статей, 6 защищённых owners и 3 special
  owners;
- `content_briefs.csv`: 35 destination-driven брифов;
- frozen: 560 observations, 558 distinct queries и 6 owners.

В `content_briefs.csv` поля `title_intent` и `h1_intent` являются
редакторскими формулировками. Каждый бриф содержит собственные primary и
secondary queries, intent, обязательные секции, факторы цены, внутренние
ссылки и evidence state. До Task 3 `case_ids` и `photo_ids` пусты только при
`status=needs_case_mapping`; это не считается готовностью production-контента.

Cluster actions после ручного approval:

- 106 `merge` — подтверждённое объединение с одним владельцем;
- 13 `article` — информационные backlog destinations без публикации;
- 23 `exclude` — товарный, guide- и внешний шум;
- 8 `hub` — неизменяемые S1–S8 URL;
- 6 `frozen` — защищённые категории 87–92;
- 5 `child` — evidence-backed candidates со статусом `blocked_facts`;
- 3 `special` — главная, `/services/` и существующий калькулятор.

Готовы без изменения URL только 8 существующих хабов, 6 frozen owners и 3
существующих special owners. Ни одна новая подуслуга, статья или geo-страница
не имеет `publication_status=ready`: пять child candidates заблокированы до
привязки реальных кейсов/фото. У S2 (рулонный и посевной газон), S4 (обрезка)
и S5 (выравнивание) exact business offer подтверждён ссылкой на секцию
текущего service-v2 payload; S3 (крупномеры) остаётся без такого
подтверждения. Все 13 статей остаются в backlog из-за отсутствия successful
representative-query SERP. Geo-страницы не создавались. Варианты Techno Niki, товарные и внешние
contaminant-формулировки исключены.

## Готовый production-пакет восьми услуг

Для S1–S8 подготовлен новый вариант страниц без смены URL, page ID, родителя
или WordPress-шаблона. Исходный контент хранится в
`ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/*.json`, а
готовые проверенные фрагменты — в соседнем каталоге `rendered/`.

Каждая страница содержит готовые hero, вводный блок, состав работ, этапы,
факторы стоимости, географию, перелинковку, FAQ-разметку и форму заявки.
Подтверждённые кейсы показаны только у S1–S3; для S4–S8 вымышленные объекты не
добавлялись. Цены S1 и S2 подписаны как предварительные ориентиры действующего
калькулятора, а не как окончательная смета.

Подключение ограничено точным совпадением page ID, slug, parent ID и шаблона.
Если JSON, HTML или CSS не загружены полностью, `servicepost.php` оставляет
старую страницу — это защищает остальные услуги от частичного релиза. Вместе
с пакетом добавлены отдельные `/privacy/` и `/consent/`, совместимые редиректы
со старых относительных `.html`-ссылок и проверяемый обработчик заявок, который
не показывает успех при ошибке `mail()`.

Сборка и целевая проверка:

```powershell
python -m tools.service_v2 validate ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2
python -m tools.service_v2 build ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2 ftp_dump_minimal/wp-content/themes/land76wp/content/service-v2/rendered
python -m unittest tools.test_service_v2 -v
```

Публикация должна выполняться только после резервного копирования изменяемых
файлов темы и корневого `server.php`. После загрузки проверяются все восемь
канонических URL, две юридические страницы, метаданные, FAQ JSON-LD,
изображения, мобильная вёрстка и отказ формы на заведомо некорректных данных.
Отправлять тестовую успешную заявку без согласования с получателем не нужно.

## Воспроизведение без сети

Команды запускаются из корня проекта. Рекомендуется bundled Python из Codex;
обычный Python 3.10+ подходит для CSV-этапов.

```powershell
python -m tools.seo_semantics.cli validate-scope --scope seo-data/2026-08-exp76-services/scope.json

python -m tools.seo_semantics.cli ingest --scope seo-data/2026-08-exp76-services/scope.json --manifest seo-data/2026-08-exp76-services/raw/source-manifest.json --output seo-data/2026-08-exp76-services/processed/keywords_raw.csv

python -m tools.seo_semantics.cli classify --scope seo-data/2026-08-exp76-services/scope.json --input seo-data/2026-08-exp76-services/processed/keywords_raw.csv --output seo-data/2026-08-exp76-services/processed/keywords_clean.csv --frozen-output seo-data/2026-08-exp76-services/processed/frozen_collisions.csv --minus-output seo-data/2026-08-exp76-services/processed/minus_words.csv

python -m tools.seo_semantics.cli serp-api-verify --queue seo-data/2026-08-exp76-services/raw/serp/serp-queue.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp

python -m tools.seo_semantics.cli cluster --scope seo-data/2026-08-exp76-services/scope.json --keywords seo-data/2026-08-exp76-services/processed/keywords_clean.csv --serp-dir seo-data/2026-08-exp76-services/raw/serp --serp-output seo-data/2026-08-exp76-services/processed/serp_results.csv --clusters-output seo-data/2026-08-exp76-services/processed/clusters.csv --url-map-output seo-data/2026-08-exp76-services/processed/url_map.csv --candidate-map-output seo-data/2026-08-exp76-services/processed/candidate_cluster_map.csv --ambiguous-output seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv

python -m tools.seo_semantics.production_architecture --data-root seo-data/2026-08-exp76-services

python -m tools.seo_semantics.cli resolve-architecture --scope seo-data/2026-08-exp76-services/scope.json --clusters seo-data/2026-08-exp76-services/processed/clusters.csv --candidate-map seo-data/2026-08-exp76-services/processed/candidate_cluster_map.csv --ambiguous seo-data/2026-08-exp76-services/processed/serp_ambiguous_pairs.csv --pair-reviews seo-data/2026-08-exp76-services/reviews/serp_pair_reviews.csv --cluster-decisions seo-data/2026-08-exp76-services/reviews/cluster_page_decisions.csv --clusters-output seo-data/2026-08-exp76-services/processed/clusters.csv --url-map-output seo-data/2026-08-exp76-services/processed/url_map.csv --page-architecture-output seo-data/2026-08-exp76-services/processed/page_architecture.csv --briefs-output seo-data/2026-08-exp76-services/processed/content_briefs.csv

python -m tools.seo_semantics.cli export --processed-dir seo-data/2026-08-exp76-services/processed --output seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx

python -m tools.seo_semantics.cli qa --scope seo-data/2026-08-exp76-services/scope.json --processed-dir seo-data/2026-08-exp76-services/processed --workbook seo-data/2026-08-exp76-services/exp76-semantic-core.xlsx
```

Перед `production_architecture` файл `reviews/serp_pair_reviews.csv` уже
должен содержать независимые ручные решения. Команда сначала сверяет их с
двумя сохранёнными top-10, проверяет transitive contradictions и только затем
строит/проверяет cluster-page assignments. Изменение destination ID при
неизменном pair evidence завершает команду ошибкой.

`export` использует только bundled `@oai/artifact-tool`. В версии 2.8.6
документированный `freezeRows(1)` не попадает в экспортированный XLSX, а
native hyperlink API отсутствует. Поэтому фильтры, стили и синие URL
сохранены, но закрепление строки и гарантированная кликабельность ссылок не
заявляются. Альтернативный writer не применялся.

## Полные проверки

```powershell
python -m unittest discover -s tools -p "test_*.py" -v
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
