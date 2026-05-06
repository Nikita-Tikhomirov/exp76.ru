<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_drenazh_blog_import_default_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/drenazh-blog-import.json';
}

function land76wp_drenazh_blog_import_default_acf_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/acf-seo-blog-post-fields.json';
}

function land76wp_drenazh_blog_import_update_acf_fields(array $fields, $context, array &$stats)
{
    if (!function_exists('update_field')) {
        $stats['errors'][] = 'ACF function update_field() is not available.';
        return;
    }

    foreach ($fields as $field_name => $field_value) {
        if ($field_name === 'blogseo_related_service_slugs') {
            continue;
        }
        update_field($field_name, $field_value, $context);
    }
}

function land76wp_drenazh_blog_import_update_acf_field_recursive(array $field, $parent = 0)
{
    if (!function_exists('acf_update_field')) {
        return;
    }

    $sub_fields = array();
    if (!empty($field['sub_fields']) && is_array($field['sub_fields'])) {
        $sub_fields = $field['sub_fields'];
        unset($field['sub_fields']);
    }

    $field['parent'] = $parent;
    acf_update_field($field);

    foreach ($sub_fields as $sub_field) {
        if (is_array($sub_field)) {
            land76wp_drenazh_blog_import_update_acf_field_recursive($sub_field, $field['key']);
        }
    }
}

function land76wp_drenazh_blog_import_acf_group($json_path, array &$stats)
{
    if (!function_exists('acf_update_field_group') || !function_exists('acf_update_field')) {
        $stats['errors'][] = 'ACF import functions are not available.';
        return;
    }

    if (!file_exists($json_path)) {
        $stats['errors'][] = 'ACF JSON file not found: ' . $json_path;
        return;
    }

    $json_raw = file_get_contents($json_path);
    $groups = json_decode($json_raw, true);
    if (!is_array($groups)) {
        $stats['errors'][] = 'Invalid ACF JSON payload.';
        return;
    }

    foreach ($groups as $group) {
        if (empty($group['key']) || empty($group['fields']) || !is_array($group['fields'])) {
            $stats['errors'][] = 'Skipped invalid ACF field group.';
            continue;
        }

        $fields = $group['fields'];
        unset($group['fields']);

        $existing_group = function_exists('acf_get_field_group') ? acf_get_field_group($group['key']) : false;
        if (!empty($existing_group['ID'])) {
            $group['ID'] = $existing_group['ID'];
        }

        acf_update_field_group($group);
        foreach ($fields as $field) {
            if (is_array($field)) {
                land76wp_drenazh_blog_import_update_acf_field_recursive($field, $group['key']);
            }
        }
        $stats['acf_groups_imported']++;
    }
}

function land76wp_drenazh_blog_import_resolve_related_services(array $slugs)
{
    $related_ids = array();
    foreach ($slugs as $slug) {
        $post = get_page_by_path(sanitize_title($slug), 'OBJECT', 'post');
        if ($post instanceof WP_Post) {
            $related_ids[] = $post->ID;
        }
    }
    return $related_ids;
}

function land76wp_drenazh_blog_import_set_featured_image($post_id, $image_url, array &$stats)
{
    if (empty($image_url) || !function_exists('attachment_url_to_postid')) {
        return;
    }

    $attachment_id = attachment_url_to_postid($image_url);
    if ($attachment_id) {
        set_post_thumbnail($post_id, $attachment_id);
        $stats['featured_images_set']++;
    }
}

