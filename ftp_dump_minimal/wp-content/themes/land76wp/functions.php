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

$land76_regional_drenazh_file = __DIR__ . '/inc/regional-drenazh.php';
if (file_exists($land76_regional_drenazh_file)) {
  require_once $land76_regional_drenazh_file;
}


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
