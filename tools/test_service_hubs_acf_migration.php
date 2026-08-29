<?php
declare(strict_types=1);

define('ABSPATH', __DIR__ . DIRECTORY_SEPARATOR);

$land76_theme_directory = dirname(__DIR__) . '/ftp_dump_minimal/wp-content/themes/land76wp';
$land76_fields = array();
$land76_groups = array();
$land76_raw_fields = array();
$land76_updated_fields = array();
$land76_updated_groups = 0;
$land76_candidate_query_failed = false;

final class Land76_Test_Wpdb
{
    public string $posts = 'wp_posts';
    public string $last_error = '';

    public function prepare($query, ...$args)
    {
        return $query;
    }

    public function get_col($query)
    {
        global $land76_raw_fields, $land76_candidate_query_failed;
        if ($land76_candidate_query_failed) {
            $this->last_error = 'injected candidate query failure';
            return array();
        }
        $this->last_error = '';
        $ids = array_keys($land76_raw_fields);
        sort($ids, SORT_NUMERIC);
        return $ids;
    }
}

$wpdb = new Land76_Test_Wpdb();

function add_action($hook, $callback): void {}
function trailingslashit($path): string { return rtrim((string) $path, '/\\') . '/'; }
function get_template_directory(): string { global $land76_theme_directory; return $land76_theme_directory; }
function wp_json_encode($value, $flags = 0, $depth = 512): string { return (string) json_encode($value, $flags, $depth); }
function acf_get_field($key) { global $land76_fields; return $land76_fields[$key] ?? false; }
function acf_get_field_group($key) { global $land76_groups; return $land76_groups[$key] ?? false; }
function acf_get_raw_field($id) { global $land76_raw_fields; return $land76_raw_fields[(int) $id] ?? false; }
function acf_update_field($field) {
    global $land76_fields, $land76_raw_fields, $land76_updated_fields;
    $land76_updated_fields[] = $field;
    $land76_raw_fields[(int) $field['ID']] = $field;
    $land76_fields[$field['key']] = $field;
    return $field;
}
function acf_update_field_group($group) {
    global $land76_updated_groups;
    $land76_updated_groups++;
    return $group;
}

require $land76_theme_directory . '/inc/import-service-hubs.php';

final class Land76_Acf_Migration_Test
{
    private int $assertions = 0;

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

    public function false($actual, string $message): void
    {
        $this->same(false, $actual, $message);
    }

    public function count(): int
    {
        return $this->assertions;
    }
}

function land76_test_legacy_field($parent = 0): array
{
    return array(
        'ID' => 10762,
        'key' => 'field_blogseo_related_services',
        'name' => 'blogseo_related_services',
        'type' => 'relationship',
        'required' => 0,
        'conditional_logic' => 0,
        'post_type' => array('post'),
        'post_status' => array('publish'),
        'taxonomy' => array('category:74'),
        'filters' => array('search', 'taxonomy'),
        'return_format' => 'id',
        'min' => 0,
        'max' => 0,
        'elements' => array('featured_image'),
        'parent' => $parent,
    );
}

function land76_test_group(array $overrides = array()): array
{
    return array_replace_recursive(
        array(
            'ID' => 10745,
            'key' => 'group_blogseo_post',
            'active' => true,
            'location' => array(array(array(
                'param' => 'post_taxonomy',
                'operator' => '==',
                'value' => 'category:72',
            ))),
        ),
        $overrides
    );
}

$test = new Land76_Acf_Migration_Test();
$expected_group = land76wp_service_hubs_required_acf_groups()['field_blogseo_related_services'];
$group = land76_test_group();
$orphan = land76_test_legacy_field(0);

$test->true(
    land76wp_service_hubs_acf_group_definition_matches($group, $expected_group),
    'The canonical active group with the exact frozen location must be accepted.'
);
$test->true(
    land76wp_service_hubs_is_exact_legacy_blog_relation($orphan, $group),
    'An exact known legacy field remains safely migratable when only its parent is stale.'
);
$test->false(
    land76wp_service_hubs_acf_group_matches($orphan, $group, $expected_group),
    'The desired live schema must still reject an orphan field before migration.'
);
$test->true(
    land76wp_service_hubs_acf_group_matches(land76_test_legacy_field(10745), $group, $expected_group),
    'The desired live schema must accept the canonical numeric group parent.'
);
$test->true(
    land76wp_service_hubs_acf_group_matches(land76_test_legacy_field('group_blogseo_post'), $group, $expected_group),
    'The desired live schema must accept the canonical group-key parent.'
);

