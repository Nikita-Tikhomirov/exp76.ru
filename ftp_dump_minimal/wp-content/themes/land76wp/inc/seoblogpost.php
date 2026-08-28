<?php
if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('land76_blogseo_field')) {
    function land76_blogseo_field($name, $default = '')
    {
        if (!function_exists('get_field')) {
            return $default;
        }

        $value = get_field($name, get_the_ID());
        return $value !== null && $value !== false && $value !== '' ? $value : $default;
    }
}

if (!function_exists('land76_blogseo_image_url')) {
    function land76_blogseo_image_url($image, $fallback = '')
    {
        if (is_array($image) && !empty($image['url'])) {
            return $image['url'];
        }

        if (is_numeric($image)) {
            $url = wp_get_attachment_image_url((int) $image, 'large');
            return $url ? $url : $fallback;
        }

        if (is_string($image) && $image !== '') {
            return $image;
        }

        return $fallback;
    }
}

if (!function_exists('land76_blogseo_asset_url')) {
    function land76_blogseo_asset_url($filename)
    {
        return home_url('/wp-content/uploads/seo-service-photos/' . ltrim($filename, '/'));
    }
}

if (!function_exists('land76_blogseo_post_topics')) {
    function land76_blogseo_post_topics($post_id)
    {
        $explicit_topic_key = (string) get_post_meta($post_id, '_land76_topic_key', true);
        if ($explicit_topic_key !== '') {
            $registry = function_exists('land76wp_service_hub_registry') ? land76wp_service_hub_registry() : array();
            if (isset($registry[$explicit_topic_key]) && hash_equals($registry[$explicit_topic_key]['topic_key'], $explicit_topic_key)) {
                return array($explicit_topic_key);
            }
            return array();
        }

        $post_categories = wp_get_post_categories($post_id);
        $topics = array(
            'drenazh' => 87,
            'otmostka' => 88,
            'plitka' => 89,
            'osushenie' => 90,
            'livnevka' => 91,
            'avtopoliv' => 92,
        );

        foreach ($topics as $topic_key => $category_id) {
            if (in_array((int) $category_id, $post_categories, true)) {
                return array($topic_key);
            }
        }

        $text = mb_strtolower(get_post_field('post_name', $post_id) . ' ' . get_the_title($post_id));
        if (preg_match('/дренаж|грунтов|глинист|уклон|труб/u', $text)) {
            return array('drenazh');
        }
        if (preg_match('/осуш|болот|сыр|низин|вода/u', $text)) {
            return array('osushenie');
        }
        if (preg_match('/ливнев|дождеприем|лотк|водосток/u', $text)) {
            return array('livnevka');
        }
        if (preg_match('/отмост/u', $text)) {
            return array('otmostka');
        }
        if (preg_match('/плитк|мощен|брусчат|дорожк/u', $text)) {
            return array('plitka');
        }
        if (preg_match('/автополив|полив|спринклер|капельн/u', $text)) {
            return array('avtopoliv');
        }

        return array('drenazh');
    }
}

