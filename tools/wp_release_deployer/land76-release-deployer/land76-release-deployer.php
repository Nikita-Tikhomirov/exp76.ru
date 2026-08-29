<?php
/**
 * Plugin Name: Land76 Release Deployer
 * Description: One-time, administrator-only deployer for the verified exp76.ru release.
 * Version: 1.0.1
 */
declare(strict_types=1);

if (!defined('ABSPATH')) { exit; }

if (defined('LAND76_RELEASE_DEPLOYER_INTEGRATION_TEST') && LAND76_RELEASE_DEPLOYER_INTEGRATION_TEST === true) {
    /** Test-only entry point. The production class has no adapter method unless the test constant exists before load. */
    trait Land76_Release_Deployer_Integration_Test_Seam {
        private static function integration_test_adapter(array $config): object {
            $config = self::validate_integration_config($config);
            $reconcile = static function () use ($config): array {
                return self::with_integration_config($config, static function (): array {
                    $state = array();
                    self::with_lock(static function () use (&$state): void { self::recover_journal($state); });
                    return $state;
                });
            };
            $apply = static function (string $phase, array $staged_files, array $target_state, ?string $failpoint) use ($config): array {
                return self::with_integration_config($config, static function () use ($phase, $staged_files, $target_state, $failpoint): array {
                    $result = array();
                    self::with_lock(static function () use (&$result, $phase, $staged_files, $target_state, $failpoint): void {
                        $state = array();
                        self::recover_journal($state);
                        $result = self::apply_phase_transaction($state, $phase, $staged_files, $target_state, $failpoint);
                    });
                    return $result;
                });
            };
            return new class($reconcile, $apply) {
                private $reconcile;
                private $apply;
                public function __construct(callable $reconcile, callable $apply) { $this->reconcile = $reconcile; $this->apply = $apply; }
                public function reconcile_before_theme_include(): array { return ($this->reconcile)(); }
                public function apply_phase_for_test(string $phase, array $staged_files, array $target_state, ?string $failpoint = null): array {
                    return ($this->apply)($phase, $staged_files, $target_state, $failpoint);
                }
            };
        }
    }
} else {
    trait Land76_Release_Deployer_Integration_Test_Seam {}
}

final class Land76_Release_Deployer {
    use Land76_Release_Deployer_Integration_Test_Seam;

