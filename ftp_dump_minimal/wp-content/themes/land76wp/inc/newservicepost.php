<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/index.css" />
<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/services.css" />
<style>
  .hero {
    min-height: 620px;
  }

  .hero__subtitle {
    color: #fff;
    font-size: 24px;
    margin-top: 15px;
    margin-bottom: 15px;
    font-weight: 500;
    text-shadow: 1px 1px 3px #000;
  }

  .hero__content {
    align-items: flex-start;
    justify-content: center;
  }

  .hero__buttons {
    margin-top: 24px;
  }

  .hero__breadcramps {
    color: #fff;
    position: absolute;
    bottom: 30px;
    text-align: right;
    font-size: 16px;
    padding: 4px 10px;
    background-color: #0000004d;
    -ms-flex-item-align: start;
    align-self: start
  }

  .hero__active-page {
    border-bottom: 2px solid #a2f9a9
  }

  .problem-block {
    background: #f9f9f9;
    padding: 40px;
    border-radius: 10px;
    margin-bottom: 40px;
    border-left: 4px solid #0a9215;
  }

  .problem-block h3 {
    color: #0a9215;
    font-family: "Poiret One", cursive;
    font-size: 28px;
    margin-bottom: 20px;
  }

  .problem-item {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    padding: 15px;
    background: #fff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .problem-item img {
    width: 60px;
    height: 60px;
    margin-right: 20px;
    border-radius: 50%;
    object-fit: cover;
  }

  .problem-item__number {
    align-items: center;
    background: #0a9215;
    border: 2px solid #fff;
    border-radius: 50%;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.22);
    color: #fff;
    display: inline-flex;
    flex: 0 0 60px;
    font-size: 18px;
    font-weight: 700;
    height: 60px;
    justify-content: center;
    margin-right: 20px;
    width: 60px;
  }

  .solution-block {
    background: #fff;
    padding: 40px;
    border-radius: 10px;
    margin-bottom: 40px;
    border: 2px solid #0a9215;
  }

  .solution-block h3 {
    color: #0a9215;
    font-family: "Poiret One", cursive;
    font-size: 28px;
    margin-bottom: 20px;
    text-align: center;
  }

  .tech-block {
    background: #f5f5f5;
    padding: 40px;
    border-radius: 10px;
    margin-bottom: 40px;
  }

  .tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 30px;
  }

  .tech-item {
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .tech-item h4 {
    color: #0a9215;
    font-family: "Poiret One", cursive;
    font-size: 20px;
    margin-bottom: 15px;
  }

  .error-block {
    background: #fff3f3;
    padding: 40px;
    border-radius: 10px;
    margin-bottom: 40px;
    border-left: 4px solid #d32f2f;
  }

  .error-block h3 {
    color: #d32f2f;
    font-family: "Poiret One", cursive;
    font-size: 28px;
    margin-bottom: 20px;
  }

  .error-item {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    padding: 15px;
    background: #fff;
    border-radius: 8px;
    /* border-left: 3px solid #d32f2f; */
  }

  .error-item img {
    width: 50px;
    height: 50px;
    margin-right: 15px;
  }

  .btn--primary-custom {
    display: inline-block;
    padding: 15px 30px;
    background: #0a9215;
    color: #fff;
    text-decoration: none;
    border-radius: 25px;
    font-weight: 600;
    font-size: 16px;
    transition: all 0.3s ease;
    border: 2px solid #0a9215;
  }

  .btn--primary-custom:hover {
    background: #0a7b12;
    color: #fff;
    text-decoration: none;
    border-color: #0a7b12;
  }

  .faq-toggle {
    margin: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    width: 100%;
    flex: 1 1 auto;
    font-weight: 600;
    line-height: 1.25;
    min-width: 0;
  }

  .service-faq-section {
    overflow-x: hidden;
  }

  .service-faq-title {
    text-align: center;
    color: #0a9215;
    font-family: "Poiret One", cursive;
    font-size: 35px;
    line-height: 1.25;
    margin: 0 0 40px;
    overflow-wrap: anywhere;
  }

  .service-faq-list {
    display: grid;
    gap: 20px;
    margin-bottom: 30px;
  }

  .service-faq-item {
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
  }

  .service-faq-question {
    background: #f5f5f5;
    padding: 20px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-width: 0;
  }

  .faq-question-text {
    flex: 1 1 auto;
    min-width: 0;
    font-size: 22px;
    color: #333;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  .faq-icon {
    flex: 0 0 auto;
    font-size: 24px;
    color: #0a9215;
    line-height: 1;
  }

  .faq-answer {
    background: #fff;
    padding: 20px;
    border-top: 1px solid #ddd;
  }

  .casesCustom {
    background: #fff;
    border-top: 2px solid #0a9215;
  }

  .howWorkCustom {
    border-bottom: 2px solid #0a9215;
  }

  .estimate-list {
    margin: 20px 0;
    padding-left: 0;
    list-style: none;
  }

  .estimate-list li {
    margin-bottom: 15px;
    line-height: 1.6;
    color: #333;
    position: relative;
    padding-left: 30px;
    font-size: 16px;
  }

  .estimate-list li:before {
    content: "\2713";
    position: absolute;
    left: 0;
    top: 2px;
    width: 20px;
    height: 20px;
    background: #0a9215;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 12px;
  }

  .problem-block p {
    margin-bottom: 25px;
  }

  .error-block p {
    margin-bottom: 25px;
  }

  .advantages {
    padding-top: 50px;
    padding-bottom: 50px;
    -webkit-box-shadow: inset 0 5px 5px rgba(0, 0, 0, .1);
    box-shadow: inset 0 5px 5px rgba(0, 0, 0, .1);
    background: url('<?php echo esc_url(get_template_directory_uri() . '/img/adv.png'); ?>') 0 0/cover fixed;
    border-top: 2px solid #0a9215
  }

  /* Media Queries */
  @media (max-width: 1024px) {
    /* Tablets */
    .advantages__how {
      flex-wrap: wrap;
      gap: 30px;
    }
    
    .advantages__step {
      flex-basis: 45%;
    }
    
    .advantages__arrow {
      display: none;
    }
    
    .advantages__text-wrap {
      width: 100%;
    }
    
    .advantages__text {
      width: 100%;
    }
    
    /* Hero font sizes for tablets */
    .hero__title {
      font-size: 28px;
    }
    
    .hero__subtitle {
      font-size: 18px;
    }
  }

  @media (max-width: 768px) {
    /* Small tablets and large mobile */
    .hero__breadcramps{
      flex-wrap: wrap;
    }
      .hero__buttons {
    display: grid;
    grid-gap: 10px;
    width: 100%;
  }
  .hero__buttons .openPopup{
    margin-left: auto !important;
  }
    .advantages__title {
      font-size: 35px;
    }
    
    .advantages__how-title {
      font-size: 28px;
    }
    
    .advantages__local {
      font-size: 24px;
    }
    
    .advantages__step {
      flex-basis: 100%;
    }
    
    .advantages__step p {
      font-size: 16px;
    }
    
    .advantages__svg-wrap {
      width: 80px;
      height: 80px;
      padding: 15px;
    }
    .hero{
      height: 80vh;
    }
    /* Hero font sizes for mobile */
    .hero__title {
      font-size: 38px;
    }
    
    .hero__subtitle {
      font-size: 20px;
      text-align: center;
    }
    .hero__buttons {
      display: grid;
      grid-gap: 10px;
      width: 100%;
    }
    .hero__buttons .openPopup{
      margin-left: auto !important;
    }

    /* Solution block responsive */
    .solution-block div[style*="grid-template-columns"] {
      grid-template-columns: 1fr !important;
      gap: 20px !important;
    }

    /* Problem items responsive */
    .problem-item {
      flex-direction: column;
      text-align: center;
    }

    .problem-item img,
    .problem-item__number {
      margin-right: 0;
      margin-bottom: 15px;
    }

    /* Error items responsive */
    .error-item {
      flex-direction: column;
      text-align: center;
    }

    .error-item img {
      margin-right: 0;
      margin-bottom: 15px;
    }

    /* Tech grid responsive */
    .tech-grid {
      grid-template-columns: 1fr !important;
      gap: 15px !important;
    }

    /* Other drainage types responsive */
    .columns3 {
      grid-template-columns: 1fr !important;
      gap: 20px !important;
    }

    /* Table responsive */
    table[style*="width: 100%"] {
      font-size: 14px;
    }

    table[style*="width: 100%"] th,
    table[style*="width: 100%"] td {
      padding: 10px !important;
      font-size: 12px;
    }

    /* FAQ responsive */
    .faq-toggle {
      font-size: 16px !important;
    }

    .faq-question-text {
      font-size: 20px !important;
    }
  }

  @media (max-width: 480px) {
    /* Mobile phones */
    .advantages__title {
      font-size: 28px;
    }
    
    .advantages__how-title {
      font-size: 24px;
    }
    
    .advantages__local {
      font-size: 20px;
    }
    
    .advantages {
      padding-top: 30px;
      padding-bottom: 30px;
    }
    
    .advantages__svg-wrap {
      width: 70px;
      height: 70px;
      padding: 12px;
    }
    
    .advantages__step p {
      font-size: 14px;
    }
    
    .cta-form {
      flex-direction: column;
      align-items: center;
    }
    
    .cta-form input {
      width: 100%;
      min-width: auto;
    }
    
    .cta-btn-custom {
      width: 100%;
    }
    
    /* Hero font sizes for small mobile */
    .hero__title {
      font-size: 24px;
      line-height: 1.2;
    }
    
    .hero__subtitle {
      font-size: 16px;
      line-height: 1.4;
    }

    /* Problem and error blocks responsive */
    .problem-block,
    .error-block,
    .solution-block {
      padding: 20px;
    }

    .problem-block h3,
    .error-block h3,
    .solution-block h3 {
      font-size: 22px;
    }

    .problem-item img,
    .error-item img {
      width: 50px;
      height: 50px;
    }

    /* Breadcrumbs responsive */
    .hero__breadcramps {
      font-size: 14px;
      padding: 6px 12px;
    }

    /* Estimate list responsive */
    .estimate-list li {
      font-size: 14px;
      padding-left: 25px;
    }

    /* Section titles responsive */
    h2[style*="font-size: 35px"] {
      font-size: 28px !important;
    }

    .service-faq-section {
      padding-top: 32px;
      padding-bottom: 32px;
    }

    .service-faq-title {
      font-size: 28px;
      line-height: 1.2;
      margin-bottom: 24px;
      padding: 0 8px;
    }

    .service-faq-list {
      gap: 14px;
      margin-bottom: 0;
    }

    .service-faq-question {
      padding: 14px 16px;
      align-items: flex-start;
    }

    /* Tech items responsive */
    .tech-item {
      padding: 15px;
    }

    .tech-item h4 {
      font-size: 18px;
    }

    .tech-item p {
      font-size: 14px;
    }

    /* FAQ responsive */
    .faq-toggle {
      font-size: 14px !important;
      gap: 10px;
    }

    .faq-question-text {
      font-size: 18px !important;
    }

    .faq-icon {
      font-size: 22px !important;
      margin-top: 2px;
    }

    .faq-answer {
      padding: 14px 16px;
    }

    .faq-answer p {
      font-size: 15px;
      line-height: 1.55;
    }
  }
</style>
<?php
if (!function_exists('land76_newservice_managed_presentation_image')) {
    function land76_newservice_managed_presentation_image($post_id, $role)
    {
        $empty = array('url' => '', 'alt' => '');
        $is_managed = hash_equals(
            'land76-service-hubs',
            (string) get_post_meta($post_id, '_land76_import_owner', true)
        );
        if (!$is_managed || !in_array($role, array('main', 'hero', 'context'), true)) {
            return $empty;
        }

        $url = (string) get_post_meta($post_id, '_land76_' . $role . '_image_url', true);
        $alt = (string) get_post_meta($post_id, '_land76_' . $role . '_image_alt', true);
        if (($url === '' || $alt === '') && $role !== 'main') {
            $url = (string) get_post_meta($post_id, '_land76_main_image_url', true);
            $alt = (string) get_post_meta($post_id, '_land76_main_image_alt', true);
        }
        if ($url === '' || $alt === '') {
            return $empty;
        }

        return array('url' => $url, 'alt' => $alt);
    }
}

if (!function_exists('land76_newservice_related_card_image')) {
    /** Pick the first page-unique related-card image from semantic and real-media fallbacks. */
    function land76_newservice_related_card_image($post_id, &$seen = null, $size = 'full')
    {
        $post_id = (int) $post_id;
        $empty = array('url' => '', 'alt' => '');
        $candidates = array();
        $candidate_identities = array();
        $append_candidate = static function ($url, $alt) use (&$candidates, &$candidate_identities, $size) {
            $url = (string) $url;
            $alt = (string) $alt;
            if ($url === '' || $alt === '') {
                return;
            }
            if ($size !== 'full' && function_exists('attachment_url_to_postid')) {
                $attachment_id = (int) attachment_url_to_postid($url);
                if ($attachment_id > 0) {
                    $sized_url = (string) wp_get_attachment_image_url($attachment_id, $size);
                    if ($sized_url !== '') {
                        $url = $sized_url;
                    }
                }
            }
            $identity = land76_newservice_image_identity($url);
            if ($identity === '' || isset($candidate_identities[$identity])) {
                return;
            }
            $candidate_identities[$identity] = true;
            $candidates[] = array('url' => $url, 'alt' => $alt);
        };
        $hub = function_exists('land76wp_service_hub_for_post')
            ? land76wp_service_hub_for_post($post_id)
            : null;
        if (is_array($hub) && function_exists('land76_service_v2_load')) {
            $hub_post_id = (int) $hub['hub_post_id'];
            $service_v2 = $hub_post_id > 0 ? land76_service_v2_load($hub_post_id) : null;
            if (is_array($service_v2)) {
                if ($hub_post_id === $post_id) {
                    if (!empty($service_v2['hero']['image']['url'])
                        && !empty($service_v2['hero']['image']['alt'])) {
                        $append_candidate(
                            $service_v2['hero']['image']['url'],
                            $service_v2['hero']['image']['alt']
                        );
                    }
                    foreach (array('scope', 'services', 'articles') as $hub_section_name) {
                        $hub_items = isset($service_v2[$hub_section_name]['items'])
                            && is_array($service_v2[$hub_section_name]['items'])
                            ? $service_v2[$hub_section_name]['items']
                            : array();
                        foreach ($hub_items as $hub_item) {
                            if (!is_array($hub_item)
                                || empty($hub_item['image']['url'])
                                || empty($hub_item['image']['alt'])) {
                                continue;
                            }
                            $append_candidate(
                                $hub_item['image']['url'],
                                $hub_item['image']['alt']
                            );
                        }
                    }
                }
                $page_key = (string) get_post_meta($post_id, '_land76_page_key', true);
                foreach (array('services', 'articles') as $section_name) {
                    $items = isset($service_v2[$section_name]['items']) && is_array($service_v2[$section_name]['items'])
                        ? $service_v2[$section_name]['items']
                        : array();
                    foreach ($items as $item) {
                        if (!is_array($item)
                            || empty($item['page_key'])
                            || !hash_equals($page_key, (string) $item['page_key'])
                            || empty($item['image']['url'])
                            || empty($item['image']['alt'])) {
                            continue;
                        }
                        $append_candidate(
                            $item['image']['url'],
                            $item['image']['alt']
                        );
                        break 2;
                    }
                }
            }
        }

        foreach (array('card', 'main') as $role) {
            $url = (string) get_post_meta($post_id, '_land76_' . $role . '_image_url', true);
            $alt = (string) get_post_meta($post_id, '_land76_' . $role . '_image_alt', true);
            $append_candidate($url, $alt);
        }

        foreach ($candidates as $candidate) {
            if (!is_array($seen)
                || land76_newservice_reserve_image($seen, $candidate['url'])) {
                return $candidate;
            }
        }

        return $empty;
    }
}

if (!function_exists('land76_newservice_image_identity')) {
    /** Normalize one media file across full-size and WordPress resized URLs. */
    function land76_newservice_image_identity($url)
    {
        $path = (string) wp_parse_url((string) $url, PHP_URL_PATH);
        if ($path === '') {
            return '';
        }

        $path = (string) preg_replace('/-\d+x\d+(?=\.[a-z0-9]+$)/i', '', $path);
        $path = (string) preg_replace('/-scaled(?=\.[a-z0-9]+$)/i', '', $path);
        return strtolower(rawurldecode($path));
    }
}

if (!function_exists('land76_newservice_reserve_image')) {
    /** Reserve an image for the current page and reject a repeated visual. */
    function land76_newservice_reserve_image(array &$seen, $url)
    {
        $identity = land76_newservice_image_identity($url);
        if ($identity === '' || isset($seen[$identity])) {
            return false;
        }

        $seen[$identity] = true;
        return true;
    }
}

if (!function_exists('land76_newservice_unique_project_image')) {
    /** Select the first real case image that has not already appeared on the page. */
    function land76_newservice_unique_project_image($post_id, array &$seen, $size = 'medium')
    {
        $post_id = (int) $post_id;
        $fallback_alt = wp_strip_all_tags((string) get_the_title($post_id));
        $candidates = array();
        $append_candidate = static function ($image) use (&$candidates, $size, $fallback_alt) {
            $url = '';
            $alt = $fallback_alt;
            if (is_array($image)) {
                if (!empty($image['sizes'][$size])) {
                    $url = (string) $image['sizes'][$size];
                } elseif (!empty($image['url'])) {
                    $url = (string) $image['url'];
                }
                if (!empty($image['alt'])) {
                    $alt = (string) $image['alt'];
                }
            } elseif ($image instanceof WP_Post) {
                $url = (string) wp_get_attachment_image_url((int) $image->ID, $size);
                $attachment_alt = (string) get_post_meta((int) $image->ID, '_wp_attachment_image_alt', true);
                if ($attachment_alt !== '') {
                    $alt = $attachment_alt;
                }
            } elseif (is_int($image) || (is_string($image) && ctype_digit($image))) {
                $attachment_id = (int) $image;
                $url = (string) wp_get_attachment_image_url($attachment_id, $size);
                $attachment_alt = (string) get_post_meta($attachment_id, '_wp_attachment_image_alt', true);
                if ($attachment_alt !== '') {
                    $alt = $attachment_alt;
                }
            } elseif (is_string($image)) {
                $url = $image;
            }
            if ($url !== '') {
                $candidates[] = array('url' => $url, 'alt' => $alt);
            }
        };

        if (function_exists('land76_get_card_image_url')) {
            $append_candidate(land76_get_card_image_url($post_id, $size, false));
        } else {
            $append_candidate(get_the_post_thumbnail_url($post_id, $size));
        }
        if (function_exists('get_field')) {
            $slider = get_field('slider', $post_id);
            if (is_array($slider)) {
                foreach ($slider as $row) {
                    if (is_array($row) && array_key_exists('image', $row)) {
                        $append_candidate($row['image']);
                    }
                }
            }
        }
        $attachments = get_attached_media('image', $post_id);
        if (is_array($attachments)) {
            foreach ($attachments as $attachment) {
                $append_candidate($attachment);
            }
        }

        foreach ($candidates as $candidate) {
            $url = $candidate['url'];
            if (land76_newservice_reserve_image($seen, $url)) {
                return $candidate;
            }
        }

        return array('url' => '', 'alt' => '');
    }
}

$ns87_post_context = get_the_ID();
$land76_managed_service_hub_post = hash_equals(
    'land76-service-hubs',
    (string) get_post_meta($ns87_post_context, '_land76_import_owner', true)
);
$ns87_main_image = land76_newservice_managed_presentation_image($ns87_post_context, 'main');
$ns87_hero_image = land76_newservice_managed_presentation_image($ns87_post_context, 'hero');
$ns87_context_image = land76_newservice_managed_presentation_image($ns87_post_context, 'context');
if ($land76_managed_service_hub_post) {
    $ns87_hub_service_image = land76_newservice_related_card_image($ns87_post_context);
    $ns87_hub_service_identity = land76_newservice_image_identity($ns87_hub_service_image['url']);
    $ns87_hero_image_identity = land76_newservice_image_identity($ns87_hero_image['url']);
    if ($ns87_hub_service_image['url'] !== ''
        && $ns87_hub_service_image['alt'] !== ''
        && $ns87_hub_service_identity !== ''
        && !hash_equals($ns87_hero_image_identity, $ns87_hub_service_identity)) {
        $ns87_main_image = $ns87_hub_service_image;
    }
}
$ns87_main_image_url = $ns87_main_image['url'];
$ns87_main_image_alt = $ns87_main_image['alt'];
$ns87_hero_image_url = $ns87_hero_image['url'];
$ns87_hero_image_alt = $ns87_hero_image['alt'];
$ns87_context_image_url = $ns87_context_image['url'];
$ns87_context_image_alt = $ns87_context_image['alt'];
$ns87_rendered_image_identities = array();
$ns87_render_hero_image = $ns87_hero_image_url !== '';
$ns87_render_main_image = $ns87_main_image_url !== '' && $ns87_main_image_alt !== '';
$ns87_render_context_image = $ns87_context_image_url !== '' && $ns87_context_image_alt !== '';
if ($land76_managed_service_hub_post) {
    $ns87_render_hero_image = $ns87_render_hero_image && land76_newservice_reserve_image($ns87_rendered_image_identities, $ns87_hero_image_url);
    $ns87_render_main_image = $ns87_render_main_image && land76_newservice_reserve_image($ns87_rendered_image_identities, $ns87_main_image_url);
    $ns87_render_context_image = $ns87_render_context_image && land76_newservice_reserve_image($ns87_rendered_image_identities, $ns87_context_image_url);
}
$ns87_hero_title = function_exists('get_field') ? get_field('ns87_hero_title', $ns87_post_context) : '';
$ns87_hero_subtitle = function_exists('get_field') ? get_field('ns87_hero_subtitle', $ns87_post_context) : '';
$ns87_hero_btn_primary_text = function_exists('get_field') ? get_field('ns87_hero_btn_primary_text', $ns87_post_context) : '';
$ns87_hero_btn_primary_url = function_exists('get_field') ? get_field('ns87_hero_btn_primary_url', $ns87_post_context) : '';
$ns87_hero_btn_secondary_text = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_text', $ns87_post_context) : '';
$ns87_hero_btn_secondary_url = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_url', $ns87_post_context) : '';
$ns87_problem_title = function_exists('get_field') ? get_field('ns87_problem_title', $ns87_post_context) : '';
$ns87_problem_text = function_exists('get_field') ? get_field('ns87_problem_text', $ns87_post_context) : '';
$ns87_problem_items = function_exists('get_field') ? get_field('ns87_problem_items', $ns87_post_context) : array();
if ($land76_managed_service_hub_post
    && function_exists('get_field')
    && function_exists('land76wp_service_hubs_merge_problem_item_images')) {
    $ns87_problem_items_raw = get_field('field_ns87_problem_items', $ns87_post_context, false);
    $ns87_problem_items = land76wp_service_hubs_merge_problem_item_images(
        $ns87_problem_items,
        $ns87_problem_items_raw
    );
}
$ns87_solution_title = function_exists('get_field') ? get_field('ns87_solution_title', $ns87_post_context) : '';
$ns87_solution_text = function_exists('get_field') ? get_field('ns87_solution_text', $ns87_post_context) : '';
$ns87_solution_points = function_exists('get_field') ? get_field('ns87_solution_points', $ns87_post_context) : array();
$ns87_prices_title = function_exists('get_field') ? get_field('ns87_prices_title', $ns87_post_context) : '';
$ns87_price_rows = function_exists('get_field') ? get_field('ns87_price_rows', $ns87_post_context) : array();
$ns87_estimate_title = function_exists('get_field') ? get_field('ns87_estimate_title', $ns87_post_context) : '';
$ns87_estimate_items = function_exists('get_field') ? get_field('ns87_estimate_items', $ns87_post_context) : array();
$ns87_estimate_total = function_exists('get_field') ? get_field('ns87_estimate_total', $ns87_post_context) : '';
$ns87_faq_title = function_exists('get_field') ? get_field('ns87_faq_title', $ns87_post_context) : '';
$ns87_faq_items = function_exists('get_field') ? get_field('ns87_faq_items', $ns87_post_context) : array();
$ns87_parent_hub = $land76_managed_service_hub_post && function_exists('land76wp_service_hub_for_post')
    ? land76wp_service_hub_for_post($ns87_post_context)
    : null;
$ns87_parent_hub_id = is_array($ns87_parent_hub) && isset($ns87_parent_hub['hub_post_id'])
    ? (int) $ns87_parent_hub['hub_post_id']
    : 0;
$ns87_parent_hub_url = is_array($ns87_parent_hub) && isset($ns87_parent_hub['canonical'])
    ? (string) $ns87_parent_hub['canonical']
    : '';
$ns87_parent_hub_title = $ns87_parent_hub_id ? get_the_title($ns87_parent_hub_id) : '';
$ns87_related_services = $land76_managed_service_hub_post && function_exists('get_field')
    ? get_field('blogseo_related_services', $ns87_post_context)
    : array();
if (!is_array($ns87_related_services)) {
    $ns87_related_services = array();
}

if (!function_exists('land76_newservice_selected_real_projects')) {
    function land76_newservice_selected_real_projects($post_id)
    {
        $selected_projects = function_exists('get_field') ? get_field('selected_real_projects', $post_id) : array();
        if (function_exists('land76wp_has_managed_service_hub_owner') && land76wp_has_managed_service_hub_owner($post_id)) {
            return is_array($selected_projects) ? $selected_projects : array();
        }

        if (!empty($selected_projects) && is_array($selected_projects)) {
            return $selected_projects;
        }

        $terms = get_the_category($post_id);
        if (empty($terms) || !function_exists('get_field')) {
            return array();
        }

        foreach ($terms as $term) {
            if (in_array((int) $term->term_id, array(72, 74), true)) {
                continue;
            }

            $category_projects = get_field('selected_works_posts', 'category_' . (int) $term->term_id);
            if (!empty($category_projects) && is_array($category_projects)) {
                return $category_projects;
            }
        }

        return array();
    }
}

if (!function_exists('land76_newservice_asset_url')) {
    function land76_newservice_asset_url($filename)
    {
        return home_url('/wp-content/uploads/seo-service-photos/' . ltrim($filename, '/'));
    }
}

if (!function_exists('land76_newservice_topic_key')) {
    function land76_newservice_topic_key($post_id)
    {
        $land76_managed_service_hub_post = hash_equals(
            'land76-service-hubs',
            (string) get_post_meta($post_id, '_land76_import_owner', true)
        );
        $explicit_topic_key = (string) get_post_meta($post_id, '_land76_topic_key', true);
        if ($explicit_topic_key !== '') {
            $registry = function_exists('land76wp_service_hub_registry') ? land76wp_service_hub_registry() : array();
            if (isset($registry[$explicit_topic_key]) && hash_equals($registry[$explicit_topic_key]['topic_key'], $explicit_topic_key)) {
                return $explicit_topic_key;
            }
            return '';
        }

        $categories = wp_get_post_categories($post_id);
        $map = array(
            87 => 'drenazh',
            88 => 'otmostka',
            89 => 'plitka',
            90 => 'osushenie',
            91 => 'livnevka',
            92 => 'avtopoliv',
        );

        foreach ($map as $category_id => $topic_key) {
            if (in_array((int) $category_id, $categories, true)) {
                return $topic_key;
            }
        }

        if (!$land76_managed_service_hub_post) { return 'drenazh'; }
        return '';
    }
}

if (!function_exists('land76_newservice_context_image')) {
    function land76_newservice_context_image($post_id, $context = '')
    {
        $land76_managed_service_hub_post = hash_equals(
            'land76-service-hubs',
            (string) get_post_meta($post_id, '_land76_import_owner', true)
        );
        if ($land76_managed_service_hub_post) {
            $image = land76_newservice_managed_presentation_image($post_id, 'context');
            return $image['url'];
        }

        $topic_key = land76_newservice_topic_key($post_id);
        $text = mb_strtolower(get_post_field('post_name', $post_id) . ' ' . get_the_title($post_id) . ' ' . $context);
        $rules = array(
            'drenazh' => array(
                '/цен|смет|стоим|cena/u' => 'cena-drenazha-uchastka.webp',
                '/высок|грунтов|grunt/u' => 'vysokie-gruntovye-vody.webp',
                '/глин|glin/u' => 'glinistaya-pochva.webp',
                '/дом|vokrug/u' => 'vokrug-doma.webp',
                '/глуб|glubin/u' => 'glubinnyy.webp',
                '/поверх|poverh/u' => 'poverhnostnyy.webp',
                '/6-сот|6-sotok/u' => '6-sotok.webp',
                '/10-сот|10-sotok/u' => '10-sotok.webp',
                '/уклон|uklon/u' => 's-uklonom.webp',
            ),
            'otmostka' => array(
                '/цен|смет|стоим|cena/u' => 'cena.webp',
                '/бетон|beton/u' => 'betonnaya-otmostka.webp',
                '/мягк|myag/u' => 'myagkaya-otmostka.webp',
                '/утепл|utepl/u' => 'uteplennaya-otmostka.webp',
                '/плит|plit/u' => 'otmostka-iz-plitki.webp',
                '/основан|podgotov/u' => 'podgotovka-osnovaniya.webp',
                '/вариант|tip|тип/u' => 'varianty.webp',
                '/залив|монтаж|montazh/u' => 'zalivka.webp',
                '/ремонт|просел|трещ|remont/u' => 'remont-staroy.webp',
            ),
            'plitka' => array(
                '/цен|смет|стоим|cena/u' => 'cena-ukladki-trotuarnoy-plitki.webp',
                '/основан|podgotov/u' => 'podgotovka-osnovaniya-pod-plitku.webp',
                '/дорож|dorozh/u' => 'sadovye-dorozhki-iz-plitki.webp',
                '/авто|парков/u' => 'ploshchadka-pod-avto-iz-plitki.webp',
                '/двор/u' => 'dvor-iz-trotuarnoy-plitki.webp',
                '/брусчат|bruschat/u' => 'ukladka-bruschatki.webp',
                '/бордюр|водоотвод/u' => 'bordyury-i-vodootvod-dlya-plitki.webp',
                '/ремонт/u' => 'remont-trotuarnoy-plitki.webp',
            ),
            'osushenie' => array(
                '/цен|смет|стоим|cena/u' => 'cena-osusheniya-uchastka.webp',
                '/дренаж|drenazh/u' => 'drenazh-dlya-osusheniya-uchastka.webp',
                '/грунтов|высок/u' => 'osushenie-pri-vysokih-gruntovyh-vodah.webp',
                '/болот|заболоч/u' => 'osushenie-zabolochennogo-uchastka.webp',
                '/дач/u' => 'osushenie-dachnogo-uchastka.webp',
                '/глин/u' => 'osushenie-glinistogo-uchastka.webp',
                '/вода|дожд/u' => 'voda-posle-dozhdya-na-uchastke.webp',
                '/проект|схем/u' => 'proektirovanie-sistemy-osusheniya.webp',
            ),
            'livnevka' => array(
                '/цен|смет|стоим|cena/u' => 'cena-livnevoy-kanalizatsii.webp',
                '/монтаж/u' => 'montazh-livnevoy-kanalizatsii.webp',
                '/дом|vokrug/u' => 'livnevka-vokrug-doma.webp',
                '/участ/u' => 'livnevka-na-uchastke.webp',
                '/дождеприем|лотк/u' => 'dozhdepriemniki-i-lotki.webp',
                '/линей/u' => 'lineynyy-vodootvod.webp',
                '/крыша|крыш/u' => 'otvod-vody-s-kryshi.webp',
                '/ремонт/u' => 'remont-livnevoy-kanalizatsii.webp',
            ),
            'avtopoliv' => array(
                '/цен|смет|стоим|cena/u' => 'cena-avtopoliva-na-uchastke.webp',
                '/монтаж/u' => 'montazh-avtopoliva.webp',
                '/газон/u' => 'avtopoliv-gazona.webp',
                '/капель/u' => 'kapelnyy-poliv.webp',
                '/сад|дерев/u' => 'avtopoliv-sada.webp',
                '/теплиц/u' => 'avtopoliv-teplitsy.webp',
                '/проект|схем/u' => 'proektirovanie-avtopoliva.webp',
                '/насос|емкост/u' => 'nasos-i-emkost-dlya-poliva.webp',
                '/обслуж|ремонт/u' => 'obsluzhivanie-avtopoliva.webp',
            ),
        );

        if (!isset($rules[$topic_key])) {
            return '';
        }
        foreach ($rules[$topic_key] as $pattern => $image) {
            if (preg_match($pattern, $text)) {
                return land76_newservice_asset_url($image);
            }
        }

        $defaults = array(
            'drenazh' => 'vysokie-gruntovye-vody.webp',
            'otmostka' => 'betonnaya-otmostka.webp',
            'plitka' => 'sadovye-dorozhki-iz-plitki.webp',
            'osushenie' => 'otvod-vody-s-uchastka.webp',
            'livnevka' => 'livnevka-na-uchastke.webp',
            'avtopoliv' => 'montazh-avtopoliva.webp',
        );

        return land76_newservice_asset_url($defaults[$topic_key]);
    }
}

if (empty($ns87_problem_items) || !is_array($ns87_problem_items)) {
    $ns87_problem_items = array(
        array(
            'title' => 'Есть задача на участке',
            'text' => 'Нужно подобрать рабочее решение под конкретный участок, рельеф, покрытия и сценарий использования.',
            'image' => land76_newservice_context_image(get_the_ID(), 'задача на участке'),
        ),
        array(
            'title' => 'Нужна понятная смета',
            'text' => 'Важно заранее понимать состав работ, материалы, сроки и итоговую стоимость без лишних позиций.',
            'image' => land76_newservice_context_image(get_the_ID(), 'стоимость смета'),
        ),
        array(
            'title' => 'Важен аккуратный монтаж',
            'text' => 'Работы должны вписаться в существующее благоустройство и не создавать новых проблем на участке.',
            'image' => land76_newservice_context_image(get_the_ID(), 'монтаж'),
        ),
    );
}

if (empty($ns87_solution_points) || !is_array($ns87_solution_points)) {
    $ns87_solution_points = array(
        array('title' => 'Осмотр', 'text' => 'Смотрим участок, ограничения, доступы, покрытия и существующие инженерные решения.'),
        array('title' => 'Схема', 'text' => 'Подбираем рабочую схему под задачу, бюджет и дальнейшую эксплуатацию.'),
        array('title' => 'Монтаж', 'text' => 'Выполняем работы по согласованной смете и понятному составу материалов.'),
        array('title' => 'Запуск', 'text' => 'Проверяем результат, объясняем обслуживание и сдаем работу заказчику.'),
    );
}

if (empty($ns87_price_rows) || !is_array($ns87_price_rows)) {
    $ns87_price_rows = array(
        array('service' => 'Осмотр и схема', 'price' => 'по расчету', 'term' => '1 день'),
        array('service' => 'Материалы и оборудование', 'price' => 'по расчету', 'term' => 'по смете'),
        array('service' => 'Монтажные работы', 'price' => 'по расчету', 'term' => 'по объему'),
    );
}

if (empty($ns87_estimate_items) || !is_array($ns87_estimate_items)) {
    $ns87_estimate_items = array(
        array('item' => 'Осмотр участка и уточнение задачи - по расчету'),
        array('item' => 'Подбор материалов и оборудования - по расчету'),
        array('item' => 'Монтажные работы - по расчету'),
        array('item' => 'Проверка и сдача результата - по расчету'),
    );
}

if (empty($ns87_faq_items) || !is_array($ns87_faq_items)) {
    $ns87_faq_items = array(
        array(
            'question' => 'Можно рассчитать стоимость заранее?',
            'answer' => 'Предварительно да. Точная смета зависит от осмотра участка, объема работ, материалов и условий монтажа.',
        ),
        array(
            'question' => 'Можно выполнить работы поэтапно?',
            'answer' => 'Да, если это не ломает техническую логику решения. Поэтапность обсуждаем при подготовке схемы.',
        ),
    );
}
$ns87_breadcrumb_title = $ns87_hero_title ? $ns87_hero_title : get_the_title();
?>

<?php if ($land76_managed_service_hub_post) : ?>
<div class="managed-service-child">
<?php endif; ?>

<!-- 1. Hero блок -->
<section class="hero">
  <div class="hero__scene" id="scene">
    <div class="hero__bg" data-depth="0.4"<?php if ($ns87_render_hero_image) : ?> style="background-image: url('<?php echo esc_url($ns87_hero_image_url); ?>');"<?php endif; ?>></div>
  </div>
  <div class="hero__content wrapper">
    <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php echo esc_html($ns87_hero_title ? $ns87_hero_title : get_the_title()); ?>
    </h1>
    <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($ns87_hero_subtitle ? $ns87_hero_subtitle : 'Выполняем работы под ключ: осмотр, схема, смета, монтаж и проверка результата.'); ?></p>
    <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
      <a href="<?php echo esc_url($ns87_hero_btn_primary_url ? $ns87_hero_btn_primary_url : '#calc'); ?>" class="hero__btn"><?php echo esc_html($ns87_hero_btn_primary_text ? $ns87_hero_btn_primary_text : 'Рассчитать стоимость'); ?></a>
      <a href="<?php echo esc_url($ns87_hero_btn_secondary_url ? $ns87_hero_btn_secondary_url : '#consultation'); ?>" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;"><?php echo esc_html($ns87_hero_btn_secondary_text ? $ns87_hero_btn_secondary_text : 'Получить консультацию'); ?></a>
    </div>
    <div class="hero__breadcramps"><a class="hero__home" href="<?php echo esc_url(get_home_url('/')); ?>">Компания «Эксперты»</a>
      <?php if ($ns87_parent_hub_url !== '' && $ns87_parent_hub_title !== '') : ?>
        <span aria-hidden="true"> | </span><a href="<?php echo esc_url($ns87_parent_hub_url); ?>"><?php echo esc_html($ns87_parent_hub_title); ?></a>
      <?php endif; ?>
      <span aria-hidden="true"> | </span><span class="hero__active-page"><?php echo esc_html($ns87_breadcrumb_title); ?></span></div>
  </div>

</section>

<!-- 2. Проблема -->
<section class="service-v2__section managed-service-child__section services wrapper howWorkCustom portfolio">
  <div class="problem-block" data-aos="fade-up" data-aos-duration="600">
    <h3><?php echo esc_html($ns87_problem_title ? $ns87_problem_title : 'Какая задача решается'); ?></h3>
    <p><?php echo esc_html($ns87_problem_text ? $ns87_problem_text : 'Подбираем решение по месту, чтобы работы были понятными по составу, стоимости и результату.'); ?></p>

    <?php $ns87_rendered_problem_image_urls = array(); ?>
    <?php foreach ($ns87_problem_items as $index => $ns87_problem_item) : ?>
    <?php
      $ns87_problem_img = '';
      $ns87_problem_img_alt = !empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : 'Проблема';
      if (!$land76_managed_service_hub_post && !empty($ns87_problem_item['image'])) {
          if (is_array($ns87_problem_item['image']) && !empty($ns87_problem_item['image']['url'])) {
              $ns87_problem_img = $ns87_problem_item['image']['url'];
              if (!empty($ns87_problem_item['image']['alt'])) {
                  $ns87_problem_img_alt = $ns87_problem_item['image']['alt'];
              }
          } elseif (is_numeric($ns87_problem_item['image'])) {
              $ns87_problem_img = wp_get_attachment_image_url((int) $ns87_problem_item['image'], 'full');
          } elseif (is_string($ns87_problem_item['image'])) {
              $ns87_problem_img = $ns87_problem_item['image'];
          }
      }
      if (!$land76_managed_service_hub_post && empty($ns87_problem_img)) {
          $ns87_problem_img = land76_newservice_context_image(get_the_ID(), !empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : '');
      }
      if (!$land76_managed_service_hub_post && $ns87_problem_img !== '' && in_array($ns87_problem_img, $ns87_rendered_problem_image_urls, true)) {
          $ns87_problem_img = '';
      }
      if (!$land76_managed_service_hub_post && $ns87_problem_img !== '') {
          $ns87_rendered_problem_image_urls[] = $ns87_problem_img;
      }
    ?>
    <div class="problem-item" data-aos="fade-up" data-aos-duration="<?php echo esc_attr(700 + ($index * 100)); ?>">
      <?php if ($land76_managed_service_hub_post) : ?>
        <span class="problem-item__number" aria-hidden="true"><?php echo esc_html(str_pad((string) ($index + 1), 2, '0', STR_PAD_LEFT)); ?></span>
      <?php elseif ($ns87_problem_img !== '') : ?>
        <img src="<?php echo esc_url($ns87_problem_img); ?>" alt="<?php echo esc_attr($ns87_problem_img_alt); ?>" loading="lazy" decoding="async">
      <?php endif; ?>
      <div>
        <h4><?php echo esc_html(!empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : ''); ?></h4>
        <p><?php echo esc_html(!empty($ns87_problem_item['text']) ? $ns87_problem_item['text'] : ''); ?></p>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
</section>

<!-- 3. Решение -->
<section class="service-v2__section managed-service-child__section services wrapper">
  <div class="solution-block" data-aos="fade-up" data-aos-duration="600">
    <h3><?php echo esc_html($ns87_solution_title ? $ns87_solution_title : 'Как мы решаем задачу'); ?></h3>
    <p><?php echo esc_html($ns87_solution_text ? $ns87_solution_text : 'Сначала разбираем условия участка, затем согласуем схему, смету и выполняем монтаж с проверкой результата.'); ?></p>

    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px;">
      <?php foreach ($ns87_solution_points as $index => $ns87_solution_point) : ?>
      <div data-aos="<?php echo esc_attr($index % 2 === 0 ? 'fade-right' : 'fade-left'); ?>" data-aos-duration="<?php echo esc_attr(700 + ($index * 100)); ?>">
        <h4 style="color: #0a9215; font-family: 
'
Poiret One
'
        , cursive; font-size: 22px; margin-bottom: 15px;"><?php echo esc_html(!empty($ns87_solution_point['title']) ? $ns87_solution_point['title'] : ''); ?></h4>
        <p><?php echo esc_html(!empty($ns87_solution_point['text']) ? $ns87_solution_point['text'] : ''); ?></p>
      </div>
      <?php endforeach; ?>
    </div>
  </div>
</section>

<!-- 4. SEO текст страницы -->
<section class="service-v2__section managed-service-child__section services wrapper">
  <div class="seo-text" style="line-height: 1.6; margin-bottom: 40px;">
    <?php if ($land76_managed_service_hub_post && $ns87_render_main_image) : ?>
      <figure class="service-main-image">
        <img src="<?php echo esc_url($ns87_main_image_url); ?>" alt="<?php echo esc_attr($ns87_main_image_alt); ?>">
      </figure>
    <?php endif; ?>
    <?php the_content(); ?>
    <?php if ($land76_managed_service_hub_post && $ns87_render_context_image) : ?>
      <figure class="service-context-image">
        <img src="<?php echo esc_url($ns87_context_image_url); ?>" alt="<?php echo esc_attr($ns87_context_image_alt); ?>" loading="lazy" decoding="async">
      </figure>
    <?php endif; ?>
  </div>
</section>
<?php $ns87_selected_projects = land76_newservice_selected_real_projects(get_the_ID()); ?>
<?php if (!empty($ns87_selected_projects)) : ?>
<!-- 5. Подтверждённые кейсы -->
<section class="service-v2__section managed-service-child__section services wrapper casesCustom">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 40px;">Примеры наших работ</h2>
  <div class="services__cards columns3">
    <?php
      foreach ($ns87_selected_projects as $post_id) {
        $post_id = is_object($post_id) && !empty($post_id->ID) ? (int) $post_id->ID : (int) $post_id;
        $post = get_post($post_id);
        if (!$post) {
          continue;
        }
        setup_postdata($post);
        if ($land76_managed_service_hub_post) {
          $project_media = land76_newservice_unique_project_image($post_id, $ns87_rendered_image_identities, 'medium');
          $project_image = $project_media['url'];
        } else {
          $project_image = function_exists('land76_get_card_image_url')
            ? land76_get_card_image_url($post_id, 'medium', !$land76_managed_service_hub_post)
            : get_the_post_thumbnail_url($post_id, 'medium');
          if (!$project_image) {
            $project_image = land76_newservice_context_image($ns87_post_context, 'пример работ');
          }
        }
        $project_title = function_exists('get_field') ? get_field('cs87_hero_title', $post_id) : '';
        if (!$project_title) {
          $project_title = get_the_title($post_id);
        }
        $project_excerpt = function_exists('get_field') ? get_field('cs87_hero_subtitle', $post_id) : '';
        if (!$project_excerpt) {
          $project_excerpt = get_the_excerpt($post_id);
        }
        if (!$project_excerpt) {
          $project_excerpt = wp_trim_words(get_post_field('post_content', $post_id), 18);
        }
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <?php if ($project_image) : ?>
            <div class="service__img-wrap">
              <img class="service__img" src="<?php echo esc_url($project_image); ?>"
                alt="<?php echo esc_attr($project_title); ?>" loading="lazy" decoding="async">
            </div>
          <?php endif; ?>
          <div class="service__text-wrap">
            <h3 class="service__title"><?php echo esc_html($project_title); ?></h3>
            <p><?php echo esc_html(wp_trim_words($project_excerpt, 22)); ?></p>
            <p>
              <strong><?php echo get_field('price', $post_id) ? 'от ' . esc_html(get_field('price', $post_id)) : 'Цена по запросу'; ?></strong>
            </p>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php echo get_permalink($post_id); ?>">Подробнее</a>
            </div>
          </div>
        </div>
      <?php
      }
      wp_reset_postdata();
    ?>
  </div>
</section>
<?php endif; ?>

<?php if ($land76_managed_service_hub_post && !empty($ns87_related_services)) : ?>
<section class="service-v2__section managed-service-child__section services wrapper service-related-services">
  <h2>Другие услуги направления</h2>
  <div class="services__cards columns3">
    <?php foreach ($ns87_related_services as $ns87_related_service) : ?>
      <?php
      $ns87_related_service_id = is_object($ns87_related_service) && !empty($ns87_related_service->ID)
          ? (int) $ns87_related_service->ID
          : (int) $ns87_related_service;
      if (!$ns87_related_service_id || $ns87_related_service_id === (int) get_the_ID()) {
          continue;
      }
      $ns87_related_service_post = get_post($ns87_related_service_id);
      $ns87_related_service_hub = $ns87_related_service_post instanceof WP_Post
          && function_exists('land76wp_service_hub_for_post')
          ? land76wp_service_hub_for_post($ns87_related_service_id)
          : null;
      if (!$ns87_related_service_post instanceof WP_Post
          || $ns87_related_service_post->post_status !== 'publish'
          || !is_array($ns87_related_service_hub)
          || !is_array($ns87_parent_hub)
          || !hash_equals((string) $ns87_parent_hub['service_id'], (string) $ns87_related_service_hub['service_id'])) {
          continue;
      }
      $ns87_related_service_card = land76_newservice_related_card_image($ns87_related_service_id, $ns87_rendered_image_identities, 'medium_large');
      ?>
      <article class="service">
        <?php if ($ns87_related_service_card['url'] !== '' && $ns87_related_service_card['alt'] !== '') : ?>
          <div class="service__img-wrap service-related-card-image">
            <img class="service__img" src="<?php echo esc_url($ns87_related_service_card['url']); ?>" alt="<?php echo esc_attr($ns87_related_service_card['alt']); ?>" loading="lazy" decoding="async">
          </div>
        <?php endif; ?>
        <div class="service__text-wrap">
          <h3 class="service__title"><?php echo esc_html(get_the_title($ns87_related_service_id)); ?></h3>
          <div class="service__link-wrap">
            <a class="service__link" href="<?php echo esc_url(get_permalink($ns87_related_service_id)); ?>">Подробнее</a>
          </div>
        </div>
      </article>
    <?php endforeach; ?>
  </div>
</section>
<?php endif; ?>

<?php
$ns87_related_article_ids = get_post_meta(get_the_ID(), '_land76_related_article_ids', true);
if (!is_array($ns87_related_article_ids)) {
    $ns87_related_article_ids = array();
}
?>
<?php if ($land76_managed_service_hub_post && !empty($ns87_related_article_ids)) : ?>
<section class="service-v2__section managed-service-child__section services wrapper service-related-articles">
  <h2>Материалы по теме</h2>
  <div class="services__cards columns3">
    <?php foreach ($ns87_related_article_ids as $ns87_related_article_id) : ?>
      <?php
      $ns87_related_article = get_post((int) $ns87_related_article_id);
      $ns87_related_article_page_key = $ns87_related_article instanceof WP_Post
          ? (string) get_post_meta($ns87_related_article->ID, '_land76_page_key', true)
          : '';
      $ns87_related_article_is_managed = $ns87_related_article instanceof WP_Post
          && function_exists('land76wp_is_managed_service_hub_post')
          && land76wp_is_managed_service_hub_post($ns87_related_article->ID);
      if (!$ns87_related_article instanceof WP_Post
          || $ns87_related_article->post_status !== 'publish'
          || !$ns87_related_article_is_managed
          || strpos($ns87_related_article_page_key, '-ARTICLE-') === false) {
          continue;
      }
      $ns87_related_article_card = land76_newservice_related_card_image($ns87_related_article->ID, $ns87_rendered_image_identities, 'medium_large');
      $ns87_related_article_card_url = $ns87_related_article_card['url'];
      $ns87_related_article_card_alt = $ns87_related_article_card['alt'];
      ?>
      <article class="service">
        <?php if ($ns87_related_article_card_url !== '' && $ns87_related_article_card_alt !== '') : ?>
          <div class="service__img-wrap service-related-card-image">
            <img class="service__img" src="<?php echo esc_url($ns87_related_article_card_url); ?>" alt="<?php echo esc_attr($ns87_related_article_card_alt); ?>" loading="lazy" decoding="async">
          </div>
        <?php endif; ?>
        <div class="service__text-wrap">
          <h3 class="service__title"><?php echo esc_html(get_the_title($ns87_related_article)); ?></h3>
          <div class="service__link-wrap">
            <a class="service__link" href="<?php echo esc_url(get_permalink($ns87_related_article)); ?>">Читать</a>
          </div>
        </div>
      </article>
    <?php endforeach; ?>
  </div>
</section>
<?php endif; ?>

<!-- 6. Цена -->
<section class="service-v2__section managed-service-child__section services wrapper service-price-section">
  <?php if ($land76_managed_service_hub_post) : ?>
  <div class="managed-service-child__price-surface">
  <?php endif; ?>
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 40px;"><?php echo esc_html($ns87_prices_title ? $ns87_prices_title : 'Стоимость услуги'); ?></h2>

  <?php if ($land76_managed_service_hub_post) : ?>
    <?php if ($ns87_estimate_total) : ?>
      <p class="service-price-factors__lead"><?php echo esc_html($ns87_estimate_total); ?></p>
    <?php endif; ?>
    <div class="service-price-factors">
      <?php foreach ($ns87_price_rows as $ns87_price_row) : ?>
        <?php if (!empty($ns87_price_row['service']) && !empty($ns87_price_row['term'])) : ?>
          <article class="service-price-factor">
            <h3><?php echo esc_html($ns87_price_row['service']); ?></h3>
            <p><?php echo esc_html($ns87_price_row['term']); ?></p>
          </article>
        <?php endif; ?>
      <?php endforeach; ?>
    </div>
  <?php else : ?>
  <div style="overflow-x: auto; margin-bottom: 30px;">
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #fff;">
      <thead>
        <tr style="background: #f5f5f5;">
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 600; font-size: 16px;">Работа</th>
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 600; font-size: 16px;">Стоимость</th>
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 600; font-size: 16px;">Примечание</th>
        </tr>
      </thead>
      <tbody>
        <?php foreach ($ns87_price_rows as $ns87_price_row) : ?>
        <tr>
          <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($ns87_price_row['service']) ? $ns87_price_row['service'] : ''); ?></td>
          <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($ns87_price_row['price']) ? $ns87_price_row['price'] : ''); ?></td>
          <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($ns87_price_row['term']) ? $ns87_price_row['term'] : ''); ?></td>
        </tr>
        <?php endforeach; ?>
      </tbody>
    </table>
  </div>

  <div style="background: #f9f9f9; padding: 30px; border-radius: 10px; margin-bottom: 30px;">
    <h3 style="margin-bottom: 20px; font-family: 
