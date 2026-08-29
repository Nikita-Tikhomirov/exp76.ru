<?php
declare(strict_types=1);

/**
 * RED integration contract for crash-safe release state.
 *
 * This harness deliberately does not reimplement the deployer. It expects the
 * production class to expose this narrow, private test-only adapter factory:
 *
 * Land76_Release_Deployer::integration_test_adapter(array $config): object
 *
 * The returned object must provide:
 *
 * - reconcile_before_theme_include(): array
 *   Reconcile one checksummed state.json and one checksummed journal.json while
 *   holding the deployer lock. Recovery must finish before theme PHP is loaded.
 *
 * - apply_phase_for_test(string $phase, array $staged_files,
 *                        array $target_state, ?string $failpoint = null): array
 *   Apply real staged files with the production journal/rollback path. The
 *   "final_state_commit" failpoint must make the final durable state commit
 *   fail after destination writes so same-request rollback can be asserted.
 *
 * Factory config keys are: docroot, storage_root, state_file, journal_file,
 * expected_phases, read_option. The read_option callback is intentionally
 * read-only: WordPress options are external invariants (phase B), never a state
 * mirror or fallback.
 *
 * Checksums in these fixtures are lowercase SHA-256 over canonical JSON of the
 * recursively key-sorted document with its top-level checksum field removed.
 * The adapter may reject fixtures if the production checksum contract differs,
 * but it must never accept corrupt state or journal data.
 */

final class Land76_State_Journal_Red_Suite {
    private array $failures = array();
    private int $assertions = 0;

    public function run(string $name, callable $test): void {
        try {
            $test($this);
            fwrite(STDOUT, "PASS {$name}\n");
        } catch (Throwable $error) {
            $this->failures[] = $name . ': ' . $error->getMessage();
            fwrite(STDERR, "RED  {$name}: {$error->getMessage()}\n");
        }
    }

    public function check(bool $condition, string $message): void {
        $this->assertions++;
        if (!$condition) {
            throw new RuntimeException($message);
        }
    }

    public function same(mixed $expected, mixed $actual, string $message): void {
        $this->assertions++;
        if ($expected !== $actual) {
            throw new RuntimeException(
                $message . '; expected=' . self::describe($expected) . '; actual=' . self::describe($actual)
            );
        }
    }

    public function finish(): never {
        if ($this->failures !== array()) {
            fwrite(
                STDERR,
                "\nEXPECTED RED: production state/journal adapter is not implemented.\n" .
                implode("\n", $this->failures) . "\n"
            );
            exit(1);
        }

        fwrite(STDOUT, "PASS {$this->assertions} assertions\n");
        exit(0);
    }

    private static function describe(mixed $value): string {
        $encoded = json_encode($value, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        return is_string($encoded) ? $encoded : get_debug_type($value);
    }
}

function land76_red_remove_tree(string $path): void {
    if (!file_exists($path) && !is_link($path)) {
        return;
    }

    $name = basename($path);
    if (!str_starts_with($name, 'land76-state-red-') && !str_contains($path, 'land76-state-red-')) {
        throw new RuntimeException('Refusing to clean a path outside the isolated RED sandbox.');
    }

    if (!is_dir($path) || is_link($path)) {
        if (!@unlink($path)) {
            throw new RuntimeException('Cannot remove isolated test file.');
        }
        return;
    }

    $items = scandir($path);
    if (!is_array($items)) {
        throw new RuntimeException('Cannot enumerate isolated test directory.');
    }

    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }
        land76_red_remove_tree($path . DIRECTORY_SEPARATOR . $item);
    }

    if (!@rmdir($path)) {
        throw new RuntimeException('Cannot remove isolated test directory.');
    }
}

function land76_red_mkdir(string $path): void {
    if (!is_dir($path) && !mkdir($path, 0700, true) && !is_dir($path)) {
        throw new RuntimeException('Cannot create isolated test directory.');
    }
}

function land76_red_canonicalize(mixed $value): mixed {
    if (!is_array($value)) {
        return $value;
    }

    if (array_is_list($value)) {
        return array_map('land76_red_canonicalize', $value);
    }

    ksort($value, SORT_STRING);
    foreach ($value as $key => $item) {
        $value[$key] = land76_red_canonicalize($item);
    }
    return $value;
}

function land76_red_json(array $document): string {
    $encoded = json_encode(
        land76_red_canonicalize($document),
        JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE
    );
    if (!is_string($encoded)) {
        throw new RuntimeException('Cannot encode canonical RED fixture JSON.');
    }
    return $encoded;
}

function land76_red_checksummed(array $document): array {
    unset($document['checksum']);
    $document['checksum'] = hash('sha256', land76_red_json($document));
    return $document;
}

function land76_red_write_json(string $path, array $document): void {
    $bytes = land76_red_json($document);
    if (file_put_contents($path, $bytes, LOCK_EX) !== strlen($bytes)) {
        throw new RuntimeException('Cannot write isolated RED fixture JSON.');
    }
}

function land76_red_read_checked_json(string $path): array {
    $bytes = file_get_contents($path);
    $document = is_string($bytes) ? json_decode($bytes, true) : null;
    if (!is_array($document) || !isset($document['checksum']) || !is_string($document['checksum'])) {
        throw new RuntimeException('Recovered state is not a checksummed JSON object.');
    }

    $checksum = $document['checksum'];
    unset($document['checksum']);
    if (!hash_equals($checksum, hash('sha256', land76_red_json($document)))) {
        throw new RuntimeException('Recovered state checksum is invalid.');
    }
    $document['checksum'] = $checksum;
    return $document;
}

$land76_red_root = sys_get_temp_dir() . DIRECTORY_SEPARATOR . 'land76-state-red-' . bin2hex(random_bytes(8));
$land76_red_docroot = $land76_red_root . DIRECTORY_SEPARATOR . 'wordpress';
$land76_red_storage = $land76_red_root . DIRECTORY_SEPARATOR . 'storage';
land76_red_mkdir($land76_red_docroot);
land76_red_mkdir($land76_red_storage);
register_shutdown_function(static function () use ($land76_red_root): void {
    if (file_exists($land76_red_root) || is_link($land76_red_root)) {
        land76_red_remove_tree($land76_red_root);
    }
});

define('ABSPATH', $land76_red_docroot . DIRECTORY_SEPARATOR);
define('ARRAY_A', 'ARRAY_A');
define('LAND76_RELEASE_DEPLOYER_INTEGRATION_TEST', true);

$land76_red_hooks = array();
$land76_red_activation_callbacks = array();
$land76_red_options = array(
    'land76_service_hubs_active_release_id' => 'service-hubs-2026-08-28',
);
$land76_red_option_writes = array();

function add_action($hook, $callback, $priority = 10): void {
    $GLOBALS['land76_red_hooks'][$hook][] = array($callback, $priority);
}
function register_activation_hook($file, $callback): void {
    $GLOBALS['land76_red_activation_callbacks'][] = array($file, $callback);
}
function wp_json_encode($value): string|false {
    return json_encode($value, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
}
function wp_mkdir_p($path): bool {
    return is_dir($path) || mkdir($path, 0700, true);
}
function wp_upload_dir(): array {
    return array('basedir' => sys_get_temp_dir());
}
function untrailingslashit($path): string {
    return rtrim((string)$path, '/\\');
}
function current_user_can($capability): bool {
    return $capability === 'manage_options';
}
function is_admin(): bool {
    return false;
}
function get_stylesheet_directory(): string {
    return ABSPATH . 'wp-content/themes/land76wp';
}
function wp_verify_nonce($nonce, $action): bool {
    return $nonce === 'valid:' . $action;
}
function esc_html__($message, $domain = ''): string {
    return (string)$message;
}
function wp_die($message, $status = 500): never {
    throw new RuntimeException('WP_DIE:' . (string)$status . ':' . (string)$message);
}
function get_option($key, $default = false): mixed {
    return $GLOBALS['land76_red_options'][$key] ?? $default;
}
function update_option($key, $value, $autoload = false): bool {
    $GLOBALS['land76_red_option_writes'][] = array($key, $value, $autoload);
    $GLOBALS['land76_red_options'][$key] = $value;
    return true;
}

require_once dirname(__DIR__) . '/land76-release-deployer/land76-release-deployer.php';

/**
 * Build a complete real-filesystem fixture: a docroot, a storage directory,
 * an external manifest, and a real rollback ZIP containing byte-identical
 * manifest and baseline file data.
 */
function land76_red_fixture(string $phase = 'A1', int $file_count = 1, ?callable $read_option = null): array {
    $docroot = untrailingslashit(ABSPATH);
    $storage = $GLOBALS['land76_red_storage'];

    foreach (array($docroot, $storage) as $path) {
        if (file_exists($path)) {
            land76_red_remove_tree($path);
        }
        land76_red_mkdir($path);
    }

    if ($file_count < 1) throw new RuntimeException('Fixture requires at least one path.');
    $relative_paths = array();
    $live_files = array();
    $staged_files = array();
    $baselines = array();
    $targets = array();
    $records = array();
    $expected_files = array();
    for ($index = 1; $index <= $file_count; $index++) {
        $relative = $file_count === 1
            ? 'wp-content/themes/land76wp/recovery-probe.txt'
            : 'wp-content/themes/land76wp/phase-' . strtolower($phase) . '/probe-' . $index . '.txt';
        $live = $docroot . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $relative);
        $stage = $storage . DIRECTORY_SEPARATOR . 'staged-' . strtolower($phase) . '-' . $index . '.txt';
        $baseline = 'baseline-before-release-' . $index . "\n";
        $target = 'target-after-release-' . $index . "\n";
        land76_red_mkdir(dirname($live));
        if (file_put_contents($live, $baseline, LOCK_EX) !== strlen($baseline)) throw new RuntimeException('Cannot write live baseline fixture.');
        if (file_put_contents($stage, $target, LOCK_EX) !== strlen($target)) throw new RuntimeException('Cannot write staged target fixture.');
        $relative_paths[] = $relative;
        $live_files[$relative] = $live;
        $staged_files[$relative] = $stage;
        $baselines[$relative] = $baseline;
        $targets[$relative] = $target;
        $records[$relative] = array(
            'exists' => true,
            'sha256' => hash('sha256', $baseline),
            'bytes' => strlen($baseline),
            'mode' => fileperms($live) & 0777,
        );
        $expected_files[$relative] = hash('sha256', $target);
    }

    $manifest = array(
        'schema' => 1,
        'release_id' => 'state-journal-red-release',
        'created_utc' => '2026-08-29T00:00:00+00:00',
        'expected_paths' => $relative_paths,
        'paths' => $records,
    );
    $manifest_bytes = land76_red_json($manifest);
    $manifest_path = $storage . DIRECTORY_SEPARATOR . 'rollback-manifest.json';
    if (file_put_contents($manifest_path, $manifest_bytes, LOCK_EX) !== strlen($manifest_bytes)) {
        throw new RuntimeException('Cannot write external rollback manifest fixture.');
    }

    if (!class_exists('ZipArchive')) {
        throw new RuntimeException('ZipArchive is required for the real rollback integration fixture.');
    }
    $zip_path = $storage . DIRECTORY_SEPARATOR . 'rollback.zip';
    $zip = new ZipArchive();
    if ($zip->open($zip_path, ZipArchive::CREATE | ZipArchive::EXCL) !== true) {
        throw new RuntimeException('Cannot create real rollback ZIP fixture.');
    }
    try {
        foreach ($baselines as $relative => $baseline) {
            if (!$zip->addFromString('files/' . $relative, $baseline)) {
                throw new RuntimeException('Cannot add baseline data to rollback ZIP fixture.');
            }
        }
        if (!$zip->addFromString('rollback-manifest.json', $manifest_bytes)) {
            throw new RuntimeException('Cannot add manifest to rollback ZIP fixture.');
        }
    } finally {
        if (!$zip->close()) {
            throw new RuntimeException('Cannot finalize real rollback ZIP fixture.');
        }
    }

    $state = land76_red_checksummed(array(
        'schema' => 1,
        'release_id' => 'state-journal-red-release',
        'generation' => 1,
        'backup' => array(
            'verified' => true,
            'zip_basename' => basename($zip_path),
            'zip_bytes' => filesize($zip_path),
            'zip_sha256' => hash_file('sha256', $zip_path),
            'manifest_basename' => basename($manifest_path),
            'manifest_bytes' => filesize($manifest_path),
            'manifest_sha256' => hash_file('sha256', $manifest_path),
        ),
        'phases' => array($phase => array('status' => 'pending')),
        'stage_verified' => false,
        'last_committed_txid' => '',
    ));

    $txid = 'tx-' . bin2hex(random_bytes(8));
    $target_state = $state;
    unset($target_state['checksum']);
    $target_state['generation'] = 2;
    $target_state['phases'][$phase] = array('status' => 'applied');
    $target_state['last_committed_txid'] = $txid;
    $target_state = land76_red_checksummed($target_state);

    $journal = land76_red_checksummed(array(
        'schema' => 1,
        'release_id' => 'state-journal-red-release',
        'txid' => $txid,
        'phase' => $phase,
        'base_state' => $state,
        'target_state' => $target_state,
        'backup_sha256' => hash_file('sha256', $zip_path),
        'attempted_paths' => $relative_paths,
        'created_dirs' => array(),
        'step' => 'applying',
    ));

    return array(
        'docroot' => $docroot,
        'storage' => $storage,
        'phase' => $phase,
        'relative' => $relative_paths[0],
        'relative_paths' => $relative_paths,
        'live' => $live_files[$relative_paths[0]],
        'live_files' => $live_files,
        'stage' => $staged_files[$relative_paths[0]],
        'staged_files' => $staged_files,
        'baseline' => $baselines[$relative_paths[0]],
        'baselines' => $baselines,
        'target' => $targets[$relative_paths[0]],
        'targets' => $targets,
        'expected_files' => $expected_files,
        'read_option' => $read_option ?? static fn(string $key, mixed $default = false): mixed => get_option($key, $default),
        'state_file' => $storage . DIRECTORY_SEPARATOR . 'state.json',
        'journal_file' => $storage . DIRECTORY_SEPARATOR . 'journal.json',
        'state' => $state,
        'target_state' => $target_state,
        'journal' => $journal,
    );
}

