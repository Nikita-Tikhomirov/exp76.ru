<?php
declare(strict_types=1);

define('ABSPATH', __DIR__ . DIRECTORY_SEPARATOR);

$land76_test_theme = dirname(__DIR__) . '/ftp_dump_minimal/wp-content/themes/land76wp';
$land76_test_posts = array();
$land76_test_meta = array();
$land76_test_acf_values = array();
$land76_test_fields_by_key = array();
$land76_test_fields_by_name = array();
$land76_test_attachments_by_url = array();
$land76_test_categories = array();
$land76_test_thumbnails = array();
$land76_test_permalinks = array();
$land76_test_update_mode = 'write';
$land76_test_registry = array();
$land76_test_skip_leaf_reference = '';
$land76_test_acf_flushes = array();

class WP_Post
{
    public int $ID;
    public string $post_type;
    public string $post_status;
    public string $post_name;
    public int $post_parent;
    public string $post_title;
    public string $post_content;
    public string $post_excerpt;

    public function __construct(array $values)
    {
        foreach ($values as $key => $value) {
            $this->{$key} = $value;
        }
    }
}

class WP_Term
{
    public int $term_id;

    public function __construct(int $term_id)
    {
        $this->term_id = $term_id;
    }
}

function add_action($hook, $callback): void {}
function wp_json_encode($value, $flags = 0, $depth = 512): string
{
    return (string) json_encode($value, $flags, $depth);
}
function wp_strip_all_tags($value): string { return strip_tags((string) $value); }
function wp_parse_url($url) { return parse_url((string) $url); }
function home_url($path = ''): string { return 'https://exp76.ru/' . ltrim((string) $path, '/'); }
function trailingslashit($value): string { return rtrim((string) $value, '/\\') . '/'; }
function acf_flush_value_cache($post_id = 0, $field_name = ''): void
{
    global $land76_test_acf_flushes;
    $land76_test_acf_flushes[] = (int) $post_id . ':' . (string) $field_name;
}
function get_template_directory(): string { global $land76_test_theme; return $land76_test_theme; }
function get_post($post_id)
{
    global $land76_test_posts;
    return $land76_test_posts[(int) $post_id] ?? null;
}
function get_post_meta($post_id, $key, $single = false)
{
    global $land76_test_meta;
    return $land76_test_meta[(int) $post_id][$key] ?? '';
}
function update_post_meta($post_id, $key, $value): bool
{
    global $land76_test_meta, $land76_test_acf_values;
    $land76_test_meta[(int) $post_id][$key] = $value;
    if (preg_match('/^ns87_problem_items_([0-9]+)_image$/D', (string) $key, $matches) === 1) {
        $row_index = (int) $matches[1];
        $land76_test_acf_values[(int) $post_id]['field_ns87_problem_items'][$row_index]['field_ns87_problem_items_image'] = $value;
    }
    return true;
}
function get_permalink($post): string
{
    global $land76_test_permalinks;
    $post_id = $post instanceof WP_Post ? $post->ID : (int) $post;
    return $land76_test_permalinks[$post_id] ?? '';
}
function get_page_template_slug($post_id): string { return 'servicepost.php'; }
function get_posts($args = array()): array { return array(); }
function get_term_by($field, $value, $taxonomy) { return new WP_Term(900); }
function wp_get_post_categories($post_id): array
{
    global $land76_test_categories;
    return $land76_test_categories[(int) $post_id] ?? array();
}
function get_post_thumbnail_id($post_id): int
{
    global $land76_test_thumbnails;
    return $land76_test_thumbnails[(int) $post_id] ?? 0;
}
function attachment_url_to_postid($url): int
{
    global $land76_test_attachments_by_url;
    return $land76_test_attachments_by_url[(string) $url] ?? 0;
}
function get_post_mime_type($post_id): string
{
    $post = get_post((int) $post_id);
    return $post instanceof WP_Post && $post->post_type === 'attachment' ? 'image/webp' : '';
}
function wp_attachment_is_image($post_id): bool
{
    return strpos(get_post_mime_type((int) $post_id), 'image/') === 0;
}
function land76wp_service_hub_registry(): array
{
    global $land76_test_registry;
    return $land76_test_registry;
}
function land76wp_service_hub_by_service_id($service_id): array
{
    global $land76_test_registry;
    if (isset($land76_test_registry[(string) $service_id])) {
        return $land76_test_registry[(string) $service_id];
    }
    return array(
        'service_id' => (string) $service_id,
        'grouping_slug' => strtolower((string) $service_id),
    );
}

function land76_test_field_by_selector($selector)
{
    global $land76_test_fields_by_key, $land76_test_fields_by_name;
    $selector = (string) $selector;
    return $land76_test_fields_by_key[$selector] ?? $land76_test_fields_by_name[$selector] ?? false;
}

function acf_get_field($selector)
{
    return land76_test_field_by_selector($selector);
}

function land76_test_format_acf_value($value, array $field)
{
    $type = isset($field['type']) ? (string) $field['type'] : '';
    if ($type === 'image') {
        $post_id = (int) $value;
        return $post_id > 0 && get_post($post_id) instanceof WP_Post
            ? array('ID' => $post_id, 'url' => 'formatted-image-' . $post_id . '.webp')
            : false;
    }
    if ($type === 'wysiwyg') {
        return (string) $value . "\n<p>formatted by acf_the_content</p>";
    }
    if ($type === 'repeater') {
        if (!is_array($value)) {
            return false;
        }
        $rows = array();
        foreach ($value as $row) {
            $formatted_row = array();
            foreach ($field['sub_fields'] as $sub_field) {
                $sub_value = is_array($row) && array_key_exists($sub_field['key'], $row)
                    ? $row[$sub_field['key']]
                    : null;
                $formatted_row[$sub_field['name']] = land76_test_format_acf_value($sub_value, $sub_field);
            }
            $rows[] = $formatted_row;
        }
        return $rows;
    }
    return $value;
}