'
Poiret One
'
, cursive; font-size: 24px; color: #333;"><?php echo esc_html($ns87_estimate_title ? $ns87_estimate_title : 'Пример расчета'); ?></h3>
    <ul class="estimate-list">
      <?php foreach ($ns87_estimate_items as $ns87_estimate_item) : ?>
      <li><?php echo esc_html(!empty($ns87_estimate_item['item']) ? $ns87_estimate_item['item'] : ''); ?></li>
      <?php endforeach; ?>
      <li><strong><?php echo esc_html($ns87_estimate_total ? $ns87_estimate_total : 'Итого: по расчету'); ?></strong></li>
    </ul>
  </div>
  <?php endif; ?>
  <?php if ($land76_managed_service_hub_post) : ?>
  </div>
  <?php endif; ?>
</section>

<!-- 8. Мини FAQ -->
<section class="service-v2__section managed-service-child__section services wrapper service-faq-section">
  <h2 class="service-faq-title"><?php echo esc_html($ns87_faq_title ? $ns87_faq_title : 'Ответы на вопросы'); ?></h2>

  <div class="service-faq-list">
    <?php foreach ($ns87_faq_items as $ns87_faq_item) : ?>
    <?php if ($land76_managed_service_hub_post) : ?>
    <details class="service-v2__faq-item service-faq-item">
      <summary><?php echo esc_html(!empty($ns87_faq_item['question']) ? $ns87_faq_item['question'] : ''); ?></summary>
      <p><?php echo esc_html(!empty($ns87_faq_item['answer']) ? $ns87_faq_item['answer'] : ''); ?></p>
    </details>
    <?php else : ?>
    <div class="service-faq-item">
      <div class="service-faq-question" onclick="var answer = this.nextElementSibling; answer.style.display = answer.style.display === 'block' ? 'none' : 'block'; this.querySelector('.faq-icon').textContent = this.querySelector('.faq-icon').textContent === '+' ? '-' : '+';">
        <h3 class="faq-toggle" style="margin: 0;">
          <span class="faq-question-text"><?php echo esc_html(!empty($ns87_faq_item['question']) ? $ns87_faq_item['question'] : ''); ?></span>
        </h3>
        <span class="faq-icon">+</span>
      </div>
      <div class="faq-answer" style="display: none;">
        <p><?php echo esc_html(!empty($ns87_faq_item['answer']) ? $ns87_faq_item['answer'] : ''); ?></p>
      </div>
    </div>
    <?php endif; ?>
    <?php endforeach; ?>
  </div>
