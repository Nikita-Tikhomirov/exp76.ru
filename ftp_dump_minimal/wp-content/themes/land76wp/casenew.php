<?php
/*
Template Name: Кейс (SEO)
Description: Продвинутый шаблон страницы кейса с SEO-структурой, ACF-полями и микроразметкой.
*/
?>

<?php
$cs87_post_id = get_the_ID();

// ── ACF fields ──────────────────────────────────────────────
$cs87_hero_title           = function_exists('get_field') ? get_field('cs87_hero_title', $cs87_post_id) : '';
$cs87_hero_subtitle        = function_exists('get_field') ? get_field('cs87_hero_subtitle', $cs87_post_id) : '';
$cs87_hero_btn_primary_text  = function_exists('get_field') ? get_field('cs87_hero_btn_primary_text', $cs87_post_id) : '';
$cs87_hero_btn_primary_url   = function_exists('get_field') ? get_field('cs87_hero_btn_primary_url', $cs87_post_id) : '';
$cs87_hero_btn_secondary_text= function_exists('get_field') ? get_field('cs87_hero_btn_secondary_text', $cs87_post_id) : '';
$cs87_hero_btn_secondary_url = function_exists('get_field') ? get_field('cs87_hero_btn_secondary_url', $cs87_post_id) : '';

$cs87_location   = function_exists('get_field') ? get_field('cs87_location', $cs87_post_id) : '';
$cs87_area       = function_exists('get_field') ? get_field('cs87_area', $cs87_post_id) : '';
$cs87_timeline   = function_exists('get_field') ? get_field('cs87_timeline', $cs87_post_id) : '';
$cs87_budget     = function_exists('get_field') ? get_field('cs87_budget', $cs87_post_id) : '';
$cs87_work_type  = function_exists('get_field') ? get_field('cs87_work_type', $cs87_post_id) : '';

$cs87_intro_title      = function_exists('get_field') ? get_field('cs87_intro_title', $cs87_post_id) : '';
$cs87_intro_text       = function_exists('get_field') ? get_field('cs87_intro_text', $cs87_post_id) : '';
$cs87_technology_title = function_exists('get_field') ? get_field('cs87_technology_title', $cs87_post_id) : '';
$cs87_technology_text  = function_exists('get_field') ? get_field('cs87_technology_text', $cs87_post_id) : '';
$cs87_result_title     = function_exists('get_field') ? get_field('cs87_result_title', $cs87_post_id) : '';
$cs87_result_text      = function_exists('get_field') ? get_field('cs87_result_text', $cs87_post_id) : '';
$cs87_scope_title      = function_exists('get_field') ? get_field('cs87_scope_title', $cs87_post_id) : '';
$cs87_scope_items      = function_exists('get_field') ? get_field('cs87_scope_items', $cs87_post_id) : array();
$cs87_price_note       = function_exists('get_field') ? get_field('cs87_price_note', $cs87_post_id) : '';
$cs87_service_url      = function_exists('get_field') ? get_field('cs87_service_url', $cs87_post_id) : '';

$cs87_challenge_title = function_exists('get_field') ? get_field('cs87_challenge_title', $cs87_post_id) : '';
$cs87_challenge_text  = function_exists('get_field') ? get_field('cs87_challenge_text', $cs87_post_id) : '';
$cs87_solution_title  = function_exists('get_field') ? get_field('cs87_solution_title', $cs87_post_id) : '';
$cs87_solution_text   = function_exists('get_field') ? get_field('cs87_solution_text', $cs87_post_id) : '';

$cs87_related_cases = function_exists('get_field') ? get_field('cs87_related_cases', $cs87_post_id) : array();

$cs87_faq_title  = function_exists('get_field') ? get_field('cs87_faq_title', $cs87_post_id) : '';
$cs87_faq_items  = function_exists('get_field') ? get_field('cs87_faq_items', $cs87_post_id) : array();

$cs87_seo_title       = function_exists('get_field') ? get_field('cs87_seo_title', $cs87_post_id) : '';
$cs87_seo_description = function_exists('get_field') ? get_field('cs87_seo_description', $cs87_post_id) : '';

// ── Defaults ────────────────────────────────────────────────
if (empty($cs87_hero_title))    $cs87_hero_title    = get_the_title();
if (empty($cs87_hero_subtitle)) $cs87_hero_subtitle = 'Выполненный проект компании «Эксперты». Фото, описание и детали работ.';

if (empty($cs87_faq_items) || !is_array($cs87_faq_items)) {
    $cs87_faq_items = array(
        array(
            'question' => 'Сколько стоит аналогичная работа?',
            'answer'   => 'Стоимость зависит от объёма, материалов и условий на объекте. Точную цену называем после осмотра. Для ориентира — свяжитесь с нами, сориентируем по похожим проектам.',
        ),
        array(
            'question' => 'Можно заказать такую же работу на моём участке?',
            'answer'   => 'Да. Приезжаем, смотрим участок, готовим схему и смету под ваш объект. Каждый проект адаптируем под конкретные условия.',
        ),
    );
}