function land76_red_adapter(array $fixture): object {
    if (!method_exists('Land76_Release_Deployer', 'integration_test_adapter')) {
        throw new RuntimeException(
            'MISSING_API Land76_Release_Deployer::integration_test_adapter(array); ' .
            'see the adapter contract at the top of this file'
        );
    }

    $factory = new ReflectionMethod(Land76_Release_Deployer::class, 'integration_test_adapter');
    $config = array(
        'docroot' => $fixture['docroot'],
        'storage_root' => $fixture['storage'],
        'state_file' => $fixture['state_file'],
        'journal_file' => $fixture['journal_file'],
        'expected_phases' => array($fixture['phase'] => $fixture['expected_files']),
        'read_option' => $fixture['read_option'],
        'sync_directory' => $fixture['sync_directory'] ?? static fn(string $directory): bool => true,
        'mode_adapter' => $fixture['mode_adapter'] ?? static fn(string $operation, string $path, int $mode): bool => true,
    );
    foreach (array('before_destination_rename', 'before_namespace_mutation', 'before_state_rename', 'before_journal_clear', 'after_backup_hashes', 'after_lock_acquired') as $callback) {
        if (isset($fixture[$callback])) $config[$callback] = $fixture[$callback];
    }
    $adapter = $factory->invoke(null, $config);

    foreach (array('reconcile_before_theme_include', 'apply_phase_for_test') as $method) {
        if (!is_object($adapter) || !method_exists($adapter, $method)) {
            throw new RuntimeException('MISSING_API integration adapter::' . $method . '()');
        }
    }
    return $adapter;
}

function land76_red_rebuild_backup(array $fixture, callable $mutate_manifest): array {
    $manifest_bytes = file_get_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json');
    $manifest = is_string($manifest_bytes) ? json_decode($manifest_bytes, true) : null;
    if (!is_array($manifest)) throw new RuntimeException('Cannot read manifest fixture for mutation.');
    $manifest = $mutate_manifest($manifest);
    if (!is_array($manifest)) throw new RuntimeException('Manifest mutator must return an array.');
    $manifest_bytes = land76_red_json($manifest);
    $manifest_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json';
    file_put_contents($manifest_path, $manifest_bytes, LOCK_EX);

    $zip_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip';
    if (!@unlink($zip_path)) throw new RuntimeException('Cannot replace rollback ZIP fixture.');
    $zip = new ZipArchive();
    if ($zip->open($zip_path, ZipArchive::CREATE | ZipArchive::EXCL) !== true) throw new RuntimeException('Cannot rebuild rollback ZIP fixture.');
    try {
        foreach ($fixture['baselines'] as $path => $baseline) {
            if (empty($manifest['paths'][$path]['exists'])) continue;
            if (!$zip->addFromString('files/' . $path, $baseline)) throw new RuntimeException('Cannot rebuild rollback data member.');
        }
        if (!$zip->addFromString('rollback-manifest.json', $manifest_bytes)) throw new RuntimeException('Cannot rebuild rollback manifest member.');
    } finally {
        if (!$zip->close()) throw new RuntimeException('Cannot close rebuilt rollback ZIP fixture.');
    }

    $state = $fixture['state'];
    unset($state['checksum']);
    $state['backup'] = array(
        'verified' => true,
        'zip_basename' => basename($zip_path),
        'zip_bytes' => filesize($zip_path),
        'zip_sha256' => hash_file('sha256', $zip_path),
        'manifest_basename' => basename($manifest_path),
        'manifest_bytes' => filesize($manifest_path),
        'manifest_sha256' => hash_file('sha256', $manifest_path),
    );
    $state = land76_red_checksummed($state);
    $target_state = $fixture['target_state'];
    unset($target_state['checksum']);
    $target_state['backup'] = $state['backup'];
    $target_state = land76_red_checksummed($target_state);
    $journal = $fixture['journal'];
    unset($journal['checksum']);
    $journal['base_state'] = $state;
    $journal['target_state'] = $target_state;
    $journal['backup_sha256'] = $state['backup']['zip_sha256'];
    $journal = land76_red_checksummed($journal);
    return array_replace($fixture, array(
        'manifest' => $manifest,
        'state' => $state,
        'target_state' => $target_state,
        'journal' => $journal,
    ));
}

function land76_red_with_config(array $fixture, callable $operation): mixed {
    $property = new ReflectionProperty(Land76_Release_Deployer::class, 'integration_config');
    $config = array(
        'docroot' => $fixture['docroot'],
        'storage_root' => $fixture['storage'],
        'state_file' => $fixture['state_file'],
        'journal_file' => $fixture['journal_file'],
        'expected_phases' => array($fixture['phase'] => $fixture['expected_files']),
        'read_option' => $fixture['read_option'],
        'sync_directory' => $fixture['sync_directory'] ?? static fn(string $directory): bool => true,
        'mode_adapter' => $fixture['mode_adapter'] ?? static fn(string $operation, string $path, int $mode): bool => true,
    );
    foreach (array('before_destination_rename', 'before_namespace_mutation', 'before_state_rename', 'before_journal_clear', 'after_backup_hashes', 'after_lock_acquired') as $callback) {
        if (isset($fixture[$callback])) $config[$callback] = $fixture[$callback];
    }
    $property->setValue(null, $config);
    try { return $operation(); }
    finally { $property->setValue(null, null); }
}

function land76_red_invoke_private(string $method, array $arguments = array()): mixed {
    $reflection = new ReflectionMethod(Land76_Release_Deployer::class, $method);
    return $reflection->invokeArgs(null, $arguments);
}

function land76_red_restore_swapped_parent(string $parent, string $old_parent): void {
    if (file_exists($parent) || is_link($parent)) land76_red_remove_tree($parent);
    if (!@rename($old_parent, $parent)) throw new RuntimeException('Cannot restore swapped namespace fixture: ' . $parent);
}

function land76_red_swap_parent(string $parent, callable $populate_replacement): string {
    $old_parent = $parent . '.pinned-' . bin2hex(random_bytes(4));
    if (!@rename($parent, $old_parent)) throw new RuntimeException('Cannot move checked namespace fixture: ' . $parent);
    land76_red_mkdir($parent);
    $populate_replacement($parent);
    return $old_parent;
}

$suite = new Land76_State_Journal_Red_Suite();

$suite->run('integration adapter factory is a private test-only seam', static function (Land76_State_Journal_Red_Suite $t): void {
    $factory = new ReflectionMethod(Land76_Release_Deployer::class, 'integration_test_adapter');
    $t->check($factory->isPrivate(), 'integration adapter must not add a public production API');
});

$suite->run('plugins_loaded registers the recovery and request-lock gate before theme bootstrap', static function (Land76_State_Journal_Red_Suite $t): void {
    $registrations = $GLOBALS['land76_red_hooks']['plugins_loaded'] ?? array();
    $matches = array_filter($registrations, static function (array $registration): bool {
        $callback = $registration[0] ?? null;
        return is_array($callback) && ($callback[0] ?? null) === Land76_Release_Deployer::class && ($callback[1] ?? null) === 'early_recovery' && ($registration[1] ?? null) === 1;
    });
    $t->same(1, count($matches), 'early recovery/lock gate must be registered exactly once at plugins_loaded priority 1');
});

$suite->run('corrupt state without journal hard-stops before theme', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    file_put_contents($fixture['state_file'], '{"schema":1,"checksum":');
    $adapter = land76_red_adapter($fixture);

    $failed_closed = false;
    try {
        $adapter->reconcile_before_theme_include();
    } catch (Throwable $error) {
        $failed_closed = true;
    }
    $t->check($failed_closed, 'corrupt state without a journal must hard-stop');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'hard-stop must not mutate live data');
    $t->check(!file_exists($fixture['journal_file']), 'hard-stop must not invent a journal');
});

$suite->run('corrupt state plus valid journal restores base state', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    file_put_contents($fixture['state_file'], '{truncated');
    land76_red_write_json($fixture['journal_file'], $fixture['journal']);
    file_put_contents($fixture['live'], $fixture['target'], LOCK_EX);
    $adapter = land76_red_adapter($fixture);

    $reconciled = $adapter->reconcile_before_theme_include();
    $t->same($fixture['state'], $reconciled, 'journal base_state must be authoritative during rollback');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'base state must be restored durably');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'attempted live file must be restored from ZIP');
    $t->check(!file_exists($fixture['journal_file']), 'verified recovery must remove the journal');
});

$suite->run('crash after rename recovers before simulated theme include', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    land76_red_write_json($fixture['journal_file'], $fixture['journal']);
    file_put_contents($fixture['live'], $fixture['target'], LOCK_EX);
    $adapter = land76_red_adapter($fixture);

    $adapter->reconcile_before_theme_include();
    $probe_path = var_export($fixture['live'], true);
    $theme_bootstrap = $fixture['docroot'] . DIRECTORY_SEPARATOR . 'wp-content' . DIRECTORY_SEPARATOR . 'themes' . DIRECTORY_SEPARATOR . 'land76wp' . DIRECTORY_SEPARATOR . 'functions.php';
    $theme_code = '<?php $GLOBALS["land76_theme_observed"] = file_get_contents(' . $probe_path . ');';
    file_put_contents($theme_bootstrap, $theme_code, LOCK_EX);
    require $theme_bootstrap;

    $t->same($fixture['baseline'], $GLOBALS['land76_theme_observed'] ?? null, 'theme include must observe recovered baseline');
    $t->check(!file_exists($fixture['journal_file']), 'pre-theme recovery must finish the journal');
});

