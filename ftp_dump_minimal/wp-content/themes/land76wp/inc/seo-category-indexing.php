<?php

function land76_indexable_service_category_ids() {
    return array(87, 88, 89, 90, 91, 92);
}

function land76_is_indexable_service_category() {
    return is_category(land76_indexable_service_category_ids());
}

function land76_service_category_descriptions() {
    return array(
        87 => 'Дренаж участка под ключ в Рыбинске, Ярославле и области: проектирование, монтаж глубинных и поверхностных систем, защита дома от воды.',
        88 => 'Отмостка вокруг дома под ключ в Рыбинске, Ярославле и области: бетонная, мягкая, утепленная и плиточная. Расчет, основание и водоотвод.',
        89 => 'Укладка тротуарной плитки под ключ в Рыбинске, Ярославле и области: дорожки, площадки, парковки, бордюры, подготовка основания и водоотвод.',
        90 => 'Осушение участка под ключ в Рыбинске, Ярославле и области: диагностика причин сырости, дренаж, водоотвод, канавы, колодцы и планировка.',
        91 => 'Ливневая канализация под ключ в Рыбинске, Ярославле и области: дождеприемники, лотки, трубы и колодцы для отвода воды от дома и участка.',
        92 => 'Автополив участка под ключ в Рыбинске, Ярославле и области: проектирование, монтаж и настройка полива газона, сада, теплицы и посадок.',
    );
}

function land76_city_hub_descriptions() {
    return array(
        'yaroslavl' => 'Услуги по благоустройству участков в Ярославле и пригородах: дренаж, ливневая канализация, отмостка, плитка, автополив и озеленение под ключ.',
        'rybinsk' => 'Услуги по благоустройству участков в Рыбинске и районе: дренаж, осушение, отмостка, мощение, автополив и комплексные работы под ключ.',
        'uglich' => 'Услуги по благоустройству участков в Угличе и районе: водоотвод, дренаж, отмостка, тротуарная плитка, автополив и озеленение.',
        'tutaev' => 'Услуги по благоустройству участков в Тутаеве и пригороде: дренаж, ливневка, отмостка, мощение, автополив и комплексные работы.',
        'pereslavl' => 'Услуги по благоустройству участков в Переславле-Залесском и районе: дренаж, осушение, отмостка, плитка и автополив под ключ.',
    );
}

function land76_filter_aioseo_service_descriptions($description) {
    if (is_category()) {
        $descriptions = land76_service_category_descriptions();
        $category_id = (int) get_queried_object_id();

        return isset($descriptions[$category_id]) ? $descriptions[$category_id] : $description;
    }

    if (is_page()) {
        $descriptions = land76_city_hub_descriptions();
        $page_slug = get_post_field('post_name', get_queried_object_id());

        return isset($descriptions[$page_slug]) ? $descriptions[$page_slug] : $description;
    }

    return $description;
}
add_filter('aioseo_description', 'land76_filter_aioseo_service_descriptions', 30);

function land76_filter_aioseo_category_robots($attributes) {
    if (!land76_is_indexable_service_category()) {
        return $attributes;
    }

    unset($attributes['noindex']);
    $attributes['index'] = 'index';

    return $attributes;
}
add_filter('aioseo_robots_meta', 'land76_filter_aioseo_category_robots', 20);

function land76_add_service_category_sitemap_index($indexes) {
    $sitemap_file = ABSPATH . 'land76-seo-categories-sitemap.xml';
    $sitemap_url = home_url('/land76-seo-categories-sitemap.xml');

    foreach ($indexes as $index) {
        if (!empty($index['loc']) && $index['loc'] === $sitemap_url) {
            return $indexes;
        }
    }

    $last_modified = file_exists($sitemap_file)
        ? gmdate('c', (int) filemtime($sitemap_file))
        : gmdate('c');

    $indexes[] = array(
        'loc' => $sitemap_url,
        'lastmod' => $last_modified,
        'count' => count(land76_indexable_service_category_ids()),
    );

    return $indexes;
}
add_filter('aioseo_sitemap_indexes', 'land76_add_service_category_sitemap_index');