if (!function_exists('land76_blogseo_topic_image_by_text')) {
    function land76_blogseo_topic_image_by_text($post_id, $post_topics)
    {
        $text = mb_strtolower(get_post_field('post_name', $post_id) . ' ' . get_the_title($post_id));
        $topic_key = !empty($post_topics[0]) ? $post_topics[0] : 'drenazh';
        $topic_rules = array(
            'drenazh' => array(
                '/труб|trub/u' => 'glubinnyy.webp',
                '/схем|план|shema|plan/u' => 's-uklonom.webp',
                '/своими|svoimi|rukami/u' => 'glubinnyy.webp',
                '/высок|грунтов|gruntov|vysok/u' => 'vysokie-gruntovye-vody.webp',
                '/глин|glin/u' => 'glinistaya-pochva.webp',
                '/поверх|poverh/u' => 'poverhnostnyy.webp',
                '/глуб|glubin/u' => 'glubinnyy.webp',
                '/уклон|uklon/u' => 's-uklonom.webp',
                '/6-sotok|6-сот/u' => '6-sotok.webp',
                '/10-sotok|10-сот/u' => '10-sotok.webp',
            ),
            'osushenie' => array(
                '/болот|заболоч|bolot/u' => 'osushenie-zabolochennogo-uchastka.webp',
                '/грязн|луж|после-дожд|posle-dozhd|gryaz/u' => 'voda-posle-dozhdya-na-uchastke.webp',
                '/грунтов|высок|gruntov|vysok/u' => 'osushenie-pri-vysokih-gruntovyh-vodah.webp',
                '/глин|glin/u' => 'osushenie-glinistogo-uchastka.webp',
                '/дренаж|drenazh/u' => 'drenazh-dlya-osusheniya-uchastka.webp',
                '/дач|dach/u' => 'osushenie-dachnogo-uchastka.webp',
            ),
            'livnevka' => array(
                '/дождеприем|dozhdepriem/u' => 'dozhdepriemniki-i-lotki.webp',
                '/линей|lineyn/u' => 'lineynyy-vodootvod.webp',
                '/крыш|krysh/u' => 'otvod-vody-s-kryshi.webp',
                '/ремонт|remont/u' => 'remont-livnevoy-kanalizatsii.webp',
                '/дом|vokrug/u' => 'livnevka-vokrug-doma.webp',
                '/ливнев|livnev/u' => 'livnevka-na-uchastke.webp',
            ),
            'otmostka' => array(
                '/треш|tresh/u' => 'remont-staroy.webp',
                '/просел|prosel/u' => 'podgotovka-osnovaniya.webp',
                '/мягк|myag/u' => 'myagkaya-otmostka.webp',
                '/бетон|beton/u' => 'betonnaya-otmostka.webp',
                '/утепл|utepl/u' => 'uteplennaya-otmostka.webp',
                '/плит|plit/u' => 'otmostka-iz-plitki.webp',
                '/залив|montazh|монтаж/u' => 'zalivka.webp',
            ),
            'plitka' => array(
                '/брусчат|bruschat/u' => 'ukladka-bruschatki.webp',
                '/дорож|dorozh/u' => 'sadovye-dorozhki-iz-plitki.webp',
                '/авто|парков|ploshch/u' => 'ploshchadka-pod-avto-iz-plitki.webp',
                '/бордюр|водоотвод|bordyur/u' => 'bordyury-i-vodootvod-dlya-plitki.webp',
                '/ремонт|remont/u' => 'remont-trotuarnoy-plitki.webp',
                '/основан|podgotov/u' => 'podgotovka-osnovaniya-pod-plitku.webp',
            ),
            'avtopoliv' => array(
                '/капель|kapeln/u' => 'kapelnyy-poliv.webp',
                '/теплиц|teplits/u' => 'avtopoliv-teplitsy.webp',
                '/газон|gazon/u' => 'avtopoliv-gazona.webp',
                '/сад|дерев|derev|sada/u' => 'avtopoliv-sada.webp',
                '/насос|емкост|оборуд|nasos/u' => 'nasos-i-emkost-dlya-poliva.webp',
                '/не работает|ремонт|обслуж|remont/u' => 'obsluzhivanie-avtopoliva.webp',
                '/схем|проект|plan|shema/u' => 'proektirovanie-avtopoliva.webp',
                '/своими|svoimi|rukami/u' => 'montazh-avtopoliva.webp',
                '/автополив|poliv/u' => 'montazh-avtopoliva.webp',
            ),
        );

        if (!empty($topic_rules[$topic_key])) {
            foreach ($topic_rules[$topic_key] as $pattern => $image) {
                if (preg_match($pattern, $text)) {
                    return $image;
                }
            }
        }

        $topic_images = array(
            'drenazh' => array('vysokie-gruntovye-vody.webp', 'glinistaya-pochva.webp', 'glubinnyy.webp', 'poverhnostnyy.webp', 's-uklonom.webp', 'vokrug-doma.webp'),
            'osushenie' => array('cena-osusheniya-uchastka.webp', 'osushenie-zabolochennogo-uchastka.webp', 'voda-posle-dozhdya-na-uchastke.webp', 'otvod-vody-s-uchastka.webp', 'osushenie-glinistogo-uchastka.webp'),
            'livnevka' => array('montazh-livnevoy-kanalizatsii.webp', 'livnevka-na-uchastke.webp', 'livnevka-vokrug-doma.webp', 'dozhdepriemniki-i-lotki.webp', 'lineynyy-vodootvod.webp'),
            'otmostka' => array('betonnaya-otmostka.webp', 'myagkaya-otmostka.webp', 'uteplennaya-otmostka.webp', 'otmostka-iz-plitki.webp', 'remont-staroy.webp', 'podgotovka-osnovaniya.webp'),
            'plitka' => array('sadovye-dorozhki-iz-plitki.webp', 'ploshchadka-pod-avto-iz-plitki.webp', 'ukladka-bruschatki.webp', 'bordyury-i-vodootvod-dlya-plitki.webp', 'remont-trotuarnoy-plitki.webp'),
            'avtopoliv' => array('avtopoliv-gazona.webp', 'montazh-avtopoliva.webp', 'kapelnyy-poliv.webp', 'avtopoliv-sada.webp', 'avtopoliv-teplitsy.webp', 'nasos-i-emkost-dlya-poliva.webp'),
        );
        $pool = !empty($topic_images[$topic_key]) ? $topic_images[$topic_key] : $topic_images['drenazh'];
        $index = abs(crc32((string) get_post_field('post_name', $post_id))) % count($pool);

        return $pool[$index];
    }
}

