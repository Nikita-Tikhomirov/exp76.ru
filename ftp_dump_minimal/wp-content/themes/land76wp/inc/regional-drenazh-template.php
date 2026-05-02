<?php
if (!defined('ABSPATH')) {
  exit;
}

$region = land76wp_get_current_drenazh_region();
if (!$region) {
  status_header(404);
  get_template_part('404');
  return;
}

$term_context = 'category_87';
$price_rows = function_exists('get_field') ? get_field('cat87_price_rows', $term_context) : array();
$estimate_items = function_exists('get_field') ? get_field('cat87_estimate_items', $term_context) : array();
$estimate_total = function_exists('get_field') ? get_field('cat87_estimate_total', $term_context) : '';
$selected_posts = function_exists('get_field') ? get_field('selected_works_posts', $term_context) : array();

if (empty($price_rows) || !is_array($price_rows)) {
  $price_rows = array(
    array('service' => 'Глубинный дренаж участка', 'price' => 'от 3 500 ₽/м.п.', 'term' => '3-7 дней'),
    array('service' => 'Поверхностный дренаж', 'price' => 'от 2 200 ₽/м.п.', 'term' => '2-5 дней'),
    array('service' => 'Дренаж вокруг дома', 'price' => 'по расчету', 'term' => 'от 3 дней'),
  );
}

if (empty($estimate_items) || !is_array($estimate_items)) {
  $estimate_items = array(
    array('item' => 'Осмотр участка и схема отвода воды'),
    array('item' => 'Расчет глубины, уклонов, труб, щебня и колодцев'),
    array('item' => 'Монтаж, проверка уклонов и вывод воды в рабочую точку'),
  );
}

