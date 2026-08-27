<!DOCTYPE html>
<html lang="ru">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport"
    content="width=device-width, height=device-height, initial-scale=1.0, user-scalable=no, maximum-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="yandex-verification" content="697af42ad3d96f49" />
  <!-- <link rel="stylesheet" href="css/styles.css" />
  <link rel="stylesheet" href="css/index.css" /> -->

<?php wp_head();?>
  <?php if ( is_front_page() ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/index.css" />

    <?php elseif ( is_page('Услуги') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/services.css" />

    <?php elseif ( is_page('Фотогалерея') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/portfolio.css" />

    <?php elseif ( is_page('Калькулятор услуг') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/calc.css" />

    <?php elseif ( is_page('Полезное') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/blog.css" />

    <?php elseif ( is_page('О нас') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/about.css" />

    <?php elseif ( is_page('Контакты') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/contacts.css" />

    <?php elseif ( is_page('Вакансии') ): ?>
      <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/job.css" />

    <?php endif; ?>

<meta property = "og:type" content = "website" />
<meta property = "og:url" content = "<?php echo get_permalink(); ?>" />
<meta property="og:image" content="<?php echo esc_url(function_exists('land76_service_v2_hero_image_url') ? land76_service_v2_hero_image_url('https://exp76.ru/wp-content/themes/land76wp/img/h11.jpg') : 'https://exp76.ru/wp-content/themes/land76wp/img/h11.jpg'); ?>" />




</head>

<body>

  <header class="header wrapper"><a class="header__logo-wrap" href="<?php echo get_home_url(); ?>"><img class="header__logo" src="<?php echo get_template_directory_uri() ?>/img/logo4.webp"
        alt="" role="presentation" /></a>
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
      <div class="header__phone-wrap"><a class="header__phone" href="tel:89159788809"><svg
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="20" height="20">
            <circle class="active-path" cx="150" cy="226.1" r="11.7" data-original="#000000" data-old_color="#000000"
              fill="#a2f9a9"></circle>
            <path class="active-path svg-path"
              d="M182.7 68.2h-65.4a6.5 6.5 0 00-6.6 6.4v123.6c0 3.5 3 6.3 6.6 6.3h65.4c3.7 0 6.6-2.8 6.6-6.3V74.6c0-3.5-3-6.4-6.6-6.4z"
              data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
            <path class="active-path svg-path"
              d="M150 0a150 150 0 100 300 150 150 0 000-300zm58.4 224c0 11.5-9.3 20.8-20.8 20.8h-75.2A20.8 20.8 0 0191.6 224V75.3c0-11.4 9.3-20.7 20.8-20.7h75.2c11.5 0 20.8 9.3 20.8 20.7V224z"
              data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
          </svg><span class="header__number">8(915)-978-88-09</span></a>
        <div class="header__time-wrap"> <svg xmlns="http://www.w3.org/2000/svg" height="20" viewBox="0 0 443.3 443.3"
            width="20">
            <path class="active-path svg-path"
              d="M221.6 0C99.4 0 0 99.4 0 221.6s99.4 221.7 221.6 221.7 221.7-99.4 221.7-221.7S343.9 0 221.6 0zm0 415.6c-106.9 0-193.9-87-193.9-194s87-193.9 194-193.9 193.9 87 193.9 194-87 193.9-194 193.9z"
              data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
            <path class="active-path svg-path" d="M235.5 83.1h-27.7v144.3l87.2 87.2 19.6-19.6-79.1-79z"
              data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
          </svg><span class="header__time">Пн-Вс: 09:00 - 21:00</span></div>
      </div>

      <div class="header__socials">

        <a class="header__social-link"  target="_blank" href="https://vk.com/exp_76"><svg xmlns="http://www.w3.org/2000/svg"
            width="20" height="20" viewBox="0 0 97.8 97.8">
            <path class="active-path svg-path"
              d="M48.9 0a48.9 48.9 0 100 97.8 48.9 48.9 0 000-97.8zm24.8 54.2c2.2 2.2 4.7 4.3 6.7 6.7 1 1.1 1.8 2.2 2.4 3.5 1 1.8.1 3.8-1.5 3.9h-10c-2.6.2-4.7-.8-6.4-2.6l-4-4.4a9.4 9.4 0 00-1.8-1.6c-1.4-.9-2.6-.6-3.3.8-.8 1.5-1 3-1.1 4.7-.1 2.4-.8 3-3.2 3a25.6 25.6 0 01-24-12c-5.1-7-9-14.7-12.7-22.6-.8-1.8-.2-2.8 1.8-2.8h9.8c1.3 0 2.2.8 2.7 2 1.8 4.4 4 8.5 6.7 12.3.7 1 1.4 2 2.5 2.8 1.1.8 2 .5 2.6-.8a38.6 38.6 0 00.4-11.6C41 33.6 40 32.4 38 32c-1-.1-.8-.5-.4-1 .8-1 1.6-1.6 3.1-1.6h11.3c1.8.4 2.2 1.2 2.4 3v12.5c0 .7.4 2.8 1.6 3.3 1 .3 1.7-.5 2.3-1.2 2.7-2.8 4.6-6.2 6.4-9.7l2-4.8c.5-1.2 1.3-1.8 2.6-1.8h10.9l1 .1c1.8.3 2.3 1.1 1.7 2.9-.9 2.8-2.6 5.2-4.3 7.5l-5.6 7.5c-1.6 2.3-1.5 3.5.6 5.5z"
              data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
          </svg><span class="header__link-name">ВКонтакте</span></a>

</div>

      <a class="header__cta openPopup" href="#header-popup" data-modal="#header-popup">Рассчитать участок</a>
      </div>

    <button class="burger" aria-label="open"><span class="burger__icon"></span></button>

  </header>
  <?php if (function_exists('land76_render_header_popup')) { land76_render_header_popup(); } ?>



  <div class="page-content">
    <main class="main">