if (!function_exists('land76_blogseo_default_image_alt')) {
    function land76_blogseo_default_image_alt($post_id, $post_topics)
    {
        $labels = array(
            'drenazh' => 'Дренаж участка',
            'osushenie' => 'Осушение участка',
            'livnevka' => 'Ливневая канализация',
            'otmostka' => 'Отмостка вокруг дома',
            'plitka' => 'Укладка тротуарной плитки',
            'avtopoliv' => 'Автополив на участке',
        );
        $topic_key = !empty($post_topics[0]) ? $post_topics[0] : 'drenazh';
        $label = isset($labels[$topic_key]) ? $labels[$topic_key] : 'Благоустройство участка';

        return $label . ': ' . get_the_title($post_id);
    }
}

$blogseo_title = land76_blogseo_field('blogseo_hero_title', get_the_title());
$blogseo_subtitle = land76_blogseo_field('blogseo_hero_subtitle', get_the_excerpt());
$blogseo_lead = land76_blogseo_field('blogseo_lead', get_the_excerpt());
$blogseo_sections = land76_blogseo_field('blogseo_sections', array());
$blogseo_main_image = land76_blogseo_field('blogseo_main_image', '');
$blogseo_main_image_url = land76_blogseo_image_url($blogseo_main_image, land76_blogseo_field('blogseo_main_image_url', ''));
$blogseo_main_image_alt = land76_blogseo_field('blogseo_main_image_alt', $blogseo_title);
$blogseo_topics = land76_blogseo_post_topics(get_the_ID());
$land76_managed_service_hub_post = hash_equals(
    'land76-service-hubs',
    (string) get_post_meta(get_the_ID(), '_land76_import_owner', true)
);

if ($land76_managed_service_hub_post) {
    $blogseo_main_image_url = (string) get_post_meta(get_the_ID(), '_land76_main_image_url', true);
    $blogseo_main_image_alt = (string) get_post_meta(get_the_ID(), '_land76_main_image_alt', true);
}

if (!$land76_managed_service_hub_post && (!$blogseo_main_image_url || strpos($blogseo_main_image_url, '001-02-1') !== false)) { /* legacy drenazh fallback */
    $blogseo_main_image_url = land76_blogseo_asset_url(land76_blogseo_topic_image_by_text(get_the_ID(), $blogseo_topics));
}

if (!$land76_managed_service_hub_post && (!$blogseo_main_image_alt || $blogseo_main_image_alt === $blogseo_title)) {
    $blogseo_main_image_alt = land76_blogseo_default_image_alt(get_the_ID(), $blogseo_topics);
}