$wrong_location = land76_test_group(array('location' => array(array(array(
    'param' => 'post_taxonomy',
    'operator' => '==',
    'value' => 'category:999',
)))));
$test->false(
    land76wp_service_hubs_is_exact_legacy_blog_relation($orphan, $wrong_location),
    'A stale parent cannot make a field migratable when the group location is not exact.'
);
$test->false(
    land76wp_service_hubs_is_exact_legacy_blog_relation($orphan, land76_test_group(array('active' => false))),
    'An inactive group cannot authorize the legacy migration.'
);
$test->false(
    land76wp_service_hubs_is_exact_legacy_blog_relation($orphan, land76_test_group(array('key' => 'group_other'))),
    'A different field group cannot authorize the legacy migration.'
);

$canonical_a = land76_test_legacy_field(10745);
$canonical_a['ID'] = 10820;
$canonical_b = land76_test_legacy_field(10745);
$canonical_b['ID'] = 10842;
$land76_raw_fields = array(
    10762 => $orphan,
    10820 => $canonical_a,
    10842 => $canonical_b,
);
$land76_fields = array('field_blogseo_related_services' => $orphan);
$land76_groups = array('group_blogseo_post' => $group);
$land76_updated_fields = array();
$land76_updated_groups = 0;
land76wp_service_hubs_migrate_legacy_blog_relation();

$test->same(3, count($land76_updated_fields), 'The migration must normalize every exact duplicate field record.');
$test->same(10762, $land76_updated_fields[0]['ID'], 'The migration must preserve the resolved field post ID.');
$test->same(0, $land76_updated_fields[0]['parent'], 'Existing orphan rows must remain hidden instead of adding more duplicate controls to the group.');
$test->same(10745, $land76_updated_fields[1]['parent'], 'Existing canonical group membership must be preserved.');
$test->same(array('post', 'page'), $land76_updated_fields[0]['post_type'], 'The migrated field must admit posts and pages.');
$test->same(array(), $land76_updated_fields[0]['taxonomy'], 'The migrated field must remove the legacy taxonomy restriction.');
$test->same(array('search'), $land76_updated_fields[0]['filters'], 'The migrated field must use the frozen search-only filter.');
$test->same(0, $land76_updated_groups, 'The targeted migration must never rewrite the existing field group.');
$inspection = land76wp_service_hubs_inspect_blog_relation($group, false);
$test->same(array(), $inspection['errors'], 'Every normalized duplicate must pass the candidate-wide schema check.');
$test->false($inspection['migration'], 'A fully normalized duplicate set must not request another migration.');
$test->same(3, count($inspection['fields']), 'The candidate-wide check must retain the exact locked inventory.');

$desired_orphan = $land76_raw_fields[10762];
$legacy_canonical = land76_test_legacy_field(10745);
$legacy_canonical['ID'] = 10820;
$land76_raw_fields = array(10762 => $desired_orphan, 10820 => $legacy_canonical);
$land76_updated_fields = array();
land76wp_service_hubs_migrate_legacy_blog_relation();
$test->same(1, count($land76_updated_fields), 'A retry must update only the remaining exact legacy duplicate.');
$test->same(10820, $land76_updated_fields[0]['ID'], 'A retry must preserve the remaining legacy row ID.');

$unknown = land76_test_legacy_field(10745);
$unknown['ID'] = 10999;
$unknown['taxonomy'] = array('category:999');
$land76_raw_fields[10999] = $unknown;
$land76_updated_fields = array();
$thrown = '';
try {
    land76wp_service_hubs_migrate_legacy_blog_relation();
} catch (RuntimeException $error) {
    $thrown = $error->getMessage();
}
$test->true(str_contains($thrown, 'acf_schema_incompatible'), 'An unknown duplicate schema must fail closed.');
$test->same(0, count($land76_updated_fields), 'Unknown duplicate data must be rejected before any field row changes.');

$foreign_parent = land76_test_legacy_field(99999);
$foreign_parent['ID'] = 11000;
$land76_raw_fields = array(10820 => $legacy_canonical, 11000 => $foreign_parent);
$foreign_inspection = land76wp_service_hubs_inspect_blog_relation($group, false);
$test->true(
    count(array_filter($foreign_inspection['errors'], static function ($error) {
        return str_contains($error, 'acf_group_incompatible');
    })) === 1,
    'A duplicate attached to an unrelated nonzero parent must fail closed.'
);

$land76_candidate_query_failed = true;
$query_failure = land76wp_service_hubs_inspect_blog_relation($group, false);
$land76_candidate_query_failed = false;
$test->true(
    count(array_filter($query_failure['errors'], static function ($error) {
        return str_contains($error, 'acf_schema_query_failed');
    })) === 1,
    'A failed duplicate inventory query must fail closed.'
);

echo 'PASS ' . $test->count() . " assertions\n";
