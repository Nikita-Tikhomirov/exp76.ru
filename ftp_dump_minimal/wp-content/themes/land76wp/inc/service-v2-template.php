<?php
/** Render the prevalidated service-v2 fragment for the current page. */

if (!defined('ABSPATH')) {
  exit;
}
$land76_service_v2_path = land76_service_v2_rendered_path();
if ($land76_service_v2_path && is_readable($land76_service_v2_path)) {
  readfile($land76_service_v2_path);
}
