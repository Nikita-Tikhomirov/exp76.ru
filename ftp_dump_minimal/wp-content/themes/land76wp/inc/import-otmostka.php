<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_otmostka_import_default_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/otmostka-import.json';
}

function land76wp_otmostka_import_update_acf_fields(array $fields, $context, array &$stats)
{
    if (!function_exists('update_field')) {
        $stats['errors'][] = 'ACF function update_field() is not available.';
        return;
    }

    foreach ($fields as $field_name => $field_value) {
        update_field($field_name, $field_value, $context);
    }
}

function land76wp_otmostka_import_upsert_post(array $post_payload, array &$stats)
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
    );

    if ($existing instanceof WP_Post) {
        $post_data['ID'] = $existing->ID;
        $post_id = wp_update_post(wp_slash($post_data), true);
        if (is_wp_error($post_id)) {
            $stats['errors'][] = 'Failed to update post ' . $slug . ': ' . $post_id->get_error_message();
            return;
        }
        $stats['posts_updated']++;
    } else {
        $post_id = wp_insert_post(wp_slash($post_data), true);
        if (is_wp_error($post_id)) {
            $stats['errors'][] = 'Failed to create post ' . $slug . ': ' . $post_id->get_error_message();
            return;
        }
        $stats['posts_created']++;
    }

    $categories = array(88, 72);
    if (!empty($post_payload['categories']) && is_array($post_payload['categories'])) {
        $categories = array_map('intval', $post_payload['categories']);
    }
    wp_set_post_categories($post_id, $categories, false);

    $acf_fields = array();
    if (!empty($post_payload['acf']) && is_array($post_payload['acf'])) {
        $acf_fields = $post_payload['acf'];
    }
    land76wp_otmostka_import_update_acf_fields($acf_fields, $post_id, $stats);
}

function land76wp_run_otmostka_import($json_path = '')
{
    $stats = array(
        'json_path' => '',
        'category_updated' => false,
        'posts_created' => 0,
        'posts_updated' => 0,
        'errors' => array(),
    );

    $json_path = $json_path ? $json_path : land76wp_otmostka_import_default_json_path();
    $stats['json_path'] = $json_path;

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

    if (!function_exists('update_field')) {
        $stats['errors'][] = 'ACF plugin is required: update_field() is unavailable.';
        return $stats;
    }

    if (!empty($payload['category']) && is_array($payload['category'])) {
        $term_id = !empty($payload['category']['term_id']) ? (int) $payload['category']['term_id'] : 88;
        $term_context = 'category_' . $term_id;
        $term_fields = !empty($payload['category']['acf']) && is_array($payload['category']['acf'])
            ? $payload['category']['acf']
            : array();

        land76wp_otmostka_import_update_acf_fields($term_fields, $term_context, $stats);
        $stats['category_updated'] = true;
    }

    if (!empty($payload['posts']) && is_array($payload['posts'])) {
        foreach ($payload['posts'] as $post_payload) {
            if (!is_array($post_payload)) {
                $stats['errors'][] = 'Skipped invalid post payload (not an object).';
                continue;
            }
            land76wp_otmostka_import_upsert_post($post_payload, $stats);
        }
    }

    return $stats;
}

function land76wp_otmostka_import_maybe_run_from_admin()
{
    if (!is_admin() || !current_user_can('manage_options')) {
        return;
    }

    if (empty($_GET['land76_run_otmostka_import'])) {
        return;
    }

    $result = land76wp_run_otmostka_import();

    wp_die(
        '<h1>Otmostka import result</h1><pre>' .
        esc_html(wp_json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT)) .
        '</pre>'
    );
}
add_action('admin_init', 'land76wp_otmostka_import_maybe_run_from_admin');
