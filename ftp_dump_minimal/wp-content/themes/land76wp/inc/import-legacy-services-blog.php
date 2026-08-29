<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_legacy_services_blog_import_default_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/legacy-services-blog-import.json';
}

function land76wp_run_legacy_services_blog_import($json_path = '')
{
    if (!function_exists('land76wp_run_drenazh_blog_import')) {
        return array(
            'json_path' => $json_path,
            'errors' => array('Base SEO blog importer is unavailable.'),
        );
    }

    $json_path = $json_path ? $json_path : land76wp_legacy_services_blog_import_default_json_path();
    return land76wp_run_drenazh_blog_import($json_path);
}
