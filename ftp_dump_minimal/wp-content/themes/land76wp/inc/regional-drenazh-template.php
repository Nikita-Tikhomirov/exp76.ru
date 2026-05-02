<?php
if (!defined('ABSPATH')) {
  exit;
}

$region = land76wp_get_current_drenazh_region();
if (!$region) {
  status_header(404);
  get_template_part('404');
  return;
}

require get_template_directory() . '/category-87.php';
