<?php
if (!defined('ABSPATH')) {
    exit;
}

/**
 * Isolated, fail-closed importer for the service-hubs release.
 *
 * Preview is read-only. Stage writes only owned drafts. Publish verifies the
 * complete staged release, then changes post_status and nothing else.
 */

function land76wp_service_hubs_expected_release_id()
{
    return 'service-hubs-2026-08-28';
}

/** Return the frozen non-hub inventory admitted by this release importer. */
function land76wp_service_hubs_expected_page_keys()
{
    static $page_keys = null;
    if (is_array($page_keys)) {
        return $page_keys;
    }

    $json = <<<'LAND76_SERVICE_HUB_EXPECTED_PAGE_KEYS_JSON'
[
  "S1-CHILD-3D",
  "S1-CHILD-DENDROPLAN",
  "S1-CHILD-MASTERPLAN",
  "S1-CHILD-RELIEF",
  "S1-CHILD-SKETCH",
  "S10-ARTICLE-POND-CARE",
  "S10-ARTICLE-POND-DIY",
  "S10-CHILD-DECORATIVE-POND",
  "S10-CHILD-FOUNTAIN",
  "S10-CHILD-STREAM",
  "S10-CHILD-SWIMMING-POND",
  "S10-CHILD-WATERFALL-CASCADE",
  "S11-ARTICLE-PRESSURE",
  "S11-CHILD-CAFE-OUTDOOR",
  "S11-CHILD-GREENHOUSE",
  "S11-CHILD-TERRACE-VERANDA",
  "S12-ARTICLE-PILE-PROS-CONS",
  "S12-CHILD-BATHHOUSE",
  "S12-CHILD-DRIVING",
  "S12-CHILD-PRIVATE-HOUSE",
  "S13-ARTICLE-CARPORT-DIY",
  "S13-ARTICLE-POLYCARBONATE-DIY",
  "S13-CHILD-BARBECUE",
  "S13-CHILD-CARPORT",
  "S13-CHILD-POLYCARBONATE-HOME",
  "S13-CHILD-TERRACE",
  "S14-ARTICLE-BRICK-GRILL-DIY",
  "S14-ARTICLE-HEATING-STOVE-DIY",
  "S14-CHILD-BARBECUE",
  "S14-CHILD-BRICK-GRILL",
  "S14-CHILD-CAULDRON-SMOKEHOUSE",
  "S14-CHILD-FIREPLACE",
  "S14-CHILD-HEATING-STOVE",
  "S15-ARTICLE-DEMOLITION-PERMIT",
  "S15-CHILD-COUNTRY-HOUSE",
  "S15-CHILD-DANGEROUS-BUILDING",
  "S15-CHILD-DEBRIS",
  "S15-CHILD-MANUAL",
  "S15-CHILD-MECHANIZED",
  "S15-CHILD-PRIVATE-HOUSE",
  "S2-CHILD-RESTORE",
  "S2-CHILD-ROLL",
  "S2-CHILD-SEED",
  "S2-CHILD-SOIL",
  "S3-CHILD-CONIFERS",
  "S3-CHILD-FRUIT",
  "S3-CHILD-HEDGE",
  "S3-CHILD-LARGE",
  "S3-CHILD-SHRUBS",
  "S4-CHILD-FLOWERBEDS",
  "S4-CHILD-LAWN-CARE",
  "S4-CHILD-PEST",
  "S4-CHILD-SHRUB-PRUNING",
  "S4-CHILD-TREE-PRUNING",
  "S5-CHILD-CULTIVATION",
  "S5-CHILD-FILL",
  "S5-CHILD-LEVEL",
  "S5-CHILD-MACHINERY",
  "S5-CHILD-VERTICAL",
  "S6-CHILD-CONCRETE",
  "S6-CHILD-STONE",
  "S6-CHILD-WOOD",
  "S7-CHILD-ARCHITECTURAL",
  "S7-CHILD-DESIGN",
  "S7-CHILD-HOLIDAY",
  "S7-CHILD-INSTALL",
  "S7-CHILD-LANDSCAPE",
  "S8-CHILD-CONCRETE",
  "S8-CHILD-GRAVEL",
  "S8-CHILD-PARKING",
  "S8-CHILD-PIPE",
  "S9-ARTICLE-OVERGROWN-SITE",
  "S9-ARTICLE-STUMP-DIY",
  "S9-CHILD-CLEARING",
  "S9-CHILD-STUMPS",
  "S9-CHILD-TREE-REMOVAL"
]
LAND76_SERVICE_HUB_EXPECTED_PAGE_KEYS_JSON;
    $decoded = json_decode($json, true);
    if (!is_array($decoded)
        || count($decoded) !== 76
        || array_keys($decoded) !== range(0, 75)
        || count(array_unique($decoded, SORT_STRING)) !== 76) {
        throw new RuntimeException('Invalid frozen service-hub page-key inventory.');
    }
    $sorted = $decoded;
    sort($sorted, SORT_STRING);
    if ($sorted !== $decoded) {
        throw new RuntimeException('Frozen service-hub page-key inventory must be sorted.');
    }

    $page_keys = $decoded;
    return $page_keys;
}

function land76wp_service_hubs_import_owner()
{
    return 'land76-service-hubs';
}

function land76wp_service_hubs_active_release_option_name()
{
    return 'land76_service_hubs_active_release_id';
}

/** Capture the marker state needed to deactivate or restore a release manually. */
function land76wp_service_hubs_active_release_snapshot()
{
    $option_name = land76wp_service_hubs_active_release_option_name();
    $option_value = get_option($option_name, null);

    return array(
        'option_name' => $option_name,
        'option_exists' => $option_value !== null,
        'option_value' => $option_value === null ? '' : (string) $option_value,
    );
}

/** Persist activation only for this frozen release and verify the stored value. */
function land76wp_service_hubs_activate_verified_release($release_id)
{
    $release_id = is_string($release_id) ? $release_id : '';
    if ($release_id === '' || !hash_equals(land76wp_service_hubs_expected_release_id(), $release_id)) {
        return land76wp_service_hubs_error('activation_release_mismatch', $release_id);
    }

    $option_name = land76wp_service_hubs_active_release_option_name();
    if (function_exists('land76_service_v2_active_release_option_name')
        && !hash_equals($option_name, (string) land76_service_v2_active_release_option_name())) {
        return land76wp_service_hubs_error('activation_option_mismatch');
    }

    // update_option() legitimately returns false when the exact value is already stored.
    update_option($option_name, $release_id, false);
    $stored_release_id = get_option($option_name, '');
    if (!is_string($stored_release_id) || !hash_equals($release_id, $stored_release_id)) {
        return land76wp_service_hubs_error('release_activation_failed', $release_id);
    }

    return '';
}

function land76wp_service_hubs_reuse_contracts()
{
    static $contracts = null;
    if (is_array($contracts)) {
        return $contracts;
    }

    $json = <<<'LAND76_SERVICE_HUB_REUSE_CONTRACTS_JSON'
{
  "S7-CHILD-HOLIDAY": {
    "page_key": "S7-CHILD-HOLIDAY",
    "service_id": "S7",
    "post_id": 10381,
    "post_type": "page",
    "post_status": "publish",
    "slug": "novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti",
    "parent_id": 0,
    "current_url": "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
    "target_url": "https://exp76.ru/novogodnee-osveshhenie-zagorodnogo-doma-v-rybinske-i-jaroslavskojj-oblasti/",
    "legacy_template": "servicepost.php",
    "target_template": "servicepost.php"
  }
}
LAND76_SERVICE_HUB_REUSE_CONTRACTS_JSON;
    $decoded = json_decode($json, true);
    if (!is_array($decoded) || $decoded === array()) {
        throw new RuntimeException('Invalid frozen service-hub reuse contracts.');
    }
    $required_fields = array(
        'page_key',
        'service_id',
        'post_id',
        'post_type',
        'post_status',
        'slug',
        'parent_id',
        'current_url',
        'target_url',
        'legacy_template',
        'target_template',
    );
    sort($required_fields, SORT_STRING);
    foreach ($decoded as $page_key => $contract) {
        $contract_fields = is_array($contract) ? array_keys($contract) : array();
        sort($contract_fields, SORT_STRING);
        if (!is_string($page_key)
            || preg_match('/^S(?:[1-9]|1[0-5])-CHILD-[A-Z0-9-]+$/D', $page_key) !== 1
            || !is_array($contract)
            || $contract_fields !== $required_fields
            || !hash_equals($page_key, (string) $contract['page_key'])
            || preg_match('/^S(?:[1-9]|1[0-5])$/D', (string) $contract['service_id']) !== 1
            || strpos($page_key, (string) $contract['service_id'] . '-CHILD-') !== 0
            || !is_int($contract['post_id'])
            || $contract['post_id'] <= 0
            || !hash_equals('page', (string) $contract['post_type'])
            || !hash_equals('publish', (string) $contract['post_status'])
            || preg_match('/^[a-z0-9-]+$/D', (string) $contract['slug']) !== 1
            || !is_int($contract['parent_id'])
            || $contract['parent_id'] < 0
            || !is_string($contract['current_url'])
            || !is_string($contract['target_url'])
            || !hash_equals($contract['current_url'], $contract['target_url'])
            || !hash_equals($contract['current_url'], land76wp_service_hubs_normalize_url($contract['current_url']))
            || !is_string($contract['legacy_template'])
            || !hash_equals('servicepost.php', (string) $contract['target_template'])) {
            throw new RuntimeException('Invalid frozen service-hub reuse contract: ' . (string) $page_key);
        }
    }
    $contracts = $decoded;

    return $contracts;
}

function land76wp_service_hubs_reuse_contract_for_item(array $item)
{
    $page_key = isset($item['page_key']) && is_string($item['page_key'])
        ? $item['page_key']
        : '';
    $contracts = land76wp_service_hubs_reuse_contracts();

    return isset($contracts[$page_key]) ? $contracts[$page_key] : null;
}

function land76wp_service_hubs_default_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/service-hubs-import.json';
}

function land76wp_service_hubs_default_release_manifest_path()
{
    return trailingslashit(get_template_directory()) . 'import/service-hubs-release-manifest.json';
}

function land76wp_service_hubs_default_acf_json_paths()
{
    $directory = trailingslashit(get_template_directory()) . 'import/';
    return array(
        $directory . 'acf-service-hub-relations.json',
        $directory . 'acf-seo-blog-post-fields.json',
    );
}

function land76wp_service_hubs_empty_result()
{
    return array(
        'applicable' => false,
        'planned' => 0,
        'created' => 0,
        'updated' => 0,
        'unchanged' => 0,
        'unresolved_cases' => array(),
        'errors' => array(),
        'rollback_snapshot' => array(),
        'operations' => array(),
    );
}

function land76wp_service_hubs_error($code, $detail = '')
{
    return $detail === '' ? (string) $code : (string) $code . ': ' . (string) $detail;
}

function land76wp_service_hubs_is_list(array $value)
{
    if ($value === array()) {
        return true;
    }

    return array_keys($value) === range(0, count($value) - 1);
}

function land76wp_service_hubs_reject_forbidden_keys(array $payload, $path = '$')
{
    $errors = array();
    $forbidden = array('cleanup', 'delete_stale_posts', 'delete_stale_terms');

    foreach ($payload as $key => $value) {
        $child_path = $path . '[' . (string) $key . ']';
        if (is_string($key) && in_array($key, $forbidden, true)) {
            $errors[] = land76wp_service_hubs_error('forbidden_payload_key', $child_path);
        }
        if (is_array($value)) {
            $errors = array_merge($errors, land76wp_service_hubs_reject_forbidden_keys($value, $child_path));
        }
    }

    return $errors;
}

function land76wp_service_hubs_normalize_url($url)
{
    $url = trim((string) $url);
    if ($url === '') {
        return '';
    }

    $parts = wp_parse_url($url);
    if (!is_array($parts) || !isset($parts['scheme'], $parts['host'], $parts['path'])) {
        return '';
    }
    if ($parts['scheme'] !== 'https' || strtolower($parts['host']) !== 'exp76.ru') {
        return '';
    }
    if (!empty($parts['query']) || !empty($parts['fragment']) || !empty($parts['user']) || !empty($parts['pass'])) {
        return '';
    }

    $path = '/' . trim($parts['path'], '/') . '/';
    return 'https://exp76.ru' . $path;
}

function land76wp_service_hubs_sort_recursive($value)
{
    if (!is_array($value)) {
        return $value;
    }

    foreach ($value as $key => $child) {
        $value[$key] = land76wp_service_hubs_sort_recursive($child);
    }
    if (!land76wp_service_hubs_is_list($value)) {
        ksort($value, SORT_STRING);
    }

    return $value;
}

function land76wp_service_hubs_item_checksum(array $item)
{
    unset($item['checksum']);
    $canonical = land76wp_service_hubs_sort_recursive($item);
    $encoded = wp_json_encode($canonical, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);

    return $encoded === false ? '' : hash('sha256', $encoded);
}

function land76wp_service_hubs_expected_item_url(array $item)
{
    $reuse_contract = land76wp_service_hubs_reuse_contract_for_item($item);
    if (is_array($reuse_contract)) {
        return (string) $reuse_contract['target_url'];
    }
    $slug = isset($item['slug']) ? (string) $item['slug'] : '';
    if (isset($item['role']) && $item['role'] === 'geo') {
        $parent_slug = isset($item['city_parent_slug']) ? (string) $item['city_parent_slug'] : '';
        return 'https://exp76.ru/' . $parent_slug . '/' . $slug . '/';
    }

    return 'https://exp76.ru/' . $slug . '/';
}

