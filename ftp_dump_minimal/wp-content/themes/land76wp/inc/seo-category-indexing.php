<?php

function land76_indexable_service_category_ids() {
    return array(87, 88, 89, 90, 91, 92);
}

function land76_is_indexable_service_category() {
    return is_category(land76_indexable_service_category_ids());
}

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