$suite->run('committed txid and exact live hashes finalize journal', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $journal = $fixture['journal'];
    unset($journal['checksum']);
    $journal['step'] = 'commit_ready';
    $journal = land76_red_checksummed($journal);
    land76_red_write_json($fixture['state_file'], $fixture['target_state']);
    land76_red_write_json($fixture['journal_file'], $journal);
    file_put_contents($fixture['live'], $fixture['target'], LOCK_EX);
    $adapter = land76_red_adapter($fixture);

    $reconciled = $adapter->reconcile_before_theme_include();
    $t->same($fixture['target_state'], $reconciled, 'matching committed target state must win');
    $t->same($fixture['target'], file_get_contents($fixture['live']), 'committed live file must not be rolled back');
    $t->check(!file_exists($fixture['journal_file']), 'committed journal must be finalized idempotently');
});

$suite->run('final state commit failure rolls back in the same request', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);

    $failed = false;
    try {
        $adapter->apply_phase_for_test(
            'A1',
            array($fixture['relative'] => $fixture['stage']),
            $fixture['target_state'],
            'final_state_commit'
        );
    } catch (Throwable $error) {
        $failed = true;
    }

    $t->check($failed, 'injected final state commit failure must escape as a failure');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'same-request rollback must restore the live file');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'same-request rollback must retain base state');
    $t->check(!file_exists($fixture['journal_file']), 'successful same-request rollback must clear the journal');
    $t->same(array(), $GLOBALS['land76_red_option_writes'], 'state/journal recovery must not mirror deployer state into WordPress options');
});

$suite->run('phase B invariant drift before first write rolls back without committing', static function (Land76_State_Journal_Red_Suite $t): void {
    $reads = 0;
    $fixture = land76_red_fixture('B', 3, static function (string $key, mixed $default = false) use (&$reads): mixed {
        $reads++;
        return $reads === 1 ? 'service-hubs-2026-08-28' : 'drifted-release';
    });
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'phase B must fail on the first pre-write recheck');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'no phase B destination may remain changed');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'phase B drift must retain base state');
    $t->check(!file_exists($fixture['journal_file']), 'same-request rollback must clear the phase B journal');
});

$suite->run('phase B invariant is the final gate after backup reverify and before rename', static function (Land76_State_Journal_Red_Suite $t): void {
    $option_value = 'service-hubs-2026-08-28';
    $backup_rechecks = 0;
    $renames = 0;
    $fixture = land76_red_fixture('B', 3, static function (string $key, mixed $default = false) use (&$option_value): mixed {
        return $option_value;
    });
    $fixture['after_backup_hashes'] = static function () use (&$backup_rechecks, &$option_value): void {
        $backup_rechecks++;
        if ($backup_rechecks === 2) $option_value = 'drifted-release';
    };
    $fixture['before_destination_rename'] = static function (string $temp) use (&$renames): void {
        if (str_contains(basename($temp), '.land76-apply-')) $renames++;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'drift introduced during pre-write backup reverify must fail the request');
    $t->same(0, $renames, 'no destination rename may occur after backup reverify changes the phase B invariant');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'pre-rename phase B drift must leave every destination at baseline');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'pre-rename phase B drift must retain base state');
    $t->check(!file_exists($fixture['journal_file']), 'pre-rename phase B drift rollback must clear the journal');
});

$suite->run('phase B invariant runs inside atomic write after the final pre-rename callback', static function (Land76_State_Journal_Red_Suite $t): void {
    $option_value = 'service-hubs-2026-08-28';
    $drift_injected = false;
    $forbidden_publish = false;
    $fixture = land76_red_fixture('B', 2, static function (string $key, mixed $default = false) use (&$option_value): mixed {
        return $option_value;
    });
    $fixture['before_destination_rename'] = static function (string $temp) use (&$option_value, &$drift_injected): void {
        if (!$drift_injected && str_contains(basename($temp), '.land76-apply-')) {
            $drift_injected = true;
            $option_value = 'drifted-release';
        }
    };
    $fixture['sync_directory'] = static function (string $directory) use (&$fixture, &$forbidden_publish): bool {
        foreach ($fixture['live_files'] as $path => $live) {
            if (is_file($live) && file_get_contents($live) === $fixture['targets'][$path]) $forbidden_publish = true;
        }
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'final atomic pre-rename drift must fail the request');
    $t->check(!$forbidden_publish, 'no target inode may be published after the final pre-rename callback drifts B');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'atomic final gate must preserve baseline for ' . $path);
});

$suite->run('phase B invariant gates commit-ready journal inside its durable rename', static function (Land76_State_Journal_Red_Suite $t): void {
    $option_value = 'service-hubs-2026-08-28';
    $drift_injected = false;
    $commit_ready_published = false;
    $fixture = land76_red_fixture('B', 2, static function (string $key, mixed $default = false) use (&$option_value): mixed {
        return $option_value;
    });
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$option_value, &$drift_injected, &$fixture): void {
        if ($drift_injected || $operation !== 'durable_rename' || $path !== $fixture['journal_file']) return;
        $temp = dirname($path) . DIRECTORY_SEPARATOR . '.' . basename($path) . '.write.tmp';
        $document = is_file($temp) ? json_decode((string)file_get_contents($temp), true) : null;
        if (!is_array($document) || ($document['step'] ?? null) !== 'commit_ready') return;
        $drift_injected = true;
        $option_value = 'drifted-release';
    };
    $fixture['sync_directory'] = static function (string $directory) use (&$fixture, &$commit_ready_published): bool {
        if ($directory !== $fixture['storage'] || !is_file($fixture['journal_file'])) return true;
        $journal = json_decode((string)file_get_contents($fixture['journal_file']), true);
        if (is_array($journal) && ($journal['step'] ?? null) === 'commit_ready') $commit_ready_published = true;
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check($drift_injected, 'commit-ready journal test must inject drift at its durable pre-rename callback');
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'commit-ready journal pre-rename drift must fail the request');
    $t->check(!$commit_ready_published, 'commit-ready journal must never be published after its pre-rename callback drifts B');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'commit-ready journal drift must retain the base generation');
    $t->check(!file_exists($fixture['journal_file']), 'commit-ready journal drift rollback must clear the applying journal');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'commit-ready journal drift must roll back ' . $path);
});

$suite->run('phase B invariant runs inside durable state write immediately before state rename', static function (Land76_State_Journal_Red_Suite $t): void {
    $option_value = 'service-hubs-2026-08-28';
    $drift_injected = false;
    $forbidden_state_commit = false;
    $fixture = land76_red_fixture('B', 2, static function (string $key, mixed $default = false) use (&$option_value): mixed {
        return $option_value;
    });
    $fixture['before_state_rename'] = static function () use (&$option_value, &$drift_injected): void {
        if (!$drift_injected) {
            $drift_injected = true;
            $option_value = 'drifted-release';
        }
    };
    $fixture['sync_directory'] = static function (string $directory) use (&$fixture, &$forbidden_state_commit): bool {
        if (!is_file($fixture['state_file'])) return true;
        $state = json_decode((string)file_get_contents($fixture['state_file']), true);
        if (is_array($state) && ($state['checksum'] ?? null) === $fixture['target_state']['checksum']) $forbidden_state_commit = true;
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'state pre-rename drift must fail the request');
    $t->check(!$forbidden_state_commit, 'target state must never be renamed after the state pre-rename drift callback');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'state pre-rename drift must retain the base generation');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'state pre-rename drift must roll back ' . $path);
});

$suite->run('phase B invariant is the final operation before journal unlink', static function (Land76_State_Journal_Red_Suite $t): void {
    $option_value = 'service-hubs-2026-08-28';
    $drift_injected = false;
    $forbidden_clear = false;
    $fixture = land76_red_fixture('B', 2, static function (string $key, mixed $default = false) use (&$option_value): mixed {
        return $option_value;
    });
    $fixture['before_journal_clear'] = static function () use (&$option_value, &$drift_injected): void {
        if (!$drift_injected) {
            $drift_injected = true;
            $option_value = 'drifted-release';
        }
    };
    $fixture['sync_directory'] = static function (string $directory) use (&$fixture, &$forbidden_clear): bool {
        if ($directory !== $fixture['storage'] || file_exists($fixture['journal_file']) || !is_file($fixture['state_file'])) return true;
        $state = json_decode((string)file_get_contents($fixture['state_file']), true);
        if (is_array($state) && ($state['checksum'] ?? null) === $fixture['target_state']['checksum']) $forbidden_clear = true;
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'journal final pre-unlink drift must fail the request');
    $t->check(!$forbidden_clear, 'commit-ready journal must not be unlinked while target state and drifted B are live');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'journal pre-unlink drift must restore base state');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'journal pre-unlink drift must restore ' . $path);
});

$suite->run('atomic state and journal final gates abort before their syscalls without recovery', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $atomic_callback_ran = false;
    $fixture['before_destination_rename'] = static function () use (&$atomic_callback_ran): void { $atomic_callback_ran = true; };
    $atomic_error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            land76_red_invoke_private('atomic_write', array(
                $fixture['target'],
                true,
                $fixture['live'],
                hash('sha256', $fixture['target']),
                0644,
                'tx-direct-i1-atomic',
                'apply',
                null,
                static function (): void { throw new RuntimeException('I1_ATOMIC_GATE'); },
            ));
        });
    } catch (Throwable $caught) { $atomic_error = $caught->getMessage(); }
    $t->check($atomic_callback_ran, 'atomic direct test must reach the final pre-rename callback');
    $t->same('I1_ATOMIC_GATE', $atomic_error, 'atomic last gate must propagate before rename');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'atomic destination bytes must remain unchanged without recovery');

    $fixture = land76_red_fixture();
    $state_before = "direct-state-before\n";
    $state_after = "direct-state-after\n";
    file_put_contents($fixture['state_file'], $state_before, LOCK_EX);
    $state_callback_ran = false;
    $fixture['before_state_rename'] = static function () use (&$state_callback_ran): void { $state_callback_ran = true; };
    $state_error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture, $state_after): void {
            land76_red_invoke_private('durable_write', array(
                $fixture['state_file'],
                $state_after,
                0600,
                static function (): void { throw new RuntimeException('I1_STATE_GATE'); },
            ));
        });
    } catch (Throwable $caught) { $state_error = $caught->getMessage(); }
    $t->check($state_callback_ran, 'durable direct test must reach the final pre-state-rename callback');
    $t->same('I1_STATE_GATE', $state_error, 'durable state last gate must propagate before rename');
    $t->same($state_before, file_get_contents($fixture['state_file']), 'authoritative state bytes must remain unchanged without recovery');

    $fixture = land76_red_fixture();
    $journal_before = "direct-journal-before\n";
    file_put_contents($fixture['journal_file'], $journal_before, LOCK_EX);
    $journal_callback_ran = false;
    $fixture['before_journal_clear'] = static function () use (&$journal_callback_ran): void { $journal_callback_ran = true; };
    $journal_error = '';
    try {
        land76_red_with_config($fixture, static function (): void {
            land76_red_invoke_private('clear_journal', array(
                static function (): void { throw new RuntimeException('I1_JOURNAL_GATE'); },
            ));
        });
    } catch (Throwable $caught) { $journal_error = $caught->getMessage(); }
    $t->check($journal_callback_ran, 'journal direct test must reach the final pre-unlink callback');
    $t->same('I1_JOURNAL_GATE', $journal_error, 'journal last gate must propagate before unlink');
    $t->same($journal_before, file_get_contents($fixture['journal_file']), 'journal bytes must remain unchanged without recovery');
});

$suite->run('phase B invariant drift after two writes rolls both back', static function (Land76_State_Journal_Red_Suite $t): void {
    $reads = 0;
    $fixture = land76_red_fixture('B', 3, static function (string $key, mixed $default = false) use (&$reads): mixed {
        $reads++;
        return $reads <= 3 ? 'service-hubs-2026-08-28' : 'drifted-release';
    });
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'phase B must detect drift before the third write');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'earlier phase B writes must be rolled back');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'mid-loop phase B drift must retain base state');
    $t->check(!file_exists($fixture['journal_file']), 'mid-loop rollback must clear the journal');
});