$blogseo_cta_title = land76_blogseo_field('blogseo_cta_title', 'Нужен расчет работ по участку?');
$blogseo_cta_text = land76_blogseo_field('blogseo_cta_text', 'Посмотрим задачу, предложим понятную схему работ и рассчитаем стоимость.');
$blogseo_cta_button_text = land76_blogseo_field('blogseo_cta_button_text', 'Получить консультацию');
$blogseo_cta_button_url = land76_blogseo_field('blogseo_cta_button_url', '#consultation');
$blogseo_related_services = land76_blogseo_field('blogseo_related_services', array());
$blogseo_faq_items = land76_blogseo_field('blogseo_faq_items', array());

if (!is_array($blogseo_sections)) {
    $blogseo_sections = array();
}

if (!is_array($blogseo_related_services)) {
    $blogseo_related_services = array();
}

if (!is_array($blogseo_faq_items)) {
    $blogseo_faq_items = array();
}
?>

<section class="hero seoblog-hero">
  <div class="hero__scene" id="scene">
    <div class="hero__bg"></div>
  </div>
  <div class="hero__content wrapper">
    <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php echo esc_html($blogseo_title); ?></h1>
    <?php if ($blogseo_subtitle) : ?>
      <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($blogseo_subtitle); ?></p>
    <?php endif; ?>
    <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
      <a href="<?php echo esc_url($blogseo_cta_button_url); ?>" class="hero__btn openPopup" data-modal="#popup"><?php echo esc_html($blogseo_cta_button_text); ?></a>
    </div>
    <div class="hero__breadcramps">
      <a class="hero__home" href="<?php echo esc_url(get_home_url()); ?>">Компания "Эксперты" | </a>
      <a class="hero__home" href="<?php echo esc_url(get_permalink(9962)); ?>">Полезное | </a>
      <span class="hero__active-page"><?php echo esc_html(get_the_title()); ?></span>
    </div>
  </div>
  <div class="animation-wrap"><img style="margin-left:100px" class="animation-wrap__img" src="<?php echo esc_url(get_template_directory_uri()); ?>/img/mouse.png" alt="" role="presentation" /><span class="animation-wrap__text">Листайте</span></div>
</section>

