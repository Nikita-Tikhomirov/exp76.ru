<?php
/**
 * Production routing and metadata for the fifteen upgraded legacy service pages.
 *
 * The exact WordPress page ID, slug, parent and template must all match before
 * the new version is shown. Any incomplete deployment therefore falls back to
 * the original page instead of rendering a broken or empty page.
 */

if (!defined('ABSPATH')) {
  exit;
}
function land76_service_v2_owners() {
  return array(
    673 => array('slug' => 'landshaftnoe-proektirovanie', 'service_id' => 'S1'),
    6868 => array('slug' => 'gazon-posevnojj-i-gazon-rulonnyjj', 'service_id' => 'S2'),
    6871 => array('slug' => 'posadka-derevev-i-kustarnikov', 'service_id' => 'S3'),
    9357 => array('slug' => 'ukhod-za-sadom', 'service_id' => 'S4'),
    667 => array('slug' => 'planirovka-territorii', 'service_id' => 'S5'),
    676 => array('slug' => 'podpornye-stenki', 'service_id' => 'S6'),
    6918 => array('slug' => 'ulichnoe-osveshhenie-uchastka', 'service_id' => 'S7'),
    9282 => array('slug' => 'vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch', 'service_id' => 'S8'),
    6870 => array('slug' => 'vykorchevyvanie-pnejj-spil-derevev', 'service_id' => 'S9'),
    6900 => array('slug' => 'sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev', 'service_id' => 'S10'),
    6922 => array('slug' => 'sistemy-tumanoobrazovaniya', 'service_id' => 'S11'),
    9138 => array('slug' => 'fundament-na-zhelezobetonnykh-svajakh', 'service_id' => 'S12'),
    9312 => array('slug' => 'navesy-iz-metalla', 'service_id' => 'S13'),
    9775 => array('slug' => 'kaminy-pechi-barbekju', 'service_id' => 'S14'),
    9838 => array('slug' => 'snos-i-demontazh-zdanijj-domov', 'service_id' => 'S15'),
  );
}

function land76_service_v2_content_directory() {
  return get_template_directory() . '/content/service-v2';
}

function land76_service_v2_active_release_option_name() {
  return 'land76_service_hubs_active_release_id';
}

/** Activate schema-v2 hubs only after the importer has verified the same release. */
function land76_service_v2_release_is_active($release_id) {
  if (!is_string($release_id) || $release_id === '') {
    return false;
  }

  $active_release_id = get_option(land76_service_v2_active_release_option_name(), '');
  return is_string($active_release_id)
    && $active_release_id !== ''
    && hash_equals($release_id, $active_release_id);
}

function land76_service_v2_load($page_id) {
  static $cache = array();

  $page_id = (int) $page_id;
  if (array_key_exists($page_id, $cache)) {
    return $cache[$page_id];
  }

  $cache[$page_id] = null;
  $owners = land76_service_v2_owners();
  if (!isset($owners[$page_id])) {
    return null;
  }

  $expected_slug = $owners[$page_id]['slug'];
  $expected_service_id = $owners[$page_id]['service_id'];
  $actual_slug = (string) get_post_field('post_name', $page_id);
  $actual_template = (string) get_page_template_slug($page_id);
  $actual_parent = (int) wp_get_post_parent_id($page_id);
  if ($actual_slug !== $expected_slug || $actual_template !== 'servicepost.php' || $actual_parent !== 921) {
    return null;
  }

  $content_directory = land76_service_v2_content_directory();
  $json_path = $content_directory . '/' . $expected_slug . '.json';
  $rendered_path = $content_directory . '/rendered/' . $expected_slug . '.html';
  $css_path = get_template_directory() . '/css/service-v2.css';
  if (!is_readable($json_path) || !is_readable($rendered_path) || !is_readable($css_path)) {
    return null;
  }

  $json_bytes = file_get_contents($json_path);
  $rendered_html = file_get_contents($rendered_path);
  if ($json_bytes === false || $rendered_html === false || $rendered_html === '') {
    return null;
  }

  $payload = json_decode($json_bytes, true);
  if (!is_array($payload) || json_last_error() !== JSON_ERROR_NONE) {
    return null;
  }

  $expected_canonical = 'https://exp76.ru/services/' . $expected_slug . '/';
  $is_valid_owner = isset(
    $payload['schema_version'],
    $payload['service_id'],
    $payload['page_id'],
    $payload['parent_id'],
    $payload['wp_template'],
    $payload['slug'],
    $payload['canonical'],
    $payload['seo']['title'],
    $payload['seo']['description'],
    $payload['hero']['image']['url']
  )
    && $payload['service_id'] === $expected_service_id
    && (int) $payload['page_id'] === $page_id
    && (int) $payload['parent_id'] === 921
    && $payload['wp_template'] === 'servicepost.php'
    && $payload['slug'] === $expected_slug
    && $payload['canonical'] === $expected_canonical;

  if (!$is_valid_owner) {
    return null;
  }

  $schema_version = (int) $payload['schema_version'];
  if ($schema_version === 1) {
    // A schema-v1 JSON file must never activate a partially deployed v2 fragment.
    $expected_root_prefix = '<div class="service-v2" data-service-id="' . $expected_service_id . '"';
    if (
      strpos($rendered_html, $expected_root_prefix) !== 0
      || strpos($rendered_html, 'data-schema-version="2"') !== false
    ) {
      return null;
    }
  } elseif ($schema_version === 2) {
    $is_valid_hub = isset(
      $payload['service_id'],
      $payload['page_key'],
      $payload['page_type'],
      $payload['release_id'],
      $payload['release_status'],
      $payload['rendered_sha256']
    )
      && $payload['page_key'] === $expected_service_id . '-HUB'
      && $payload['page_type'] === 'hub'
      && is_string($payload['release_id'])
      && land76_service_v2_release_is_active($payload['release_id'])
      && $payload['release_status'] === 'ready'
      && is_string($payload['rendered_sha256'])
      && preg_match('/\A[0-9a-f]{64}\z/D', $payload['rendered_sha256']) === 1;
    if (!$is_valid_hub) {
      return null;
    }

    $expected_root_marker = '<div class="service-v2" data-service-id="' . $expected_service_id . '" data-schema-version="2">';
    if (strpos($rendered_html, $expected_root_marker) !== 0) {
      return null;
    }

    $actual_rendered_sha256 = hash('sha256', $rendered_html);
    if (!hash_equals($payload['rendered_sha256'], $actual_rendered_sha256)) {
      return null;
    }
  } else {
    return null;
  }

  $payload['_rendered_path'] = $rendered_path;
  $payload['_rendered_html'] = $rendered_html;
  $cache[$page_id] = $payload;
  return $payload;
}

