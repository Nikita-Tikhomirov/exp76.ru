<?php
add_action( 'wp_enqueue_scripts', 'style_theme' );
add_action( 'wp_footer', 'scripts_theme' );

$land76_import_file = __DIR__ . '/inc/import-drenazh.php';
if (file_exists($land76_import_file)) {
  require_once $land76_import_file;
}

$land76_drenazh_blog_import_file = __DIR__ . '/inc/import-drenazh-blog.php';
if (file_exists($land76_drenazh_blog_import_file)) {
  require_once $land76_drenazh_blog_import_file;
}

$land76_otmostka_import_file = __DIR__ . '/inc/import-otmostka.php';
if (file_exists($land76_otmostka_import_file)) {
  require_once $land76_otmostka_import_file;
}

$land76_otmostka_blog_import_file = __DIR__ . '/inc/import-otmostka-blog.php';
if (file_exists($land76_otmostka_blog_import_file)) {
  require_once $land76_otmostka_blog_import_file;
}

$land76_plitka_import_file = __DIR__ . '/inc/import-plitka.php';
if (file_exists($land76_plitka_import_file)) {
  require_once $land76_plitka_import_file;
}

$land76_plitka_blog_import_file = __DIR__ . '/inc/import-plitka-blog.php';
if (file_exists($land76_plitka_blog_import_file)) {
  require_once $land76_plitka_blog_import_file;
}

$land76_osushenie_import_file = __DIR__ . '/inc/import-osushenie.php';
if (file_exists($land76_osushenie_import_file)) {
  require_once $land76_osushenie_import_file;
}

$land76_osushenie_blog_import_file = __DIR__ . '/inc/import-osushenie-blog.php';
if (file_exists($land76_osushenie_blog_import_file)) {
  require_once $land76_osushenie_blog_import_file;
}

$land76_livnevka_import_file = __DIR__ . '/inc/import-livnevka.php';
if (file_exists($land76_livnevka_import_file)) {
  require_once $land76_livnevka_import_file;
}

$land76_livnevka_blog_import_file = __DIR__ . '/inc/import-livnevka-blog.php';
if (file_exists($land76_livnevka_blog_import_file)) {
  require_once $land76_livnevka_blog_import_file;
}

$land76_autopoliv_import_file = __DIR__ . '/inc/import-autopoliv.php';
if (file_exists($land76_autopoliv_import_file)) {
  require_once $land76_autopoliv_import_file;
}

$land76_autopoliv_blog_import_file = __DIR__ . '/inc/import-autopoliv-blog.php';
if (file_exists($land76_autopoliv_blog_import_file)) {
  require_once $land76_autopoliv_blog_import_file;
}

$land76_case_seo_import_file = __DIR__ . '/inc/import-case-seo.php';
if (file_exists($land76_case_seo_import_file)) {
  require_once $land76_case_seo_import_file;
}

$land76_service_previews_import_file = __DIR__ . '/inc/import-service-previews.php';
if (file_exists($land76_service_previews_import_file)) {
  require_once $land76_service_previews_import_file;
}

$land76_hidden_categories_file = __DIR__ . '/inc/hidden-categories.php';
if (file_exists($land76_hidden_categories_file)) {
  require_once $land76_hidden_categories_file;
}

function land76_region_page_slugs() {
  return array('yaroslavl', 'rybinsk', 'uglich', 'tutaev', 'pereslavl');
}

function land76_regional_service_slugs() {
  return array('drenazh-uchastka', 'ukladka-trotuarnoy-plitki', 'osushenie-uchastka', 'otmostka-vokrug-doma', 'avtopoliv-na-uchastke', 'livnevaya-kanalizatsiya');
}