function get_field($selector, $post_id = false, $format_value = true)
{
    global $land76_test_acf_values;
    $field = land76_test_field_by_selector($selector);
    if (!is_array($field) || empty($field['key'])) {
        return false;
    }
    $raw = $land76_test_acf_values[(int) $post_id][$field['key']] ?? false;
    return $format_value ? land76_test_format_acf_value($raw, $field) : $raw;
}

function land76_test_acf_update_storage($value, array $field)
{
    $type = isset($field['type']) ? (string) $field['type'] : '';
    if ($type === 'image') {
        return (int) $value;
    }
    if ($type === 'relationship' || $type === 'post_object') {
        return is_array($value) ? array_map('intval', $value) : (int) $value;
    }
    if ($type === 'repeater') {
        if (!is_array($value)) {
            return false;
        }
        $stored_rows = array();
        foreach ($value as $row) {
            $stored_row = array();
            foreach ($field['sub_fields'] as $sub_field) {
                if (is_array($row) && array_key_exists($sub_field['key'], $row)) {
                    $sub_value = $row[$sub_field['key']];
                } elseif (is_array($row) && array_key_exists($sub_field['name'], $row)) {
                    $sub_value = $row[$sub_field['name']];
                } else {
                    continue;
                }
                $stored_row[$sub_field['key']] = land76_test_acf_update_storage($sub_value, $sub_field);
            }
            $stored_rows[] = $stored_row;
        }
        return $stored_rows;
    }
    return $value;
}

function land76_test_write_acf_references($post_id, $value, array $field, string $storage_name): void
{
    global $land76_test_skip_leaf_reference, $land76_test_acf_flushes;
    if (!in_array($field['type'], array('repeater', 'group'), true) || !is_array($value)) {
        return;
    }
    $rows = $field['type'] === 'repeater' ? $value : array($value);
    foreach ($rows as $row_index => $row) {
        foreach ($field['sub_fields'] as $sub_field) {
            if (is_array($row) && array_key_exists($sub_field['key'], $row)) {
                $sub_value = $row[$sub_field['key']];
            } elseif (is_array($row) && array_key_exists($sub_field['name'], $row)) {
                $sub_value = $row[$sub_field['name']];
            } else {
                continue;
            }
            $sub_storage_name = $field['type'] === 'repeater'
                ? $storage_name . '_' . $row_index . '_' . $sub_field['name']
                : $storage_name . '_' . $sub_field['name'];
            if (!hash_equals($sub_storage_name, $land76_test_skip_leaf_reference)) {
                update_post_meta((int) $post_id, '_' . $sub_storage_name, $sub_field['key']);
            }
            land76_test_write_acf_references((int) $post_id, $sub_value, $sub_field, $sub_storage_name);
        }
    }
}

function update_field($selector, $value, $post_id): bool
{
    global $land76_test_acf_values, $land76_test_update_mode;
    global $land76_test_fields_by_key;
    if ($land76_test_update_mode === 'noop') {
        return false;
    }
    $field = land76_test_field_by_selector($selector);
    if (!is_array($field) || empty($field['key'])) {
        return false;
    }
    $land76_test_acf_values[(int) $post_id][$field['key']] = land76_test_acf_update_storage($value, $field);
    if (isset($land76_test_fields_by_key[(string) $selector])) {
        update_post_meta((int) $post_id, '_' . $field['name'], $field['key']);
        land76_test_write_acf_references((int) $post_id, $value, $field, $field['name']);
    }
    return true;
}

require $land76_test_theme . '/inc/import-service-hubs.php';

final class Land76_Acf_Storage_Test
{
    private int $assertions = 0;
    private int $failures = 0;

    public function run(string $name, callable $test): void
    {
        try {
            land76_test_reset();
            $test($this);
            echo "PASS {$name}\n";
        } catch (Throwable $error) {
            $this->failures++;
            echo "FAIL {$name}: {$error->getMessage()}\n";
        }
    }

    public function same($expected, $actual, string $message): void
    {
        $this->assertions++;
        if ($expected !== $actual) {
            throw new RuntimeException(
                $message . "\nExpected: " . var_export($expected, true) . "\nActual: " . var_export($actual, true)
            );
        }
    }

    public function true($actual, string $message): void
    {
        $this->same(true, $actual, $message);
    }

    public function throws(callable $callback, string $message_fragment, string $message): void
    {
        $this->assertions++;
        try {
            $callback();
        } catch (Throwable $error) {
            if (strpos($error->getMessage(), $message_fragment) !== false) {
                return;
            }
            throw new RuntimeException($message . ': unexpected error ' . $error->getMessage());
        }
        throw new RuntimeException($message . ': no error was thrown');
    }

    public function finish(): void
    {
        echo $this->assertions . " assertions, " . $this->failures . " failures\n";
        if ($this->failures !== 0) {
            exit(1);
        }
    }
}

function land76_test_register_field(array $field): void
{
    global $land76_test_fields_by_key, $land76_test_fields_by_name;
    $land76_test_fields_by_key[$field['key']] = $field;
    $land76_test_fields_by_name[$field['name']] = $field;
}