$suite->run('phase B invariant drift after state save reverses commit-ready state', static function (Land76_State_Journal_Red_Suite $t): void {
    $reads = 0;
    $fixture = land76_red_fixture('B', 3, static function (string $key, mixed $default = false) use (&$reads): mixed {
        $reads++;
        return $reads <= 6 ? 'service-hubs-2026-08-28' : 'drifted-release';
    });
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'post-save phase B drift must fail the request');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'post-save drift must roll back every destination');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'post-save drift must restore base state');
    $t->check(!file_exists($fixture['journal_file']), 'post-save rollback must clear the journal');
});

$suite->run('phase B invariant is rechecked immediately before journal clear', static function (Land76_State_Journal_Red_Suite $t): void {
    $reads = 0;
    $fixture = land76_red_fixture('B', 3, static function (string $key, mixed $default = false) use (&$reads): mixed {
        $reads++;
        return $reads <= 7 ? 'service-hubs-2026-08-28' : 'drifted-release';
    });
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'PHASE_B_INVARIANT_DRIFT'), 'final pre-clear phase B drift must fail the request');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'final pre-clear drift must roll back every destination');
    $t->same($fixture['state'], land76_red_read_checked_json($fixture['state_file']), 'final pre-clear drift must restore base state');
    $t->check(!file_exists($fixture['journal_file']), 'final pre-clear drift rollback must clear the journal only after restoration');
});

$suite->run('phase B commit-won reconciliation refuses a drifted database invariant', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture('B', 2, static fn(string $key, mixed $default = false): mixed => 'drifted-release');
    $journal = $fixture['journal'];
    unset($journal['checksum']);
    $journal['step'] = 'commit_ready';
    $journal = land76_red_checksummed($journal);
    land76_red_write_json($fixture['state_file'], $fixture['target_state']);
    land76_red_write_json($fixture['journal_file'], $journal);
    foreach ($fixture['targets'] as $path => $target) file_put_contents($fixture['live_files'][$path], $target, LOCK_EX);
    $adapter = land76_red_adapter($fixture);

    $reconciled = $adapter->reconcile_before_theme_include();
    $t->same($fixture['state'], $reconciled, 'commit-won reconciliation must restore the phase B base state after option drift');
    foreach ($fixture['baselines'] as $path => $baseline) $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'commit-won reconciliation must roll back live phase B files');
    $t->check(!file_exists($fixture['journal_file']), 'reconciled phase B rollback must clear the journal');
});

$suite->run('rollback reverify rejects an internally checksummed wrong manifest schema', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array { $manifest['schema'] = 2; return $manifest; }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_SCHEMA_INVALID'), 'manifest schema must be exact even when every outer hash agrees');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'invalid manifest schema must fail before destination mutation');
    $t->check(!file_exists($fixture['journal_file']), 'invalid manifest schema must fail before journal creation');
});

$suite->run('rollback reverify requires the exact manifest release identity', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array { unset($manifest['release_id']); return $manifest; }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_RELEASE_MISMATCH'), 'manifest release ID must be present and exact');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'missing manifest release ID must fail before mutation');
});

$suite->run('rollback reverify requires the exact frozen expected path list', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array { $manifest['expected_paths'] = array(); return $manifest; }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_PATH_SET_INVALID'), 'expected_paths must equal the frozen runtime path list exactly');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'wrong expected path list must fail before mutation');
});

$suite->run('rollback reverify requires strict boolean existence records', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array {
            $path = $manifest['expected_paths'][0];
            $manifest['paths'][$path]['exists'] = 1;
            return $manifest;
        }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_RECORD_INVALID'), 'exists must be a JSON boolean, not a truthy scalar');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'non-boolean record must fail before mutation');
});

$suite->run('rollback reverify validates every existing record byte count', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array {
            $path = $manifest['expected_paths'][0];
            $manifest['paths'][$path]['bytes']++;
            return $manifest;
        }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MEMBER_SIZE_MISMATCH'), 'manifest bytes must equal the exact ZIP member size');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'wrong rollback byte count must fail before mutation');
});

$suite->run('rollback reverify accepts only POSIX permission bits as stored mode', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array {
            $path = $manifest['expected_paths'][0];
            $manifest['paths'][$path]['mode'] = 0100644;
            return $manifest;
        }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_RECORD_INVALID'), 'stored mode must not contain file type bits');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'invalid stored mode must fail before mutation');
});

$suite->run('rollback reverify rejects untrusted manifest fields and absolute storage paths', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array {
            $manifest['backup_path'] = 'C:\\public\\rollback.zip';
            return $manifest;
        }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_SHAPE_INVALID'), 'rollback manifest must contain only its trusted fixed fields');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'untrusted manifest field must fail before mutation');
});

$suite->run('rollback reverify rejects extra fields in per-path records', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture(),
        static function (array $manifest): array {
            $path = $manifest['expected_paths'][0];
            $manifest['paths'][$path]['source_path'] = '/var/www/private/source.php';
            return $manifest;
        }
    );
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_MANIFEST_RECORD_INVALID'), 'per-path records must contain only exists/hash/bytes/mode');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'extra record field must fail before mutation');
});

$suite->run('checksummed state requires a strict boolean backup verification flag', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $state = $fixture['state']; unset($state['checksum']); $state['backup']['verified'] = 1; $state = land76_red_checksummed($state);
    $target = $fixture['target_state']; unset($target['checksum']); $target['backup']['verified'] = 1; $target = land76_red_checksummed($target);
    $fixture = array_replace($fixture, array('state' => $state, 'target_state' => $target));
    land76_red_write_json($fixture['state_file'], $state);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $target);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check($error !== '', 'backup.verified must be a JSON boolean');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'non-boolean verified flag must fail before mutation');
});

$suite->run('backup metadata accepts only the two deterministic rollback artifact basenames', static function (Land76_State_Journal_Red_Suite $t): void {
    $cases = array(
        'zip-state' => array('zip_basename' => 'state.json'),
        'zip-journal' => array('zip_basename' => 'journal.json'),
        'zip-lock' => array('zip_basename' => 'operation.lock'),
        'manifest-state' => array('manifest_basename' => 'state.json'),
        'manifest-journal' => array('manifest_basename' => 'journal.json'),
        'manifest-lock' => array('manifest_basename' => 'operation.lock'),
        'zip-arbitrary' => array('zip_basename' => 'other-safe.zip'),
        'manifest-arbitrary' => array('manifest_basename' => 'other-safe.json'),
        'swapped-artifacts' => array('zip_basename' => 'rollback-manifest.json', 'manifest_basename' => 'rollback.zip'),
        'both-zip' => array('zip_basename' => 'rollback.zip', 'manifest_basename' => 'rollback.zip'),
        'both-manifest' => array('zip_basename' => 'rollback-manifest.json', 'manifest_basename' => 'rollback-manifest.json'),
    );
    foreach ($cases as $name => $changes) {
        $fixture = land76_red_fixture();
        $state = $fixture['state'];
        unset($state['checksum']);
        $state['backup'] = array_replace($state['backup'], $changes);
        $state = land76_red_checksummed($state);
        $target = $fixture['target_state'];
        unset($target['checksum']);
        $target['backup'] = $state['backup'];
        $target = land76_red_checksummed($target);
        $fixture['state'] = $state;
        $fixture['target_state'] = $target;
        land76_red_write_json($fixture['state_file'], $state);
        $error = '';
        try {
            land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $target);
        } catch (Throwable $caught) {
            $error = $caught->getMessage();
        }
        $t->same('STATE_CORRUPT_OR_MISSING', $error, $name . ' must be rejected during checked-state validation before artifact access');
        $t->same($fixture['baseline'], file_get_contents($fixture['live']), $name . ' must fail before destination mutation');
        $t->check(!file_exists($fixture['journal_file']), $name . ' must fail before journal creation');
    }
});

$suite->run('backup corruption between writes halts before the next destination mutation', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture('B', 2, static fn(string $key, mixed $default = false): mixed => 'service-hubs-2026-08-28');
    $apply_renames = 0;
    $fixture['before_destination_rename'] = static function (string $temp) use (&$apply_renames, &$fixture): void {
        if (!str_contains(basename($temp), '.land76-apply-')) return;
        $apply_renames++;
        if ($apply_renames === 1) file_put_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json', 'corrupt-between-writes', LOCK_EX);
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('B', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $second = $fixture['relative_paths'][1];
    $t->check(str_contains($error, 'ROLLBACK_ARTIFACT'), 'corrupt rollback sidecar must abort the active transaction');
    $t->same($fixture['baselines'][$second], file_get_contents($fixture['live_files'][$second]), 'second destination must remain untouched after between-write corruption');
    $persisted = land76_red_read_checked_json($fixture['state_file']);
    $t->same($fixture['state']['checksum'], $persisted['checksum'], 'corruption before final commit must leave authoritative state at the base generation');
    $t->check(file_exists($fixture['journal_file']), 'unrecoverable artifact corruption must retain the journal and fail closed');
});

$suite->run('crash before destination rename leaves one journal-owned temp that recovery removes', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state'], 'crash_before_rename');
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }

    $destination_dir = dirname($fixture['live']);
    $temps = glob($destination_dir . DIRECTORY_SEPARATOR . '.land76-apply-*.tmp');
    $t->check(str_contains($error, 'INJECTED_PROCESS_CRASH_BEFORE_RENAME'), 'the crash failpoint must stop after durable temp creation and before rename');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'pre-rename crash must leave the destination baseline untouched');
    $t->check(is_file($fixture['journal_file']), 'journal ownership must be durable before the destination temp is created');
    $t->check(is_array($temps) && count($temps) === 1 && is_file($temps[0]) && !is_link($temps[0]), 'crash must leave exactly one regular release-owned destination temp');
    $t->same($fixture['target'], file_get_contents($temps[0]), 'orphan temp must contain the staged release bytes');

    $reconciled = $adapter->reconcile_before_theme_include();
    $t->same($fixture['state'], $reconciled, 'recovery must retain the base state after a pre-rename crash');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'recovery must retain the destination baseline');
    $t->check(!file_exists($temps[0]) && !is_link($temps[0]), 'recovery must unlink only the exact journal-derived orphan temp');
    $t->check(!file_exists($fixture['journal_file']), 'successful recovery must clear the owning journal');
});

$suite->run('destination temp replacement before rename is refused without publishing it', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $fixture['before_destination_rename'] = static function (string $temp, string $destination): void {
        if (!@unlink($temp) || !@mkdir($temp, 0700)) throw new RuntimeException('Cannot install non-regular temp race fixture.');
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $error = '';
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'DESTINATION_TEMP_UNSAFE') || str_contains($error, 'DESTINATION_TEMP_RACE'), 'pre-rename temp must remain the exact regular file that was created and hashed');
    $t->same($fixture['baseline'], file_get_contents($fixture['live']), 'a replaced temp must never be renamed onto the destination');
    $t->check(is_file($fixture['journal_file']), 'unsafe temp evidence must retain the recovery journal and fail closed');
});

$suite->run('destination ancestor replacement at the last namespace failpoint cannot redirect rename', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $swapped = false;
    $old_parent = dirname($fixture['live']) . '.pinned-original';
    $decoy = "namespace-decoy\n";
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$swapped, $old_parent, $decoy): void {
        if ($swapped || $operation !== 'destination_rename') return;
        $swapped = true;
        $parent = dirname($path);
        if (!@rename($parent, $old_parent)) throw new RuntimeException('Cannot move checked destination ancestor fixture.');
        land76_red_mkdir($parent);
        if (file_put_contents($path, $decoy, LOCK_EX) !== strlen($decoy)) throw new RuntimeException('Cannot create replacement namespace decoy.');
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            $write = new ReflectionMethod(Land76_Release_Deployer::class, 'atomic_write');
            $write->invoke(
                null,
                $fixture['stage'],
                false,
                $fixture['live'],
                hash('sha256', $fixture['target']),
                0644,
                'tx-namespace-race',
                'apply',
                null,
                null
            );
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check($swapped, 'adversarial callback must replace the checked destination ancestor');
    $t->same('DESTINATION_NAMESPACE_RACE', $error, 'pinned destination namespace must fail closed after ancestor replacement');
    $t->same($decoy, file_get_contents($fixture['live']), 'replacement namespace decoy must never receive release bytes');
    $t->same($fixture['baseline'], file_get_contents($old_parent . DIRECTORY_SEPARATOR . basename($fixture['live'])), 'original destination must remain at baseline after namespace refusal');
});

