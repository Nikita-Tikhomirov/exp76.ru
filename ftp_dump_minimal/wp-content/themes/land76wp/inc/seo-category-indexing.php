<?php

function land76_indexable_service_category_ids() {
    return array(87, 88, 89, 90, 91, 92);
}

function land76_is_indexable_service_category() {
    return is_category(land76_indexable_service_category_ids());
}

function land76_is_owned_service_hub_grouping_term($term, array $hub) {
    if (!$term instanceof WP_Term
        || $term->taxonomy !== 'category'
        || !isset($hub['service_id'], $hub['grouping_slug'], $hub['canonical'], $hub['archive_policy'])
        || !hash_equals((string) $hub['grouping_slug'], (string) $term->slug)
        || !function_exists('land76wp_service_hubs_expected_release_id')
        || !function_exists('land76wp_service_hubs_import_owner')
        || !function_exists('land76wp_service_hubs_term_checksum')) {
        return false;
    }

    $release_id = (string) get_term_meta($term->term_id, '_land76_release_id', true);
    $manifest_sha256 = (string) get_term_meta($term->term_id, '_land76_manifest_sha256', true);
    if (!hash_equals(land76wp_service_hubs_expected_release_id(), $release_id)
        || !preg_match('/^[a-f0-9]{64}$/', $manifest_sha256)
        || hash_equals(str_repeat('0', 64), $manifest_sha256)) {
        return false;
    }

    $service_id = (string) $hub['service_id'];
    $expected = array(
        '_land76_release_id' => $release_id,
        '_land76_manifest_sha256' => $manifest_sha256,
        '_land76_page_key' => $service_id . '-GROUPING',
        '_land76_service_id' => $service_id,
        '_land76_topic_key' => $service_id,
        '_land76_canonical' => (string) $hub['canonical'],
        '_land76_hub_url' => (string) $hub['canonical'],
        '_land76_archive_policy' => (string) $hub['archive_policy'],
        '_land76_import_owner' => land76wp_service_hubs_import_owner(),
        '_land76_import_checksum' => land76wp_service_hubs_term_checksum($hub, $release_id, $manifest_sha256),
    );
    foreach ($expected as $meta_key => $expected_value) {
        if (!hash_equals((string) $expected_value, (string) get_term_meta($term->term_id, $meta_key, true))) {
            return false;
        }
    }

    return true;
}

function land76_service_hub_grouping_for_current_archive() {
    if (!is_category() || !function_exists('land76wp_service_hub_by_grouping_slug')) {
        return null;
    }

    $term = get_queried_object();
    if (!$term instanceof WP_Term || $term->taxonomy !== 'category') {
        return null;
    }

    $hub = land76wp_service_hub_by_grouping_slug($term->slug);
    return $hub !== null && land76_is_owned_service_hub_grouping_term($term, $hub) ? $hub : null;
}

function land76_redirect_service_hub_grouping_archive() {
    $hub = land76_service_hub_grouping_for_current_archive();
    if ($hub === null || $hub['archive_policy'] !== 'redirect_to_hub') {
        return;
    }

    wp_safe_redirect($hub['canonical'], 301, 'land76-service-hubs');
    exit;
}
add_action('template_redirect', 'land76_redirect_service_hub_grouping_archive', 1);

function land76_filter_service_hub_grouping_canonical($canonical) {
    $hub = land76_service_hub_grouping_for_current_archive();
    return $hub === null ? $canonical : $hub['canonical'];
}
add_filter('redirect_canonical', 'land76_filter_service_hub_grouping_canonical', 20);
add_filter('aioseo_canonical_url', 'land76_filter_service_hub_grouping_canonical', 20);

function land76_service_hub_grouping_term_ids() {
    $term_ids = array();
    if (!function_exists('land76wp_service_hub_registry')) {
        return $term_ids;
    }
    foreach (land76wp_service_hub_registry() as $hub) {
        $term = get_term_by('slug', $hub['grouping_slug'], 'category');
        if ($term instanceof WP_Term && land76_is_owned_service_hub_grouping_term($term, $hub)) {
            $term_ids[] = (int) $term->term_id;
        }
    }

    return array_values(array_unique($term_ids));
}

function land76_exclude_service_hub_groupings_from_core_sitemap($args, $taxonomy) {
    if ($taxonomy !== 'category') {
        return $args;
    }

    $excluded = isset($args['exclude']) && is_array($args['exclude']) ? array_map('intval', $args['exclude']) : array();
    $excluded = array_merge($excluded, land76_service_hub_grouping_term_ids());
    $args['exclude'] = array_values(array_unique($excluded));

    return $args;
}
add_filter('wp_sitemaps_taxonomies_query_args', 'land76_exclude_service_hub_groupings_from_core_sitemap', 20, 2);

function land76_exclude_service_hub_grouping_entries_from_aioseo_sitemap($entries) {
    if (!is_array($entries)) {
        return $entries;
    }

    $blocked_urls = array();
    foreach (land76_service_hub_grouping_term_ids() as $term_id) {
        $term_url = get_term_link($term_id, 'category');
        if (!is_wp_error($term_url)) {
            $blocked_urls[] = trailingslashit($term_url);
        }
    }

    $filtered = array();
    foreach ($entries as $entry) {
        $entry_url = is_array($entry) && !empty($entry['loc']) ? trailingslashit($entry['loc']) : '';
        if ($entry_url !== '' && in_array($entry_url, $blocked_urls, true)) {
            continue;
        }
        $filtered[] = $entry;
    }

    return $filtered;
}
add_filter('aioseo_sitemap_terms', 'land76_exclude_service_hub_grouping_entries_from_aioseo_sitemap', 20);

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