function land76_is_unknown_regional_service_request() {
  $path = isset($_SERVER['REQUEST_URI']) ? trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/') : '';
  if (!preg_match('#^([^/]+)/([^/]+)/?$#', $path, $matches)) {
    return false;
  }

  if ($matches[1] === 'category') {
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
  if (is_singular('post') && has_category(72, get_queried_object_id())) {
    wp_enqueue_style('land76-services', get_template_directory_uri() . '/css/services.css', array(), null);
    wp_enqueue_style('land76-seoblog', get_template_directory_uri() . '/css/seoblog.css', array('land76-services'), null);
  }

}


function scripts_theme() {

}




add_theme_support( 'post-thumbnails' );

function land76_get_card_image_url($post_id = null, $size = 'medium', $fallback = true) {
  $post_id = $post_id ? (int) $post_id : get_the_ID();

  if ($post_id && has_post_thumbnail($post_id)) {
    $thumbnail_url = get_the_post_thumbnail_url($post_id, $size);
    if ($thumbnail_url) {
      return $thumbnail_url;
    }
  }

  if ($post_id && function_exists('get_field')) {
    $field_names = array(
      'service_card_image',
      'card_image',
      'ns87_card_image',
      'ns87_hero_image',
      'image',
      'blogseo_main_image_url',
    );

    foreach ($field_names as $field_name) {
      $image = get_field($field_name, $post_id);
      if (empty($image)) {
        continue;
      }

      if (is_array($image) && !empty($image['sizes'][$size])) {
        return $image['sizes'][$size];
      }

      if (is_array($image) && !empty($image['url'])) {
        return $image['url'];
      }

      if (is_numeric($image)) {
        $attachment_url = wp_get_attachment_image_url((int) $image, $size);
        if ($attachment_url) {
          return $attachment_url;
        }
      }

      if (is_string($image)) {
        return $image;
      }
    }
  }

  return $fallback ? 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp' : '';
}

function land76_get_card_image_alt($post_id = null, $fallback = '') {
  $post_id = $post_id ? (int) $post_id : get_the_ID();
  $fallback = $fallback ? $fallback : ($post_id ? get_the_title($post_id) : '');

  if (!$post_id) {
    return $fallback;
  }

  $custom_alt = get_post_meta($post_id, '_land76_service_preview_alt', true);
  if ($custom_alt) {
    return $custom_alt;
  }

  $thumbnail_id = get_post_thumbnail_id($post_id);
  if ($thumbnail_id) {
    $attachment_alt = get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true);
    if ($attachment_alt) {
      return $attachment_alt;
    }
  }

  return $fallback;
}

add_filter('aioseo_title', function ($title) {
  if (!is_singular('post') || !in_category(72) || !function_exists('get_field')) {
    return $title;
  }

  $seo_title = get_field('blogseo_seo_title', get_the_ID());
  return $seo_title ? $seo_title : $title;
}, 20, 1);

add_filter('aioseo_description', function ($description) {
  if (!is_singular('post') || !in_category(72) || !function_exists('get_field')) {
    return $description;
  }

  $seo_description = get_field('blogseo_seo_description', get_the_ID());
  return $seo_description ? $seo_description : $description;
}, 20, 1);

function land76_is_case_seo_template() {
  return is_page_template('casenew.php') && function_exists('get_field');
}

add_filter('aioseo_title', function ($title) {
  if (!land76_is_case_seo_template()) {
    return $title;
  }

  $seo_title = get_field('cs87_seo_title', get_the_ID());
  return $seo_title ? $seo_title : $title;
}, 20, 1);

add_filter('aioseo_description', function ($description) {
  if (!land76_is_case_seo_template()) {
    return $description;
  }

  $seo_description = get_field('cs87_seo_description', get_the_ID());
  return $seo_description ? $seo_description : $description;
}, 20, 1);



if ( function_exists('acf_add_options_page') ) {

  acf_add_options_page(array(
      'page_title' 	=> 'Настройка темы',
      'menu_title'	=> 'Настройка темы',
      'menu_slug' 	=> 'theme-general-settings',
      'capability'	=> 'edit_posts',
      'redirect'		=> false
    ));
}

// ACF: Секции категорий на главной (repeater на странице Настройка темы)
add_action('acf/init', 'land76_register_home_category_sections_acf');
function land76_register_home_category_sections_acf() {
  if (!function_exists('acf_add_local_field_group')) return;

  acf_add_local_field_group(array(
    'key' => 'group_home_category_sections',
    'title' => 'Секции категорий на главной',
    'fields' => array(
      array(
        'key' => 'field_home_category_sections',
        'label' => 'Секции',
        'name' => 'home_category_sections',
        'type' => 'repeater',
        'layout' => 'block',
        'button_label' => 'Добавить секцию категории',
        'sub_fields' => array(
          array(
            'key' => 'field_home_sec_title',
            'label' => 'Заголовок секции (H2)',
            'name' => 'title',
            'type' => 'text',
          ),
          array(
            'key' => 'field_home_sec_text',
            'label' => 'Текстовый блок',
            'name' => 'text',
            'type' => 'wysiwyg',
            'tabs' => 'visual',
            'media_upload' => 1,
          ),
          array(
            'key' => 'field_home_sec_cat',
            'label' => 'Категория услуг',
            'name' => 'category',
            'type' => 'taxonomy',
            'taxonomy' => 'category',
            'field_type' => 'select',
            'return_format' => 'id',
          ),
        ),
      ),
    ),
    'location' => array(
      array(
        array(
          'param' => 'options_page',
          'operator' => '==',
          'value' => 'theme-general-settings',
        ),
      ),
    ),
    'position' => 'normal',
    'style' => 'default',
    'label_placement' => 'top',
  ));
}