$suite->run('durable rename and owned unlink seams reject last-moment ancestor replacement', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $state_before = "namespace-state-before\n";
    $state_decoy = "namespace-state-decoy\n";
    file_put_contents($fixture['state_file'], $state_before, LOCK_EX);
    $old_storage = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_storage, $fixture, $state_decoy): void {
        if ($operation !== 'durable_rename' || $old_storage !== null || $path !== $fixture['state_file']) return;
        $old_storage = land76_red_swap_parent($fixture['storage'], static function (string $replacement) use ($state_decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . 'state.json', $state_decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            land76_red_invoke_private('durable_write', array($fixture['state_file'], "namespace-state-after\n", 0600, null));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('STATE_NAMESPACE_RACE', $error, 'durable rename must reject a replaced storage ancestor');
    $t->same($state_decoy, file_get_contents($fixture['state_file']), 'replacement state decoy must remain untouched');
    $t->same($state_before, file_get_contents($old_storage . DIRECTORY_SEPARATOR . 'state.json'), 'original state inode must remain untouched');

    $fixture = land76_red_fixture();
    $temp = dirname($fixture['live']) . DIRECTORY_SEPARATOR . '.land76-apply-owned.tmp';
    $temp_before = "owned-temp-before\n";
    $temp_decoy = "owned-temp-decoy\n";
    file_put_contents($temp, $temp_before, LOCK_EX);
    $old_parent = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_parent, $temp, $temp_decoy): void {
        if ($operation !== 'destination_temp_unlink' || $old_parent !== null || $path !== $temp) return;
        $old_parent = land76_red_swap_parent(dirname($temp), static function (string $replacement) use ($temp, $temp_decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . basename($temp), $temp_decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($temp): void { land76_red_invoke_private('cleanup_release_owned_temp', array($temp)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('DESTINATION_TEMP_NAMESPACE_RACE', $error, 'owned temp unlink must reject a replaced destination ancestor');
    $t->same($temp_decoy, file_get_contents($temp), 'replacement temp decoy must not be unlinked');
    $t->same($temp_before, file_get_contents($old_parent . DIRECTORY_SEPARATOR . basename($temp)), 'original owned temp must remain after namespace refusal');

    $fixture = land76_red_fixture();
    $journal_before = "namespace-journal-before\n";
    $journal_decoy = "namespace-journal-decoy\n";
    file_put_contents($fixture['journal_file'], $journal_before, LOCK_EX);
    $old_storage = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_storage, $fixture, $journal_decoy): void {
        if ($operation !== 'journal_unlink' || $old_storage !== null || $path !== $fixture['journal_file']) return;
        $old_storage = land76_red_swap_parent($fixture['storage'], static function (string $replacement) use ($journal_decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . 'journal.json', $journal_decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void { land76_red_invoke_private('clear_journal', array(null)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('JOURNAL_NAMESPACE_RACE', $error, 'journal unlink must reject a replaced storage ancestor');
    $t->same($journal_decoy, file_get_contents($fixture['journal_file']), 'replacement journal decoy must not be unlinked');
    $t->same($journal_before, file_get_contents($old_storage . DIRECTORY_SEPARATOR . 'journal.json'), 'original journal must remain after namespace refusal');

    $fixture = land76_red_fixture();
    $rollback_before = $fixture['baseline'];
    $rollback_decoy = "rollback-unlink-decoy\n";
    $old_parent = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_parent, $fixture, $rollback_decoy): void {
        if ($operation !== 'rollback_unlink' || $old_parent !== null || $path !== $fixture['live']) return;
        $old_parent = land76_red_swap_parent(dirname($fixture['live']), static function (string $replacement) use ($fixture, $rollback_decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . basename($fixture['live']), $rollback_decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            land76_red_invoke_private('unlink_regular_in_pinned_namespace', array(
                $fixture['live'],
                'Cannot remove introduced file during automatic rollback.',
                'ROLLBACK_DESTINATION_NAMESPACE_RACE',
                'rollback_unlink',
                null,
            ));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('ROLLBACK_DESTINATION_NAMESPACE_RACE', $error, 'rollback unlink must reject a replaced destination ancestor');
    $t->same($rollback_decoy, file_get_contents($fixture['live']), 'replacement rollback decoy must not be unlinked');
    $t->same($rollback_before, file_get_contents($old_parent . DIRECTORY_SEPARATOR . basename($fixture['live'])), 'original rollback target must remain after namespace refusal');
});

$suite->run('recovery and remove-tree rmdir or unlink seams preserve both namespaces after replacement', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $parent = $fixture['docroot'] . DIRECTORY_SEPARATOR . 'recovery-rmdir-parent';
    $directory = $parent . DIRECTORY_SEPARATOR . 'journaled-empty';
    land76_red_mkdir($directory);
    $old_parent = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_parent, $parent, $directory): void {
        if ($operation !== 'recovery_rmdir' || $old_parent !== null || $path !== $directory) return;
        $old_parent = land76_red_swap_parent($parent, static function (string $replacement) use ($directory): void {
            land76_red_mkdir($replacement . DIRECTORY_SEPARATOR . basename($directory));
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($directory): void {
            land76_red_invoke_private('rmdir_empty_in_pinned_namespace', array(
                $directory,
                'JOURNAL_CREATED_DIRECTORY_RECOVERY_FAILED',
                'JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE',
                'recovery_rmdir',
            ));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE', $error, 'recovery rmdir must reject a replaced ancestor');
    $t->check(is_dir($directory), 'replacement recovery directory must not be removed');
    $t->check(is_dir($old_parent . DIRECTORY_SEPARATOR . basename($directory)), 'original recovery directory must not be removed');

    $fixture = land76_red_fixture();
    $stage = $fixture['storage'] . DIRECTORY_SEPARATOR . 'stage-remove-unlink';
    $owned = $stage . DIRECTORY_SEPARATOR . 'owned.txt';
    $original = "remove-tree-original\n";
    $decoy = "remove-tree-decoy\n";
    land76_red_mkdir($stage);
    file_put_contents($owned, $original, LOCK_EX);
    $old_stage = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_stage, $stage, $owned, $decoy): void {
        if ($operation !== 'remove_tree_unlink' || $old_stage !== null || $path !== $owned) return;
        $old_stage = land76_red_swap_parent($stage, static function (string $replacement) use ($owned, $decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . basename($owned), $decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($stage): void { land76_red_invoke_private('remove_tree', array($stage)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('REMOVE_TREE_NAMESPACE_RACE', $error, 'remove_tree unlink must reject a replaced tree namespace');
    $t->same($decoy, file_get_contents($owned), 'replacement remove_tree file must remain untouched');
    $t->same($original, file_get_contents($old_stage . DIRECTORY_SEPARATOR . basename($owned)), 'original remove_tree file must remain untouched');

    $fixture = land76_red_fixture();
    $stage = $fixture['storage'] . DIRECTORY_SEPARATOR . 'stage-remove-rmdir';
    land76_red_mkdir($stage);
    $old_stage = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_stage, $stage): void {
        if ($operation !== 'remove_tree_rmdir' || $old_stage !== null || $path !== $stage) return;
        $old_stage = land76_red_swap_parent($stage, static function (string $replacement): void {});
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($stage): void { land76_red_invoke_private('remove_tree', array($stage)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('REMOVE_TREE_NAMESPACE_RACE', $error, 'remove_tree rmdir must reject a replaced directory inode');
    $t->check(is_dir($stage), 'replacement remove_tree directory must remain');
    $t->check(is_dir($old_stage), 'original remove_tree directory must remain');
});

$suite->run('storage and destination mkdir seams reject replaced parent namespaces', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $storage_parent = $fixture['storage'];
    $new_storage = $storage_parent . DIRECTORY_SEPARATOR . 'protected-root';
    $fixture['storage'] = $new_storage;
    $fixture['state_file'] = $new_storage . DIRECTORY_SEPARATOR . 'state.json';
    $fixture['journal_file'] = $new_storage . DIRECTORY_SEPARATOR . 'journal.json';
    $old_parent = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_parent, $storage_parent, $new_storage): void {
        if ($operation !== 'storage_root_mkdir' || $old_parent !== null || $path !== $new_storage) return;
        $old_parent = land76_red_swap_parent($storage_parent, static function (string $replacement): void {});
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void { land76_red_invoke_private('storage_root', array(true)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('ROLLBACK_STORAGE_NAMESPACE_RACE', $error, 'storage-root mkdir must reject a replaced parent');
    $t->check(!file_exists($new_storage), 'replacement parent must not receive the protected storage directory');
    $t->check(!file_exists($old_parent . DIRECTORY_SEPARATOR . basename($new_storage)), 'original parent must not receive the storage directory after refusal');

    $fixture = land76_red_fixture();
    $new_directory = $fixture['storage'] . DIRECTORY_SEPARATOR . 'new-stage' . DIRECTORY_SEPARATOR . 'nested';
    $old_storage = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_storage, $fixture): void {
        if ($operation !== 'storage_directory_mkdir' || $old_storage !== null) return;
        $old_storage = land76_red_swap_parent($fixture['storage'], static function (string $replacement): void {});
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($new_directory): void { land76_red_invoke_private('ensure_storage_directory', array($new_directory)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('STORAGE_DIRECTORY_NAMESPACE_RACE', $error, 'staging mkdir must reject a replaced storage root');
    $t->check(!file_exists($fixture['storage'] . DIRECTORY_SEPARATOR . 'new-stage'), 'replacement storage must not receive a stage directory');
    $t->check(!file_exists($old_storage . DIRECTORY_SEPARATOR . 'new-stage'), 'original storage must remain unchanged after staging mkdir refusal');

    $fixture = land76_red_fixture();
    $destination_parent = $fixture['docroot'] . DIRECTORY_SEPARATOR . 'destination-mkdir-parent';
    $destination = $destination_parent . DIRECTORY_SEPARATOR . 'created';
    land76_red_mkdir($destination_parent);
    $old_destination_parent = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_destination_parent, $destination_parent, $destination): void {
        if ($operation !== 'destination_directory_mkdir' || $old_destination_parent !== null || $path !== $destination) return;
        $old_destination_parent = land76_red_swap_parent($destination_parent, static function (string $replacement): void {});
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($destination): void {
            land76_red_invoke_private('mkdir_in_pinned_namespace', array(
                $destination,
                0755,
                'DESTINATION_DIRECTORY_CREATE_FAILED',
                'DESTINATION_DIRECTORY_NAMESPACE_RACE',
                'destination_directory_mkdir',
            ));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('DESTINATION_DIRECTORY_NAMESPACE_RACE', $error, 'destination mkdir must reject a replaced parent');
    $t->check(!file_exists($destination), 'replacement destination parent must not receive the created directory');
    $t->check(!file_exists($old_destination_parent . DIRECTORY_SEPARATOR . basename($destination)), 'original destination parent must remain unchanged');
});

$suite->run('crash during rollback remains idempotently recoverable on the next request', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture('A1', 2);
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $adapter = land76_red_adapter($fixture);
    $error = '';
    try {
        $adapter->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state'], 'crash_mid_rollback');
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }

    $live_bytes = array_map('file_get_contents', $fixture['live_files']);
    $t->check(str_contains($error, 'INJECTED_ROLLBACK_PROCESS_CRASH'), 'rollback crash failpoint must interrupt recovery after a real restore mutation');
    $t->check(in_array($fixture['baselines'][$fixture['relative_paths'][1]], $live_bytes, true), 'one destination must already be restored before the injected rollback crash');
    $t->check(in_array($fixture['targets'][$fixture['relative_paths'][0]], $live_bytes, true), 'one destination must remain applied when rollback is interrupted');
    $t->check(is_file($fixture['journal_file']), 'interrupted rollback must retain its recovery journal');

    $first_recovery = $adapter->reconcile_before_theme_include();
    foreach ($fixture['baselines'] as $path => $baseline) {
        $t->same($baseline, file_get_contents($fixture['live_files'][$path]), 'next recovery must restore every destination idempotently');
    }
    $t->same($fixture['state'], $first_recovery, 'next recovery must restore the checksummed base state');
    $t->check(!file_exists($fixture['journal_file']), 'completed retry must clear the recovery journal');
    $t->same($fixture['state'], $adapter->reconcile_before_theme_include(), 'a later recovery pass must be a state-preserving no-op');
});

$suite->run('rollback reapplies and verifies every original POSIX mode', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture('A1', 2);
    $mode_calls = array();
    $fixture['mode_adapter'] = static function (string $operation, string $path, int $mode) use (&$mode_calls): bool {
        $mode_calls[] = array($operation, $path, $mode);
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    try {
        land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state'], 'final_state_commit');
    } catch (Throwable $ignored) {}

    foreach ($fixture['live_files'] as $relative => $live) {
        $original_mode = $fixture['journal']['base_state']['backup']['verified']
            ? json_decode((string)file_get_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json'), true)['paths'][$relative]['mode']
            : null;
        $set_on_restore_temp = false;
        foreach ($mode_calls as $call) {
            if ($call[0] === 'set' && $call[2] === $original_mode && dirname($call[1]) === dirname($live) && str_contains(basename($call[1]), '.land76-restore-')) $set_on_restore_temp = true;
        }
        $t->check($set_on_restore_temp, 'rollback must set the original manifest mode before its atomic rename for ' . $relative);
        $t->check(in_array(array('verify', $live, $original_mode), $mode_calls, true), 'rollback verification must compare the original manifest mode for ' . $relative);
    }
});

$suite->run('rollback artifact inode replacement after hashing is detected before consumption', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $manifest_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json';
    $original_manifest = file_get_contents($manifest_path);
    $fixture['after_backup_hashes'] = static function () use ($manifest_path, $original_manifest): void {
        if (!is_string($original_manifest) || !@rename($manifest_path, $manifest_path . '.old')) throw new RuntimeException('Cannot move artifact race fixture.');
        if (file_put_contents($manifest_path, $original_manifest, LOCK_EX) !== strlen($original_manifest)) throw new RuntimeException('Cannot replace artifact race fixture.');
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            $verify = new ReflectionMethod(Land76_Release_Deployer::class, 'exact_reverify_backup');
            $verify->invoke(null, $fixture['state']);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'ROLLBACK_ARTIFACT_CHANGED'), 'byte-identical path replacement must still fail inode-continuity verification');
});

$suite->run('recovery fails closed when an original POSIX mode cannot be verified', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $fixture['mode_adapter'] = static fn(string $operation, string $path, int $mode): bool => $operation !== 'verify';
    $manifest = json_decode((string)file_get_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json'), true);
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture, $manifest): void {
            $verify = new ReflectionMethod(Land76_Release_Deployer::class, 'verify_restored');
            $verify->invoke(null, $fixture['relative_paths'], $manifest);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('JOURNAL_RECOVERY_MODE_FAILED', $error, 'recovery may not accept correct bytes with the wrong POSIX mode');
});

$suite->run('journal directory sync completes while every destination is still at baseline', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $observations = array();
    $fixture['sync_directory'] = static function (string $directory) use (&$observations, &$fixture): bool {
        $observations[] = array(
            'directory' => rtrim($directory, '/\\'),
            'live' => file_get_contents($fixture['live']),
            'journal' => is_file($fixture['journal_file']),
        );
        return true;
    };
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);

    $storage = rtrim($fixture['storage'], '/\\');
    $journal_sync_at_baseline = false;
    $destination_sync_seen = false;
    foreach ($observations as $observation) {
        if ($observation['directory'] === $storage && $observation['journal'] && $observation['live'] === $fixture['baseline']) $journal_sync_at_baseline = true;
        if ($observation['live'] === $fixture['target']) {
            $destination_sync_seen = true;
            break;
        }
    }
    $t->check($journal_sync_at_baseline, 'a durable journal parent sync must finish before any destination mutation');
    $t->check($destination_sync_seen, 'destination rename must be followed by a parent-directory sync');
});

$suite->run('durability preflight fails closed when required directory fsync is unavailable', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $fixture['sync_directory'] = static fn(string $directory): bool => false;
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void {
            $preflight = new ReflectionMethod(Land76_Release_Deployer::class, 'assert_durability_preflight');
            $preflight->invoke(null);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->check(str_contains($error, 'DIRECTORY_SYNC'), 'activation durability preflight must fail closed when its directory adapter cannot fsync');
});

$suite->run('activation retry initializes state after a pre-state durability failure', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_remove_tree($fixture['storage']);
    $syncs = 0;
    $fixture['sync_directory'] = static function (string $directory) use (&$syncs): bool {
        $syncs++;
        return $syncs !== 4;
    };
    $first_error = '';
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::activation_preflight(); });
    } catch (Throwable $caught) {
        $first_error = $caught->getMessage();
    }
    $t->check(str_contains($first_error, 'DIRECTORY_SYNC'), 'first activation must stop at the injected pre-state durability failure');
    $t->check(is_dir($fixture['storage']) && is_file($fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock'), 'pre-state failure fixture must leave only initialized storage metadata');
    $t->check(!file_exists($fixture['state_file']) && !file_exists($fixture['journal_file']), 'pre-state failure must not invent partial state or journal data');

    $fixture['sync_directory'] = static fn(string $directory): bool => true;
    $retry_error = '';
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::activation_preflight(); });
    } catch (Throwable $caught) {
        $retry_error = $caught->getMessage();
    }
    $t->same('', $retry_error, 'activation retry must accept safe storage containing only the durable lock file');
    $state = land76_red_read_checked_json($fixture['state_file']);
    $t->same(1, $state['generation'], 'activation retry must durably create the initial state generation');
    $t->check(!file_exists($fixture['journal_file']), 'activation retry must not create a transaction journal');
});

$suite->run('journal rejects an untrusted created-directory path before recovery mutation', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $unrelated = $fixture['docroot'] . DIRECTORY_SEPARATOR . 'unrelated-empty';
    land76_red_mkdir($unrelated);
    $journal = $fixture['journal'];
    unset($journal['checksum']);
    $journal['created_dirs'] = array('unrelated-empty');
    $journal = land76_red_checksummed($journal);
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    land76_red_write_json($fixture['journal_file'], $journal);
    $error = '';
    try {
        land76_red_adapter($fixture)->reconcile_before_theme_include();
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('JOURNAL_CORRUPT', $error, 'created directories must be trusted ancestors of a frozen phase destination');
    $t->check(is_dir($unrelated), 'recovery must never remove an unrelated directory named by a forged journal');
});

$suite->run('recovery removes only journaled empty created directories', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_rebuild_backup(
        land76_red_fixture('A1', 2),
        static function (array $manifest): array {
            foreach ($manifest['expected_paths'] as $path) $manifest['paths'][$path] = array('exists' => false);
            return $manifest;
        }
    );
    $created_relative = 'wp-content/themes/land76wp/phase-a1';
    $created = $fixture['docroot'] . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $created_relative);
    $unjournaled = dirname($created) . DIRECTORY_SEPARATOR . 'unjournaled-empty';
    land76_red_mkdir($unjournaled);
    $journal = $fixture['journal'];
    unset($journal['checksum']);
    $journal['created_dirs'] = array($created_relative);
    $journal = land76_red_checksummed($journal);
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    land76_red_write_json($fixture['journal_file'], $journal);
    foreach ($fixture['live_files'] as $path => $live) file_put_contents($live, $fixture['targets'][$path], LOCK_EX);

    $recovered = land76_red_adapter($fixture)->reconcile_before_theme_include();
    $t->same($fixture['state'], $recovered, 'recovery must restore base state after removing introduced files');
    $t->check(!file_exists($created), 'journaled directory must be removed after it becomes empty');
    $t->check(is_dir($unjournaled), 'an unjournaled empty sibling must remain untouched');
});

$suite->run('normal request returns only a generic 503 while a writer owns the lock', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $lock_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock';
    $writer = fopen($lock_path, 'c+b');
    if (!is_resource($writer) || !flock($writer, LOCK_EX | LOCK_NB)) throw new RuntimeException('Cannot acquire writer fixture lock.');
    $old_server = $_SERVER;
    $old_post = $_POST;
    $_SERVER['REQUEST_METHOD'] = 'GET';
    $_POST = array();
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::early_recovery(); });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    } finally {
        flock($writer, LOCK_UN);
        fclose($writer);
        $_SERVER = $old_server;
        $_POST = $old_post;
    }
    $t->same('WP_DIE:503:Service temporarily unavailable.', $error, 'writer contention must not disclose lock or journal details before theme load');
});

$suite->run('normal request holds a shared lock until explicit shutdown release', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $old_server = $_SERVER;
    $old_post = $_POST;
    $_SERVER['REQUEST_METHOD'] = 'POST';
    $_POST = array('action' => 'land76_release_apply', 'phase' => 'A1', '_wpnonce' => 'invalid-near-miss');
    $writer = null;
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::early_recovery(); });
        $writer = fopen($fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock', 'c+b');
        if (!is_resource($writer)) throw new RuntimeException('Cannot open competing writer fixture lock.');
        $t->check(!flock($writer, LOCK_EX | LOCK_NB), 'normal and unauthorized near-match requests must retain SH across theme execution');
        $release = new ReflectionMethod(Land76_Release_Deployer::class, 'release_request_lock');
        $release->invoke(null);
        $t->check(flock($writer, LOCK_EX | LOCK_NB), 'shutdown release must make the exclusive writer lock obtainable');
    } finally {
        try {
            $release = new ReflectionMethod(Land76_Release_Deployer::class, 'release_request_lock');
            $release->invoke(null);
        } catch (Throwable $ignored) {}
        if (is_resource($writer)) { flock($writer, LOCK_UN); fclose($writer); }
        $_SERVER = $old_server;
        $_POST = $old_post;
    }
});

$suite->run('exact authorized deployer POST recovers under retained EX before theme and reuses ownership in handler', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture('A1', 2);
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    land76_red_write_json($fixture['journal_file'], $fixture['journal']);
    file_put_contents($fixture['live_files'][$fixture['relative_paths'][0]], $fixture['targets'][$fixture['relative_paths'][0]], LOCK_EX);
    $old_server = $_SERVER;
    $old_post = $_POST;
    $_SERVER['REQUEST_METHOD'] = 'POST';
    $_POST = array(
        'action' => 'land76_release_apply',
        'phase' => 'A1',
        '_wpnonce' => 'valid:land76_release_deployer:apply:A1',
    );
    $probe = null;
    $probe_obtained_ex = false;
    $theme_saw_partial_release = false;
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::early_recovery(); });
        $theme_saw_partial_release = file_exists($fixture['journal_file']);
        foreach ($fixture['baselines'] as $path => $baseline) {
            if (file_get_contents($fixture['live_files'][$path]) !== $baseline) $theme_saw_partial_release = true;
        }
        $probe = fopen($fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock', 'c+b');
        if (!is_resource($probe)) throw new RuntimeException('Cannot open authorized writer probe lock.');
        $probe_obtained_ex = flock($probe, LOCK_EX | LOCK_NB);
        if ($probe_obtained_ex) flock($probe, LOCK_UN);

        $result = land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state']);
        $t->check(!$theme_saw_partial_release, 'authorized writer early hook must reconcile a partial journal before the theme sentinel');
        $t->check(!$probe_obtained_ex, 'authorized writer must retain EX ownership across theme bootstrap');
        $t->same($fixture['target_state'], $result, 'authorized request must later complete the normal EX-locked transaction path');
        foreach ($fixture['targets'] as $path => $target) $t->same($target, file_get_contents($fixture['live_files'][$path]), 'handler must reuse retained EX and publish ' . $path);
        $t->check(!flock($probe, LOCK_EX | LOCK_NB), 'successful handler return must keep the request EX lock through shutdown');
        $release = new ReflectionMethod(Land76_Release_Deployer::class, 'release_request_lock');
        $release->invoke(null);
        $t->check(flock($probe, LOCK_EX | LOCK_NB), 'explicit shutdown release must make EX ownership available after handler completion');
        flock($probe, LOCK_UN);
    } finally {
        if (is_resource($probe)) { flock($probe, LOCK_UN); fclose($probe); }
        try {
            $release = new ReflectionMethod(Land76_Release_Deployer::class, 'release_request_lock');
            $release->invoke(null);
        } catch (Throwable $ignored) {}
        $_SERVER = $old_server;
        $_POST = $old_post;
    }
});

$suite->run('authorized writer retains early EX through same-request rollback until shutdown', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $old_server = $_SERVER;
    $old_post = $_POST;
    $_SERVER['REQUEST_METHOD'] = 'POST';
    $_POST = array(
        'action' => 'land76_release_apply',
        'phase' => 'A1',
        '_wpnonce' => 'valid:land76_release_deployer:apply:A1',
    );
    $probe = null;
    try {
        land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::early_recovery(); });
        $error = '';
        try {
            land76_red_adapter($fixture)->apply_phase_for_test('A1', $fixture['staged_files'], $fixture['target_state'], 'final_state_commit');
        } catch (Throwable $caught) { $error = $caught->getMessage(); }
        $t->check(str_contains($error, 'APPLY_FAILED_RECOVERED'), 'injected handler failure must complete same-request rollback');
        $probe = fopen($fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock', 'c+b');
        if (!is_resource($probe)) throw new RuntimeException('Cannot open rollback lifetime probe lock.');
        $t->check(!flock($probe, LOCK_EX | LOCK_NB), 'recovered handler failure must retain request EX until shutdown');
        land76_red_invoke_private('release_request_lock');
        $t->check(flock($probe, LOCK_EX | LOCK_NB), 'shutdown release must free EX after same-request rollback');
        flock($probe, LOCK_UN);
    } finally {
        if (is_resource($probe)) { flock($probe, LOCK_UN); fclose($probe); }
        try { land76_red_invoke_private('release_request_lock'); } catch (Throwable $ignored) {}
        $_SERVER = $old_server;
        $_POST = $old_post;
    }
});