function land76_test_reset(): void
{
    global $land76_test_posts, $land76_test_meta, $land76_test_acf_values;
    global $land76_test_fields_by_key, $land76_test_fields_by_name;
    global $land76_test_attachments_by_url, $land76_test_categories;
    global $land76_test_thumbnails, $land76_test_permalinks, $land76_test_update_mode, $land76_test_registry;
    global $land76_test_skip_leaf_reference;

    $problem_field = array(
        'key' => 'field_ns87_problem_items',
        'name' => 'ns87_problem_items',
        'type' => 'repeater',
        'sub_fields' => array(
            array('key' => 'field_ns87_problem_items_title', 'name' => 'title', 'type' => 'text'),
            array('key' => 'field_ns87_problem_items_text', 'name' => 'text', 'type' => 'textarea'),
            array('key' => 'field_ns87_problem_items_image', 'name' => 'image', 'type' => 'image'),
        ),
    );
    $sections_field = array(
        'key' => 'field_blogseo_sections',
        'name' => 'blogseo_sections',
        'type' => 'repeater',
        'sub_fields' => array(
            array('key' => 'field_blogseo_section_heading', 'name' => 'heading', 'type' => 'text'),
            array('key' => 'field_blogseo_section_body', 'name' => 'body', 'type' => 'wysiwyg'),
            array(
                'key' => 'field_blogseo_section_points',
                'name' => 'points',
                'type' => 'repeater',
                'sub_fields' => array(
                    array('key' => 'field_blogseo_section_point_title', 'name' => 'title', 'type' => 'text'),
                    array('key' => 'field_blogseo_section_point_text', 'name' => 'text', 'type' => 'textarea'),
                ),
            ),
        ),
    );
    $plain_field = array('key' => 'field_ns87_hero_title', 'name' => 'ns87_hero_title', 'type' => 'text');
    $relationship_field = array(
        'key' => 'field_fake_relationship',
        'name' => 'fake_relationship',
        'type' => 'relationship',
    );
    $related_services = array(
        'key' => 'field_blogseo_related_services',
        'name' => 'blogseo_related_services',
        'type' => 'relationship',
    );
    $selected_projects = array(
        'key' => 'field_land76_selected_real_projects',
        'name' => 'selected_real_projects',
        'type' => 'relationship',
    );

    $land76_test_posts = array(
        1001 => new WP_Post(array(
            'ID' => 1001,
            'post_type' => 'post',
            'post_status' => 'draft',
            'post_name' => 'fixture-page',
            'post_parent' => 0,
            'post_title' => 'Fixture title',
            'post_content' => '<p>Fixture content</p>',
            'post_excerpt' => '',
        )),
        501 => new WP_Post(array('ID' => 501, 'post_type' => 'attachment', 'post_status' => 'inherit', 'post_name' => 'main', 'post_parent' => 0, 'post_title' => '', 'post_content' => '', 'post_excerpt' => '')),
        601 => new WP_Post(array('ID' => 601, 'post_type' => 'attachment', 'post_status' => 'inherit', 'post_name' => 'problem', 'post_parent' => 0, 'post_title' => '', 'post_content' => '', 'post_excerpt' => '')),
        10381 => new WP_Post(array('ID' => 10381, 'post_type' => 'page', 'post_status' => 'publish', 'post_name' => 'holiday', 'post_parent' => 0, 'post_title' => '', 'post_content' => '', 'post_excerpt' => '')),
    );
    $land76_test_meta = array();
    $land76_test_acf_values = array();
    $land76_test_fields_by_key = array();
    $land76_test_fields_by_name = array();
    foreach (array($problem_field, $sections_field, $plain_field, $relationship_field, $related_services, $selected_projects) as $field) {
        land76_test_register_field($field);
    }
    $land76_test_attachments_by_url = array(
        'https://exp76.ru/uploads/main.webp' => 501,
        'https://exp76.ru/uploads/problem.webp' => 601,
    );
    $land76_test_categories = array(1001 => array(74, 900));
    $land76_test_thumbnails = array(1001 => 501);
    $land76_test_permalinks = array(
        1001 => 'https://exp76.ru/services/fixture-page/',
        10381 => 'https://exp76.ru/holiday/',
    );
    $land76_test_update_mode = 'write';
    $land76_test_skip_leaf_reference = '';
    $land76_test_acf_flushes = array();
    $land76_test_registry = array();
    for ($service_number = 1; $service_number <= 15; $service_number++) {
        $service_id = 'S' . $service_number;
        $hub_post_id = 30000 + $service_number;
        $hub_slug = strtolower($service_id) . '-hub';
        $canonical = 'https://exp76.ru/services/' . $hub_slug . '/';
        $land76_test_posts[$hub_post_id] = new WP_Post(array(
            'ID' => $hub_post_id,
            'post_type' => 'page',
            'post_status' => 'publish',
            'post_name' => $hub_slug,
            'post_parent' => 0,
            'post_title' => '',
            'post_content' => '',
            'post_excerpt' => '',
        ));
        $land76_test_permalinks[$hub_post_id] = $canonical;
        $land76_test_registry[$service_id] = array(
            'service_id' => $service_id,
            'hub_post_id' => $hub_post_id,
            'canonical' => $canonical,
            'grouping_slug' => strtolower($service_id),
        );
    }
}

function land76_test_item(string $page_key, array $acf = array()): array
{
    $item = array(
        'page_key' => $page_key,
        'service_id' => strpos($page_key, 'S7-') === 0 ? 'S7' : 'S1',
        'topic_key' => strpos($page_key, 'S7-') === 0 ? 'S7' : 'S1',
        'role' => 'child_service',
        'slug' => 'fixture-page',
        'canonical' => 'https://exp76.ru/services/fixture-page/',
        'post_title' => 'Fixture title',
        'post_content' => '<p>Fixture content</p>',
        'checksum' => str_repeat('a', 64),
        'main_image' => array('url' => 'https://exp76.ru/uploads/main.webp', 'alt' => 'Main image'),
        'seo' => array('title' => 'SEO title', 'description' => 'SEO description'),
    );
    if ($acf !== array()) {
        $item['acf'] = $acf;
    }
    return $item;
}

function land76_test_release_operations(): array
{
    $operations = array();
    foreach (land76wp_service_hubs_expected_page_keys() as $index => $page_key) {
        $operations[] = array(
            'kind' => 'post',
            'action' => 'update',
            'post_id' => 20000 + $index,
            'item' => array('page_key' => $page_key),
        );
    }
    return $operations;
}