get_header('seo');
?>
<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/index.css" />
<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/services.css" />
<style>
  .regional-block { background: #fff; border-radius: 8px; padding: 34px; margin-bottom: 34px; box-shadow: 0 8px 25px rgba(0,0,0,.08); }
  .regional-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; }
  .regional-card { background: #fff; border: 1px solid #e0e0e0; border-left: 4px solid #0a9215; border-radius: 8px; padding: 22px; }
  .regional-card h3 { color: #0a9215; font-size: 22px; margin-bottom: 12px; }
  .regional-steps { counter-reset: step; }
  .regional-step { position: relative; padding-left: 54px; margin-bottom: 20px; }
  .regional-step:before { counter-increment: step; content: counter(step); position: absolute; left: 0; top: 0; width: 36px; height: 36px; border-radius: 50%; background: #0a9215; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; }
  .regional-faq { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 16px; background: #fff; }
  .regional-faq h3 { font-size: 20px; margin-bottom: 10px; color: #333; }
  .regional-cta { text-align: center; background: #f6fff7; border: 2px solid #0a9215; border-radius: 8px; padding: 38px; }
  .regional-cta .hero__btn { display: inline-block; margin-top: 18px; }
  @media (max-width: 768px) {
    .regional-block { padding: 22px; }
    .regional-grid { grid-template-columns: 1fr; }
  }
</style>

<main>
  <section class="hero hero--main">
    <div class="hero__content wrapper">
      <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800">Дренаж участка в <?php echo esc_html($region['locative']); ?> под ключ</h1>
      <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($region['lead']); ?></p>
      <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
        <a href="#calc" class="hero__btn">Рассчитать стоимость</a>
        <a href="#consultation" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;">Получить консультацию</a>
      </div>
      <div class="hero__breadcramps">
        <a href="/">Компания "Эксперты"</a> | <span class="hero__active-page">Дренаж участка в <?php echo esc_html($region['locative']); ?></span>
      </div>
    </div>
  </section>

  <section class="advantages wrapper">
    <div class="advantages__inner">
      <h2 class="advantages__title">Почему дренаж лучше делать по схеме</h2>
      <div class="advantages__how">
        <div class="advantages__step"><p class="advantages__step-description">Сначала проверяем рельеф, грунт и точки сброса воды.</p></div>
        <div class="advantages__step"><p class="advantages__step-description">Считаем глубину, уклоны, материалы и колодцы до монтажа.</p></div>
        <div class="advantages__step"><p class="advantages__step-description">Связываем дренаж с ливневкой, дорожками и планом участка.</p></div>
        <div class="advantages__step"><p class="advantages__step-description">Сдаем систему, которую можно обслуживать без переделок.</p></div>
      </div>
    </div>
  </section>

  <section class="services wrapper">
    <div class="regional-block">
      <h2 class="services__title">Когда нужен дренаж участка в <?php echo esc_html($region['locative']); ?></h2>
      <p>Дренаж нужен, если после дождя вода долго стоит на газоне, появляется сырость у фундамента, размывает дорожки, вспучивает покрытие или участок невозможно нормально благоустроить.</p>
      <?php foreach ($region['text'] as $paragraph) : ?>
        <p><?php echo esc_html($paragraph); ?></p>
      <?php endforeach; ?>
    </div>
  </section>

  <section class="services wrapper">
    <div class="regional-block">
      <h2 class="services__title">Какие задачи решает дренаж на участке</h2>
      <div class="regional-grid">
        <div class="regional-card"><h3>Защита дома</h3><p>Отводим воду от фундамента, цоколя и отмостки, чтобы снизить риск сырости, подмыва и трещин.</p></div>
        <div class="regional-card"><h3>Сухие дорожки и газон</h3><p>Убираем застой воды с рабочих зон участка, въезда, дорожек и будущего благоустройства.</p></div>
        <div class="regional-card"><h3>Работа с грунтовыми водами</h3><p>Подбираем глубинный дренаж, когда проблема связана не только с дождем, но и с уровнем воды в грунте.</p></div>
        <div class="regional-card"><h3>Понятная смета</h3><p>Сразу считаем трассы, материалы, колодцы и объем работ, чтобы не продавать лишние метры.</p></div>
      </div>
    </div>
  </section>

  <section class="services wrapper">
    <h2 class="services__title">Услуги по дренажу участка</h2>
    <div class="services__cards columns3">
      <?php
      $posts = get_posts(array(
        'numberposts' => -1,
        'post_type' => 'post',
        'post_status' => 'publish',
        'post_name__in' => land76wp_drenazh_service_slugs(),
        'orderby' => 'post_name__in',
        'suppress_filters' => true,
        'tax_query' => array(
          array(
            'taxonomy' => 'category',
            'field' => 'term_id',
            'terms' => array(87, 74),
            'operator' => 'AND',
          ),
        ),
      ));
      foreach ($posts as $post) :
        setup_postdata($post);
      ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <?php if (has_post_thumbnail()) : ?>
              <img class="service__img" src="<?php echo esc_url(get_the_post_thumbnail_url(get_the_ID())); ?>" alt="<?php echo esc_attr(get_the_title()); ?>">
            <?php endif; ?>
          </div>
          <div class="service__text-wrap">
            <h3 class="service__title"><?php the_title(); ?></h3>
            <?php the_excerpt(); ?>
            <div class="service__link-wrap"><a class="service__link" href="<?php the_permalink(); ?>">Подробнее</a></div>
          </div>
        </div>
      <?php endforeach; wp_reset_postdata(); ?>
    </div>
  </section>

  <?php if (!empty($selected_posts) && is_array($selected_posts)) : ?>
  <section class="services wrapper casesCustom">
    <h2 class="services__title">Примеры работ</h2>
    <div class="services__cards columns3">
      <?php foreach ($selected_posts as $post_id) : ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <?php if (has_post_thumbnail($post_id)) : ?>
              <img class="service__img" src="<?php echo esc_url(get_the_post_thumbnail_url($post_id)); ?>" alt="<?php echo esc_attr(get_the_title($post_id)); ?>">
            <?php endif; ?>
          </div>
          <div class="service__text-wrap">
            <h3 class="service__title"><?php echo esc_html(get_the_title($post_id)); ?></h3>
            <p><?php echo esc_html(wp_trim_words(get_the_excerpt($post_id), 18)); ?></p>
            <p><strong><?php echo get_field('price', $post_id) ? 'от ' . esc_html(get_field('price', $post_id)) : 'Цена по запросу'; ?></strong></p>
            <div class="service__link-wrap"><a class="service__link" href="<?php echo esc_url(get_permalink($post_id)); ?>">Подробнее</a></div>
          </div>
        </div>
      <?php endforeach; ?>
    </div>
  </section>
  <?php endif; ?>

  <section id="calc" class="services wrapper portfolio">
    <h2 class="services__title">Стоимость дренажа участка в <?php echo esc_html($region['locative']); ?></h2>
    <div style="overflow-x: auto; margin-bottom: 30px;">
      <table style="width: 100%; border-collapse: collapse; background: #fff;">
        <thead><tr style="background: #0a9215; color: #fff;"><th style="padding: 15px; border: 1px solid #ddd;">Услуга</th><th style="padding: 15px; border: 1px solid #ddd;">Цена</th><th style="padding: 15px; border: 1px solid #ddd;">Сроки</th></tr></thead>
        <tbody>
          <?php foreach ($price_rows as $row) : ?>
            <tr>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($row['service']) ? $row['service'] : ''); ?></td>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($row['price']) ? $row['price'] : ''); ?></td>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($row['term']) ? $row['term'] : ''); ?></td>
            </tr>
          <?php endforeach; ?>
        </tbody>
      </table>
    </div>
    <div class="regional-block">
      <h3>Что входит в расчет</h3>
      <ul>
        <?php foreach ($estimate_items as $item) : ?>
          <li><?php echo esc_html(!empty($item['item']) ? $item['item'] : ''); ?></li>
        <?php endforeach; ?>
        <?php if ($estimate_total) : ?><li><strong><?php echo esc_html($estimate_total); ?></strong></li><?php endif; ?>
      </ul>
    </div>
  </section>

  <section class="services wrapper">
    <div class="regional-block regional-steps">
      <h2 class="services__title">Как мы работаем в <?php echo esc_html($region['locative']); ?></h2>
      <div class="regional-step"><h3>Осматриваем участок</h3><p>Смотрим рельеф, уровень воды, дом, дорожки, точки сброса и доступ для работ.</p></div>
      <div class="regional-step"><h3>Делаем схему</h3><p>Подбираем тип дренажа, глубину, уклоны, колодцы и связь с ливневой канализацией.</p></div>
      <div class="regional-step"><h3>Считаем смету</h3><p>Фиксируем материалы, объем земляных работ и понятный состав монтажа.</p></div>
      <div class="regional-step"><h3>Монтируем и проверяем</h3><p>Укладываем систему, контролируем уклоны, закрываем траншеи и показываем, как обслуживать дренаж.</p></div>
    </div>
  </section>

  <section class="services wrapper">
    <h2 class="services__title">Вопросы по дренажу участка в <?php echo esc_html($region['locative']); ?></h2>
    <div class="regional-faq"><h3>Можно ли посчитать стоимость без выезда?</h3><p>Предварительно можно. Для точной сметы нужен осмотр: важно увидеть уклон, грунт, доступ к участку и куда реально выводить воду.</p></div>
    <div class="regional-faq"><h3>Что лучше: глубинный или поверхностный дренаж?</h3><p>Это зависит от причины воды. Если проблема в грунте и уровне воды, нужен глубинный дренаж; если вода идет с покрытия и крыши, часто достаточно поверхностной системы или ливневки.</p></div>
    <div class="regional-faq"><h3>Можно ли сделать дренаж на готовом участке?</h3><p>Да, но схему подбираем аккуратнее: учитываем дорожки, посадки, заборы и подъезд техники, чтобы не переделывать благоустройство без необходимости.</p></div>
  </section>

  <section class="services wrapper">
    <div class="regional-cta">
      <h2 class="services__title">Рассчитать дренаж участка в <?php echo esc_html($region['locative']); ?></h2>
      <p>Опишите участок и проблему с водой. Подскажем рабочую схему, ориентировочную стоимость и ближайшие сроки монтажа.</p>
      <a href="#consultation" class="hero__btn openPopup" data-modal="#popup">Получить расчет</a>
    </div>
  </section>
</main>

<?php get_footer(); ?>