</section>
<!-- 10. CTA -->
<?php if ($land76_managed_service_hub_post) : ?>
<section class="service-v2 service-v2__section managed-service-child__section service-v2__cta wrapper" id="calc">
  <div class="service-v2__cta-inner">
    <div class="managed-service-child__cta-copy">
      <h2>Получите расчёт по вашему участку</h2>
      <p>Пришлите фото, план или краткое описание задачи. Предварительно оценим состав работ, а точную смету подготовим после уточнения условий объекта.</p>
    </div>
    <div class="formWrapper service-v2__form-wrapper">
      <form class="form service-v2__form" method="post" action="<?php echo esc_url(home_url('/server.php')); ?>">
        <?php land76_render_form_security_fields('managed-service-cta-v4'); ?>
        <label class="form__label">
          <span>Ваше имя</span>
          <input class="form__input" type="text" name="name" autocomplete="name" required>
        </label>
        <label class="form__label">
          <span>Телефон</span>
          <input class="form__input" type="tel" name="phone" autocomplete="tel" inputmode="tel" required>
        </label>
        <label class="service-v2__consent">
          <input type="checkbox" name="consent" value="1" required>
          <span>Соглашаюсь с <a href="<?php echo esc_url(home_url('/privacy/')); ?>">политикой конфиденциальности</a> и <a href="<?php echo esc_url(home_url('/consent/')); ?>">обработкой персональных данных</a>.</span>
        </label>
        <button class="service-v2__button form__btn" type="submit">Получить расчёт</button>
      </form>
      <div class="ajaxMessage">
        <div class="ajaxMessage__success">
          <div class="ajaxMessage__title"><p>Спасибо!</p><p>Ваша заявка принята</p></div>
          <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время</div>
        </div>
        <div class="ajaxMessage__error">
          <div class="ajaxMessage__title">Ошибка при отправке!</div>
          <div class="ajaxMessage__text">Попробуйте позднее</div>
        </div>
        <button class="ajaxMessage__btn btn closeModal" type="button">Закрыть</button>
      </div>
    </div>
  </div>