function land76_test_seed_verified_post(array $item): array
{
    global $land76_test_meta;
    $land76_test_meta[1001] = array_merge($land76_test_meta[1001] ?? array(), array(
        '_land76_release_id' => 'release-fixture',
        '_land76_manifest_sha256' => 'manifest-fixture',
        '_land76_page_key' => $item['page_key'],
        '_land76_service_id' => $item['service_id'],
        '_land76_topic_key' => $item['topic_key'],
        '_land76_canonical' => $item['canonical'],
        '_land76_import_owner' => land76wp_service_hubs_import_owner(),
        '_land76_import_checksum' => $item['checksum'],
        '_land76_main_image_url' => $item['main_image']['url'],
        '_land76_main_image_alt' => $item['main_image']['alt'],
        '_aioseo_title' => $item['seo']['title'],
        '_aioseo_description' => $item['seo']['description'],
    ));
    return array(
        'kind' => 'post',
        'action' => 'update',
        'post_id' => 1001,
        'post_type' => 'post',
        'parent_id' => 0,
        'item' => $item,
    );
}

function land76_test_verify(array $item, array $post_ids): array
{
    $operation = land76_test_seed_verified_post($item);
    return land76wp_service_hubs_verify_staged_item(
        $operation,
        'release-fixture',
        'manifest-fixture',
        $post_ids,
        'draft'
    );
}

$test = new Land76_Acf_Storage_Test();

$test->run('verifier compares raw image storage by exact field key', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta, $land76_test_fields_by_key;
    $item = land76_test_item('S1-CHILD-TEST', array(
        'ns87_problem_items' => array(array(
            'title' => 'Problem',
            'text' => 'Details',
            'image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
        ), array(
            'title' => 'Upload',
            'text' => 'Attachment',
            'image' => 'https://exp76.ru/uploads/problem.webp',
        )),
    ));
    $land76_test_acf_values[1001]['field_ns87_problem_items'] = array(array(
        'field_ns87_problem_items_title' => 'Problem',
        'field_ns87_problem_items_text' => 'Details',
        'field_ns87_problem_items_image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
    ), array(
        'field_ns87_problem_items_title' => 'Upload',
        'field_ns87_problem_items_text' => 'Attachment',
        'field_ns87_problem_items_image' => 601,
    ));
    $land76_test_meta[1001]['_ns87_problem_items'] = 'field_ns87_problem_items';
    land76_test_write_acf_references(
        1001,
        $land76_test_acf_values[1001]['field_ns87_problem_items'],
        $land76_test_fields_by_key['field_ns87_problem_items'],
        'ns87_problem_items'
    );
    $test->same(array(), land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), 'formatted image output must not affect storage verification');

    $land76_test_acf_values[1001]['field_ns87_problem_items'][1]['field_ns87_problem_items_image'] = 'https://exp76.ru/uploads/problem.webp';
    $test->true(
        in_array('staged_acf_mismatch: S1-CHILD-TEST.ns87_problem_items', land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), true),
        'an uploads URL left raw must not normalize to the expected attachment ID'
    );
    foreach (array(array('ID' => 601), get_post(601)) as $formatted_actual) {
        $land76_test_acf_values[1001]['field_ns87_problem_items'][1]['field_ns87_problem_items_image'] = $formatted_actual;
        $test->true(
            in_array('staged_acf_mismatch: S1-CHILD-TEST.ns87_problem_items', land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), true),
            'a formatted array or object must not satisfy the exact raw image contract'
        );
    }
    $land76_test_acf_values[1001]['field_ns87_problem_items'][1]['field_ns87_problem_items_image'] = array('ID' => 601);
    $land76_test_meta[1001]['_ns87_problem_items_1_image'] = 'field_wrong';
    $compound_errors = land76_test_verify($item, array('S1-CHILD-TEST' => 1001));
    $test->true(
        in_array('staged_acf_mismatch: S1-CHILD-TEST.ns87_problem_items', $compound_errors, true),
        'malformed actual raw storage must report the field mismatch'
    );
    $test->true(
        in_array('staged_acf_reference_mismatch: S1-CHILD-TEST.ns87_problem_items_1_image', $compound_errors, true),
        'malformed actual raw storage must not suppress expected leaf companion verification'
    );
    $land76_test_meta[1001]['_ns87_problem_items_1_image'] = 'field_ns87_problem_items_image';
    $land76_test_acf_values[1001]['field_ns87_problem_items'][1]['field_ns87_problem_items_image'] = 601;

    foreach (array('title', 'text', 'image') as $leaf_name) {
        $storage_name = 'ns87_problem_items_0_' . $leaf_name;
        $expected_key = $land76_test_meta[1001]['_' . $storage_name];
        $land76_test_meta[1001]['_' . $storage_name] = 'field_wrong';
        $test->true(
            in_array('staged_acf_reference_mismatch: S1-CHILD-TEST.' . $storage_name, land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), true),
            'every nested raw leaf companion must match its exact field key'
        );
        $land76_test_meta[1001]['_' . $storage_name] = $expected_key;
    }
});

$test->run('verifier compares raw WYSIWYG bytes', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta, $land76_test_fields_by_key;
    $body = "<p>Raw body</p>\n\n<p>Second paragraph</p>";
    $item = land76_test_item('S1-CHILD-TEST', array(
        'blogseo_sections' => array(array('heading' => 'Heading', 'body' => $body)),
    ));
    $land76_test_acf_values[1001]['field_blogseo_sections'] = array(array(
        'field_blogseo_section_heading' => 'Heading',
        'field_blogseo_section_body' => $body,
    ));
    $land76_test_meta[1001]['_blogseo_sections'] = 'field_blogseo_sections';
    land76_test_write_acf_references(
        1001,
        $land76_test_acf_values[1001]['field_blogseo_sections'],
        $land76_test_fields_by_key['field_blogseo_sections'],
        'blogseo_sections'
    );
    $test->same(array(), land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), 'WYSIWYG formatting must not change the storage contract');
});