function land76wp_service_hubs_validate_local_evidence($value, $page_key)
{
    if (!is_array($value) || !land76wp_service_hubs_is_list($value) || $value === array()) {
        return array(land76wp_service_hubs_error('missing_local_evidence', $page_key));
    }

    $errors = array();
    foreach ($value as $index => $evidence) {
        $text = '';
        if (is_string($evidence)) {
            $text = trim(wp_strip_all_tags($evidence));
        } elseif (is_array($evidence) && isset($evidence['text']) && is_string($evidence['text'])) {
            $text = trim(wp_strip_all_tags($evidence['text']));
        }
        if ($text === '' || strpos($text, "\xEF\xBF\xBD") !== false) {
            $errors[] = land76wp_service_hubs_error('invalid_local_evidence', $page_key . '[' . (string) $index . ']');
        }
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_validate_relation_list(array $references, $field, $page_key)
{
    $errors = array();
    $seen = array();
    foreach ($references as $index => $reference) {
        if (!is_string($reference) || trim($reference) === '') {
            $errors[] = land76wp_service_hubs_error('invalid_relation', $page_key . '.' . $field . '[' . (string) $index . ']');
            continue;
        }
        $reference = trim($reference);
        if (isset($seen[$reference])) {
            $errors[] = land76wp_service_hubs_error('duplicate_relation', $page_key . ' -> ' . $reference);
        }
        $seen[$reference] = true;
    }

    return $errors;
}

function land76wp_service_hubs_validate_related_service_references(array $references, $page_key)
{
    $errors = array();
    $seen = array();
    foreach ($references as $index => $reference) {
        $slug = '';
        $canonical = '';
        if (is_string($reference)) {
            $slug = trim($reference);
            $canonical = 'https://exp76.ru/' . $slug . '/';
        } elseif (is_array($reference)
            && isset($reference['slug'], $reference['canonical'])
            && is_string($reference['slug'])
            && is_string($reference['canonical'])) {
            $slug = trim($reference['slug']);
            $canonical = land76wp_service_hubs_normalize_url($reference['canonical']);
            if (!hash_equals($reference['canonical'], $canonical)) {
                $canonical = '';
            }
        }
        if ($slug === '' || $slug !== sanitize_title($slug) || $canonical === '') {
            $errors[] = land76wp_service_hubs_error('invalid_related_service_reference', $page_key . '[' . (string) $index . ']');
            continue;
        }
        $fingerprint = $slug . '|' . $canonical;
        if (isset($seen[$fingerprint])) {
            $errors[] = land76wp_service_hubs_error('duplicate_relation', $page_key . ' -> ' . $slug);
        }
        $seen[$fingerprint] = true;
    }

    return $errors;
}

function land76wp_service_hubs_validate_presentation_images($value, $page_key)
{
    $errors = array();
    $roles = array('hero', 'context', 'card');
    $url_prefix = 'https://exp76.ru/wp-content/themes/land76wp/generated/context/';
    if (!is_array($value) || land76wp_service_hubs_is_list($value)) {
        return array(land76wp_service_hubs_error('invalid_presentation_images', $page_key));
    }
    foreach (array_keys($value) as $role) {
        if (!is_string($role) || !in_array($role, $roles, true)) {
            $errors[] = land76wp_service_hubs_error('invalid_presentation_image_role', $page_key);
        }
    }
    foreach ($roles as $role) {
        if (!array_key_exists($role, $value)
            || !is_array($value[$role])
            || land76wp_service_hubs_is_list($value[$role])) {
            $errors[] = land76wp_service_hubs_error('invalid_presentation_image', $page_key . '.' . $role);
            continue;
        }
        $image = $value[$role];
        $keys = array_keys($image);
        sort($keys, SORT_STRING);
        if ($keys !== array('alt', 'url')) {
            $errors[] = land76wp_service_hubs_error('invalid_presentation_image', $page_key . '.' . $role);
            continue;
        }
        $image_url = is_string($image['url']) ? trim($image['url']) : '';
        $image_alt = is_string($image['alt']) ? trim($image['alt']) : '';
        $alt_length = preg_match_all('/./us', $image_alt, $alt_characters);
        if ($image_url === ''
            || $image_alt === ''
            || $image_url !== $image['url']
            || $image_alt !== $image['alt']
            || $alt_length === false
            || $alt_length < 12) {
            $errors[] = land76wp_service_hubs_error('invalid_presentation_image', $page_key . '.' . $role);
            continue;
        }
        $pattern = '#^' . preg_quote($url_prefix, '#') . '(context-photo-[a-z0-9]+(?:-[a-z0-9]+)*\.webp)$#D';
        if (!preg_match($pattern, $image_url, $matches)) {
            $errors[] = land76wp_service_hubs_error('invalid_presentation_image_url', $page_key . '.' . $role);
            continue;
        }
        $image_path = get_template_directory() . '/generated/context/' . $matches[1];
        if (!is_file($image_path)) {
            $errors[] = land76wp_service_hubs_error('unresolved_presentation_image', $page_key . '.' . $role);
        }
    }

    return $errors;
}

function land76wp_service_hubs_presentation_meta_keys()
{
    return array(
        'hero' => array(
            'url' => '_land76_hero_image_url',
            'alt' => '_land76_hero_image_alt',
        ),
        'context' => array(
            'url' => '_land76_context_image_url',
            'alt' => '_land76_context_image_alt',
        ),
        'card' => array(
            'url' => '_land76_card_image_url',
            'alt' => '_land76_card_image_alt',
        ),
    );
}

function land76wp_service_hubs_validate_item(array $item, array &$seen_page_keys, array &$seen_canonicals)
{
    $errors = array();
    $required_strings = array('page_key', 'service_id', 'topic_key', 'role', 'slug', 'canonical', 'post_title', 'checksum');
    foreach ($required_strings as $key) {
        if (!isset($item[$key]) || !is_string($item[$key]) || trim($item[$key]) === '') {
            $errors[] = land76wp_service_hubs_error('missing_item_field', $key);
        }
    }
    if ($errors !== array()) {
        return $errors;
    }

    $page_key = (string) $item['page_key'];
    $service_id = (string) $item['service_id'];
    $topic_key = (string) $item['topic_key'];
    $role = (string) $item['role'];
    $slug = (string) $item['slug'];
    $canonical = (string) $item['canonical'];
    $checksum = strtolower((string) $item['checksum']);

    if (!preg_match('/^S(?:[1-9]|1[0-5])-(?:CHILD|ARTICLE|GEO)-[A-Z0-9-]+$/', $page_key)) {
        $errors[] = land76wp_service_hubs_error('invalid_page_key', $page_key);
    }
    if (!preg_match('/^S(?:[1-9]|1[0-5])$/', $service_id) || !hash_equals($service_id, $topic_key)) {
        $errors[] = land76wp_service_hubs_error('ownership_drift', $page_key);
    }
    if (land76wp_service_hub_by_service_id($service_id) === null) {
        $errors[] = land76wp_service_hubs_error('unknown_service_id', $service_id);
    }
    if (!in_array($role, array('child_service', 'article', 'geo'), true)) {
        $errors[] = land76wp_service_hubs_error('unsupported_role', $role);
    } else {
        $role_tokens = array('child_service' => 'CHILD', 'article' => 'ARTICLE', 'geo' => 'GEO');
        $expected_role_token = $role_tokens[$role];
        $expected_page_key_prefix = $service_id . '-' . $expected_role_token . '-';
        if (strpos($page_key, $expected_page_key_prefix) !== 0) {
            $errors[] = land76wp_service_hubs_error('page_key_ownership_mismatch', $page_key);
        }
    }
    if ($slug !== sanitize_title($slug) || $slug === '') {
        $errors[] = land76wp_service_hubs_error('invalid_slug', $slug);
    }
    if (!hash_equals($canonical, land76wp_service_hubs_normalize_url($canonical))) {
        $errors[] = land76wp_service_hubs_error('invalid_canonical', $canonical);
    } elseif (!hash_equals($canonical, land76wp_service_hubs_expected_item_url($item))) {
        $errors[] = land76wp_service_hubs_error('canonical_slug_mismatch', $page_key);
    }
    if ((string) $item['checksum'] !== $checksum || !preg_match('/^[a-f0-9]{64}$/', $checksum)) {
        $errors[] = land76wp_service_hubs_error('invalid_checksum', $page_key);
    } else {
        $computed_checksum = land76wp_service_hubs_item_checksum($item);
        if ($computed_checksum === '' || !hash_equals($computed_checksum, $checksum)) {
            $errors[] = land76wp_service_hubs_error('checksum_mismatch', $page_key);
        }
    }
    if (isset($seen_page_keys[$page_key])) {
        $errors[] = land76wp_service_hubs_error('duplicate_page_key', $page_key);
    }
    if (isset($seen_canonicals[$canonical])) {
        $errors[] = land76wp_service_hubs_error('duplicate_canonical', $canonical);
    }
    $seen_page_keys[$page_key] = true;
    $seen_canonicals[$canonical] = true;

    if (!isset($item['post_content']) || !is_string($item['post_content']) || trim(wp_strip_all_tags($item['post_content'])) === '') {
        $errors[] = land76wp_service_hubs_error('missing_item_field', 'post_content');
    }
    if (array_key_exists('post_excerpt', $item) && !is_string($item['post_excerpt'])) {
        $errors[] = land76wp_service_hubs_error('invalid_item_field', 'post_excerpt');
    }
    if (!array_key_exists('seo', $item)) {
        $errors[] = land76wp_service_hubs_error('missing_seo', $page_key);
    } elseif (!is_array($item['seo'])) {
        $errors[] = land76wp_service_hubs_error('invalid_seo', $page_key);
    } else {
        foreach (array('title', 'description') as $seo_key) {
            if (!isset($item['seo'][$seo_key])
                || !is_string($item['seo'][$seo_key])
                || trim(wp_strip_all_tags($item['seo'][$seo_key])) === '') {
                $errors[] = land76wp_service_hubs_error('invalid_seo', $page_key . '.' . $seo_key);
            }
        }
    }
    if (!isset($item['main_image']) || !is_array($item['main_image'])) {
        $errors[] = land76wp_service_hubs_error('missing_item_field', 'main_image');
    } else {
        $image_url = isset($item['main_image']['url']) && is_string($item['main_image']['url'])
            ? trim($item['main_image']['url'])
            : '';
        $image_alt = isset($item['main_image']['alt']) && is_string($item['main_image']['alt'])
            ? trim($item['main_image']['alt'])
            : '';
        if ($image_url === '' || $image_alt === '') {
            $errors[] = land76wp_service_hubs_error('invalid_main_image', $page_key);
        } elseif (!function_exists('attachment_url_to_postid')) {
            $errors[] = land76wp_service_hubs_error('media_api_unavailable', $page_key);
        } else {
            $attachment_id = (int) attachment_url_to_postid($image_url);
            $mime_type = $attachment_id ? (string) get_post_mime_type($attachment_id) : '';
            if (!$attachment_id || strpos($mime_type, 'image/') !== 0) {
                $errors[] = land76wp_service_hubs_error('unresolved_main_image', $image_url);
            }
        }
    }
    if (array_key_exists('presentation_images', $item)) {
        $errors = array_merge(
            $errors,
            land76wp_service_hubs_validate_presentation_images($item['presentation_images'], $page_key)
        );
    }

    foreach (array('case_ids', 'related_service_page_keys', 'related_service_slugs', 'related_article_page_keys') as $list_key) {
        if (array_key_exists($list_key, $item) && (!is_array($item[$list_key]) || !land76wp_service_hubs_is_list($item[$list_key]))) {
            $errors[] = land76wp_service_hubs_error('invalid_item_list', $list_key);
        }
    }
    foreach (array('related_service_page_keys', 'related_article_page_keys') as $relation_field) {
        if (isset($item[$relation_field]) && is_array($item[$relation_field]) && land76wp_service_hubs_is_list($item[$relation_field])) {
            $errors = array_merge(
                $errors,
                land76wp_service_hubs_validate_relation_list($item[$relation_field], $relation_field, $page_key)
            );
        }
    }
    if (isset($item['related_service_slugs']) && is_array($item['related_service_slugs']) && land76wp_service_hubs_is_list($item['related_service_slugs'])) {
        $errors = array_merge(
            $errors,
            land76wp_service_hubs_validate_related_service_references($item['related_service_slugs'], $page_key)
        );
    }
    if (array_key_exists('related_service_page_keys', $item) && array_key_exists('related_service_slugs', $item)) {
        $errors[] = land76wp_service_hubs_error('ambiguous_related_services', $page_key);
    }
    if (array_key_exists('acf', $item)) {
        if (!is_array($item['acf'])) {
            $errors[] = land76wp_service_hubs_error('invalid_acf', $page_key);
        } else {
            foreach (array_keys($item['acf']) as $field_name) {
                if (!is_string($field_name)
                    || !preg_match('/^[A-Za-z][A-Za-z0-9_]*$/', $field_name)
                    || strpos($field_name, '_land76_') === 0
                    || strpos($field_name, '_wp_') === 0
                    || strpos($field_name, '_aioseo_') === 0) {
                    $errors[] = land76wp_service_hubs_error('forbidden_acf_field', $page_key);
                }
            }
            foreach (array('selected_works_posts', 'selected_real_projects', 'blogseo_related_services') as $managed_field) {
                if (array_key_exists($managed_field, $item['acf'])) {
                    $errors[] = land76wp_service_hubs_error('ambiguous_managed_acf_field', $page_key . '.' . $managed_field);
                }
            }
        }
    }

    if ($role === 'geo') {
        if (!isset($item['city_parent_slug']) || !is_string($item['city_parent_slug']) || $item['city_parent_slug'] !== sanitize_title($item['city_parent_slug'])) {
            $errors[] = land76wp_service_hubs_error('invalid_city_parent_slug', $page_key);
        }
        $local_evidence = array_key_exists('local_evidence', $item) ? $item['local_evidence'] : null;
        $errors = array_merge($errors, land76wp_service_hubs_validate_local_evidence($local_evidence, $page_key));
    }

    return $errors;
}

function land76wp_service_hubs_validate_payload(array $payload)
{
    $errors = land76wp_service_hubs_reject_forbidden_keys($payload);
    if (!isset($payload['schema_version']) || !is_int($payload['schema_version']) || $payload['schema_version'] !== 1) {
        $errors[] = land76wp_service_hubs_error('invalid_schema_version');
    }
    if (!isset($payload['release_id']) || !is_string($payload['release_id']) || !hash_equals(land76wp_service_hubs_expected_release_id(), $payload['release_id'])) {
        $errors[] = land76wp_service_hubs_error('invalid_release_id');
    }
    if (!isset($payload['release_status']) || !in_array($payload['release_status'], array('draft', 'ready'), true)) {
        $errors[] = land76wp_service_hubs_error('invalid_release_status');
    }
    if (!isset($payload['manifest_sha256'])
        || !is_string($payload['manifest_sha256'])
        || !preg_match('/^[a-f0-9]{64}$/', $payload['manifest_sha256'])
        || hash_equals(str_repeat('0', 64), $payload['manifest_sha256'])) {
        $errors[] = land76wp_service_hubs_error('invalid_manifest_sha256');
    }
    if (!isset($payload['items']) || !is_array($payload['items']) || !land76wp_service_hubs_is_list($payload['items'])) {
        $errors[] = land76wp_service_hubs_error('invalid_items');
        return array_values(array_unique($errors));
    }
    if (isset($payload['release_status']) && $payload['release_status'] === 'draft' && $payload['items'] !== array()) {
        $errors[] = land76wp_service_hubs_error('draft_payload_must_be_empty');
    }
    if (isset($payload['release_status']) && $payload['release_status'] === 'ready' && $payload['items'] === array()) {
        $errors[] = land76wp_service_hubs_error('empty_payload');
    }
    if (isset($payload['release_status']) && $payload['release_status'] === 'ready') {
        $errors = array_merge(
            $errors,
            land76wp_service_hubs_validate_expected_inventory($payload['items'], 'payload')
        );
    }
    if (count(land76wp_service_hub_registry()) !== 15) {
        $errors[] = land76wp_service_hubs_error('invalid_registry');
    }

    $seen_page_keys = array();
    $seen_canonicals = array();
    foreach ($payload['items'] as $index => $item) {
        if (!is_array($item)) {
            $errors[] = land76wp_service_hubs_error('invalid_item', (string) $index);
            continue;
        }
        $item_errors = land76wp_service_hubs_validate_item($item, $seen_page_keys, $seen_canonicals);
        foreach ($item_errors as $item_error) {
            $errors[] = 'items[' . (string) $index . ']: ' . $item_error;
        }
    }

    return array_values(array_unique($errors));
}

/** Reject a complete-looking payload whose page keys differ from the frozen release. */
function land76wp_service_hubs_validate_expected_inventory(array $items, $source_label)
{
    $expected_page_keys = land76wp_service_hubs_expected_page_keys();
    if (count($expected_page_keys) !== 76) {
        return array(land76wp_service_hubs_error('expected_inventory_mismatch', 'frozen inventory'));
    }

    $actual_page_keys = array();
    $child_count = 0;
    $article_count = 0;
    foreach ($items as $item) {
        if (!is_array($item) || !isset($item['page_key']) || !is_string($item['page_key'])) {
            return array(land76wp_service_hubs_error('expected_inventory_mismatch', (string) $source_label));
        }
        $page_key = $item['page_key'];
        $actual_page_keys[] = $page_key;
        if (strpos($page_key, '-CHILD-') !== false) {
            $child_count++;
        } elseif (strpos($page_key, '-ARTICLE-') !== false) {
            $article_count++;
        }
    }
    sort($actual_page_keys, SORT_STRING);

    if (count($actual_page_keys) !== 76
        || $child_count !== 65
        || $article_count !== 11
        || $actual_page_keys !== $expected_page_keys) {
        return array(land76wp_service_hubs_error('expected_inventory_mismatch', (string) $source_label));
    }

    return array();
}

function land76wp_service_hubs_manifest_inventory(array $items)
{
    $inventory = array();
    foreach ($items as $item) {
        if (!is_array($item)
            || !isset($item['page_key'], $item['checksum'])
            || !is_string($item['page_key'])
            || !is_string($item['checksum'])) {
            return array();
        }
        $inventory[] = array(
            'page_key' => (string) $item['page_key'],
            'checksum' => (string) $item['checksum'],
        );
    }
    usort($inventory, function ($left, $right) {
        $page_key_order = strcmp($left['page_key'], $right['page_key']);
        return $page_key_order === 0 ? strcmp($left['checksum'], $right['checksum']) : $page_key_order;
    });

    return $inventory;
}

function land76wp_service_hubs_validate_manifest_binding(array $payload, array $release_manifest, $manifest_source_sha256)
{
    $errors = array();
    $source_manifest_sha256 = isset($release_manifest['source_manifest_sha256'])
        ? (string) $release_manifest['source_manifest_sha256']
        : '';
    if (!isset($payload['manifest_sha256'])
        || !is_string($payload['manifest_sha256'])
        || !hash_equals((string) $payload['manifest_sha256'], (string) $manifest_source_sha256)) {
        $errors[] = land76wp_service_hubs_error('manifest_hash_mismatch');
    }
    if (!isset($release_manifest['schema_version'], $release_manifest['release_id'], $release_manifest['release_status'])
        || !isset($payload['schema_version'], $payload['release_id'], $payload['release_status'])
        || (int) $release_manifest['schema_version'] !== (int) $payload['schema_version']
        || !hash_equals((string) $release_manifest['release_id'], (string) $payload['release_id'])
        || !hash_equals((string) $release_manifest['release_status'], (string) $payload['release_status'])) {
        $errors[] = land76wp_service_hubs_error('manifest_release_mismatch');
    }
    if (!preg_match('/^[a-f0-9]{64}$/', $source_manifest_sha256)
        || hash_equals(str_repeat('0', 64), $source_manifest_sha256)) {
        $errors[] = land76wp_service_hubs_error('invalid_source_manifest_sha256');
    }
    if (!isset($release_manifest['items'])
        || !is_array($release_manifest['items'])
        || !land76wp_service_hubs_is_list($release_manifest['items'])
        || !isset($payload['items'])
        || !is_array($payload['items'])
        || !land76wp_service_hubs_is_list($payload['items'])) {
        $errors[] = land76wp_service_hubs_error('manifest_inventory_mismatch');
        return array_values(array_unique($errors));
    }

    $manifest_inventory = land76wp_service_hubs_manifest_inventory($release_manifest['items']);
    $payload_inventory = land76wp_service_hubs_manifest_inventory($payload['items']);
    $manifest_has_invalid_item = $release_manifest['items'] !== array() && $manifest_inventory === array();
    $payload_has_invalid_item = $payload['items'] !== array() && $payload_inventory === array();
    foreach ($release_manifest['items'] as $manifest_item) {
        if (!is_array($manifest_item)
            || array_keys(land76wp_service_hubs_sort_recursive($manifest_item)) !== array('checksum', 'page_key')) {
            $manifest_has_invalid_item = true;
            break;
        }
    }
    if ($manifest_has_invalid_item
        || $payload_has_invalid_item
        || wp_json_encode($manifest_inventory) !== wp_json_encode($payload_inventory)) {
        $errors[] = land76wp_service_hubs_error('manifest_inventory_mismatch');
    }
    if (isset($payload['release_status']) && $payload['release_status'] === 'ready') {
        $errors = array_merge(
            $errors,
            land76wp_service_hubs_validate_expected_inventory($payload['items'], 'payload')
        );
    }
    if (isset($release_manifest['release_status']) && $release_manifest['release_status'] === 'ready') {
        $errors = array_merge(
            $errors,
            land76wp_service_hubs_validate_expected_inventory($release_manifest['items'], 'release_manifest')
        );
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_required_acf_fields()
{
    return array(
        'field_land76_selected_works_posts' => array('name' => 'selected_works_posts', 'type' => 'relationship', 'post_type' => array('page'), 'post_status' => array('publish'), 'taxonomy' => array(), 'filters' => array('search'), 'return_format' => 'id'),
        'field_land76_selected_real_projects' => array('name' => 'selected_real_projects', 'type' => 'relationship', 'post_type' => array('page'), 'post_status' => array('publish'), 'taxonomy' => array(), 'filters' => array('search'), 'return_format' => 'id'),
        'field_blogseo_related_services' => array('name' => 'blogseo_related_services', 'type' => 'relationship', 'post_type' => array('post', 'page'), 'post_status' => array('publish'), 'taxonomy' => array(), 'filters' => array('search'), 'return_format' => 'id'),
    );
}

function land76wp_service_hubs_required_acf_groups()
{
    return array(
        'field_land76_selected_works_posts' => array(
            'key' => 'group_land76_service_hub_category_relations',
            'location' => array(array(array('param' => 'taxonomy', 'operator' => '==', 'value' => 'category'))),
        ),
        'field_land76_selected_real_projects' => array(
            'key' => 'group_land76_service_hub_post_relations',
            'location' => array(array(array('param' => 'post_taxonomy', 'operator' => '==', 'value' => 'category:74'))),
        ),
        'field_blogseo_related_services' => array(
            'key' => 'group_blogseo_post',
            'location' => array(array(array('param' => 'post_taxonomy', 'operator' => '==', 'value' => 'category:72'))),
        ),
    );
}

function land76wp_service_hubs_acf_group_matches(array $field, array $group, array $expected_group)
{
    return land76wp_service_hubs_acf_group_definition_matches($group, $expected_group)
        && land76wp_service_hubs_acf_field_parent_matches($field, $group, $expected_group);
}

function land76wp_service_hubs_acf_group_definition_matches(array $group, array $expected_group)
{
    $actual_location = isset($group['location']) ? $group['location'] : null;

    return !empty($group['active'])
        && isset($group['key'])
        && hash_equals((string) $expected_group['key'], (string) $group['key'])
        && wp_json_encode(land76wp_service_hubs_sort_recursive($actual_location))
            === wp_json_encode(land76wp_service_hubs_sort_recursive($expected_group['location']));
}

function land76wp_service_hubs_acf_field_parent_matches(array $field, array $group, array $expected_group)
{
    $group_parent = !empty($group['ID']) ? (string) $group['ID'] : '';
    $field_parent = isset($field['parent']) ? (string) $field['parent'] : '';

    return $field_parent !== ''
        && (hash_equals((string) $expected_group['key'], $field_parent)
            || ($group_parent !== '' && hash_equals($group_parent, $field_parent)));
}

function land76wp_service_hubs_acf_schema_matches(array $field, array $expected)
{
    foreach ($expected as $key => $expected_value) {
        $actual_value = isset($field[$key]) ? $field[$key] : null;
        if (is_array($expected_value)) {
            $actual_value = is_array($actual_value) ? array_values($actual_value) : array();
            $sorted_expected = array_values($expected_value);
            sort($actual_value);
            sort($sorted_expected);
            if ($actual_value !== $sorted_expected) {
                return false;
            }
        } elseif ($actual_value !== $expected_value) {
            return false;
        }
    }

    return true;
}

function land76wp_service_hubs_blog_relation_desired_schema()
{
    return array(
        'key' => 'field_blogseo_related_services',
        'name' => 'blogseo_related_services',
        'type' => 'relationship',
        'required' => 0,
        'conditional_logic' => 0,
        'post_type' => array('post', 'page'),
        'post_status' => array('publish'),
        'taxonomy' => array(),
        'filters' => array('search'),
        'return_format' => 'id',
        'min' => 0,
        'max' => 0,
        'elements' => array('featured_image'),
    );
}

function land76wp_service_hubs_is_exact_legacy_blog_relation(array $field, array $group)
{
    $group_key = 'group_blogseo_post';
    if (!isset($group['key']) || !hash_equals($group_key, (string) $group['key'])) {
        return false;
    }
    $expected = array(
        'key' => 'field_blogseo_related_services',
        'name' => 'blogseo_related_services',
        'type' => 'relationship',
        'required' => 0,
        'conditional_logic' => 0,
        'post_type' => array('post'),
        'post_status' => array('publish'),
        'taxonomy' => array('category:74'),
        'filters' => array('search', 'taxonomy'),
        'return_format' => 'id',
        'min' => 0,
        'max' => 0,
        'elements' => array('featured_image'),
    );
    if (!land76wp_service_hubs_acf_schema_matches($field, $expected)) {
        return false;
    }

    $expected_groups = land76wp_service_hubs_required_acf_groups();
    return isset($expected_groups['field_blogseo_related_services'])
        && land76wp_service_hubs_acf_group_definition_matches(
            $group,
            $expected_groups['field_blogseo_related_services']
        );
}

/** Load every published duplicate by numeric ID, bypassing ACF's ambiguous key alias cache. */
function land76wp_service_hubs_blog_relation_candidate_fields($for_update = false)
{
    global $wpdb;

    $field_key = 'field_blogseo_related_services';
    $query = $wpdb->prepare(
        "SELECT ID FROM {$wpdb->posts} WHERE post_type = %s AND post_status = %s AND post_name = %s ORDER BY ID ASC",
        'acf-field',
        'publish',
        $field_key
    );
    if (!is_string($query) || $query === '') {
        return array(
            'errors' => array(land76wp_service_hubs_error('acf_schema_query_failed', $field_key)),
            'fields' => array(),
        );
    }
    if ($for_update) {
        $query .= ' FOR UPDATE';
    }
    $ids = $wpdb->get_col($query);
    if (!is_array($ids) || (isset($wpdb->last_error) && (string) $wpdb->last_error !== '')) {
        return array(
            'errors' => array(land76wp_service_hubs_error('acf_schema_query_failed', $field_key)),
            'fields' => array(),
        );
    }

    $fields = array();
    $seen = array();
    foreach ($ids as $candidate_id) {
        $candidate_id = (int) $candidate_id;
        if ($candidate_id <= 0 || isset($seen[$candidate_id])) {
            return array(
                'errors' => array(land76wp_service_hubs_error('acf_schema_inventory_invalid', $field_key)),
                'fields' => array(),
            );
        }
        $seen[$candidate_id] = true;
        $field = acf_get_raw_field($candidate_id);
        if (!is_array($field)
            || (int) (isset($field['ID']) ? $field['ID'] : 0) !== $candidate_id
            || !isset($field['key'])
            || !hash_equals($field_key, (string) $field['key'])) {
            return array(
                'errors' => array(land76wp_service_hubs_error('acf_schema_inventory_invalid', (string) $candidate_id)),
                'fields' => array(),
            );
        }
        $fields[] = $field;
    }

    return array('errors' => array(), 'fields' => $fields);
}

/** Inspect the full duplicate set so ACF's nondeterministic single-key lookup cannot hide stale rows. */
function land76wp_service_hubs_inspect_blog_relation(array $group, $for_update = false)
{
    $result = array(
        'errors' => array(),
        'fields' => array(),
        'missing' => false,
        'migration' => false,
    );
    $expected_group = land76wp_service_hubs_required_acf_groups()['field_blogseo_related_services'];
    if (!land76wp_service_hubs_acf_group_definition_matches($group, $expected_group)) {
        $result['errors'][] = land76wp_service_hubs_error('acf_group_incompatible', 'blogseo_related_services');
        return $result;
    }
    $group_id = isset($group['ID']) ? (int) $group['ID'] : 0;
    if ($group_id <= 0) {
        $result['errors'][] = land76wp_service_hubs_error('acf_group_incompatible', 'blogseo_related_services.ID');
        return $result;
    }

    $candidates = land76wp_service_hubs_blog_relation_candidate_fields($for_update);
    if ($candidates['errors'] !== array()) {
        $result['errors'] = $candidates['errors'];
        return $result;
    }
    $result['fields'] = $candidates['fields'];
    if ($result['fields'] === array()) {
        $result['missing'] = true;
        return $result;
    }

    $desired = land76wp_service_hubs_blog_relation_desired_schema();
    $canonical_parent_count = 0;
    foreach ($result['fields'] as $field) {
        $field_parent = isset($field['parent']) ? (string) $field['parent'] : '';
        if (!in_array($field_parent, array('', '0', (string) $group_id), true)) {
            $result['errors'][] = land76wp_service_hubs_error(
                'acf_group_incompatible',
                'blogseo_related_services.' . (string) $field['ID'] . '.parent'
            );
            continue;
        }
        $is_desired = land76wp_service_hubs_acf_schema_matches($field, $desired);
        $is_legacy = land76wp_service_hubs_is_exact_legacy_blog_relation($field, $group);
        if (!$is_desired && !$is_legacy) {
            $result['errors'][] = land76wp_service_hubs_error(
                'acf_schema_incompatible',
                'blogseo_related_services.' . (string) $field['ID']
            );
            continue;
        }
        if ($is_legacy) {
            $result['migration'] = true;
        }
        if (land76wp_service_hubs_acf_field_parent_matches($field, $group, $expected_group)) {
            $canonical_parent_count++;
        }
    }
    if ($canonical_parent_count === 0) {
        $result['errors'][] = land76wp_service_hubs_error('acf_group_incompatible', 'blogseo_related_services.parent');
    }

    $result['errors'] = array_values(array_unique($result['errors']));
    return $result;
}

function land76wp_service_hubs_verify_acf_schema($allow_missing = true)
{
    $result = array('errors' => array(), 'missing' => array(), 'migrations' => array());
    $required_functions = array('get_field', 'update_field', 'acf_get_field', 'acf_get_raw_field', 'acf_get_field_group');
    foreach ($required_functions as $function_name) {
        if (!function_exists($function_name)) {
            $result['errors'][] = land76wp_service_hubs_error('acf_unavailable', $function_name);
        }
    }
    if ($result['errors'] !== array()) {
        return $result;
    }

    $required_groups = land76wp_service_hubs_required_acf_groups();
    foreach (land76wp_service_hubs_required_acf_fields() as $field_key => $expected) {
        $field_name = $expected['name'];
        $expected_group = $required_groups[$field_key];
        $group = acf_get_field_group($expected_group['key']);
        if ($field_key === 'field_blogseo_related_services' && is_array($group)) {
            $inspection = land76wp_service_hubs_inspect_blog_relation($group, false);
            if ($inspection['missing']) {
                $result['missing'][] = $field_key;
            }
            $result['errors'] = array_merge($result['errors'], $inspection['errors']);
            if ($inspection['migration'] && $inspection['errors'] === array()) {
                $result['migrations'][] = $field_key;
            }
            continue;
        }
        $field = acf_get_field($field_key);
        if (!$field || !is_array($field)) {
            $result['missing'][] = $field_key;
            continue;
        }
        foreach ($expected as $key => $expected_value) {
            $actual_value = isset($field[$key]) ? $field[$key] : null;
            if (is_array($expected_value)) {
                $actual_value = is_array($actual_value) ? array_values($actual_value) : array();
                sort($actual_value);
                $sorted_expected = array_values($expected_value);
                sort($sorted_expected);
                if ($actual_value !== $sorted_expected) {
                    $result['errors'][] = land76wp_service_hubs_error('acf_schema_incompatible', $field_name . '.' . $key);
                }
            } elseif ($actual_value !== $expected_value) {
                $result['errors'][] = land76wp_service_hubs_error('acf_schema_incompatible', $field_name . '.' . $key);
            }
        }
        if ($field_name === 'blogseo_related_services' && !empty($field['taxonomy'])) {
            $result['errors'][] = land76wp_service_hubs_error('acf_schema_incompatible', $field_name . '.taxonomy');
        }
        if (!is_array($group)
            || !land76wp_service_hubs_acf_group_matches($field, $group, $expected_group)) {
            $result['errors'][] = land76wp_service_hubs_error('acf_group_incompatible', $field_name);
        }
    }
    if (!$allow_missing && $result['missing'] !== array()) {
        foreach ($result['missing'] as $field_key) {
            $result['errors'][] = land76wp_service_hubs_error('acf_schema_missing', $field_key);
        }
    }

    return $result;
}

function land76wp_service_hubs_collect_acf_field_names(array $fields, array &$names)
{
    foreach ($fields as $field) {
        if (!is_array($field)) {
            continue;
        }
        if (isset($field['name']) && is_string($field['name']) && $field['name'] !== '') {
            $names[$field['name']] = true;
        }
        if (isset($field['sub_fields']) && is_array($field['sub_fields'])) {
            land76wp_service_hubs_collect_acf_field_names($field['sub_fields'], $names);
        }
    }
}

function land76wp_service_hubs_bundled_acf_field_names()
{
    $names = array();
    foreach (land76wp_service_hubs_default_acf_json_paths() as $json_path) {
        if (!is_readable($json_path)) {
            continue;
        }
        $raw = file_get_contents($json_path);
        if (!is_string($raw)) {
            continue;
        }
        $groups = json_decode($raw, true);
        if (!is_array($groups)) {
            continue;
        }
        foreach ($groups as $group) {
            if (is_array($group) && isset($group['fields']) && is_array($group['fields'])) {
                land76wp_service_hubs_collect_acf_field_names($group['fields'], $names);
            }
        }
    }

    return $names;
}

function land76wp_service_hubs_preflight_item_acf(array $items)
{
    $result = array('errors' => array(), 'missing' => array());
    $bundled_names = land76wp_service_hubs_bundled_acf_field_names();
    foreach ($items as $item) {
        if (!isset($item['acf']) || !is_array($item['acf'])) {
            continue;
        }
        foreach ($item['acf'] as $field_name => $field_value) {
            $field = acf_get_field($field_name);
            if (is_array($field) && isset($field['name']) && hash_equals((string) $field_name, (string) $field['name'])) {
                continue;
            }
            if (isset($bundled_names[$field_name])) {
                $result['missing'][] = $field_name;
            } else {
                $result['errors'][] = land76wp_service_hubs_error('unknown_acf_field', $item['page_key'] . '.' . $field_name);
            }
        }
    }
    $result['errors'] = array_values(array_unique($result['errors']));
    $result['missing'] = array_values(array_unique($result['missing']));

    return $result;
}

function land76wp_service_hubs_find_owned_posts($page_key, $post_type)
{
    return get_posts(array(
        'post_type' => $post_type,
        'post_status' => array('draft', 'pending', 'private', 'publish', 'future'),
        'posts_per_page' => -1,
        'orderby' => 'ID',
        'order' => 'ASC',
        'meta_query' => array(
            'relation' => 'AND',
            array('key' => '_land76_import_owner', 'value' => land76wp_service_hubs_import_owner(), 'compare' => '='),
            array('key' => '_land76_page_key', 'value' => (string) $page_key, 'compare' => '='),
        ),
        'suppress_filters' => true,
    ));
}

function land76wp_service_hubs_find_page_key_posts($page_key)
{
    return get_posts(array(
        'post_type' => array('post', 'page'),
        'post_status' => array('draft', 'pending', 'private', 'publish', 'future'),
        'posts_per_page' => -1,
        'orderby' => 'ID',
        'order' => 'ASC',
        'meta_query' => array(
            array('key' => '_land76_page_key', 'value' => (string) $page_key, 'compare' => '='),
        ),
        'suppress_filters' => true,
    ));
}

function land76wp_service_hubs_find_global_slug_posts($slug)
{
    return get_posts(array(
        'name' => (string) $slug,
        'post_type' => array('post', 'page'),
        'post_status' => array('draft', 'pending', 'private', 'publish', 'future'),
        'posts_per_page' => -1,
        'orderby' => 'ID',
        'order' => 'ASC',
        'suppress_filters' => true,
    ));
}

function land76wp_service_hubs_validate_case_ids(array $case_ids, $page_key)
{
    $errors = array();
    $seen = array();
    foreach ($case_ids as $case_id) {
        if (!is_int($case_id) && !(is_string($case_id) && ctype_digit($case_id))) {
            $errors[] = land76wp_service_hubs_error('invalid_case_id', $page_key);
            continue;
        }
        $case_id = (int) $case_id;
        if ($case_id <= 0) {
            $errors[] = land76wp_service_hubs_error('invalid_case_id', $page_key);
            continue;
        }
        if (isset($seen[$case_id])) {
            $errors[] = land76wp_service_hubs_error('duplicate_case_id', (string) $case_id);
            continue;
        }
        $seen[$case_id] = true;
        $case_post = get_post($case_id);
        if (!$case_post instanceof WP_Post
            || $case_post->post_type !== 'page'
            || $case_post->post_status !== 'publish'
            || get_page_template_slug($case_id) !== 'casenew.php') {
            $errors[] = land76wp_service_hubs_error('unresolved_case', (string) $case_id);
        }
    }

    return $errors;
}

function land76wp_service_hubs_term_checksum(array $hub, $release_id, $manifest_sha256)
{
    $data = array(
        'release_id' => (string) $release_id,
        'manifest_sha256' => (string) $manifest_sha256,
        'service_id' => (string) $hub['service_id'],
        'grouping_slug' => (string) $hub['grouping_slug'],
        'canonical' => (string) $hub['canonical'],
        'archive_policy' => (string) $hub['archive_policy'],
    );
    return hash('sha256', wp_json_encode(land76wp_service_hubs_sort_recursive($data), JSON_UNESCAPED_SLASHES));
}

function land76wp_service_hubs_plan_grouping_terms($release_id, $manifest_sha256)
{
    $operations = array();
    $errors = array();
    foreach (land76wp_service_hub_registry() as $service_id => $hub) {
        $term = get_term_by('slug', $hub['grouping_slug'], 'category');
        $checksum = land76wp_service_hubs_term_checksum($hub, $release_id, $manifest_sha256);
        $operation = array(
            'kind' => 'grouping_term',
            'service_id' => $service_id,
            'page_key' => $service_id . '-GROUPING',
            'slug' => $hub['grouping_slug'],
            'canonical' => $hub['canonical'],
            'checksum' => $checksum,
            'term_id' => 0,
            'action' => 'create',
        );
        if ($term instanceof WP_Term) {
            $operation['term_id'] = (int) $term->term_id;
            $owner = (string) get_term_meta($term->term_id, '_land76_import_owner', true);
            $stored_service_id = (string) get_term_meta($term->term_id, '_land76_service_id', true);
            if (!hash_equals(land76wp_service_hubs_import_owner(), $owner) || !hash_equals($service_id, $stored_service_id)) {
                $errors[] = land76wp_service_hubs_error('grouping_slug_conflict', $hub['grouping_slug']);
            } else {
                $stored_checksum = (string) get_term_meta($term->term_id, '_land76_import_checksum', true);
                $stored_release = (string) get_term_meta($term->term_id, '_land76_release_id', true);
                $stored_manifest = (string) get_term_meta($term->term_id, '_land76_manifest_sha256', true);
                $operation['action'] = hash_equals($checksum, $stored_checksum)
                    && hash_equals((string) $release_id, $stored_release)
                    && hash_equals((string) $manifest_sha256, $stored_manifest)
                    && hash_equals($service_id . '-GROUPING', (string) get_term_meta($term->term_id, '_land76_page_key', true))
                    && hash_equals($service_id, (string) get_term_meta($term->term_id, '_land76_topic_key', true))
                    && hash_equals((string) $hub['canonical'], (string) get_term_meta($term->term_id, '_land76_canonical', true))
                    && hash_equals((string) $hub['canonical'], (string) get_term_meta($term->term_id, '_land76_hub_url', true))
                    && hash_equals('redirect_to_hub', (string) get_term_meta($term->term_id, '_land76_archive_policy', true))
                    ? 'unchanged'
                    : 'update';
            }
        }
        $operations[] = $operation;
    }

    return array('operations' => $operations, 'errors' => $errors);
}

function land76wp_service_hubs_post_type_for_role($role)
{
    return $role === 'geo' ? 'page' : 'post';
}

function land76wp_service_hubs_plan_geo_item(array $item)
{
    $errors = array();
    $city_slug = isset($item['city_parent_slug']) ? (string) $item['city_parent_slug'] : '';
    $slug = isset($item['slug']) ? (string) $item['slug'] : '';
    $local_evidence = isset($item['local_evidence']) ? $item['local_evidence'] : array();
    $case_ids = isset($item['case_ids']) && is_array($item['case_ids']) ? $item['case_ids'] : array();

    if ($local_evidence === array()) {
        $errors[] = land76wp_service_hubs_error('missing_local_evidence', $item['page_key']);
    }
    $city_parent = get_page_by_path($city_slug, 'OBJECT', 'page');
    if (!$city_parent instanceof WP_Post
        || $city_parent->post_status !== 'publish'
        || $city_parent->post_name !== $city_slug
        || (int) $city_parent->post_parent !== 0) {
        $errors[] = land76wp_service_hubs_error('invalid_city_parent', $city_slug);
        $parent_id = 0;
    } else {
        $parent_id = (int) $city_parent->ID;
    }

    $global_matches = land76wp_service_hubs_find_global_slug_posts($slug);
    $children = get_posts(array(
        'post_type' => 'page',
        'post_status' => array('draft', 'pending', 'private', 'publish', 'future'),
        'post_parent' => $parent_id,
        'name' => $slug,
        'posts_per_page' => -1,
        'suppress_filters' => true,
    ));
    if (count($children) > 1) {
        $errors[] = land76wp_service_hubs_error('duplicate_geo_child', $item['page_key']);
    }
    foreach ($global_matches as $global_match) {
        if ((int) $global_match->post_parent !== $parent_id) {
            $errors[] = land76wp_service_hubs_error('global_slug_collision', $slug);
        }
    }

    return array(
        'errors' => array_values(array_unique($errors)),
        'parent_id' => $parent_id,
        'template' => 'page-service-hub-region.php',
        'local_evidence' => $local_evidence,
        'case_ids' => $case_ids,
    );
}

function land76wp_service_hubs_plan_reuse_item(array $item, array $contract)
{
    $errors = array();
    $operation = array(
        'kind' => 'post',
        'action' => 'reuse_update',
        'post_id' => (int) $contract['post_id'],
        'post_type' => (string) $contract['post_type'],
        'parent_id' => (int) $contract['parent_id'],
        'template' => (string) $contract['target_template'],
        'reuse_claim_state' => '',
        'reuse_contract' => $contract,
        'item' => $item,
    );

    if (!isset($item['page_key'], $item['service_id'], $item['topic_key'], $item['role'], $item['slug'], $item['canonical'])
        || !hash_equals((string) $contract['page_key'], (string) $item['page_key'])
        || !hash_equals((string) $contract['service_id'], (string) $item['service_id'])
        || !hash_equals((string) $contract['service_id'], (string) $item['topic_key'])
        || !hash_equals('child_service', (string) $item['role'])
        || !hash_equals((string) $contract['slug'], (string) $item['slug'])
        || !hash_equals((string) $contract['current_url'], (string) $item['canonical'])
        || !hash_equals((string) $contract['current_url'], (string) $contract['target_url'])) {
        $errors[] = land76wp_service_hubs_error('reuse_contract_mismatch', (string) $contract['page_key']);
    }

    $post = get_post((int) $contract['post_id']);
    if (!$post instanceof WP_Post) {
        $errors[] = land76wp_service_hubs_error('reuse_missing_post', (string) $contract['page_key']);
        return array('operation' => $operation, 'errors' => array_values(array_unique($errors)));
    }
    if ((int) $post->ID !== (int) $contract['post_id']) {
        $errors[] = land76wp_service_hubs_error('reuse_id_mismatch', (string) $contract['page_key']);
    }
    if (!hash_equals((string) $contract['post_type'], (string) $post->post_type)) {
        $errors[] = land76wp_service_hubs_error('reuse_type_mismatch', (string) $contract['page_key']);
    }
    if (!hash_equals((string) $contract['post_status'], (string) $post->post_status)) {
        $errors[] = land76wp_service_hubs_error('reuse_status_mismatch', (string) $contract['page_key']);
    }
    if (!hash_equals((string) $contract['slug'], (string) $post->post_name)) {
        $errors[] = land76wp_service_hubs_error('reuse_slug_mismatch', (string) $contract['page_key']);
    }
    if ((int) $post->post_parent !== (int) $contract['parent_id']) {
        $errors[] = land76wp_service_hubs_error('reuse_parent_mismatch', (string) $contract['page_key']);
    }
    $permalink = land76wp_service_hubs_normalize_url(get_permalink($post));
    if (!hash_equals((string) $contract['current_url'], $permalink)
        || !hash_equals((string) $contract['target_url'], $permalink)) {
        $errors[] = land76wp_service_hubs_error('reuse_url_mismatch', (string) $contract['page_key']);
    }

    $page_key_posts = land76wp_service_hubs_find_page_key_posts($item['page_key']);
    foreach ($page_key_posts as $page_key_post) {
        if ((int) $page_key_post->ID !== (int) $contract['post_id']) {
            $errors[] = land76wp_service_hubs_error('reuse_owner_mismatch', (string) $contract['page_key']);
        }
    }
    $slug_posts = land76wp_service_hubs_find_global_slug_posts($item['slug']);
    if (count($slug_posts) !== 1 || (int) $slug_posts[0]->ID !== (int) $contract['post_id']) {
        $errors[] = land76wp_service_hubs_error('reuse_owner_mismatch', (string) $contract['page_key']);
    }

    $owner = (string) get_post_meta($post->ID, '_land76_import_owner', true);
    $stored_page_key = (string) get_post_meta($post->ID, '_land76_page_key', true);
    $stored_service_id = (string) get_post_meta($post->ID, '_land76_service_id', true);
    $stored_topic_key = (string) get_post_meta($post->ID, '_land76_topic_key', true);
    $stored_canonical = (string) get_post_meta($post->ID, '_land76_canonical', true);
    $expected_template = (string) $contract['legacy_template'];
    if ($owner === '') {
        $operation['reuse_claim_state'] = 'legacy_exact_match';
        $management_meta_keys = array(
            '_land76_release_id',
            '_land76_manifest_sha256',
            '_land76_page_key',
            '_land76_service_id',
            '_land76_topic_key',
            '_land76_canonical',
            '_land76_import_checksum',
            '_land76_main_image_url',
            '_land76_main_image_alt',
            '_land76_hero_image_url',
            '_land76_hero_image_alt',
            '_land76_context_image_url',
            '_land76_context_image_alt',
            '_land76_card_image_url',
            '_land76_card_image_alt',
            '_land76_related_article_ids',
            '_land76_region',
            '_land76_local_evidence',
        );
        foreach ($management_meta_keys as $management_meta_key) {
            if ((string) get_post_meta($post->ID, $management_meta_key, true) !== '') {
                $errors[] = land76wp_service_hubs_error('reuse_partial_owner', (string) $contract['page_key']);
                break;
            }
        }
    } elseif (hash_equals(land76wp_service_hubs_import_owner(), $owner)) {
        $operation['reuse_claim_state'] = 'managed_exact_match';
        $expected_template = (string) $contract['target_template'];
        if (!hash_equals((string) $contract['page_key'], $stored_page_key)
            || !hash_equals((string) $contract['service_id'], $stored_service_id)
            || !hash_equals((string) $contract['service_id'], $stored_topic_key)
            || !hash_equals((string) $contract['target_url'], $stored_canonical)) {
            $errors[] = land76wp_service_hubs_error('reuse_owner_mismatch', (string) $contract['page_key']);
        }
    } else {
        $errors[] = land76wp_service_hubs_error('reuse_owner_mismatch', (string) $contract['page_key']);
    }
    $current_template = (string) get_page_template_slug($post->ID);
    if (!hash_equals($expected_template, $current_template)) {
        $errors[] = land76wp_service_hubs_error('reuse_template_mismatch', (string) $contract['page_key']);
    }

    return array('operation' => $operation, 'errors' => array_values(array_unique($errors)));
}

function land76wp_service_hubs_verify_reuse_target(array $operation, $required_claim_state = '')
{
    if (!isset($operation['item']) || !is_array($operation['item'])) {
        return array(land76wp_service_hubs_error('reuse_contract_mismatch', 'missing item'));
    }
    $contract = land76wp_service_hubs_reuse_contract_for_item($operation['item']);
    if (!is_array($contract)
        || !isset($operation['reuse_contract'])
        || !is_array($operation['reuse_contract'])
        || $operation['reuse_contract'] !== $contract
        || !isset($operation['action'], $operation['post_id'], $operation['post_type'], $operation['parent_id'], $operation['template'])
        || $operation['action'] !== 'reuse_update'
        || (int) $operation['post_id'] !== (int) $contract['post_id']
        || !hash_equals((string) $operation['post_type'], (string) $contract['post_type'])
        || (int) $operation['parent_id'] !== (int) $contract['parent_id']
        || !hash_equals((string) $operation['template'], (string) $contract['target_template'])) {
        return array(land76wp_service_hubs_error('reuse_contract_mismatch', (string) $operation['item']['page_key']));
    }

    $planned = land76wp_service_hubs_plan_reuse_item($operation['item'], $contract);
    $errors = $planned['errors'];
    $claim_state = isset($planned['operation']['reuse_claim_state'])
        ? (string) $planned['operation']['reuse_claim_state']
        : '';
    if ($required_claim_state !== '' && !hash_equals((string) $required_claim_state, $claim_state)) {
        $errors[] = land76wp_service_hubs_error('reuse_owner_mismatch', (string) $contract['page_key']);
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_plan_item(array $item, $release_id, $manifest_sha256)
{
    $reuse_contract = land76wp_service_hubs_reuse_contract_for_item($item);
    if (is_array($reuse_contract)) {
        return land76wp_service_hubs_plan_reuse_item($item, $reuse_contract);
    }
    $errors = array();
    $post_type = land76wp_service_hubs_post_type_for_role($item['role']);
    $owned_posts = land76wp_service_hubs_find_owned_posts($item['page_key'], $post_type);
    if (count($owned_posts) > 1) {
        $errors[] = land76wp_service_hubs_error('duplicate_owned_record', $item['page_key']);
    }
    $existing = count($owned_posts) === 1 ? $owned_posts[0] : null;
    $page_key_posts = land76wp_service_hubs_find_page_key_posts($item['page_key']);
    foreach ($page_key_posts as $page_key_post) {
        if (!$existing instanceof WP_Post || (int) $page_key_post->ID !== (int) $existing->ID) {
            $errors[] = land76wp_service_hubs_error('page_key_conflict', $item['page_key']);
        }
    }

    $global_matches = land76wp_service_hubs_find_global_slug_posts($item['slug']);
    foreach ($global_matches as $global_match) {
        if (!$existing instanceof WP_Post || (int) $global_match->ID !== (int) $existing->ID) {
            $errors[] = land76wp_service_hubs_error('slug_conflict', $item['slug']);
        }
    }

    $geo = null;
    if ($item['role'] === 'geo') {
        $geo = land76wp_service_hubs_plan_geo_item($item);
        $errors = array_merge($errors, $geo['errors']);
    }
    if (isset($item['case_ids']) && is_array($item['case_ids'])) {
        $errors = array_merge($errors, land76wp_service_hubs_validate_case_ids($item['case_ids'], $item['page_key']));
    }

    $operation = array(
        'kind' => 'post',
        'action' => 'create',
        'post_id' => 0,
        'post_type' => $post_type,
        'parent_id' => $geo === null ? 0 : (int) $geo['parent_id'],
        'template' => $geo === null ? '' : $geo['template'],
        'item' => $item,
    );
    if ($existing instanceof WP_Post) {
        $operation['post_id'] = (int) $existing->ID;
        if ($existing->post_name !== $item['slug'] || $existing->post_type !== $post_type) {
            $errors[] = land76wp_service_hubs_error('owned_record_shape_mismatch', $item['page_key']);
        }
        $stored_owner = (string) get_post_meta($existing->ID, '_land76_import_owner', true);
        $stored_page_key = (string) get_post_meta($existing->ID, '_land76_page_key', true);
        $stored_service = (string) get_post_meta($existing->ID, '_land76_service_id', true);
        $stored_topic = (string) get_post_meta($existing->ID, '_land76_topic_key', true);
        if (!hash_equals(land76wp_service_hubs_import_owner(), $stored_owner)
            || !hash_equals($item['page_key'], $stored_page_key)
            || !hash_equals($item['service_id'], $stored_service)
            || !hash_equals($item['topic_key'], $stored_topic)) {
            $errors[] = land76wp_service_hubs_error('ownership_drift', $item['page_key']);
        }
        if ($existing->post_status === 'publish') {
            $operation['action'] = 'published';
        } elseif ($existing->post_status !== 'draft') {
            $errors[] = land76wp_service_hubs_error('invalid_staged_status', $item['page_key']);
        } else {
            $stored_release = (string) get_post_meta($existing->ID, '_land76_release_id', true);
            $stored_manifest = (string) get_post_meta($existing->ID, '_land76_manifest_sha256', true);
            $stored_checksum = (string) get_post_meta($existing->ID, '_land76_import_checksum', true);
            if (!hash_equals((string) $release_id, $stored_release)) {
                $errors[] = land76wp_service_hubs_error('staged_release_mismatch', $item['page_key']);
            }
            $operation['action'] = hash_equals($item['checksum'], $stored_checksum)
                && hash_equals((string) $manifest_sha256, $stored_manifest)
                ? 'unchanged'
                : 'update';
        }
    }

    return array('operation' => $operation, 'errors' => array_values(array_unique($errors)));
}

function land76wp_service_hubs_validate_related_page_keys(array $items)
{
    $errors = array();
    $available = array();
    foreach ($items as $item) {
        $available[$item['page_key']] = $item;
    }
    foreach (land76wp_service_hub_registry() as $service_id => $hub) {
        $available[$service_id . '-HUB'] = array('service_id' => $service_id, 'role' => 'hub');
    }
    foreach ($items as $item) {
        foreach (array('related_service_page_keys', 'related_article_page_keys') as $field) {
            if (!isset($item[$field]) || !is_array($item[$field])) {
                continue;
            }
            foreach ($item[$field] as $related_page_key) {
                if (!is_string($related_page_key) || !isset($available[$related_page_key])) {
                    $errors[] = land76wp_service_hubs_error('unresolved_relation', $item['page_key'] . ' -> ' . (string) $related_page_key);
                    continue;
                }
                $related_role = $available[$related_page_key]['role'];
                if ($field === 'related_service_page_keys' && !in_array($related_role, array('hub', 'child_service'), true)) {
                    $errors[] = land76wp_service_hubs_error('wrong_relation_role', (string) $related_page_key);
                }
                if ($field === 'related_article_page_keys' && $related_role !== 'article') {
                    $errors[] = land76wp_service_hubs_error('wrong_relation_role', (string) $related_page_key);
                }
            }
        }
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_service_id_for_post($post_id)
{
    $post_id = (int) $post_id;
    foreach (land76wp_service_hub_registry() as $service_id => $hub) {
        if ((int) $hub['hub_post_id'] === $post_id) {
            return $service_id;
        }
    }
    if (!hash_equals(land76wp_service_hubs_import_owner(), (string) get_post_meta($post_id, '_land76_import_owner', true))) {
        return '';
    }
    $service_id = (string) get_post_meta($post_id, '_land76_service_id', true);
    $topic_key = (string) get_post_meta($post_id, '_land76_topic_key', true);
    if ($service_id === '' || !hash_equals($service_id, $topic_key) || land76wp_service_hub_by_service_id($service_id) === null) {
        return '';
    }

    return $service_id;
}

function land76wp_service_hubs_preflight_external_relations(array $items)
{
    $errors = array();
    $available = array();
    foreach ($items as $available_item) {
        $available[$available_item['page_key']] = $available_item;
    }
    foreach (land76wp_service_hub_registry() as $service_id => $hub) {
        $available[$service_id . '-HUB'] = array('service_id' => $service_id, 'role' => 'hub');
    }

    foreach ($items as $item) {
        $has_primary_commercial = $item['role'] !== 'article';
        if (isset($item['related_service_page_keys']) && is_array($item['related_service_page_keys'])) {
            foreach ($item['related_service_page_keys'] as $page_key) {
                if (isset($available[$page_key])
                    && hash_equals((string) $item['service_id'], (string) $available[$page_key]['service_id'])
                    && in_array($available[$page_key]['role'], array('hub', 'child_service'), true)) {
                    $has_primary_commercial = true;
                }
                if (is_string($page_key) && preg_match('/^S(?:[1-9]|1[0-5])-HUB$/', $page_key)) {
                    if (!land76wp_service_hubs_resolve_page_key($page_key, array())) {
                        $errors[] = land76wp_service_hubs_error('unresolved_relation', $item['page_key'] . ' -> ' . $page_key);
                    }
                }
            }
        }
        if (isset($item['related_service_slugs']) && is_array($item['related_service_slugs'])) {
            try {
                $related_ids = land76wp_service_hubs_resolve_related_slugs($item['related_service_slugs']);
                foreach ($related_ids as $related_id) {
                    if (hash_equals((string) $item['service_id'], land76wp_service_hubs_service_id_for_post($related_id))) {
                        $has_primary_commercial = true;
                    }
                }
            } catch (Throwable $error) {
                $errors[] = land76wp_service_hubs_error('unresolved_relation', $item['page_key'] . ' -> ' . $error->getMessage());
            }
        }
        if (!$has_primary_commercial) {
            $errors[] = land76wp_service_hubs_error('missing_primary_commercial_relation', $item['page_key']);
        }
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_build_plan(array $payload)
{
    $plan = land76wp_service_hubs_empty_result();
    $plan['release_id'] = isset($payload['release_id']) ? (string) $payload['release_id'] : '';
    $plan['release_status'] = isset($payload['release_status']) ? (string) $payload['release_status'] : '';
    $plan['manifest_sha256'] = isset($payload['manifest_sha256']) ? (string) $payload['manifest_sha256'] : '';
    $plan['payload_sha256'] = hash('sha256', wp_json_encode(land76wp_service_hubs_sort_recursive($payload), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    $plan['errors'] = land76wp_service_hubs_validate_payload($payload);

    if ($plan['errors'] !== array()) {
        return $plan;
    }
    if ($payload['release_status'] === 'draft' && $payload['items'] === array()) {
        $plan['reason'] = 'empty_payload';
        return $plan;
    }

    $acf = land76wp_service_hubs_verify_acf_schema(true);
    $plan['errors'] = array_merge($plan['errors'], $acf['errors']);
    if ($plan['errors'] !== array()) {
        $plan['errors'] = array_values(array_unique($plan['errors']));
        return $plan;
    }
    $item_acf = land76wp_service_hubs_preflight_item_acf($payload['items']);
    $plan['errors'] = array_merge($plan['errors'], $item_acf['errors']);
    $plan['acf_missing'] = array_values(array_unique(array_merge($acf['missing'], $item_acf['missing'])));
    $plan['acf_migrations'] = array_values(array_unique($acf['migrations']));
    $plan['errors'] = array_merge($plan['errors'], land76wp_service_hubs_validate_related_page_keys($payload['items']));
    $plan['errors'] = array_merge($plan['errors'], land76wp_service_hubs_preflight_external_relations($payload['items']));

    $grouping = land76wp_service_hubs_plan_grouping_terms($payload['release_id'], $payload['manifest_sha256']);
    $plan['errors'] = array_merge($plan['errors'], $grouping['errors']);
    foreach ($grouping['operations'] as $operation) {
        $plan['operations'][] = $operation;
    }

    foreach ($payload['items'] as $item) {
        $item_plan = land76wp_service_hubs_plan_item($item, $payload['release_id'], $payload['manifest_sha256']);
        $plan['errors'] = array_merge($plan['errors'], $item_plan['errors']);
        $plan['operations'][] = $item_plan['operation'];
        foreach ($item_plan['errors'] as $error) {
            if (strpos($error, 'unresolved_case') !== false) {
                $plan['unresolved_cases'][] = $error;
            }
        }
    }

    if ($plan['errors'] === array()) {
        foreach ($plan['operations'] as &$operation) {
            if ($operation['kind'] !== 'post' || !in_array($operation['action'], array('unchanged', 'published'), true)) {
                continue;
            }
            $required_status = $operation['action'] === 'published' ? 'publish' : 'draft';
            $staged_errors = land76wp_service_hubs_verify_staged_item(
                $operation,
                $payload['release_id'],
                $payload['manifest_sha256'],
                $required_status
            );
            if ($staged_errors === array()) {
                continue;
            }
            if ($operation['action'] === 'unchanged') {
                $operation['action'] = 'update';
            } else {
                $plan['errors'] = array_merge($plan['errors'], $staged_errors);
            }
        }
        unset($operation);
    }

    $plan['errors'] = array_values(array_unique($plan['errors']));
    $plan['unresolved_cases'] = array_values(array_unique($plan['unresolved_cases']));
    $plan['planned'] = count($plan['operations']);
    $plan['applicable'] = $plan['errors'] === array();

    return $plan;
}

function land76wp_service_hubs_acf_update_field_recursive(array $field, $parent)
{
    $sub_fields = isset($field['sub_fields']) && is_array($field['sub_fields']) ? $field['sub_fields'] : array();
    unset($field['sub_fields']);
    $field['parent'] = $parent;
    $updated = acf_update_field($field);
    $next_parent = !empty($updated['ID']) ? (int) $updated['ID'] : $field['key'];
    foreach ($sub_fields as $sub_field) {
        if (is_array($sub_field)) {
            land76wp_service_hubs_acf_update_field_recursive($sub_field, $next_parent);
        }
    }
}

function land76wp_service_hubs_import_acf_file($json_path)
{
    if (!is_readable($json_path)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_json_unreadable', $json_path));
    }
    $raw = file_get_contents($json_path);
    if (!is_string($raw)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_json_unreadable', $json_path));
    }
    $groups = json_decode($raw, true);
    if (!is_array($groups)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_json_invalid', $json_path));
    }
    foreach ($groups as $group) {
        if (!is_array($group) || empty($group['key']) || empty($group['fields']) || !is_array($group['fields'])) {
            throw new RuntimeException(land76wp_service_hubs_error('acf_group_invalid', $json_path));
        }
        $fields = $group['fields'];
        unset($group['fields']);
        $existing = acf_get_field_group($group['key']);
        if (!empty($existing['ID'])) {
            $group['ID'] = $existing['ID'];
        }
        $updated = acf_update_field_group($group);
        $parent = !empty($updated['ID']) ? (int) $updated['ID'] : $group['key'];
        foreach ($fields as $field) {
            land76wp_service_hubs_acf_update_field_recursive($field, $parent);
        }
    }
}

function land76wp_service_hubs_bundled_acf_group_field($json_path, $group_key, $field_key)
{
    if (!is_readable($json_path)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_json_unreadable', $json_path));
    }
    $raw = file_get_contents($json_path);
    $groups = is_string($raw) ? json_decode($raw, true) : null;
    if (!is_array($groups)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_json_invalid', $json_path));
    }
    foreach ($groups as $group) {
        if (!is_array($group) || !isset($group['key']) || !hash_equals((string) $group_key, (string) $group['key'])) {
            continue;
        }
        $fields = isset($group['fields']) && is_array($group['fields']) ? $group['fields'] : array();
        foreach ($fields as $field) {
            if (is_array($field) && isset($field['key']) && hash_equals((string) $field_key, (string) $field['key'])) {
                return array('group' => $group, 'field' => $field);
            }
        }
    }

    throw new RuntimeException(land76wp_service_hubs_error('acf_schema_missing', $field_key));
}

function land76wp_service_hubs_migrate_legacy_blog_relation()
{
    $field_key = 'field_blogseo_related_services';
    $group_key = 'group_blogseo_post';
    $group = acf_get_field_group($group_key);
    if (!is_array($group)) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_schema_incompatible', $field_key));
    }
    $inspection = land76wp_service_hubs_inspect_blog_relation($group, true);
    if ($inspection['missing'] || $inspection['errors'] !== array() || !$inspection['migration']) {
        throw new RuntimeException(
            $inspection['errors'] !== array()
                ? implode('; ', $inspection['errors'])
                : land76wp_service_hubs_error('acf_schema_incompatible', $field_key)
        );
    }

    $paths = land76wp_service_hubs_default_acf_json_paths();
    $bundled = land76wp_service_hubs_bundled_acf_group_field($paths[1], $group_key, $field_key);
    $candidate_ids = array();
    foreach ($inspection['fields'] as $field) {
        $candidate_ids[] = (int) $field['ID'];
        if (land76wp_service_hubs_acf_schema_matches(
            $field,
            land76wp_service_hubs_blog_relation_desired_schema()
        )) {
            continue;
        }
        if (!land76wp_service_hubs_is_exact_legacy_blog_relation($field, $group)) {
            throw new RuntimeException(land76wp_service_hubs_error('acf_schema_incompatible', (string) $field['ID']));
        }
        $target_field = $bundled['field'];
        $target_field['ID'] = (int) $field['ID'];
        $target_field['parent'] = isset($field['parent']) ? $field['parent'] : 0;
        $updated = acf_update_field($target_field);
        if (!is_array($updated)
            || (int) (isset($updated['ID']) ? $updated['ID'] : 0) !== (int) $field['ID']
            || empty($updated['key'])
            || !hash_equals($field_key, (string) $updated['key'])) {
            throw new RuntimeException(land76wp_service_hubs_error('acf_schema_migration_failed', (string) $field['ID']));
        }
    }

    $verified = land76wp_service_hubs_inspect_blog_relation($group, true);
    $verified_ids = array();
    foreach ($verified['fields'] as $field) {
        $verified_ids[] = (int) $field['ID'];
    }
    if ($verified['missing']
        || $verified['errors'] !== array()
        || $verified['migration']
        || $verified_ids !== $candidate_ids) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_schema_migration_failed', $field_key));
    }
}

function land76wp_service_hubs_install_missing_blog_relation()
{
    $field_key = 'field_blogseo_related_services';
    $group_key = 'group_blogseo_post';
    if (acf_get_field($field_key)) {
        throw new RuntimeException(land76wp_service_hubs_error('stage_target_changed', $field_key));
    }
    $paths = land76wp_service_hubs_default_acf_json_paths();
    $bundled = land76wp_service_hubs_bundled_acf_group_field($paths[1], $group_key, $field_key);
    $group = acf_get_field_group($group_key);
    if (!is_array($group)) {
        $group_data = $bundled['group'];
        unset($group_data['fields']);
        $group = acf_update_field_group($group_data);
    }
    if (!is_array($group) || empty($group['key']) || !hash_equals($group_key, (string) $group['key'])) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_group_incompatible', $group_key));
    }
    $target_field = $bundled['field'];
    $target_field['parent'] = !empty($group['ID']) ? (int) $group['ID'] : $group_key;
    $expected_groups = land76wp_service_hubs_required_acf_groups();
    if (!land76wp_service_hubs_acf_group_matches(
        $target_field,
        $group,
        $expected_groups[$field_key]
    )) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_group_incompatible', $group_key));
    }
    $updated = acf_update_field($target_field);
    if (!is_array($updated) || empty($updated['key']) || !hash_equals($field_key, (string) $updated['key'])) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_schema_install_failed', $field_key));
    }
}

function land76wp_service_hubs_install_missing_acf_schema(array $missing, array $migrations)
{
    if ($missing === array() && $migrations === array()) {
        return;
    }
    foreach (array('acf_update_field_group', 'acf_update_field', 'acf_get_raw_field', 'acf_get_field_group') as $function_name) {
        if (!function_exists($function_name)) {
            throw new RuntimeException(land76wp_service_hubs_error('acf_unavailable', $function_name));
        }
    }
    $relation_field_keys = array(
        'field_land76_selected_works_posts',
        'field_land76_selected_real_projects',
    );
    $unknown_missing = array_diff($missing, array_merge($relation_field_keys, array('field_blogseo_related_services')));
    if ($unknown_missing !== array()) {
        throw new RuntimeException(land76wp_service_hubs_error('acf_schema_missing', implode(',', $unknown_missing)));
    }
    if (array_intersect($missing, $relation_field_keys) !== array()) {
        $paths = land76wp_service_hubs_default_acf_json_paths();
        land76wp_service_hubs_import_acf_file($paths[0]);
    }
    if (in_array('field_blogseo_related_services', $missing, true)) {
        land76wp_service_hubs_install_missing_blog_relation();
    }
    foreach ($migrations as $migration) {
        if (!hash_equals('field_blogseo_related_services', (string) $migration)) {
            throw new RuntimeException(land76wp_service_hubs_error('acf_schema_incompatible', (string) $migration));
        }
        land76wp_service_hubs_migrate_legacy_blog_relation();
    }
    $verified = land76wp_service_hubs_verify_acf_schema(false);
    if ($verified['errors'] !== array() || $verified['migrations'] !== array()) {
        throw new RuntimeException(implode('; ', array_merge($verified['errors'], $verified['migrations'])));
    }
}

function land76wp_service_hubs_snapshot_post($post_id)
{
    $post = get_post($post_id);
    if (!$post instanceof WP_Post) {
        return array('post_id' => (int) $post_id, 'missing' => true);
    }
    return array(
        'post_id' => (int) $post_id,
        'post_type' => $post->post_type,
        'post_status' => $post->post_status,
        'post_name' => $post->post_name,
        'post_parent' => (int) $post->post_parent,
        'permalink' => land76wp_service_hubs_normalize_url(get_permalink($post)),
        'template' => (string) get_page_template_slug($post_id),
        'post_title' => $post->post_title,
        'post_excerpt' => $post->post_excerpt,
        'post_content_sha256' => hash('sha256', (string) $post->post_content),
        'categories' => wp_get_post_categories($post_id),
        'owner' => (string) get_post_meta($post_id, '_land76_import_owner', true),
        'release_id' => (string) get_post_meta($post_id, '_land76_release_id', true),
        'checksum' => (string) get_post_meta($post_id, '_land76_import_checksum', true),
    );
}

function land76wp_service_hubs_revalidate_stage_targets(array $plan)
{
    $errors = array();
    foreach ($plan['operations'] as $operation) {
        if ($operation['kind'] === 'grouping_term') {
            $term = get_term_by('slug', $operation['slug'], 'category');
            if ($operation['action'] === 'create') {
                if ($term instanceof WP_Term) {
                    $errors[] = land76wp_service_hubs_error('stage_target_changed', $operation['page_key']);
                }
                continue;
            }
            if (!$term instanceof WP_Term
                || (int) $term->term_id !== (int) $operation['term_id']
                || !hash_equals(land76wp_service_hubs_import_owner(), (string) get_term_meta($term->term_id, '_land76_import_owner', true))
                || !hash_equals((string) $operation['service_id'], (string) get_term_meta($term->term_id, '_land76_service_id', true))) {
                $errors[] = land76wp_service_hubs_error('stage_target_changed', $operation['page_key']);
            }
            continue;
        }

        if ($operation['kind'] !== 'post') {
            continue;
        }
        $item = $operation['item'];
        if ($operation['action'] === 'reuse_update') {
            $errors = array_merge(
                $errors,
                land76wp_service_hubs_verify_reuse_target($operation)
            );
            continue;
        }
        if ($operation['action'] === 'published') {
            $errors[] = land76wp_service_hubs_error('published_record_cannot_be_restaged', $item['page_key']);
            continue;
        }
        if ((int) $operation['post_id'] === 0) {
            if (land76wp_service_hubs_find_page_key_posts($item['page_key']) !== array()
                || land76wp_service_hubs_find_global_slug_posts($item['slug']) !== array()) {
                $errors[] = land76wp_service_hubs_error('stage_target_changed', $item['page_key']);
            }
            continue;
        }

        $post = get_post((int) $operation['post_id']);
        if (!$post instanceof WP_Post
            || $post->post_status !== 'draft'
            || $post->post_type !== $operation['post_type']
            || $post->post_name !== $item['slug']
            || !hash_equals(land76wp_service_hubs_import_owner(), (string) get_post_meta($post->ID, '_land76_import_owner', true))
            || !hash_equals((string) $item['page_key'], (string) get_post_meta($post->ID, '_land76_page_key', true))
            || !hash_equals((string) $item['service_id'], (string) get_post_meta($post->ID, '_land76_service_id', true))
            || !hash_equals((string) $item['topic_key'], (string) get_post_meta($post->ID, '_land76_topic_key', true))
            || !hash_equals((string) $plan['release_id'], (string) get_post_meta($post->ID, '_land76_release_id', true))) {
            $errors[] = land76wp_service_hubs_error('stage_target_changed', $item['page_key']);
        }
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_ensure_grouping_term(array $operation, array &$stats)
{
    if ($operation['action'] === 'unchanged') {
        $stats['unchanged']++;
        return (int) $operation['term_id'];
    }

    $term_id = (int) $operation['term_id'];
    if ($operation['action'] === 'create') {
        $inserted = wp_insert_term($operation['service_id'], 'category', array('slug' => $operation['slug']));
        if (is_wp_error($inserted) || empty($inserted['term_id'])) {
            $message = is_wp_error($inserted) ? $inserted->get_error_message() : 'missing term_id';
            throw new RuntimeException(land76wp_service_hubs_error('grouping_term_create_failed', $message));
        }
        $term_id = (int) $inserted['term_id'];
        $stats['created']++;
    } else {
        $stats['updated']++;
    }

    update_term_meta($term_id, '_land76_release_id', $stats['release_id']);
    update_term_meta($term_id, '_land76_manifest_sha256', $stats['manifest_sha256']);
    update_term_meta($term_id, '_land76_page_key', $operation['page_key']);
    update_term_meta($term_id, '_land76_service_id', $operation['service_id']);
    update_term_meta($term_id, '_land76_topic_key', $operation['service_id']);
    update_term_meta($term_id, '_land76_canonical', $operation['canonical']);
    update_term_meta($term_id, '_land76_hub_url', $operation['canonical']);
    update_term_meta($term_id, '_land76_archive_policy', 'redirect_to_hub');
    update_term_meta($term_id, '_land76_import_owner', land76wp_service_hubs_import_owner());
    update_term_meta($term_id, '_land76_import_checksum', $operation['checksum']);

    return $term_id;
}

function land76wp_service_hubs_merge_categories(array $current_categories, $base_category, $grouping_term_id, array $all_grouping_ids)
{
    $managed = array_merge(array(72, 74), array_map('intval', $all_grouping_ids));
    $preserved = array_diff(array_map('intval', $current_categories), $managed);
    $merged = array_unique(array_merge($preserved, array((int) $base_category, (int) $grouping_term_id)));
    sort($merged, SORT_NUMERIC);

    return array_values($merged);
}

function land76wp_service_hubs_resolve_related_slugs(array $references)
{
    $resolved = array();
    foreach ($references as $reference) {
        $slug = is_array($reference) && isset($reference['slug']) ? (string) $reference['slug'] : (string) $reference;
        $canonical = is_array($reference) && isset($reference['canonical'])
            ? land76wp_service_hubs_normalize_url($reference['canonical'])
            : 'https://exp76.ru/' . sanitize_title($slug) . '/';
        $slug = sanitize_title($slug);
        $matches = land76wp_service_hubs_find_global_slug_posts($slug);
        if (count($matches) !== 1 || !$matches[0] instanceof WP_Post || $matches[0]->post_status !== 'publish') {
            throw new RuntimeException(land76wp_service_hubs_error('related_slug_conflict', $slug));
        }
        $post = $matches[0];
        $actual_canonical = land76wp_service_hubs_normalize_url(get_permalink($post));
        if ($canonical === '' || !hash_equals($canonical, $actual_canonical)) {
            throw new RuntimeException(land76wp_service_hubs_error('related_canonical_mismatch', $slug));
        }
        if (hash_equals(land76wp_service_hubs_import_owner(), (string) get_post_meta($post->ID, '_land76_import_owner', true))) {
            $stored_canonical = (string) get_post_meta($post->ID, '_land76_canonical', true);
            if (!hash_equals($canonical, $stored_canonical)) {
                throw new RuntimeException(land76wp_service_hubs_error('related_canonical_mismatch', $slug));
            }
        }
        $is_registered_hub = false;
        foreach (land76wp_service_hub_registry() as $hub) {
            if ((int) $hub['hub_post_id'] === (int) $post->ID) {
                $is_registered_hub = true;
                break;
            }
        }
        $related_page_key = (string) get_post_meta($post->ID, '_land76_page_key', true);
        $is_managed_child = function_exists('land76wp_is_managed_service_hub_post')
            && land76wp_is_managed_service_hub_post($post->ID)
            && strpos($related_page_key, '-CHILD-') !== false;
        $is_legacy_commercial = $post->post_type === 'post' && has_category(74, $post->ID);
        if (!$is_registered_hub && !$is_managed_child && !$is_legacy_commercial) {
            throw new RuntimeException(land76wp_service_hubs_error('related_role_mismatch', $slug));
        }
        $resolved[] = (int) $post->ID;
    }

    return array_values(array_unique($resolved));
}

function land76wp_service_hubs_resolve_page_key($page_key, array $post_ids)
{
    if (isset($post_ids[$page_key])) {
        return (int) $post_ids[$page_key];
    }
    if (preg_match('/^(S(?:[1-9]|1[0-5]))-HUB$/', (string) $page_key, $matches)) {
        $hub = land76wp_service_hub_by_service_id($matches[1]);
        if ($hub === null) {
            return 0;
        }
        $post = get_post((int) $hub['hub_post_id']);
        if (!$post instanceof WP_Post || $post->post_type !== 'page' || $post->post_status !== 'publish') {
            return 0;
        }
        $permalink = land76wp_service_hubs_normalize_url(get_permalink($post));
        return hash_equals($hub['canonical'], $permalink) ? (int) $post->ID : 0;
    }

    $reuse_contracts = land76wp_service_hubs_reuse_contracts();
    if (isset($reuse_contracts[$page_key])) {
        $contract = $reuse_contracts[$page_key];
        $post = get_post((int) $contract['post_id']);
        if (!$post instanceof WP_Post
            || (int) $post->ID !== (int) $contract['post_id']
            || !hash_equals((string) $contract['post_type'], (string) $post->post_type)
            || !hash_equals((string) $contract['post_status'], (string) $post->post_status)
            || !hash_equals((string) $contract['slug'], (string) $post->post_name)
            || (int) $post->post_parent !== (int) $contract['parent_id']
            || !hash_equals((string) $contract['target_url'], land76wp_service_hubs_normalize_url(get_permalink($post)))
            || !hash_equals((string) $contract['target_template'], (string) get_page_template_slug($post->ID))
            || !hash_equals(land76wp_service_hubs_import_owner(), (string) get_post_meta($post->ID, '_land76_import_owner', true))
            || !hash_equals((string) $contract['page_key'], (string) get_post_meta($post->ID, '_land76_page_key', true))
            || !hash_equals((string) $contract['service_id'], (string) get_post_meta($post->ID, '_land76_service_id', true))
            || !hash_equals((string) $contract['service_id'], (string) get_post_meta($post->ID, '_land76_topic_key', true))) {
            return 0;
        }
        $page_key_matches = land76wp_service_hubs_find_page_key_posts($page_key);
        $slug_matches = land76wp_service_hubs_find_global_slug_posts($contract['slug']);
        if (count($page_key_matches) !== 1
            || (int) $page_key_matches[0]->ID !== (int) $contract['post_id']
            || count($slug_matches) !== 1
            || (int) $slug_matches[0]->ID !== (int) $contract['post_id']) {
            return 0;
        }

        return (int) $contract['post_id'];
    }

    $matches = land76wp_service_hubs_find_owned_posts((string) $page_key, 'post');
    return count($matches) === 1 ? (int) $matches[0]->ID : 0;
}

function land76wp_service_hubs_apply_acf(array $item, $post_id, array $post_ids)
{
    $field_keys = array(
        'selected_real_projects' => 'field_land76_selected_real_projects',
        'blogseo_related_services' => 'field_blogseo_related_services',
    );
    if (isset($item['acf']) && is_array($item['acf'])) {
        foreach ($item['acf'] as $field_name => $field_value) {
            if (isset($field_keys[$field_name])) {
                update_field($field_keys[$field_name], $field_value, $post_id);
            } else {
                update_field($field_name, $field_value, $post_id);
            }
        }
    }
    if (array_key_exists('case_ids', $item)) {
        update_field('field_land76_selected_real_projects', array_map('intval', $item['case_ids']), $post_id);
    }
    if (array_key_exists('related_service_page_keys', $item)) {
        $related_ids = array();
        foreach ($item['related_service_page_keys'] as $page_key) {
            $related_id = land76wp_service_hubs_resolve_page_key($page_key, $post_ids);
            if (!$related_id) {
                throw new RuntimeException(land76wp_service_hubs_error('unresolved_relation', $page_key));
            }
            $related_ids[] = $related_id;
        }
        update_field('field_blogseo_related_services', array_values(array_unique($related_ids)), $post_id);
    }
    if (array_key_exists('related_service_slugs', $item)) {
        update_field(
            'field_blogseo_related_services',
            land76wp_service_hubs_resolve_related_slugs($item['related_service_slugs']),
            $post_id
        );
    }
}

function land76wp_service_hubs_apply_post_metadata(array $item, $post_id, $release_id, $manifest_sha256, array $post_ids)
{
    update_post_meta($post_id, '_land76_release_id', $release_id);
    update_post_meta($post_id, '_land76_manifest_sha256', $manifest_sha256);
    update_post_meta($post_id, '_land76_page_key', $item['page_key']);
    update_post_meta($post_id, '_land76_service_id', $item['service_id']);
    update_post_meta($post_id, '_land76_topic_key', $item['topic_key']);
    update_post_meta($post_id, '_land76_canonical', $item['canonical']);
    update_post_meta($post_id, '_land76_import_owner', land76wp_service_hubs_import_owner());
    update_post_meta($post_id, '_land76_import_checksum', $item['checksum']);
    update_post_meta($post_id, '_land76_main_image_url', $item['main_image']['url']);
    update_post_meta($post_id, '_land76_main_image_alt', $item['main_image']['alt']);
    $presentation_meta = land76wp_service_hubs_presentation_meta_keys();
    $presentation_images = isset($item['presentation_images']) && is_array($item['presentation_images'])
        ? $item['presentation_images']
        : array();
    foreach ($presentation_meta as $role => $meta_keys) {
        if (isset($presentation_images[$role]) && is_array($presentation_images[$role])) {
            update_post_meta($post_id, $meta_keys['url'], $presentation_images[$role]['url']);
            update_post_meta($post_id, $meta_keys['alt'], $presentation_images[$role]['alt']);
        }
    }

    if ($item['role'] === 'geo') {
        update_post_meta($post_id, '_wp_page_template', 'page-service-hub-region.php');
        update_post_meta($post_id, '_land76_region', $item['city_parent_slug']);
        update_post_meta($post_id, '_land76_local_evidence', wp_json_encode($item['local_evidence'], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    }
    if (isset($item['seo']) && is_array($item['seo'])) {
        if (array_key_exists('title', $item['seo'])) {
            update_post_meta($post_id, '_aioseo_title', (string) $item['seo']['title']);
        }
        if (array_key_exists('description', $item['seo'])) {
            update_post_meta($post_id, '_aioseo_description', (string) $item['seo']['description']);
        }
    }
    if (array_key_exists('related_article_page_keys', $item)) {
        $related_ids = array();
        foreach ($item['related_article_page_keys'] as $page_key) {
            $related_id = land76wp_service_hubs_resolve_page_key($page_key, $post_ids);
            if (!$related_id) {
                throw new RuntimeException(land76wp_service_hubs_error('unresolved_relation', $page_key));
            }
            $related_ids[] = $related_id;
        }
        update_post_meta($post_id, '_land76_related_article_ids', array_values(array_unique($related_ids)));
    }

    land76wp_service_hubs_apply_acf($item, $post_id, $post_ids);
    $attachment_id = attachment_url_to_postid($item['main_image']['url']);
    if (!$attachment_id) {
        throw new RuntimeException(land76wp_service_hubs_error('unresolved_main_image', $item['main_image']['url']));
    }
    set_post_thumbnail($post_id, $attachment_id);
}

function land76wp_service_hubs_apply_reuse_item(array $operation, $release_id, $manifest_sha256, array $post_ids, array $grouping_ids, array $all_grouping_ids)
{
    $item = $operation['item'];
    $contract = $operation['reuse_contract'];
    $post_id = (int) $contract['post_id'];
    $updated_id = wp_update_post(wp_slash(array(
        'ID' => $post_id,
        'post_title' => wp_strip_all_tags($item['post_title']),
        'post_content' => $item['post_content'],
        'post_excerpt' => isset($item['post_excerpt']) ? (string) $item['post_excerpt'] : '',
    )), true);
    if (is_wp_error($updated_id) || (int) $updated_id !== $post_id) {
        $message = is_wp_error($updated_id) ? $updated_id->get_error_message() : 'post id changed';
        throw new RuntimeException(land76wp_service_hubs_error('reuse_publish_failed', $message));
    }

    $current_categories = wp_get_post_categories($post_id);
    $categories = land76wp_service_hubs_merge_categories(
        $current_categories,
        74,
        $grouping_ids[$item['service_id']],
        $all_grouping_ids
    );
    wp_set_post_categories($post_id, $categories, false);
    land76wp_service_hubs_apply_post_metadata(
        $item,
        $post_id,
        $release_id,
        $manifest_sha256,
        $post_ids
    );
    update_post_meta($post_id, '_wp_page_template', (string) $contract['target_template']);
}

function land76wp_service_hubs_release_lock_name($release_id)
{
    global $wpdb;

    $database_name = isset($wpdb->dbname) ? (string) $wpdb->dbname : '';
    $table_prefix = isset($wpdb->prefix) ? (string) $wpdb->prefix : '';
    $site_identity = function_exists('home_url') ? (string) home_url('/') : '';
    return hash(
        'sha256',
        wp_json_encode(
            array(
                'owner' => land76wp_service_hubs_import_owner(),
                'database' => $database_name,
                'prefix' => $table_prefix,
                'site' => $site_identity,
                'release_id' => (string) $release_id,
            ),
            JSON_UNESCAPED_SLASHES
        )
    );
}

function land76wp_service_hubs_acquire_release_lock($release_id)
{
    global $wpdb;

    if (!is_string($release_id) || $release_id === '') {
        return array();
    }
    $lock_name = land76wp_service_hubs_release_lock_name($release_id);
    $query = $wpdb->prepare(
        'SELECT GET_LOCK(%s, 0) AS acquired, CONNECTION_ID() AS connection_id',
        $lock_name
    );
    if (!is_string($query)) {
        return array();
    }
    $row = $wpdb->get_row($query, ARRAY_A);
    if (!is_array($row)
        || !isset($row['acquired'], $row['connection_id'])
        || (string) $row['acquired'] !== '1'
        || (string) $row['connection_id'] === '') {
        return array();
    }
    $lock = array(
        'name' => $lock_name,
        'connection_id' => (string) $row['connection_id'],
    );

    return land76wp_service_hubs_owns_release_lock($lock) ? $lock : array();
}

function land76wp_service_hubs_owns_release_lock(array $lock)
{
    global $wpdb;

    if (!isset($lock['name'], $lock['connection_id'])
        || !is_string($lock['name'])
        || $lock['name'] === ''
        || !is_string($lock['connection_id'])
        || $lock['connection_id'] === '') {
        return false;
    }
    $query = $wpdb->prepare(
        'SELECT CONNECTION_ID() AS connection_id, IS_USED_LOCK(%s) AS owner_connection_id',
        $lock['name']
    );
    if (!is_string($query)) {
        return false;
    }
    $row = $wpdb->get_row($query, ARRAY_A);
    if (!is_array($row) || !isset($row['connection_id'], $row['owner_connection_id'])) {
        return false;
    }

    return hash_equals($lock['connection_id'], (string) $row['connection_id'])
        && hash_equals($lock['connection_id'], (string) $row['owner_connection_id']);
}

function land76wp_service_hubs_release_release_lock(array $lock)
{
    global $wpdb;

    if (!land76wp_service_hubs_owns_release_lock($lock)) {
        return false;
    }
    $query = $wpdb->prepare('SELECT RELEASE_LOCK(%s)', $lock['name']);
    if (!is_string($query)) {
        return false;
    }

    return (string) $wpdb->get_var($query) === '1';
}

function land76wp_service_hubs_pin_wpdb_connection()
{
    global $wpdb;

    $property = null;
    $previous_reconnect_retries = null;
    $changed = false;
    try {
        $reflection = new ReflectionObject($wpdb);
        if (!$reflection->hasProperty('reconnect_retries')) {
            return array();
        }
        $query_method = $reflection->getMethod('query');
        $do_query_method = $reflection->getMethod('_do_query');
        $check_connection_method = $reflection->getMethod('check_connection');
        $property = $reflection->getProperty('reconnect_retries');
        if ($query_method->getDeclaringClass()->getName() !== 'wpdb'
            || $do_query_method->getDeclaringClass()->getName() !== 'wpdb'
            || $check_connection_method->getDeclaringClass()->getName() !== 'wpdb'
            || $property->getDeclaringClass()->getName() !== 'wpdb') {
            return array();
        }
        $property->setAccessible(true);
        $previous_reconnect_retries = $property->getValue($wpdb);
        if (!is_int($previous_reconnect_retries) || $previous_reconnect_retries < 0) {
            return array();
        }
        $property->setValue($wpdb, 0);
        $changed = true;
        if ((int) $property->getValue($wpdb) !== 0) {
            $property->setValue($wpdb, $previous_reconnect_retries);
            return array();
        }

        return array(
            'wpdb' => $wpdb,
            'property' => $property,
            'reconnect_retries' => $previous_reconnect_retries,
        );
    } catch (Throwable $error) {
        if ($changed && $property instanceof ReflectionProperty) {
            try {
                $property->setValue($wpdb, $previous_reconnect_retries);
            } catch (Throwable $restore_error) {
                error_log('[land76-service-hubs] Failed to restore wpdb reconnect policy after pin failure.');
            }
        }

        return array();
    }
}

function land76wp_service_hubs_restore_wpdb_connection(array $pin)
{
    if (!isset($pin['wpdb'], $pin['property'], $pin['reconnect_retries'])
        || !is_object($pin['wpdb'])
        || !$pin['property'] instanceof ReflectionProperty
        || !is_int($pin['reconnect_retries'])
        || $pin['reconnect_retries'] < 0) {
        return false;
    }
    try {
        $pin['property']->setValue($pin['wpdb'], $pin['reconnect_retries']);
        return (int) $pin['property']->getValue($pin['wpdb']) === $pin['reconnect_retries'];
    } catch (Throwable $error) {
        return false;
    }
}

function land76wp_service_hubs_execute_stage(array $plan)
{
    global $wpdb;

    $stats = $plan;
    $stats['created'] = 0;
    $stats['updated'] = 0;
    $stats['unchanged'] = 0;
    $stats['rollback_snapshot'] = array();

    $release_id = isset($plan['release_id']) ? $plan['release_id'] : '';
    $release_lock = land76wp_service_hubs_acquire_release_lock($release_id);
    if ($release_lock === array()) {
        $stats['errors'][] = land76wp_service_hubs_error('stage_lock_unavailable', (string) $release_id);
        return $stats;
    }
    $connection_pin = land76wp_service_hubs_pin_wpdb_connection();
    if ($connection_pin === array()) {
        if (!land76wp_service_hubs_release_release_lock($release_lock)) {
            error_log('[land76-service-hubs] Failed to release advisory lock after connection pin failure.');
        }
        $stats['errors'][] = land76wp_service_hubs_error('stage_connection_pin_unavailable');
        return $stats;
    }

    try {

    $stats['errors'] = array_merge($stats['errors'], land76wp_service_hubs_revalidate_stage_targets($plan));
    if ($stats['errors'] !== array()) {
        return $stats;
    }

    $is_noop = empty($plan['acf_missing']) && empty($plan['acf_migrations']);
    foreach ($plan['operations'] as $operation) {
        if (!in_array($operation['action'], array('unchanged', 'reuse_update'), true)) {
            $is_noop = false;
            break;
        }
    }
    if ($is_noop) {
        $stats['errors'] = array_merge($stats['errors'], land76wp_service_hubs_verify_grouping_terms($plan));
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] === 'post') {
                if ($operation['action'] === 'reuse_update') {
                    $stats['errors'] = array_merge(
                        $stats['errors'],
                        land76wp_service_hubs_verify_reuse_target($operation)
                    );
                } else {
                    $stats['errors'] = array_merge(
                        $stats['errors'],
                        land76wp_service_hubs_verify_staged_item($operation, $plan['release_id'], $plan['manifest_sha256'], 'draft')
                    );
                }
            }
        }
        $stats['errors'] = array_values(array_unique($stats['errors']));
        if ($stats['errors'] === array()) {
            $stats['unchanged'] = count($plan['operations']);
        }
        return $stats;
    }

    if ($wpdb->query('START TRANSACTION') === false) {
        $stats['errors'][] = land76wp_service_hubs_error('transaction_start_failed', (string) $wpdb->last_error);
        return $stats;
    }
    try {
        $target_errors = land76wp_service_hubs_revalidate_stage_targets($plan);
        if ($target_errors !== array()) {
            throw new RuntimeException(implode('; ', $target_errors));
        }
        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            throw new RuntimeException(land76wp_service_hubs_error('stage_lock_lost'));
        }
        land76wp_service_hubs_install_missing_acf_schema(
            isset($plan['acf_missing']) ? $plan['acf_missing'] : array(),
            isset($plan['acf_migrations']) ? $plan['acf_migrations'] : array()
        );
        $planned_items = array();
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] === 'post') {
                $planned_items[] = $operation['item'];
            }
        }
        $item_acf = land76wp_service_hubs_preflight_item_acf($planned_items);
        if ($item_acf['errors'] !== array() || $item_acf['missing'] !== array()) {
            throw new RuntimeException(
                land76wp_service_hubs_error(
                    'acf_schema_incompatible',
                    implode('; ', array_merge($item_acf['errors'], $item_acf['missing']))
                )
            );
        }
        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            throw new RuntimeException(land76wp_service_hubs_error('stage_lock_lost'));
        }
        $grouping_ids = array();
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] !== 'grouping_term') {
                continue;
            }
            if ($operation['term_id']) {
                $stats['rollback_snapshot'][] = array(
                    'term_id' => (int) $operation['term_id'],
                    'release_id' => (string) get_term_meta($operation['term_id'], '_land76_release_id', true),
                    'checksum' => (string) get_term_meta($operation['term_id'], '_land76_import_checksum', true),
                );
            }
            $grouping_ids[$operation['service_id']] = land76wp_service_hubs_ensure_grouping_term($operation, $stats);
        }

        $post_ids = array();
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] !== 'post') {
                continue;
            }
            $item = $operation['item'];
            if ($operation['action'] === 'reuse_update') {
                $post_ids[$item['page_key']] = (int) $operation['post_id'];
                $stats['unchanged']++;
                continue;
            }
            if ($operation['action'] === 'unchanged') {
                $post_ids[$item['page_key']] = (int) $operation['post_id'];
                $stats['unchanged']++;
                continue;
            }
            if ($operation['post_id']) {
                $stats['rollback_snapshot'][] = land76wp_service_hubs_snapshot_post($operation['post_id']);
            } else {
                $stats['rollback_snapshot'][] = array('page_key' => $item['page_key'], 'planned_create' => true);
            }
            $post_data = array(
                'post_type' => $operation['post_type'],
                'post_status' => 'draft',
                'post_name' => $item['slug'],
                'post_parent' => (int) $operation['parent_id'],
                'post_title' => wp_strip_all_tags($item['post_title']),
                'post_content' => $item['post_content'],
                'post_excerpt' => isset($item['post_excerpt']) ? (string) $item['post_excerpt'] : '',
            );
            if ($operation['action'] === 'update') {
                $post_data['ID'] = (int) $operation['post_id'];
                $post_id = wp_update_post(wp_slash($post_data), true);
                $stats['updated']++;
            } else {
                $post_id = wp_insert_post(wp_slash($post_data), true);
                $stats['created']++;
            }
            if (is_wp_error($post_id) || !$post_id) {
                $message = is_wp_error($post_id) ? $post_id->get_error_message() : 'missing post_id';
                throw new RuntimeException(land76wp_service_hubs_error('stage_post_failed', $message));
            }
            $post_ids[$item['page_key']] = (int) $post_id;
        }

        $all_grouping_ids = array_values($grouping_ids);
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] !== 'post'
                || in_array($operation['action'], array('unchanged', 'reuse_update'), true)) {
                continue;
            }
            $item = $operation['item'];
            $post_id = $post_ids[$item['page_key']];
            if ($item['role'] !== 'geo') {
                $base_category = $item['role'] === 'article' ? 72 : 74;
                $current_categories = $operation['action'] === 'create' ? array() : wp_get_post_categories($post_id);
                $categories = land76wp_service_hubs_merge_categories(
                    $current_categories,
                    $base_category,
                    $grouping_ids[$item['service_id']],
                    $all_grouping_ids
                );
                wp_set_post_categories($post_id, $categories, false);
            }
            land76wp_service_hubs_apply_post_metadata(
                $item,
                $post_id,
                $plan['release_id'],
                $plan['manifest_sha256'],
                $post_ids
            );
        }

        $verification_plan = $plan;
        foreach ($verification_plan['operations'] as &$verification_operation) {
            if ($verification_operation['kind'] === 'post') {
                $verification_operation['post_id'] = $post_ids[$verification_operation['item']['page_key']];
            }
        }
        unset($verification_operation);
        $verification_errors = land76wp_service_hubs_verify_grouping_terms($verification_plan);
        foreach ($verification_plan['operations'] as $verification_operation) {
            if ($verification_operation['kind'] !== 'post') {
                continue;
            }
            if ($verification_operation['action'] === 'reuse_update') {
                $verification_errors = array_merge(
                    $verification_errors,
                    land76wp_service_hubs_verify_reuse_target($verification_operation)
                );
            } else {
                $verification_errors = array_merge(
                    $verification_errors,
                    land76wp_service_hubs_verify_staged_item(
                        $verification_operation,
                        $plan['release_id'],
                        $plan['manifest_sha256'],
                        'draft'
                    )
                );
            }
        }
        if ($verification_errors !== array()) {
            throw new RuntimeException(
                land76wp_service_hubs_error('stage_verification_failed', implode('; ', array_values(array_unique($verification_errors))))
            );
        }

        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            throw new RuntimeException(land76wp_service_hubs_error('stage_lock_lost'));
        }
        if ($wpdb->query('COMMIT') === false) {
            throw new RuntimeException(land76wp_service_hubs_error('transaction_commit_failed', (string) $wpdb->last_error));
        }
    } catch (Throwable $error) {
        if ($wpdb->query('ROLLBACK') === false) {
            $stats['errors'][] = land76wp_service_hubs_error('transaction_rollback_failed', (string) $wpdb->last_error);
        }
        $stats['errors'][] = land76wp_service_hubs_error('stage_rollback', $error->getMessage());
        $stats['created'] = 0;
        $stats['updated'] = 0;
    }

    } finally {
        $lock_released = land76wp_service_hubs_release_release_lock($release_lock);
        $connection_restored = land76wp_service_hubs_restore_wpdb_connection($connection_pin);
        if (!$lock_released) {
            error_log('[land76-service-hubs] Advisory lock ownership was lost; release was skipped.');
        }
        if (!$connection_restored) {
            error_log('[land76-service-hubs] Failed to restore wpdb reconnect policy.');
        }
    }

    return $stats;
}

