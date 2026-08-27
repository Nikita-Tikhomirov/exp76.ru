<?php
/** Serve complete legal documents at the URLs used by every contact form. */

if (!defined('ABSPATH')) {
  exit;
}

function land76_legal_pages() {
  return array(
    'privacy' => array(
      'title' => 'Политика конфиденциальности — Компания «Эксперты»',
      'description' => 'Политика обработки и защиты персональных данных пользователей сайта exp76.ru.',
    ),
    'consent' => array(
      'title' => 'Согласие на обработку персональных данных — Компания «Эксперты»',
      'description' => 'Условия согласия на обработку персональных данных, передаваемых через формы сайта exp76.ru.',
    ),
  );
}

function land76_legal_page_request_slug() {
  if (is_admin() || empty($_SERVER['REQUEST_URI'])) {
    return '';
  }

  $path = trim((string) wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']), PHP_URL_PATH), '/');
  $home_path = trim((string) wp_parse_url(home_url('/'), PHP_URL_PATH), '/');
  if ($home_path !== '' && strpos($path, $home_path . '/') === 0) {
    $path = substr($path, strlen($home_path) + 1);
  }

  $pages = land76_legal_pages();
  return isset($pages[$path]) ? $path : '';
}

function land76_legacy_legal_page_request_slug() {
  if (is_admin() || empty($_SERVER['REQUEST_URI'])) {
    return '';
  }

  $path = (string) wp_parse_url(wp_unslash($_SERVER['REQUEST_URI']), PHP_URL_PATH);
  $legacy_pages = array(
    'privacy.html' => 'privacy',
    'consent.html' => 'consent',
  );
  $filename = basename($path);
  return isset($legacy_pages[$filename]) ? $legacy_pages[$filename] : '';
}

function land76_redirect_legacy_legal_page() {
  $slug = land76_legacy_legal_page_request_slug();
  if (!$slug) {
    return;
  }

  wp_safe_redirect(home_url('/' . $slug . '/'), 301, 'land76');
  exit;
}

function land76_legal_page_config() {
  $slug = land76_legal_page_request_slug();
  $pages = land76_legal_pages();
  return $slug && isset($pages[$slug]) ? $pages[$slug] : null;
}

function land76_legal_page_current_url($fallback = '') {
  $slug = land76_legal_page_request_slug();
  return $slug ? home_url('/' . $slug . '/') : $fallback;
}

function land76_legal_page_filter_title($title) {
  $config = land76_legal_page_config();
  return $config ? $config['title'] : $title;
}

function land76_legal_page_filter_description($description) {
  $config = land76_legal_page_config();
  return $config ? $config['description'] : $description;
}

function land76_legal_page_filter_canonical($canonical) {
  return land76_legal_page_current_url($canonical);
}

function land76_legal_page_filter_robots($robots) {
  if (!land76_legal_page_request_slug()) {
    return $robots;
  }

  $robots['noindex'] = true;
  $robots['follow'] = true;
  unset($robots['index'], $robots['nofollow']);
  return $robots;
}

function land76_legal_page_disable_aioseo_schema($disabled) {
  return land76_legal_page_request_slug() ? true : $disabled;
}

function land76_legal_page_enqueue_assets() {
  if (!land76_legal_page_request_slug()) {
    return;
  }

  $path = get_template_directory() . '/css/legal-pages.css';
  if (is_readable($path)) {
    wp_enqueue_style(
      'land76-legal-pages',
      get_template_directory_uri() . '/css/legal-pages.css',
      array('style2'),
      filemtime($path)
    );
  }
}

function land76_legal_page_print_fallback_meta() {
  $config = land76_legal_page_config();
  if (!$config || defined('AIOSEO_VERSION') || function_exists('aioseo')) {
    return;
  }

  echo '<meta name="description" content="' . esc_attr($config['description']) . '">' . "\n";
  echo '<meta name="robots" content="noindex,follow">' . "\n";
  echo '<link rel="canonical" href="' . esc_url(land76_legal_page_current_url()) . '">' . "\n";
}

function land76_render_legal_page() {
  $land76_legal_slug = land76_legal_page_request_slug();
  if (!$land76_legal_slug) {
    return;
  }

  global $wp_query;
  if ($wp_query) {
    $wp_query->is_404 = false;
    $wp_query->is_page = true;
    $wp_query->is_singular = true;
  }

  status_header(200);
  get_header('page');
  require get_template_directory() . '/inc/legal-page-template.php';
  echo '</main></div>';
  get_footer();
  exit;
}

add_action('wp_enqueue_scripts', 'land76_legal_page_enqueue_assets', 20);
add_action('wp_head', 'land76_legal_page_print_fallback_meta', 1);
add_action('template_redirect', 'land76_redirect_legacy_legal_page', 0);
add_action('template_redirect', 'land76_render_legal_page', 1);
add_filter('aioseo_title', 'land76_legal_page_filter_title', 999);
add_filter('aioseo_description', 'land76_legal_page_filter_description', 999);
add_filter('aioseo_canonical_url', 'land76_legal_page_filter_canonical', 999);
add_filter('pre_get_document_title', 'land76_legal_page_filter_title', 999);
add_filter('get_canonical_url', 'land76_legal_page_filter_canonical', 999);
add_filter('wp_robots', 'land76_legal_page_filter_robots', 999);
add_filter('aioseo_schema_disable', 'land76_legal_page_disable_aioseo_schema', 999);
