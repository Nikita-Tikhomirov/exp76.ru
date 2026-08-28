<?php
if (!defined('ABSPATH')) {
    exit;
}

/** Return the immutable service-hub ownership registry. */
function land76wp_service_hub_registry()
{
    static $registry = null;

    if ($registry !== null) {
        return $registry;
    }

    $registry_json = <<<'LAND76_SERVICE_HUB_REGISTRY_JSON'
{
  "S1": {
    "service_id": "S1",
    "topic_key": "S1",
    "hub_post_id": 673,
    "hub_slug": "landshaftnoe-proektirovanie",
    "grouping_slug": "landshaftnoe-proektirovanie",
    "canonical": "https://exp76.ru/services/landshaftnoe-proektirovanie/",
    "archive_policy": "redirect_to_hub"
  },
  "S2": {
    "service_id": "S2",
    "topic_key": "S2",
    "hub_post_id": 6868,
    "hub_slug": "gazon-posevnojj-i-gazon-rulonnyjj",
    "grouping_slug": "gazon-posevnojj-i-gazon-rulonnyjj",
    "canonical": "https://exp76.ru/services/gazon-posevnojj-i-gazon-rulonnyjj/",
    "archive_policy": "redirect_to_hub"
  },
  "S3": {
    "service_id": "S3",
    "topic_key": "S3",
    "hub_post_id": 6871,
    "hub_slug": "posadka-derevev-i-kustarnikov",
    "grouping_slug": "posadka-derevev-i-kustarnikov",
    "canonical": "https://exp76.ru/services/posadka-derevev-i-kustarnikov/",
    "archive_policy": "redirect_to_hub"
  },
  "S4": {
    "service_id": "S4",
    "topic_key": "S4",
    "hub_post_id": 9357,
    "hub_slug": "ukhod-za-sadom",
    "grouping_slug": "ukhod-za-sadom",
    "canonical": "https://exp76.ru/services/ukhod-za-sadom/",
    "archive_policy": "redirect_to_hub"
  },
  "S5": {
    "service_id": "S5",
    "topic_key": "S5",
    "hub_post_id": 667,
    "hub_slug": "planirovka-territorii",
    "grouping_slug": "planirovka-territorii",
    "canonical": "https://exp76.ru/services/planirovka-territorii/",
    "archive_policy": "redirect_to_hub"
  },
  "S6": {
    "service_id": "S6",
    "topic_key": "S6",
    "hub_post_id": 676,
    "hub_slug": "podpornye-stenki",
    "grouping_slug": "podpornye-stenki",
    "canonical": "https://exp76.ru/services/podpornye-stenki/",
    "archive_policy": "redirect_to_hub"
  },
  "S7": {
    "service_id": "S7",
    "topic_key": "S7",
    "hub_post_id": 6918,
    "hub_slug": "ulichnoe-osveshhenie-uchastka",
    "grouping_slug": "ulichnoe-osveshhenie-uchastka",
    "canonical": "https://exp76.ru/services/ulichnoe-osveshhenie-uchastka/",
    "archive_policy": "redirect_to_hub"
  },
  "S8": {
    "service_id": "S8",
    "topic_key": "S8",
    "hub_post_id": 9282,
    "hub_slug": "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch",
    "grouping_slug": "vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch",
    "canonical": "https://exp76.ru/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/",
    "archive_policy": "redirect_to_hub"
  }
}
LAND76_SERVICE_HUB_REGISTRY_JSON;

    $decoded = json_decode($registry_json, true);
    $registry = is_array($decoded) ? $decoded : array();

    return $registry;
}

function land76wp_service_hub_by_service_id($service_id)
{
    $registry = land76wp_service_hub_registry();
    $service_id = strtoupper(trim((string) $service_id));

    return isset($registry[$service_id]) ? $registry[$service_id] : null;
}

function land76wp_service_hub_by_grouping_slug($slug)
{
    $slug = sanitize_title((string) $slug);
    foreach (land76wp_service_hub_registry() as $hub) {
        if (isset($hub['grouping_slug']) && hash_equals((string) $hub['grouping_slug'], $slug)) {
            return $hub;
        }
    }

    return null;
}

function land76wp_service_hub_for_post($post_id)
{
    $post_id = (int) $post_id;
    foreach (land76wp_service_hub_registry() as $hub) {
        if ((int) $hub['hub_post_id'] === $post_id) {
            return $hub;
        }
    }

    $service_id = get_post_meta($post_id, '_land76_service_id', true);
    $topic_key = get_post_meta($post_id, '_land76_topic_key', true);
    if ($service_id === '' || !hash_equals((string) $service_id, (string) $topic_key)) {
        return null;
    }

    return land76wp_service_hub_by_service_id($service_id);
}

function land76wp_is_managed_service_hub_post($post_id)
{
    $owner = get_post_meta((int) $post_id, '_land76_import_owner', true);
    if (!hash_equals('land76-service-hubs', (string) $owner)) {
        return false;
    }

    return land76wp_service_hub_for_post($post_id) !== null;
}