function land76wp_drenazh_blog_import_upsert_post(array $post_payload, array &$stats)
{
    $slug = isset($post_payload['slug']) ? sanitize_title($post_payload['slug']) : '';
    if ($slug === '') {
        $stats['errors'][] = 'Skipped post with empty slug.';
        return;
    }

    $existing = get_page_by_path($slug, 'OBJECT', 'post');
    $post_data = array(
        'post_type' => 'post',
        'post_status' => 'publish',
        'post_name' => $slug,
        'post_title' => isset($post_payload['post_title']) ? wp_strip_all_tags($post_payload['post_title']) : $slug,
        'post_content' => isset($post_payload['post_content']) ? $post_payload['post_content'] : '',
        'post_excerpt' => isset($post_payload['post_excerpt']) ? $post_payload['post_excerpt'] : '',
        'menu_order' => isset($post_payload['menu_order']) ? (int) $post_payload['menu_order'] : 0,
    );

    if ($existing instanceof WP_Post) {
        $post_data['ID'] = $existing->ID;
        $post_id = wp_update_post(wp_slash($post_data), true);
        if (is_wp_error($post_id)) {
            $stats['errors'][] = 'Failed to update blog post ' . $slug . ': ' . $post_id->get_error_message();
            return;
        }
        $stats['posts_updated']++;
    } else {
        $post_id = wp_insert_post(wp_slash($post_data), true);
        if (is_wp_error($post_id)) {
            $stats['errors'][] = 'Failed to create blog post ' . $slug . ': ' . $post_id->get_error_message();
            return;
        }
        $stats['posts_created']++;
    }

    $categories = !empty($post_payload['categories']) && is_array($post_payload['categories'])
        ? array_map('intval', $post_payload['categories'])
        : array(87, 72);
    wp_set_post_categories($post_id, $categories, false);

    $acf_fields = !empty($post_payload['acf']) && is_array($post_payload['acf']) ? $post_payload['acf'] : array();
    if (!empty($acf_fields['blogseo_related_service_slugs']) && is_array($acf_fields['blogseo_related_service_slugs'])) {
        $acf_fields['blogseo_related_services'] = land76wp_drenazh_blog_import_resolve_related_services($acf_fields['blogseo_related_service_slugs']);
    }

    land76wp_drenazh_blog_import_update_acf_fields($acf_fields, $post_id, $stats);

    if (!empty($post_payload['featured_image_url'])) {
        land76wp_drenazh_blog_import_set_featured_image($post_id, $post_payload['featured_image_url'], $stats);
    }
}

function land76wp_run_drenazh_blog_import($json_path = '', $acf_json_path = '')
{
    $stats = array(
        'json_path' => '',
        'acf_json_path' => '',
        'acf_groups_imported' => 0,
        'posts_created' => 0,
        'posts_updated' => 0,
        'featured_images_set' => 0,
        'errors' => array(),
    );

    $json_path = $json_path ? $json_path : land76wp_drenazh_blog_import_default_json_path();
    $acf_json_path = $acf_json_path ? $acf_json_path : land76wp_drenazh_blog_import_default_acf_json_path();
    $stats['json_path'] = $json_path;
    $stats['acf_json_path'] = $acf_json_path;

    if (!function_exists('update_field')) {
        $stats['errors'][] = 'ACF plugin is required: update_field() is unavailable.';
        return $stats;
    }

    land76wp_drenazh_blog_import_acf_group($acf_json_path, $stats);

    if (!file_exists($json_path)) {
        $stats['errors'][] = 'JSON file not found: ' . $json_path;
        return $stats;
    }

    $json_raw = file_get_contents($json_path);
    if ($json_raw === false) {
        $stats['errors'][] = 'Could not read JSON file: ' . $json_path;
        return $stats;
    }

    $payload = json_decode($json_raw, true);
    if (!is_array($payload)) {
        $stats['errors'][] = 'Invalid JSON payload.';
        return $stats;
    }

    if (!empty($payload['posts']) && is_array($payload['posts'])) {
        foreach ($payload['posts'] as $post_payload) {
            if (!is_array($post_payload)) {
                $stats['errors'][] = 'Skipped invalid post payload (not an object).';
                continue;
            }
            land76wp_drenazh_blog_import_upsert_post($post_payload, $stats);
        }
    }

    return $stats;
}