    private const NONCE = 'land76_release_deployer';
    private const RELEASE_ID = 'exp76-production-release-20260829-133000-r2';
    private const HUB_RELEASE_ID = 'service-hubs-2026-08-28';
    private const MAX_UPLOAD_BYTES = 15_000_000;
    private const ORDER = array('A1', 'A2', 'C', 'B');
    private const ACTIVATION_ERROR_CODES = array(
        'ACTIVATION_LINT_UNAVAILABLE', 'ACTIVATION_STORAGE_SCAN_FAILED', 'ACTIVATION_STORAGE_NOT_EMPTY',
        'ACTIVATION_STORAGE_UNSAFE', 'ACTIVATION_STATE_VERIFY_FAILED', 'DIRECTORY_SYNC_UNSUPPORTED',
        'DIRECTORY_SYNC_TARGET_UNSAFE', 'DIRECTORY_SYNC_OPEN_FAILED', 'DIRECTORY_SYNC_FAILED',
        'DIRECTORY_SYNC_PIN_LSTAT_FAILED', 'DIRECTORY_SYNC_PIN_LINK_REFUSED',
        'DIRECTORY_SYNC_PIN_NOT_DIRECTORY', 'DIRECTORY_SYNC_PIN_OPEN_FAILED',
        'DIRECTORY_SYNC_PIN_FSTAT_FAILED', 'DIRECTORY_SYNC_PIN_HANDLE_NOT_DIRECTORY',
        'DIRECTORY_SYNC_PIN_IDENTITY_MISMATCH', 'DIRECTORY_SYNC_VERIFY_LSTAT_FAILED',
        'DIRECTORY_SYNC_VERIFY_LINK_REFUSED', 'DIRECTORY_SYNC_VERIFY_NOT_DIRECTORY',
        'DIRECTORY_SYNC_VERIFY_IDENTITY_MISMATCH', 'DIRECTORY_SYNC_VERIFY_HANDLE_FAILED',
        'NAMESPACE_PIN_UNSUPPORTED', 'ROLLBACK_STORAGE_INSIDE_DOCROOT', 'ROLLBACK_STORAGE_PATH_UNSAFE',
        'ROLLBACK_STORAGE_LSTAT_FAILED', 'ROLLBACK_STORAGE_NOT_INITIALIZED', 'ROLLBACK_STORAGE_MODE_INVALID',
        'ROLLBACK_STORAGE_NAMESPACE_RACE', 'LOCK_PATH_UNSAFE', 'LOCK_PATH_LSTAT_FAILED', 'LOCK_OPEN_FAILED',
        'LOCK_PATH_RACE', 'LOCK_INITIALIZE_FAILED', 'LOCK_NAMESPACE_RACE', 'LOCK_BUSY',
        'STATE_TEMP_CREATE_FAILED', 'STATE_TEMP_RACE', 'STATE_WRITE_FAILED', 'STATE_RENAME_FAILED',
        'DURABLE_COMMIT_UNCERTAIN_AFTER_RENAME', 'STATE_CORRUPT_OR_MISSING', 'STATE_SCHEMA_INVALID',
        'STATE_RELEASE_INVALID', 'STATE_GENERATION_INVALID', 'STATE_SHAPE_INVALID', 'STATE_PHASE_INVALID',
        'JOURNAL_CORRUPT', 'JOURNAL_CORRUPT_OR_MISSING', 'JOURNAL_REQUIRES_LOCKED_RECOVERY',
    );
    private const REGISTRY_FUNCTIONS = array(
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
    private static ?array $integration_config = null;
    /** @var resource|null Shared request lock retained from plugins_loaded through shutdown. */
    private static $request_lock = null;
    private static ?string $request_lock_mode = null;
    private static bool $request_lock_shutdown_registered = false;
    /** @var array<int,array<int,array{path:string,stat:array,handle:mixed}>> */
    private static array $lock_namespace_pins = array();

    public static function init(): void {
        if (function_exists('add_action')) {
            // Register before wp-admin menu APIs exist; callbacks resolve after WordPress loads them.
            add_action('plugins_loaded', array(__CLASS__, 'early_recovery'), 1);
            add_action('init', array(__CLASS__, 'bootstrap_importer'), 1);
            add_action('admin_menu', array(__CLASS__, 'menu'));
            add_action('admin_post_land76_release_backup', array(__CLASS__, 'backup_action'));
            add_action('admin_post_land76_release_apply', array(__CLASS__, 'apply_action'));
            add_action('admin_post_land76_release_stage', array(__CLASS__, 'stage_action'));
            add_action('admin_post_land76_release_download', array(__CLASS__, 'download_action'));
        }
    }

    public static function expected(): array { return require __DIR__ . '/frozen-expectations.php'; }
    /** Show administrators a safe activation failure code instead of a generic WordPress fatal screen. */
    public static function activate(): void {
        try {
            self::activation_preflight();
        } catch (Throwable $error) {
            wp_die(esc_html(self::activation_error_code($error)), 500);
        }
    }
    public static function activation_preflight(): void {
        self::assert_durability_preflight();
        self::storage_root(true); self::require_ziparchive();
        self::sync_directory(self::storage_root(false));
        if (!function_exists('proc_open') || !defined('PHP_BINARY') || PHP_BINARY === '') self::fail('ACTIVATION_LINT_UNAVAILABLE');
        self::with_lock(static function (): void {
            self::cleanup_known_stage_workspaces();
            $state_status = self::read_checked_file(self::state_file(), 'state');
            $journal_status = self::read_checked_file(self::journal_file(), 'journal');
            if ($state_status['status'] === 'missing' && $journal_status['status'] === 'missing') {
                self::cleanup_release_owned_temp(self::durable_temp_path(self::state_file()));
                self::cleanup_release_owned_temp(self::durable_temp_path(self::journal_file()));
                $storage = self::storage_root(false);
                $storage_pins = self::pin_directory_namespace($storage, 'ACTIVATION_STORAGE_NAMESPACE_RACE');
                try {
                    self::verify_directory_namespace($storage_pins, 'ACTIVATION_STORAGE_NAMESPACE_RACE');
                    $entries = scandir($storage);
                    if (!is_array($entries)) self::fail('ACTIVATION_STORAGE_SCAN_FAILED');
                    self::verify_directory_namespace($storage_pins, 'ACTIVATION_STORAGE_NAMESPACE_RACE');
                    foreach ($entries as $entry) {
                        if ($entry === '.' || $entry === '..') continue;
                        if ($entry !== 'operation.lock') self::fail('ACTIVATION_STORAGE_NOT_EMPTY');
                        $lock = $storage . DIRECTORY_SEPARATOR . $entry;
                        $stat = @lstat($lock);
                        if (!is_array($stat) || self::path_is_link_or_reparse($lock, $stat) || (($stat['mode'] & 0170000) !== 0100000)) self::fail('ACTIVATION_STORAGE_UNSAFE');
                    }
                    self::verify_directory_namespace($storage_pins, 'ACTIVATION_STORAGE_NAMESPACE_RACE');
                } finally {
                    self::close_directory_namespace($storage_pins);
                }
                $expected = self::save(self::default_state());
                $actual = self::read_state_required();
                if (!hash_equals((string)$expected['checksum'], (string)$actual['checksum'])) self::fail('ACTIVATION_STATE_VERIFY_FAILED');
                return;
            }
            $state = array();
            self::recover_journal($state);
        });
    }
    private static function activation_error_code(Throwable $error): string {
        $message = $error->getMessage();
        if (in_array($message, self::ACTIVATION_ERROR_CODES, true)) return $message;
        return match ($message) {
            'ZipArchive is unavailable. This deployer fails closed; install/enable PHP Zip before use.' => 'ACTIVATION_ZIPARCHIVE_UNAVAILABLE',
            'The parent of ABSPATH is not writable; refusing to store rollback data in the public document root.' => 'ACTIVATION_STORAGE_PARENT_UNWRITABLE',
            default => 'ACTIVATION_PREFLIGHT_FAILED',
        };
    }
    public static function early_recovery(): void {
        // A missing storage directory means activation has never initialized this plugin.
        if (!self::storage_is_initialized()) return;
        try {
            if (self::is_exact_authorized_writer_request()) {
                self::acquire_request_exclusive_lock();
                $state = array();
                self::recover_journal($state);
            } else {
                self::acquire_request_shared_lock();
            }
        }
        catch (Throwable $error) {
            if ($error->getMessage() !== 'REQUEST_LOCK_BUSY') throw $error;
            wp_die(esc_html__('Service temporarily unavailable.', 'land76-release-deployer'), 503);
        }
    }
    public static function importer_bootstrap_target(): ?string {
        if (!function_exists('is_admin') || !is_admin() || !current_user_can('manage_options') || !function_exists('get_stylesheet_directory')) return null;
        return untrailingslashit(get_stylesheet_directory()) . '/inc/import-service-hubs.php';
    }
    public static function bootstrap_importer(): void {
        $target = self::importer_bootstrap_target();
        if ($target === null) return;
        $state = self::state();
        if (($state['phases']['A1']['status'] ?? '') !== 'applied' || ($state['phases']['A2']['status'] ?? '') === 'applied') return;
        $a1_files = self::runtime_phase_files('A1');
        $a2_files = self::runtime_phase_files('A2');
        $registry = __DIR__ . '/vendor/service-hub-registry.php';
        if (!self::live_matches_phase('A1')) self::fail('A1_LIVE_HASH_MISMATCH');
        $importer_hash = $a1_files['wp-content/themes/land76wp/inc/import-service-hubs.php'] ?? null;
        $registry_hash = $a2_files['wp-content/themes/land76wp/inc/service-hub-registry.php'] ?? null;
        if (!is_string($importer_hash)) self::fail('A1_IMPORTER_HASH_MISMATCH');

        $present = array_filter(self::REGISTRY_FUNCTIONS, 'function_exists');
        if ($present === array()) {
            if (!is_string($registry_hash)) self::fail('A2_VENDOR_REGISTRY_HASH_MISMATCH');
            self::require_exact_php_file($registry, $registry_hash, 'A2_VENDOR_REGISTRY_HASH_MISMATCH');
        } elseif (count($present) !== count(self::REGISTRY_FUNCTIONS)) {
            self::fail('SERVICE_HUB_REGISTRY_PARTIAL');
        }
        foreach (self::REGISTRY_FUNCTIONS as $function) if (!function_exists($function)) self::fail('SERVICE_HUB_REGISTRY_INCOMPLETE');
        self::require_exact_php_file($target, $importer_hash, 'A1_IMPORTER_HASH_MISMATCH');
    }
    public static function all_paths(): array {
        $paths = array(); foreach (self::expected() as $phase) { foreach ($phase['files'] as $path => $hash) { $paths[$path] = $hash; } }
        ksort($paths, SORT_STRING); return $paths;
    }
    public static function default_state(): array {
        $phases = array(); foreach (self::ORDER as $phase) { $phases[$phase] = array('status' => 'pending'); }
        return array(
            'schema' => 1,
            'release_id' => self::RELEASE_ID,
            'generation' => 1,
            'backup' => array('verified' => false),
            'phases' => $phases,
            'stage_verified' => false,
            'last_error' => '',
            'last_committed_txid' => '',
        );
    }
    private static function state_file(): string {
        return self::$integration_config['state_file'] ?? (self::storage_root(false) . DIRECTORY_SEPARATOR . 'state.json');
    }
    private static function journal_file(): string {
        return self::$integration_config['journal_file'] ?? (self::storage_root(false) . DIRECTORY_SEPARATOR . 'journal.json');
    }
    private static function state(): array {
        $journal_status = self::read_checked_file(self::journal_file(), 'journal');
        if ($journal_status['status'] !== 'missing') self::fail('JOURNAL_REQUIRES_LOCKED_RECOVERY');
        return self::read_state_required();
    }
    /** Persist the only authoritative deployer state outside ABSPATH. */
    private static function save(array $state, ?callable $last_gate = null): array {
        $state = self::validate_checksummed_document(self::checksummed_document($state, 'state'), 'state');
        self::durable_write(self::state_file(), self::encode_json($state, false), 0600, $last_gate);
        return $state;
    }
    private static function save_journal(array $journal, ?callable $last_gate = null): array {
        $journal = self::validate_checksummed_document(self::checksummed_document($journal, 'journal'), 'journal');
        self::durable_write(self::journal_file(), self::encode_json($journal, false), 0600, $last_gate);
        return $journal;
    }
    private static function canonicalize(mixed $value): mixed {
        if (!is_array($value)) return $value;
        if (array_is_list($value)) return array_map(array(__CLASS__, 'canonicalize'), $value);
        ksort($value, SORT_STRING);
        foreach ($value as $key => $item) $value[$key] = self::canonicalize($item);
        return $value;
    }
    private static function encode_json(array $document, bool $canonical): string {
        try {
            $json = json_encode(
                $canonical ? self::canonicalize($document) : $document,
                JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR
            );
        } catch (Throwable $error) { self::fail('STATE_ENCODE_FAILED'); }
        if (!is_string($json)) self::fail('STATE_ENCODE_FAILED');
        return $json;
    }
    private static function ordered_map(array $source, array $order): array {
        $ordered = array();
        foreach ($order as $key) if (array_key_exists($key, $source)) { $ordered[$key] = $source[$key]; unset($source[$key]); }
        ksort($source, SORT_STRING);
        foreach ($source as $key => $value) $ordered[$key] = $value;
        return $ordered;
    }
    private static function normalize_state(array $state): array {
        $checksum = isset($state['checksum']) && is_string($state['checksum']) ? $state['checksum'] : null;
        unset($state['checksum']);
        if (isset($state['backup']) && is_array($state['backup'])) {
            $state['backup'] = self::ordered_map($state['backup'], array(
                'verified', 'zip_basename', 'zip_bytes', 'zip_sha256',
                'manifest_basename', 'manifest_bytes', 'manifest_sha256',
            ));
        }
        if (isset($state['phases']) && is_array($state['phases'])) {
            $phases = array();
            foreach (self::runtime_phase_ids() as $phase) if (isset($state['phases'][$phase])) $phases[$phase] = $state['phases'][$phase];
            foreach ($state['phases'] as $phase => $value) if (!array_key_exists($phase, $phases)) $phases[$phase] = $value;
            $state['phases'] = $phases;
        }
        $state = self::ordered_map($state, array(
            'schema', 'release_id', 'generation', 'backup', 'phases',
            'stage_verified', 'last_error', 'last_committed_txid',
        ));
        if ($checksum !== null) $state['checksum'] = $checksum;
        return $state;
    }
    private static function normalize_journal(array $journal): array {
        $checksum = isset($journal['checksum']) && is_string($journal['checksum']) ? $journal['checksum'] : null;
        unset($journal['checksum']);
        if (isset($journal['base_state']) && is_array($journal['base_state'])) $journal['base_state'] = self::normalize_state($journal['base_state']);
        if (isset($journal['target_state']) && is_array($journal['target_state'])) $journal['target_state'] = self::normalize_state($journal['target_state']);
        $journal = self::ordered_map($journal, array(
            'schema', 'release_id', 'txid', 'phase', 'base_state', 'target_state',
            'backup_sha256', 'attempted_paths', 'created_dirs', 'step',
        ));
        if ($checksum !== null) $journal['checksum'] = $checksum;
        return $journal;
    }
    private static function checksummed_document(array $document, string $kind): array {
        unset($document['checksum']);
        $document = $kind === 'journal' ? self::normalize_journal($document) : self::normalize_state($document);
        $document['checksum'] = hash('sha256', self::encode_json($document, true));
        return $kind === 'journal' ? self::normalize_journal($document) : self::normalize_state($document);
    }
    private static function validate_checksummed_document(array $document, string $kind): array {
        $checksum = $document['checksum'] ?? null;
        if (!is_string($checksum) || preg_match('/\A[a-f0-9]{64}\z/', $checksum) !== 1) self::fail(strtoupper($kind) . '_CHECKSUM_MISSING');
        unset($document['checksum']);
        if (!hash_equals($checksum, hash('sha256', self::encode_json($document, true)))) self::fail(strtoupper($kind) . '_CHECKSUM_INVALID');
        $document['checksum'] = $checksum;
        $document = $kind === 'journal' ? self::normalize_journal($document) : self::normalize_state($document);
        return $kind === 'journal' ? self::validate_journal_document($document) : self::validate_state_document($document);
    }
    private static function read_checked_file(string $path, string $kind): array {
        $pins = array();
        try {
            $pins = self::pin_directory_namespace(dirname($path), strtoupper($kind) . '_NAMESPACE_RACE');
            self::verify_directory_namespace($pins, strtoupper($kind) . '_NAMESPACE_RACE');
            clearstatcache(true, $path);
            $stat = @lstat($path);
            if (!is_array($stat)) {
                if (file_exists($path) || is_link($path)) return array('status' => 'invalid', 'document' => null);
                self::verify_directory_namespace($pins, strtoupper($kind) . '_NAMESPACE_RACE');
                return array('status' => 'missing', 'document' => null);
            }
            self::assert_safe_storage_regular_file($path);
            $bytes = self::read_regular_file_in_pinned_namespace($path, strtoupper($kind) . '_READ_RACE');
            self::verify_directory_namespace($pins, strtoupper($kind) . '_NAMESPACE_RACE');
        } catch (Throwable $error) { return array('status' => 'invalid', 'document' => null); }
        finally { self::close_directory_namespace($pins); }
        try { $document = json_decode($bytes, true, 64, JSON_THROW_ON_ERROR); }
        catch (Throwable $error) { return array('status' => 'invalid', 'document' => null); }
        if (!is_array($document) || array_is_list($document)) return array('status' => 'invalid', 'document' => null);
        try { return array('status' => 'valid', 'document' => self::validate_checksummed_document($document, $kind)); }
        catch (Throwable $error) { return array('status' => 'invalid', 'document' => null); }
    }
    private static function read_state_required(): array {
        $status = self::read_checked_file(self::state_file(), 'state');
        if ($status['status'] !== 'valid' || !is_array($status['document'])) self::fail('STATE_CORRUPT_OR_MISSING');
        return $status['document'];
    }
    private static function validate_state_document(array $state): array {
        if (($state['schema'] ?? null) !== 1 || !is_string($state['release_id'] ?? null) || $state['release_id'] === '') self::fail('STATE_SCHEMA_INVALID');
        if (self::$integration_config === null && !hash_equals(self::RELEASE_ID, $state['release_id'])) self::fail('STATE_RELEASE_INVALID');
        if (!is_int($state['generation'] ?? null) || $state['generation'] < 1) self::fail('STATE_GENERATION_INVALID');
        if (!is_array($state['backup'] ?? null) || !is_array($state['phases'] ?? null) || !is_string($state['last_committed_txid'] ?? null)) self::fail('STATE_SHAPE_INVALID');
        foreach (self::runtime_phase_ids() as $phase) {
            $status = $state['phases'][$phase]['status'] ?? null;
            if (!is_string($status) || !in_array($status, array('pending', 'applied'), true)) self::fail('STATE_PHASE_INVALID');
        }
        if (!array_key_exists('verified', $state['backup']) || !is_bool($state['backup']['verified'])) self::fail('BACKUP_VERIFIED_BOOLEAN_INVALID');
        if ($state['backup']['verified']) self::validate_backup_metadata($state['backup']);
        return self::normalize_state($state);
    }
    private static function validate_backup_metadata(array $backup): void {
        if (($backup['zip_basename'] ?? null) !== 'rollback.zip' || ($backup['manifest_basename'] ?? null) !== 'rollback-manifest.json') self::fail('BACKUP_METADATA_INVALID');
        if (hash_equals($backup['zip_basename'], $backup['manifest_basename'])) self::fail('BACKUP_METADATA_INVALID');
        foreach (array('zip_bytes', 'manifest_bytes') as $key) if (!isset($backup[$key]) || !is_int($backup[$key]) || $backup[$key] < 1) self::fail('BACKUP_METADATA_INVALID');
        foreach (array('zip_sha256', 'manifest_sha256') as $key) if (!isset($backup[$key]) || !is_string($backup[$key]) || preg_match('/\A[a-f0-9]{64}\z/', $backup[$key]) !== 1) self::fail('BACKUP_METADATA_INVALID');
    }
    private static function validate_integration_config(array $config): array {
        foreach (array('docroot', 'storage_root', 'state_file', 'journal_file', 'expected_phases') as $key) if (!isset($config[$key])) self::fail('INTEGRATION_CONFIG_INVALID');
        foreach (array('docroot', 'storage_root', 'state_file', 'journal_file') as $key) if (!is_string($config[$key]) || $config[$key] === '') self::fail('INTEGRATION_CONFIG_INVALID');
        if (!is_dir($config['docroot']) || !is_dir($config['storage_root']) || is_link($config['docroot']) || is_link($config['storage_root'])) self::fail('INTEGRATION_CONFIG_INVALID');
        $storage = rtrim($config['storage_root'], '/\\');
        if (dirname($config['state_file']) !== $storage || dirname($config['journal_file']) !== $storage || basename($config['state_file']) !== 'state.json' || basename($config['journal_file']) !== 'journal.json') self::fail('INTEGRATION_CONFIG_INVALID');
        if (!is_array($config['expected_phases']) || !is_callable($config['read_option'] ?? null) || !is_callable($config['sync_directory'] ?? null) || !is_callable($config['mode_adapter'] ?? null)) self::fail('INTEGRATION_CONFIG_INVALID');
        foreach ($config['expected_phases'] as $phase => $files) {
            if (!is_string($phase) || $phase === '' || !is_array($files)) self::fail('INTEGRATION_CONFIG_INVALID');
            foreach ($files as $path => $hash) {
                if (!is_string($path) || !is_string($hash) || preg_match('/\A[a-f0-9]{64}\z/', $hash) !== 1) self::fail('INTEGRATION_CONFIG_INVALID');
                self::validate_path($path);
            }
        }
        foreach (array('before_destination_rename', 'before_namespace_mutation', 'before_state_rename', 'before_journal_clear', 'after_backup_hashes', 'after_lock_acquired') as $callback) {
            if (array_key_exists($callback, $config) && !is_callable($config[$callback])) self::fail('INTEGRATION_CONFIG_INVALID');
        }
        $config['docroot'] = rtrim($config['docroot'], '/\\');
        $config['storage_root'] = $storage;
        return $config;
    }
    private static function with_integration_config(array $config, callable $operation): mixed {
        if (self::$integration_config !== null) self::fail('INTEGRATION_CONFIG_REENTRANT');
        self::$integration_config = $config;
        try { return $operation(); }
        finally { self::$integration_config = null; }
    }
    private static function runtime_phase_ids(): array {
        return self::$integration_config !== null ? array_keys(self::$integration_config['expected_phases']) : self::ORDER;
    }
    private static function runtime_phase_files(string $phase): array {
        if (self::$integration_config !== null) return self::$integration_config['expected_phases'][$phase] ?? array();
        $expected = self::expected();
        return isset($expected[$phase]['files']) && is_array($expected[$phase]['files']) ? $expected[$phase]['files'] : array();
    }
    private static function runtime_all_paths(): array {
        $paths = array();
        foreach (self::runtime_phase_ids() as $phase) foreach (self::runtime_phase_files($phase) as $path => $hash) $paths[$path] = $hash;
        ksort($paths, SORT_STRING);
        return $paths;
    }
    private static function runtime_option(string $key, mixed $default = false): mixed {
        if (self::$integration_config !== null) return (self::$integration_config['read_option'])($key, $default);
        return function_exists('get_option') ? get_option($key, $default) : $default;
    }
    private static function assert_phase_invariant(string $phase): void {
        if ($phase === 'B' && self::runtime_option('land76_service_hubs_active_release_id', '') !== self::HUB_RELEASE_ID) {
            self::fail('PHASE_B_INVARIANT_DRIFT');
        }
    }
    private static function sync_file_handle($handle, string $error): void {
        if (!function_exists('fsync') || !@fsync($handle)) self::fail($error);
    }
    private static function sync_regular_file(string $path, string $error): void {
        $pins = self::pin_directory_namespace(dirname($path), $error);
        $handle = null;
        try {
            self::verify_directory_namespace($pins, $error);
            clearstatcache(true, $path);
            $stat = @lstat($path);
            if (!is_array($stat) || self::path_is_link_or_reparse($path, $stat) || (($stat['mode'] & 0170000) !== 0100000)) self::fail($error);
            self::namespace_failpoint('regular_file_sync_open', $path);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($path, $stat, 0100000, $error);
            $handle = @fopen($path, 'r+b');
            if (!is_resource($handle)) self::fail($error);
            $opened = self::assert_path_handle_identity($path, $handle, $error);
            if (($opened['dev'] ?? null) !== ($stat['dev'] ?? null) || ($opened['ino'] ?? null) !== ($stat['ino'] ?? null)) self::fail($error);
            self::sync_file_handle($handle, $error);
            self::assert_path_handle_identity($path, $handle, $error);
            self::verify_directory_namespace($pins, $error);
        }
        finally {
            if (is_resource($handle)) fclose($handle);
            self::close_directory_namespace($pins);
        }
    }
    private static function assert_path_handle_identity(string $path, $handle, string $error): array {
        clearstatcache(true, $path);
        $path_stat = @lstat($path); $handle_stat = is_resource($handle) ? fstat($handle) : false;
        if (!is_array($path_stat) || !is_array($handle_stat) || self::path_is_link_or_reparse($path, $path_stat) || (($path_stat['mode'] & 0170000) !== 0100000) || (($handle_stat['mode'] & 0170000) !== 0100000)) self::fail($error);
        if (($path_stat['dev'] ?? null) !== ($handle_stat['dev'] ?? null) || ($path_stat['ino'] ?? null) !== ($handle_stat['ino'] ?? null)) self::fail($error);
        return $path_stat;
    }
    /**
     * PHP has no openat/renameat/unlinkat API. On production POSIX we therefore
     * retain handles for every directory in the managed chain and revalidate
     * each (dev, ino) immediately around pathname operations. This fails closed
     * on deterministic namespace replacement, but the supported threat model
     * excludes an active same-UID filesystem attacker racing the final check
     * and the following pathname syscall.
     */
    private static function pin_directory_namespace(string $directory, string $error): array {
        $directory = self::normalize_directory_path($directory);
        if ($directory === '') self::fail($error);
        $anchor = self::namespace_anchor_for($directory);
        if ($anchor === '' || !self::path_is_within($directory, $anchor)) self::fail($error);
        $paths = array($anchor);
        if (!self::paths_equal($directory, $anchor)) {
            $relative = ltrim(substr($directory, strlen($anchor)), DIRECTORY_SEPARATOR);
            $current = $anchor;
            foreach (explode(DIRECTORY_SEPARATOR, $relative) as $segment) {
                if ($segment === '' || $segment === '.' || $segment === '..') self::fail($error);
                $current = rtrim($current, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $segment;
                $paths[] = $current;
            }
        }
        $pins = array();
        try {
            foreach ($paths as $path) {
                clearstatcache(true, $path);
                $stat = @lstat($path);
                if (!is_array($stat)) self::fail_namespace($error, 'PIN_LSTAT_FAILED');
                if (self::path_is_link_or_reparse($path, $stat)) self::fail_namespace($error, 'PIN_LINK_REFUSED');
                if (($stat['mode'] & 0170000) !== 0040000) self::fail_namespace($error, 'PIN_NOT_DIRECTORY');
                $handle = null;
                if (DIRECTORY_SEPARATOR === '/') {
                    $handle = @fopen($path, 'rb');
                    if (!is_resource($handle)) self::fail_namespace($error, 'PIN_OPEN_FAILED');
                    $handle_stat = @fstat($handle);
                    if (!is_array($handle_stat)) { fclose($handle); self::fail_namespace($error, 'PIN_FSTAT_FAILED'); }
                    if (($handle_stat['mode'] & 0170000) !== 0040000) { fclose($handle); self::fail_namespace($error, 'PIN_HANDLE_NOT_DIRECTORY'); }
                    if (!self::same_stat_identity($stat, $handle_stat)) { fclose($handle); self::fail_namespace($error, 'PIN_IDENTITY_MISMATCH'); }
                } elseif (self::$integration_config === null) self::fail('NAMESPACE_PIN_UNSUPPORTED');
                $pins[] = array('path' => $path, 'stat' => $stat, 'handle' => $handle);
            }
            return $pins;
        } catch (Throwable $caught) {
            self::close_directory_namespace($pins);
            throw $caught;
        }
    }
    private static function verify_directory_namespace(array $pins, string $error): void {
        if ($pins === array()) self::fail($error);
        foreach ($pins as $pin) {
            $path = $pin['path']; $expected = $pin['stat']; $handle = $pin['handle'];
            clearstatcache(true, $path);
            $actual = @lstat($path);
            if (!is_array($actual)) self::fail_namespace($error, 'VERIFY_LSTAT_FAILED');
            if (self::path_is_link_or_reparse($path, $actual)) self::fail_namespace($error, 'VERIFY_LINK_REFUSED');
            if (($actual['mode'] & 0170000) !== 0040000) self::fail_namespace($error, 'VERIFY_NOT_DIRECTORY');
            if (!self::same_stat_identity($actual, $expected)) self::fail_namespace($error, 'VERIFY_IDENTITY_MISMATCH');
            if (is_resource($handle)) {
                $handle_stat = @fstat($handle);
                if (!is_array($handle_stat) || (($handle_stat['mode'] & 0170000) !== 0040000) || !self::same_stat_identity($handle_stat, $expected)) self::fail_namespace($error, 'VERIFY_HANDLE_FAILED');
            }
        }
    }
    private static function same_stat_identity(array $left, array $right): bool {
        foreach (array('dev', 'ino') as $key) {
            if (!array_key_exists($key, $left) || !array_key_exists($key, $right) || !is_int($left[$key]) || !is_int($right[$key]) || $left[$key] !== $right[$key]) return false;
        }
        return true;
    }
    private static function normalize_directory_path(string $path): string {
        $path = str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $path);
        if ($path === DIRECTORY_SEPARATOR || preg_match('/\A[A-Za-z]:\\\\\z/', $path) === 1) return $path;
        return rtrim($path, DIRECTORY_SEPARATOR);
    }
    private static function paths_equal(string $left, string $right): bool {
        $left = self::normalize_directory_path($left); $right = self::normalize_directory_path($right);
        return DIRECTORY_SEPARATOR === '\\' ? strcasecmp($left, $right) === 0 : $left === $right;
    }
    private static function path_is_within(string $path, string $root): bool {
        $path = self::normalize_directory_path($path); $root = self::normalize_directory_path($root);
        if (self::paths_equal($path, $root)) return true;
        $compare_path = DIRECTORY_SEPARATOR === '\\' ? strtolower($path) : $path;
        $compare_root = DIRECTORY_SEPARATOR === '\\' ? strtolower($root) : $root;
        return str_starts_with($compare_path, rtrim($compare_root, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR);
    }
    /** Host-owned ancestors may be execute-only; pin every node inside the managed namespace. */
    private static function namespace_anchor_for(string $directory): string {
        $directory = self::normalize_directory_path($directory);
        $storage = self::normalize_directory_path(self::storage_path());
        $upload_tmp = ini_get('upload_tmp_dir');
        $wordpress_tmp = function_exists('get_temp_dir') ? get_temp_dir() : '';
        $candidates = array(
            self::normalize_directory_path(self::docroot()),
            self::normalize_directory_path(__DIR__),
            $storage,
            self::normalize_directory_path(dirname($storage)),
            self::normalize_directory_path(sys_get_temp_dir()),
            self::normalize_directory_path(is_string($upload_tmp) ? $upload_tmp : ''),
            self::normalize_directory_path(is_string($wordpress_tmp) ? $wordpress_tmp : ''),
        );
        $anchor = ''; $best_length = -1;
        foreach (array_unique($candidates) as $candidate) {
            if ($candidate !== '' && self::path_is_within($directory, $candidate) && strlen($candidate) > $best_length) {
                $anchor = $candidate; $best_length = strlen($candidate);
            }
        }
        return $anchor;
    }
    /** Preserve legacy failure contracts while exposing only safe target-preflight failure classes. */
    private static function fail_namespace(string $error, string $detail): void {
        self::fail($error === 'DIRECTORY_SYNC_TARGET_UNSAFE' ? 'DIRECTORY_SYNC_' . $detail : $error);
    }
    private static function close_directory_namespace(array $pins): void {
        foreach (array_reverse($pins) as $pin) if (is_resource($pin['handle'] ?? null)) fclose($pin['handle']);
    }
    private static function namespace_failpoint(string $operation, string $path): void {
        if (self::$integration_config !== null && isset(self::$integration_config['before_namespace_mutation'])) (self::$integration_config['before_namespace_mutation'])($operation, $path);
    }
    private static function assert_path_identity_type(string $path, array $expected, int $type, string $error): array {
        clearstatcache(true, $path);
        $actual = @lstat($path);
        if (!is_array($actual) || self::path_is_link_or_reparse($path, $actual) || (($actual['mode'] & 0170000) !== $type)) self::fail($error);
        if (($actual['dev'] ?? null) !== ($expected['dev'] ?? null) || ($actual['ino'] ?? null) !== ($expected['ino'] ?? null)) self::fail($error);
        return $actual;
    }
    /** Unlink one already-owned regular file while its complete parent chain remains pinned. */
    private static function unlink_regular_in_pinned_namespace(string $path, string $error, string $namespace_error, string $operation, ?callable $last_gate = null): bool {
        $parent = dirname($path);
        $pins = self::pin_directory_namespace($parent, $namespace_error);
        try {
            self::verify_directory_namespace($pins, $namespace_error);
            clearstatcache(true, $path);
            $expected = @lstat($path);
            if (!is_array($expected)) {
                if (file_exists($path) || is_link($path)) self::fail($error);
                return false;
            }
            if (self::path_is_link_or_reparse($path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) self::fail($error);
            self::namespace_failpoint($operation, $path);
            self::verify_directory_namespace($pins, $namespace_error);
            self::assert_path_identity_type($path, $expected, 0100000, $namespace_error);
            if ($last_gate !== null) $last_gate();
            if (!@unlink($path)) self::fail($error);
            self::verify_directory_namespace($pins, $namespace_error);
            clearstatcache(true, $path);
            if (@lstat($path) !== false || file_exists($path) || is_link($path)) self::fail($namespace_error);
            self::sync_directory($parent);
            return true;
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    /** Remove one empty owned directory while retaining its inode and every parent directory handle. */
    private static function rmdir_empty_in_pinned_namespace(string $path, string $error, string $namespace_error, string $operation): void {
        $pins = self::pin_directory_namespace($path, $namespace_error);
        $leaf_pin = $pins[count($pins) - 1] ?? null;
        $parent_pins = array_slice($pins, 0, -1);
        if (!is_array($leaf_pin) || $parent_pins === array()) {
            self::close_directory_namespace($pins);
            self::fail($namespace_error);
        }
        try {
            self::verify_directory_namespace($pins, $namespace_error);
            self::namespace_failpoint($operation, $path);
            self::verify_directory_namespace($pins, $namespace_error);
            if (!@rmdir($path)) self::fail($error);
            self::verify_directory_namespace($parent_pins, $namespace_error);
            $leaf_handle = $leaf_pin['handle'] ?? null;
            if (is_resource($leaf_handle)) {
                $handle_stat = fstat($leaf_handle); $expected = $leaf_pin['stat'];
                if (!is_array($handle_stat) || (($handle_stat['mode'] & 0170000) !== 0040000) || ($handle_stat['dev'] ?? null) !== ($expected['dev'] ?? null) || ($handle_stat['ino'] ?? null) !== ($expected['ino'] ?? null)) self::fail($namespace_error);
            }
            clearstatcache(true, $path);
            if (@lstat($path) !== false || file_exists($path) || is_link($path)) self::fail($namespace_error);
            self::sync_directory(dirname($path));
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    /** Create one directory only after pinning and revalidating the complete parent chain. */
    private static function mkdir_in_pinned_namespace(string $path, int $mode, string $error, string $namespace_error, string $operation): void {
        $parent = dirname($path);
        $pins = self::pin_directory_namespace($parent, $namespace_error);
        try {
            self::verify_directory_namespace($pins, $namespace_error);
            clearstatcache(true, $path);
            if (@lstat($path) !== false || file_exists($path) || is_link($path)) self::fail($error);
            self::namespace_failpoint($operation, $path);
            self::verify_directory_namespace($pins, $namespace_error);
            clearstatcache(true, $path);
            if (@lstat($path) !== false || file_exists($path) || is_link($path)) self::fail($namespace_error);
            if (!@mkdir($path, $mode)) self::fail($error);
            self::verify_directory_namespace($pins, $namespace_error);
            clearstatcache(true, $path);
            $created = @lstat($path);
            if (!is_array($created) || self::path_is_link_or_reparse($path, $created) || (($created['mode'] & 0170000) !== 0040000)) self::fail($namespace_error);
            self::set_directory_mode_exact($path, $mode, $error);
            self::assert_path_identity_type($path, $created, 0040000, $namespace_error);
            self::sync_directory($parent);
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    private static function verify_mode_exact(string $path, int $mode, string $error): void {
        if ($mode < 0 || $mode > 0777) self::fail($error);
        $pins = self::pin_directory_namespace(dirname($path), $error);
        try {
            self::verify_directory_namespace($pins, $error);
            if (self::$integration_config !== null) {
                if ((self::$integration_config['mode_adapter'])('verify', $path, $mode) !== true) self::fail($error);
            } else {
                if (DIRECTORY_SEPARATOR !== '/') self::fail('POSIX_MODE_UNSUPPORTED');
                clearstatcache(true, $path);
                $stat = @lstat($path);
                if (!is_array($stat) || self::path_is_link_or_reparse($path, $stat) || (($stat['mode'] & 0170000) !== 0100000) || (($stat['mode'] & 0777) !== $mode)) self::fail($error);
            }
            self::verify_directory_namespace($pins, $error);
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    private static function set_mode_exact(string $path, int $mode, string $error): void {
        if ($mode < 0 || $mode > 0777) self::fail($error);
        $pins = self::pin_directory_namespace(dirname($path), $error);
        try {
            self::verify_directory_namespace($pins, $error);
            clearstatcache(true, $path);
            $expected = @lstat($path);
            if (!is_array($expected) || self::path_is_link_or_reparse($path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) self::fail($error);
            if (self::$integration_config !== null) {
                if ((self::$integration_config['mode_adapter'])('set', $path, $mode) !== true) self::fail($error);
            } elseif (DIRECTORY_SEPARATOR !== '/' || !@chmod($path, $mode)) self::fail($error);
            self::assert_path_identity_type($path, $expected, 0100000, $error);
            self::verify_directory_namespace($pins, $error);
            self::verify_mode_exact($path, $mode, $error);
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    /** Persist directory-entry metadata on POSIX; tests on other hosts must inject an exact adapter. */
    private static function sync_directory(string $directory): void {
        $directory = str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $directory);
        if ($directory !== DIRECTORY_SEPARATOR && preg_match('/\A[A-Za-z]:\\\\?\z/', $directory) !== 1) $directory = rtrim($directory, DIRECTORY_SEPARATOR);
        $pins = self::pin_directory_namespace($directory, 'DIRECTORY_SYNC_TARGET_UNSAFE');
        try {
            self::verify_directory_namespace($pins, 'DIRECTORY_SYNC_TARGET_UNSAFE');
            if (self::$integration_config !== null) {
                if ((self::$integration_config['sync_directory'])($directory) !== true) self::fail('DIRECTORY_SYNC_FAILED');
            } else {
                if (DIRECTORY_SEPARATOR !== '/' || !function_exists('fsync')) self::fail('DIRECTORY_SYNC_UNSUPPORTED');
                $leaf_pin = $pins[count($pins) - 1] ?? null;
                $handle = is_array($leaf_pin) ? ($leaf_pin['handle'] ?? null) : null;
                if (!is_resource($handle)) self::fail('DIRECTORY_SYNC_OPEN_FAILED');
                if (!@fsync($handle)) self::fail('DIRECTORY_SYNC_FAILED');
            }
            self::verify_directory_namespace($pins, 'DIRECTORY_SYNC_TARGET_UNSAFE');
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    private static function assert_durability_preflight(): void {
        if (self::$integration_config === null && (DIRECTORY_SEPARATOR !== '/' || !function_exists('fsync'))) self::fail('DIRECTORY_SYNC_UNSUPPORTED');
        $storage = self::storage_path();
        self::sync_directory(dirname($storage));
        if (is_dir($storage) && !is_link($storage)) self::sync_directory($storage);
    }
    private static function durable_temp_path(string $path): string {
        return dirname($path) . DIRECTORY_SEPARATOR . '.' . basename($path) . '.write.tmp';
    }
    private static function durable_write(string $path, string $bytes, int $mode, ?callable $last_gate = null): void {
        $temp = self::durable_temp_path($path);
        $pins = self::pin_directory_namespace(dirname($path), 'STATE_NAMESPACE_RACE');
        $handle = null;
        $temp_identity = null;
        try {
            self::verify_directory_namespace($pins, 'STATE_NAMESPACE_RACE');
            self::cleanup_release_owned_temp($temp);
            self::verify_directory_namespace($pins, 'STATE_NAMESPACE_RACE');
            $handle = @fopen($temp, 'x+b'); if (!is_resource($handle)) self::fail('STATE_TEMP_CREATE_FAILED');
            try {
                $temp_identity = fstat($handle);
                if (!is_array($temp_identity) || (($temp_identity['mode'] & 0170000) !== 0100000)) self::fail('STATE_TEMP_RACE');
                self::assert_path_handle_identity($temp, $handle, 'STATE_TEMP_RACE');
                self::write_all($handle, $bytes);
                if (!fflush($handle)) self::fail('STATE_WRITE_FAILED');
                self::assert_path_handle_identity($temp, $handle, 'STATE_TEMP_RACE');
                self::set_mode_exact($temp, $mode, 'STATE_MODE_FAILED');
                self::assert_path_handle_identity($temp, $handle, 'STATE_TEMP_RACE');
                self::sync_file_handle($handle, 'STATE_SYNC_FAILED');
                self::assert_path_handle_identity($temp, $handle, 'STATE_TEMP_RACE');
            }
            finally { if (is_resource($handle)) { fclose($handle); $handle = null; } }
            if (!is_array($temp_identity)) self::fail('STATE_TEMP_RACE');
            self::assert_path_identity_type($temp, $temp_identity, 0100000, 'STATE_TEMP_RACE');
            if (self::$integration_config !== null && $path === self::state_file() && isset(self::$integration_config['before_state_rename'])) (self::$integration_config['before_state_rename'])();
            self::namespace_failpoint('durable_rename', $path);
            self::verify_directory_namespace($pins, 'STATE_NAMESPACE_RACE');
            self::assert_path_identity_type($temp, $temp_identity, 0100000, 'STATE_TEMP_RACE');
            if ($last_gate !== null) $last_gate();
            if (!@rename($temp, $path)) self::fail('STATE_RENAME_FAILED');
            self::verify_directory_namespace($pins, 'STATE_NAMESPACE_RACE');
            self::assert_path_identity_type($path, $temp_identity, 0100000, 'STATE_TEMP_RACE');
            try { self::sync_directory(dirname($path)); }
            catch (Throwable $error) { self::fail('DURABLE_COMMIT_UNCERTAIN_AFTER_RENAME:' . basename($path) . ':' . $error->getMessage()); }
            self::assert_path_identity_type($path, $temp_identity, 0100000, 'STATE_TEMP_RACE');
        } finally {
            if (is_resource($handle)) fclose($handle);
            try {
                self::verify_directory_namespace($pins, 'STATE_NAMESPACE_RACE');
                self::cleanup_release_owned_temp($temp);
            } finally {
                self::close_directory_namespace($pins);
            }
        }
    }
    private static function fail(string $message): void { throw new RuntimeException($message); }
    /** @return resource */
    private static function open_operation_lock() {
        $storage = self::storage_root(false);
        $lock_path = $storage . DIRECTORY_SEPARATOR . 'operation.lock';
        $pins = self::pin_directory_namespace($storage, 'LOCK_NAMESPACE_RACE');
        $handle = null;
        try {
            self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
            clearstatcache(true, $lock_path);
            $path_stat = @lstat($lock_path);
            $expected_path_stat = null;
            self::namespace_failpoint('lock_open', $lock_path);
            self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
            if (is_array($path_stat)) self::assert_path_identity_type($lock_path, $path_stat, 0100000, 'LOCK_PATH_RACE');
            $created = false;
            if (is_array($path_stat)) {
                if (self::path_is_link_or_reparse($lock_path, $path_stat) || (($path_stat['mode'] & 0170000) !== 0100000)) self::fail('LOCK_PATH_UNSAFE');
                $expected_path_stat = $path_stat;
                $handle = @fopen($lock_path, 'r+b');
            } else {
                if (file_exists($lock_path) || is_link($lock_path)) self::fail('LOCK_PATH_LSTAT_FAILED');
                $handle = @fopen($lock_path, 'x+b');
                $created = is_resource($handle);
                if (!$created) {
                    clearstatcache(true, $lock_path);
                    $path_stat = @lstat($lock_path);
                    if (!is_array($path_stat) || self::path_is_link_or_reparse($lock_path, $path_stat) || (($path_stat['mode'] & 0170000) !== 0100000)) self::fail('LOCK_OPEN_FAILED');
                    $expected_path_stat = $path_stat;
                    $handle = @fopen($lock_path, 'r+b');
                }
            }
            if (!is_resource($handle)) self::fail('LOCK_OPEN_FAILED');
            self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
            clearstatcache(true, $lock_path);
            $path_stat = @lstat($lock_path); $handle_stat = fstat($handle);
            if (!is_array($path_stat) || !is_array($handle_stat) || self::path_is_link_or_reparse($lock_path, $path_stat) || (($path_stat['mode'] & 0170000) !== 0100000)) self::fail('LOCK_PATH_UNSAFE');
            if (($path_stat['dev'] ?? null) !== ($handle_stat['dev'] ?? null) || ($path_stat['ino'] ?? null) !== ($handle_stat['ino'] ?? null)) self::fail('LOCK_PATH_RACE');
            if (is_array($expected_path_stat) && (($path_stat['dev'] ?? null) !== ($expected_path_stat['dev'] ?? null) || ($path_stat['ino'] ?? null) !== ($expected_path_stat['ino'] ?? null))) self::fail('LOCK_PATH_RACE');
            if ($created) {
                if (!fflush($handle)) self::fail('LOCK_INITIALIZE_FAILED');
                self::set_mode_exact($lock_path, 0600, 'LOCK_INITIALIZE_FAILED');
                self::sync_file_handle($handle, 'LOCK_INITIALIZE_FAILED');
                self::sync_directory(dirname($lock_path));
            } else self::verify_mode_exact($lock_path, 0600, 'LOCK_MODE_INVALID');
            self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
            self::$lock_namespace_pins[(int)$handle] = $pins;
            return $handle;
        } catch (Throwable $error) {
            if (is_resource($handle)) fclose($handle);
            self::close_directory_namespace($pins);
            throw $error;
        }
    }
    private static function close_operation_lock($handle): void {
        $key = is_resource($handle) ? (int)$handle : -1;
        if (is_resource($handle)) fclose($handle);
        if (isset(self::$lock_namespace_pins[$key])) {
            self::close_directory_namespace(self::$lock_namespace_pins[$key]);
            unset(self::$lock_namespace_pins[$key]);
        }
    }
    private static function validate_acquired_lock($handle, string $mode): void {
        $pins = self::$lock_namespace_pins[(int)$handle] ?? null;
        if (!is_array($pins)) self::fail('LOCK_NAMESPACE_RACE');
        self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
        $storage_pin = $pins[count($pins) - 1] ?? null;
        if (!is_array($storage_pin) || !is_string($storage_pin['path'] ?? null)) self::fail('LOCK_NAMESPACE_RACE');
        $lock_path = $storage_pin['path'] . DIRECTORY_SEPARATOR . 'operation.lock';
        if (self::$integration_config !== null && isset(self::$integration_config['after_lock_acquired'])) (self::$integration_config['after_lock_acquired'])($mode, $lock_path);
        self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
        self::assert_path_handle_identity($lock_path, $handle, 'LOCK_PATH_RACE');
    }
    private static function validate_retained_lock($handle): void {
        $pins = self::$lock_namespace_pins[(int)$handle] ?? null;
        if (!is_array($pins)) self::fail('LOCK_NAMESPACE_RACE');
        self::verify_directory_namespace($pins, 'LOCK_NAMESPACE_RACE');
        $storage_pin = $pins[count($pins) - 1] ?? null;
        if (!is_array($storage_pin) || !is_string($storage_pin['path'] ?? null)) self::fail('LOCK_NAMESPACE_RACE');
        self::assert_path_handle_identity($storage_pin['path'] . DIRECTORY_SEPARATOR . 'operation.lock', $handle, 'LOCK_PATH_RACE');
    }
    private static function with_lock(callable $operation): mixed {
        if (is_resource(self::$request_lock)) {
            if (self::$request_lock_mode !== 'EX') self::fail('LOCK_BUSY');
            self::validate_acquired_lock(self::$request_lock, 'EX');
            try { return $operation(); }
            finally { self::validate_retained_lock(self::$request_lock); }
        }
        $handle = self::open_operation_lock();
        if (!@flock($handle, LOCK_EX | LOCK_NB)) { self::close_operation_lock($handle); self::fail('LOCK_BUSY'); }
        try { self::validate_acquired_lock($handle, 'EX'); }
        catch (Throwable $error) { @flock($handle, LOCK_UN); self::close_operation_lock($handle); throw $error; }
        try { return $operation(); }
        finally {
            try { self::validate_retained_lock($handle); }
            finally { @flock($handle, LOCK_UN); self::close_operation_lock($handle); }
        }
    }
    private static function release_request_lock(): void {
        if (!is_resource(self::$request_lock)) { self::$request_lock = null; self::$request_lock_mode = null; return; }
        @flock(self::$request_lock, LOCK_UN);
        self::close_operation_lock(self::$request_lock);
        self::$request_lock = null;
        self::$request_lock_mode = null;
    }
    private static function retain_request_lock($handle, string $mode): void {
        self::$request_lock = $handle;
        self::$request_lock_mode = $mode;
        if (!self::$request_lock_shutdown_registered) {
            register_shutdown_function(static function (): void { self::release_request_lock(); });
            self::$request_lock_shutdown_registered = true;
        }
    }
    private static function acquire_request_exclusive_lock(): void {
        if (is_resource(self::$request_lock)) {
            if (self::$request_lock_mode !== 'EX') self::fail('REQUEST_LOCK_BUSY');
            self::validate_acquired_lock(self::$request_lock, 'EX');
            return;
        }
        $handle = self::open_operation_lock();
        if (!@flock($handle, LOCK_EX | LOCK_NB)) { self::close_operation_lock($handle); self::fail('REQUEST_LOCK_BUSY'); }
        try {
            self::validate_acquired_lock($handle, 'EX');
            self::retain_request_lock($handle, 'EX');
        } catch (Throwable $error) {
            @flock($handle, LOCK_UN);
            self::close_operation_lock($handle);
            throw $error;
        }
    }
    private static function acquire_request_shared_lock(): void {
        if (is_resource(self::$request_lock)) {
            self::validate_acquired_lock(self::$request_lock, self::$request_lock_mode ?? 'SH');
            return;
        }
        $handle = self::open_operation_lock();
        if (!@flock($handle, LOCK_SH | LOCK_NB)) { self::close_operation_lock($handle); self::fail('REQUEST_LOCK_BUSY'); }
        try {
            self::validate_acquired_lock($handle, 'SH');
            $journal_status = self::read_checked_file(self::journal_file(), 'journal');
            if ($journal_status['status'] === 'missing') {
                self::reconcile_state_and_journal();
            } else {
                @flock($handle, LOCK_UN);
                if (!@flock($handle, LOCK_EX | LOCK_NB)) self::fail('REQUEST_LOCK_BUSY');
                self::validate_acquired_lock($handle, 'EX');
                self::reconcile_state_and_journal();
                if (!@flock($handle, LOCK_SH | LOCK_NB)) self::fail('REQUEST_LOCK_BUSY');
                self::validate_acquired_lock($handle, 'SH');
            }
            self::retain_request_lock($handle, 'SH');
        } catch (Throwable $error) {
            @flock($handle, LOCK_UN);
            self::close_operation_lock($handle);
            throw $error;
        }
    }

    public static function validate_path(string $path): void {
        if ($path === '' || str_contains($path, '\\') || str_starts_with($path, '/') || str_contains($path, "\0")) self::fail('Unsafe archive path.');
        $parts = explode('/', $path);
        foreach ($parts as $part) if ($part === '' || $part === '.' || $part === '..') self::fail('Unsafe archive path.');
    }
    /** Validate an exact file-only inventory after every archive member was hashed. */
    public static function validate_inventory(array $entries, array $expected): bool {
        $seen = array();
        foreach ($entries as $entry) {
            if (!isset($entry['name'], $entry['sha256']) || !is_string($entry['name']) || !is_string($entry['sha256'])) self::fail('Invalid archive inventory.');
            self::validate_path($entry['name']);
            if (!empty($entry['directory']) || !empty($entry['symlink']) || isset($seen[$entry['name']])) self::fail('Archive contains an unsupported member.');
            if (!isset($expected[$entry['name']]) || !hash_equals($expected[$entry['name']], $entry['sha256'])) self::fail('Archive contents do not match the frozen release.');
            $seen[$entry['name']] = true;
        }
        if (count($seen) !== count($expected)) self::fail('Archive inventory is incomplete.');
        return true;
    }
    public static function validate_upload_name_hash(string $name, string $hash, array $phase): void {
        if ($name !== $phase['filename'] || !hash_equals($phase['archive_sha256'], $hash)) self::fail('Uploaded archive filename or SHA-256 does not match the frozen release.');
    }
    public static function may_apply(string $phase, array $state): bool {
        if (empty($state['backup']['verified']) || !in_array($phase, self::ORDER, true)) return false;
        if ($phase === 'A2' && empty($state['stage_verified'])) return false;
        if ($phase === 'B' && self::runtime_option('land76_service_hubs_active_release_id', '') !== self::HUB_RELEASE_ID) return false;
        $position = array_search($phase, self::ORDER, true);
        return $position === 0 || (($state['phases'][self::ORDER[$position - 1]]['status'] ?? '') === 'applied');
    }
    public static function rollback_manifest(array $paths, string $release_id): array {
        return array('schema' => 1, 'release_id' => $release_id, 'created_utc' => gmdate('c'), 'expected_paths' => array_keys($paths), 'paths' => $paths);
    }
    private static function nonce_action(string $operation, string $phase = ''): string { return self::NONCE . ':' . $operation . ($phase === '' ? '' : ':' . $phase); }
    public static function request_is_authorized(array $request, string $operation = 'backup'): bool {
        return (($request['REQUEST_METHOD'] ?? '') === 'POST') && current_user_can('manage_options') && wp_verify_nonce((string)($request['nonce'] ?? ''), self::nonce_action($operation));
    }
    private static function is_exact_authorized_writer_request(): bool {
        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') return false;
        $action = $_POST['action'] ?? null; $nonce = $_POST['_wpnonce'] ?? null;
        if (!is_string($action) || !is_string($nonce)) return false;
        $operation = match ($action) {
            'land76_release_backup' => 'backup',
            'land76_release_stage' => 'stage',
            'land76_release_apply' => (is_string($_POST['phase'] ?? null) && in_array($_POST['phase'], self::ORDER, true)) ? 'apply:' . $_POST['phase'] : '',
            default => '',
        };
        if ($operation === '') return false;
        return self::request_is_authorized(array('REQUEST_METHOD' => 'POST', 'nonce' => $nonce), $operation);
    }
    private static function guard(string $operation, string $phase = ''): void {
        if (!self::request_is_authorized(array('REQUEST_METHOD' => $_SERVER['REQUEST_METHOD'] ?? '', 'nonce' => $_POST['_wpnonce'] ?? ''), $operation . ($phase === '' ? '' : ':' . $phase))) wp_die(esc_html__('Unauthorized request.', 'land76-release-deployer'), 403);
    }
    private static function download_guard(): void {
        if (!current_user_can('manage_options') || !wp_verify_nonce((string)($_REQUEST['_wpnonce'] ?? ''), self::nonce_action('download'))) wp_die(esc_html__('Unauthorized request.', 'land76-release-deployer'), 403);
    }
    private static function docroot(): string {
        $root = self::$integration_config['docroot'] ?? untrailingslashit(ABSPATH);
        return rtrim(str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $root), DIRECTORY_SEPARATOR);
    }
    private static function storage_path(): string {
        if (self::$integration_config !== null) return self::$integration_config['storage_root'];
        return dirname(self::docroot()) . DIRECTORY_SEPARATOR . '.land76-release-deployer-r2';
    }
    private static function assert_storage_outside_docroot(string $root): void {
        $root = rtrim(str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $root), DIRECTORY_SEPARATOR);
        $docroot = rtrim(self::docroot(), DIRECTORY_SEPARATOR);
        $compare_root = DIRECTORY_SEPARATOR === '\\' ? strtolower($root) : $root;
        $compare_docroot = DIRECTORY_SEPARATOR === '\\' ? strtolower($docroot) : $docroot;
        if ($compare_root === $compare_docroot || str_starts_with($compare_root, $compare_docroot . DIRECTORY_SEPARATOR)) self::fail('ROLLBACK_STORAGE_INSIDE_DOCROOT');
    }
    /** Lstat the complete managed storage chain so no site-owned node can redirect through a link. */
    private static function assert_storage_directory_chain(string $root): void {
        $current = self::normalize_directory_path($root);
        $boundary = self::normalize_directory_path(dirname(self::storage_path()));
        if (!self::path_is_within($current, $boundary)) self::fail('ROLLBACK_STORAGE_PATH_UNSAFE');
        while ($current !== '') {
            clearstatcache(true, $current);
            $stat = @lstat($current);
            if (is_array($stat)) {
                if (self::path_is_link_or_reparse($current, $stat) || (($stat['mode'] & 0170000) !== 0040000)) self::fail('ROLLBACK_STORAGE_PATH_UNSAFE');
            } elseif (file_exists($current) || is_link($current)) {
                self::fail('ROLLBACK_STORAGE_LSTAT_FAILED');
            }
            if (self::paths_equal($current, $boundary)) break;
            $parent = dirname($current);
            if ($parent === $current || $parent === '' || $parent === '.' || !self::path_is_within($parent, $boundary)) self::fail('ROLLBACK_STORAGE_PATH_UNSAFE');
            $current = $parent;
        }
    }
    private static function set_directory_mode_exact(string $root, int $mode, string $error): void {
        $pins = self::pin_directory_namespace(dirname($root), $error);
        try {
            self::verify_directory_namespace($pins, $error);
            clearstatcache(true, $root);
            $expected = @lstat($root);
            if (!is_array($expected) || self::path_is_link_or_reparse($root, $expected) || (($expected['mode'] & 0170000) !== 0040000)) self::fail($error);
            if (self::$integration_config !== null) {
                if ((self::$integration_config['mode_adapter'])('set', $root, $mode) !== true || (self::$integration_config['mode_adapter'])('verify', $root, $mode) !== true) self::fail($error);
            } else {
                if (DIRECTORY_SEPARATOR !== '/' || !@chmod($root, $mode)) self::fail($error);
                clearstatcache(true, $root);
                $stat = @lstat($root);
                if (!is_array($stat) || self::path_is_link_or_reparse($root, $stat) || (($stat['mode'] & 0170000) !== 0040000) || (($stat['mode'] & 0777) !== $mode)) self::fail($error);
            }
            self::assert_path_identity_type($root, $expected, 0040000, $error);
            self::verify_directory_namespace($pins, $error);
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    private static function enforce_storage_mode(string $root): void {
        self::set_directory_mode_exact($root, 0700, 'ROLLBACK_STORAGE_MODE_INVALID');
    }
    private static function storage_is_initialized(): bool {
        $root = self::storage_path();
        self::assert_storage_outside_docroot($root);
        self::assert_storage_directory_chain($root);
        clearstatcache(true, $root);
        $stat = @lstat($root);
        if (!is_array($stat)) return false;
        self::enforce_storage_mode($root);
        return true;
    }
    private static function storage_root(bool $create = false): string {
        $root = self::storage_path();
        self::assert_storage_outside_docroot($root);
        self::assert_storage_directory_chain($root);
        clearstatcache(true, $root);
        $stat = @lstat($root);
        if (!is_array($stat) && $create) {
            $parent = dirname($root);
            if (!is_dir($parent) || !is_writable($parent)) self::fail('The parent of ABSPATH is not writable; refusing to store rollback data in the public document root.');
            self::mkdir_in_pinned_namespace($root, 0700, 'Cannot create protected rollback storage.', 'ROLLBACK_STORAGE_NAMESPACE_RACE', 'storage_root_mkdir');
            self::assert_storage_directory_chain($root);
            $stat = @lstat($root);
        }
        if (!is_array($stat)) self::fail('ROLLBACK_STORAGE_NOT_INITIALIZED');
        if (self::path_is_link_or_reparse($root, $stat) || (($stat['mode'] & 0170000) !== 0040000)) self::fail('ROLLBACK_STORAGE_PATH_UNSAFE');
        self::enforce_storage_mode($root);
        return $root;
    }
    private static function ensure_storage_directory(string $path): void {
        $storage = rtrim(self::storage_root(false), DIRECTORY_SEPARATOR);
        $path = rtrim(str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $path), DIRECTORY_SEPARATOR);
        $compare_path = DIRECTORY_SEPARATOR === '\\' ? strtolower($path) : $path;
        $compare_storage = DIRECTORY_SEPARATOR === '\\' ? strtolower($storage) : $storage;
        if (!str_starts_with($compare_path, $compare_storage . DIRECTORY_SEPARATOR)) self::fail('STORAGE_DIRECTORY_OUTSIDE_ROOT');
        $relative = substr($path, strlen($storage) + 1);
        if ($relative === '' || str_contains($relative, '..' . DIRECTORY_SEPARATOR)) self::fail('STORAGE_DIRECTORY_PATH_INVALID');
        $current = $storage;
        foreach (explode(DIRECTORY_SEPARATOR, $relative) as $segment) {
            if ($segment === '' || $segment === '.' || $segment === '..') self::fail('STORAGE_DIRECTORY_PATH_INVALID');
            $current .= DIRECTORY_SEPARATOR . $segment;
            clearstatcache(true, $current);
            $stat = @lstat($current);
            if (is_array($stat)) {
                if (self::path_is_link_or_reparse($current, $stat) || (($stat['mode'] & 0170000) !== 0040000)) self::fail('STORAGE_DIRECTORY_UNSAFE');
                continue;
            }
            if (file_exists($current) || is_link($current)) self::fail('STORAGE_DIRECTORY_LSTAT_FAILED');
            self::mkdir_in_pinned_namespace($current, 0700, 'STORAGE_DIRECTORY_CREATE_FAILED', 'STORAGE_DIRECTORY_NAMESPACE_RACE', 'storage_directory_mkdir');
        }
        self::set_directory_mode_exact($path, 0700, 'STORAGE_DIRECTORY_MODE_FAILED');
    }
    private static function assert_safe_storage_regular_file(string $path): array {
        $storage = rtrim(self::storage_root(false), DIRECTORY_SEPARATOR);
        $path = str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $path);
        $compare_path = DIRECTORY_SEPARATOR === '\\' ? strtolower($path) : $path;
        $compare_prefix = DIRECTORY_SEPARATOR === '\\' ? strtolower($storage . DIRECTORY_SEPARATOR) : $storage . DIRECTORY_SEPARATOR;
        if (!str_starts_with($compare_path, $compare_prefix)) self::fail('STORAGE_FILE_OUTSIDE_ROOT');
        self::assert_storage_directory_chain(dirname($path));
        clearstatcache(true, $path);
        $stat = @lstat($path);
        if (!is_array($stat) || self::path_is_link_or_reparse($path, $stat) || (($stat['mode'] & 0170000) !== 0100000)) self::fail('STORAGE_FILE_UNSAFE');
        return $stat;
    }
    private static function assert_storage_artifact_identity(string $path, array $expected): array {
        $actual = self::assert_safe_storage_regular_file($path);
        if (($actual['dev'] ?? null) !== ($expected['dev'] ?? null) || ($actual['ino'] ?? null) !== ($expected['ino'] ?? null) || (int)$actual['size'] !== (int)$expected['size']) self::fail('ROLLBACK_ARTIFACT_CHANGED');
        return $actual;
    }
    private static function release_stage_path(string $phase, string $archive_hash): string {
        if (!in_array($phase, self::runtime_phase_ids(), true) || preg_match('/\A[a-f0-9]{64}\z/', $archive_hash) !== 1) self::fail('STAGE_IDENTITY_INVALID');
        return self::storage_root(false) . DIRECTORY_SEPARATOR . 'stage-' . strtolower($phase) . '-' . $archive_hash;
    }
    private static function prepare_stage_workspace(string $phase, string $archive_hash): string {
        $stage = self::release_stage_path($phase, $archive_hash);
        self::remove_tree($stage);
        return $stage;
    }
    private static function cleanup_known_stage_workspaces(): void {
        if (self::$integration_config !== null) return;
        foreach (self::expected() as $phase => $expectation) {
            $hash = $expectation['archive_sha256'] ?? null;
            if (is_string($hash) && preg_match('/\A[a-f0-9]{64}\z/', $hash) === 1) self::remove_tree(self::release_stage_path((string)$phase, $hash));
        }
    }
    private static function abs_path(string $relative): string {
        self::validate_path($relative); return self::docroot() . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $relative);
    }
    private static function path_is_link_or_reparse(string $path, array $stat): bool {
        return (($stat['mode'] & 0170000) === 0120000) || is_link($path);
    }
    /** Lstat every existing docroot node and require directory ancestors plus a regular-or-missing leaf. */
    private static function assert_safe_release_path(string $relative, string $leaf_kind = 'regular_or_missing'): ?array {
        self::validate_path($relative);
        if (!in_array($leaf_kind, array('regular_or_missing', 'directory_or_missing'), true)) self::fail('RELEASE_PATH_EXPECTATION_INVALID');
        $current = self::docroot();
        clearstatcache(true, $current);
        $root_stat = @lstat($current);
        if (!is_array($root_stat)) self::fail('RELEASE_DOCROOT_LSTAT_FAILED');
        if (self::path_is_link_or_reparse($current, $root_stat)) self::fail('RELEASE_PATH_LINK_REFUSED');
        if (($root_stat['mode'] & 0170000) !== 0040000) self::fail('RELEASE_DOCROOT_NOT_DIRECTORY');
        $segments = explode('/', $relative);
        $missing = false;
        $leaf_stat = null;
        foreach ($segments as $index => $segment) {
            $current .= DIRECTORY_SEPARATOR . $segment;
            if ($missing) continue;
            clearstatcache(true, $current);
            $stat = @lstat($current);
            if (!is_array($stat)) {
                if (file_exists($current) || is_link($current)) self::fail('RELEASE_PATH_LSTAT_FAILED');
                $missing = true;
                continue;
            }
            if (self::path_is_link_or_reparse($current, $stat)) self::fail('RELEASE_PATH_LINK_REFUSED');
            $leaf = $index === count($segments) - 1;
            $type = $stat['mode'] & 0170000;
            if (!$leaf && $type !== 0040000) self::fail('RELEASE_PATH_ANCESTOR_NOT_DIRECTORY');
            if ($leaf && $leaf_kind === 'regular_or_missing' && $type !== 0100000) self::fail('RELEASE_PATH_LEAF_NOT_REGULAR');
            if ($leaf && $leaf_kind === 'directory_or_missing' && $type !== 0040000) self::fail('RELEASE_PATH_LEAF_NOT_DIRECTORY');
            if ($leaf) $leaf_stat = $stat;
        }
        return $leaf_stat;
    }
    private static function read_regular_file_in_pinned_namespace(string $path, string $error): string {
        $pins = self::pin_directory_namespace(dirname($path), $error);
        $handle = null;
        try {
            self::verify_directory_namespace($pins, $error);
            clearstatcache(true, $path);
            $expected = @lstat($path);
            if (!is_array($expected) || self::path_is_link_or_reparse($path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) self::fail($error);
            self::namespace_failpoint('regular_file_open', $path);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($path, $expected, 0100000, $error);
            $handle = @fopen($path, 'rb');
            if (!is_resource($handle)) self::fail($error);
            $opened = self::assert_path_handle_identity($path, $handle, $error);
            if (($opened['dev'] ?? null) !== ($expected['dev'] ?? null) || ($opened['ino'] ?? null) !== ($expected['ino'] ?? null)) self::fail($error);
            self::verify_directory_namespace($pins, $error);
            $bytes = stream_get_contents($handle);
            if (!is_string($bytes)) self::fail($error);
            self::assert_path_handle_identity($path, $handle, $error);
            self::verify_directory_namespace($pins, $error);
            return $bytes;
        } finally {
            if (is_resource($handle)) fclose($handle);
            self::close_directory_namespace($pins);
        }
    }
    private static function sha_file(string $path): string {
        $pins = self::pin_directory_namespace(dirname($path), 'HASH_NAMESPACE_RACE');
        $handle = null;
        try {
            self::verify_directory_namespace($pins, 'HASH_NAMESPACE_RACE');
            clearstatcache(true, $path);
            $expected = @lstat($path);
            if (!is_array($expected) || self::path_is_link_or_reparse($path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) self::fail('Expected regular file is unavailable.');
            self::namespace_failpoint('hash_file_open', $path);
            self::verify_directory_namespace($pins, 'HASH_NAMESPACE_RACE');
            self::assert_path_identity_type($path, $expected, 0100000, 'HASH_FILE_RACE');
            $handle = @fopen($path, 'rb');
            if (!is_resource($handle)) self::fail('Cannot hash file.');
            $opened = self::assert_path_handle_identity($path, $handle, 'HASH_FILE_RACE');
            if (($opened['dev'] ?? null) !== ($expected['dev'] ?? null) || ($opened['ino'] ?? null) !== ($expected['ino'] ?? null)) self::fail('HASH_FILE_RACE');
            self::verify_directory_namespace($pins, 'HASH_NAMESPACE_RACE');
            $context = hash_init('sha256');
            $hashed = hash_update_stream($context, $handle);
            if (!is_int($hashed) || $hashed < 0) self::fail('Cannot hash file.');
            self::assert_path_handle_identity($path, $handle, 'HASH_FILE_RACE');
            self::verify_directory_namespace($pins, 'HASH_NAMESPACE_RACE');
            return hash_final($context);
        } finally {
            if (is_resource($handle)) fclose($handle);
            self::close_directory_namespace($pins);
        }
    }
    private static function require_exact_php_file(string $path, string $hash, string $error): void {
        $pins = self::pin_directory_namespace(dirname($path), $error);
        try {
            self::verify_directory_namespace($pins, $error);
            clearstatcache(true, $path);
            $expected = @lstat($path);
            if (!is_array($expected) || self::path_is_link_or_reparse($path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) self::fail($error);
            if (!hash_equals($hash, self::sha_file($path))) self::fail($error);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($path, $expected, 0100000, $error);
            self::namespace_failpoint('php_require', $path);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($path, $expected, 0100000, $error);
            require_once $path;
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($path, $expected, 0100000, $error);
        } finally {
            self::close_directory_namespace($pins);
        }
    }
    private static function require_ziparchive(): void { if (!class_exists('ZipArchive')) self::fail('ZipArchive is unavailable. This deployer fails closed; install/enable PHP Zip before use.'); }

    private static function zip_entries(string $zip_path): array {
        self::require_ziparchive();
        $pins = self::pin_directory_namespace(dirname($zip_path), 'ZIP_NAMESPACE_RACE');
        clearstatcache(true, $zip_path);
        $expected = @lstat($zip_path);
        if (!is_array($expected) || self::path_is_link_or_reparse($zip_path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) {
            self::close_directory_namespace($pins);
            self::fail('Cannot open ZIP archive.');
        }
        $zip = new ZipArchive(); $opened = false;
        $entries = array();
        try {
            self::verify_directory_namespace($pins, 'ZIP_NAMESPACE_RACE');
            self::namespace_failpoint('zip_open', $zip_path);
            self::verify_directory_namespace($pins, 'ZIP_NAMESPACE_RACE');
            self::assert_path_identity_type($zip_path, $expected, 0100000, 'ZIP_FILE_RACE');
            if ($zip->open($zip_path) !== true) self::fail('Cannot open ZIP archive.');
            $opened = true;
            self::verify_directory_namespace($pins, 'ZIP_NAMESPACE_RACE');
            self::assert_path_identity_type($zip_path, $expected, 0100000, 'ZIP_FILE_RACE');
            for ($index = 0; $index < $zip->numFiles; $index++) {
                $stat = $zip->statIndex($index); if (!is_array($stat) || !isset($stat['name'])) self::fail('Cannot inspect ZIP entry.');
                $name = (string)$stat['name']; $directory = str_ends_with($name, '/'); $symlink = false;
                if (method_exists($zip, 'getExternalAttributesIndex')) { $opsys = 0; $attributes = 0; if (!$zip->getExternalAttributesIndex($index, $opsys, $attributes)) self::fail('Cannot inspect ZIP entry attributes.'); $symlink = (($attributes >> 16) & 0170000) === 0120000; }
                else { self::fail('ZIP entry attributes cannot be inspected safely.'); }
                $stream = $zip->getStream($name); if (!is_resource($stream)) self::fail('Cannot read ZIP entry.');
                $ctx = hash_init('sha256'); while (!feof($stream)) { $buffer = fread($stream, 1048576); if ($buffer === false) { fclose($stream); self::fail('Cannot hash ZIP entry.'); } hash_update($ctx, $buffer); } fclose($stream);
                $entries[] = array('name' => $name, 'sha256' => hash_final($ctx), 'size' => (int)($stat['size'] ?? 0), 'directory' => $directory, 'symlink' => $symlink);
            }
            self::verify_directory_namespace($pins, 'ZIP_NAMESPACE_RACE');
            self::assert_path_identity_type($zip_path, $expected, 0100000, 'ZIP_FILE_RACE');
            return $entries;
        } finally {
            if ($opened) $zip->close();
            try {
                self::verify_directory_namespace($pins, 'ZIP_NAMESPACE_RACE');
                self::assert_path_identity_type($zip_path, $expected, 0100000, 'ZIP_FILE_RACE');
            } finally {
                self::close_directory_namespace($pins);
            }
        }
    }
    private static function read_zip_member_in_pinned_namespace(string $zip_path, string $member, string $error): string {
        $pins = self::pin_directory_namespace(dirname($zip_path), $error);
        clearstatcache(true, $zip_path);
        $expected = @lstat($zip_path);
        if (!is_array($expected) || self::path_is_link_or_reparse($zip_path, $expected) || (($expected['mode'] & 0170000) !== 0100000)) {
            self::close_directory_namespace($pins);
            self::fail($error);
        }
        $zip = new ZipArchive(); $opened = false;
        try {
            self::verify_directory_namespace($pins, $error);
            self::namespace_failpoint('zip_open', $zip_path);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($zip_path, $expected, 0100000, $error);
            if ($zip->open($zip_path) !== true) self::fail($error);
            $opened = true;
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($zip_path, $expected, 0100000, $error);
            $bytes = $zip->getFromName($member);
            if (!is_string($bytes)) self::fail($error);
            self::verify_directory_namespace($pins, $error);
            self::assert_path_identity_type($zip_path, $expected, 0100000, $error);
            return $bytes;
        } finally {
            if ($opened) $zip->close();
            try {
                self::verify_directory_namespace($pins, $error);
                self::assert_path_identity_type($zip_path, $expected, 0100000, $error);
            } finally {
                self::close_directory_namespace($pins);
            }
        }
    }
    private static function extract_to_stage(string $zip_path, string $stage, array $expected): void {
        self::validate_inventory(self::zip_entries($zip_path), $expected);
        self::ensure_storage_directory($stage);
        foreach (array_keys($expected) as $path) {
            $content = self::read_zip_member_in_pinned_namespace($zip_path, $path, 'Cannot extract a frozen ZIP entry.');
            $target = $stage . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $path); $dir = dirname($target);
            self::ensure_storage_directory($dir);
            self::durable_write($target, $content, 0600);
            if (!hash_equals($expected[$path], self::sha_file($target))) self::fail('Staged file verification failed.');
        }
    }
    private static function remove_tree(string $path, ?string $validated_storage = null): void {
        $storage = $validated_storage ?? rtrim(self::storage_root(false), DIRECTORY_SEPARATOR);
        $path = rtrim(str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $path), DIRECTORY_SEPARATOR);
        $prefix = $storage . DIRECTORY_SEPARATOR;
        $compare_path = DIRECTORY_SEPARATOR === '\\' ? strtolower($path) : $path;
        $compare_prefix = DIRECTORY_SEPARATOR === '\\' ? strtolower($prefix) : $prefix;
        if (!str_starts_with($compare_path, $compare_prefix)) self::fail('REMOVE_TREE_OUTSIDE_STORAGE');
        clearstatcache(true, $path);
        $stat = @lstat($path);
        if (!is_array($stat)) {
            if (file_exists($path) || is_link($path)) self::fail('REMOVE_TREE_LSTAT_FAILED');
            return;
        }
        $type = $stat['mode'] & 0170000;
        if ($type === 0120000 || is_link($path)) self::fail('REMOVE_TREE_LINK_REFUSED');
        if ($type !== 0040000) self::fail('REMOVE_TREE_ROOT_NOT_DIRECTORY');
        $pins = self::pin_directory_namespace($path, 'REMOVE_TREE_NAMESPACE_RACE');
        try {
            self::verify_directory_namespace($pins, 'REMOVE_TREE_NAMESPACE_RACE');
            $items = scandir($path);
            if (!is_array($items)) self::fail('REMOVE_TREE_SCAN_FAILED');
            self::verify_directory_namespace($pins, 'REMOVE_TREE_NAMESPACE_RACE');
            foreach ($items as $item) {
                if ($item === '.' || $item === '..') continue;
                $target = $path . DIRECTORY_SEPARATOR . $item;
                $target_stat = @lstat($target);
                if (!is_array($target_stat)) self::fail('REMOVE_TREE_LSTAT_FAILED');
                $target_type = $target_stat['mode'] & 0170000;
                if ($target_type === 0040000) self::remove_tree($target, $storage);
                elseif ($target_type === 0100000 && !is_link($target)) self::unlink_regular_in_pinned_namespace($target, 'REMOVE_TREE_UNLINK_FAILED', 'REMOVE_TREE_NAMESPACE_RACE', 'remove_tree_unlink');
                else self::fail('REMOVE_TREE_SPECIAL_REFUSED');
                self::verify_directory_namespace($pins, 'REMOVE_TREE_NAMESPACE_RACE');
            }
        } finally {
            self::close_directory_namespace($pins);
        }
        self::rmdir_empty_in_pinned_namespace($path, 'REMOVE_TREE_RMDIR_FAILED', 'REMOVE_TREE_NAMESPACE_RACE', 'remove_tree_rmdir');
    }
    private static function with_stage_cleanup(string $stage, callable $operation): mixed {
        try { return $operation(); }
        finally { self::remove_tree($stage); }
    }
    /** Run a command without shell interpolation and enforce a wall-clock deadline. */
    private static function run_process(array $command, float $timeout_seconds): array {
        if (!function_exists('proc_open')) return array('status' => 'unavailable', 'exit_code' => null);
        $pipes = array();
        try { $process = @proc_open($command, array(1 => array('pipe', 'w'), 2 => array('pipe', 'w')), $pipes); }
        catch (Throwable $error) { return array('status' => 'unavailable', 'exit_code' => null); }
        if (!is_resource($process)) return array('status' => 'unavailable', 'exit_code' => null);
        foreach ($pipes as $pipe) if (is_resource($pipe)) stream_set_blocking($pipe, false);
        $deadline = microtime(true) + max(0.001, $timeout_seconds);
        $exit_code = null;
        $timed_out = false;
        while (true) {
            $status = proc_get_status($process);
            if (!is_array($status) || empty($status['running'])) { $exit_code = is_array($status) ? (int)($status['exitcode'] ?? -1) : -1; break; }
            if (microtime(true) >= $deadline) { $timed_out = true; @proc_terminate($process); break; }
            usleep(10_000);
        }
        foreach ($pipes as $pipe) if (is_resource($pipe)) fclose($pipe);
        $closed_exit = @proc_close($process);
        if ($timed_out) return array('status' => 'timeout', 'exit_code' => null);
        if ($exit_code === null || $exit_code < 0) $exit_code = (int)$closed_exit;
        return array('status' => 'ran', 'exit_code' => $exit_code);
    }
    public static function lint_php(array $files, ?callable $runner = null): string {
        $process_runner = $runner ?? array(__CLASS__, 'run_process');
        $frozen_paths = self::all_paths();
        foreach ($files as $relative => $file) {
            if (!is_string($relative)) self::fail('PHP_LINT_PATH_INVALID');
            self::validate_path($relative);
            if (!str_ends_with(strtolower($relative), '.php')) continue;
            if (!isset($frozen_paths[$relative])) self::fail('PHP_LINT_PATH_INVALID');
            $result = (!defined('PHP_BINARY') || PHP_BINARY === '')
                ? array('status' => 'unavailable', 'exit_code' => null)
                : $process_runner(array(PHP_BINARY, '-l', $file), 10);
            if (($result['status'] ?? '') === 'ran' && (int)($result['exit_code'] ?? -1) === 0) continue;
            if (($result['status'] ?? '') === 'timeout') self::fail('PHP_LINT_TIMEOUT:' . $relative);
            if (($result['status'] ?? '') === 'ran') self::fail('PHP_LINT_FAILED:' . $relative);
            self::fail('PHP_LINT_UNAVAILABLE:' . $relative);
        }
        return 'ran';
    }
    private static function with_php_lint_gate(array $files, callable $after_lint, ?callable $runner = null): string {
        $lint = self::lint_php($files, $runner);
        $after_lint($lint);
        return $lint;
    }
    private static function verify_drift(array $manifest, array $phase_files): void {
        foreach ($phase_files as $path => $_) {
            $before = $manifest['paths'][$path] ?? null;
            if (!is_array($before)) self::fail('Rollback manifest lacks a release path.');
            $live = self::abs_path($path);
            $stat = self::assert_safe_release_path($path);
            if (!$before['exists']) {
                if ($stat !== null) self::fail('Destination drift detected before apply.');
            } elseif ($stat === null || !hash_equals((string)$before['sha256'], self::sha_file($live))) {
                self::fail('Destination drift detected before apply.');
            }
        }
    }
    private static function verify_apply_drift(array $manifest, string $current_phase): void {
        $completed = array();
        foreach (self::ORDER as $phase) { if ($phase === $current_phase) break; foreach (self::expected()[$phase]['files'] as $path => $hash) $completed[$path] = $hash; }
        foreach (self::all_paths() as $path => $hash) {
            $live = self::abs_path($path);
            if (isset($completed[$path])) { if (self::assert_safe_release_path($path) === null || !hash_equals($completed[$path], self::sha_file($live))) self::fail('Completed release phase has drifted.'); continue; }
            self::verify_drift($manifest, array($path => $hash));
        }
    }
    private static function destination_temp_path(string $txid, string $relative, string $purpose): string {
        if (preg_match('/\A[a-zA-Z0-9._-]{1,128}\z/', $txid) !== 1 || !in_array($purpose, array('apply', 'restore'), true)) self::fail('DESTINATION_TEMP_IDENTITY_INVALID');
        self::validate_path($relative);
        $name = '.land76-' . $purpose . '-' . hash('sha256', $txid . "\0" . $relative . "\0" . $purpose) . '.tmp';
        return dirname(self::abs_path($relative)) . DIRECTORY_SEPARATOR . $name;
    }
    /** Remove only an exact transaction-derived regular temp; links and special files fail closed. */
    private static function cleanup_release_owned_temp(string $path): void {
        self::unlink_regular_in_pinned_namespace($path, 'DESTINATION_TEMP_UNSAFE', 'DESTINATION_TEMP_NAMESPACE_RACE', 'destination_temp_unlink');
    }
    private static function cleanup_journal_temps(array $journal): void {
        foreach ($journal['attempted_paths'] as $relative) {
            self::assert_safe_release_path($relative);
            foreach (array('apply', 'restore') as $purpose) self::cleanup_release_owned_temp(self::destination_temp_path($journal['txid'], $relative, $purpose));
        }
    }
    private static function write_all($handle, string $bytes): void {
        $offset = 0; $length = strlen($bytes);
        while ($offset < $length) {
            $written = fwrite($handle, substr($bytes, $offset));
            if (!is_int($written) || $written < 1) self::fail('TEMP_WRITE_FAILED');
            $offset += $written;
        }
    }
    private static function atomic_write(string $source, bool $source_is_bytes, string $destination, string $hash, ?int $mode, string $txid, string $purpose, ?string $failpoint = null, ?callable $last_gate = null): void {
        $destination = str_replace(array('/', '\\'), DIRECTORY_SEPARATOR, $destination); $prefix = self::docroot() . DIRECTORY_SEPARATOR;
        if (!str_starts_with($destination, $prefix)) self::fail('DESTINATION_OUTSIDE_DOCROOT');
        $relative = str_replace(DIRECTORY_SEPARATOR, '/', substr($destination, strlen($prefix))); self::assert_safe_release_path($relative);
        $dir = dirname($destination); if (!is_dir($dir) || is_link($dir)) self::fail('DESTINATION_DIRECTORY_UNAVAILABLE');
        $temp = self::destination_temp_path($txid, $relative, $purpose);
        $destination_pins = self::pin_directory_namespace($dir, 'DESTINATION_NAMESPACE_RACE');
        $source_pins = $source_is_bytes ? array() : self::pin_directory_namespace(dirname($source), 'STAGED_NAMESPACE_RACE');
        $in = null; $out = null;
        $preserve_temp = false;
        $temp_identity = null;
        try {
            self::verify_directory_namespace($destination_pins, 'DESTINATION_NAMESPACE_RACE');
            if (!$source_is_bytes) {
                self::verify_directory_namespace($source_pins, 'STAGED_NAMESPACE_RACE');
                $source_expected = self::assert_safe_storage_regular_file($source);
                $in = @fopen($source, 'rb');
                if (is_resource($in)) {
                    $source_opened = self::assert_path_handle_identity($source, $in, 'STAGED_FILE_RACE');
                    if (($source_opened['dev'] ?? null) !== ($source_expected['dev'] ?? null) || ($source_opened['ino'] ?? null) !== ($source_expected['ino'] ?? null)) self::fail('STAGED_FILE_RACE');
                }
            }
            $out = @fopen($temp, 'x+b');
            if ((!$source_is_bytes && !is_resource($in)) || !is_resource($out)) self::fail('TEMP_O_EXCL_CREATE_FAILED');
            $temp_identity = fstat($out);
            if (!is_array($temp_identity) || (($temp_identity['mode'] & 0170000) !== 0100000)) self::fail('DESTINATION_TEMP_UNSAFE');
            self::assert_path_handle_identity($temp, $out, 'DESTINATION_TEMP_RACE');
            if ($source_is_bytes) self::write_all($out, $source);
            elseif (stream_copy_to_stream($in, $out) === false) self::fail('TEMP_WRITE_FAILED');
            if (is_resource($in)) {
                self::assert_path_handle_identity($source, $in, 'STAGED_FILE_RACE');
                self::verify_directory_namespace($source_pins, 'STAGED_NAMESPACE_RACE');
            }
            if (!fflush($out)) self::fail('TEMP_WRITE_FAILED');
            self::assert_path_handle_identity($temp, $out, 'DESTINATION_TEMP_RACE');
            self::set_mode_exact($temp, $mode ?? 0644, 'TEMP_MODE_FAILED');
            self::assert_path_handle_identity($temp, $out, 'DESTINATION_TEMP_RACE');
            self::sync_file_handle($out, 'TEMP_WRITE_FAILED');
            self::assert_path_handle_identity($temp, $out, 'DESTINATION_TEMP_RACE');
            if (is_resource($in)) { fclose($in); $in = null; }
            fclose($out); $out = null;
            self::assert_regular_path_identity($temp, $temp_identity, 'DESTINATION_TEMP_RACE');
            if (!hash_equals($hash, self::sha_file($temp))) self::fail('TEMP_HASH_FAILED');
            if (self::$integration_config !== null && isset(self::$integration_config['before_destination_rename'])) (self::$integration_config['before_destination_rename'])($temp, $destination);
            self::assert_regular_path_identity($temp, $temp_identity, 'DESTINATION_TEMP_RACE');
            if ($purpose === 'apply' && $failpoint === 'crash_before_rename') {
                $preserve_temp = true;
                self::fail('INJECTED_PROCESS_CRASH_BEFORE_RENAME');
            }
            self::assert_safe_release_path($relative);
            self::namespace_failpoint('destination_rename', $destination);
            self::verify_directory_namespace($destination_pins, 'DESTINATION_NAMESPACE_RACE');
            if ($last_gate !== null) $last_gate();
            if (!@rename($temp, $destination)) self::fail('DESTINATION_RENAME_FAILED');
            self::verify_directory_namespace($destination_pins, 'DESTINATION_NAMESPACE_RACE');
            self::sync_directory($dir);
            self::assert_regular_path_identity($destination, $temp_identity, 'DESTINATION_TEMP_RACE');
            if (self::assert_safe_release_path($relative) === null || !hash_equals($hash, self::sha_file($destination))) self::fail('DESTINATION_HASH_FAILED');
            self::verify_mode_exact($destination, $mode ?? 0644, 'DESTINATION_MODE_FAILED');
        } finally {
            if (is_resource($in)) fclose($in);
            if (is_resource($out)) fclose($out);
            try {
                self::verify_directory_namespace($destination_pins, 'DESTINATION_NAMESPACE_RACE');
                if (!$preserve_temp) self::cleanup_release_owned_temp($temp);
            } finally {
                self::close_directory_namespace($source_pins);
                self::close_directory_namespace($destination_pins);
            }
        }
    }
    private static function assert_regular_path_identity(string $path, array $expected, string $error): array {
        clearstatcache(true, $path);
        $actual = @lstat($path);
        if (!is_array($actual) || self::path_is_link_or_reparse($path, $actual) || (($actual['mode'] & 0170000) !== 0100000)) self::fail('DESTINATION_TEMP_UNSAFE');
        if (($actual['dev'] ?? null) !== ($expected['dev'] ?? null) || ($actual['ino'] ?? null) !== ($expected['ino'] ?? null)) self::fail($error);
        return $actual;
    }
    private static function validate_journal_document(array $journal): array {
        foreach (array('release_id', 'txid', 'phase', 'backup_sha256', 'step') as $key) if (!isset($journal[$key]) || !is_string($journal[$key]) || $journal[$key] === '') self::fail('JOURNAL_SHAPE_INVALID');
        if (($journal['schema'] ?? null) !== 1 || !is_array($journal['base_state'] ?? null) || !is_array($journal['target_state'] ?? null)) self::fail('JOURNAL_SCHEMA_INVALID');
        if (!is_array($journal['attempted_paths'] ?? null) || !array_is_list($journal['attempted_paths']) || !is_array($journal['created_dirs'] ?? null) || !array_is_list($journal['created_dirs'])) self::fail('JOURNAL_PATHS_INVALID');
        if (!in_array($journal['step'], array('applying', 'commit_ready'), true) || preg_match('/\A[a-zA-Z0-9._-]{1,128}\z/', $journal['txid']) !== 1) self::fail('JOURNAL_STEP_INVALID');
        if (preg_match('/\A[a-f0-9]{64}\z/', $journal['backup_sha256']) !== 1) self::fail('JOURNAL_BACKUP_INVALID');
        $journal['base_state'] = self::validate_checksummed_document($journal['base_state'], 'state');
        $journal['target_state'] = self::validate_checksummed_document($journal['target_state'], 'state');
        $base = $journal['base_state']; $target = $journal['target_state'];
        if (!hash_equals((string)$base['release_id'], $journal['release_id']) || !hash_equals($journal['release_id'], (string)$target['release_id'])) self::fail('JOURNAL_RELEASE_INVALID');
        if ((int)$target['generation'] !== (int)$base['generation'] + 1 || !hash_equals($journal['txid'], (string)$target['last_committed_txid'])) self::fail('JOURNAL_TARGET_INVALID');
        if (empty($base['backup']['verified']) || !hash_equals((string)$base['backup']['zip_sha256'], $journal['backup_sha256'])) self::fail('JOURNAL_BACKUP_INVALID');
        if (self::encode_json($base['backup'], true) !== self::encode_json($target['backup'], true)) self::fail('JOURNAL_TARGET_BACKUP_CHANGED');
        if (!isset($base['phases'][$journal['phase']]) || !isset($target['phases'][$journal['phase']]) || ($target['phases'][$journal['phase']]['status'] ?? '') !== 'applied') self::fail('JOURNAL_PHASE_INVALID');
        foreach ($base['phases'] as $phase => $phase_state) if ($phase !== $journal['phase'] && self::encode_json($phase_state, true) !== self::encode_json($target['phases'][$phase] ?? array(), true)) self::fail('JOURNAL_TARGET_PHASE_DRIFT');
        $expected = self::runtime_phase_files($journal['phase']); if ($expected === array()) self::fail('JOURNAL_PHASE_INVALID');
        foreach (array('attempted_paths', 'created_dirs') as $key) {
            $seen = array();
            foreach ($journal[$key] as $path) {
                if (!is_string($path) || isset($seen[$path])) self::fail('JOURNAL_PATHS_INVALID');
                self::validate_path($path); $seen[$path] = true;
                if ($key === 'attempted_paths' && !array_key_exists($path, $expected)) self::fail('JOURNAL_PATHS_INVALID');
                if ($key === 'created_dirs') {
                    $trusted = false;
                    foreach ($journal['attempted_paths'] as $attempted_path) {
                        if (str_starts_with($attempted_path, $path . '/')) { $trusted = true; break; }
                    }
                    if (!$trusted) self::fail('JOURNAL_PATHS_INVALID');
                }
            }
        }
        return self::normalize_journal($journal);
    }
    private static function backup_artifact_paths(array $state): array {
        self::validate_backup_metadata($state['backup']);
        return array(
            'zip' => self::storage_root(false) . DIRECTORY_SEPARATOR . $state['backup']['zip_basename'],
            'manifest' => self::storage_root(false) . DIRECTORY_SEPARATOR . $state['backup']['manifest_basename'],
        );
    }
    /** Reverify the exact external manifest, ZIP bytes, and every rollback member before live mutation. */
    private static function exact_reverify_backup(array $state, ?string $journal_backup_sha256 = null): array {
        $storage_pins = self::pin_directory_namespace(self::storage_root(false), 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        try {
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        if (empty($state['backup']['verified'])) self::fail('ROLLBACK_ARTIFACT_UNVERIFIED');
        $paths = self::backup_artifact_paths($state); $backup = $state['backup'];
        $artifact_stats = array();
        foreach ($paths as $key => $path) {
            try { $artifact_stats[$key] = self::assert_safe_storage_regular_file($path); }
            catch (Throwable $error) { self::fail('ROLLBACK_ARTIFACT_UNAVAILABLE'); }
        }
        if ((int)$artifact_stats['zip']['size'] !== $backup['zip_bytes'] || (int)$artifact_stats['manifest']['size'] !== $backup['manifest_bytes']) self::fail('ROLLBACK_ARTIFACT_SIZE_MISMATCH');
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        self::assert_storage_artifact_identity($paths['manifest'], $artifact_stats['manifest']);
        $zip_bytes = self::read_regular_file_in_pinned_namespace($paths['zip'], 'ROLLBACK_ARTIFACT_READ_FAILED');
        $manifest_bytes = self::read_regular_file_in_pinned_namespace($paths['manifest'], 'ROLLBACK_ARTIFACT_READ_FAILED');
        $zip_hash = hash('sha256', $zip_bytes); $manifest_hash = hash('sha256', $manifest_bytes);
        if (!hash_equals((string)$backup['zip_sha256'], $zip_hash) || !hash_equals((string)$backup['manifest_sha256'], $manifest_hash)) self::fail('ROLLBACK_ARTIFACT_HASH_MISMATCH');
        if ($journal_backup_sha256 !== null && !hash_equals($journal_backup_sha256, $zip_hash)) self::fail('JOURNAL_BACKUP_HASH_MISMATCH');
        if (self::$integration_config !== null && isset(self::$integration_config['after_backup_hashes'])) (self::$integration_config['after_backup_hashes'])($paths);
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        self::assert_storage_artifact_identity($paths['manifest'], $artifact_stats['manifest']);
        if (self::read_regular_file_in_pinned_namespace($paths['manifest'], 'ROLLBACK_ARTIFACT_CHANGED') !== $manifest_bytes) self::fail('ROLLBACK_ARTIFACT_CHANGED');
        try { $manifest = is_string($manifest_bytes) ? json_decode($manifest_bytes, true, 64, JSON_THROW_ON_ERROR) : null; }
        catch (Throwable $error) { $manifest = null; }
        if (!is_array($manifest) || !is_array($manifest['paths'] ?? null) || !is_string($manifest_bytes)) self::fail('ROLLBACK_MANIFEST_INVALID');
        if (($manifest['schema'] ?? null) !== 1) self::fail('ROLLBACK_MANIFEST_SCHEMA_INVALID');
        if (!is_string($manifest['release_id'] ?? null) || !hash_equals((string)$state['release_id'], $manifest['release_id'])) self::fail('ROLLBACK_MANIFEST_RELEASE_MISMATCH');
        $manifest_keys = array_keys($manifest); sort($manifest_keys, SORT_STRING);
        if ($manifest_keys !== array('created_utc', 'expected_paths', 'paths', 'release_id', 'schema') || !is_string($manifest['created_utc']) || $manifest['created_utc'] === '') self::fail('ROLLBACK_MANIFEST_SHAPE_INVALID');
        $expected_paths = array_keys(self::runtime_all_paths());
        if (!is_array($manifest['expected_paths'] ?? null) || !array_is_list($manifest['expected_paths']) || $manifest['expected_paths'] !== $expected_paths) self::fail('ROLLBACK_MANIFEST_PATH_SET_INVALID');
        $record_paths = array_keys($manifest['paths']); sort($record_paths, SORT_STRING);
        if ($record_paths !== $expected_paths) self::fail('ROLLBACK_MANIFEST_PATH_SET_INVALID');
        $expected_entries = array('rollback-manifest.json' => hash('sha256', $manifest_bytes));
        $expected_sizes = array('rollback-manifest.json' => strlen($manifest_bytes));
        foreach ($manifest['paths'] as $path => $record) {
            if (!is_string($path) || !is_array($record) || !array_key_exists('exists', $record)) self::fail('ROLLBACK_MANIFEST_INVALID');
            if (!is_bool($record['exists'])) self::fail('ROLLBACK_MANIFEST_RECORD_INVALID');
            self::validate_path($path);
            $record_keys = array_keys($record); sort($record_keys, SORT_STRING);
            $required_keys = $record['exists'] ? array('bytes', 'exists', 'mode', 'sha256') : array('exists');
            if ($record_keys !== $required_keys) self::fail('ROLLBACK_MANIFEST_RECORD_INVALID');
            if (!$record['exists']) continue;
            if (!is_string($record['sha256'] ?? null) || preg_match('/\A[a-f0-9]{64}\z/', $record['sha256']) !== 1 || !is_int($record['bytes'] ?? null) || $record['bytes'] < 0 || !is_int($record['mode'] ?? null) || $record['mode'] < 0 || $record['mode'] > 0777) self::fail('ROLLBACK_MANIFEST_RECORD_INVALID');
            $expected_entries['files/' . $path] = $record['sha256'];
            $expected_sizes['files/' . $path] = $record['bytes'];
        }
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        $zip_entries = self::zip_entries($paths['zip']);
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        self::validate_inventory($zip_entries, $expected_entries);
        foreach ($zip_entries as $entry) if (($expected_sizes[$entry['name']] ?? null) !== $entry['size']) self::fail('ROLLBACK_MEMBER_SIZE_MISMATCH');
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        $embedded_manifest = self::read_zip_member_in_pinned_namespace($paths['zip'], 'rollback-manifest.json', 'ROLLBACK_ZIP_REOPEN_FAILED');
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        self::assert_storage_artifact_identity($paths['zip'], $artifact_stats['zip']);
        if (self::read_regular_file_in_pinned_namespace($paths['zip'], 'ROLLBACK_ARTIFACT_CHANGED') !== $zip_bytes) self::fail('ROLLBACK_ARTIFACT_CHANGED');
        self::assert_storage_artifact_identity($paths['manifest'], $artifact_stats['manifest']);
        if (self::read_regular_file_in_pinned_namespace($paths['manifest'], 'ROLLBACK_ARTIFACT_CHANGED') !== $manifest_bytes) self::fail('ROLLBACK_ARTIFACT_CHANGED');
        if (!is_string($embedded_manifest) || $embedded_manifest !== $manifest_bytes) self::fail('ROLLBACK_MANIFEST_COPY_MISMATCH');
        self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        return array('manifest' => $manifest, 'zip' => $paths['zip']);
        } finally {
            self::close_directory_namespace($storage_pins);
        }
    }
    private static function clear_journal(?callable $last_gate = null): void {
        $path = self::journal_file();
        $gate = static function () use ($last_gate): void {
            if (self::$integration_config !== null && isset(self::$integration_config['before_journal_clear'])) (self::$integration_config['before_journal_clear'])();
            if ($last_gate !== null) $last_gate();
        };
        self::unlink_regular_in_pinned_namespace($path, 'JOURNAL_CLEAR_FAILED', 'JOURNAL_NAMESPACE_RACE', 'journal_unlink', $gate);
    }
    private static function live_matches_phase(string $phase): bool {
        $expected = self::runtime_phase_files($phase); if ($expected === array()) return false;
        foreach ($expected as $path => $hash) {
            $live = self::abs_path($path);
            if (self::assert_safe_release_path($path) === null || !hash_equals($hash, self::sha_file($live))) return false;
        }
        return true;
    }
    private static function restore_changed(array $changed, array $manifest, array $backup_state, string $backup_sha256, string $txid, ?string $failpoint = null): void {
        $restored = 0;
        foreach (array_reverse($changed) as $path) {
            $artifacts = self::exact_reverify_backup($backup_state, $backup_sha256);
            $before = $manifest['paths'][$path] ?? null; if (!is_array($before)) self::fail('JOURNAL_RECOVERY_MANIFEST_GAP');
            $destination = self::abs_path($path);
            if (!$before['exists']) {
                $stat = self::assert_safe_release_path($path);
                if ($stat !== null) self::unlink_regular_in_pinned_namespace($destination, 'Cannot remove introduced file during automatic rollback.', 'ROLLBACK_DESTINATION_NAMESPACE_RACE', 'rollback_unlink');
                continue;
            }
            $content = self::read_zip_member_in_pinned_namespace($artifacts['zip'], 'files/' . $path, 'Rollback archive entry is unavailable.');
            if (!hash_equals((string)$before['sha256'], hash('sha256', $content))) self::fail('Rollback archive entry is unavailable.');
            self::atomic_write($content, true, $destination, (string)$before['sha256'], (int)$before['mode'], $txid, 'restore');
            $restored++;
            if ($failpoint === 'crash_mid_rollback' && $restored === 1) self::fail('INJECTED_ROLLBACK_PROCESS_CRASH');
        }
    }
    private static function verify_restored(array $paths, array $manifest): void {
        foreach ($paths as $path) {
            $before = $manifest['paths'][$path] ?? null; $live = self::abs_path($path);
            if (!is_array($before)) self::fail('JOURNAL_RECOVERY_VERIFY_FAILED');
            $stat = self::assert_safe_release_path($path);
            if (($before['exists'] && ($stat === null || (int)$stat['size'] !== (int)$before['bytes'] || !hash_equals((string)$before['sha256'], self::sha_file($live)))) || (!$before['exists'] && $stat !== null)) self::fail('JOURNAL_RECOVERY_VERIFY_FAILED');
            if ($before['exists']) self::verify_mode_exact($live, (int)$before['mode'], 'JOURNAL_RECOVERY_MODE_FAILED');
        }
    }
    private static function reconcile_state_and_journal(?string $failpoint = null): array {
        $state_status = self::read_checked_file(self::state_file(), 'state');
        $journal_status = self::read_checked_file(self::journal_file(), 'journal');
        if ($journal_status['status'] === 'missing') {
            if ($state_status['status'] !== 'valid' || !is_array($state_status['document'])) self::fail('STATE_CORRUPT_OR_MISSING');
            return $state_status['document'];
        }
        if ($journal_status['status'] !== 'valid' || !is_array($journal_status['document'])) self::fail('JOURNAL_CORRUPT');
        $journal = $journal_status['document'];
        $artifacts = self::exact_reverify_backup($journal['base_state'], $journal['backup_sha256']);
        self::cleanup_journal_temps($journal);
        $commit_won = (
            $state_status['status'] === 'valid' && is_array($state_status['document']) &&
            $journal['step'] === 'commit_ready' &&
            hash_equals($journal['txid'], (string)$state_status['document']['last_committed_txid']) &&
            hash_equals((string)$journal['target_state']['checksum'], (string)$state_status['document']['checksum']) &&
            self::live_matches_phase($journal['phase'])
        );
        if ($commit_won) {
            try { self::assert_phase_invariant($journal['phase']); }
            catch (Throwable $invariant_error) { $commit_won = false; }
        }
        if ($commit_won) {
            self::clear_journal(static function () use ($journal): void { self::assert_phase_invariant($journal['phase']); });
            return $state_status['document'];
        }
        self::restore_changed($journal['attempted_paths'], $artifacts['manifest'], $journal['base_state'], $journal['backup_sha256'], $journal['txid'], $failpoint);
        foreach (array_reverse($journal['created_dirs']) as $relative) {
            $directory = self::abs_path($relative);
            $directory_stat = self::assert_safe_release_path($relative, 'directory_or_missing');
            if ($directory_stat !== null) {
                $directory_pins = self::pin_directory_namespace($directory, 'JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE');
                try {
                    self::verify_directory_namespace($directory_pins, 'JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE');
                    $entries = scandir($directory);
                    if (!is_array($entries)) self::fail('JOURNAL_CREATED_DIRECTORY_SCAN_FAILED');
                    self::verify_directory_namespace($directory_pins, 'JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE');
                } finally {
                    self::close_directory_namespace($directory_pins);
                }
                if ($entries !== array('.', '..')) continue;
                self::rmdir_empty_in_pinned_namespace($directory, 'JOURNAL_CREATED_DIRECTORY_RECOVERY_FAILED', 'JOURNAL_CREATED_DIRECTORY_NAMESPACE_RACE', 'recovery_rmdir');
            }
        }
        self::verify_restored($journal['attempted_paths'], $artifacts['manifest']);
        self::exact_reverify_backup($journal['base_state'], $journal['backup_sha256']);
        $base = self::save($journal['base_state']);
        $verified = self::read_state_required();
        self::exact_reverify_backup($verified, $journal['backup_sha256']);
        if (!hash_equals((string)$base['checksum'], (string)$verified['checksum'])) self::fail('JOURNAL_BASE_STATE_VERIFY_FAILED');
        self::clear_journal();
        return $base;
    }
    private static function recover_journal(array &$state): void { $state = self::reconcile_state_and_journal(); }
    private static function begin_journal(array &$state, string $phase, array $target_state): void {
        $state = self::validate_checksummed_document($state, 'state');
        $target_state = self::validate_checksummed_document($target_state, 'state');
        self::save_journal(array(
            'schema' => 1,
            'release_id' => $state['release_id'],
            'txid' => $target_state['last_committed_txid'],
            'phase' => $phase,
            'base_state' => $state,
            'target_state' => $target_state,
            'backup_sha256' => $state['backup']['zip_sha256'],
            'attempted_paths' => array(),
            'created_dirs' => array(),
            'step' => 'applying',
        ));
    }
    private static function current_journal(): array {
        $status = self::read_checked_file(self::journal_file(), 'journal');
        if ($status['status'] !== 'valid' || !is_array($status['document'])) self::fail('JOURNAL_CORRUPT_OR_MISSING');
        return $status['document'];
    }
    private static function journal_attempt(array &$state, string $path): void {
        $journal = self::current_journal();
        if (!in_array($path, $journal['attempted_paths'], true)) { $journal['attempted_paths'][] = $path; self::save_journal($journal); }
    }
    private static function journal_created_dir(string $path): void {
        $journal = self::current_journal();
        if (!in_array($path, $journal['created_dirs'], true)) { $journal['created_dirs'][] = $path; self::save_journal($journal); }
    }
    private static function mark_journal_commit_ready(?callable $last_gate = null): void {
        $journal = self::current_journal(); $journal['step'] = 'commit_ready'; self::save_journal($journal, $last_gate);
    }
    private static function ensure_destination_directory(string $relative): void {
        self::assert_safe_release_path($relative);
        $segments = explode('/', $relative); array_pop($segments); $current = self::docroot(); $relative_dir = '';
        foreach ($segments as $segment) {
            $relative_dir = $relative_dir === '' ? $segment : $relative_dir . '/' . $segment;
            $current .= DIRECTORY_SEPARATOR . $segment;
            $stat = @lstat($current);
            if (is_array($stat)) {
                if (self::path_is_link_or_reparse($current, $stat) || (($stat['mode'] & 0170000) !== 0040000)) self::fail('DESTINATION_DIRECTORY_UNSAFE');
                continue;
            }
            if (file_exists($current) || is_link($current)) self::fail('DESTINATION_DIRECTORY_UNSAFE');
            self::journal_created_dir($relative_dir);
            self::mkdir_in_pinned_namespace($current, 0755, 'DESTINATION_DIRECTORY_CREATE_FAILED', 'DESTINATION_DIRECTORY_NAMESPACE_RACE', 'destination_directory_mkdir');
            self::assert_safe_release_path($relative_dir, 'directory_or_missing');
        }
    }
    private static function apply_phase_transaction(array &$state, string $phase, array $staged_files, array $target_state, ?string $failpoint = null): array {
        $expected = self::runtime_phase_files($phase); if ($expected === array()) self::fail('UNKNOWN_RELEASE_PHASE');
        $state = self::validate_checksummed_document($state, 'state');
        $target_state = self::validate_checksummed_document($target_state, 'state');
        if ((int)$target_state['generation'] !== (int)$state['generation'] + 1 || ($target_state['phases'][$phase]['status'] ?? '') !== 'applied' || $target_state['last_committed_txid'] === '') self::fail('TARGET_STATE_INVALID');
        if (!hash_equals((string)$state['backup']['zip_sha256'], (string)$target_state['backup']['zip_sha256'])) self::fail('TARGET_BACKUP_CHANGED');
        $expected_keys = array_keys($expected); $staged_keys = array_keys($staged_files); sort($expected_keys, SORT_STRING); sort($staged_keys, SORT_STRING);
        if ($expected_keys !== $staged_keys) self::fail('STAGED_FILES_INCOMPLETE');
        foreach ($expected as $path => $hash) {
            if (!is_string($staged_files[$path] ?? null)) self::fail('STAGED_FILE_INVALID');
            try { self::assert_safe_storage_regular_file($staged_files[$path]); }
            catch (Throwable $error) { self::fail('STAGED_FILE_INVALID'); }
            if (!hash_equals($hash, self::sha_file($staged_files[$path]))) self::fail('STAGED_FILE_INVALID');
        }
        $artifacts = self::exact_reverify_backup($state, (string)$state['backup']['zip_sha256']);
        foreach ($expected as $path => $_) if (!isset($artifacts['manifest']['paths'][$path])) self::fail('ROLLBACK_MANIFEST_PHASE_GAP');
        self::assert_phase_invariant($phase);
        self::begin_journal($state, $phase, $target_state);
        try {
            foreach ($expected as $path => $hash) {
                self::journal_attempt($state, $path);
                self::ensure_destination_directory($path);
                $before = $artifacts['manifest']['paths'][$path];
                $artifacts = self::exact_reverify_backup($state, (string)$state['backup']['zip_sha256']);
                self::assert_phase_invariant($phase);
                self::atomic_write(
                    $staged_files[$path],
                    false,
                    self::abs_path($path),
                    $hash,
                    !empty($before['exists']) ? (int)$before['mode'] : 0644,
                    (string)$target_state['last_committed_txid'],
                    'apply',
                    $failpoint,
                    static function () use ($phase): void { self::assert_phase_invariant($phase); }
                );
            }
            self::assert_phase_invariant($phase);
            if (!self::live_matches_phase($phase)) self::fail('POST_APPLY_VERIFY_FAILED');
            self::mark_journal_commit_ready(static function () use ($phase): void { self::assert_phase_invariant($phase); });
            if ($failpoint === 'final_state_commit' || $failpoint === 'crash_mid_rollback') self::fail('INJECTED_FINAL_STATE_COMMIT_FAILURE');
            if ($failpoint !== null) self::fail('UNKNOWN_TEST_FAILPOINT');
            self::assert_phase_invariant($phase);
            self::exact_reverify_backup($state, (string)$state['backup']['zip_sha256']);
            $state = self::save($target_state, static function () use ($phase): void { self::assert_phase_invariant($phase); });
            self::assert_phase_invariant($phase);
            self::exact_reverify_backup($state, (string)$state['backup']['zip_sha256']);
            $committed = self::read_state_required();
            if (!hash_equals((string)$state['checksum'], (string)$committed['checksum'])) self::fail('FINAL_STATE_VERIFY_FAILED');
            self::exact_reverify_backup($committed, (string)$state['backup']['zip_sha256']);
            self::assert_phase_invariant($phase);
            self::clear_journal(static function () use ($phase): void { self::assert_phase_invariant($phase); });
            return $state;
        } catch (Throwable $write_error) {
            if ($failpoint === 'crash_before_rename' && $write_error->getMessage() === 'INJECTED_PROCESS_CRASH_BEFORE_RENAME') throw $write_error;
            try { $state = self::reconcile_state_and_journal($failpoint === 'crash_mid_rollback' ? $failpoint : null); }
            catch (Throwable $recovery_error) { self::fail('APPLY_FAILED_RECOVERY_FAILED:' . $write_error->getMessage() . ':' . $recovery_error->getMessage()); }
            self::fail('APPLY_FAILED_RECOVERED:' . $write_error->getMessage());
        }
    }

    private static function create_backup_snapshot(array &$state): void {
        self::require_ziparchive();
        $records = array();
        $storage = self::storage_root(false);
        $storage_pins = self::pin_directory_namespace($storage, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
        $zip_path = $storage . DIRECTORY_SEPARATOR . 'rollback.zip';
        $zip_build_path = $storage . DIRECTORY_SEPARATOR . '.rollback.zip.build.tmp';
        $manifest_path = $storage . DIRECTORY_SEPARATOR . 'rollback-manifest.json';
        $zip = new ZipArchive();
        $zip_open = false;
        $zip_identity = null;
        $zip_published = false;
        $complete = false;
        $preserve_artifacts = false;
        try {
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            self::cleanup_release_owned_temp($zip_path);
            self::cleanup_release_owned_temp($zip_build_path);
            self::cleanup_release_owned_temp($manifest_path);
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            self::namespace_failpoint('backup_zip_open', $zip_build_path);
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            if ($zip->open($zip_build_path, ZipArchive::CREATE | ZipArchive::EXCL) !== true) self::fail('Cannot create rollback ZIP.');
            $zip_open = true;
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            foreach (self::runtime_all_paths() as $relative => $_) {
                $live = self::abs_path($relative);
                $stat = self::assert_safe_release_path($relative);
                $record = array('exists' => $stat !== null);
                if ($stat !== null) {
                    $source_bytes = self::read_regular_file_in_pinned_namespace($live, 'ROLLBACK_SOURCE_NAMESPACE_RACE');
                    $hash = hash('sha256', $source_bytes);
                    $before_add = self::assert_safe_release_path($relative);
                    if ($before_add === null || ($before_add['dev'] ?? null) !== ($stat['dev'] ?? null) || ($before_add['ino'] ?? null) !== ($stat['ino'] ?? null) || $before_add['size'] !== $stat['size'] || (int)$before_add['size'] !== strlen($source_bytes) || (($before_add['mode'] & 0777) !== ($stat['mode'] & 0777))) self::fail('ROLLBACK_SOURCE_DRIFT');
                    $record += array('sha256' => $hash, 'bytes' => strlen($source_bytes), 'mode' => ($before_add['mode'] & 0777));
                    if (!$zip->addFromString('files/' . $relative, $source_bytes)) self::fail('Cannot add a file to rollback ZIP.');
                }
                $records[$relative] = $record;
            }
            $manifest = self::rollback_manifest($records, (string)$state['release_id']);
            $json = self::encode_json($manifest, false);
            if (!$zip->addFromString('rollback-manifest.json', $json)) self::fail('Cannot add rollback manifest.');
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            if (!$zip->close()) self::fail('Cannot finalize rollback ZIP.');
            $zip_open = false;
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            clearstatcache(true, $zip_build_path);
            $zip_identity = @lstat($zip_build_path);
            if (!is_array($zip_identity) || self::path_is_link_or_reparse($zip_build_path, $zip_identity) || (($zip_identity['mode'] & 0170000) !== 0100000)) self::fail('ROLLBACK_ZIP_CREATE_RACE');
            self::set_mode_exact($zip_build_path, 0600, 'ROLLBACK_ZIP_MODE_FAILED');
            self::sync_regular_file($zip_build_path, 'ROLLBACK_ZIP_SYNC_FAILED');
            self::namespace_failpoint('backup_zip_publish', $zip_path);
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            self::assert_path_identity_type($zip_build_path, $zip_identity, 0100000, 'ROLLBACK_ZIP_CREATE_RACE');
            clearstatcache(true, $zip_path);
            if (@lstat($zip_path) !== false || file_exists($zip_path) || is_link($zip_path)) self::fail('ROLLBACK_ZIP_CREATE_RACE');
            if (!@rename($zip_build_path, $zip_path)) self::fail('ROLLBACK_ZIP_CREATE_RACE');
            $zip_published = true;
            self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
            self::assert_path_identity_type($zip_path, $zip_identity, 0100000, 'ROLLBACK_ZIP_CREATE_RACE');
            self::sync_directory(dirname($zip_path));
            self::durable_write($manifest_path, $json, 0600);
            $zip_stat = self::assert_safe_storage_regular_file($zip_path);
            $manifest_stat = self::assert_safe_storage_regular_file($manifest_path);
            $state['backup'] = array(
                'verified' => true,
                'zip_basename' => basename($zip_path),
                'zip_bytes' => (int)$zip_stat['size'],
                'zip_sha256' => self::sha_file($zip_path),
                'manifest_basename' => basename($manifest_path),
                'manifest_bytes' => (int)$manifest_stat['size'],
                'manifest_sha256' => self::sha_file($manifest_path),
            );
            $state['generation'] = (int)$state['generation'] + 1; $state['last_error'] = '';
            self::exact_reverify_backup($state);
            try { $state = self::save($state); }
            catch (Throwable $error) {
                if (str_starts_with($error->getMessage(), 'DURABLE_COMMIT_UNCERTAIN_AFTER_RENAME:state.json:')) $preserve_artifacts = true;
                throw $error;
            }
            $complete = true;
        } finally {
            if ($zip_open) {
                $zip->close();
                $zip_open = false;
                clearstatcache(true, $zip_build_path);
                $partial_stat = @lstat($zip_build_path);
                if (is_array($partial_stat) && !self::path_is_link_or_reparse($zip_build_path, $partial_stat) && (($partial_stat['mode'] & 0170000) === 0100000)) $zip_identity = $partial_stat;
            }
            try {
                self::verify_directory_namespace($storage_pins, 'ROLLBACK_STORAGE_NAMESPACE_RACE');
                if (!$complete && !$preserve_artifacts) {
                    if (is_array($zip_identity)) {
                        $owned_zip_path = $zip_published ? $zip_path : $zip_build_path;
                        self::assert_path_identity_type($owned_zip_path, $zip_identity, 0100000, 'ROLLBACK_ZIP_CREATE_RACE');
                        self::cleanup_release_owned_temp($owned_zip_path);
                    }
                    self::cleanup_release_owned_temp($manifest_path);
                }
            } finally {
                self::close_directory_namespace($storage_pins);
            }
        }
    }
    public static function backup_action(): void {
        self::guard('backup'); try { self::with_lock(function (): void { $state = array(); self::recover_journal($state); if (!empty($state['backup']['verified'])) { self::exact_reverify_backup($state); self::redirect('Backup already verified.'); }
            self::create_backup_snapshot($state); self::redirect('Rollback snapshot verified.'); });
        } catch (Throwable $error) { self::record_error($error->getMessage()); self::redirect('Backup failed.'); } }
    public static function apply_action(): void {
        $requested_phase = isset($_POST['phase']) ? (string)$_POST['phase'] : ''; self::guard('apply', $requested_phase); try { self::with_lock(function () use ($requested_phase): void { $phase_id = $requested_phase; $expectations = self::expected(); if (!isset($expectations[$phase_id])) self::fail('Unknown release phase.'); $state = array(); self::recover_journal($state); if (!self::may_apply($phase_id, $state)) self::fail('Backup or predecessor phase gate is not satisfied.'); $phase = $expectations[$phase_id];
            if (($state['phases'][$phase_id]['status'] ?? '') === 'applied') { foreach ($phase['files'] as $path => $hash) if (self::assert_safe_release_path($path) === null || !hash_equals($hash, self::sha_file(self::abs_path($path)))) self::fail('Completed phase has drifted; refusing a repeat apply.'); self::redirect('Phase already applied; live hashes are verified.'); }
            if (empty($_FILES['release_zip']) || !is_array($_FILES['release_zip']) || ($_FILES['release_zip']['error'] ?? UPLOAD_ERR_NO_FILE) !== UPLOAD_ERR_OK) self::fail('A ZIP upload is required.'); $upload = $_FILES['release_zip']; if ((int)$upload['size'] <= 0 || (int)$upload['size'] > self::MAX_UPLOAD_BYTES || !is_uploaded_file((string)$upload['tmp_name'])) self::fail('Uploaded ZIP violates the size or upload-source policy.'); $archive_hash = self::sha_file((string)$upload['tmp_name']); self::validate_upload_name_hash((string)$upload['name'], $archive_hash, $phase);
            $stage = self::prepare_stage_workspace($phase_id, $archive_hash);
            self::with_stage_cleanup($stage, function () use (&$state, $phase_id, $phase, $stage, $upload): void {
                self::extract_to_stage((string)$upload['tmp_name'], $stage, $phase['files']);
                $lint_files = array(); foreach (array_keys($phase['files']) as $path) { $lint_files[$path] = $stage . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $path); }
                self::with_php_lint_gate($lint_files, function (string $lint) use (&$state, $phase_id, $phase, $stage): void {
                    $artifacts = self::exact_reverify_backup($state); self::verify_apply_drift($artifacts['manifest'], $phase_id);
                    $target_state = $state; unset($target_state['checksum']);
                    $target_state['generation'] = (int)$state['generation'] + 1;
                    $target_state['phases'][$phase_id] = array('status' => 'applied', 'applied_utc' => gmdate('c'), 'lint' => $lint);
                    $target_state['last_error'] = '';
                    $target_state['last_committed_txid'] = 'tx-' . bin2hex(random_bytes(16));
                    $target_state = self::checksummed_document($target_state, 'state');
                    $staged_files = array(); foreach (array_keys($phase['files']) as $path) { $staged_files[$path] = $stage . DIRECTORY_SEPARATOR . str_replace('/', DIRECTORY_SEPARATOR, $path); }
                    self::apply_phase_transaction($state, $phase_id, $staged_files, $target_state);
                });
            });
            self::redirect('Phase ' . $phase_id . ' applied and verified.'); });
        } catch (Throwable $error) { self::record_error($error->getMessage()); self::redirect('Phase apply failed.'); } }
    public static function stage_action(): void {
        self::guard('stage');
        try { self::with_lock(function (): void {
            $state = array(); self::recover_journal($state);
            if (($state['phases']['A1']['status'] ?? '') !== 'applied') self::fail('A1 must be applied before the importer stage checkpoint.');
            if ((string)($_POST['release_id'] ?? '') !== self::HUB_RELEASE_ID) self::fail('Type the exact importer release ID to record the Stage checkpoint.');
            $state['stage_verified'] = true;
            $state['last_error'] = '';
            $state['generation'] = (int)$state['generation'] + 1;
            self::save($state);
            self::redirect('Stage checkpoint recorded. Verify importer Preview/Stage results before applying A2.'); });
        } catch (Throwable $error) { self::record_error($error->getMessage()); self::redirect('Stage checkpoint failed.'); }
    }
    /** Keep PHP lint diagnostics durable without persisting staging paths or process output. */
    private static function stable_error_for_storage(string $message): string {
        foreach (array('PHP_LINT_UNAVAILABLE', 'PHP_LINT_TIMEOUT', 'PHP_LINT_FAILED') as $code) {
            $prefix = $code . ':';
            if (!str_starts_with($message, $prefix)) continue;
            foreach (self::runtime_phase_ids() as $phase) {
                foreach (array_keys(self::runtime_phase_files($phase)) as $path) {
                    $stable = $prefix . $path;
                    if ($message === $stable || str_starts_with($message, $stable . ':')) return $stable;
                }
            }
            return 'PHP_LINT_PATH_INVALID';
        }
        return substr($message, 0, 500);
    }
    private static function record_error(string $message): void {
        $message = self::stable_error_for_storage($message);
        try { self::with_lock(function () use ($message): void { $state = array(); self::recover_journal($state); $state['generation'] = (int)$state['generation'] + 1; $state['last_error'] = $message; self::save($state); }); }
        catch (Throwable $ignored) {}
    }
    private static function redirect(string $message): void { wp_safe_redirect(add_query_arg('land76_notice', rawurlencode($message), admin_url('tools.php?page=land76-release-deployer'))); exit; }
    public static function download_action(): void { self::download_guard(); try { $state = self::state(); $artifacts = self::exact_reverify_backup($state); $backup = $state['backup']; $bytes = self::read_regular_file_in_pinned_namespace($artifacts['zip'], 'ROLLBACK_DOWNLOAD_RACE'); if (strlen($bytes) !== (int)$backup['zip_bytes'] || !hash_equals((string)$backup['zip_sha256'], hash('sha256', $bytes))) self::fail('ROLLBACK_DOWNLOAD_RACE'); nocache_headers(); header('Cache-Control: no-store, private, max-age=0'); header('X-Content-Type-Options: nosniff'); header('Content-Type: application/zip'); header('Content-Length: ' . (string)$backup['zip_bytes']); header('Content-Disposition: attachment; filename="' . basename((string)$backup['zip_basename']) . '"'); echo $bytes; exit; } catch (Throwable $error) { wp_die(esc_html($error->getMessage()), 404); } }
    public static function menu(): void { add_management_page('Land76 release deployer', 'Land76 release deployer', 'manage_options', 'land76-release-deployer', array(__CLASS__, 'page')); }
    public static function page(): void { if (!current_user_can('manage_options')) wp_die(esc_html__('Unauthorized.', 'land76-release-deployer'), 403); $state = self::state(); $phase = null; foreach (self::ORDER as $candidate) if (($state['phases'][$candidate]['status'] ?? '') !== 'applied') { $phase = $candidate; break; } ?>
        <div class="wrap"><h1>Land76 release deployer</h1><p><strong>Внимание:</strong> публикация и действия импортера выполняются отдельно и этот плагин их не запускает.</p>
        <?php if (isset($_GET['land76_notice'])) : ?><div class="notice notice-info"><p><?php echo esc_html(rawurldecode((string)$_GET['land76_notice'])); ?></p></div><?php endif; ?>
        <table class="widefat striped"><tbody><tr><th>Backup verified</th><td><?php echo !empty($state['backup']['verified']) ? 'yes' : 'no'; ?></td></tr><?php foreach (self::ORDER as $id) : ?><tr><th><?php echo esc_html($id); ?></th><td><?php echo esc_html((string)$state['phases'][$id]['status']); ?><?php if (isset($state['phases'][$id]['lint'])) : ?> — PHP lint: <?php echo esc_html((string)$state['phases'][$id]['lint']); ?><?php endif; ?></td></tr><?php endforeach; ?><?php if (!empty($state['backup']['verified'])) : ?><tr><th>Archive</th><td><?php echo esc_html($state['backup']['zip_basename'] . ' — ' . $state['backup']['zip_bytes'] . ' bytes — ' . $state['backup']['zip_sha256']); ?></td></tr><?php endif; ?><tr><th>Last error</th><td><?php echo esc_html((string)$state['last_error']); ?></td></tr></tbody></table>
        <?php if (empty($state['backup']['verified'])) : ?><form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="land76_release_backup"><?php wp_nonce_field(self::nonce_action('backup')); submit_button('Create verified rollback snapshot'); ?></form><?php else : ?><p><a class="button" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=land76_release_download'), self::nonce_action('download'))); ?>">Download rollback archive</a></p><?php if ($phase === 'A2' && empty($state['stage_verified'])) : ?><h2>Importer Stage checkpoint</h2><p>Run importer Preview and Stage separately, then type <code><?php echo esc_html(self::HUB_RELEASE_ID); ?></code> to unlock A2.</p><form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="land76_release_stage"><?php wp_nonce_field(self::nonce_action('stage')); ?><input name="release_id" required><input type="submit" class="button" value="Record Stage checkpoint"></form><?php elseif ($phase !== null && self::may_apply($phase, $state)) : ?><h2>Apply phase <?php echo esc_html($phase); ?></h2><form method="post" enctype="multipart/form-data" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><input type="hidden" name="action" value="land76_release_apply"><input type="hidden" name="phase" value="<?php echo esc_attr($phase); ?>"><?php wp_nonce_field(self::nonce_action('apply', $phase)); ?><input required type="file" name="release_zip" accept=".zip,application/zip"><?php submit_button('Upload and apply ' . $phase); ?></form><?php endif; endif; ?></div>
    <?php }
}
Land76_Release_Deployer::init();
if (function_exists('register_activation_hook')) register_activation_hook(__FILE__, array('Land76_Release_Deployer', 'activate'));