<section class="seoblog wrapper">
  <article class="seoblog__article">
    <?php if ($blogseo_lead) : ?>
      <p class="seoblog__lead"><?php echo esc_html($blogseo_lead); ?></p>
    <?php endif; ?>

    <?php if ($blogseo_main_image_url) : ?>
      <figure class="seoblog__figure">
        <img src="<?php echo esc_url($blogseo_main_image_url); ?>" alt="<?php echo esc_attr($blogseo_main_image_alt); ?>">
      </figure>
    <?php endif; ?>

    <?php if (!empty($blogseo_sections)) : ?>
      <nav class="seoblog__toc" aria-label="Оглавление">
        <p class="seoblog__toc-title">Содержание</p>
        <ol>
          <?php foreach ($blogseo_sections as $index => $section) : ?>
            <?php if (!empty($section['heading'])) : ?>
              <li><a href="#blog-section-<?php echo esc_attr($index + 1); ?>"><?php echo esc_html($section['heading']); ?></a></li>
            <?php endif; ?>
          <?php endforeach; ?>
        </ol>
      </nav>
    <?php endif; ?>

    <?php if (!empty($blogseo_sections)) : ?>
      <?php foreach ($blogseo_sections as $index => $section) : ?>
        <section class="seoblog__section" id="blog-section-<?php echo esc_attr($index + 1); ?>">
          <?php if (!empty($section['heading'])) : ?>
            <h2><?php echo esc_html($section['heading']); ?></h2>
          <?php endif; ?>
          <?php if (!empty($section['body'])) : ?>
            <div class="seoblog__text"><?php echo wp_kses_post($section['body']); ?></div>
          <?php endif; ?>
          <?php if (!empty($section['points']) && is_array($section['points'])) : ?>
            <div class="seoblog__points">
              <?php foreach ($section['points'] as $point) : ?>
                <div class="seoblog__point">
                  <?php if (!empty($point['title'])) : ?>
                    <h3><?php echo esc_html($point['title']); ?></h3>
                  <?php endif; ?>
                  <?php if (!empty($point['text'])) : ?>
                    <p><?php echo esc_html($point['text']); ?></p>
                  <?php endif; ?>
                </div>
              <?php endforeach; ?>
            </div>
          <?php endif; ?>
        </section>
      <?php endforeach; ?>
    <?php else : ?>
      <div class="seoblog__text"><?php the_content(); ?></div>
    <?php endif; ?>

    <section class="seoblog__cta" id="consultation">
      <div>
        <h2><?php echo esc_html($blogseo_cta_title); ?></h2>
        <p><?php echo esc_html($blogseo_cta_text); ?></p>
      </div>
      <a href="<?php echo esc_url($blogseo_cta_button_url); ?>" class="hero__btn openPopup" data-modal="#popup"><?php echo esc_html($blogseo_cta_button_text); ?></a>
    </section>

    <?php if (!empty($blogseo_related_services)) : ?>
      <section class="seoblog__related">
        <h2>Связанные услуги</h2>
        <div class="seoblog__related-grid">
          <?php foreach ($blogseo_related_services as $related_post_id) : ?>
            <?php
            $related_post = get_post($related_post_id);
            $related_page_key = $related_post instanceof WP_Post
                ? (string) get_post_meta($related_post->ID, '_land76_page_key', true)
                : '';
            $is_registered_hub = false;
            $service_hub_registry = function_exists('land76wp_service_hub_registry')
                ? land76wp_service_hub_registry()
                : array();
            foreach ($service_hub_registry as $service_hub) {
                if ($related_post instanceof WP_Post && (int) $service_hub['hub_post_id'] === (int) $related_post->ID) {
                    $is_registered_hub = true;
                    break;
                }
            }
            $is_managed_child = $related_post instanceof WP_Post
                && function_exists('land76wp_is_managed_service_hub_post')
                && land76wp_is_managed_service_hub_post($related_post->ID)
                && strpos($related_page_key, '-CHILD-') !== false;
            $is_legacy_commercial = $related_post instanceof WP_Post
                && $related_post->post_type === 'post'
                && has_category(74, $related_post->ID);
            if (!$related_post instanceof WP_Post
                || $related_post->post_status !== 'publish'
                || (!$is_registered_hub && !$is_managed_child && !$is_legacy_commercial)) {
                continue;
            }
            ?>
            <a class="seoblog__related-card" href="<?php echo esc_url(get_permalink($related_post)); ?>">
              <?php if (has_post_thumbnail($related_post)) : ?>
                <img src="<?php echo esc_url(get_the_post_thumbnail_url($related_post, 'medium')); ?>" alt="<?php echo esc_attr(get_the_title($related_post)); ?>">
              <?php endif; ?>
              <span><?php echo esc_html(get_the_title($related_post)); ?></span>
            </a>
          <?php endforeach; ?>
        </div>
      </section>
    <?php endif; ?>

    <?php if (!empty($blogseo_faq_items)) : ?>
      <section class="seoblog__faq">
        <h2>Вопросы по теме</h2>
        <?php foreach ($blogseo_faq_items as $item) : ?>
          <div class="seoblog__faq-item">
            <?php if (!empty($item['question'])) : ?>
              <h3><?php echo esc_html($item['question']); ?></h3>
            <?php endif; ?>
            <?php if (!empty($item['answer'])) : ?>
              <p><?php echo esc_html($item['answer']); ?></p>
            <?php endif; ?>
          </div>
        <?php endforeach; ?>
      </section>
      <script type="application/ld+json">
      <?php
      $faq_schema = array(
          '@context' => 'https://schema.org',
          '@type' => 'FAQPage',
          'mainEntity' => array(),
      );
      foreach ($blogseo_faq_items as $item) {
          if (empty($item['question']) || empty($item['answer'])) {
              continue;
          }
          $faq_schema['mainEntity'][] = array(
              '@type' => 'Question',
              'name' => wp_strip_all_tags($item['question']),
              'acceptedAnswer' => array(
                  '@type' => 'Answer',
                  'text' => wp_strip_all_tags($item['answer']),
              ),
          );
      }
      echo wp_json_encode($faq_schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
      ?>
      </script>
    <?php endif; ?>
  </article>
</section>