function land76wp_service_hubs_required_categories_for_item(array $item)
{
    if ($item['role'] === 'geo') {
        return array();
    }
    $hub = land76wp_service_hub_by_service_id($item['service_id']);
    $term = $hub === null ? null : get_term_by('slug', $hub['grouping_slug'], 'category');
    if (!$term instanceof WP_Term) {
        return array();
    }
    return array($item['role'] === 'article' ? 72 : 74, (int) $term->term_id);
}

function land76wp_service_hubs_normalize_field_value($value)
{
    if ($value instanceof WP_Post) {
        return (int) $value->ID;
    }
    if (!is_array($value)) {
        return $value;
    }
    $normalized = array();
    foreach ($value as $key => $child) {
        $normalized[$key] = land76wp_service_hubs_normalize_field_value($child);
    }
    if (land76wp_service_hubs_is_list($normalized)) {
        usort($normalized, function ($left, $right) {
            return strcmp(wp_json_encode($left), wp_json_encode($right));
        });
    } else {
        ksort($normalized, SORT_STRING);
    }

    return $normalized;
}

function land76wp_service_hubs_field_values_equal($expected, $actual)
{
    return wp_json_encode(land76wp_service_hubs_normalize_field_value($expected), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)
        === wp_json_encode(land76wp_service_hubs_normalize_field_value($actual), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
}

function land76wp_service_hubs_verify_published_permalink($post, array $item)
{
    if (!$post instanceof WP_Post || $post->post_status !== 'publish') {
        return array();
    }
    $permalink = land76wp_service_hubs_normalize_url(get_permalink($post));
    if (!hash_equals((string) $item['canonical'], $permalink)) {
        return array(land76wp_service_hubs_error('staged_permalink_mismatch', $item['page_key']));
    }

    return array();
}

function land76wp_service_hubs_verify_staged_item(array $operation, $release_id, $manifest_sha256, $required_status = '')
{
    $errors = array();
    $item = $operation['item'];
    $post_id = (int) $operation['post_id'];
    $post = get_post($post_id);
    if (!$post instanceof WP_Post) {
        return array(land76wp_service_hubs_error('missing_staged_record', $item['page_key']));
    }
    if ($required_status !== '' && $post->post_status !== $required_status) {
        $errors[] = land76wp_service_hubs_error('invalid_staged_status', $item['page_key']);
    } elseif ($required_status === '' && !in_array($post->post_status, array('draft', 'publish'), true)) {
        $errors[] = land76wp_service_hubs_error('invalid_staged_status', $item['page_key']);
    }
    if ($post->post_type !== $operation['post_type'] || $post->post_name !== $item['slug'] || (int) $post->post_parent !== (int) $operation['parent_id']) {
        $errors[] = land76wp_service_hubs_error('staged_shape_mismatch', $item['page_key']);
    }
    $expected_excerpt = isset($item['post_excerpt']) ? (string) $item['post_excerpt'] : '';
    if ($post->post_title !== wp_strip_all_tags($item['post_title'])
        || $post->post_content !== $item['post_content']
        || $post->post_excerpt !== $expected_excerpt) {
        $errors[] = land76wp_service_hubs_error('staged_content_mismatch', $item['page_key']);
    }
    $expected_meta = array(
        '_land76_release_id' => $release_id,
        '_land76_manifest_sha256' => $manifest_sha256,
        '_land76_page_key' => $item['page_key'],
        '_land76_service_id' => $item['service_id'],
        '_land76_topic_key' => $item['topic_key'],
        '_land76_canonical' => $item['canonical'],
        '_land76_import_owner' => land76wp_service_hubs_import_owner(),
        '_land76_import_checksum' => $item['checksum'],
        '_land76_main_image_url' => $item['main_image']['url'],
        '_land76_main_image_alt' => $item['main_image']['alt'],
    );
    $presentation_meta = land76wp_service_hubs_presentation_meta_keys();
    $presentation_images = isset($item['presentation_images']) && is_array($item['presentation_images'])
        ? $item['presentation_images']
        : array();
    foreach ($presentation_meta as $role => $meta_keys) {
        if (isset($presentation_images[$role]) && is_array($presentation_images[$role])) {
            $expected_meta[$meta_keys['url']] = $presentation_images[$role]['url'];
            $expected_meta[$meta_keys['alt']] = $presentation_images[$role]['alt'];
        }
    }
    foreach ($expected_meta as $meta_key => $expected_value) {
        $actual_value = (string) get_post_meta($post_id, $meta_key, true);
        if (!hash_equals((string) $expected_value, $actual_value)) {
            $errors[] = land76wp_service_hubs_error('staged_metadata_mismatch', $item['page_key'] . '.' . $meta_key);
        }
    }
    $errors = array_merge($errors, land76wp_service_hubs_verify_published_permalink($post, $item));
    $required_categories = land76wp_service_hubs_required_categories_for_item($item);
    $actual_categories = array_map('intval', wp_get_post_categories($post_id));
    foreach ($required_categories as $category_id) {
        if (!in_array((int) $category_id, $actual_categories, true)) {
            $errors[] = land76wp_service_hubs_error('staged_category_mismatch', $item['page_key']);
        }
    }
    if ($item['role'] === 'article' && in_array(74, $actual_categories, true)) {
        $errors[] = land76wp_service_hubs_error('mutually_exclusive_category', $item['page_key']);
    }
    if ($item['role'] === 'child_service' && in_array(72, $actual_categories, true)) {
        $errors[] = land76wp_service_hubs_error('mutually_exclusive_category', $item['page_key']);
    }
    $expected_grouping_id = count($required_categories) === 2 ? (int) $required_categories[1] : 0;
    $other_grouping_ids = array();
    foreach (land76wp_service_hub_registry() as $hub) {
        $grouping_term = get_term_by('slug', $hub['grouping_slug'], 'category');
        if ($grouping_term instanceof WP_Term
            && (int) $grouping_term->term_id !== $expected_grouping_id
            && in_array((int) $grouping_term->term_id, $actual_categories, true)) {
            $other_grouping_ids[] = (int) $grouping_term->term_id;
        }
    }
    if ($other_grouping_ids !== array()) {
        $errors[] = land76wp_service_hubs_error('staged_category_mismatch', $item['page_key'] . '.other_grouping_ids');
    }
    $attachment_id = get_post_thumbnail_id($post_id);
    if (!$attachment_id || attachment_url_to_postid($item['main_image']['url']) !== (int) $attachment_id) {
        $errors[] = land76wp_service_hubs_error('staged_media_mismatch', $item['page_key']);
    }
    if (array_key_exists('case_ids', $item)) {
        $actual_case_ids = get_field('selected_real_projects', $post_id);
        $actual_case_ids = is_array($actual_case_ids) ? array_map('intval', $actual_case_ids) : array();
        $expected_case_ids = array_map('intval', $item['case_ids']);
        sort($actual_case_ids);
        sort($expected_case_ids);
        if ($actual_case_ids !== $expected_case_ids) {
            $errors[] = land76wp_service_hubs_error('staged_acf_mismatch', $item['page_key'] . '.selected_real_projects');
        }
    }
    if (isset($item['acf']) && is_array($item['acf'])) {
        foreach ($item['acf'] as $field_name => $expected_value) {
            $actual_value = get_field($field_name, $post_id);
            if (!land76wp_service_hubs_field_values_equal($expected_value, $actual_value)) {
                $errors[] = land76wp_service_hubs_error('staged_acf_mismatch', $item['page_key'] . '.' . $field_name);
            }
        }
    }
    if (array_key_exists('related_service_page_keys', $item)) {
        $expected_related_ids = array();
        foreach ($item['related_service_page_keys'] as $related_page_key) {
            $expected_related_ids[] = land76wp_service_hubs_resolve_page_key($related_page_key, array());
        }
        $actual_related_ids = get_field('blogseo_related_services', $post_id);
        if (!land76wp_service_hubs_field_values_equal($expected_related_ids, $actual_related_ids)) {
            $errors[] = land76wp_service_hubs_error('staged_acf_mismatch', $item['page_key'] . '.blogseo_related_services');
        }
    }
    if (array_key_exists('related_service_slugs', $item)) {
        $expected_related_ids = land76wp_service_hubs_resolve_related_slugs($item['related_service_slugs']);
        $actual_related_ids = get_field('blogseo_related_services', $post_id);
        if (!land76wp_service_hubs_field_values_equal($expected_related_ids, $actual_related_ids)) {
            $errors[] = land76wp_service_hubs_error('staged_acf_mismatch', $item['page_key'] . '.blogseo_related_services');
        }
    }
    if (array_key_exists('related_article_page_keys', $item)) {
        $expected_related_ids = array();
        foreach ($item['related_article_page_keys'] as $related_page_key) {
            $expected_related_ids[] = land76wp_service_hubs_resolve_page_key($related_page_key, array());
        }
        $actual_related_ids = get_post_meta($post_id, '_land76_related_article_ids', true);
        if (!land76wp_service_hubs_field_values_equal($expected_related_ids, $actual_related_ids)) {
            $errors[] = land76wp_service_hubs_error('staged_relation_mismatch', $item['page_key'] . '._land76_related_article_ids');
        }
    }
    if (isset($item['seo']) && is_array($item['seo'])) {
        if (array_key_exists('title', $item['seo'])
            && !hash_equals((string) $item['seo']['title'], (string) get_post_meta($post_id, '_aioseo_title', true))) {
            $errors[] = land76wp_service_hubs_error('staged_seo_mismatch', $item['page_key'] . '._aioseo_title');
        }
        if (array_key_exists('description', $item['seo'])
            && !hash_equals((string) $item['seo']['description'], (string) get_post_meta($post_id, '_aioseo_description', true))) {
            $errors[] = land76wp_service_hubs_error('staged_seo_mismatch', $item['page_key'] . '._aioseo_description');
        }
    }
    if ($item['role'] === 'geo') {
        $stored_template = (string) get_post_meta($post_id, '_wp_page_template', true);
        $stored_region = (string) get_post_meta($post_id, '_land76_region', true);
        $stored_evidence = json_decode((string) get_post_meta($post_id, '_land76_local_evidence', true), true);
        if (!hash_equals('page-service-hub-region.php', $stored_template)
            || !hash_equals((string) $item['city_parent_slug'], $stored_region)
            || !land76wp_service_hubs_field_values_equal($item['local_evidence'], $stored_evidence)) {
            $errors[] = land76wp_service_hubs_error('staged_geo_mismatch', $item['page_key'] . '._wp_page_template');
        }
    }
    if ($operation['action'] === 'reuse_update'
        && !hash_equals((string) $operation['template'], (string) get_page_template_slug($post_id))) {
        $errors[] = land76wp_service_hubs_error('staged_template_mismatch', $item['page_key']);
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_verify_grouping_terms(array $plan)
{
    $errors = array();
    foreach ($plan['operations'] as $operation) {
        if ($operation['kind'] !== 'grouping_term') {
            continue;
        }
        $term = get_term_by('slug', $operation['slug'], 'category');
        if (!$term instanceof WP_Term) {
            $errors[] = land76wp_service_hubs_error('missing_grouping_term', $operation['slug']);
            continue;
        }
        $expected = array(
            '_land76_release_id' => $plan['release_id'],
            '_land76_manifest_sha256' => $plan['manifest_sha256'],
            '_land76_page_key' => $operation['page_key'],
            '_land76_service_id' => $operation['service_id'],
            '_land76_topic_key' => $operation['service_id'],
            '_land76_canonical' => $operation['canonical'],
            '_land76_archive_policy' => 'redirect_to_hub',
            '_land76_import_owner' => land76wp_service_hubs_import_owner(),
            '_land76_import_checksum' => $operation['checksum'],
            '_land76_hub_url' => $operation['canonical'],
        );
        foreach ($expected as $key => $value) {
            if (!hash_equals((string) $value, (string) get_term_meta($term->term_id, $key, true))) {
                $errors[] = land76wp_service_hubs_error('grouping_term_mismatch', $operation['slug'] . '.' . $key);
            }
        }
    }

    return array_values(array_unique($errors));
}

function land76wp_service_hubs_publish_plan(array $plan)
{
    global $wpdb;

    $stats = $plan;
    $stats['created'] = 0;
    $stats['updated'] = 0;
    $stats['unchanged'] = 0;
    $stats['rollback_snapshot'] = array();

    $release_id = isset($plan['release_id']) ? $plan['release_id'] : '';
    $release_lock = land76wp_service_hubs_acquire_release_lock($release_id);
    if ($release_lock === array()) {
        $stats['errors'][] = land76wp_service_hubs_error('publish_lock_unavailable', (string) $release_id);
        return $stats;
    }
    $connection_pin = land76wp_service_hubs_pin_wpdb_connection();
    if ($connection_pin === array()) {
        if (!land76wp_service_hubs_release_release_lock($release_lock)) {
            error_log('[land76-service-hubs] Failed to release publish lock after connection pin failure.');
        }
        $stats['errors'][] = land76wp_service_hubs_error('publish_connection_pin_unavailable');
        return $stats;
    }

    try {

    $stats['errors'] = array_merge($stats['errors'], land76wp_service_hubs_verify_grouping_terms($plan));
    $publish_ids = array();
    $reuse_operations = array();
    $post_ids = array();
    $grouping_ids = array();

    foreach ($plan['operations'] as $operation) {
        if ($operation['kind'] === 'grouping_term') {
            $term = get_term_by('slug', $operation['slug'], 'category');
            if ($term instanceof WP_Term) {
                $grouping_ids[$operation['service_id']] = (int) $term->term_id;
            }
            continue;
        }
        if ($operation['kind'] !== 'post') {
            continue;
        }
        $post_ids[$operation['item']['page_key']] = (int) $operation['post_id'];
        if ($operation['action'] === 'reuse_update') {
            $claim_state = isset($operation['reuse_claim_state'])
                ? (string) $operation['reuse_claim_state']
                : '';
            $required_claim_state = hash_equals('managed_exact_match', $claim_state)
                ? 'managed_exact_match'
                : '';
            $reuse_errors = land76wp_service_hubs_verify_reuse_target(
                $operation,
                $required_claim_state
            );
            $stats['errors'] = array_merge($stats['errors'], $reuse_errors);
            $is_exact_managed_reuse = false;
            if ($reuse_errors === array() && $required_claim_state === 'managed_exact_match') {
                $is_exact_managed_reuse = land76wp_service_hubs_verify_staged_item(
                    $operation,
                    $plan['release_id'],
                    $plan['manifest_sha256'],
                    'publish'
                ) === array();
            }
            if ($is_exact_managed_reuse) {
                $stats['unchanged']++;
            } else {
                $reuse_operations[] = $operation;
            }
            continue;
        }
        $item_errors = land76wp_service_hubs_verify_staged_item(
            $operation,
            $plan['release_id'],
            $plan['manifest_sha256']
        );
        $stats['errors'] = array_merge($stats['errors'], $item_errors);
        $post = get_post((int) $operation['post_id']);
        if ($post instanceof WP_Post && $post->post_status === 'publish') {
            $stats['unchanged']++;
        } else {
            $publish_ids[] = (int) $operation['post_id'];
        }
    }
    $stats['errors'] = array_values(array_unique($stats['errors']));
    if ($stats['errors'] !== array()) {
        return $stats;
    }
    if ($publish_ids === array() && $reuse_operations === array()) {
        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            $stats['errors'][] = land76wp_service_hubs_error('publish_lock_lost');
            return $stats;
        }
        $stats['rollback_snapshot'][] = land76wp_service_hubs_active_release_snapshot();
        $activation_error = land76wp_service_hubs_activate_verified_release($plan['release_id']);
        if ($activation_error !== '') {
            $stats['errors'][] = $activation_error;
        }
        return $stats;
    }
    $all_grouping_ids = array_values(array_unique(array_map('intval', $grouping_ids)));
    $transaction_committed = false;

    if ($wpdb->query('START TRANSACTION') === false) {
        $stats['errors'][] = land76wp_service_hubs_error('transaction_start_failed', (string) $wpdb->last_error);
        return $stats;
    }
    try {
        foreach ($reuse_operations as $operation) {
            if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
                throw new RuntimeException(land76wp_service_hubs_error('publish_lock_lost'));
            }
            $reuse_errors = land76wp_service_hubs_verify_reuse_target($operation);
            if ($reuse_errors !== array()) {
                throw new RuntimeException(implode('; ', $reuse_errors));
            }
            $stats['rollback_snapshot'][] = land76wp_service_hubs_snapshot_post($operation['post_id']);
            land76wp_service_hubs_apply_reuse_item(
                $operation,
                $plan['release_id'],
                $plan['manifest_sha256'],
                $post_ids,
                $grouping_ids,
                $all_grouping_ids
            );
            if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
                throw new RuntimeException(land76wp_service_hubs_error('publish_lock_lost'));
            }
            $stats['updated']++;
        }
        foreach ($publish_ids as $post_id) {
            if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
                throw new RuntimeException(land76wp_service_hubs_error('publish_lock_lost'));
            }
            $stats['rollback_snapshot'][] = array('post_id' => $post_id, 'post_status' => 'draft');
            $updated_id = wp_update_post(array('ID' => $post_id, 'post_status' => 'publish'), true);
            if (is_wp_error($updated_id) || !$updated_id) {
                $message = is_wp_error($updated_id) ? $updated_id->get_error_message() : 'missing post_id';
                throw new RuntimeException(land76wp_service_hubs_error('publish_failed', $message));
            }
            if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
                throw new RuntimeException(land76wp_service_hubs_error('publish_lock_lost'));
            }
            $stats['updated']++;
        }
        $verification_errors = array();
        foreach ($plan['operations'] as $operation) {
            if ($operation['kind'] !== 'post') {
                continue;
            }
            if ($operation['action'] === 'reuse_update') {
                $verification_errors = array_merge(
                    $verification_errors,
                    land76wp_service_hubs_verify_reuse_target($operation, 'managed_exact_match')
                );
            }
            $verification_errors = array_merge(
                $verification_errors,
                land76wp_service_hubs_verify_staged_item(
                    $operation,
                    $plan['release_id'],
                    $plan['manifest_sha256'],
                    'publish'
                )
            );
        }
        if ($verification_errors !== array()) {
            throw new RuntimeException(
                land76wp_service_hubs_error('publish_verification_failed', implode('; ', array_values(array_unique($verification_errors))))
            );
        }
        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            throw new RuntimeException(land76wp_service_hubs_error('publish_lock_lost'));
        }
        if ($wpdb->query('COMMIT') === false) {
            throw new RuntimeException(land76wp_service_hubs_error('transaction_commit_failed', (string) $wpdb->last_error));
        }
        $transaction_committed = true;
    } catch (Throwable $error) {
        if ($wpdb->query('ROLLBACK') === false) {
            $stats['errors'][] = land76wp_service_hubs_error('transaction_rollback_failed', (string) $wpdb->last_error);
        }
        $stats['errors'][] = land76wp_service_hubs_error('publish_rollback', $error->getMessage());
        $stats['updated'] = 0;
    }
    if ($transaction_committed) {
        if (!land76wp_service_hubs_owns_release_lock($release_lock)) {
            $stats['errors'][] = land76wp_service_hubs_error('publish_lock_lost');
        } else {
            $stats['rollback_snapshot'][] = land76wp_service_hubs_active_release_snapshot();
            $activation_error = land76wp_service_hubs_activate_verified_release($plan['release_id']);
            if ($activation_error !== '') {
                $stats['errors'][] = $activation_error;
            }
        }
    }

    } finally {
        $lock_released = land76wp_service_hubs_release_release_lock($release_lock);
        $connection_restored = land76wp_service_hubs_restore_wpdb_connection($connection_pin);
        if (!$lock_released) {
            error_log('[land76-service-hubs] Publish lock ownership was lost; release was skipped.');
        }
        if (!$connection_restored) {
            error_log('[land76-service-hubs] Failed to restore wpdb reconnect policy after publish.');
        }
    }

    return $stats;
}

