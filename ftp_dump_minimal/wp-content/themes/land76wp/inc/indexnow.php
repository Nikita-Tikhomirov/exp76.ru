<?php

if (!defined('LAND76_INDEXNOW_KEY')) {
    define('LAND76_INDEXNOW_KEY', 'f2ad132888f56822c43105282c44dd25');
}

function land76_indexnow_submit_urls($urls) {
    $home_host = wp_parse_url(home_url('/'), PHP_URL_HOST);
    $urls = array_values(array_unique(array_filter(array_map('esc_url_raw', (array) $urls), function ($url) use ($home_host) {
        return $url && wp_parse_url($url, PHP_URL_HOST) === $home_host;
    })));

    if (!$urls) {
        return;
    }

    $request_key = 'land76_indexnow_' . md5(implode('|', $urls));
    if (get_transient($request_key)) {
        return;
    }
    set_transient($request_key, 1, 5 * MINUTE_IN_SECONDS);

    wp_remote_post('https://yandex.com/indexnow', array(
        'headers' => array('Content-Type' => 'application/json; charset=utf-8'),
        'body' => wp_json_encode(array(
            'host' => $home_host,
            'key' => LAND76_INDEXNOW_KEY,
            'keyLocation' => home_url('/' . LAND76_INDEXNOW_KEY . '.txt'),
            'urlList' => $urls,
        )),
        'blocking' => false,
        'timeout' => 0.01,
    ));
}

function land76_indexnow_post_status_changed($new_status, $old_status, $post) {
    if ($new_status !== 'publish' || !is_post_type_viewable($post->post_type)) {
        return;
    }

    land76_indexnow_submit_urls(array(get_permalink($post)));
}
add_action('transition_post_status', 'land76_indexnow_post_status_changed', 10, 3);

function land76_indexnow_category_updated($term_id) {
    $url = get_category_link($term_id);
    if (!is_wp_error($url)) {
        land76_indexnow_submit_urls(array($url));
    }
}
add_action('edited_category', 'land76_indexnow_category_updated');
