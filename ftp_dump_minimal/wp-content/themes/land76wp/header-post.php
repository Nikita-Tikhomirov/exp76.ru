<!DOCTYPE html>
<html lang="ru">

<head>
  <meta charset="UTF-8" />
  <meta name="viewport"
    content="width=device-width, height=device-height, initial-scale=1.0, user-scalable=no, maximum-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="yandex-verification" content="697af42ad3d96f49" />
  <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
  <link link rel="stylesheet" href="https://unpkg.com/swiper/swiper-bundle.css">
  <link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/post.css" />
	<?php wp_head();?>

<meta property = "og:type" content = "website" />
<meta property = "og:url" content = "<?php echo get_permalink(); ?>" />
<meta property = "og:image" content = "https://exp76.ru/wp-content/themes/land76wp/img/h11.jpg" />
	
</head>

<body>
  <header class="header wrapper"><a class="header__logo-wrap" href="<?php echo get_home_url(); ?>"><img class="header__logo" src="<?php echo get_template_directory_uri() ?>/img/logo4.png"
        alt="" role="presentation" /></a>
    <nav class="menu">
      <ul class="menu__list">
        <li class="menu__item"><a class="menu__link" href="<?php echo get_home_url(); ?>">Главная</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(921); ?>">Услуги</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(160); ?>">Фотогалерея</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(9973); ?>">Калькулятор услуг</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(9962); ?>">Полезное</a></li>
        <li class="menu__item"><a class="menu__link" href="<?php echo get_permalink(227); ?>">Контакты</a></li>
        <li class="menu__about-list-wrap"><a class="menu__about-link hover-link" href="<?php echo get_permalink(181); ?>">О нас</a>
          <ul class="menu__about-list">
            <li class="menu__about-item hover-link1"><a class="menu__about-link" href="<?php echo get_permalink(7679); ?>">Вакансии</a></li>
          </ul>
        </li>
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
          
          <a class="header__social-link"  target="_blank" href="https://www.facebook.com/groups/exp76/?ref=share"><svg
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 167.7 167.7" width="20" height="20">
            <path class="active-path svg-path"
              d="M83.8.3a83.8 83.8 0 00-14 166.4v-65H49.6V78.2h20.2V61c0-20 12.3-31 30.2-31 8.5 0 15.9.7 18 1v20.9h-12.4C96 51.9 94 56.5 94 63.3v15h23.2l-3 23.4H94v65.6A83.8 83.8 0 0083.8.3z"
              data-original="#010002" data-old_color="#010002" fill="#a2f9a9"></path>
          </svg><span class="header__link-name">Facebook</span></a>
          
          <a class="header__social-link"  target="_blank" href="https://www.instagram.com/exp_76/?igshid=e2jlt4ojs5qq"><svg
            xmlns="http://www.w3.org/2000/svg" viewBox="0 0 89.8 89.8" width="20" height="20">
            <path class="active-path svg-path"
              d="M58.3 23.9H31.5a7.8 7.8 0 00-7.7 7.7v26.8c0 4.2 3.4 7.7 7.7 7.7h26.8c4.2 0 7.7-3.5 7.7-7.7V31.6c0-4.2-3.5-7.7-7.7-7.7zm-13.4 35a14 14 0 110-27.8 14 14 0 010 27.8zm14.3-25a3.3 3.3 0 110-6.5 3.3 3.3 0 010 6.6z"
              data-original="#6A453B" data-old_color="#6A453B" fill="#a2f9a9"></path>
            <path class="active-path svg-path" d="M44.9 37a8 8 0 100 16 8 8 0 000-16z" data-original="#6A453B"
              data-old_color="#6A453B" fill="#a2f9a9"></path>
            <path class="active-path svg-path"
              d="M44.9 0a44.9 44.9 0 100 89.8 44.9 44.9 0 000-89.8zm27 58.4c0 7.5-6.1 13.6-13.6 13.6H31.5c-7.5 0-13.6-6.1-13.6-13.6V31.6c0-7.5 6-13.6 13.6-13.6h26.8c7.5 0 13.6 6.1 13.6 13.6v26.8z"
              data-original="#6A453B" data-old_color="#6A453B" fill="#a2f9a9"></path>
          </svg><span class="header__link-name">Instagram</span></a></div>
      </div>
    
    <button class="burger" aria-label="open"><span class="burger__icon"></span></button>
    <?php wp_head() ?>
  </header>

  <div class="page-content">
    <main class="main">

      <section class="hero">
        <div class="hero__scene" id="scene">
          <div class="hero__bg" data-depth="0.4"></div>
        </div>
        <div class="hero__content wrapper">
          <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php the_title();?></h1><a
            class="hero__btn openPopup" data-modal="#popup" data-aos="fade-up" data-aos-duration="10000">Заказать
            звонок</a>

          <div class="hero__breadcramps"><a class="hero__home" href="<?php echo get_home_url(); ?>">Компания "Эксперты"
              | </a><a class="hero__home" href="<?php echo get_permalink(9962); ?>">Полезное | </a><span
              class="hero__active-page"><?php the_title();?></span></div>
        </div>

                <div class="animation-wrap"><img style="margin-left:100px" class="animation-wrap__img" src="<?php echo get_template_directory_uri() ?>/img/mouse.png" alt=""
            role="presentation" /><span class="animation-wrap__text">Листайте</span></div>

        <div class="formWrapper" id="popup">
          <form class="form">
            <p class="form__title">Заполните форму</p><label class="form__label">
              <p>Имя или название организации *</p><input class="form__input" type="text" name="name" placeholder=""
                required="required" />
            </label><label class="form__label">
              <p>Контактный телефон *</p><input class="form__input" type="text" name="phone" placeholder=""
                required="required" />
            </label>
            <div class="formConsent"><label class="formConsent__container"><input class="formConsent__input"
                  type="checkbox" required="required" /><span class="formConsent__checkbox"><svg
                    class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px">
                    <path
                      d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265  c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386  c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928  C170.827,363.533,162.165,366.839,153.504,366.839z"
                      fill="#B22917"></path>
                  </svg></span></label>
              <p class="formConsent__text">Я ознакомлен и согласен с <a href="privacy.html">политикой конфиденциальности
                </a>оператора, подтверждаю свое <a href="consent.html">согласие </a>на обработку введенных мною
                персональных данных</p>
            </div><button class="form__btn btn" type="submit">Отправить</button>
          </form>
          <div class="ajaxMessage">
            <div class="ajaxMessage__success">
              <div class="ajaxMessage__title">
                <p>Спасибо!</p>
                <p>Ваша заявка принята</p>
              </div>
              <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время, что бы обсудить детали и ответить на
                вопросы</div>
            </div>
            <div class="ajaxMessage__error">
              <div class="ajaxMessage__title">Ошибка при отправке!</div>
              <div class="ajaxMessage__text">Попробуйте позднее</div>
            </div><button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
          </div>
        </div>
      </section>