function land76_service_v2_current() {
  if (!is_singular('page')) {
    return null;
  }

  return land76_service_v2_load(get_queried_object_id());
}

function land76_service_v2_rendered_path() {
  $service = land76_service_v2_current();
  return $service && !empty($service['_rendered_path']) ? $service['_rendered_path'] : '';
}

function land76_service_v2_meta_value($field, $fallback) {
  $service = land76_service_v2_current();
  return $service && !empty($service['seo'][$field]) ? $service['seo'][$field] : $fallback;
}

function land76_service_v2_filter_title($title) {
  return land76_service_v2_meta_value('title', $title);
}

function land76_service_v2_filter_description($description) {
  return land76_service_v2_meta_value('description', $description);
}

function land76_service_v2_filter_canonical($canonical) {
  $service = land76_service_v2_current();
  return $service && !empty($service['canonical']) ? $service['canonical'] : $canonical;
}

function land76_service_v2_hero_image_url($fallback = '') {
  $service = land76_service_v2_current();
  return $service && !empty($service['hero']['image']['url']) ? $service['hero']['image']['url'] : $fallback;
}

function land76_service_v2_enqueue_assets() {
  $service = land76_service_v2_current();
  if (!$service) {
    return;
  }

  $css_path = get_template_directory() . '/css/service-v2.css';
  if (!is_readable($css_path)) {
    return;
  }

  wp_enqueue_style(
    'land76-service-v2',
    get_template_directory_uri() . '/css/service-v2.css',
    array('style2'),
    filemtime($css_path)
  );
}

function land76_service_v2_print_fallback_meta() {
  $service = land76_service_v2_current();
  if (!$service || defined('AIOSEO_VERSION') || function_exists('aioseo')) {
    return;
  }

  echo '<meta name="description" content="' . esc_attr($service['seo']['description']) . '">' . "\n";
  echo '<link rel="canonical" href="' . esc_url($service['canonical']) . '">' . "\n";
}

add_action('wp_enqueue_scripts', 'land76_service_v2_enqueue_assets', 20);
add_action('wp_head', 'land76_service_v2_print_fallback_meta', 1);
add_filter('aioseo_title', 'land76_service_v2_filter_title', 999);
add_filter('aioseo_description', 'land76_service_v2_filter_description', 999);
add_filter('aioseo_canonical_url', 'land76_service_v2_filter_canonical', 999);
add_filter('wpseo_title', 'land76_service_v2_filter_title', 999);
add_filter('wpseo_metadesc', 'land76_service_v2_filter_description', 999);
add_filter('wpseo_canonical', 'land76_service_v2_filter_canonical', 999);
add_filter('pre_get_document_title', 'land76_service_v2_filter_title', 999);
add_filter('get_canonical_url', 'land76_service_v2_filter_canonical', 999);
