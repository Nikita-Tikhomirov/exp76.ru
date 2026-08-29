<?php
declare(strict_types=1);

if ($argc !== 2 || !in_array($argv[1], array('present', 'absent', 'partial', 'a2-noop', 'a1-drift'), true)) {
    fwrite(STDERR, "Usage: php bridge-lifecycle.php <present|absent|partial|a2-noop|a1-drift>\n");
    exit(2);
}

$scenario = $argv[1];
$root = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-bridge-' . bin2hex(random_bytes(8));
$docroot = $root . DIRECTORY_SEPARATOR . 'wordpress';
$storage = $root . DIRECTORY_SEPARATOR . 'storage';
$theme = $docroot . DIRECTORY_SEPARATOR . 'wp-content' . DIRECTORY_SEPARATOR . 'themes' . DIRECTORY_SEPARATOR . 'land76wp';
$importer = $theme . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'import-service-hubs.php';
$probe = $theme . DIRECTORY_SEPARATOR . 'inc' . DIRECTORY_SEPARATOR . 'a1-probe.php';

function land76_bridge_remove_tree(string $path): void {
    if (!file_exists($path) && !is_link($path)) return;
    if (!is_dir($path) || is_link($path)) {
        if (!@unlink($path)) throw new RuntimeException('TEST_CLEANUP_FILE_FAILED');
        return;
    }
    $items = scandir($path);
    if (!is_array($items)) throw new RuntimeException('TEST_CLEANUP_SCAN_FAILED');
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        land76_bridge_remove_tree($path . DIRECTORY_SEPARATOR . $item);
    }
    if (!@rmdir($path)) throw new RuntimeException('TEST_CLEANUP_DIRECTORY_FAILED');
}

register_shutdown_function(static function () use ($root): void {
    if (file_exists($root) || is_link($root)) land76_bridge_remove_tree($root);
});

if (!mkdir(dirname($importer), 0700, true) || !mkdir($storage, 0700, true)) {
    throw new RuntimeException('TEST_SETUP_DIRECTORY_FAILED');
}
$importer_bytes = '<?php $GLOBALS["land76_bridge_imported"] = true;';
$probe_bytes = '<?php return "a1-exact";';
file_put_contents($importer, $importer_bytes, LOCK_EX);
file_put_contents($probe, $scenario === 'a1-drift' ? $probe_bytes . 'drift' : $probe_bytes, LOCK_EX);

define('ABSPATH', $docroot . DIRECTORY_SEPARATOR);
define('LAND76_RELEASE_DEPLOYER_INTEGRATION_TEST', true);
function add_action($hook, $callback, $priority = 10): void {}
function add_filter($hook, $callback, $priority = 10): void {}
function register_activation_hook($file, $callback): void {}
function untrailingslashit($path): string { return rtrim((string)$path, '/\\'); }
function is_admin(): bool { return true; }
function current_user_can($capability): bool { return $capability === 'manage_options'; }
function get_stylesheet_directory(): string { return untrailingslashit(ABSPATH) . '/wp-content/themes/land76wp'; }

$registry_functions = array(
    'land76wp_is_supported_case_template',
    'land76wp_service_hub_registry',
    'land76wp_service_hub_by_service_id',
    'land76wp_service_hub_by_grouping_slug',
    'land76wp_has_managed_service_hub_owner',
    'land76wp_claims_managed_service_hub_post',
    'land76wp_managed_page_contract',
    'land76wp_service_hub_for_post',
    'land76wp_is_managed_service_hub_post',
    'land76wp_service_hub_schema_context',
    'land76wp_service_hub_managed_meta_value',
    'land76wp_service_hub_filter_managed_title',
    'land76wp_service_hub_filter_managed_description',
    'land76wp_service_hub_filter_managed_canonical',
    'land76wp_service_hub_disable_aioseo_schema',
    'land76wp_service_hub_filter_aioseo_schema_output',
);
if ($scenario === 'present') {
    foreach ($registry_functions as $function) eval('function ' . $function . '(...$args) { return array(); }');
} elseif ($scenario === 'partial') {
    eval('function land76wp_service_hub_registry(...$args) { return array(); }');
}

require_once dirname(__DIR__) . '/land76-release-deployer/land76-release-deployer.php';

$expected = array(
    'A1' => array(
        'wp-content/themes/land76wp/inc/import-service-hubs.php' => hash('sha256', $importer_bytes),
        'wp-content/themes/land76wp/inc/a1-probe.php' => hash('sha256', $probe_bytes),
    ),
    'A2' => array(
        'wp-content/themes/land76wp/inc/service-hub-registry.php' => 'd3529b114146a0a7e510995a372f40e65b6eeef029c957844b37a9a92bff58d0',
    ),
);
$config = array(
    'docroot' => $docroot,
    'storage_root' => $storage,
    'state_file' => $storage . DIRECTORY_SEPARATOR . 'state.json',
    'journal_file' => $storage . DIRECTORY_SEPARATOR . 'journal.json',
    'expected_phases' => $expected,
    'read_option' => static fn(string $key, mixed $default = false): mixed => $default,
    'sync_directory' => static fn(string $directory): bool => true,
    'mode_adapter' => static fn(string $operation, string $path, int $mode): bool => true,
);
$integration_config = new ReflectionProperty(Land76_Release_Deployer::class, 'integration_config');
$checksummed = new ReflectionMethod(Land76_Release_Deployer::class, 'checksummed_document');
$integration_config->setValue(null, $config);
try {
    $state = array(
        'schema' => 1,
        'release_id' => 'bridge-lifecycle-test',
        'generation' => 1,
        'backup' => array('verified' => false),
        'phases' => array(
            'A1' => array('status' => 'applied'),
            'A2' => array('status' => $scenario === 'a2-noop' ? 'applied' : 'pending'),
        ),
        'stage_verified' => false,
        'last_error' => '',
        'last_committed_txid' => '',
    );
    $state = $checksummed->invoke(null, $state, 'state');
    file_put_contents($config['state_file'], json_encode($state, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), LOCK_EX);

    $error = '';
    try {
        Land76_Release_Deployer::bootstrap_importer();
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
} finally {
    $integration_config->setValue(null, null);
}

$imported = !empty($GLOBALS['land76_bridge_imported']);
$ok = match ($scenario) {
    'present', 'absent' => $error === '' && $imported,
    'partial' => $error === 'SERVICE_HUB_REGISTRY_PARTIAL' && !$imported,
    'a2-noop' => $error === '' && !$imported,
    'a1-drift' => $error === 'A1_LIVE_HASH_MISMATCH' && !$imported,
};
if (!$ok) {
    fwrite(STDERR, 'FAIL scenario=' . $scenario . ' error=' . $error . ' imported=' . ($imported ? 'yes' : 'no') . "\n");
    exit(1);
}
fwrite(STDOUT, 'PASS bridge ' . $scenario . "\n");
