<?php
/**
 * Production routing and metadata for the eight upgraded legacy service pages.
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
    673 => 'landshaftnoe-proektirovanie',
    6868 => 'gazon-posevnojj-i-gazon-rulonnyjj',
    6871 => 'posadka-derevev-i-kustarnikov',
    9357 => 'ukhod-za-sadom',
    667 => 'planirovka-territorii',
    676 => 'podpornye-stenki',
    6918 => 'ulichnoe-osveshhenie-uchastka',
    9282 => 'vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch',
  );
}

function land76_service_v2_content_directory() {
  return get_template_directory() . '/content/service-v2';
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

  $expected_slug = $owners[$page_id];
  $actual_slug = (string) get_post_field('post_name', $page_id);
  $actual_template = (string) get_page_template_slug($page_id);
  $actual_parent = (int) wp_get_post_parent_id($page_id);
  if ($actual_slug !== $expected_slug || $actual_template !== 'servicepost.php' || $actual_parent !== 921) {
    return null;
  }

  $content_directory = land76_service_v2_content_directory();
  $json_path = $content_directory . '/' . $expected_slug . '.json';
  $rendered_path = $content_directory . '/rendered/' . $expected_slug . '.html';
  if (!is_readable($json_path) || !is_readable($rendered_path)) {
    return null;
  }

  $payload = json_decode(file_get_contents($json_path), true);
  if (!is_array($payload)) {
    return null;
  }

  $expected_canonical = 'https://exp76.ru/services/' . $expected_slug . '/';
  $is_valid = isset(
    $payload['schema_version'],
    $payload['page_id'],
    $payload['parent_id'],
    $payload['wp_template'],
    $payload['slug'],
    $payload['canonical'],
    $payload['seo']['title'],
    $payload['seo']['description'],
    $payload['hero']['image']['url']
  )
    && (int) $payload['schema_version'] === 1
    && (int) $payload['page_id'] === $page_id
    && (int) $payload['parent_id'] === 921
    && $payload['wp_template'] === 'servicepost.php'
    && $payload['slug'] === $expected_slug
    && $payload['canonical'] === $expected_canonical;

  if (!$is_valid) {
    return null;
  }

  $payload['_rendered_path'] = $rendered_path;
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
  if (!land76_service_v2_current()) {
    return;
  }

  $path = get_template_directory() . '/css/service-v2.css';
  if (!is_readable($path)) {
    return;
  }

  wp_enqueue_style(
    'land76-service-v2',
    get_template_directory_uri() . '/css/service-v2.css',
    array('style2'),
    filemtime($path)
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