$suite->run('second exact authorized writer receives generic 503 before theme while first writer owns EX', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $lock_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock';
    $first_writer = fopen($lock_path, 'c+b');
    if (!is_resource($first_writer) || !flock($first_writer, LOCK_EX | LOCK_NB)) throw new RuntimeException('Cannot acquire first authorized writer fixture lock.');
    $old_server = $_SERVER;
    $old_post = $_POST;
    $_SERVER['REQUEST_METHOD'] = 'POST';
    $_POST = array(
        'action' => 'land76_release_apply',
        'phase' => 'A1',
        '_wpnonce' => 'valid:land76_release_deployer:apply:A1',
    );
    $error = '';
    $theme_ran = false;
    try {
        try {
            land76_red_with_config($fixture, static function (): void { Land76_Release_Deployer::early_recovery(); });
            $theme_ran = true;
        } catch (Throwable $caught) {
            $error = $caught->getMessage();
        }
    } finally {
        flock($first_writer, LOCK_UN);
        fclose($first_writer);
        $_SERVER = $old_server;
        $_POST = $old_post;
    }
    $t->same('WP_DIE:503:Service temporarily unavailable.', $error, 'contending authorized writer must fail generically in the early hook');
    $t->check(!$theme_ran, 'theme sentinel must not run for an authorized writer that cannot obtain EX');
});

