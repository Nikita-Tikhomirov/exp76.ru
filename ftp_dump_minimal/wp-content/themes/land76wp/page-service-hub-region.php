<?php
/*
Template Name: Service Hub Region
*/

if (!defined('ABSPATH')) {
    exit;
}

$land76_region_page_id = get_queried_object_id();
$land76_region_service_id = (string) get_post_meta($land76_region_page_id, '_land76_service_id', true);
$land76_region_topic_key = (string) get_post_meta($land76_region_page_id, '_land76_topic_key', true);
$land76_region_page_key = (string) get_post_meta($land76_region_page_id, '_land76_page_key', true);
$land76_region_owner = (string) get_post_meta($land76_region_page_id, '_land76_import_owner', true);
$land76_region_canonical = (string) get_post_meta($land76_region_page_id, '_land76_canonical', true);
$land76_region_main_image_url = (string) get_post_meta($land76_region_page_id, '_land76_main_image_url', true);
$land76_region_main_image_alt = (string) get_post_meta($land76_region_page_id, '_land76_main_image_alt', true);
$land76_region_slug = (string) get_post_meta($land76_region_page_id, '_land76_region', true);
$land76_region_evidence_raw = (string) get_post_meta($land76_region_page_id, '_land76_local_evidence', true);
$land76_region_evidence = json_decode($land76_region_evidence_raw, true);
$land76_region_page = get_post($land76_region_page_id);
$land76_region_parent = $land76_region_page instanceof WP_Post ? get_post((int) $land76_region_page->post_parent) : null;
$land76_region_hub = function_exists('land76wp_service_hub_by_service_id')
    ? land76wp_service_hub_by_service_id($land76_region_service_id)
    : null;
$land76_region_evidence_errors = function_exists('land76wp_service_hubs_validate_local_evidence')
    ? land76wp_service_hubs_validate_local_evidence($land76_region_evidence, $land76_region_page_key)
    : array('evidence_validator_unavailable');
$land76_region_actual_canonical = function_exists('land76wp_service_hubs_normalize_url')
    ? land76wp_service_hubs_normalize_url(get_permalink($land76_region_page_id))
    : '';
$land76_region_case_ids = function_exists('get_field')
    ? get_field('selected_real_projects', $land76_region_page_id)
    : array();
$land76_region_case_ids = is_array($land76_region_case_ids) ? $land76_region_case_ids : array();

$land76_region_valid = $land76_region_page instanceof WP_Post
    && $land76_region_page->post_type === 'page'
    && $land76_region_page->post_status === 'publish'
    && hash_equals('land76-service-hubs', $land76_region_owner)
    && hash_equals($land76_region_service_id, $land76_region_topic_key)
    && strpos($land76_region_page_key, $land76_region_service_id . '-GEO-') === 0
    && $land76_region_canonical !== ''
    && hash_equals($land76_region_canonical, $land76_region_actual_canonical)
    && $land76_region_main_image_url !== ''
    && $land76_region_main_image_alt !== ''
    && $land76_region_parent instanceof WP_Post
    && $land76_region_parent->post_type === 'page'
    && $land76_region_parent->post_status === 'publish'
    && (int) $land76_region_parent->post_parent === 0
    && $land76_region_parent->post_name === $land76_region_slug
    && $land76_region_hub !== null
    && is_array($land76_region_evidence)
    && $land76_region_evidence_errors === array();

if (!$land76_region_valid) {
    status_header(404);
    nocache_headers();
    $land76_not_found_template = get_404_template();
    if ($land76_not_found_template) {
        include $land76_not_found_template;
    }
    exit;
}

get_header();
?>
<main class="service-hub-region" data-service-id="<?php echo esc_attr($land76_region_service_id); ?>">
  <section class="hero service-hub-region__hero">
    <div class="hero__content wrapper">
      <h1 class="hero__title"><?php echo esc_html(get_the_title($land76_region_page_id)); ?></h1>
      <div class="hero__breadcramps">
        <a class="hero__home" href="<?php echo esc_url(home_url('/')); ?>">Компания «Эксперты» | </a>
        <a class="hero__home" href="<?php echo esc_url(get_permalink($land76_region_parent)); ?>"><?php echo esc_html(get_the_title($land76_region_parent)); ?> | </a>
        <a class="hero__home" href="<?php echo esc_url($land76_region_hub['canonical']); ?>"><?php echo esc_html(get_the_title((int) $land76_region_hub['hub_post_id'])); ?> | </a>
        <span class="hero__active-page"><?php echo esc_html(get_the_title($land76_region_page_id)); ?></span>
      </div>
    </div>
  </section>

  <section class="services wrapper service-hub-region__content">
    <figure class="service-hub-region__main-image">
      <img src="<?php echo esc_url($land76_region_main_image_url); ?>" alt="<?php echo esc_attr($land76_region_main_image_alt); ?>">
    </figure>
    <?php echo wp_kses_post(apply_filters('the_content', $land76_region_page->post_content)); ?>
    <div class="service-hub-region__evidence" aria-label="Подтвержденные сведения по региону">
      <?php foreach ($land76_region_evidence as $land76_evidence_item) : ?>
        <?php if (is_string($land76_evidence_item) && trim($land76_evidence_item) !== '') : ?>
          <p><?php echo esc_html($land76_evidence_item); ?></p>
        <?php elseif (is_array($land76_evidence_item) && !empty($land76_evidence_item['text'])) : ?>
          <p><?php echo esc_html($land76_evidence_item['text']); ?></p>
        <?php endif; ?>
      <?php endforeach; ?>
    </div>
    <?php if ($land76_region_case_ids !== array()) : ?>
      <div class="service-hub-region__cases">
        <h2>Примеры работ</h2>
        <div class="services__cards columns3">
          <?php foreach ($land76_region_case_ids as $land76_region_case_id) : ?>
            <?php
            $land76_region_case = get_post((int) $land76_region_case_id);
            if (!$land76_region_case instanceof WP_Post
                || $land76_region_case->post_type !== 'page'
                || $land76_region_case->post_status !== 'publish'
                || get_page_template_slug($land76_region_case->ID) !== 'casenew.php') {
                continue;
            }
            ?>
            <article class="service">
              <div class="service__text-wrap">
                <h3 class="service__title"><?php echo esc_html(get_the_title($land76_region_case)); ?></h3>
                <div class="service__link-wrap">
                  <a class="service__link" href="<?php echo esc_url(get_permalink($land76_region_case)); ?>">Смотреть работу</a>
                </div>
              </div>
            </article>
          <?php endforeach; ?>
        </div>
      </div>
    <?php endif; ?>
  </section>

  <?php
  $land76_shared_service_template = get_template_directory() . '/inc/service-v2-template.php';
  if (is_readable($land76_shared_service_template)) {
      include $land76_shared_service_template;
  }
  ?>
</main>
<?php
get_footer();
