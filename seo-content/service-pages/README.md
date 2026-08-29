# Production content for child service pages

`pages/*.json` — авторские исходники дочерних коммерческих страниц. Они не
содержат WordPress-операций и сами ничего не публикуют. Валидатор связывает
каждый файл с двумя approved registries:

- `complete_service_children.csv` фиксирует URL, owner hub, create/reuse и границу интента;
- `evidence.json` фиксирует допустимые case IDs и WordPress media.

Authoritative source текущего release —
`tools.seo_semantics.complete_service_architecture.build_complete_service_rows()`.
При запуске без `--architecture` генератор сравнивает с ним checked-in CSV и
останавливается при drift. Сейчас registries содержат 65 child pages для 15
хабов: 64 create и один reuse — `S7-CHILD-HOLIDAY`. Устаревшего
`S5-CHILD-STUMPS` в release нет: интент корчевания принадлежит S9. Число страниц
не зашито в общей валидации, поэтому явно переданный следующий approved registry
может быть расширен без переписывания генератора.

## Обязательные поля

Верхний уровень:

`schema_version`, `destination_id`, `service_id`, `deployment`, `slug`,
`canonical`, `post_title`, `seo`, `h1`, `lead`, `scope`, `audience`, `process`,
`pricing`, `proof`, `geo`, `faq`, `links`, `cta`, `boundary`.

Минимальные production-блоки:

- `scope.results` — не менее двух результатов;
- `audience.items` — не менее трёх сценариев «кому/когда»;
- `process.steps` — не менее пяти этапов;
- `pricing.factors` — не менее трёх факторов без выдуманных сумм;
- `proof` — ссылка на registry, подтверждённый WP attachment, честная подпись и
  только подтверждённые case IDs;
- `geo.areas` — не менее двух территорий и отдельный geo-текст;
- `faq.items` — не менее пяти пар вопрос/ответ;
- `links` — точный parent hub и хотя бы одна дочерняя страница того же hub;
- `boundary.excluded_intents` — хотя бы один исключённый интент.

Полная машинная форма находится в [schema.json](schema.json). Python-валидатор
дополнительно проверяет registries, уникальность `seo.title`,
`seo.description`, `h1`, `lead`, placeholders, абсолютные обещания,
неподтверждённые сроки/цены и честность media caption.

## Create и frozen reuse

Для `create` deployment-поля текущего объекта равны `null`, preserve-флаги —
`false`. Для `reuse` JSON обязан дословно повторить `current_wp_id`, post type,
URL и template из architecture; preserve-флаги — `true`.

Эти deployment-поля нужны только локальному fail-closed контролю и не попадают
в importer item. В текущем release единственный child reuse —
`S7-CHILD-HOLIDAY`; его WP ID, type, URL и template сохраняются по architecture.
PHP importer определяет reuse по frozen `page_key`; item для create и reuse
имеет одну схему. `servicepost.php` направляет managed reuse child page в
`newservicepost.php`, поэтому для обеих операций
`post_content` содержит блоки, которых нет в новом template, а template-owned
hero/problem/process/pricing/FAQ передаются через `acf`. Отдельная функция
`render_standalone_html()` строит полный безопасный HTML для локального preview,
но importer item его не использует: иначе на reuse появились бы второй H1 и
дубли FAQ.

## Валидный пример одного source-файла

Это пример формы, а не готовый текст для публикации. Его `destination_id`, URL,
граница и media соответствуют approved registries.

