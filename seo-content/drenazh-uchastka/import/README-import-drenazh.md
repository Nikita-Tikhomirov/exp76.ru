# Импорт дренажа в WordPress

1. Сгенерируйте JSON командой:
   `python tools/generate_drenazh_seo_docs.py`

2. Возьмите файл:
   `seo-content/drenazh-uchastka/import/drenazh-import.json`

3. Загрузите `drenazh-import.json` на сайт в тему:
   `wp-content/themes/land76wp/import/drenazh-import.json`

4. Убедитесь, что в теме есть файл импортера:
   `wp-content/themes/land76wp/inc/import-drenazh.php`
   (он подключается из `functions.php` автоматически).

5. Запустите импорт из-под администратора WP:
   `https://ВАШ_ДОМЕН/wp-admin/?land76_run_drenazh_import=1`

6. После выполнения проверьте результат:
   - категория `87` заполнена ACF-полями `cat87_*`;
   - созданы/обновлены посты из `PRICE_PAGE + SERVICE_PAGES + PROBLEM_PAGES`;
   - у постов выставлены рубрики `87` и `72`;
   - геостраницы не импортированы.

7. После успешного запуска отключите триггер импорта:
   - временно закомментируйте строку в `functions.php`:
     `require_once __DIR__ . '/inc/import-drenazh.php';`
   - либо оставьте файл подключенным, но не используйте URL с параметром `land76_run_drenazh_import=1`.