$test->run('fresh generic ACF write uses the field key and round-trips storage', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_acf_flushes;
    $item = land76_test_item('S1-CHILD-TEST', array(
        'ns87_problem_items' => array(array(
            'title' => 'Problem',
            'text' => 'Details',
            'image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
        ), array(
            'title' => 'Upload',
            'text' => 'Attachment',
            'image' => 'https://exp76.ru/uploads/problem.webp',
        )),
    ));
    land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
    $test->same('field_ns87_problem_items', get_post_meta(1001, '_ns87_problem_items', true), 'first save must create the exact companion reference');
    $test->same(array(array(
        'field_ns87_problem_items_title' => 'Problem',
        'field_ns87_problem_items_text' => 'Details',
        'field_ns87_problem_items_image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
    ), array(
        'field_ns87_problem_items_title' => 'Upload',
        'field_ns87_problem_items_text' => 'Attachment',
        'field_ns87_problem_items_image' => 601,
    )), $land76_test_acf_values[1001]['field_ns87_problem_items'] ?? null, 'first save must persist prepared raw storage');
    foreach (array(
        'ns87_problem_items_0_title' => 'field_ns87_problem_items_title',
        'ns87_problem_items_0_text' => 'field_ns87_problem_items_text',
        'ns87_problem_items_0_image' => 'field_ns87_problem_items_image',
        'ns87_problem_items_1_title' => 'field_ns87_problem_items_title',
        'ns87_problem_items_1_text' => 'field_ns87_problem_items_text',
        'ns87_problem_items_1_image' => 'field_ns87_problem_items_image',
    ) as $storage_name => $field_key) {
        $test->same(
            $field_key,
            get_post_meta(1001, '_' . $storage_name, true),
            'first save must create every exact nested companion reference'
        );
    }
    $test->true(
        in_array('1001:ns87_problem_items_0_image', $land76_test_acf_flushes, true),
        'the directly restored image leaf cache must be flushed'
    );
    $test->true(
        in_array('1001:ns87_problem_items', $land76_test_acf_flushes, true),
        'the restored repeater parent cache must be flushed'
    );
});

$test->run('unresolved or unsafe ACF image URL fails closed', function (Land76_Acf_Storage_Test $test): void {
    foreach (array(
        'https://exp76.ru/uploads/missing.webp',
        'https://exp76.ru/wp-content/themes/land76wp/generated/context/../secret.webp',
        'https://example.org/wp-content/themes/land76wp/generated/context/context-photo-tree-pruning.webp',
    ) as $unsafe_url) {
        $item = land76_test_item('S1-CHILD-TEST', array(
            'ns87_problem_items' => array(array(
                'title' => 'Problem',
                'text' => 'Details',
                'image' => $unsafe_url,
            )),
        ));
        $test->throws(
            function () use ($item): void {
                land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
            },
            'unresolved_acf_image',
            'only an attachment or an exact checked-in context image is allowed'
        );
    }
});

$test->run('expected image arrays resolve one exact attachment while malformed raw scalars fail', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_fields_by_key;
    $item = land76_test_item('S1-CHILD-TEST', array(
        'ns87_problem_items' => array(array(
            'title' => 'Problem',
            'text' => 'Details',
            'image' => array('url' => 'https://exp76.ru/uploads/problem.webp'),
        )),
    ));
    land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
    $test->same(
        601,
        $land76_test_acf_values[1001]['field_ns87_problem_items'][0]['field_ns87_problem_items_image'] ?? 0,
        'a URL-only expected image array must resolve to its exact attachment ID'
    );

    land76_test_reset();
    $item['acf']['ns87_problem_items'][0]['image'] = array(
        'ID' => 601,
        'url' => 'https://exp76.ru/uploads/main.webp',
    );
    $test->throws(
        function () use ($item): void {
            land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
        },
        'unresolved_acf_image',
        'contradictory image ID and URL selectors must fail closed'
    );

    foreach (array(array('ID' => 0), array('id' => -1)) as $invalid_id_selector) {
        land76_test_reset();
        $invalid_id_selector['url'] = 'https://exp76.ru/uploads/problem.webp';
        $item['acf']['ns87_problem_items'][0]['image'] = $invalid_id_selector;
        $test->throws(
            function () use ($item): void {
                land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
            },
            'unresolved_acf_image',
            'an explicit nonpositive image ID must not be repaired by a valid URL selector'
        );
    }

    $image_field = $land76_test_fields_by_key['field_ns87_problem_items']['sub_fields'][2];
    $raw_overrides = array();
    $test->throws(
        function () use ($image_field, &$raw_overrides): void {
            land76wp_service_hubs_prepare_acf_image_storage(
                601.5,
                $image_field,
                'actual',
                'ns87_problem_items_0_image',
                $raw_overrides,
                'fixture.actual_image'
            );
        },
        'unresolved_acf_image',
        'actual raw image storage must be an integer or numeric string, never a coerced float'
    );
});

$test->run('missing nested companion fails key-based apply for every repeater leaf', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_skip_leaf_reference;
    foreach (array('title', 'text', 'image') as $leaf_name) {
        land76_test_reset();
        $land76_test_skip_leaf_reference = 'ns87_problem_items_0_' . $leaf_name;
        $item = land76_test_item('S1-CHILD-TEST', array(
            'ns87_problem_items' => array(array(
                'title' => 'Problem',
                'text' => 'Details',
                'image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
            )),
        ));
        $test->throws(
            function () use ($item): void {
                land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
            },
            'acf_storage_write_failed: ns87_problem_items_0_' . $leaf_name,
            'the importer must not synthesize any companion missing from ACF first save'
        );
    }
});

