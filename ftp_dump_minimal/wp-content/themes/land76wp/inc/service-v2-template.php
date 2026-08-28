<?php
/** Render the prevalidated service-v2 fragment for the current page. */

if (!defined('ABSPATH')) {
  exit;
}
$service_v2 = land76_service_v2_current();
if ($service_v2 && isset($service_v2['_rendered_html'])) {
  // Generated HTML bytes were read and verified once by the fail-closed loader.
  echo $service_v2['_rendered_html'];
}
