<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_case_seo_import_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/cases-seo-import.json';
}

function land76wp_case_seo_import_acf_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/acf-import-casenew.json';
}

function land76wp_case_seo_import_update_acf_field_recursive(array $field, $parent = 0)
{
    if (!function_exists('acf_update_field') || empty($field['key'])) {
        return 0;
    }

    $sub_fields = array();
    if (!empty($field['sub_fields']) && is_array($field['sub_fields'])) {
        $sub_fields = $field['sub_fields'];
        unset($field['sub_fields']);
    }

    $field['parent'] = $parent;
    $updated_field = acf_update_field($field);
    $field_id = 0;
    if (is_array($updated_field) && !empty($updated_field['ID'])) {
        $field_id = (int) $updated_field['ID'];
    }

    if (!$field_id && function_exists('acf_get_field')) {
        $stored_field = acf_get_field($field['key']);
        if (!empty($stored_field['ID'])) {
            $field_id = (int) $stored_field['ID'];
        }
    }

    foreach ($sub_fields as $sub_field) {
        if (is_array($sub_field)) {
            land76wp_case_seo_import_update_acf_field_recursive($sub_field, $field_id ? $field_id : $field['key']);
        }
    }

    return $field_id;
}

function land76wp_case_seo_import_acf_group($json_path, array &$stats)
{
    if (!function_exists('acf_update_field_group') || !function_exists('acf_update_field')) {
        $stats['errors'][] = 'ACF import functions are not available.';
        return;
    }

    if (!file_exists($json_path)) {
        $stats['errors'][] = 'ACF JSON file not found: ' . $json_path;
        return;
    }

    $groups = json_decode(file_get_contents($json_path), true);
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

        $updated_group = acf_update_field_group($group);
        $group_id = 0;
        if (is_array($updated_group) && !empty($updated_group['ID'])) {
            $group_id = (int) $updated_group['ID'];
        }
        if (!$group_id && function_exists('acf_get_field_group')) {
            $stored_group = acf_get_field_group($group['key']);
            if (!empty($stored_group['ID'])) {
                $group_id = (int) $stored_group['ID'];
            }
        }

        foreach ($fields as $field) {
            if (is_array($field)) {
                land76wp_case_seo_import_update_acf_field_recursive($field, $group_id ? $group_id : $group['key']);
            }
        }

        $stats['acf_groups_imported']++;
    }
}

function land76wp_case_seo_import_resolve_post_id($url_or_path)
{
    $value = trim((string) $url_or_path);
    if ($value === '') {
        return 0;
    }

    $post_id = url_to_postid($value);
    if ($post_id) {
        return (int) $post_id;
    }

    $path = wp_parse_url($value, PHP_URL_PATH);
    $path = $path ? trim($path, '/') : trim($value, '/');
    if ($path === '') {
        return 0;
    }

    $post_id = url_to_postid(home_url('/' . $path . '/'));
    if ($post_id) {
        return (int) $post_id;
    }

    $post = get_page_by_path($path, OBJECT, array('page', 'post'));
    return $post instanceof WP_Post ? (int) $post->ID : 0;
}

function land76wp_case_seo_import_field_keys()
{
    return array(
        'cs87_hero_title' => 'field_cs87_hero_title',
        'cs87_hero_subtitle' => 'field_cs87_hero_subtitle',
        'cs87_hero_btn_primary_text' => 'field_cs87_hero_btn_primary_text',
        'cs87_hero_btn_primary_url' => 'field_cs87_hero_btn_primary_url',
        'cs87_hero_btn_secondary_text' => 'field_cs87_hero_btn_secondary_text',
        'cs87_hero_btn_secondary_url' => 'field_cs87_hero_btn_secondary_url',
        'cs87_location' => 'field_cs87_location',
        'cs87_work_type' => 'field_cs87_work_type',
        'cs87_area' => 'field_cs87_area',
        'cs87_timeline' => 'field_cs87_timeline',
        'cs87_budget' => 'field_cs87_budget',
        'cs87_intro_title' => 'field_cs87_intro_title',
        'cs87_intro_text' => 'field_cs87_intro_text',
        'cs87_technology_title' => 'field_cs87_technology_title',
        'cs87_technology_text' => 'field_cs87_technology_text',
        'cs87_result_title' => 'field_cs87_result_title',
        'cs87_result_text' => 'field_cs87_result_text',
        'cs87_scope_title' => 'field_cs87_scope_title',
        'cs87_scope_items' => 'field_cs87_scope_items',
        'cs87_price_note' => 'field_cs87_price_note',
        'cs87_challenge_title' => 'field_cs87_challenge_title',
        'cs87_challenge_text' => 'field_cs87_challenge_text',
        'cs87_solution_title' => 'field_cs87_solution_title',
        'cs87_solution_text' => 'field_cs87_solution_text',
        'cs87_related_cases' => 'field_cs87_related_cases',
        'cs87_related_case_urls' => 'field_cs87_related_case_urls',
        'cs87_faq_title' => 'field_cs87_faq_title',
        'cs87_faq_items' => 'field_cs87_faq_items',
        'cs87_seo_title' => 'field_cs87_seo_title',
        'cs87_seo_description' => 'field_cs87_seo_description',
        'cs87_case_keywords' => 'field_cs87_case_keywords',
        'cs87_service_url' => 'field_cs87_service_url',
    );
}