function land76wp_service_hub_managed_meta_value($meta_key, $fallback)
{
    if (!is_singular()) {
        return $fallback;
    }
    $post_id = (int) get_queried_object_id();
    if (!land76wp_is_managed_service_hub_post($post_id)) {
        return $fallback;
    }
    $stored_canonical = (string) get_post_meta($post_id, '_land76_canonical', true);
    $actual_canonical = trailingslashit((string) get_permalink($post_id));
    if ($stored_canonical === '' || !hash_equals($stored_canonical, $actual_canonical)) {
        return $fallback;
    }
    $value = (string) get_post_meta($post_id, $meta_key, true);

    return $value === '' ? $fallback : $value;
}

function land76wp_service_hub_filter_managed_title($title)
{
    return land76wp_service_hub_managed_meta_value('_aioseo_title', $title);
}

function land76wp_service_hub_filter_managed_description($description)
{
    return land76wp_service_hub_managed_meta_value('_aioseo_description', $description);
}

function land76wp_service_hub_filter_managed_canonical($canonical)
{
    return land76wp_service_hub_managed_meta_value('_land76_canonical', $canonical);
}

add_filter('aioseo_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('aioseo_description', 'land76wp_service_hub_filter_managed_description', 999);
add_filter('aioseo_canonical_url', 'land76wp_service_hub_filter_managed_canonical', 999);
add_filter('wpseo_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('wpseo_metadesc', 'land76wp_service_hub_filter_managed_description', 999);
add_filter('wpseo_canonical', 'land76wp_service_hub_filter_managed_canonical', 999);
add_filter('pre_get_document_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('get_canonical_url', 'land76wp_service_hub_filter_managed_canonical', 999);

function land76wp_service_hub_output_registry_schema()
{
    if (!is_singular()) {
        return;
    }

    $post_id = get_queried_object_id();
    $hub = land76wp_service_hub_for_post($post_id);
    if ($hub === null) {
        return;
    }

    $is_hub_page = (int) $hub['hub_post_id'] === (int) $post_id;
    $is_managed = land76wp_is_managed_service_hub_post($post_id);
    if (!$is_hub_page && !$is_managed) {
        return;
    }

    $page_key = (string) get_post_meta($post_id, '_land76_page_key', true);
    $is_article = strpos($page_key, '-ARTICLE-') !== false;
    $current_url = $is_hub_page ? $hub['canonical'] : (string) get_post_meta($post_id, '_land76_canonical', true);
    $actual_url = trailingslashit((string) get_permalink($post_id));
    if ($current_url === '' || !hash_equals($current_url, $actual_url)) {
        return;
    }

    $title = wp_strip_all_tags(get_the_title($post_id));
    $description = (string) get_post_meta($post_id, '_aioseo_description', true);
    if ($description === '') {
        $description = wp_strip_all_tags(get_the_excerpt($post_id));
    }
    $nodes = array();

    if (!$is_article) {
        $service = array(
            '@type' => 'Service',
            '@id' => trailingslashit($current_url) . '#service',
            'name' => $title,
            'serviceType' => get_the_title((int) $hub['hub_post_id']),
            'description' => $description,
            'provider' => array('@id' => home_url('/#organization')),
            'url' => $current_url,
            'category' => get_the_title((int) $hub['hub_post_id']),
            'inLanguage' => 'ru-RU',
        );
        $image_url = $is_hub_page ? '' : (string) get_post_meta($post_id, '_land76_main_image_url', true);
        if ($image_url !== '') {
            $service['image'] = array(
                '@type' => 'ImageObject',
                'url' => $image_url,
                'caption' => (string) get_post_meta($post_id, '_land76_main_image_alt', true),
            );
        }
        $nodes[] = array_filter($service);
    }

    $breadcrumb_items = array(
        array(
            '@type' => 'ListItem',
            'position' => 1,
            'name' => get_bloginfo('name'),
            'item' => home_url('/'),
        ),
    );
    if (!$is_hub_page) {
        $breadcrumb_items[] = array(
            '@type' => 'ListItem',
            'position' => count($breadcrumb_items) + 1,
            'name' => get_the_title((int) $hub['hub_post_id']),
            'item' => $hub['canonical'],
        );
    }
    $breadcrumb_items[] = array(
        '@type' => 'ListItem',
        'position' => count($breadcrumb_items) + 1,
        'name' => $title,
        'item' => $current_url,
    );
    $nodes[] = array(
        '@type' => 'BreadcrumbList',
        '@id' => trailingslashit($current_url) . '#service-hub-breadcrumb',
        'itemListElement' => $breadcrumb_items,
    );

    echo "\n<script type=\"application/ld+json\" class=\"land76-service-hub-schema\">";
    echo wp_json_encode(
        array('@context' => 'https://schema.org', '@graph' => $nodes),
        JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES
    );
    echo "</script>\n";
}
add_action('wp_head', 'land76wp_service_hub_output_registry_schema', 31);