</section>
</div>
<?php else : ?>
<section class="advantages wrapper">
  <div style="text-align: center; background: #f9f9f9; padding: 40px; border-radius: 10px;">
    <h2 style="font-weight: 600; margin-bottom: 35px;">Получите расчёт по вашему участку</h2>
    <p style="margin-bottom: 30px;">Пришлите фото, план или краткое описание задачи. Предварительно оценим состав работ, а точную смету подготовим после уточнения условий объекта.</p>
    <form class="cta-form form" id="calc" method="post" action="<?php echo esc_url(home_url('/server.php')); ?>" style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
      <?php land76_render_form_security_fields('managed-service-cta-v3'); ?>
      <input type="text" name="name" placeholder="Ваше имя" required
        style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
      <input type="tel" name="phone" placeholder="Ваш телефон" required
        style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
      <div class="formConsent" style="flex-basis: 100%; text-align: center; margin-top: 10px;"><label class="formConsent__container"><input class="formConsent__input" type="checkbox" name="consent" value="1" required="required" /><span class="formConsent__checkbox"><svg class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px"><path d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928C170.827,363.533,162.165,366.839,153.504,366.839z" fill="#B22917"></path></svg></span></label><span class="formConsent__text" style="font-size: 12px;">Я согласен с <a href="<?php echo esc_url(home_url('/privacy/')); ?>">политикой конфиденциальности</a> и <a href="<?php echo esc_url(home_url('/consent/')); ?>">обработкой персональных данных</a></span></div>
      <button type="submit" class="btn--primary-custom">Получить расчет</button>
    </form>
    <div class="ajaxMessage" style="display:none;">
      <div class="ajaxMessage__success">
        <div class="ajaxMessage__title"><p>Спасибо!</p><p>Ваша заявка принята</p></div>
        <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время</div>
      </div>
      <div class="ajaxMessage__error">
        <div class="ajaxMessage__title">Ошибка при отправке!</div>
        <div class="ajaxMessage__text">Попробуйте позднее</div>
      </div>
      <button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
    </div>
  </div>
</section>
<?php endif; ?>