function land76wp_case_seo_import_update_fields($post_id, array $fields, array &$stats)
{
    if (!function_exists('update_field')) {
        $stats['errors'][] = 'ACF function update_field() is not available.';
        return;
    }

    $field_keys = land76wp_case_seo_import_field_keys();

    if (!empty($fields['cs87_related_case_urls']) && is_array($fields['cs87_related_case_urls'])) {
        $related_ids = array();
        foreach ($fields['cs87_related_case_urls'] as $related_url) {
            $related_id = land76wp_case_seo_import_resolve_post_id($related_url);
            if ($related_id) {
                $related_ids[] = $related_id;
            }
        }
        $fields['cs87_related_cases'] = array_values(array_unique($related_ids));
        $fields['cs87_related_case_urls'] = implode("\n", $fields['cs87_related_case_urls']);
    }

    foreach ($fields as $field_name => $field_value) {
        $field_key = isset($field_keys[$field_name]) ? $field_keys[$field_name] : $field_name;
        update_field($field_key, $field_value, $post_id);
    }
}

function land76wp_case_seo_import_update_category_case_maps(array $maps, array &$stats)
{
    if (!function_exists('update_field')) {
        return;
    }

    foreach ($maps as $map_key => $map) {
        if (empty($map['acf_context']) || empty($map['acf_field']) || empty($map['cases']) || !is_array($map['cases'])) {
            continue;
        }

        $case_ids = array();
        foreach ($map['cases'] as $case) {
            if (empty($case['url'])) {
                continue;
            }
            $case_id = land76wp_case_seo_import_resolve_post_id($case['url']);
            if ($case_id) {
                $case_ids[] = $case_id;
            } else {
                $stats['unresolved_category_cases'][] = $map_key . ': ' . $case['url'];
            }
        }

        $case_ids = array_values(array_unique($case_ids));
        update_field($map['acf_field'], $case_ids, $map['acf_context']);
        $stats['category_maps_updated'][$map_key] = count($case_ids);
    }
}

function land76wp_run_case_seo_import($json_path = '', $acf_json_path = '')
{
    $stats = array(
        'json_path' => '',
        'acf_json_path' => '',
        'acf_groups_imported' => 0,
        'cases_updated' => 0,
        'templates_updated' => 0,
        'category_maps_updated' => array(),
        'unresolved_cases' => array(),
        'unresolved_category_cases' => array(),
        'errors' => array(),
    );

    $json_path = $json_path ? $json_path : land76wp_case_seo_import_json_path();
    $acf_json_path = $acf_json_path ? $acf_json_path : land76wp_case_seo_import_acf_json_path();
    $stats['json_path'] = $json_path;
    $stats['acf_json_path'] = $acf_json_path;

    if (!file_exists($json_path)) {
        $stats['errors'][] = 'Case SEO JSON file not found: ' . $json_path;
        return $stats;
    }

    $payload = json_decode(file_get_contents($json_path), true);
    if (!is_array($payload) || empty($payload['cases']) || !is_array($payload['cases'])) {
        $stats['errors'][] = 'Invalid case SEO JSON payload.';
        return $stats;
    }

    land76wp_case_seo_import_acf_group($acf_json_path, $stats);

    foreach ($payload['cases'] as $case) {
        $case_url = isset($case['url']) ? $case['url'] : '';
        $post_id = land76wp_case_seo_import_resolve_post_id($case_url);
        if (!$post_id) {
            $stats['unresolved_cases'][] = $case_url;
            continue;
        }

        update_post_meta($post_id, '_wp_page_template', 'casenew.php');
        $stats['templates_updated']++;

        $acf_fields = !empty($case['acf']) && is_array($case['acf']) ? $case['acf'] : array();
        land76wp_case_seo_import_update_fields($post_id, $acf_fields, $stats);
        $stats['cases_updated']++;
    }

    if (!empty($payload['category_case_maps']) && is_array($payload['category_case_maps'])) {
        land76wp_case_seo_import_update_category_case_maps($payload['category_case_maps'], $stats);
    }

    return $stats;
}