function land76wp_service_hubs_execute_plan(array $plan, $mode)
{
    if (!isset($plan['applicable'], $plan['release_status'], $plan['errors'])
        || !$plan['applicable']
        || $plan['release_status'] !== 'ready'
        || $plan['errors'] !== array()) {
        if (!isset($plan['errors']) || !is_array($plan['errors'])) {
            $plan['errors'] = array();
        }
        $plan['errors'][] = land76wp_service_hubs_error('clean_ready_plan_required');
        return $plan;
    }
    if ($mode === 'stage') {
        return land76wp_service_hubs_execute_stage($plan);
    }
    if ($mode === 'publish') {
        return land76wp_service_hubs_publish_plan($plan);
    }

    $plan['errors'][] = land76wp_service_hubs_error('invalid_mode', (string) $mode);
    return $plan;
}

function land76wp_run_service_hubs_import($json_path = '', $mode = 'preview')
{
    $result = land76wp_service_hubs_empty_result();
    if (!in_array($mode, array('preview', 'stage', 'publish'), true)) {
        $result['errors'][] = land76wp_service_hubs_error('invalid_mode', (string) $mode);
        return $result;
    }
    $json_path = $json_path !== '' ? $json_path : land76wp_service_hubs_default_json_path();
    if (!is_readable($json_path) || !is_file($json_path)) {
        $result['errors'][] = land76wp_service_hubs_error('payload_unreadable', $json_path);
        return $result;
    }
    $raw = file_get_contents($json_path);
    if (!is_string($raw)) {
        $result['errors'][] = land76wp_service_hubs_error('payload_unreadable', $json_path);
        return $result;
    }
    $payload = json_decode($raw, true);
    if (!is_array($payload) || json_last_error() !== JSON_ERROR_NONE) {
        $result['errors'][] = land76wp_service_hubs_error('payload_json_invalid', json_last_error_msg());
        return $result;
    }

    $release_manifest_path = land76wp_service_hubs_default_release_manifest_path();
    if (!is_readable($release_manifest_path) || !is_file($release_manifest_path)) {
        $result['errors'][] = land76wp_service_hubs_error('manifest_unreadable', $release_manifest_path);
        return $result;
    }
    $release_manifest_raw = file_get_contents($release_manifest_path);
    if (!is_string($release_manifest_raw)) {
        $result['errors'][] = land76wp_service_hubs_error('manifest_unreadable', $release_manifest_path);
        return $result;
    }
    $release_manifest = json_decode($release_manifest_raw, true);
    if (!is_array($release_manifest) || json_last_error() !== JSON_ERROR_NONE) {
        $result['errors'][] = land76wp_service_hubs_error('manifest_json_invalid', json_last_error_msg());
        return $result;
    }
    $manifest_source_sha256 = hash('sha256', $release_manifest_raw);
    $manifest_errors = land76wp_service_hubs_validate_manifest_binding(
        $payload,
        $release_manifest,
        $manifest_source_sha256
    );
    if ($manifest_errors !== array()) {
        $result['errors'] = $manifest_errors;
        $result['source_sha256'] = hash('sha256', $raw);
        $result['manifest_source_sha256'] = $manifest_source_sha256;
        return $result;
    }

    $plan = land76wp_service_hubs_build_plan($payload);
    $plan['json_path'] = $json_path;
    $plan['source_sha256'] = hash('sha256', $raw);
    $plan['release_manifest_path'] = $release_manifest_path;
    $plan['manifest_source_sha256'] = $manifest_source_sha256;
    if ($mode === 'preview') {
        return $plan;
    }
    if ($payload['release_status'] !== 'ready') {
        $plan['errors'][] = land76wp_service_hubs_error('draft_release_apply_forbidden');
        return $plan;
    }
    if (!$plan['applicable'] || $plan['errors'] !== array()) {
        return $plan;
    }

    return land76wp_service_hubs_execute_plan($plan, $mode);
}