// ── SEO meta overrides ─────────────────────────────────────
$cs87_page_title = $cs87_seo_title ? $cs87_seo_title : $cs87_hero_title;
$cs87_page_description = $cs87_seo_description ? $cs87_seo_description : wp_strip_all_tags($cs87_hero_subtitle);

// ── Facts for schema and display ───────────────────────────
$cs87_facts = array();
if ($cs87_location)  $cs87_facts[] = array('label' => 'Объект',     'value' => $cs87_location);
if ($cs87_work_type) $cs87_facts[] = array('label' => 'Тип работ',   'value' => $cs87_work_type);
if ($cs87_area)      $cs87_facts[] = array('label' => 'Площадь',     'value' => $cs87_area);
if ($cs87_timeline)  $cs87_facts[] = array('label' => 'Сроки',       'value' => $cs87_timeline);
if ($cs87_budget)    $cs87_facts[] = array('label' => 'Бюджет',      'value' => $cs87_budget);

$cs87_thumbnail_url = get_the_post_thumbnail_url($cs87_post_id, 'large');
if (!$cs87_thumbnail_url) {
    $cs87_thumbnail_url = 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp';
}

$cs87_schema = array(
    '@context'      => 'https://schema.org',
    '@type'         => 'CreativeWork',
    'name'          => $cs87_hero_title,
    'description'   => wp_strip_all_tags($cs87_hero_subtitle),
    'image'         => $cs87_thumbnail_url,
    'url'           => get_permalink($cs87_post_id),
    'datePublished' => get_the_date('c', $cs87_post_id),
    'dateModified'  => get_the_modified_date('c', $cs87_post_id),
    'author' => array(
        '@type' => 'Organization',
        'name'  => 'Компания «Эксперты»',
        'url'   => home_url(),
    ),
    'about' => $cs87_work_type ?: 'Ландшафтные работы',
);

