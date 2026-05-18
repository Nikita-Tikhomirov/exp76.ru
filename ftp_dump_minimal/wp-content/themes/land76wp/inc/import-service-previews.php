<?php
if (!defined('ABSPATH')) {
    exit;
}

function land76wp_service_previews_import_json_path()
{
    return trailingslashit(get_template_directory()) . 'import/service-previews-import.json';
}

function land76wp_service_previews_find_attachment($relative_file, $url)
{
    $attachments = get_posts(array(
        'post_type' => 'attachment',
        'post_status' => 'inherit',
        'posts_per_page' => 1,
        'fields' => 'ids',
        'meta_key' => '_wp_attached_file',
        'meta_value' => $relative_file,
        'suppress_filters' => true,
    ));

    if (!empty($attachments)) {
        return (int) $attachments[0];
    }

    $attachments = get_posts(array(
        'post_type' => 'attachment',
        'post_status' => 'inherit',
        'posts_per_page' => 1,
        'fields' => 'ids',
        's' => basename($relative_file),
        'suppress_filters' => true,
    ));

    foreach ($attachments as $attachment_id) {
        if (wp_get_attachment_url($attachment_id) === $url) {
            return (int) $attachment_id;
        }
    }

    return 0;
}

function land76wp_service_previews_register_attachment(array $item, array &$stats)
{
    $upload_dir = wp_upload_dir();
    if (!empty($upload_dir['error'])) {
        $stats['errors'][] = 'Upload dir error: ' . $upload_dir['error'];
        return 0;
    }

    $subdir = !empty($item['upload_subdir']) ? trim($item['upload_subdir'], '/') : 'seo-service-photos';
    $filename = isset($item['filename']) ? sanitize_file_name($item['filename']) : '';
    if ($filename === '') {
        $stats['errors'][] = 'Skipped preview with empty filename.';
        return 0;
    }

    $relative_file = $subdir . '/' . $filename;
    $file_path = trailingslashit($upload_dir['basedir']) . $relative_file;
    $file_url = trailingslashit($upload_dir['baseurl']) . $relative_file;

    if (!file_exists($file_path)) {
        $stats['errors'][] = 'Preview image file not found: ' . $file_path;
        return 0;
    }

    $attachment_id = land76wp_service_previews_find_attachment($relative_file, $file_url);
    $filetype = wp_check_filetype($filename, null);
    $attachment_data = array(
        'post_mime_type' => !empty($filetype['type']) ? $filetype['type'] : 'image/webp',
        'post_title' => !empty($item['title']) ? wp_strip_all_tags($item['title']) : pathinfo($filename, PATHINFO_FILENAME),
        'post_content' => !empty($item['description']) ? wp_strip_all_tags($item['description']) : '',
        'post_excerpt' => !empty($item['caption']) ? wp_strip_all_tags($item['caption']) : '',
        'post_status' => 'inherit',
        'guid' => $file_url,
    );

    if ($attachment_id) {
        $attachment_data['ID'] = $attachment_id;
        wp_update_post(wp_slash($attachment_data));
        $stats['attachments_updated']++;
    } else {
        $attachment_id = wp_insert_attachment(wp_slash($attachment_data), $file_path);
        if (is_wp_error($attachment_id)) {
            $stats['errors'][] = 'Could not create attachment for ' . $filename . ': ' . $attachment_id->get_error_message();
            return 0;
        }
        update_post_meta($attachment_id, '_wp_attached_file', $relative_file);
        $stats['attachments_created']++;
    }

    if (!function_exists('wp_generate_attachment_metadata')) {
        require_once ABSPATH . 'wp-admin/includes/image.php';
    }

    $metadata = wp_generate_attachment_metadata($attachment_id, $file_path);
    if (!empty($metadata) && is_array($metadata)) {
        wp_update_attachment_metadata($attachment_id, $metadata);
    }

    if (!empty($item['alt'])) {
        update_post_meta($attachment_id, '_wp_attachment_image_alt', wp_strip_all_tags($item['alt']));
    }

    return (int) $attachment_id;
}

function land76wp_run_service_previews_import($json_path = '')
{
    $stats = array(
        'json_path' => '',
        'attachments_created' => 0,
        'attachments_updated' => 0,
        'posts_updated' => 0,
        'unresolved_posts' => array(),
        'errors' => array(),
    );

    $json_path = $json_path ? $json_path : land76wp_service_previews_import_json_path();
    $stats['json_path'] = $json_path;

    if (!file_exists($json_path)) {
        $stats['errors'][] = 'Service previews JSON file not found: ' . $json_path;
        return $stats;
    }

    $payload = json_decode(file_get_contents($json_path), true);
    if (!is_array($payload) || empty($payload['items']) || !is_array($payload['items'])) {
        $stats['errors'][] = 'Invalid service previews JSON payload.';
        return $stats;
    }

    foreach ($payload['items'] as $item) {
        $slug = isset($item['slug']) ? sanitize_title($item['slug']) : '';
        if ($slug === '') {
            $stats['errors'][] = 'Skipped preview with empty slug.';
            continue;
        }

        $post = get_page_by_path($slug, OBJECT, 'post');
        if (!$post instanceof WP_Post) {
            $stats['unresolved_posts'][] = $slug;
            continue;
        }

        $attachment_id = land76wp_service_previews_register_attachment($item, $stats);
        if (!$attachment_id) {
            continue;
        }

        set_post_thumbnail($post->ID, $attachment_id);
        update_post_meta($post->ID, '_land76_service_preview_alt', !empty($item['alt']) ? wp_strip_all_tags($item['alt']) : '');
        delete_post_meta($post->ID, '_land76_service_preview_source_case');
        $stats['posts_updated']++;
    }

    return $stats;
}