$test->run('invalid ACF field key or name fails before write', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_fields_by_key, $land76_test_fields_by_name;
    $land76_test_fields_by_name['ns87_hero_title']['key'] = '';
    $land76_test_fields_by_key['field_ns87_hero_title']['key'] = '';
    $item = land76_test_item('S1-CHILD-TEST', array('ns87_hero_title' => 'value'));
    $test->throws(
        function () use ($item): void {
            land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
        },
        'acf_schema_incompatible',
        'a missing exact field key must stop the write'
    );
});

$test->run('generic ACF schema rejects wrong types nested keys and ambiguous rows', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_fields_by_key;
    $land76_test_fields_by_key['field_ns87_hero_title']['type'] = 'textarea';
    $test->throws(
        function (): void {
            land76wp_service_hubs_apply_acf(
                land76_test_item('S1-CHILD-TEST', array('ns87_hero_title' => 'value')),
                1001,
                array('S1-CHILD-TEST' => 1001)
            );
        },
        'acf_schema_incompatible',
        'the frozen top-level field type must be exact'
    );

    land76_test_reset();
    $land76_test_fields_by_key['field_ns87_problem_items']['sub_fields'][0]['key'] = 'field_wrong_title';
    $test->throws(
        function (): void {
            land76wp_service_hubs_apply_acf(
                land76_test_item('S1-CHILD-TEST', array('ns87_problem_items' => array(array('title' => 'Problem')))),
                1001,
                array('S1-CHILD-TEST' => 1001)
            );
        },
        'acf_schema_incompatible',
        'nested fields must match the exact checked-in parent schema'
    );

    land76_test_reset();
    $test->throws(
        function (): void {
            land76wp_service_hubs_apply_acf(
                land76_test_item('S1-CHILD-TEST', array('ns87_problem_items' => array(array(
                    'title' => 'Problem',
                    'field_ns87_problem_items_title' => 'Problem',
                )))),
                1001,
                array('S1-CHILD-TEST' => 1001)
            );
        },
        'invalid_acf_storage',
        'one row must not specify the same nested field by both name and key'
    );
});

$test->run('wrong companion reference fails staged verification', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta;
    $item = land76_test_item('S1-CHILD-TEST', array('ns87_hero_title' => 'exact raw value'));
    $land76_test_acf_values[1001]['field_ns87_hero_title'] = 'exact raw value';
    $land76_test_meta[1001]['_ns87_hero_title'] = 'field_wrong';
    $errors = land76_test_verify($item, array('S1-CHILD-TEST' => 1001));
    $test->true(in_array('staged_acf_reference_mismatch: S1-CHILD-TEST.ns87_hero_title', $errors, true), 'wrong companion reference must fail closed');
});

$test->run('managed relationship fields use raw ordered unique IDs and exact companions', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta;
    $item = land76_test_item('S1-CHILD-TEST');
    $item['case_ids'] = array(777, 778);
    $land76_test_acf_values[1001]['field_land76_selected_real_projects'] = array('777', '778');
    $land76_test_meta[1001]['_selected_real_projects'] = 'field_land76_selected_real_projects';
    $test->same(array(), land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), 'exact raw relationship order and companion must pass');

    $land76_test_acf_values[1001]['field_land76_selected_real_projects'] = array('778', '777');
    $test->true(
        in_array('staged_acf_mismatch: S1-CHILD-TEST.selected_real_projects', land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), true),
        'relationship order drift must fail'
    );

    $land76_test_acf_values[1001]['field_land76_selected_real_projects'] = array('777', '778');
    $land76_test_meta[1001]['_selected_real_projects'] = 'field_wrong';
    $test->true(
        in_array('staged_acf_reference_mismatch: S1-CHILD-TEST.selected_real_projects', land76_test_verify($item, array('S1-CHILD-TEST' => 1001)), true),
        'managed relationship companion drift must fail'
    );
});

$test->run('no-op update is accepted only when post-write storage is exact', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta, $land76_test_update_mode;
    $item = land76_test_item('S1-CHILD-TEST', array('ns87_hero_title' => 'expected'));
    $land76_test_acf_values[1001]['field_ns87_hero_title'] = 'wrong';
    $land76_test_meta[1001]['_ns87_hero_title'] = 'field_ns87_hero_title';
    $land76_test_update_mode = 'noop';
    land76wp_service_hubs_apply_acf($item, 1001, array('S1-CHILD-TEST' => 1001));
    $errors = land76_test_verify($item, array('S1-CHILD-TEST' => 1001));
    $test->true(in_array('staged_acf_mismatch: S1-CHILD-TEST.ns87_hero_title', $errors, true), 'post-write verification, not update_field return value, must reject wrong storage');
});

$test->run('duplicate or malformed relationship IDs fail closed', function (Land76_Acf_Storage_Test $test): void {
    foreach (array(array(77, 77), array(77, 0), array(77, 'bad')) as $invalid_ids) {
        $test->throws(
            function () use ($invalid_ids): void {
                call_user_func('land76wp_service_hubs_normalize_relation_ids', $invalid_ids, 'fixture.fake_relationship');
            },
            'invalid_acf_relation',
            'relationship IDs must be ordered positive unique integers'
        );
    }
    $test->throws(
        function (): void {
            land76wp_service_hubs_normalize_relation_ids(array(get_post(1001)), 'fixture.actual_relation', 'actual');
        },
        'invalid_acf_relation',
        'formatted post objects must not satisfy the raw relationship contract'
    );
    global $land76_test_fields_by_key;
    $raw_overrides = array();
    $storage_references = array();
    $test->throws(
        function () use (&$raw_overrides, &$storage_references, $land76_test_fields_by_key): void {
            land76wp_service_hubs_prepare_acf_storage_value(
                array(get_post(1001)),
                $land76_test_fields_by_key['field_fake_relationship'],
                'actual',
                'fake_relationship',
                $raw_overrides,
                'fixture.actual_relationship_storage',
                $storage_references
            );
        },
        'invalid_acf_relation',
        'schema-aware actual normalization must not hide a formatted relationship object'
    );
});