if ($cs87_location) {
    $cs87_schema['contentLocation'] = array(
        '@type' => 'Place',
        'name'  => $cs87_location,
    );
}
?><!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0, user-scalable=no, maximum-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="yandex-verification" content="697af42ad3d96f49" />

  <meta property="og:type" content="article" />
  <meta property="og:url" content="<?php echo esc_url(get_permalink()); ?>" />
  <meta property="og:title" content="<?php echo esc_attr($cs87_page_title); ?>" />
  <meta property="og:description" content="<?php echo esc_attr($cs87_page_description); ?>" />
  <meta property="og:image" content="<?php echo esc_url($cs87_thumbnail_url); ?>" />
  <meta property="og:site_name" content="Компания «Эксперты»" />

  <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
  <link rel="stylesheet" href="https://unpkg.com/swiper/swiper-bundle.css">
  <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/portfoliopost.css" />
  <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/services.css" />
  <?php wp_head(); ?>
  <style>
    /* ── Hero ─────────────────────────────── */
    .hero__subtitle {
      color: #fff;
      font-size: 24px;
      margin-top: 15px;
      margin-bottom: 15px;
      font-weight: 500;
      text-shadow: 1px 1px 3px #000;
    }
    .hero__content { align-items: flex-start; justify-content: center; }
    .hero__buttons { margin-top: 40px; }
    .hero__breadcramps {
      color: #fff;
      position: absolute;
      bottom: 30px;
      text-align: right;
      font-size: 16px;
      padding: 4px 10px;
      background-color: #0000004d;
      align-self: start;
    }
    .hero__active-page { border-bottom: 2px solid #a2f9a9; }

    /* ── Facts ────────────────────────────── */
    .case-facts {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 20px;
      margin-top: 30px;
    }
    .case-fact {
      background: #fff;
      padding: 25px 20px;
      border-radius: 10px;
      text-align: center;
      box-shadow: 0 2px 8px rgba(0,0,0,.08);
      border-top: 3px solid #0a9215;
    }
    .case-fact__label {
      font-size: 14px;
      color: #777;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: .5px;
    }
    .case-fact__value {
      font-size: 18px;
      font-weight: 700;
      color: #333;
    }

    /* ── Challenge / Solution ─────────────── */
    .cs-block {
      padding: 40px;
      border-radius: 10px;
      margin-bottom: 40px;
      box-shadow: 0 5px 18px rgba(0,0,0,.1);
    }
    .cs-block--challenge {
      background: #f9f9f9;
      border-left: 4px solid #ff5e00;
    }
    .cs-block--solution {
      background: #f0faf1;
      border-left: 4px solid #0a9215;
    }
    .cs-block h3 {
      font-family: "Poiret One", cursive;
      font-size: 34px;
      font-weight: 900;
      line-height: 1.2;
      margin-bottom: 20px;
      text-shadow: 1px 2px 3px #00000024;
    }
    .cs-block--challenge h3 { color: #ff5e00; }
    .cs-block--solution h3  { color: #0a9215; }
    .cs-block p { line-height: 1.8; color: #333; font-size: 16px; }
    .seo-text {
      max-width: 980px;
      margin: 0 auto 34px !important;
      padding: 32px 36px;
      background: rgba(255,255,255,.88);
      border-left: 4px solid #0a9215;
      box-shadow: 0 5px 18px rgba(0,0,0,.12);
      color: #333;
      text-shadow: none;
    }
    .seo-text h2,
    .seo-text h3,
    .seo-text h4 {
      margin: 0 0 16px;
      font-family: "Poiret One", cursive;
      font-weight: 900;
      line-height: 1.22;
      color: #0a9215;
      text-shadow: 1px 2px 3px #00000024;
    }
    .seo-text h2 { font-size: 34px; }
    .seo-text h3 { font-size: 28px; }
    .seo-text h4 { font-size: 24px; }
    .seo-text p {
      margin: 0 0 14px;
      color: #333;
      font-size: 17px;
      line-height: 1.72;
      text-shadow: none;
    }
    .seo-text ul,
    .seo-text ol {
      display: grid;
      gap: 9px;
      margin: 16px 0 20px;
      padding-left: 0;
      list-style: none;
    }
    .seo-text li {
      position: relative;
      padding-left: 26px;
      color: #333;
      font-size: 16px;
      line-height: 1.65;
      text-shadow: none;
    }
    .seo-text li:before {
      content: "";
      position: absolute;
      left: 0;
      top: .65em;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #0a9215;
      box-shadow: 0 0 0 4px rgba(10,146,21,.12);
    }
    .case-seo-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 24px;
      margin-top: 28px;
    }
    .case-seo-card {
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,.08);
      padding: 28px;
      border-top: 3px solid #0a9215;
    }
    .case-seo-card h3 {
      color: #0a9215;
      font-family: "Poiret One", cursive;
      font-size: 29px;
      font-weight: 900;
      line-height: 1.22;
      margin-bottom: 14px;
      text-shadow: 1px 2px 3px #00000022;
    }
    .case-seo-card p, .case-seo-card li {
      color: #333;
      font-size: 16px;
      line-height: 1.7;
    }
    .case-seo-list {
      margin: 0;
      padding-left: 20px;
    }
    .case-price-note {
      margin-top: 28px;
      padding: 24px 28px;
      border-radius: 8px;
      background: #f0faf1;
      border-left: 4px solid #0a9215;
      line-height: 1.75;
    }
    .case-service-link {
      display: inline-block;
      margin-top: 18px;
      color: #0a9215;
      font-weight: 700;
      text-decoration: underline;
    }

    /* ── Gallery ──────────────────────────── */
    .slider2Top { padding: 0 !important; margin: 0 !important; }
    .swiper-slide-top {
      width: 100% !important;
      height: 500px !important;
      object-fit: cover;
    }
    .swiper-button-prev, .swiper-button-next { top: 35% !important; }
    .swiper-slide-bottom { height: 140px !important; object-fit: cover; }

    /* ── Related cards ────────────────────── */
    .casesCustom { background: #fff; border-top: 2px solid #0a9215; }

    /* ── CTA ──────────────────────────────── */
    .cta-block {
      text-align: center;
      background: #f9f9f9;
      padding: 40px;
      border-radius: 10px;
    }
    .cta-block h2 { font-weight: 700; margin-bottom: 35px; }
    .cta-block p  { margin-bottom: 30px; }
    .cta-form {
      display: flex;
      gap: 15px;
      justify-content: center;
      flex-wrap: wrap;
    }
    .cta-form input {
      padding: 15px;
      border: 1px solid #ddd;
      border-radius: 5px;
      min-width: 200px;
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
      transition: all .3s ease;
      border: 2px solid #0a9215;
      cursor: pointer;
    }
    .btn--primary-custom:hover { background: #0a7b12; border-color: #0a7b12; }

    /* ── FAQ ──────────────────────────────── */
    .faq-toggle {
      margin: 0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;
      font-weight: 700;
    }
    .faq-toggle span { font-size: 24px; margin-left: 20px; flex-shrink: 0; }
    .faq-answer { background: #fff; padding: 20px; border-top: 1px solid #ddd; }

    /* ── Section titles ───────────────────── */
    .section-title {
      text-align: center;
      color: #0a9215;
      font-family: "Poiret One", cursive;
      font-size: 40px;
      font-weight: 900;
      line-height: 1.2;
      margin-bottom: 40px;
      text-shadow: 1px 2px 3px #00000024;
    }

    /* ── Media ────────────────────────────── */
    @media (max-width: 768px) {
      .hero__breadcramps { flex-wrap: wrap; }
      .hero__buttons { display: grid; grid-gap: 10px; width: 100%; }
      .hero__buttons .openPopup { margin-left: auto !important; }
      .hero__title { font-size: 38px; }
      .hero__subtitle { font-size: 20px; text-align: center; }
      .hero { height: 80vh; }
      .swiper-slide-top { height: 300px !important; }
      .swiper-button-next, .swiper-button-next:after,
      .swiper-button-prev, .swiper-button-prev:after {
        display: block !important;
        top: 170px !important;
      }
      .swiper-button-next { right: 0 !important; }
      .swiper-button-prev  { left: 0 !important; }
      .cs-block { padding: 25px; }
      .case-facts { grid-template-columns: 1fr 1fr; }
      .case-seo-grid { grid-template-columns: 1fr; }
      .seo-text { padding: 26px 22px; }
      .cta-form { flex-direction: column; align-items: center; }
      .cta-form input { width: 100%; min-width: auto; }
      .btn--primary-custom { width: 100%; }
      .section-title { font-size: 31px; }
    }
    @media (max-width: 480px) {
      .hero__title { font-size: 24px; line-height: 1.2; }
      .hero__subtitle { font-size: 16px; line-height: 1.4; }
      .case-facts { grid-template-columns: 1fr; }
      .cs-block { padding: 20px; }
      .cs-block h3 { font-size: 28px; }
      .seo-text { padding: 24px 18px; }
      .seo-text h2 { font-size: 29px; }
      .seo-text h3,
      .case-seo-card h3 { font-size: 25px; }
    }
  </style>
</head>
<body>

  <!-- ═══ HEADER ═══════════════════════════════════════════ -->
  <header class="header wrapper">
    <a class="header__logo-wrap" href="<?php echo get_home_url(); ?>">
      <img class="header__logo" src="<?php echo get_template_directory_uri(); ?>/img/logo4.webp" alt="" role="presentation" />
    </a>
    <nav class="menu">
      <ul class="menu__list">
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(921); ?>">Услуги</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(160); ?>">Работы</a></li>
        <li class="menu__about-list-wrap"><a class="menu__about-link hover-link" href="<?php echo get_permalink(181); ?>">О компании</a>
          <ul class="menu__about-list">
            <li class="menu__about-item hover-link1"><a class="menu__about-link" href="<?php echo get_permalink(7679); ?>">Вакансии</a></li>
          </ul>
        </li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(9973); ?>">Цены / Расчет</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(227); ?>">Контакты</a></li>
      </ul>
    </nav>
    <div class="header__links">
      <div class="header__phone-wrap">
        <a class="header__phone" href="tel:89159788809">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="20" height="20">
            <circle class="active-path" cx="150" cy="226.1" r="11.7" fill="#a2f9a9"></circle>
            <path class="active-path svg-path" d="M182.7 68.2h-65.4a6.5 6.5 0 00-6.6 6.4v123.6c0 3.5 3 6.3 6.6 6.3h65.4c3.7 0 6.6-2.8 6.6-6.3V74.6c0-3.5-3-6.4-6.6-6.4z" fill="#a2f9a9"></path>
            <path class="active-path svg-path" d="M150 0a150 150 0 100 300 150 150 0 000-300zm58.4 224c0 11.5-9.3 20.8-20.8 20.8h-75.2A20.8 20.8 0 0191.6 224V75.3c0-11.4 9.3-20.7 20.8-20.7h75.2c11.5 0 20.8 9.3 20.8 20.7V224z" fill="#a2f9a9"></path>
          </svg>
          <span class="header__number">8(915)-978-88-09</span>
        </a>
        <div class="header__time-wrap">
          <svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 0 443.3 443.3" width="20">
            <path class="active-path svg-path" d="M221.6 0C99.4 0 0 99.4 0 221.6s99.4 221.7 221.6 221.7 221.7-99.4 221.7-221.7S343.9 0 221.6 0zm0 415.6c-106.9 0-193.9-87-193.9-194s87-193.9 194-193.9 193.9 87 193.9 194-87 193.9-194 193.9z" fill="#a2f9a9"></path>
            <path class="active-path svg-path" d="M235.5 83.1h-27.7v144.3l87.2 87.2 19.6-19.6-79.1-79z" fill="#a2f9a9"></path>
          </svg>
          <span class="header__time">Пн-Вс: 09:00 - 21:00</span>
        </div>
      </div>
      <div class="header__socials">
        <a class="header__social-link" target="_blank" href="https://vk.com/exp_76">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 97.8 97.8">
            <path class="active-path svg-path" d="M48.9 0a48.9 48.9 0 100 97.8 48.9 48.9 0 000-97.8zm24.8 54.2c2.2 2.2 4.7 4.3 6.7 6.7 1 1.1 1.8 2.2 2.4 3.5 1 1.8.1 3.8-1.5 3.9h-10c-2.6.2-4.7-.8-6.4-2.6l-4-4.4a9.4 9.4 0 00-1.8-1.6c-1.4-.9-2.6-.6-3.3.8-.8 1.5-1 3-1.1 4.7-.1 2.4-.8 3-3.2 3a25.6 25.6 0 01-24-12c-5.1-7-9-14.7-12.7-22.6-.8-1.8-.2-2.8 1.8-2.8h9.8c1.3 0 2.2.8 2.7 2 1.8 4.4 4 8.5 6.7 12.3.7 1 1.4 2 2.5 2.8 1.1.8 2 .5 2.6-.8a38.6 38.6 0 00.4-11.6C41 33.6 40 32.4 38 32c-1-.1-.8-.5-.4-1 .8-1 1.6-1.6 3.1-1.6h11.3c1.8.4 2.2 1.2 2.4 3v12.5c0 .7.4 2.8 1.6 3.3 1 .3 1.7-.5 2.3-1.2 2.7-2.8 4.6-6.2 6.4-9.7l2-4.8c.5-1.2 1.3-1.8 2.6-1.8h10.9l1 .1c1.8.3 2.3 1.1 1.7 2.9-.9 2.8-2.6 5.2-4.3 7.5l-5.6 7.5c-1.6 2.3-1.5 3.5.6 5.5z" fill="#a2f9a9"></path>
          </svg>
          <span class="header__link-name">ВКонтакте</span>
        </a>
      </div>

      <a class="header__cta openPopup" href="#header-popup" data-modal="#header-popup">Рассчитать участок</a>
      </div>

    <button class="burger" aria-label="open"><span class="burger__icon"></span></button>
  </header>
  <?php if (function_exists('land76_render_header_popup')) { land76_render_header_popup(); } ?>


  <div class="page-content">
    <main class="main">

      <!-- ═══ 1. HERO ════════════════════════════════════ -->
      <section class="hero">
        <div class="hero__scene" id="scene">
          <div class="hero__bg" data-depth="0.4"></div>
        </div>
        <div class="hero__content wrapper">
          <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800">
            <?php echo esc_html($cs87_hero_title); ?>
          </h1>
          <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900">
            <?php echo esc_html($cs87_hero_subtitle); ?>
          </p>
          <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
            <?php if ($cs87_hero_btn_primary_text) : ?>
              <a href="<?php echo esc_url($cs87_hero_btn_primary_url ?: '#gallery'); ?>" class="hero__btn">
                <?php echo esc_html($cs87_hero_btn_primary_text); ?>
              </a>
            <?php else : ?>
              <a href="#gallery" class="hero__btn">Смотреть фото</a>
            <?php endif; ?>
            <?php if ($cs87_hero_btn_secondary_text) : ?>
              <a href="<?php echo esc_url($cs87_hero_btn_secondary_url ?: '#popup'); ?>" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;">
                <?php echo esc_html($cs87_hero_btn_secondary_text); ?>
              </a>
            <?php else : ?>
              <a class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;">Заказать звонок</a>
            <?php endif; ?>
          </div>
          <div class="hero__breadcramps">
            <a class="hero__home" href="<?php echo get_home_url(); ?>">Компания «Эксперты» | </a>
            <a class="hero__home" href="<?php echo get_permalink(160); ?>">Фотогалерея | </a>
            <span class="hero__active-page"><?php echo esc_html($cs87_hero_title); ?></span>
          </div>
        </div>
        <div class="animation-wrap">
          <img style="margin-left:100px" class="animation-wrap__img" src="<?php echo get_template_directory_uri(); ?>/img/mouse.png" alt="" role="presentation" />
          <span class="animation-wrap__text">Листайте</span>
        </div>

        <!-- Popup form -->
        <div class="formWrapper" id="popup">
          <form class="form">
            <p class="form__title">Заполните форму</p>
            <label class="form__label"><p>Имя или название организации *</p><input class="form__input" type="text" name="name" required /></label>
            <label class="form__label"><p>Контактный телефон *</p><input class="form__input" type="text" name="phone" required /></label>
            <div class="formConsent">
              <label class="formConsent__container"><input class="formConsent__input" type="checkbox" required /><span class="formConsent__checkbox"><svg class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px"><path d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928C170.827,363.533,162.165,366.839,153.504,366.839z" fill="#B22917"></path></svg></span></label>
              <p class="formConsent__text">Я ознакомлен и согласен с <a href="/privacy/">политикой конфиденциальности</a> оператора, подтверждаю свое <a href="/consent/">согласие</a> на обработку введенных мною персональных данных</p>
            </div>
            <button class="form__btn btn" type="submit">Отправить</button>
          </form>
          <div class="ajaxMessage">
            <div class="ajaxMessage__success">
              <div class="ajaxMessage__title"><p>Спасибо!</p><p>Ваша заявка принята</p></div>
              <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время, чтобы обсудить детали и ответить на вопросы</div>
            </div>
            <div class="ajaxMessage__error">
              <div class="ajaxMessage__title">Ошибка при отправке!</div>
              <div class="ajaxMessage__text">Попробуйте позднее</div>
            </div>
            <button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
          </div>
        </div>
      </section>

      <!-- ═══ 2. PROJECT FACTS ══════════════════════════ -->
      <?php if (!empty($cs87_facts)) : ?>
      <section class="services wrapper">
        <h2 class="section-title" data-aos="fade-up">О проекте</h2>
        <div class="case-facts" data-aos="fade-up" data-aos-duration="500">
          <?php foreach ($cs87_facts as $fact) : ?>
          <div class="case-fact">
            <div class="case-fact__label"><?php echo esc_html($fact['label']); ?></div>
            <div class="case-fact__value"><?php echo esc_html($fact['value']); ?></div>
          </div>
          <?php endforeach; ?>
        </div>
      </section>
      <?php endif; ?>

      <!-- ═══ 3. PHOTO GALLERY ══════════════════════════ -->
      <section class="services wrapper" id="gallery">
        <h2 class="section-title" data-aos="fade-up">Фотографии проекта</h2>

        <?php if (have_rows('slider')) : ?>
        <div class="slider2 slider2Top" data-aos="fade-up">
          <div class="swiper-wrapper">
            <?php while (have_rows('slider')) : the_row();
              $image = get_sub_field('image');
              if (!empty($image)) :
                $size_desktop = 'large';
                $size_mobile  = 'medium';
                $thumb_desktop = $image['sizes'][$size_desktop] ?? $image['url'];
                $thumb_mobile  = $image['sizes'][$size_mobile] ?? $image['url'];
                $alt = $image['alt'] ?: 'Фото проекта';
            ?>
              <img class="swiper-slide swiper-slide-top"
                   src="<?php echo esc_url($thumb_mobile); ?>"
                   srcset="<?php echo esc_url($thumb_mobile); ?> 768w, <?php echo esc_url($thumb_desktop); ?> 1200w"
                   sizes="(max-width: 768px) 768px, 1200px"
                   alt="<?php echo esc_attr($alt); ?>"
                   loading="lazy" />
            <?php endif;
            endwhile; ?>
          </div>
          <div class="swiper-button-next"></div>
          <div class="swiper-button-prev"></div>
        </div>

        <?php if (function_exists('reset_rows')) reset_rows(); ?>
        <div class="slider2-thumbs" style="margin-top: 10px;" data-aos="fade-up">
          <div class="swiper-wrapper">
            <?php while (have_rows('slider')) : the_row();
              $image = get_sub_field('image');
              if (!empty($image)) :
                $thumb = $image['sizes']['medium'] ?? $image['url'];
            ?>
              <img class="swiper-slide swiper-slide-bottom"
                   src="<?php echo esc_url($thumb); ?>"
                   alt="<?php echo esc_attr($image['alt'] ?? ''); ?>"
                   loading="lazy" />
            <?php endif;
            endwhile; ?>
          </div>
        </div>
        <?php else : ?>
          <p style="text-align:center; color:#777;">Фотографии проекта загружаются.</p>
        <?php endif; ?>
      </section>

      <!-- ═══ 4. PROJECT DESCRIPTION (the_content) ═════ -->
      <section class="services wrapper">
        <div class="seo-text" style="line-height:1.8; margin-bottom:40px;" data-aos="fade-up">
          <?php the_content(); ?>
        </div>
      </section>

      <?php if ($cs87_intro_title || $cs87_intro_text || $cs87_technology_text || $cs87_result_text || $cs87_scope_items || $cs87_price_note) : ?>
      <section class="services wrapper">
        <?php if ($cs87_intro_title || $cs87_intro_text) : ?>
          <h2 class="section-title" data-aos="fade-up"><?php echo esc_html($cs87_intro_title ?: 'Описание проекта'); ?></h2>
          <?php if ($cs87_intro_text) : ?>
            <div class="seo-text" style="line-height:1.8; margin-bottom:34px;" data-aos="fade-up">
              <p><?php echo esc_html($cs87_intro_text); ?></p>
            </div>
          <?php endif; ?>
        <?php endif; ?>

        <div class="case-seo-grid">
          <?php if ($cs87_technology_title || $cs87_technology_text) : ?>
          <div class="case-seo-card" data-aos="fade-up">
            <h3><?php echo esc_html($cs87_technology_title ?: 'Технология работ'); ?></h3>
            <p><?php echo esc_html($cs87_technology_text); ?></p>
          </div>
          <?php endif; ?>

          <?php if ($cs87_result_title || $cs87_result_text) : ?>
          <div class="case-seo-card" data-aos="fade-up">
            <h3><?php echo esc_html($cs87_result_title ?: 'Результат'); ?></h3>
            <p><?php echo esc_html($cs87_result_text); ?></p>
          </div>
          <?php endif; ?>

          <?php if ($cs87_scope_title || !empty($cs87_scope_items)) : ?>
          <div class="case-seo-card" data-aos="fade-up">
            <h3><?php echo esc_html($cs87_scope_title ?: 'Что учесть при заказе'); ?></h3>
            <?php if (!empty($cs87_scope_items) && is_array($cs87_scope_items)) : ?>
            <ul class="case-seo-list">
              <?php foreach ($cs87_scope_items as $scope_item) :
                $scope_text = is_array($scope_item) ? ($scope_item['item'] ?? '') : $scope_item;
                if (!$scope_text) continue;
              ?>
                <li><?php echo esc_html($scope_text); ?></li>
              <?php endforeach; ?>
            </ul>
            <?php endif; ?>
          </div>
          <?php endif; ?>

          <?php if ($cs87_price_note) : ?>
          <div class="case-seo-card" data-aos="fade-up">
            <h3>Цена и расчет похожего проекта</h3>
            <p><?php echo esc_html($cs87_price_note); ?></p>
            <?php if ($cs87_service_url) : ?>
              <a class="case-service-link" href="<?php echo esc_url($cs87_service_url); ?>">Перейти к услуге</a>
            <?php endif; ?>
          </div>
          <?php endif; ?>
        </div>
      </section>
      <?php endif; ?>

      <!-- ═══ 5. CHALLENGE / SOLUTION ═════════════════ -->
      <?php if ($cs87_challenge_title || $cs87_challenge_text || $cs87_solution_title || $cs87_solution_text) : ?>
      <section class="services wrapper">
        <?php if ($cs87_challenge_title || $cs87_challenge_text) : ?>
        <div class="cs-block cs-block--challenge" data-aos="fade-right">
          <h3><?php echo esc_html($cs87_challenge_title ?: 'Задача'); ?></h3>
          <p><?php echo esc_html($cs87_challenge_text ?: ''); ?></p>
        </div>
        <?php endif; ?>

        <?php if ($cs87_solution_title || $cs87_solution_text) : ?>
        <div class="cs-block cs-block--solution" data-aos="fade-left">
          <h3><?php echo esc_html($cs87_solution_title ?: 'Решение'); ?></h3>
          <p><?php echo esc_html($cs87_solution_text ?: ''); ?></p>
        </div>
        <?php endif; ?>
      </section>
      <?php endif; ?>

      <!-- ═══ 6. RELATED CASES ════════════════════════ -->
      <?php if (!empty($cs87_related_cases) && is_array($cs87_related_cases)) : ?>
      <section class="services wrapper casesCustom">
        <h2 class="section-title" data-aos="fade-up">Похожие проекты</h2>
        <div class="services__cards columns3">
          <?php foreach ($cs87_related_cases as $related_id) :
            $related_post = get_post($related_id);
            if (!$related_post) continue;
            $related_thumb = get_the_post_thumbnail_url($related_id, 'medium');
            if (!$related_thumb) $related_thumb = 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp';
          ?>
          <div class="service" data-aos="fade-up" data-aos-duration="400">
            <div class="service__img-wrap">
              <img class="service__img" src="<?php echo esc_url($related_thumb); ?>" alt="<?php echo esc_attr(get_the_title($related_id)); ?>" loading="lazy" />
            </div>
            <div class="service__text-wrap">
              <h3 class="service__title"><?php echo esc_html(get_the_title($related_id)); ?></h3>
              <p><?php echo esc_html(wp_trim_words(get_the_excerpt($related_id) ?: get_post_field('post_content', $related_id), 15)); ?></p>
              <div class="service__link-wrap">
                <a class="service__link" href="<?php echo esc_url(get_permalink($related_id)); ?>">Подробнее</a>
              </div>
            </div>
          </div>
          <?php endforeach; ?>
        </div>
      </section>
      <?php endif; ?>

      <!-- ═══ 7. FAQ ══════════════════════════════════ -->
      <section class="services wrapper">
        <h2 class="section-title" data-aos="fade-up">
          <?php echo esc_html($cs87_faq_title ?: 'Частые вопросы'); ?>
        </h2>
        <div style="margin-bottom: 30px;" data-aos="fade-up">
          <?php foreach ($cs87_faq_items as $cs87_faq_item) : ?>
          <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
            <div style="background: #f5f5f5; padding: 20px; cursor: pointer;"
                 onclick="var a=this.nextElementSibling;a.style.display=a.style.display==='block'?'none':'block';var i=this.querySelector('.faq-icon');i.textContent=i.textContent==='+'?'-':'+';">
              <h3 class="faq-toggle">
                <span><?php echo esc_html($cs87_faq_item['question'] ?? ''); ?></span>
                <span class="faq-icon" style="font-size:24px; color:#0a9215;">+</span>
              </h3>
            </div>
            <div class="faq-answer" style="display: none;">
              <p><?php echo esc_html($cs87_faq_item['answer'] ?? ''); ?></p>
            </div>
          </div>
          <?php endforeach; ?>
        </div>
      </section>

      <!-- ═══ 8. CTA ══════════════════════════════════ -->
      <section class="services wrapper">
        <div class="cta-block" data-aos="fade-up">
          <h2>Хотите такой же результат?</h2>
          <p>Оставьте заявку — приедем, осмотрим объект и подготовим смету за 1 день.</p>
          <form class="cta-form" id="cta-case">
            <input type="text" name="name" placeholder="Ваше имя" required />
            <input type="tel" name="phone" placeholder="Ваш телефон" required />
            <button type="submit" class="btn--primary-custom">Получить расчёт</button>
          </form>
        </div>
      </section>

    </main>
  </div>

  <!-- ═══ FOOTER ══════════════════════════════════════════ -->
  <footer class="footer wrapper">
    <img class="footer__logo" src="<?php echo get_template_directory_uri(); ?>/img/logo4.webp" alt="" role="presentation" />
    <div class="footer__services-wrap">
      <span class="footer__title">Услуги</span>
      <ul class="footer__services columns2">
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/services/landshaftnoe-proektirovanie/">Ландшафтное проектирование</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/drenazh-uchastka/">Дренаж участка</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/ukladka-trotuarnoy-plitki/">Укладка тротуарной плитки</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/livnevaya-kanalizatsiya/">Ливневая канализация</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/services/posadka-derevev-i-kustarnikov/">Посадка деревьев и кустарников</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/avtopoliv-na-uchastke/">Системы автоматического полива</a></li>
      </ul>
    </div>
    <div class="footer__wrap">
      <a class="footer__number" href="tel:89159788809">
        <span class="footer__number">8(915)-978-88-09</span>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="20" height="20">
          <circle class="active-path" cx="150" cy="226.1" r="11.7" fill="#a2f9a9"></circle>
          <path class="active-path svg-path" d="M182.7 68.2h-65.4a6.5 6.5 0 00-6.6 6.4v123.6c0 3.5 3 6.3 6.6 6.3h65.4c3.7 0 6.6-2.8 6.6-6.3V74.6c0-3.5-3-6.4-6.6-6.4z" fill="#a2f9a9"></path>
          <path class="active-path svg-path" d="M150 0a150 150 0 100 300 150 150 0 000-300zm58.4 224c0 11.5-9.3 20.8-20.8 20.8h-75.2A20.8 20.8 0 0191.6 224V75.3c0-11.4 9.3-20.7 20.8-20.7h75.2c11.5 0 20.8 9.3 20.8 20.7V224z" fill="#a2f9a9"></path>
        </svg>
      </a>
      <span class="footer__copiryght">© 2018 Компания «Эксперты»</span>
    </div>
  </footer>

  <!-- ═══ SCRIPTS ════════════════════════════════════════ -->
  <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/parallax/3.1.0/parallax.min.js"></script>
  <script src="https://unpkg.com/swiper/swiper-bundle.js"></script>
  <script src="<?php bloginfo('template_directory'); ?>/js/main.js?v=20260511"></script>

  <!-- Yandex.Metrika counter -->
  <script type="text/javascript">
    (function(d,w,c){(w[c]=w[c]||[]).push(function(){try{w.yaCounter42305934=new Ya.Metrika({id:42305934,clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true})}catch(e){}});
    var n=d.getElementsByTagName("script")[0],s=d.createElement("script"),f=function(){n.parentNode.insertBefore(s,n)};
    s.type="text/javascript";s.async=true;s.src="https://mc.yandex.ru/metrika/watch.js";
    if(w.opera=="[object Opera]"){d.addEventListener("DOMContentLoaded",f,false)}else{f()}})(document,window,"yandex_metrika_callbacks");
  </script>
  <noscript><div><img src="https://mc.yandex.ru/watch/42305934" style="position:absolute;left:-9999px" alt="" /></div></noscript>

  <script type="application/ld+json"><?php echo wp_json_encode($cs87_schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); ?></script>
  <?php wp_footer(); ?>
</body>
</html>
