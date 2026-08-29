<?php
declare(strict_types=1);

define('ABSPATH', __DIR__ . '/wordpress/');
define('ARRAY_A', 'ARRAY_A');
$registered_hooks = array();
function add_action($hook, $callback, $priority = 10) { global $registered_hooks; $registered_hooks[$hook][] = $callback; }
$activation_callbacks = array();
function register_activation_hook($file, $callback) { global $activation_callbacks; $activation_callbacks[] = $callback; }
function wp_json_encode($value) { return json_encode($value, JSON_UNESCAPED_SLASHES); }
function wp_mkdir_p($path) { return is_dir($path) || mkdir($path, 0700, true); }
function wp_upload_dir() { return array('basedir' => sys_get_temp_dir()); }
function untrailingslashit($path) { return rtrim($path, '/\\'); }
function current_user_can($cap) { return $cap === 'manage_options'; }
function is_admin() { return true; }
function get_stylesheet_directory() { return ABSPATH . 'wp-content/themes/land76wp'; }
function wp_verify_nonce($nonce, $action) { return $nonce === 'valid:' . $action; }
function get_option($key, $default = false) { global $test_options; return $test_options[$key] ?? $default; }
function update_option($key, $value, $autoload = false) { global $test_options; $test_options[$key] = $value; return true; }
function esc_html__($text, $domain = '') { return (string)$text; }
function esc_html($text) { return htmlspecialchars((string)$text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function esc_url($url) { return (string)$url; }
function admin_url($path = '') { return '/wp-admin/' . ltrim((string)$path, '/'); }
function wp_nonce_field($action) { echo '<input type="hidden" value="' . esc_html($action) . '">'; }
function submit_button($text) { echo '<button>' . esc_html($text) . '</button>'; }
function wp_die($message, $status = 500) { throw new RuntimeException((string)$message, (int)$status); }

require_once dirname(__DIR__) . '/land76-release-deployer/land76-release-deployer.php';

$failures = array();
$assertions = 0;
function check($condition, string $message): void { global $failures, $assertions; $assertions++; if (!$condition) { $failures[] = $message; } }
function throws(callable $callback, string $message): void { try { $callback(); check(false, $message); } catch (RuntimeException $ignored) {} }
function remove_test_tree(string $path): void {
    if (!is_dir($path)) return;
    $items = scandir($path);
    if (!is_array($items)) return;
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        $target = $path . DIRECTORY_SEPARATOR . $item;
        is_dir($target) ? remove_test_tree($target) : @unlink($target);
    }
    @rmdir($path);
}
function lint_gate_result(array $process_result): array {
    $stage_file = tempnam(sys_get_temp_dir(), 'land76-stage-');
    $live_marker = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-live-' . bin2hex(random_bytes(8));
    $journal = array();
    $error_message = '';
    try {
        if (!is_string($stage_file) || file_put_contents($stage_file, '<?php syntax error') === false) {
            throw new RuntimeException('TEST_STAGE_SETUP_FAILED');
        }
        $gate = new ReflectionMethod(Land76_Release_Deployer::class, 'with_php_lint_gate');
        $gate->invoke(
            null,
            array('wp-content/themes/land76wp/inc/import-service-hubs.php' => $stage_file),
            function () use (&$journal, $live_marker): void {
                $journal[] = 'wp-content/themes/land76wp/inc/import-service-hubs.php';
                file_put_contents($live_marker, 'mutated');
            },
            fn(array $command, int $timeout_seconds): array => $process_result
        );
    } catch (Throwable $error) {
        $error_message = $error->getMessage();
    } finally {
        if (is_string($stage_file)) @unlink($stage_file);
        $live_exists = file_exists($live_marker);
        @unlink($live_marker);
    }
    return array('error' => $error_message, 'journal' => $journal, 'live_exists' => $live_exists);
}
check(isset($registered_hooks['admin_post_land76_release_apply']), 'admin post apply hook registers even before admin menu API is loaded');
check(isset($registered_hooks['admin_post_land76_release_backup']), 'admin post backup hook registers even before admin menu API is loaded');
check(count($activation_callbacks) === 1, 'activation preflight is registered without frontend storage access');

$activation_root = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-activation-' . bin2hex(random_bytes(8));
$activation_docroot = $activation_root . DIRECTORY_SEPARATOR . 'wordpress';
$activation_storage = $activation_root . DIRECTORY_SEPARATOR . 'storage';
$activation_state_file = $activation_storage . DIRECTORY_SEPARATOR . 'state.json';
$activation_journal_file = $activation_storage . DIRECTORY_SEPARATOR . 'journal.json';
$activation_result = array('message' => '', 'status' => 0);
$activation_integration_config = new ReflectionProperty(Land76_Release_Deployer::class, 'integration_config');
wp_mkdir_p($activation_docroot);
wp_mkdir_p($activation_storage);
try {
    $activation_integration_config->setValue(null, array(
        'docroot' => $activation_docroot,
        'storage_root' => $activation_storage,
        'state_file' => $activation_state_file,
        'journal_file' => $activation_journal_file,
        'expected_phases' => array('A1' => array()),
        'read_option' => fn(string $key, mixed $default = false): mixed => $default,
        'sync_directory' => static function (string $directory): bool {
            throw new RuntimeException('UNTRUSTED_SECRET_CODE');
        },
        'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
    ));
    ($activation_callbacks[0])();
} catch (RuntimeException $error) {
    $activation_result = array('message' => $error->getMessage(), 'status' => $error->getCode());
} finally {
    $activation_integration_config->setValue(null, null);
}
check(
    $activation_result === array('message' => 'ACTIVATION_PREFLIGHT_FAILED', 'status' => 500),
    'registered activation callback exposes only a stable preflight error code'
);
$activation_result = array('message' => '', 'status' => 0);
try {
    $activation_integration_config->setValue(null, array(
        'docroot' => $activation_docroot,
        'storage_root' => $activation_storage,
        'state_file' => $activation_state_file,
        'journal_file' => $activation_journal_file,
        'expected_phases' => array('A1' => array()),
        'read_option' => fn(string $key, mixed $default = false): mixed => $default,
        'sync_directory' => static function (string $directory): bool {
            throw new RuntimeException('activation preflight path C:\\private\\release-secret');
        },
        'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
    ));
    ($activation_callbacks[0])();
} catch (RuntimeException $error) {
    $activation_result = array('message' => $error->getMessage(), 'status' => $error->getCode());
} finally {
    $activation_integration_config->setValue(null, null);
}
check(
    $activation_result === array('message' => 'ACTIVATION_PREFLIGHT_FAILED', 'status' => 500),
    'registered activation callback does not expose a preflight path'
);
$activation_result = array('message' => '', 'status' => 0);
try {
    $activation_integration_config->setValue(null, array(
        'docroot' => $activation_docroot,
        'storage_root' => $activation_storage,
        'state_file' => $activation_state_file,
        'journal_file' => $activation_journal_file,
        'expected_phases' => array('A1' => array()),
        'read_option' => fn(string $key, mixed $default = false): mixed => $default,
        'sync_directory' => static fn(string $directory): bool => false,
        'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
    ));
    ($activation_callbacks[0])();
} catch (RuntimeException $error) {
    $activation_result = array('message' => $error->getMessage(), 'status' => $error->getCode());
} finally {
    $activation_integration_config->setValue(null, null);
}
check(
    $activation_result === array('message' => 'DIRECTORY_SYNC_FAILED', 'status' => 500),
    'registered activation callback preserves an allowlisted preflight failure code'
);
$activation_error_code = new ReflectionMethod(Land76_Release_Deployer::class, 'activation_error_code');
foreach (array(
    'DIRECTORY_SYNC_PIN_LSTAT_FAILED',
    'DIRECTORY_SYNC_PIN_LINK_REFUSED',
    'DIRECTORY_SYNC_PIN_NOT_DIRECTORY',
    'DIRECTORY_SYNC_PIN_OPEN_FAILED',
    'DIRECTORY_SYNC_PIN_FSTAT_FAILED',
    'DIRECTORY_SYNC_PIN_HANDLE_NOT_DIRECTORY',
    'DIRECTORY_SYNC_PIN_IDENTITY_MISMATCH',
    'DIRECTORY_SYNC_VERIFY_LSTAT_FAILED',
    'DIRECTORY_SYNC_VERIFY_LINK_REFUSED',
    'DIRECTORY_SYNC_VERIFY_NOT_DIRECTORY',
    'DIRECTORY_SYNC_VERIFY_IDENTITY_MISMATCH',
    'DIRECTORY_SYNC_VERIFY_HANDLE_FAILED',
) as $diagnostic_code) {
    check(
        $activation_error_code->invoke(null, new RuntimeException($diagnostic_code)) === $diagnostic_code,
        'activation callback preserves safe namespace diagnostic code ' . $diagnostic_code
    );
}
$pin_directory_namespace = new ReflectionMethod(Land76_Release_Deployer::class, 'pin_directory_namespace');
$managed_config = array(
    'docroot' => $activation_docroot,
    'storage_root' => $activation_storage,
    'state_file' => $activation_state_file,
    'journal_file' => $activation_journal_file,
    'expected_phases' => array('A1' => array()),
    'read_option' => fn(string $key, mixed $default = false): mixed => $default,
    'sync_directory' => static fn(string $directory): bool => true,
    'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
);
$missing_pin_error = '';
try {
    $activation_integration_config->setValue(null, $managed_config);
    $pin_directory_namespace->invoke(null, $activation_root . DIRECTORY_SEPARATOR . 'missing-pin-target', 'DIRECTORY_SYNC_TARGET_UNSAFE');
} catch (Throwable $error) {
    $missing_pin_error = $error->getMessage();
} finally {
    $activation_integration_config->setValue(null, null);
}
check($missing_pin_error === 'DIRECTORY_SYNC_PIN_LSTAT_FAILED', 'directory sync pin reports a safe lstat failure class without a path');
$not_directory_pin = tempnam(sys_get_temp_dir(), 'land76-pin-file-');
$not_directory_pin_error = '';
try {
    if (!is_string($not_directory_pin)) throw new RuntimeException('Cannot create namespace pin test file.');
    $activation_integration_config->setValue(null, $managed_config);
    $pin_directory_namespace->invoke(null, $not_directory_pin, 'DIRECTORY_SYNC_TARGET_UNSAFE');
} catch (Throwable $error) {
    $not_directory_pin_error = $error->getMessage();
} finally {
    $activation_integration_config->setValue(null, null);
    if (is_string($not_directory_pin)) @unlink($not_directory_pin);
}
check($not_directory_pin_error === 'DIRECTORY_SYNC_PIN_NOT_DIRECTORY', 'directory sync pin reports a safe node-type failure class without a path');
$managed_nested = $activation_storage . DIRECTORY_SEPARATOR . 'managed' . DIRECTORY_SEPARATOR . 'nested';
wp_mkdir_p($managed_nested);
$namespace_anchor_for = new ReflectionMethod(Land76_Release_Deployer::class, 'namespace_anchor_for');
try {
    $activation_integration_config->setValue(null, $managed_config);
    $storage_parent_anchor = $namespace_anchor_for->invoke(null, dirname($activation_storage));
    $upload_temp_anchor = $namespace_anchor_for->invoke(null, sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-upload-probe');
} finally {
    $activation_integration_config->setValue(null, null);
}
check($storage_parent_anchor === dirname($activation_storage), 'storage creation pins its exact managed parent anchor');
check($upload_temp_anchor === rtrim(sys_get_temp_dir(), '/\\'), 'uploaded archives pin from the PHP temp root');
$managed_pins = array();
try {
    $activation_integration_config->setValue(null, $managed_config);
    $managed_pins = $pin_directory_namespace->invoke(null, $managed_nested, 'MANAGED_PIN_FAILED');
} finally {
    $close_directory_namespace = new ReflectionMethod(Land76_Release_Deployer::class, 'close_directory_namespace');
    $close_directory_namespace->invoke(null, $managed_pins);
    $activation_integration_config->setValue(null, null);
}
check(
    ($managed_pins[0]['path'] ?? null) === $activation_storage,
    'storage namespace pinning starts at the managed storage root instead of a host ancestor'
);
$managed_docroot_pins = array();
try {
    $activation_integration_config->setValue(null, $managed_config);
    $managed_docroot_pins = $pin_directory_namespace->invoke(null, $activation_docroot, 'MANAGED_PIN_FAILED');
} finally {
    $close_directory_namespace->invoke(null, $managed_docroot_pins);
    $activation_integration_config->setValue(null, null);
}
check(
    ($managed_docroot_pins[0]['path'] ?? null) === $activation_docroot,
    'release namespace pinning starts at the managed document root instead of a host ancestor'
);
$outside_managed_error = '';
$outside_managed_root = DIRECTORY_SEPARATOR === '\\' ? substr(__DIR__, 0, 3) : DIRECTORY_SEPARATOR;
try {
    $activation_integration_config->setValue(null, $managed_config);
    $pin_directory_namespace->invoke(null, $outside_managed_root, 'MANAGED_PIN_FAILED');
} catch (Throwable $error) {
    $outside_managed_error = $error->getMessage();
} finally {
    $activation_integration_config->setValue(null, null);
}
check($outside_managed_error === 'MANAGED_PIN_FAILED', 'namespace pinning rejects directories outside managed or upload-temp roots');
check(
    !file_exists($activation_state_file) && !file_exists($activation_journal_file),
    'activation failure does not persist diagnostic state or journal files'
);
remove_test_tree($activation_root);

$expected = array('wp-content/themes/land76wp/a.php' => hash('sha256', 'a'));
check(Land76_Release_Deployer::validate_inventory(array(array('name' => 'wp-content/themes/land76wp/a.php', 'sha256' => hash('sha256', 'a'), 'size' => 1)), $expected) === true, 'exact inventory accepted');
throws(fn() => Land76_Release_Deployer::validate_inventory(array(array('name' => '../wp-config.php', 'sha256' => hash('sha256', 'a'), 'size' => 1)), $expected), 'traversal rejected');
throws(fn() => Land76_Release_Deployer::validate_inventory(array(array('name' => 'wp-content/themes/land76wp/a.php', 'sha256' => hash('sha256', 'a'), 'size' => 1), array('name' => 'wp-content/themes/land76wp/a.php', 'sha256' => hash('sha256', 'a'), 'size' => 1)), $expected), 'duplicate rejected');
throws(fn() => Land76_Release_Deployer::validate_inventory(array(array('name' => 'wp-content/themes/land76wp/a.php', 'sha256' => hash('sha256', 'b'), 'size' => 1)), $expected), 'entry hash rejected');
throws(fn() => Land76_Release_Deployer::validate_upload_name_hash('bad.zip', 'x', array('filename' => 'ok.zip', 'archive_sha256' => 'x')), 'wrong filename rejected');

$state = array('backup' => array('verified' => true), 'phases' => array('A1' => array('status' => 'pending'), 'A2' => array('status' => 'pending'), 'C' => array('status' => 'pending'), 'B' => array('status' => 'pending')));
check(Land76_Release_Deployer::may_apply('A1', $state), 'A1 allowed after backup');
check(!Land76_Release_Deployer::may_apply('A2', $state), 'phase order gate');
$state['phases']['A1']['status'] = 'applied';
check(!Land76_Release_Deployer::may_apply('A2', $state), 'A2 requires explicit Stage checkpoint');
$state['stage_verified'] = true;
check(Land76_Release_Deployer::may_apply('A2', $state), 'A2 unlocked by A1 and Stage checkpoint');
$state['backup']['verified'] = false;
check(!Land76_Release_Deployer::may_apply('A2', $state), 'backup gate');

$manifest = Land76_Release_Deployer::rollback_manifest(array('x.php' => array('exists' => false), 'y.php' => array('exists' => true, 'sha256' => 'abc', 'bytes' => 3, 'mode' => 0644)), 'release-test');
check($manifest['paths']['x.php']['exists'] === false && $manifest['paths']['y.php']['sha256'] === 'abc', 'rollback manifest maps missing and existing files');
check(Land76_Release_Deployer::request_is_authorized(array('REQUEST_METHOD' => 'POST', 'nonce' => 'valid:land76_release_deployer:apply:A1'), 'apply:A1'), 'phase-bound POST nonce accepts exact phase');
check(!Land76_Release_Deployer::request_is_authorized(array('REQUEST_METHOD' => 'POST', 'nonce' => 'valid:land76_release_deployer:apply:A2'), 'apply:A1'), 'phase-bound nonce rejects another phase');
check(!Land76_Release_Deployer::request_is_authorized(array('REQUEST_METHOD' => 'GET', 'nonce' => 'valid:land76_release_deployer:apply:A1'), 'apply:A1'), 'no public endpoint / POST guard');
check(!Land76_Release_Deployer::request_is_authorized(array('REQUEST_METHOD' => 'POST', 'nonce' => 'bad'), 'apply:A1'), 'nonce guard');
check(Land76_Release_Deployer::importer_bootstrap_target() === ABSPATH . 'wp-content/themes/land76wp/inc/import-service-hubs.php', 'admin-only importer bootstrap targets active theme import file');
$frozen = Land76_Release_Deployer::expected();
$default_state = Land76_Release_Deployer::default_state();
$storage_path = new ReflectionMethod(Land76_Release_Deployer::class, 'storage_path');
check($default_state['release_id'] === 'exp76-production-release-20260829-140000-r3', 'R3 uses a distinct frozen production release identity');
check(str_ends_with($storage_path->invoke(null), '.land76-release-deployer-r3'), 'R3 uses isolated protected state and rollback storage');
check(count($frozen['A1']['files']) === 26 && count($frozen['A2']['files']) === 23 && count($frozen['C']['files']) === 1 && count($frozen['B']['files']) === 30, 'frozen inventories contain all 80 verified entries');
check(($frozen['A2']['files']['wp-content/themes/land76wp/page-service-hub-region.php'] ?? null) === 'a32a12a1987db2c7e4f829f24ed63e8ec6249917423357dd5ad59736c7a29432', 'A2 frozen inventory deploys the exact regional service-hub renderer');
check($frozen['A2']['files']['wp-content/themes/land76wp/inc/service-hub-registry.php'] === '87aa0a611cdc9bd62f9b46edfae39274977a13d6863e0d5140cbf923242f99e5', 'vendored bridge registry hash is frozen');
check($frozen['A1']['files']['wp-content/themes/land76wp/inc/import-service-hubs.php'] === '85217effdf3efdd05592ac35c42d7af106fd98e49bdbe7685e914b3413a288bd', 'A1 importer bootstrap hash is frozen');
check(hash_file('sha256', dirname(__DIR__) . '/land76-release-deployer/vendor/service-hub-registry.php') === $frozen['A2']['files']['wp-content/themes/land76wp/inc/service-hub-registry.php'], 'vendored bridge registry is byte-exact A2 content');
$source = file_get_contents(dirname(__DIR__) . '/land76-release-deployer/land76-release-deployer.php');
check(is_string($source) && str_contains($source, ' * Version: 1.0.2'), 'R3 plugin version is frozen');
check(is_string($source) && str_contains($source, "'land76wp_is_supported_case_template'"), 'bridge requires the shared case-template predicate');
check(
    land76wp_is_supported_case_template('casenew.php')
    && land76wp_is_supported_case_template('portfoliopost.php')
    && !land76wp_is_supported_case_template('single.php'),
    'early bridge predicate preserves the exact supported case-template allowlist'
);
check(is_string($source) && str_contains($source, "wp_nonce_field(self::nonce_action('backup'))"), 'backup form uses its action-specific nonce');
check(is_string($source) && str_contains($source, "wp_nonce_field(self::nonce_action('apply', \$phase))"), 'apply form binds nonce to rendered phase');
check(is_string($source) && str_contains($source, "wp_nonce_url(admin_url('admin-post.php?action=land76_release_download'), self::nonce_action('download'))"), 'download link uses a download-specific nonce');

$lint_file = tempnam(sys_get_temp_dir(), 'land76-lint-');
if (is_string($lint_file)) {
    file_put_contents($lint_file, '<?php if (');
    try {
        $lint_status = Land76_Release_Deployer::lint_php(
            array('wp-content/themes/land76wp/inc/import-service-hubs.php' => $lint_file),
            fn(array $command, int $timeout_seconds): array => array('status' => 'ran', 'exit_code' => 0)
        );
        check($lint_status === 'ran', 'successful injected PHP lint returns ran');
    } catch (Throwable $error) {
        check(false, 'successful injected PHP lint returns ran');
    } finally {
        @unlink($lint_file);
    }
} else {
    check(false, 'successful injected PHP lint returns ran');
}

$lint_relative = 'wp-content/themes/land76wp/inc/import-service-hubs.php';
$unavailable = lint_gate_result(array('status' => 'unavailable', 'exit_code' => null));
check(
    $unavailable === array('error' => 'PHP_LINT_UNAVAILABLE:' . $lint_relative, 'journal' => array(), 'live_exists' => false),
    'unavailable process runner hard-stops before journal and live writes with a stable relative error'
);
$timed_out = lint_gate_result(array('status' => 'timeout', 'exit_code' => null));
check(
    $timed_out === array('error' => 'PHP_LINT_TIMEOUT:' . $lint_relative, 'journal' => array(), 'live_exists' => false),
    'timed-out PHP lint hard-stops before journal and live writes with a stable relative error'
);
$nonzero = lint_gate_result(array('status' => 'ran', 'exit_code' => 255));
check(
    $nonzero === array('error' => 'PHP_LINT_FAILED:' . $lint_relative, 'journal' => array(), 'live_exists' => false),
    'nonzero PHP lint hard-stops before journal and live writes with a stable relative error'
);

$runner_timeout = null;
$runner_marker = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-runner-' . bin2hex(random_bytes(8));
$runner_code = 'usleep(1500000); file_put_contents(' . var_export($runner_marker, true) . ', "late");';
$runner_started = microtime(true);
try {
    $process_runner = new ReflectionMethod(Land76_Release_Deployer::class, 'run_process');
    $runner_timeout = $process_runner->invoke(null, array(PHP_BINARY, '-r', $runner_code), 0.02);
} catch (Throwable $error) {
    $runner_timeout = array('status' => 'test-error', 'exit_code' => null);
}
$runner_elapsed = microtime(true) - $runner_started;
usleep(1_700_000);
$runner_wrote_late = file_exists($runner_marker);
@unlink($runner_marker);
check(
    ($runner_timeout['status'] ?? '') === 'timeout' && $runner_elapsed < 0.75 && !$runner_wrote_late,
    'real process runner terminates a PHP lint command without a delayed child side effect'
);

$unknown_lint_file = tempnam(sys_get_temp_dir(), 'land76-unknown-lint-');
$unknown_lint_error = '';
try {
    if (!is_string($unknown_lint_file)) throw new RuntimeException('TEST_LINT_SETUP_FAILED');
    Land76_Release_Deployer::lint_php(
        array('wp-content/themes/land76wp/not-in-frozen-release.php' => $unknown_lint_file),
        fn(array $command, int $timeout_seconds): array => array('status' => 'ran', 'exit_code' => 255)
    );
} catch (Throwable $error) {
    $unknown_lint_error = $error->getMessage();
} finally {
    if (is_string($unknown_lint_file)) @unlink($unknown_lint_file);
}
check(
    $unknown_lint_error === 'PHP_LINT_PATH_INVALID',
    'PHP lint refuses a non-frozen relative path without persisting it'
);

$persist_root = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-persist-' . bin2hex(random_bytes(8));
$persist_docroot = $persist_root . DIRECTORY_SEPARATOR . 'wordpress';
$persist_storage = $persist_root . DIRECTORY_SEPARATOR . 'storage';
wp_mkdir_p($persist_docroot);
wp_mkdir_p($persist_storage);
$persist_state_file = $persist_storage . DIRECTORY_SEPARATOR . 'state.json';
$persist_journal_file = $persist_storage . DIRECTORY_SEPARATOR . 'journal.json';
$persist_state = array(
    'schema' => 1,
    'release_id' => 'lint-persistence-test',
    'generation' => 1,
    'backup' => array('verified' => false),
    'phases' => array('A1' => array('status' => 'pending')),
    'stage_verified' => false,
    'last_error' => '',
    'last_committed_txid' => '',
);
$checksummed_document = new ReflectionMethod(Land76_Release_Deployer::class, 'checksummed_document');
$persist_state = $checksummed_document->invoke(null, $persist_state, 'state');
file_put_contents($persist_state_file, json_encode($persist_state, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
$integration_config = new ReflectionProperty(Land76_Release_Deployer::class, 'integration_config');
$absolute_lint_path = $persist_root . DIRECTORY_SEPARATOR . 'stage' . DIRECTORY_SEPARATOR . 'import-service-hubs.php';
try {
    $integration_config->setValue(null, array(
        'docroot' => $persist_docroot,
        'storage_root' => $persist_storage,
        'state_file' => $persist_state_file,
        'journal_file' => $persist_journal_file,
        'expected_phases' => array('A1' => array($lint_relative => hash('sha256', 'target'))),
        'read_option' => fn(string $key, mixed $default = false): mixed => $default,
        'sync_directory' => fn(string $directory): bool => true,
        'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
    ));
    $record_error = new ReflectionMethod(Land76_Release_Deployer::class, 'record_error');
    $record_error->invoke(null, 'PHP_LINT_FAILED:' . $lint_relative . ':' . $absolute_lint_path);
} finally {
    $integration_config->setValue(null, null);
}
$persisted_state = json_decode((string)file_get_contents($persist_state_file), true);
check(
    is_array($persisted_state) && ($persisted_state['generation'] ?? 0) === 2,
    'record_error durably commits a new checksummed state generation'
);
check(
    is_array($persisted_state)
        && ($persisted_state['last_error'] ?? '') === 'PHP_LINT_FAILED:' . $lint_relative
        && !str_contains((string)file_get_contents($persist_state_file), $absolute_lint_path),
    'persisted lint error contains only its stable code and frozen relative path'
);
remove_test_tree($persist_root);

$ui_root = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-ui-' . bin2hex(random_bytes(8));
$ui_docroot = $ui_root . DIRECTORY_SEPARATOR . 'wordpress';
$ui_storage = $ui_root . DIRECTORY_SEPARATOR . 'storage';
wp_mkdir_p($ui_docroot);
wp_mkdir_p($ui_storage);
$ui_state_file = $ui_storage . DIRECTORY_SEPARATOR . 'state.json';
$ui_state = array(
    'schema' => 1,
    'release_id' => 'lint-ui-test',
    'generation' => 1,
    'backup' => array('verified' => false),
    'phases' => array(
        'A1' => array('status' => 'applied', 'applied_utc' => '2026-08-29T00:00:00+00:00', 'lint' => 'ran'),
        'A2' => array('status' => 'pending'),
        'C' => array('status' => 'pending'),
        'B' => array('status' => 'pending'),
    ),
    'stage_verified' => false,
    'last_error' => '',
    'last_committed_txid' => '',
);
$ui_state = $checksummed_document->invoke(null, $ui_state, 'state');
file_put_contents($ui_state_file, json_encode($ui_state, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
$ui_html = '';
try {
    $integration_config->setValue(null, array(
        'docroot' => $ui_docroot,
        'storage_root' => $ui_storage,
        'state_file' => $ui_state_file,
        'journal_file' => $ui_storage . DIRECTORY_SEPARATOR . 'journal.json',
        'expected_phases' => array('A1' => array(), 'A2' => array(), 'C' => array(), 'B' => array()),
        'read_option' => fn(string $key, mixed $default = false): mixed => $default,
        'sync_directory' => fn(string $directory): bool => true,
        'mode_adapter' => fn(string $operation, string $path, int $mode): bool => true,
    ));
    ob_start();
    Land76_Release_Deployer::page();
    $ui_html = (string)ob_get_clean();
} catch (Throwable $error) {
    if (ob_get_level() > 0) ob_end_clean();
} finally {
    $integration_config->setValue(null, null);
}
check(str_contains($ui_html, 'PHP lint: ran'), 'admin UI displays the recorded PHP lint status');
remove_test_tree($ui_root);

if ($failures) { fwrite(STDERR, implode("\n", $failures) . "\n"); exit(1); }
echo "PASS " . $assertions . " assertions\n";