$test->run('operation post map rejects missing duplicate and nonpositive records', function (Land76_Acf_Storage_Test $test): void {
    $operations = land76_test_release_operations();
    $post_ids = call_user_func('land76wp_service_hubs_build_relation_post_ids', $operations);
    $test->same(91, count($post_ids), 'the closed relation map must contain 76 release posts and 15 validated hubs');
    $test->same(20000, $post_ids['S1-CHILD-3D'] ?? 0, 'the closed map must retain the exact release operation ID');
    $test->same(30001, $post_ids['S1-HUB'] ?? 0, 'the closed map must include the independently validated S1 hub');
    $invalid_sets = array();
    $invalid_sets['nonpositive post ID'] = $operations;
    $invalid_sets['nonpositive post ID'][0]['post_id'] = 0;
    $invalid_sets['missing post ID'] = $operations;
    unset($invalid_sets['missing post ID'][0]['post_id']);
    $invalid_sets['malformed post ID'] = $operations;
    $invalid_sets['malformed post ID'][0]['post_id'] = 'not-an-id';
    $invalid_sets['negative post ID'] = $operations;
    $invalid_sets['negative post ID'][0]['post_id'] = -1;
    $invalid_sets['missing page key'] = $operations;
    unset($invalid_sets['missing page key'][0]['item']['page_key']);
    $invalid_sets['duplicate page key'] = $operations;
    $invalid_sets['duplicate page key'][] = $operations[0];
    $invalid_sets['duplicate post ID'] = $operations;
    $invalid_sets['duplicate post ID'][1]['post_id'] = $operations[0]['post_id'];
    $invalid_sets['operation collides with hub ID'] = $operations;
    $invalid_sets['operation collides with hub ID'][0]['post_id'] = 30001;
    $invalid_sets['incomplete operation inventory'] = array_slice($operations, 0, -1);
    foreach ($invalid_sets as $case_name => $invalid_operations) {
        $test->throws(
            function () use ($invalid_operations): void {
                call_user_func('land76wp_service_hubs_build_relation_post_ids', $invalid_operations);
            },
            'invalid_operation_post_map',
            $case_name . ' must fail the closed relation-map contract'
        );
    }
});

$test->run('planned create IDs defer only the complete map while preserving strict namespace checks', function (Land76_Acf_Storage_Test $test): void {
    $operations = land76_test_release_operations();
    foreach ($operations as &$operation) {
        $operation['post_id'] = 0;
        $operation['action'] = 'create';
    }
    unset($operation);
    $hub_post_ids = land76wp_service_hubs_build_validated_hub_relation_post_ids();
    $test->same(
        true,
        land76wp_service_hubs_validate_relation_operation_namespace($operations, $hub_post_ids, true),
        'all-create Preview may defer only the not-yet-assigned release IDs'
    );
    $invalid_pending_sets = array();
    $invalid_pending_sets['missing post ID'] = $operations;
    unset($invalid_pending_sets['missing post ID'][0]['post_id']);
    $invalid_pending_sets['malformed post ID'] = $operations;
    $invalid_pending_sets['malformed post ID'][0]['post_id'] = 'bad';
    $invalid_pending_sets['negative post ID'] = $operations;
    $invalid_pending_sets['negative post ID'][0]['post_id'] = -1;
    $invalid_pending_sets['non-create zero'] = $operations;
    $invalid_pending_sets['non-create zero'][0]['action'] = 'update';
    $invalid_pending_sets['create positive'] = $operations;
    $invalid_pending_sets['create positive'][0]['post_id'] = 20000;
    foreach ($invalid_pending_sets as $case_name => $invalid_operations) {
        $test->throws(
            function () use ($invalid_operations, $hub_post_ids): void {
                land76wp_service_hubs_validate_relation_operation_namespace(
                    $invalid_operations,
                    $hub_post_ids,
                    true
                );
            },
            'invalid_operation_post_map',
            $case_name . ' must never be hidden by create-ID deferral'
        );
    }
    $operations[0]['item']['page_key'] = $operations[1]['item']['page_key'];
    $test->throws(
        function () use ($operations, $hub_post_ids): void {
            land76wp_service_hubs_validate_relation_operation_namespace($operations, $hub_post_ids, true);
        },
        'invalid_operation_post_map',
        'pending IDs must not mask a duplicate or missing release page key'
    );
});

$test->run('realized Stage creates keep their action and enter the finalized 91-entry map', function (Land76_Acf_Storage_Test $test): void {
    $operations = land76_test_release_operations();
    foreach ($operations as &$operation) {
        $operation['action'] = 'create';
        $operation['post_id'] = 0;
    }
    unset($operation);
    $hub_post_ids = land76wp_service_hubs_build_validated_hub_relation_post_ids();
    $test->same(
        true,
        land76wp_service_hubs_validate_relation_operation_namespace($operations, $hub_post_ids, true),
        'Preview must defer the exact create-zero namespace'
    );
    foreach ($operations as $index => &$operation) {
        $operation['post_id'] = 20000 + $index;
    }
    unset($operation);
    $finalized = land76wp_service_hubs_build_relation_post_ids($operations);
    $test->same(91, count($finalized), 'realized create IDs must produce the complete finalized relation map');
    $test->same(20000, $finalized['S1-CHILD-3D'] ?? 0, 'finalized creates must retain their exact assigned Stage ID');

    $operations[0]['post_id'] = 0;
    $test->throws(
        function () use ($operations): void {
            land76wp_service_hubs_build_relation_post_ids($operations);
        },
        'invalid_operation_post_map',
        'finalized mode must still reject an unrealized create-zero operation'
    );
});

