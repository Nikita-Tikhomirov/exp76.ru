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

$blogseo_title = land76_blogseo_field('blogseo_hero_title', get_the_title());
$blogseo_subtitle = land76_blogseo_field('blogseo_hero_subtitle', get_the_excerpt());
$blogseo_lead = land76_blogseo_field('blogseo_lead', get_the_excerpt());
$blogseo_sections = land76_blogseo_field('blogseo_sections', array());
$blogseo_main_image = land76_blogseo_field('blogseo_main_image', '');
$blogseo_main_image_url = land76_blogseo_image_url($blogseo_main_image, land76_blogseo_field('blogseo_main_image_url', 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp'));
$blogseo_main_image_alt = land76_blogseo_field('blogseo_main_image_alt', $blogseo_title);
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
            if (!$related_post instanceof WP_Post) {
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
