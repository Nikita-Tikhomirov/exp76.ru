<?php
add_action( 'wp_enqueue_scripts', 'style_theme' );
add_action( 'wp_footer', 'scripts_theme' );

$land76_import_file = __DIR__ . '/inc/import-drenazh.php';
if (file_exists($land76_import_file)) {
  require_once $land76_import_file;
}

$land76_otmostka_import_file = __DIR__ . '/inc/import-otmostka.php';
if (file_exists($land76_otmostka_import_file)) {
  require_once $land76_otmostka_import_file;
}

$land76_plitka_import_file = __DIR__ . '/inc/import-plitka.php';
if (file_exists($land76_plitka_import_file)) {
  require_once $land76_plitka_import_file;
}

$land76_osushenie_import_file = __DIR__ . '/inc/import-osushenie.php';
if (file_exists($land76_osushenie_import_file)) {
  require_once $land76_osushenie_import_file;
}

$land76_livnevka_import_file = __DIR__ . '/inc/import-livnevka.php';
if (file_exists($land76_livnevka_import_file)) {
  require_once $land76_livnevka_import_file;
}

$land76_autopoliv_import_file = __DIR__ . '/inc/import-autopoliv.php';
if (file_exists($land76_autopoliv_import_file)) {
  require_once $land76_autopoliv_import_file;
}

function land76_region_page_slugs() {
  return array('yaroslavl', 'rybinsk', 'uglich', 'tutaev', 'pereslavl');
}

function land76_regional_service_slugs() {
  return array('drenazh-uchastka', 'ukladka-trotuarnoy-plitki', 'osushenie-uchastka');
}

function land76_is_unknown_regional_service_request() {
  $path = isset($_SERVER['REQUEST_URI']) ? trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/') : '';
  if (!preg_match('#^([^/]+)/([^/]+)/?$#', $path, $matches)) {
    return false;
  }

  if (!in_array($matches[2], land76_regional_service_slugs(), true)) {
    return false;
  }

  return !in_array($matches[1], land76_region_page_slugs(), true);
}

add_filter('redirect_canonical', function ($redirect_url) {
  return land76_is_unknown_regional_service_request() ? false : $redirect_url;
}, 10, 1);

add_action('template_redirect', function () {
  if (!land76_is_unknown_regional_service_request()) {
    return;
  }

  global $wp_query;
  $wp_query->set_404();
  status_header(404);
  nocache_headers();
  $template = get_404_template();
  if ($template) {
    include $template;
  } else {
    echo '404';
  }
  exit;
}, 0);


function style_theme() {

  // wp_enqueue_style('style1', get_template_directory_uri() . '/css/index.css');
  wp_enqueue_style('style2', get_template_directory_uri() . '/css/styles.css');

}


function scripts_theme() {

}




add_theme_support( 'post-thumbnails' );



if ( function_exists('acf_add_options_page') ) {

  acf_add_options_page(array(
      'page_title' 	=> 'Настройка темы',
      'menu_title'	=> 'Настройка темы',
      'menu_slug' 	=> 'theme-general-settings',
      'capability'	=> 'edit_posts',
      'redirect'		=> false
    ));
}