$test->run('closed relation map requires the exact S1 through S15 registry keys', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_registry;
    unset($land76_test_registry['S15']);
    $test->throws(
        function (): void {
            land76wp_service_hubs_build_relation_post_ids(land76_test_release_operations());
        },
        'invalid_operation_post_map: hub registry',
        'a missing registry hub must fail before any relation can be verified'
    );
});

$test->run('validated registry hub participates in the closed relation map', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta;
    $item = land76_test_item('S1-CHILD-TEST');
    $item['related_service_page_keys'] = array('S1-HUB');
    $land76_test_acf_values[1001]['field_blogseo_related_services'] = array(30001);
    $land76_test_meta[1001]['_blogseo_related_services'] = 'field_blogseo_related_services';
    $test->same(
        array(),
        land76_test_verify($item, array('S1-CHILD-TEST' => 1001, 'S1-HUB' => 30001)),
        'a hub relation must resolve only through its independently validated closed-map entry'
    );
});

$test->run('S7 relation verification uses only the supplied full operation map', function (Land76_Acf_Storage_Test $test): void {
    global $land76_test_acf_values, $land76_test_meta;
    $item = land76_test_item('S7-CHILD-DESIGN');
    $item['related_service_page_keys'] = array('S7-CHILD-HOLIDAY');
    $land76_test_acf_values[1001]['field_blogseo_related_services'] = array(10381);
    $land76_test_meta[1001]['_blogseo_related_services'] = 'field_blogseo_related_services';
    $test->same(
        array(),
        land76_test_verify($item, array('S7-CHILD-DESIGN' => 1001, 'S7-CHILD-HOLIDAY' => 10381)),
        'the unowned frozen reuse target must resolve through the Stage operation map'
    );
    $test->true(
        in_array('staged_relation_map_mismatch: S7-CHILD-DESIGN -> S7-CHILD-HOLIDAY', land76_test_verify($item, array('S7-CHILD-DESIGN' => 1001)), true),
        'a missing relation map entry must fail closed'
    );
    $test->true(
        in_array('staged_acf_mismatch: S7-CHILD-DESIGN.blogseo_related_services', land76_test_verify($item, array('S7-CHILD-DESIGN' => 1001, 'S7-CHILD-HOLIDAY' => 9999)), true),
        'a wrong relation map ID must fail exact storage verification'
    );
});

$test->run('managed template merge restores only validated raw theme images by anchored row', function (Land76_Acf_Storage_Test $test): void {
    $formatted = array(
        array('title' => 'Problem', 'text' => 'Details', 'image' => false),
        array('title' => 'Upload', 'text' => 'Attachment', 'image' => array('ID' => 601, 'url' => 'upload.webp')),
    );
    $raw = array(
        array(
            'field_ns87_problem_items_title' => 'Problem',
            'field_ns87_problem_items_text' => 'Details',
            'field_ns87_problem_items_image' => 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp',
        ),
        array(
            'field_ns87_problem_items_title' => 'Upload',
            'field_ns87_problem_items_text' => 'Attachment',
            'field_ns87_problem_items_image' => 601,
        ),
    );
    $expected = $formatted;
    $expected[0]['image'] = 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-landscape-design-worktable.webp';
    $test->same($expected, land76wp_service_hubs_merge_problem_item_images($formatted, $raw), 'only the validated external leaf must replace formatted image output');

    $swapped = array_reverse($raw);
    $test->same($formatted, land76wp_service_hubs_merge_problem_item_images($formatted, $swapped), 'swapped title and text anchors must disable the merge');
    $test->same($formatted, land76wp_service_hubs_merge_problem_item_images($formatted, array($raw[0])), 'row-count mismatch must disable the merge');
    $invalid_rows = array();
    $invalid_rows['malformed raw row'] = $raw;
    $invalid_rows['malformed raw row'][0] = 'not-an-array';
    $invalid_rows['missing raw key'] = $raw;
    unset($invalid_rows['missing raw key'][0]['field_ns87_problem_items_image']);
    $invalid_rows['uploads URL'] = $raw;
    $invalid_rows['uploads URL'][0]['field_ns87_problem_items_image'] = 'https://exp76.ru/wp-content/uploads/problem.webp';
    $invalid_rows['formatted array'] = $raw;
    $invalid_rows['formatted array'][0]['field_ns87_problem_items_image'] = array('ID' => 601, 'url' => 'upload.webp');
    $invalid_rows['formatted object'] = $raw;
    $invalid_rows['formatted object'][0]['field_ns87_problem_items_image'] = get_post(601);
    $invalid_rows['foreign URL'] = $raw;
    $invalid_rows['foreign URL'][0]['field_ns87_problem_items_image'] = 'https://example.org/unsafe.webp';
    $invalid_rows['traversal URL'] = $raw;
    $invalid_rows['traversal URL'][0]['field_ns87_problem_items_image'] = 'https://exp76.ru/wp-content/themes/land76wp/generated/context/%2e%2e/context-photo-secret.webp';
    $invalid_rows['unreadable theme URL'] = $raw;
    $invalid_rows['unreadable theme URL'][0]['field_ns87_problem_items_image'] = 'https://exp76.ru/wp-content/themes/land76wp/generated/context/context-photo-does-not-exist.webp';
    $invalid_rows['zero attachment ID'] = $raw;
    $invalid_rows['zero attachment ID'][0]['field_ns87_problem_items_image'] = 0;
    $invalid_rows['negative attachment ID'] = $raw;
    $invalid_rows['negative attachment ID'][0]['field_ns87_problem_items_image'] = -1;
    $invalid_rows['nonimage post ID'] = $raw;
    $invalid_rows['nonimage post ID'][0]['field_ns87_problem_items_image'] = 1001;
    foreach ($invalid_rows as $case_name => $invalid_raw) {
        $test->same(
            $formatted,
            land76wp_service_hubs_merge_problem_item_images($formatted, $invalid_raw),
            $case_name . ' must return the original formatted rows without fatal error'
        );
    }
});

$test->finish();