```json
{
  "schema_version": 1,
  "destination_id": "S1-CHILD-SKETCH",
  "service_id": "S1",
  "deployment": {
    "action": "create",
    "current_wp_id": null,
    "current_post_type": null,
    "current_url": null,
    "target_template": "newservicepost.php",
    "preserve_id": false,
    "preserve_permalink": false
  },
  "slug": "eskiznyj-proekt-uchastka",
  "canonical": "https://exp76.ru/eskiznyj-proekt-uchastka/",
  "post_title": "Эскизный проект участка",
  "seo": {
    "title": "Эскизный проект участка в Ярославле — заказать разработку",
    "description": "Эскизный проект загородного участка в Ярославле и области: зонирование, концепция, состав результата и факторы расчёта стоимости."
  },
  "h1": "Эскизный проект участка в Ярославле",
  "lead": "Разрабатываем концепцию участка с функциональными зонами и связями между ними до перехода к детальной проектной документации.",
  "scope": {
    "heading": "Что входит в эскизный проект",
    "text": "Состав проекта согласуем по исходным данным, особенностям территории и задачам владельца участка.",
    "results": [
      {
        "title": "Схема зонирования",
        "text": "Показываем расположение основных зон и логичные связи между ними."
      },
      {
        "title": "Концепция участка",
        "text": "Фиксируем направление дальнейшей проработки без подмены рабочего проекта."
      }
    ]
  },
  "audience": {
    "heading": "Кому и когда нужен эскиз",
    "text": "Страница помогает владельцам, которым нужно согласовать общую логику участка до детального проектирования.",
    "items": [
      {
        "title": "Перед благоустройством",
        "text": "Когда требуется определить зоны до закупки материалов и начала работ."
      },
      {
        "title": "При изменении участка",
        "text": "Когда существующая планировка не соответствует новому сценарию использования."
      },
      {
        "title": "Перед рабочим проектом",
        "text": "Когда сначала нужно согласовать концепцию и только затем детализацию."
      }
    ]
  },
  "process": {
    "heading": "Как разрабатывается эскиз",
    "steps": [
      { "title": "Заявка", "text": "Уточняем задачи, состав семьи и сценарии использования участка." },
      { "title": "Исходные данные", "text": "Изучаем план, фотографии, рельеф и существующие объекты территории." },
      { "title": "Зонирование", "text": "Распределяем функциональные зоны и намечаем связи между ними." },
      { "title": "Концепция", "text": "Собираем выбранное решение в цельную эскизную схему участка." },
      { "title": "Согласование", "text": "Обсуждаем результат и фиксируем направление дальнейшей детализации." }
    ]
  },
  "pricing": {
    "heading": "От чего зависит стоимость эскиза",
    "text": "Точный расчёт готовим после получения исходных данных и определения состава результата.",
    "factors": [
      { "title": "Площадь", "text": "Учитываем размер территории и количество функциональных зон." },
      { "title": "Исходные условия", "text": "Оцениваем рельеф, существующие объекты и доступность материалов." },
      { "title": "Состав результата", "text": "Фиксируем необходимую глубину проработки и формат передачи материалов." }
    ]
  },
  "proof": {
    "evidence_ref": "S1-CHILD-SKETCH",
    "case_ids": [],
    "main_image_attachment_id": 7330,
    "main_image_alt": "Концептуальная схема ландшафтного проектирования участка",
    "caption": "Иллюстрация: пример графического представления концепции без привязки к выполненному объекту."
  },
  "geo": {
    "heading": "Проектирование в Ярославле и области",
    "text": "Работаем с участками в Ярославле, Рыбинске и населённых пунктах Ярославской области с учётом исходных данных территории.",
    "areas": ["Ярославль", "Рыбинск", "Ярославская область"]
  },
  "faq": {
    "heading": "Вопросы об эскизном проекте",
    "items": [
      { "question": "Какие исходные данные нужны?", "answer": "Нужны план или схема участка, фотографии и описание желаемых зон." },
      { "question": "Эскиз заменяет рабочий проект?", "answer": "Нет, эскиз фиксирует концепцию, а рабочая документация содержит детализацию." },
      { "question": "Можно начать работу дистанционно?", "answer": "Да, если есть читаемый план, фотографии и достаточно сведений об участке." },
      { "question": "Учитываются существующие объекты?", "answer": "Да, на схеме отмечаются сохраняемые строения, посадки и другие ограничения." },
      { "question": "Что происходит после согласования?", "answer": "После согласования можно перейти к необходимым разделам детального проекта." }
    ]
  },
  "links": {
    "parent": {
      "page_key": "S1-HUB",
      "url": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
      "label": "Ландшафтное проектирование"
    },
    "related_services": [
      {
        "page_key": "S1-CHILD-MASTERPLAN",
        "url": "https://exp76.ru/generalnyj-plan-uchastka/",
        "label": "Генеральный план участка"
      }
    ]
  },
  "cta": {
    "heading": "Обсудить эскиз участка",
    "text": "Пришлите план и фотографии территории — уточним задачу и состав результата.",
    "primary_label": "Получить расчёт",
    "primary_url": "#calc",
    "secondary_label": "Задать вопрос",
    "secondary_url": "#consultation"
  },
  "boundary": {
    "summary": "Эскиз, зонирование и концепция; полный комплект проекта остаётся хабу.",
    "excluded_intents": ["полный комплект рабочего проекта", "кадастровая документация"]
  }
}
```

## Команды

Из корня worktree default inputs уже настроены на:

- `seo-content/service-pages/pages/*.json`;
- `processed/complete_service_children.csv` с обязательной проверкой против
  executable source;
- `seo-content/service-pages/evidence.json`.

Поэтому для текущего release достаточно:

```powershell
python tools/service_page_content.py validate

python tools/service_page_content.py render-items `
  --output build/service-page-items.json

python tools/service_page_content.py render-bundle `
  --release-id service-hubs-2026-08-28 `
  --source-manifest seo-content/service-hubs/release-manifest.json `
  --deployment-manifest-output seo-content/service-pages/import/service-pages-release-manifest.json `
  --payload-output seo-content/service-pages/import/service-pages-import.json
```

`--pages-dir`, `--architecture` и `--evidence` остаются доступны для явно
утверждённого следующего registry. Явно переданный architecture CSV валидируется
по своему inventory и не обязан содержать ровно 65 строк.

`render-payload` дополнительно требует `--release-id` и подтверждённый
`--manifest-sha256`. Полученный файл соответствует wrapper schema импортера,
но команда не вызывает WordPress и не меняет сайт.

`render-bundle` выполняет ту же сборку без ручной подстановки хэша: сначала
создаёт точный inventory из 65 `page_key` и checksum, затем привязывает к нему
ready-payload SHA-256 хэшем. Оба файла остаются локальными; команда не запускает
preview, stage или publish в WordPress.

## Граница доказательств для S9–S15

Для legacy-направлений точными кейсами считаются только WP 8613 для
`S9-CHILD-STUMPS` и WP 8608 для страниц декоративного пруда и каскада S10.
Остальные media имеют тип `service_photo` или `context_photo`: их можно
описывать как изображения со страницы услуги или визуальный контекст, но нельзя
называть выполненным компанией объектом или «нашей работой». Registry не
подтверждает цены, сроки, бренды, гарантии и технические абсолютные обещания.
