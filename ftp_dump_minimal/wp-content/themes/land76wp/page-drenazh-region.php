<?php
/*
Template Name: Региональная страница дренажа
*/

if (!defined('ABSPATH')) {
  exit;
}

$land76_region_page_id = get_queried_object_id();
$land76_region_slug = get_post_meta($land76_region_page_id, '_land76_region_slug', true);
$land76_region_name = get_post_meta($land76_region_page_id, '_land76_region_name', true);
$land76_region_locative = get_post_meta($land76_region_page_id, '_land76_region_locative', true);
$land76_region_title = get_post_meta($land76_region_page_id, '_land76_region_title', true);
$land76_region_description = get_post_meta($land76_region_page_id, '_land76_region_description', true);
$land76_region_lead = get_post_meta($land76_region_page_id, '_land76_region_lead', true);

if (!$land76_region_slug) {
  $land76_region_slug = get_post_field('post_name', $land76_region_page_id);
}

$land76_request_path = isset($_SERVER['REQUEST_URI']) ? trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/') : '';
$land76_request_parts = $land76_request_path !== '' ? explode('/', $land76_request_path) : array();
if (!empty($land76_request_parts[0]) && $land76_request_parts[0] !== $land76_region_slug) {
  global $wp_query;
  $wp_query->set_404();
  status_header(404);
  nocache_headers();
  include get_404_template();
  exit;
}

if (!$land76_region_name) {
  $land76_region_name = get_the_title($land76_region_page_id);
}

if (!$land76_region_locative) {
  $land76_region_locative = $land76_region_name;
}

if (!$land76_region_title) {
  $land76_region_title = 'Дренаж участка в ' . $land76_region_locative . ' под ключ — цена и монтаж';
}

if (!$land76_region_description) {
  $land76_region_description = 'Дренаж участка в ' . $land76_region_locative . ' под ключ: обследование, схема отвода воды, смета и монтаж дренажной системы.';
}

if (!$land76_region_lead) {
  $land76_region_lead = 'Проектируем и монтируем дренаж участка в ' . $land76_region_locative . ': убираем воду от дома, дорожек, газона и зоны въезда.';
}

$land76_region_content = trim(get_post_field('post_content', $land76_region_page_id));
if ($land76_region_content !== '') {
  $land76_region_content = apply_filters('the_content', $land76_region_content);
}

$GLOBALS['land76wp_current_drenazh_region_page'] = array(
  'slug' => $land76_region_slug,
  'name' => $land76_region_name,
  'locative' => $land76_region_locative,
  'title' => $land76_region_title,
  'description' => $land76_region_description,
  'lead' => $land76_region_lead,
  'content' => $land76_region_content,
  'text' => array(),
);

if (!function_exists('land76wp_get_current_drenazh_region')) {
  function land76wp_get_current_drenazh_region() {
    return isset($GLOBALS['land76wp_current_drenazh_region_page'])
      ? $GLOBALS['land76wp_current_drenazh_region_page']
      : null;
  }
}

add_filter('aioseo_title', function ($title) use ($land76_region_title) {
  return $land76_region_title ? $land76_region_title : $title;
}, 20);

add_filter('aioseo_description', function ($description) use ($land76_region_description) {
  return $land76_region_description ? $land76_region_description : $description;
}, 20);

add_filter('pre_get_document_title', function ($title) use ($land76_region_title) {
  return $land76_region_title ? $land76_region_title : $title;
}, 20);

require get_template_directory() . '/category-87.php';