$suite->run('operation lock inode replacement after flock is refused', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    land76_red_write_json($fixture['state_file'], $fixture['state']);
    $swapped = false;
    $fixture['after_lock_acquired'] = static function (string $mode, string $lock_path) use (&$swapped): void {
        if ($swapped) return;
        $swapped = true;
        if (!@rename($lock_path, $lock_path . '.old')) throw new RuntimeException('Cannot move locked inode fixture.');
        if (file_put_contents($lock_path, '') !== 0) throw new RuntimeException('Cannot replace locked inode fixture.');
    };
    $error = '';
    try {
        land76_red_adapter($fixture)->reconcile_before_theme_include();
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('LOCK_PATH_RACE', $error, 'flock must be revalidated against the current lock pathname before protected work');
});

$suite->run('exclusive lock inode is revalidated after protected work', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $lock_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'operation.lock';
    $old_lock = $lock_path . '.post-lock-' . bin2hex(random_bytes(4));
    $protected_work = false;
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($lock_path, $old_lock, &$protected_work): void {
            land76_red_invoke_private('with_lock', array(static function () use ($lock_path, $old_lock, &$protected_work): void {
                $protected_work = true;
                if (!rename($lock_path, $old_lock)) throw new RuntimeException('Cannot move lock inode during protected work fixture.');
                file_put_contents($lock_path, '', LOCK_EX);
            }));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->check($protected_work, 'post-lock identity test must execute protected work before replacement');
    $t->same('LOCK_PATH_RACE', $error, 'with_lock must reject lock-inode replacement during protected work before releasing ownership');
});

$suite->run('rollback storage is refused when configured inside ABSPATH', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $inside = $fixture['docroot'] . DIRECTORY_SEPARATOR . '.land76-release-deployer';
    land76_red_mkdir($inside);
    $fixture['storage'] = $inside;
    $fixture['state_file'] = $inside . DIRECTORY_SEPARATOR . 'state.json';
    $fixture['journal_file'] = $inside . DIRECTORY_SEPARATOR . 'journal.json';
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void {
            $storage = new ReflectionMethod(Land76_Release_Deployer::class, 'storage_root');
            $storage->invoke(null, false);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('ROLLBACK_STORAGE_INSIDE_DOCROOT', $error, 'predictable rollback storage may never reside beneath ABSPATH');
});

$suite->run('rollback storage requires an exact verified 0700 mode', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $fixture['mode_adapter'] = static function (string $operation, string $path, int $mode) use ($fixture): bool {
        if ($operation === 'verify' && rtrim($path, '/\\') === rtrim($fixture['storage'], '/\\') && $mode === 0700) return false;
        return true;
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function (): void {
            $storage = new ReflectionMethod(Land76_Release_Deployer::class, 'storage_root');
            $storage->invoke(null, false);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('ROLLBACK_STORAGE_MODE_INVALID', $error, 'storage must fail closed if exact 0700 cannot be verified');
});

$suite->run('staging workspace has one deterministic release-owned crash cleanup path', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $archive_hash = str_repeat('a', 64);
    $prepared = '';
    land76_red_with_config($fixture, static function () use ($fixture, $archive_hash, &$prepared): void {
        $path_method = new ReflectionMethod(Land76_Release_Deployer::class, 'release_stage_path');
        $first = $path_method->invoke(null, 'A1', $archive_hash);
        $second = $path_method->invoke(null, 'A1', $archive_hash);
        if ($first !== $second) throw new RuntimeException('Stage path is not deterministic.');
        land76_red_mkdir($first);
        file_put_contents($first . DIRECTORY_SEPARATOR . 'orphan.txt', 'crash-orphan', LOCK_EX);
        $prepare = new ReflectionMethod(Land76_Release_Deployer::class, 'prepare_stage_workspace');
        $prepared = $prepare->invoke(null, 'A1', $archive_hash);
    });
    $t->check(str_starts_with($prepared, $fixture['storage'] . DIRECTORY_SEPARATOR . 'stage-a1-'), 'stage path must remain inside protected rollback storage');
    $t->check(!file_exists($prepared), 'retry preparation must remove the exact stale stage tree before extraction');
});

$suite->run('remove_tree refuses every path outside validated rollback storage', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $outside = dirname($fixture['storage']) . DIRECTORY_SEPARATOR . 'outside-tree';
    land76_red_mkdir($outside);
    $sentinel = $outside . DIRECTORY_SEPARATOR . 'sentinel.txt';
    file_put_contents($sentinel, 'outside');
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($outside): void {
            $remove = new ReflectionMethod(Land76_Release_Deployer::class, 'remove_tree');
            $remove->invoke(null, $outside);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('REMOVE_TREE_OUTSIDE_STORAGE', $error, 'remove_tree must reject a sibling path before enumeration');
    $t->check(is_file($sentinel), 'outside sentinel must remain untouched');
});

$suite->run('release path lstat guard refuses a directory where a regular leaf is expected', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    if (!@unlink($fixture['live']) || !@mkdir($fixture['live'], 0700)) throw new RuntimeException('Cannot create non-regular leaf fixture.');
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($fixture): void {
            $guard = new ReflectionMethod(Land76_Release_Deployer::class, 'assert_safe_release_path');
            $guard->invoke(null, $fixture['relative']);
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('RELEASE_PATH_LEAF_NOT_REGULAR', $error, 'existing destination leaf must be a regular file');
});

