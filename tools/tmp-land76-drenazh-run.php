<?php
$token = 'run_20260426_e74e1f_9f7c8d2a';
$provided = isset($_GET['token']) ? (string) $_GET['token'] : '';
if (!hash_equals($token, $provided)) {
    http_response_code(403);
    exit('forbidden');
}

require __DIR__ . '/../ftp_dump_minimal/../../../../../../../../wp-load.php';

if (!function_exists('land76wp_run_drenazh_import')) {
    http_response_code(500);
    exit('import function not found');
}

$result = land76wp_run_drenazh_import();
header('Content-Type: application/json; charset=utf-8');
echo wp_json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
