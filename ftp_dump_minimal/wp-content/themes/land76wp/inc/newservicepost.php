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
$ns87_post_context = get_the_ID();
$ns87_hero_title = function_exists('get_field') ? get_field('ns87_hero_title', $ns87_post_context) : '';
$ns87_hero_subtitle = function_exists('get_field') ? get_field('ns87_hero_subtitle', $ns87_post_context) : '';
$ns87_hero_btn_primary_text = function_exists('get_field') ? get_field('ns87_hero_btn_primary_text', $ns87_post_context) : '';
$ns87_hero_btn_primary_url = function_exists('get_field') ? get_field('ns87_hero_btn_primary_url', $ns87_post_context) : '';
$ns87_hero_btn_secondary_text = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_text', $ns87_post_context) : '';
$ns87_hero_btn_secondary_url = function_exists('get_field') ? get_field('ns87_hero_btn_secondary_url', $ns87_post_context) : '';
$ns87_problem_title = function_exists('get_field') ? get_field('ns87_problem_title', $ns87_post_context) : '';
$ns87_problem_text = function_exists('get_field') ? get_field('ns87_problem_text', $ns87_post_context) : '';
$ns87_problem_items = function_exists('get_field') ? get_field('ns87_problem_items', $ns87_post_context) : array();
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

if (!function_exists('land76_newservice_selected_real_projects')) {
    function land76_newservice_selected_real_projects($post_id)
    {
        $selected_projects = function_exists('get_field') ? get_field('selected_real_projects', $post_id) : array();
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

        return 'drenazh';
    }
}

if (!function_exists('land76_newservice_context_image')) {
    function land76_newservice_context_image($post_id, $context = '')
    {
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

<!-- 1. Hero блок -->
<section class="hero">
  <div class="hero__scene" id="scene">
    <div class="hero__bg" data-depth="0.4"></div>
  </div>
  <div class="hero__content wrapper">
    <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php echo esc_html($ns87_hero_title ? $ns87_hero_title : get_the_title()); ?>
    </h1>
    <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($ns87_hero_subtitle ? $ns87_hero_subtitle : 'Выполняем работы под ключ: осмотр, схема, смета, монтаж и проверка результата.'); ?></p>
    <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
      <a href="<?php echo esc_url($ns87_hero_btn_primary_url ? $ns87_hero_btn_primary_url : '#calc'); ?>" class="hero__btn"><?php echo esc_html($ns87_hero_btn_primary_text ? $ns87_hero_btn_primary_text : 'Рассчитать стоимость'); ?></a>
      <a href="<?php echo esc_url($ns87_hero_btn_secondary_url ? $ns87_hero_btn_secondary_url : '#consultation'); ?>" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;"><?php echo esc_html($ns87_hero_btn_secondary_text ? $ns87_hero_btn_secondary_text : 'Получить консультацию'); ?></a>
    </div>
    <div class="hero__breadcramps"><a class="hero__home" href="<?php echo get_home_url(); ?>">Компания "Эксперты"
        | </a><span class="hero__active-page"><?php echo esc_html($ns87_breadcrumb_title); ?></span></div>
  </div>

  <div class="animation-wrap"><img style="margin-left:100px" class="animation-wrap__img"
      src="<?php echo get_template_directory_uri() ?>/img/mouse.png" alt="" role="presentation" /><span
      class="animation-wrap__text">Листайте</span></div>
</section>

<!-- 2. Проблема -->
<section class="services wrapper howWorkCustom portfolio">
  <div class="problem-block" data-aos="fade-up" data-aos-duration="600">
    <h3><?php echo esc_html($ns87_problem_title ? $ns87_problem_title : 'Какая задача решается'); ?></h3>
    <p><?php echo esc_html($ns87_problem_text ? $ns87_problem_text : 'Подбираем решение по месту, чтобы работы были понятными по составу, стоимости и результату.'); ?></p>

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
          $ns87_problem_img = land76_newservice_context_image(get_the_ID(), !empty($ns87_problem_item['title']) ? $ns87_problem_item['title'] : '');
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
<section class="services wrapper">
  <div class="seo-text" style="line-height: 1.6; margin-bottom: 40px;">
    <?php the_content(); ?>
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
    $selected_projects = land76_newservice_selected_real_projects(get_the_ID());

    if ($selected_projects && !empty($selected_projects)) {
      foreach ($selected_projects as $post_id) {
        $post_id = is_object($post_id) && !empty($post_id->ID) ? (int) $post_id->ID : (int) $post_id;
        $post = get_post($post_id);
        if (!$post) {
          continue;
        }
        setup_postdata($post);
        $project_image = function_exists('land76_get_card_image_url')
          ? land76_get_card_image_url($post_id, 'medium')
          : get_the_post_thumbnail_url($post_id, 'medium');
        if (!$project_image) {
          $project_image = land76_newservice_context_image(get_the_ID(), 'пример работ');
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
          <div class="service__img-wrap">
            <img class="service__img" src="<?php echo esc_url($project_image); ?>"
              alt="<?php echo esc_attr($project_title); ?>">
          </div>
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
    }
    ?>
  </div>
</section>

<!-- 6. Цена -->
<section class="services wrapper">
  <h2 style="text-align: center; color: #0a9215; font-family: 
'
Poiret One
'
, cursive; font-size: 35px; margin-bottom: 40px;"><?php echo esc_html($ns87_prices_title ? $ns87_prices_title : 'Стоимость услуги'); ?></h2>

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
, cursive; font-size: 24px; color: #333;"><?php echo esc_html($ns87_estimate_title ? $ns87_estimate_title : 'Пример расчета'); ?></h3>
    <ul class="estimate-list">
      <?php foreach ($ns87_estimate_items as $ns87_estimate_item) : ?>
      <li><?php echo esc_html(!empty($ns87_estimate_item['item']) ? $ns87_estimate_item['item'] : ''); ?></li>
      <?php endforeach; ?>
      <li><strong><?php echo esc_html($ns87_estimate_total ? $ns87_estimate_total : 'Итого: по расчету'); ?></strong></li>
    </ul>
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
<!-- 10. CTA -->
<section class="advantages wrapper">
  <div style="text-align: center; background: #f9f9f9; padding: 40px; border-radius: 10px;">
    <h2 style="font-weight: 700; margin-bottom: 35px;">Получите расчет по услуге за 1 день</h2>
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