$suite->run('backup core lstat-guards ancestors and leaf before reading or adding a file', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    if (!@unlink($fixture['live']) || !@mkdir($fixture['live'], 0700)) throw new RuntimeException('Cannot create unsafe backup leaf fixture.');
    $state = $fixture['state'];
    unset($state['checksum']);
    $state['backup'] = array('verified' => false);
    $state = land76_red_checksummed($state);
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use (&$state): void {
            $backup = new ReflectionMethod(Land76_Release_Deployer::class, 'create_backup_snapshot');
            $backup->invokeArgs(null, array(&$state));
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $t->same('RELEASE_PATH_LEAF_NOT_REGULAR', $error, 'backup must invoke the lstat path-chain guard before file reads');
    $t->check(!file_exists($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip'), 'failed backup must remove its exact partial ZIP');
    $t->check(!file_exists($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json'), 'failed backup must remove its exact partial sidecar');
});

$suite->run('backup retry replaces only deterministic release-owned artifact paths', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    file_put_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip', 'stale-partial-zip', LOCK_EX);
    file_put_contents($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json', 'stale-partial-manifest', LOCK_EX);
    $state = $fixture['state'];
    unset($state['checksum']);
    $state['backup'] = array('verified' => false);
    $state = land76_red_checksummed($state);
    land76_red_write_json($fixture['state_file'], $state);
    land76_red_with_config($fixture, static function () use (&$state): void {
        $backup = new ReflectionMethod(Land76_Release_Deployer::class, 'create_backup_snapshot');
        $backup->invokeArgs(null, array(&$state));
    });
    $t->same('rollback.zip', $state['backup']['zip_basename'], 'backup ZIP ownership must use one deterministic crash-recoverable basename');
    $t->same('rollback-manifest.json', $state['backup']['manifest_basename'], 'backup sidecar ownership must use one deterministic crash-recoverable basename');
    $t->check(hash_file('sha256', $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip') === $state['backup']['zip_sha256'], 'retry must replace stale ZIP bytes with the exact verified snapshot');
    $t->check(hash_file('sha256', $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback-manifest.json') === $state['backup']['manifest_sha256'], 'retry must replace stale sidecar bytes with the exact verified manifest');
});

$suite->run('backup ZIP publish pins the closed build inode before final rename', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $state = $fixture['state'];
    unset($state['checksum']);
    $state['backup'] = array('verified' => false);
    $state = land76_red_checksummed($state);
    land76_red_write_json($fixture['state_file'], $state);
    $replacement = null;
    $original = null;
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$replacement, &$original): void {
        if ($operation !== 'backup_zip_publish' || $replacement !== null) return;
        $replacement = file_get_contents(dirname($path) . DIRECTORY_SEPARATOR . '.rollback.zip.build.tmp');
        if (!is_string($replacement)) throw new RuntimeException('Cannot read completed backup build fixture.');
        $build = dirname($path) . DIRECTORY_SEPARATOR . '.rollback.zip.build.tmp';
        $original = $build . '.original';
        if (!rename($build, $original)) throw new RuntimeException('Cannot move completed backup build inode.');
        if (file_put_contents($build, $replacement, LOCK_EX) !== strlen($replacement)) throw new RuntimeException('Cannot install byte-identical backup build replacement.');
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use (&$state): void { land76_red_invoke_private('create_backup_snapshot', array(&$state)); });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $build = $fixture['storage'] . DIRECTORY_SEPARATOR . '.rollback.zip.build.tmp';
    $t->same('ROLLBACK_ZIP_CREATE_RACE', $error, 'byte-identical closed ZIP inode replacement must be refused before publish');
    $t->check(!file_exists($fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip'), 'replaced build inode must never be published as rollback.zip');
    $t->same($replacement, file_get_contents($build), 'replacement build bytes must not be deleted or renamed');
    $t->same($replacement, file_get_contents($original), 'original completed ZIP inode must remain available for fail-closed diagnosis');
});

$suite->run('download byte-read helper refuses a storage ancestor swap before opening ZIP', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $zip_path = $fixture['storage'] . DIRECTORY_SEPARATOR . 'rollback.zip';
    $old_storage = null;
    $decoy = "not-the-verified-download\n";
    $fixture['before_namespace_mutation'] = static function (string $operation, string $path) use (&$old_storage, $fixture, $zip_path, $decoy): void {
        if ($operation !== 'regular_file_open' || $path !== $zip_path || $old_storage !== null) return;
        $old_storage = land76_red_swap_parent($fixture['storage'], static function (string $replacement) use ($decoy): void {
            file_put_contents($replacement . DIRECTORY_SEPARATOR . 'rollback.zip', $decoy, LOCK_EX);
        });
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use ($zip_path): void {
            land76_red_invoke_private('read_regular_file_in_pinned_namespace', array($zip_path, 'ROLLBACK_DOWNLOAD_RACE'));
        });
    } catch (Throwable $caught) { $error = $caught->getMessage(); }
    $t->same('ROLLBACK_DOWNLOAD_RACE', $error, 'download helper must reject a replaced storage ancestor before fopen');
    $t->same($decoy, file_get_contents($zip_path), 'replacement download decoy must remain unread and unchanged');
    $t->same($fixture['state']['backup']['zip_sha256'], hash_file('sha256', $old_storage . DIRECTORY_SEPARATOR . 'rollback.zip'), 'original verified ZIP must remain unchanged');
});

$suite->run('ambiguous state directory sync preserves newly referenced rollback artifacts', static function (Land76_State_Journal_Red_Suite $t): void {
    $fixture = land76_red_fixture();
    $state = $fixture['state'];
    unset($state['checksum']);
    $state['backup'] = array('verified' => false);
    $state = land76_red_checksummed($state);
    land76_red_write_json($fixture['state_file'], $state);
    $failed_after_state_rename = false;
    $fixture['sync_directory'] = static function (string $directory) use (&$failed_after_state_rename, $fixture): bool {
        if ($failed_after_state_rename || !is_file($fixture['state_file'])) return true;
        $document = json_decode((string)file_get_contents($fixture['state_file']), true);
        if (is_array($document) && ($document['backup']['verified'] ?? false) === true) {
            $failed_after_state_rename = true;
            return false;
        }
        return true;
    };
    $error = '';
    try {
        land76_red_with_config($fixture, static function () use (&$state): void {
            $backup = new ReflectionMethod(Land76_Release_Deployer::class, 'create_backup_snapshot');
            $backup->invokeArgs(null, array(&$state));
        });
    } catch (Throwable $caught) {
        $error = $caught->getMessage();
    }
    $persisted = land76_red_read_checked_json($fixture['state_file']);
    $zip = isset($persisted['backup']['zip_basename']) ? $fixture['storage'] . DIRECTORY_SEPARATOR . $persisted['backup']['zip_basename'] : '';
    $manifest = isset($persisted['backup']['manifest_basename']) ? $fixture['storage'] . DIRECTORY_SEPARATOR . $persisted['backup']['manifest_basename'] : '';
    $t->check(str_contains($error, 'COMMIT_UNCERTAIN_AFTER_RENAME'), 'post-rename directory sync failure must be classified as an ambiguous state commit; got=' . $error);
    $t->check($persisted['backup']['verified'] === true, 'renamed state must retain its verified backup metadata');
    $t->check(is_file($zip) && is_file($manifest), 'cleanup must preserve every artifact referenced by ambiguously committed state');
});

if (DIRECTORY_SEPARATOR === '/') {
    $suite->run('production POSIX file and directory fsync paths execute without adapters', static function (Land76_State_Journal_Red_Suite $t): void {
        $fixture = land76_red_fixture();
        $sync_file = new ReflectionMethod(Land76_Release_Deployer::class, 'sync_regular_file');
        $sync_directory = new ReflectionMethod(Land76_Release_Deployer::class, 'sync_directory');
        $set_mode = new ReflectionMethod(Land76_Release_Deployer::class, 'set_mode_exact');
        $sync_file->invoke(null, $fixture['stage'], 'POSIX_FILE_SYNC_SMOKE_FAILED');
        $sync_directory->invoke(null, $fixture['storage']);
        $set_mode->invoke(null, $fixture['stage'], 0600, 'POSIX_MODE_SMOKE_FAILED');
        clearstatcache(true, $fixture['stage']);
        $t->same(0600, fileperms($fixture['stage']) & 0777, 'production POSIX mode verification must observe exact permission bits');
    });

    $suite->run('POSIX integration namespace pins retain real handles for every managed ancestor', static function (Land76_State_Journal_Red_Suite $t): void {
        $fixture = land76_red_fixture();
        $pins = land76_red_with_config($fixture, static function () use ($fixture): array {
            return land76_red_invoke_private('pin_directory_namespace', array($fixture['storage'], 'POSIX_PIN_FAILED'));
        });
        try {
            $t->check($pins !== array(), 'POSIX pin chain must not be empty');
            foreach ($pins as $pin) $t->check(is_resource($pin['handle'] ?? null), 'every managed POSIX ancestor pin must retain a real directory handle');
        } finally {
            land76_red_invoke_private('close_directory_namespace', array($pins));
        }
    });

    $suite->run('storage-root replacement after flock cannot authorize protected work through the old lock inode', static function (Land76_State_Journal_Red_Suite $t): void {
        $fixture = land76_red_fixture();
        $old_storage = $fixture['storage'] . '.pinned-original';
        $swapped = false;
        $protected_work = false;
        $replacement_lock = null;
        $replacement_ex = false;
        $fixture['after_lock_acquired'] = static function (string $mode, string $lock_path) use (&$swapped, &$replacement_lock, &$replacement_ex, $fixture, $old_storage): void {
            if ($swapped) return;
            $swapped = true;
            if (!rename($fixture['storage'], $old_storage)) throw new RuntimeException('Cannot move checked storage root fixture.');
            if (!mkdir($fixture['storage'], 0700)) throw new RuntimeException('Cannot create fresh split-lock storage namespace.');
            $fresh_lock_path = $fixture['storage'] . DIRECTORY_SEPARATOR . basename($lock_path);
            if (file_put_contents($fresh_lock_path, '') !== 0 || !chmod($fresh_lock_path, 0600)) throw new RuntimeException('Cannot create fresh split-lock inode.');
            $replacement_lock = fopen($fresh_lock_path, 'r+b');
            if (!is_resource($replacement_lock)) throw new RuntimeException('Cannot open fresh split-lock inode.');
            $replacement_ex = flock($replacement_lock, LOCK_EX | LOCK_NB);
        };
        $error = '';
        try {
            land76_red_with_config($fixture, static function () use (&$protected_work): void {
                $with_lock = new ReflectionMethod(Land76_Release_Deployer::class, 'with_lock');
                $with_lock->invoke(null, static function () use (&$protected_work): void { $protected_work = true; });
            });
        } catch (Throwable $caught) {
            $error = $caught->getMessage();
        }
        $t->check($swapped, 'adversarial callback must replace the checked storage root after flock');
        $t->check($replacement_ex, 'fresh replacement lock inode must demonstrate a real split-lock namespace');
        $t->same('LOCK_NAMESPACE_RACE', $error, 'storage-root replacement must invalidate retained lock ownership');
        $t->check(!$protected_work, 'no protected transaction work may run under a split storage namespace');
        $t->check(is_dir($fixture['storage']) && !is_link($fixture['storage']), 'test must use a fresh directory namespace rather than a symlink back to the old lock');
        if (is_resource($replacement_lock)) { flock($replacement_lock, LOCK_UN); fclose($replacement_lock); }
        land76_red_remove_tree($fixture['storage']);
        if (!rename($old_storage, $fixture['storage'])) throw new RuntimeException('Cannot restore storage after split-lock test.');
    });

    $suite->run('remove_tree refuses a real symlink root without touching its target', static function (Land76_State_Journal_Red_Suite $t): void {
        $fixture = land76_red_fixture();
        $target = dirname($fixture['storage']) . DIRECTORY_SEPARATOR . 'symlink-target';
        land76_red_mkdir($target);
        $sentinel = $target . DIRECTORY_SEPARATOR . 'sentinel.txt';
        file_put_contents($sentinel, 'outside');
        $stage_link = $fixture['storage'] . DIRECTORY_SEPARATOR . 'stage-symlink';
        if (!symlink($target, $stage_link)) throw new RuntimeException('POSIX test target cannot create the required symlink fixture.');
        $error = '';
        try {
            land76_red_with_config($fixture, static function () use ($stage_link): void {
                $remove = new ReflectionMethod(Land76_Release_Deployer::class, 'remove_tree');
                $remove->invoke(null, $stage_link);
            });
        } catch (Throwable $caught) {
            $error = $caught->getMessage();
        }
        $t->same('REMOVE_TREE_LINK_REFUSED', $error, 'remove_tree must reject a symlink root');
        $t->same('outside', file_get_contents($sentinel), 'symlink target must remain untouched');
    });
    $suite->run('release path lstat guard refuses a real symlink ancestor', static function (Land76_State_Journal_Red_Suite $t): void {
        $fixture = land76_red_fixture();
        $link = dirname($fixture['live']);
        if (!@unlink($fixture['live']) || !@rmdir($link)) throw new RuntimeException('Cannot prepare ancestor symlink fixture.');
        $target = dirname($fixture['storage']) . DIRECTORY_SEPARATOR . 'release-path-target';
        land76_red_mkdir($target);
        $sentinel = $target . DIRECTORY_SEPARATOR . 'sentinel.txt';
        file_put_contents($sentinel, 'outside');
        if (!symlink($target, $link)) throw new RuntimeException('POSIX test target cannot create the required ancestor symlink fixture.');
        $error = '';
        try {
            land76_red_with_config($fixture, static function () use ($fixture): void {
                $guard = new ReflectionMethod(Land76_Release_Deployer::class, 'assert_safe_release_path');
                $guard->invoke(null, $fixture['relative']);
            });
        } catch (Throwable $caught) {
            $error = $caught->getMessage();
        }
        $t->same('RELEASE_PATH_LINK_REFUSED', $error, 'real ancestor symlink must be refused');
        $t->same('outside', file_get_contents($sentinel), 'ancestor symlink target must remain untouched');
    });
} else {
    fwrite(STDOUT, "SKIP real POSIX fsync/mode/symlink/namespace-swap tests: host does not provide POSIX filesystem semantics\n");
}

$suite->finish();
