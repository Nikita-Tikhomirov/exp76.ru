<?php

function land76wp_hidden_public_category_ids() {
  return array(74);
}

function land76wp_rebuilt_service_category_ids() {
  return array(87, 88, 89, 90, 91, 92);
}

function land76wp_is_hidden_public_category_archive() {
  return is_category(land76wp_hidden_public_category_ids());
}

function land76wp_render_hidden_category_404() {
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
}

add_filter('redirect_canonical', function ($redirect_url) {
  return land76wp_is_hidden_public_category_archive() ? false : $redirect_url;
}, 10, 1);

add_action('template_redirect', function () {
  if (land76wp_is_hidden_public_category_archive()) {
    land76wp_render_hidden_category_404();
  }
}, 0);

add_filter('wp_robots', function ($robots) {
  if (land76wp_is_hidden_public_category_archive()) {
    $robots['noindex'] = true;
    $robots['nofollow'] = true;
  }

  return $robots;
});

function land76wp_exclude_hidden_categories_from_terms($args, $taxonomies) {
  if (is_admin() || !in_array('category', (array) $taxonomies, true)) {
    return $args;
  }

  $hidden_ids = land76wp_hidden_public_category_ids();
  $existing_exclude = isset($args['exclude']) ? (array) $args['exclude'] : array();
  $args['exclude'] = array_values(array_unique(array_merge($existing_exclude, $hidden_ids)));

  return $args;
}

add_filter('get_terms_args', 'land76wp_exclude_hidden_categories_from_terms', 10, 2);

function land76wp_exclude_hidden_categories_from_widget($args) {
  $hidden_ids = land76wp_hidden_public_category_ids();
  $existing_exclude = isset($args['exclude']) ? explode(',', (string) $args['exclude']) : array();
  $args['exclude'] = implode(',', array_values(array_unique(array_filter(array_merge($existing_exclude, $hidden_ids)))));

  return $args;
}

add_filter('widget_categories_args', 'land76wp_exclude_hidden_categories_from_widget');
add_filter('widget_categories_dropdown_args', 'land76wp_exclude_hidden_categories_from_widget');

function land76wp_post_is_hidden_legacy_service($post_id) {
  $category_ids = wp_get_post_categories((int) $post_id);
  if (!$category_ids) {
    return false;
  }

  $has_hidden_category = (bool) array_intersect($category_ids, land76wp_hidden_public_category_ids());
  $has_rebuilt_category = (bool) array_intersect($category_ids, land76wp_rebuilt_service_category_ids());

  return $has_hidden_category && !$has_rebuilt_category;
}

add_filter('the_posts', function ($posts, $query) {
  if (is_admin() || !$query->is_main_query() || !$query->is_search()) {
    return $posts;
  }

  return array_values(array_filter($posts, function ($post) {
    return !land76wp_post_is_hidden_legacy_service($post->ID);
  }));
}, 10, 2);
