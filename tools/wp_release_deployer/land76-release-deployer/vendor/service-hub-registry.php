<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_is_supported_case_template($template)
{
    return in_array((string) $template, array('casenew.php', 'portfoliopost.php'), true);
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
  },
  "S9": {
    "service_id": "S9",
    "topic_key": "S9",
    "hub_post_id": 6870,
    "hub_slug": "vykorchevyvanie-pnejj-spil-derevev",
    "grouping_slug": "vykorchevyvanie-pnejj-spil-derevev",
    "canonical": "https://exp76.ru/services/vykorchevyvanie-pnejj-spil-derevev/",
    "archive_policy": "redirect_to_hub"
  },
  "S10": {
    "service_id": "S10",
    "topic_key": "S10",
    "hub_post_id": 6900,
    "hub_slug": "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev",
    "grouping_slug": "sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev",
    "canonical": "https://exp76.ru/services/sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev/",
    "archive_policy": "redirect_to_hub"
  },
  "S11": {
    "service_id": "S11",
    "topic_key": "S11",
    "hub_post_id": 6922,
    "hub_slug": "sistemy-tumanoobrazovaniya",
    "grouping_slug": "sistemy-tumanoobrazovaniya",
    "canonical": "https://exp76.ru/services/sistemy-tumanoobrazovaniya/",
    "archive_policy": "redirect_to_hub"
  },
  "S12": {
    "service_id": "S12",
    "topic_key": "S12",
    "hub_post_id": 9138,
    "hub_slug": "fundament-na-zhelezobetonnykh-svajakh",
    "grouping_slug": "fundament-na-zhelezobetonnykh-svajakh",
    "canonical": "https://exp76.ru/services/fundament-na-zhelezobetonnykh-svajakh/",
    "archive_policy": "redirect_to_hub"
  },
  "S13": {
    "service_id": "S13",
    "topic_key": "S13",
    "hub_post_id": 9312,
    "hub_slug": "navesy-iz-metalla",
    "grouping_slug": "navesy-iz-metalla",
    "canonical": "https://exp76.ru/services/navesy-iz-metalla/",
    "archive_policy": "redirect_to_hub"
  },
  "S14": {
    "service_id": "S14",
    "topic_key": "S14",
    "hub_post_id": 9775,
    "hub_slug": "kaminy-pechi-barbekju",
    "grouping_slug": "kaminy-pechi-barbekju",
    "canonical": "https://exp76.ru/services/kaminy-pechi-barbekju/",
    "archive_policy": "redirect_to_hub"
  },
  "S15": {
    "service_id": "S15",
    "topic_key": "S15",
    "hub_post_id": 9838,
    "hub_slug": "snos-i-demontazh-zdanijj-domov",
    "grouping_slug": "snos-i-demontazh-zdanijj-domov",
    "canonical": "https://exp76.ru/services/snos-i-demontazh-zdanijj-domov/",
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

function land76wp_has_managed_service_hub_owner($post_id)
{
    $owner = (string) get_post_meta((int) $post_id, '_land76_import_owner', true);

    return hash_equals('land76-service-hubs', $owner);
}

/** Detect both intact ownership and orphaned managed runtime records. */
function land76wp_claims_managed_service_hub_post($post_id)
{
    $post_id = (int) $post_id;
    if (land76wp_has_managed_service_hub_owner($post_id)) {
        return true;
    }

    $page_key = (string) get_post_meta($post_id, '_land76_page_key', true);

    return preg_match('/^S(?:[1-9]|1[0-5])-(?:CHILD|ARTICLE|GEO)-[A-Z0-9-]+$/D', $page_key) === 1;
}

/**
 * Validate every runtime boundary before a claimed managed post is rendered.
 *
 * A non-null result is the only supported admission ticket for managed child,
 * article and regional pages. Merely owning one matching meta field is not
 * sufficient.
 */
function land76wp_managed_page_contract($post_id)
{
    $post_id = (int) $post_id;
    $owner = (string) get_post_meta($post_id, '_land76_import_owner', true);
    if ($post_id < 1 || !hash_equals('land76-service-hubs', $owner)) {
        return null;
    }

    $post = get_post($post_id);
    if (!$post instanceof WP_Post || $post->post_status !== 'publish') {
        return null;
    }

    $page_key = (string) get_post_meta($post_id, '_land76_page_key', true);
    $service_id = strtoupper((string) get_post_meta($post_id, '_land76_service_id', true));
    $topic_key = strtoupper((string) get_post_meta($post_id, '_land76_topic_key', true));
    $stored_canonical = trailingslashit((string) get_post_meta($post_id, '_land76_canonical', true));
    $actual_canonical = trailingslashit((string) get_permalink($post_id));
    $hub = land76wp_service_hub_by_service_id($service_id);

    if ($page_key === ''
        || $service_id === ''
        || !hash_equals($service_id, $topic_key)
        || strpos($page_key, $service_id . '-') !== 0
        || $stored_canonical === '/'
        || $actual_canonical === '/'
        || !hash_equals($stored_canonical, $actual_canonical)
        || $hub === null) {
        return null;
    }

    $role = '';
    if (preg_match('/^S(?:[1-9]|1[0-5])-CHILD-[A-Z0-9-]+$/D', $page_key)) {
        $role = 'child';
        $valid_post_shape = ($post->post_type === 'post' && has_category(74, $post_id) && !has_category(72, $post_id))
            || ($post->post_type === 'page' && hash_equals('servicepost.php', (string) get_page_template_slug($post_id)));
    } elseif (preg_match('/^S(?:[1-9]|1[0-5])-ARTICLE-[A-Z0-9-]+$/D', $page_key)) {
        $role = 'article';
        $valid_post_shape = $post->post_type === 'post' && has_category(72, $post_id) && !has_category(74, $post_id);
    } elseif (preg_match('/^S(?:[1-9]|1[0-5])-GEO-[A-Z0-9-]+$/D', $page_key)) {
        $role = 'geo';
        $valid_post_shape = $post->post_type === 'page'
            && hash_equals('page-service-hub-region.php', (string) get_page_template_slug($post_id));
    } else {
        return null;
    }

    if (!$valid_post_shape) {
        return null;
    }

    return array(
        'post_id' => $post_id,
        'post' => $post,
        'post_type' => $post->post_type,
        'post_status' => $post->post_status,
        'page_key' => $page_key,
        'service_id' => $service_id,
        'topic_key' => $topic_key,
        'canonical' => $stored_canonical,
        'current_url' => $actual_canonical,
        'role' => $role,
        'hub' => $hub,
    );
}

function land76wp_service_hub_for_post($post_id)
{
    $post_id = (int) $post_id;
    foreach (land76wp_service_hub_registry() as $hub) {
        if ((int) $hub['hub_post_id'] === $post_id) {
            return $hub;
        }
    }

    $contract = land76wp_managed_page_contract($post_id);

    return is_array($contract) ? $contract['hub'] : null;
}

function land76wp_is_managed_service_hub_post($post_id)
{
    return land76wp_managed_page_contract($post_id) !== null;
}

function land76wp_service_hub_schema_context($post_id)
{
    $post_id = (int) $post_id;
    $hub = null;
    $role = '';
    $current_url = '';

    foreach (land76wp_service_hub_registry() as $registered_hub) {
        if ((int) $registered_hub['hub_post_id'] === $post_id) {
            $hub = $registered_hub;
            $role = 'hub';
            $current_url = trailingslashit((string) $registered_hub['canonical']);
            break;
        }
    }

    if ($role === 'hub') {
        $post = get_post($post_id);
        $actual_url = trailingslashit((string) get_permalink($post_id));
        if (!$post instanceof WP_Post
            || $post->post_type !== 'page'
            || $post->post_status !== 'publish'
            || $actual_url === '/'
            || !hash_equals($current_url, $actual_url)) {
            return null;
        }
    } else {
        $contract = land76wp_managed_page_contract($post_id);
        if (!is_array($contract)) {
            return null;
        }
        $post = $contract['post'];
        $hub = $contract['hub'];
        $role = $contract['role'];
        $current_url = $contract['current_url'];
    }

    $title = (string) get_the_title($post_id);
    $description = '';
    $image_url = '';
    $image_alt = '';
    if ($role === 'hub') {
        $service_v2 = function_exists('land76_service_v2_current')
            ? land76_service_v2_current()
            : null;
        if (!is_array($service_v2)
            || empty($service_v2['hero']['title'])
            || empty($service_v2['seo']['description'])) {
            return null;
        }

        $title = (string) $service_v2['hero']['title'];
        $description = (string) $service_v2['seo']['description'];
        $image_url = isset($service_v2['hero']['image']['url'])
            ? (string) $service_v2['hero']['image']['url']
            : '';
        $image_alt = isset($service_v2['hero']['image']['alt'])
            ? (string) $service_v2['hero']['image']['alt']
            : '';
    } else {
        $description = (string) get_post_meta($post_id, '_aioseo_description', true);
        if ($description === '') {
            $description = wp_strip_all_tags((string) get_the_excerpt($post_id));
        }
        $image_url = (string) get_post_meta($post_id, '_land76_main_image_url', true);
        $image_alt = (string) get_post_meta($post_id, '_land76_main_image_alt', true);
    }
    if ($image_url === '' && has_post_thumbnail($post_id)) {
        $image_url = (string) get_the_post_thumbnail_url($post_id, 'full');
    }

    return array(
        'post_id' => $post_id,
        'post' => $post,
        'hub' => $hub,
        'role' => $role,
        'current_url' => $current_url,
        'title' => wp_strip_all_tags($title),
        'description' => wp_strip_all_tags($description),
        'image_url' => esc_url_raw($image_url),
        'image_alt' => sanitize_text_field($image_alt),
    );
}

function land76wp_service_hub_managed_meta_value($meta_key, $fallback)
{
    if (!is_singular()) {
        return $fallback;
    }
    $post_id = (int) get_queried_object_id();
    $contract = land76wp_managed_page_contract($post_id);
    if (!is_array($contract)) {
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

/** Keep AIOSEO from printing a second graph beside the managed theme graph. */
function land76wp_service_hub_disable_aioseo_schema($disabled)
{
    if ($disabled || !is_singular()) {
        return (bool) $disabled;
    }

    $context = land76wp_service_hub_schema_context(get_queried_object_id());

    return is_array($context);
}

/** Empty older AIOSEO graph output when its boolean disable filter is unavailable. */
function land76wp_service_hub_filter_aioseo_schema_output($schema)
{
    if (!is_singular()) {
        return $schema;
    }

    $context = land76wp_service_hub_schema_context(get_queried_object_id());
    if (is_array($context)) {
        return array();
    }

    return $schema;
}

add_filter('aioseo_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('aioseo_description', 'land76wp_service_hub_filter_managed_description', 999);
add_filter('aioseo_canonical_url', 'land76wp_service_hub_filter_managed_canonical', 999);
add_filter('aioseo_schema_disable', 'land76wp_service_hub_disable_aioseo_schema', 999);
add_filter('aioseo_schema_output', 'land76wp_service_hub_filter_aioseo_schema_output', 999);
add_filter('wpseo_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('wpseo_metadesc', 'land76wp_service_hub_filter_managed_description', 999);
add_filter('wpseo_canonical', 'land76wp_service_hub_filter_managed_canonical', 999);
add_filter('pre_get_document_title', 'land76wp_service_hub_filter_managed_title', 999);
add_filter('get_canonical_url', 'land76wp_service_hub_filter_managed_canonical', 999);