function land76wp_service_hubs_register_tools_page()
{
    add_management_page(
        'Service hubs release',
        'Service hubs release',
        'manage_options',
        'land76-service-hubs-release',
        'land76wp_service_hubs_render_tools_page'
    );
}
add_action('admin_menu', 'land76wp_service_hubs_register_tools_page');

function land76wp_service_hubs_render_tools_page()
{
    if (!current_user_can('manage_options')) {
        wp_die(esc_html__('You are not allowed to run this importer.', 'land76wp'));
    }

    $json_path = land76wp_service_hubs_default_json_path();
    $result = null;
    $requested_mode = 'preview';
    if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'POST') {
        check_admin_referer('land76_service_hubs_release', 'land76_service_hubs_nonce');
        $requested_mode = isset($_POST['land76_mode']) ? sanitize_key(wp_unslash($_POST['land76_mode'])) : 'preview';
        if (!in_array($requested_mode, array('preview', 'stage', 'publish'), true)) {
            $requested_mode = 'preview';
        }

        $preview = land76wp_run_service_hubs_import($json_path, 'preview');
        $result = $preview;
        if ($requested_mode !== 'preview') {
            $confirmation_release_id = isset($_POST['confirmation_release_id'])
                ? sanitize_text_field(wp_unslash($_POST['confirmation_release_id']))
                : '';
            $source_before = is_readable($json_path) ? hash_file('sha256', $json_path) : '';
            $source_before = is_string($source_before) ? $source_before : '';
            $manifest_path = land76wp_service_hubs_default_release_manifest_path();
            $manifest_before = is_readable($manifest_path) ? hash_file('sha256', $manifest_path) : '';
            $manifest_before = is_string($manifest_before) ? $manifest_before : '';
            if (!hash_equals(land76wp_service_hubs_expected_release_id(), $confirmation_release_id)) {
                $result['errors'][] = land76wp_service_hubs_error('release_confirmation_mismatch');
            } elseif (!$preview['applicable'] || $preview['errors'] !== array()) {
                $result['errors'][] = land76wp_service_hubs_error('clean_preview_required');
            } elseif (!hash_equals($preview['source_sha256'], $source_before)) {
                $result['errors'][] = land76wp_service_hubs_error('payload_changed_after_preview');
            } elseif (!isset($preview['manifest_source_sha256'])
                || !hash_equals($preview['manifest_source_sha256'], $manifest_before)) {
                $result['errors'][] = land76wp_service_hubs_error('manifest_changed_after_preview');
            } else {
                $result = land76wp_service_hubs_execute_plan($preview, $requested_mode);
            }
        }
    }
    ?>
    <div class="wrap">
        <h1><?php echo esc_html__('Service hubs release', 'land76wp'); ?></h1>
        <p><?php echo esc_html__('Preview is read-only. Stage creates owned drafts. Publish changes only verified draft statuses.', 'land76wp'); ?></p>
        <form method="post">
            <?php wp_nonce_field('land76_service_hubs_release', 'land76_service_hubs_nonce'); ?>
            <p>
                <label for="land76-confirm-release"><?php echo esc_html__('Type the release ID before stage or publish:', 'land76wp'); ?></label><br>
                <input id="land76-confirm-release" name="confirmation_release_id" type="text" autocomplete="off" class="regular-text">
            </p>
            <p>
                <button class="button" type="submit" name="land76_mode" value="preview"><?php echo esc_html__('Preview', 'land76wp'); ?></button>
                <button class="button" type="submit" name="land76_mode" value="stage"><?php echo esc_html__('Stage drafts', 'land76wp'); ?></button>
                <button class="button button-primary" type="submit" name="land76_mode" value="publish"><?php echo esc_html__('Publish verified release', 'land76wp'); ?></button>
            </p>
        </form>
        <?php if (is_array($result)) : ?>
            <h2><?php echo esc_html(ucfirst($requested_mode)); ?></h2>
            <pre><?php echo esc_html(wp_json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE)); ?></pre>
        <?php endif; ?>
    </div>
    <?php
}
