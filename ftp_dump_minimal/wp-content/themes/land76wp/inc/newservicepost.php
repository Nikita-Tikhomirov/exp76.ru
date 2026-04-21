<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/index.css" />
<link rel="stylesheet" href="<?php bloginfo("template_directory"); ?>/css/services.css" />
<style>
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
    margin-top: 40px;
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
    width: 100%;
    font-weight: 700;
  }

  .faq-toggle span {
    font-size: 24px;
    margin-left: 20px;
    flex-shrink: 0;
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
    background: url(../img/adv.png) 0 0/cover fixed;
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

    .problem-item img {
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

    .faq-toggle span {
      font-size: 20px !important;
      width: fit-content;
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
    }

    .faq-toggle span {
      font-size: 18px !important;
    }
  }
</style>
<?php
$ns87_term_context = 'category_87';
$ns87_hero_title = function_exists('get_field') ? get_field('ns87_hero_title', $ns87_term_context) : '';
$ns87_hero_subtitle = function_exists('get_field') ? get_field('ns87_hero_subtitle', $ns87_term_context) : '';
$ns87_hero_btn_primary_text = function_exists('get_field') ? get_field('ns87_hero_btn_primary_text', $ns87_term_context) : '';
$ns87_hero_btn_primary_url = function_exists('get_field') ? get_field('ns87_hero_btn_primary_url', $ns87_term_context) : '';
$ns87_hero_btn_secondary_text = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_text', $ns87_term_context) : '';
$ns87_hero_btn_secondary_url = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_url', $ns87_term_context) : '';
$ns87_problem_title = function_exists('get_field') ? get_field('ns87_problem_title', $ns87_term_context) : '';
$ns87_problem_text = function_exists('get_field') ? get_field('ns87_problem_text', $ns87_term_context) : '';
$ns87_problem_items = function_exists('get_field') ? get_field('ns87_problem_items', $ns87_term_context) : array();
$ns87_solution_title = function_exists('get_field') ? get_field('ns87_solution_title', $ns87_term_context) : '';
$ns87_solution_text = function_exists('get_field') ? get_field('ns87_solution_text', $ns87_term_context) : '';
$ns87_solution_points = function_exists('get_field') ? get_field('ns87_solution_points', $ns87_term_context) : array();
$ns87_prices_title = function_exists('get_field') ? get_field('ns87_prices_title', $ns87_term_context) : '';
$ns87_price_rows = function_exists('get_field') ? get_field('ns87_price_rows', $ns87_term_context) : array();
$ns87_estimate_title = function_exists('get_field') ? get_field('ns87_estimate_title', $ns87_term_context) : '';
$ns87_estimate_items = function_exists('get_field') ? get_field('ns87_estimate_items', $ns87_term_context) : array();
$ns87_estimate_total = function_exists('get_field') ? get_field('ns87_estimate_total', $ns87_term_context) : '';
$ns87_faq_title = function_exists('get_field') ? get_field('ns87_faq_title', $ns87_term_context) : '';
$ns87_faq_items = function_exists('get_field') ? get_field('ns87_faq_items', $ns87_term_context) : array();

if (empty($ns87_problem_items) || !is_array($ns87_problem_items)) {
    $ns87_problem_items = array(
        array(
            'title' => 'Вода стоит на участке',
            'text' => 'Постоянные лужи, болотистая почва, невозможность использовать землю для посадок и строительства',
            'image' => 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp',
        ),
        array(
            'title' => 'Подтапливает фундамент',
            'text' => 'Грунтовые воды разрушают бетон, вызывают коррозию арматуры, создают плесень в подвале',
            'image' => 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp',
        ),
        array(
            'title' => 'Невозможно использовать землю',
            'text' => 'Затопленный газон, погибшие растения, невозможность строительства и благоустройства',
            'image' => 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp',
        ),
    );
}

if (empty($ns87_solution_points) || !is_array($ns87_solution_points)) {
    $ns87_solution_points = array(
        array('title' => 'Тип дренажа', 'text' => 'Комбинированная система: глубинный + поверхностный дренаж с дренажными колодцами'),
        array('title' => 'Как делается', 'text' => 'Монтаж перфорированных труб на уровне грунтовых вод с уклоном 2-3% и выводом в дренажный колодец'),
        array('title' => 'Почему именно так', 'text' => 'Только комплексный подход обеспечивает отвод как поверхностных, так и грунтовых вод'),
        array('title' => 'Результат', 'text' => 'Сухой участок, защищенный фундамент, возможность полноценного использования земли'),
    );
}

if (empty($ns87_price_rows) || !is_array($ns87_price_rows)) {
    $ns87_price_rows = array(
        array('service' => 'Глубинный дренаж (высокий УГВ)', 'price' => 'от 4 500 ₽', 'term' => '5-7 дней'),
        array('service' => 'Поверхностный дренаж', 'price' => 'от 2 800 ₽', 'term' => '2-4 дня'),
        array('service' => 'Дренажные колодцы', 'price' => 'от 25 000 ₽', 'term' => '1-2 дня'),
    );
}

if (empty($ns87_estimate_items) || !is_array($ns87_estimate_items)) {
    $ns87_estimate_items = array(
        array('item' => 'Геологические изыскания - 25 000 ₽'),
        array('item' => 'Проектирование системы - 20 000 ₽'),
        array('item' => 'Монтаж дренажных труб (200 м) - 900 000 ₽'),
        array('item' => 'Установка дренажных колодцев (4 шт) - 100 000 ₽'),
    );
}

if (empty($ns87_faq_items) || !is_array($ns87_faq_items)) {
    $ns87_faq_items = array(
        array(
            'question' => 'Как определить высокий уровень грунтовых вод?',
            'answer' => 'Признаки высокого УГВ: лужи не уходят после дождя, вода в подвале, заболоченность участка, уровень воды в колодцах выше 2 метров.',
        ),
        array(
            'question' => 'Нужна ли разрешительная документация?',
            'answer' => 'Для дренажной системы на собственном участке разрешительная документация не требуется, за исключением случаев подключения к центральной канализации.',
        ),
    );
}
?>

<!-- 1. Hero блок -->
<section class="hero">
  <div class="hero__scene" id="scene">
    <div class="hero__bg" data-depth="0.4"></div>
  </div>
  <div class="hero__content wrapper">
    <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php echo esc_html($ns87_hero_title ? $ns87_hero_title : 'Дренаж участка с высоким уровнем грунтовых вод'); ?>
    </h1>
    <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($ns87_hero_subtitle ? $ns87_hero_subtitle : 'Профессиональное решение для участков с высоким уровнем грунтовых вод. Гарантия защиты фундамента и благоустройства.'); ?></p>
    <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
      <a href="<?php echo esc_url($ns87_hero_btn_primary_url ? $ns87_hero_btn_primary_url : '#calc'); ?>" class="hero__btn"><?php echo esc_html($ns87_hero_btn_primary_text ? $ns87_hero_btn_primary_text : 'Рассчитать стоимость'); ?></a>
      <a href="<?php echo esc_url($ns87_hero_btn_secondary_url ? $ns87_hero_btn_secondary_url : '#consultation'); ?>" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;"><?php echo esc_html($ns87_hero_btn_secondary_text ? $ns87_hero_btn_secondary_text : 'Получить консультацию'); ?></a>
    </div>
    <div class="hero__breadcramps"><a class="hero__home" href="<?php echo get_home_url(); ?>">Компания "Эксперты"
        | </a><span class="hero__active-page">Дренаж с высоким уровнем грунтовых вод</span></div>
  </div>

  <div class="animation-wrap"><img style="margin-left:100px" class="animation-wrap__img"
      src="<?php echo get_template_directory_uri() ?>/img/mouse.png" alt="" role="presentation" /><span
      class="animation-wrap__text">Листайте</span></div>
</section>

<!-- 2. Проблема -->
<section class="services wrapper howWorkCustom portfolio">
  <div class="problem-block" data-aos="fade-up" data-aos-duration="600">
    <h3><?php echo esc_html($ns87_problem_title ? $ns87_problem_title : 'Вода стоит на участке?'); ?></h3>
    <p><?php echo esc_html($ns87_problem_text ? $ns87_problem_text : 'Высокий уровень грунтовых вод — это серьезная проблема, которая требует немедленного решения. Игнорирование проблемы приводит к разрушению фундамента и порче имущества.'); ?></p>

    <?php foreach ($ns87_problem_items as $index => $ns87_problem_item) : ?>
    <?php
      $ns87_problem_img = '';
      if (!empty($ns87_problem_item['image'])) {
          if (is_array($ns87_problem_item['image']) && !empty($ns87_problem_item['image']['url'])) {
              $ns87_problem_img = $ns87_problem_item['image']['url'];
          } elseif (is_numeric($ns87_problem_item['image'])) {
              $ns87_problem_img = wp_get_attachment_image_url((int) $ns87_problem_item['image'], 'full');
          } elseif (is_string($ns87_problem_item['image'])) {
              $ns87_problem_img = $ns87_problem_item['image'];
          }
      }
      if (empty($ns87_problem_img)) {
          $ns87_problem_img = 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp';
      }
    ?>
    <div class="problem-item" data-aos="fade-up" data-aos-duration="<?php echo esc_attr(700 + ($index * 100)); ?>">
      <img src="<?php echo esc_url($ns87_problem_img); ?>" alt="<?php echo esc_attr(!empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : 'Проблема'); ?>">
      <div>
        <h4><?php echo esc_html(!empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : ''); ?></h4>
        <p><?php echo esc_html(!empty($ns87_problem_item['text']) ? $ns87_problem_item['text'] : ''); ?></p>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
</section>

<!-- 3. Решение -->
<section class="services wrapper">
  <div class="solution-block" data-aos="fade-up" data-aos-duration="600">
    <h3><?php echo esc_html($ns87_solution_title ? $ns87_solution_title : 'Комплексное решение проблемы'); ?></h3>
    <p><?php echo esc_html($ns87_solution_text ? $ns87_solution_text : 'Для участков с высоким уровнем грунтовых вод применяем комбинированную систему дренажа, которая обеспечивает 100% защиту от влаги.'); ?></p>

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

<!-- 4. Технология -->
<section class="services wrapper">
  <div class="tech-block" data-aos="fade-up" data-aos-duration="600">
    <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 20px;">Технология монтажа</h2>
    <p style="text-align: center; margin-bottom: 30px;">Применяем проверенные технологии с учетом геологических
      особенностей участка</p>

    <div class="tech-grid">
      <div class="tech-item" data-aos="fade-up" data-aos-duration="700">
        <h4>Глубина</h4>
        <p>1.5-2.5 метра до уровня залегания грунтовых вод</p>
      </div>

      <div class="tech-item" data-aos="fade-up" data-aos-duration="800">
        <h4>Трубы</h4>
        <p>Гофрированные трубы ПНД 110-160 мм с геотекстильной обмоткой</p>
      </div>

      <div class="tech-item" data-aos="fade-up" data-aos-duration="900">
        <h4>Уклон</h4>
        <p>2-3% на 1 метр для самотека воды к дренажным колодцам</p>
      </div>

      <div class="tech-item" data-aos="fade-up" data-aos-duration="1000">
        <h4>Схема</h4>
        <p>Елочка с выводом в главный дренажный колодец и ливневую канализацию</p>
      </div>
    </div>
  </div>
</section>

<!-- 5. Кейсы -->
<section class="services wrapper casesCustom">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 40px;">Примеры наших работ</h2>
  <div class="services__cards columns3">
    <?php
    // Get selected posts from ACF field for Real Projects
    $selected_projects = get_field('selected_real_projects');

    if ($selected_projects && !empty($selected_projects)) {
      foreach ($selected_projects as $post_id) {
        $post = get_post($post_id);
        setup_postdata($post);
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <?php if (has_post_thumbnail($post_id)): ?>
              <img class="service__img" src="<?php echo get_the_post_thumbnail_url($post_id); ?>"
                alt="<?php echo get_the_title($post_id); ?>">
            <?php else: ?>
              <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/default-case.jpg"
                alt="<?php echo get_the_title($post_id); ?>">
            <?php endif; ?>
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title"><?php echo get_the_title($post_id); ?></h5>
            <?php
            $excerpt = get_the_excerpt($post_id);
            if (empty($excerpt)) {
              $excerpt = wp_trim_words(get_post_field('post_content', $post_id), 15);
            }
            echo '<p>' . $excerpt . '</p>';
            ?>
            <p>
              <strong><?php echo get_field('price', $post_id) ? 'from ' . get_field('price', $post_id) : 'Price on request'; ?></strong>
            </p>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php echo get_permalink($post_id); ?>">Read more</a>
            </div>
          </div>
        </div>
      <?php
      }
      wp_reset_postdata();
    } else {
      // Fallback to default static cards if no posts selected
      ?>
      <div class="service" data-aos="fade-up" data-aos-duration="400">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/high-water-1.jpg"
            alt="Äðåíàæ ñ âûñîêèì ÓÃÂ 6 ñîòîê">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Äðåíàæ ñ âûñîêèì ÓÃÂ 6 ñîòîê</h5>
          <p>Êîìïëåêñíûé äðåíàæ ó÷àñòêà ñ âûñîêèì óðîâíåì ãðóíòîâûõ âîä. Óñòàíîâêà 4 äðåíàæíûõ êîëîäöåâ.</p>
          <p><strong>îò 480 000 â</strong></p>
        </div>
      </div>

      <div class="service" data-aos="fade-up" data-aos-duration="500">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/high-water-2.jpg"
            alt="Äðåíàæ çàáîëî÷åííîãî ó÷àñòêà">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Äðåíàæ çàáîëî÷åííîãî ó÷àñòêà</h5>
          <p>Îñóøåíèå ïðîáëåìíîãî ó÷àñòêà 10 ñîòîê ñ âûñîêèì óðîâíåì ãðóíòîâûõ âîä.</p>
          <p><strong>îò 750 000 â</strong></p>
        </div>
      </div>

      <div class="service" data-aos="fade-up" data-aos-duration="600">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/high-water-3.jpg"
            alt="Ïðèñòåííûé äðåíàæ ñ âûñîêèì ÓÃÂ">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Ïðèñòåííûé äðåíàæ ñ âûñîêèì ÓÃÂ</h5>
          <p>Çàùèòà ôóíäàìåíòà äîìà îò ãðóíòîâûõ âîä ñ óñòàíîâêîé ïðèñòâîëüíîé äðåíàæíîé ñèñòåìû.</p>
          <p><strong>îò 320 000 â</strong></p>
        </div>
      </div>
    <?php } ?>
  </div>
</section>

<!-- 6. Цена -->
<section class="services wrapper">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 40px;"><?php echo esc_html($ns87_prices_title ? $ns87_prices_title : 'Стоимость дренажа с высоким УГВ'); ?></h2>

  <div style="overflow-x: auto; margin-bottom: 30px;">
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #fff;">
      <thead>
        <tr style="background: #f5f5f5;">
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Услуга
          </th>
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Цена
            за метр</th>
          <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Сроки
          </th>
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
, cursive; font-size: 24px; color: #333;"><?php echo esc_html($ns87_estimate_title ? $ns87_estimate_title : 'Пример сметы на дренаж участка 10 соток (высокий УГВ)'); ?></h3>
    <ul class="estimate-list">
      <?php foreach ($ns87_estimate_items as $ns87_estimate_item) : ?>
      <li><?php echo esc_html(!empty($ns87_estimate_item['item']) ? $ns87_estimate_item['item'] : ''); ?></li>
      <?php endforeach; ?>
      <li><strong><?php echo esc_html($ns87_estimate_total ? $ns87_estimate_total : 'Итого: 1 045 000 ₽'); ?></strong></li>
    </ul>
  </div>
</section>

<!-- 7. Ошибки -->
<section class="services wrapper portfolio">
  <div class="error-block" data-aos="fade-up" data-aos-duration="600">
    <h3>Частые ошибки при монтаже</h3>
    <p>Избегайте этих ошибок, которые приводят к неэффективной работе дренажной системы</p>

    <div class="error-item" data-aos="fade-up" data-aos-duration="700">
      <img src="https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp" alt="Неправильный уклон">
      <div>
        <h4>Неправильный уклон</h4>
        <p>Уклон менее 1% приводит к застою воды в трубах и образованию засоров</p>
      </div>
    </div>

    <div class="error-item" data-aos="fade-up" data-aos-duration="800">
      <img src="https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp" alt="Нет геотекстиля">
      <div>
        <h4>Нет геотекстиля</h4>
        <p>Отсутствие геотекстильной обмотки приводит к заиливанию труб и выходу системы из строя</p>
      </div>
    </div>

    <div class="error-item" data-aos="fade-up" data-aos-duration="900">
      <img src="https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp" alt="Экономия на трубах">
      <div>
        <h4>Экономия на трубах</h4>
        <p>Использование дешевых труб без перфорации и геотекстиля быстро приводит к поломке системы</p>
      </div>
    </div>
  </div>
</section>



<!-- 8. Мини FAQ -->
<section class="services wrapper">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
, cursive; font-size: 35px; margin-bottom: 40px;"><?php echo esc_html($ns87_faq_title ? $ns87_faq_title : 'Ответы на вопросы'); ?></h2>

  <div style="margin-bottom: 30px;">
    <?php foreach ($ns87_faq_items as $ns87_faq_item) : ?>
    <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
      <div style="background: #f5f5f5; padding: 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;" onclick="var answer = this.nextElementSibling; answer.style.display = answer.style.display === 'block' ? 'none' : 'block'; this.querySelector('.faq-icon').textContent = this.querySelector('.faq-icon').textContent === '+' ? '-' : '+';">
        <h3 class="faq-toggle" style="margin: 0;">
          <span style="display: none;">+</span>
          <span style="display: none;">-</span>
          <span><?php echo esc_html(!empty($ns87_faq_item['question']) ? $ns87_faq_item['question'] : ''); ?></span>
        </h3>
        <span class="faq-icon" style="font-size: 24px; color: #0a9215;">+</span>
      </div>
      <div class="faq-answer" style="display: none;">
        <p><?php echo esc_html(!empty($ns87_faq_item['answer']) ? $ns87_faq_item['answer'] : ''); ?></p>
      </div>
    </div>
    <?php endforeach; ?>
  </div>
</section>
<!-- 9. Перелинковка -->
<section class="services wrapper">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
, cursive; font-size: 35px; margin-bottom: 40px;">Другие виды дренажа</h2>

  <div class="columns3" style=" gap: 30px;">
    <?php
    // Get selected posts from ACF field for Other Drainage Types
    $selected_drainage = get_field('selected_other_drainage');

    if ($selected_drainage && !empty($selected_drainage)) {
      foreach ($selected_drainage as $post_id) {
        $post = get_post($post_id);
        setup_postdata($post);
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <?php if (has_post_thumbnail($post_id)): ?>
              <img class="service__img" src="<?php echo get_the_post_thumbnail_url($post_id); ?>"
                alt="<?php echo get_the_title($post_id); ?>">
            <?php else: ?>
              <img class="service__img" src="/wp-content/themes/theme/assets/img/drainage/default-drainage.jpg"
                alt="<?php echo get_the_title($post_id); ?>">
            <?php endif; ?>
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title"><?php echo get_the_title($post_id); ?></h5>
            <?php
            $excerpt = get_the_excerpt($post_id);
            if (empty($excerpt)) {
              $excerpt = wp_trim_words(get_post_field('post_content', $post_id), 15);
            }
            echo '<p>' . $excerpt . '</p>';
            ?>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php echo get_permalink($post_id); ?>">Подробнее</a>
            </div>
          </div>
        </div>
      <?php
      }
      wp_reset_postdata();
    } else {
      // Fallback to default static cards if no posts selected
      ?>
      <div class="service" data-aos="fade-up" data-aos-duration="400">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/drainage/deep-drainage.jpg"
            alt="Ãëóáèííûé äðåíàæ">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Ãëóáèííûé äðåíàæ</h5>
          <p>Äëÿ ó÷àñòêîâ ñ âûñîêèì óðîâíåì ãðóíòîâûõ âîä è ïîñòîÿííîé âëàæíîñòüþ</p>
          <div class="service__link-wrap">
            <a class="service__link" href="/glubinnyj-drenazh/">Ïîäðîáíåå</a>
          </div>
        </div>
      </div>

      <div class="service" data-aos="fade-up" data-aos-duration="500">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/drainage/surface-drainage.jpg"
            alt="Ïîâåðõíîñòíûé äðåíàæ">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Ïîâåðõíîñòíûé äðåíàæ</h5>
          <p>Äëÿ îòâîäà äîæäåâûõ è òàëûõ âîä ñ ïîâåðõíîñòè ó÷àñòêà</p>
          <div class="service__link-wrap">
            <a class="service__link" href="/poverhnostnyj-drenazh/">Ïîäðîáíåå</a>
          </div>
        </div>
      </div>

      <div class="service" data-aos="fade-up" data-aos-duration="600">
        <div class="service__img-wrap">
          <img class="service__img" src="/wp-content/themes/theme/assets/img/drainage/price.jpg" alt="Öåíà íà äðåíàæ">
        </div>
        <div class="service__text-wrap">
          <h5 class="service__title">Öåíà</h5>
          <p>Ïîäðîáíûé ðàñ÷åò ñòîèìîñòè äðåíàæíûõ ñèñòåì ëþáîé ñëîæíîñòè</p>
          <div class="service__link-wrap">
            <a class="service__link" href="/drenazh-uchastka/cena/">Ïîäðîáíåå</a>
          </div>
        </div>
      </div>
    <?php } ?>
  </div>
</section>

<!-- 10. CTA -->
<section class="advantages wrapper">
  <div style="text-align: center; background: #f9f9f9; padding: 40px; border-radius: 10px;">
    <h2 style="font-weight: 700; margin-bottom: 35px;">Получите расчет дренажа с высоким УГВ за 1 день</h2>
    <p style="margin-bottom: 30px;">Оставьте заявку и наш специалист свяжется с вами для бесплатной консультации и
      точного расчета стоимости</p>
    <form class="cta-form" id="calc" style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
      <input type="text" placeholder="Ваше имя" required
        style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
      <input type="tel" placeholder="Ваш телефон" required
        style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
      <button type="submit" class="btn--primary-custom">Получить расчет</button>
    </form>
  </div>
</section>
