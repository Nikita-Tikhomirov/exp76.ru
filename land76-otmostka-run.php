<?php
$token = 'run_20260501_otmostka_4f7b2a9c';
$provided = isset($_GET['token']) ? (string) $_GET['token'] : '';
if (!hash_equals($token, $provided)) {
    http_response_code(403);
    exit('forbidden');
}

require __DIR__ . '/wp-load.php';

$import_file = get_template_directory() . '/inc/import-otmostka.php';
if (file_exists($import_file)) {
    require_once $import_file;
}

if (!function_exists('land76wp_run_otmostka_import')) {
    http_response_code(500);
    exit('import function not found');
}

$result = land76wp_run_otmostka_import();
header('Content-Type: application/json; charset=utf-8');
echo wp_json_encode($result, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
