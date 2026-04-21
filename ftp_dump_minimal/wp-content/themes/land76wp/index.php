<?php
/*
Template Name: Главная страница
*/
?>
<?php get_header(); ?>


<section class="services wrapper">
  <h2 class="services__title">Услуги </h2>
  <div class="services__cards columns3">

    <?php

    $posts = get_posts(array(
      'numberposts' => -1,
      'category' => 74,
      'orderby' => 'date',
      'order' => 'DESC',
      'include' => array(),
      'exclude' => array(),
      'meta_key' => '',
      'meta_value' => '',
      'post_type' => 'page',
      'suppress_filters' => true, // подавление работы фильтров изменения SQL запроса
    ));

    foreach ($posts as $post) {
      setup_postdata($post);
      // формат вывода the_title() ...
    


      ?>
      <div class="service" data-aos="fade-up" data-aos-duration="400">

        <div class="service__img-wrap">
          <img class="service__img" src="<?php the_post_thumbnail_url(); ?>" alt="" role="presentation" />
        </div>

        <div class="service__text-wrap">

          <h5 class="service__title"><?php the_title() ?></h5>

          <?php the_excerpt() ?>

        </div>

        <div class="service__link-wrap">
          <a class="service__link" href="<?php the_permalink() ?>">Подробнее</a>
        </div>

      </div>


      <?php
    }

    wp_reset_postdata(); // сброс
    
    ?>



  </div>

</section>

<style>
  @media only screen and (max-width: 767px) {
    .case .case__img-wrap {
      height: 300px !important;
    }
  }
</style>

<section class="portfolio wrapper">

  <div class="portfolio__bg-left" data-aos="fade-right" data-aos-duration="600"><img
      src="<?php echo get_template_directory_uri() ?>/img/bg-left.png"></div>

  <h2 class="portfolio__title" data-aos="fade-right" data-aos-duration="700">Наши работы </h2>
  <?php
  $posts = get_posts([
    'numberposts' => -1,
    'category' => 75,
    'orderby' => 'date',
    'order' => 'DESC',
    'post_type' => 'page',
    'suppress_filters' => true,
  ]);

  if ($posts): ?>

    <div class="cont">
      <div class="portfolio-slider gallery-top">
        <div class="swiper-wrapper">
          <?php foreach ($posts as $post):
            setup_postdata($post);
            $thumb = get_the_post_thumbnail_url($post, 'large');
            ?>
            <div class="case swiper-slide">
              <div class="case__img-wrap">
                <img class="case__img" src="<?php echo esc_url($thumb); ?>" alt="" role="presentation" />
              </div>
              <div class="case__content">
                <p class="case__title"><?php the_title(); ?></p>
                <div class="case__description"><?php the_excerpt(); ?></div>
                <a class="case__link" href="<?php the_permalink(); ?>">Подробнее</a>
              </div>
            </div>
          <?php endforeach; ?>
        </div>
      </div>
      <div class="swiper-button-next"></div>
      <div class="swiper-button-prev"></div>
    </div>

    <div class="gallery-thumbs">
      <div class="swiper-wrapper">
        <?php foreach ($posts as $post):
          setup_postdata($post);
          $thumb_small = get_the_post_thumbnail_url($post, 'thumbnail');
          ?>
          <div class="swiper-slide">
            <img class="gallery-thumbs__img" src="<?php echo esc_url($thumb_small); ?>" alt="" role="presentation" />
          </div>
        <?php endforeach; ?>
      </div>
    </div>

    <?php
    wp_reset_postdata();
  endif;
  ?>


  <a class="portfolio__link" href="#">Посмотреть все работы</a>
</section>

<section class="about wrapper">
  <h2 class="about__title" data-aos="fade-right" data-aos-duration="600">О нас</h2>
  <div class="about__wrap">
    <p class="about__text" data-aos="fade-right" data-aos-duration="800">Мы поможем вам сформировать уникальную
      концепцию в соответствии с особенностями территории или участка, поможем в закупке растений, создадим зону
      отдыха, разобьем цветник или рокарий, посадим зелёный газон, построим беседку и барбекю комплекс, оформим
      патио, построим водоём, проведём систему автоматического полива и подключим освещение участка. Скажите нам,
      каким вы видите свой сад, и мы сделаем его таким! В нашей компании «ЭКСПЕРТЫ» трудятся специалисты разных
      направлений, благодаря чему мы можем сделать ландшафтный дизайн под ключ, от разработки до воплощения,
      включая прокладку дренажей и ливневых систем, строительство фундамента, возведение отмостки вокруг строений,
      оформление парковок и въездов на участок, возведение заборов, ограждений, въездных групп, садовых дорожек.
    </p>
    <div class="about__logo-wrap" data-aos="fade-up" data-aos-duration="1000">
      <img class="about__logo" src="<?php echo get_template_directory_uri() ?>/img/al2.png" alt=""
        role="presentation" />
      <div class="about__logo-text">
        <p class="about__name">ЭКСПЕРТЫ</p>
        <p class="about__logo-desc">Ландшафтно-строительная компания</p>
      </div>
    </div>
  </div>
  <div class="about__how">
    <div class="about__step">
      <div class="about__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" height="512" viewBox="0 0 64 64" width="512">
          <path class="active-path"
            d="M36 11.05V5a3 3 0 00-3-3H5a3 3 0 00-3 3v54a3 3 0 003 3h28a3 3 0 003-3v-6.05a20.97 20.97 0 000-41.9zM28.72 4l-.31 1.24a1 1 0 01-.97.76H10.56a1 1 0 01-.97-.76L9.28 4zM34 59a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1h2.22l.43 1.73A3 3 0 0010.56 8h16.88a3 3 0 002.91-2.27L30.78 4H33a1 1 0 011 1v6.05a20.97 20.97 0 000 41.9zm12-11.54a18.86 18.86 0 01-22 0V34a1 1 0 011-1h1.62a13.2 13.2 0 0016.76 0H45a1 1 0 011 1zm2-1.64V34a3 3 0 00-3-3h-2a1 1 0 00-.68.27 11.18 11.18 0 01-14.64 0A1 1 0 0027 31h-2a3 3 0 00-3 3v11.82a19 19 0 1126 0z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
          <path class="active-path"
            d="M10 56h18v2H10zM6 56h2v2H6zM30 56h2v2h-2zM40 9.52l1.03-3.86 1.93.52-1.03 3.86zM45.64 11.59l2-3.47 1.73 1-2 3.47zM50.55 15.03l2.83-2.82 1.41 1.4-2.83 2.84zM54.42 19.63l3.46-2 1 1.73-3.46 2zM56.97 25.08l3.86-1.04.52 1.93-3.87 1.04zM58 31h4v2h-4zM56.97 38.92l.51-1.94 3.87 1.04-.52 1.93zM54.42 44.37l1-1.73 3.46 2-1 1.73zM50.55 48.97l1.41-1.41 2.83 2.82-1.42 1.42zM45.63 52.42l1.74-1 2 3.46-1.74 1zM40 54.48l1.93-.52 1.03 3.86-1.93.52zM35 15a9 9 0 109 9 9.01 9.01 0 00-9-9zm0 16a7 7 0 117-7 7 7 0 01-7 7z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
        </svg></div>
      <p class="about__step-description">Звонок / Заявка</p>
    </div>
    <div class="about__arrow"></div>
    <div class="about__step">
      <div class="about__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 480" width="512"
          height="512">
          <path class="active-path"
            d="M478 67l-24-32a8 8 0 00-12 0l-24 32-2 5v376a32 32 0 0064 0V72l-2-5zm-14 381a16 16 0 11-32 0v-16h32v16zm0-32h-32v-16h32v16zm0-32h-32V96h32v288zm0-304h-32v-5l16-22 16 22v5zM392 0H40c-4 0-8 4-8 8v137c-19 4-32 20-32 39v256c0 22 18 40 40 40h288l6-2 64-64 1-3h1V8c0-4-4-8-8-8zM240 440c0 13-11 24-24 24H40c-13 0-24-11-24-24V184c0-13 11-24 24-24h176c13 0 24 11 24 24v256zM136 96v48H80V96h56zM80 80V48h56v32H80zm128 16v48h-56V96h56zm-56-16V48h56v32h-56zm72 65V96h56v112h-24v-24c0-19-13-35-32-39zm0-65V48h56v32h-56zm112 373v-37h37l-37 37zm48-53h-56c-4 0-8 4-8 8v56h-72c5-7 8-15 8-24V224h104c4 0 8-4 8-8V40c0-4-4-8-8-8H72c-4 0-8 4-8 8v104H48V16h336v384zM352 96v112h-56V96h56zm-56-16V48h56v32h-56z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
          <path class="active-path"
            d="M216 184H40c-4 0-8 4-8 8v48c0 4 4 8 8 8h176c4 0 8-4 8-8v-48c0-4-4-8-8-8zm-8 48H48v-32h160v32zM224 328h-48c-4 0-8 4-8 8v96c0 4 4 8 8 8h48c4 0 8-4 8-8v-96c0-4-4-8-8-8zm-8 96h-32v-80h32v80zM224 264h-48c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32h-32v-16h32v16zM152 328h-48c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32h-32v-16h32v16zM152 264h-48c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32h-32v-16h32v16zM80 328H32c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32H40v-16h32v16zM80 264H32c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32H40v-16h32v16zM152 392h-48c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32h-32v-16h32v16zM80 392H32c-4 0-8 4-8 8v32c0 4 4 8 8 8h48c4 0 8-4 8-8v-32c0-4-4-8-8-8zm-8 32H40v-16h32v16z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
        </svg></div>
      <p class="about__step-description">Расчет</p>
    </div>
    <div class="about__arrow"></div>
    <div class="about__step">
      <div class="about__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="512"
          width="512">
          <path class="active-path"
            d="M373 20L78 0C68 0 60 7 59 17l-2 34H17C8 51 0 59 0 69v425c0 10 8 18 17 18h227c2 0 4-1 5-3l34-33h1l58 4c10 0 18-7 19-17l28-424c1-10-6-18-16-19zM251 486v-52c0-1 1-3 3-3h52zm95-24c0 2-1 3-3 3l-46-4 32-31 2-5V69c0-10-8-18-17-18h-78c-10 0-10 15 0 15h78c1 0 2 1 2 3v347h-62c-10 0-18 8-18 18v63H18c-2 0-3-1-3-3V69c0-2 1-3 3-3h178c9 0 9-15 0-15H72l2-33c0-2 1-3 3-3l295 20c2 0 2 1 2 3z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
          <path class="active-path"
            d="M268 237H63a8 8 0 000 15h205a7 7 0 100-15zM268 289H63a8 8 0 000 15h205a7 7 0 100-15zM56 192c0 4 3 8 7 8h205a7 7 0 100-15H63c-4 0-7 3-7 7zM92 140c0 4 3 7 7 7h133a8 8 0 000-15H99c-4 0-7 4-7 8zM195 439a36391 36391 0 01-54 0c-9 0-14-2-16-11-1-7-12-6-14 0-6 17-14 10-19-1s-6-23-8-35c-2-8-15-6-15 2 0 11-1 22-4 32l-11 31c-4 9 11 13 14 4l11-27c5 12 15 26 31 18l7-6c8 9 20 8 31 8h47c9 0 9-15 0-15zM506 246c-4-3-9-5-15-6h-5v-10c0-7-4-14-10-17v-15c0-31-48-31-48 0v15c-6 4-10 10-10 17v11c-25 2-25 40 0 41v101c0 9 15 10 15 0V282h38v161c0 24-38 24-38-1v-13c1-10-14-11-15-1v13c0 11 4 20 10 27 1 15 8 30 19 42 3 3 7 2 10-1 12-11 18-26 19-42 5-5 9-10 9-27l1-68c12 3 26-7 26-20v-91c0-5-2-11-6-15zm-73-5v-11c0-2 2-4 4-5h30a5 5 0 014 5v11zm19-52c5 0 9 4 9 9v12h-18v-12c0-5 4-9 9-9zm0 304c-4-5-6-11-7-17a33 33 0 0014 0c-1 6-3 12-7 17zm45-141c0 7-11 7-11 0v-78c0-4-4-7-8-7h-58c-8 0-7-11 0-11l71-1c4 1 6 3 6 6v91z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
        </svg></div>
      <p class="about__step-description">Договор</p>
    </div>
    <div class="about__arrow"></div>
    <div class="about__step">
      <div class="about__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512"
          height="512">
          <path class="active-path"
            d="M377 453h-3a120 120 0 00-119-85h-5-2l-2 1h-5l-2 1h-2l-2 1h-3l-2 1h-2l-2 1h-2l-2 1-3 1 1-3 13-63 28 6-1 7a38 38 0 0038 42c16 0 32-10 37-27l1-6 28 6-10 49a8 8 0 0015 3l12-56a8 8 0 00-6-9l-34-8 2-6a8 8 0 00-6-9l-22-5-20-4 43-205 5 2 2 1h3a73 73 0 008 2h3l-40 184a7 7 0 1015 3l40-188c18-2 34-11 46-26h1a7 7 0 000-1l1-1v-1l6-28c1-5-2-9-6-9L307 0c-4-1-8 2-9 6l-6 28v2a7 7 0 000 2h1c5 18 16 33 31 43l-44 208-7-2a8 8 0 00-9 7l-1 6-34-7c-4-1-8 1-9 5l-15 71-2 13a124 124 0 00-15 10l-2 1-2 1-1 2-2 1-2 2-1 1-2 2-2 1-1 2-2 2-1 1-2 2-1 1-2 2-1 2-2 3h-1l-2 4-1 1-2 3-1 2-1 2-1 2-1 2-1 2-1 2-1 2-1 2h-2c-34 0-62 28-62 62 0 5 3 8 7 8h330c4 0 7-3 7-8 0-28-23-51-51-51zM309 30l3-14 100 22-3 13-100-21zm3 16l87 19a58 58 0 01-38 12h-1-2l-3-1h-1a60 60 0 01-5-1h-1l-3-1-3-1-3-1v-1h-2l-1-1c-10-5-19-14-24-24zm-37 278l3-20 32 6 9 3 7 1-6 19c-3 11-15 18-27 16-11-2-19-14-18-25zM99 497c4-22 22-39 44-40l-4 25a8 8 0 1015 1 105 105 0 01105-100c49 0 91 33 103 80 1 4 4 6 8 5h7c17 0 32 12 35 29H99z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
        </svg></div>
      <p class="about__step-description">Работа</p>
    </div>
    <div class="about__arrow"></div>
    <div class="about__step">
      <div class="about__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 497.2 497.2" width="512"
          height="512">
          <path class="active-path"
            d="M466 240c-33 0-64-17-83-44l-6-10-7 10c-19 27-50 44-83 44h-30v128c0 31 14 60 37 80H129v-32h104V272H65v64H17V16h352v144h16V0H1v347l116 117h201l59 33 67-38c33-19 53-53 53-91V240h-31zM113 437l-85-85h85v85zM81 336v-48h136v112h-88v-64H81zm400 32c0 32-17 61-45 77l-59 34-60-34a88 88 0 01-44-77V256h14c35 0 68-16 90-43 21 27 54 43 89 43h15v112z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
          <path class="active-path"
            d="M449 320v48c0 20-11 39-29 49l8 14c23-13 37-37 37-63v-48h-16zM49 32v48h288V32H49zm272 32H65V48h256v16zM443 274L337 381l-27-27-11 12 38 37 117-117zM97 304h104v16H97zM145 336h56v16h-56zM145 368h56v16h-56zM49 112h256v16H49zM49 144h256v16H49zM49 176h256v16H49zM49 208h152v16H49zM49 240h152v16H49zM321 112h16v16h-16zM321 144h16v16h-16zM321 176h16v16h-16zM217 208h16v16h-16zM217 240h16v16h-16z"
            data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
        </svg></div>
      <p class="about__step-description">Акт</p>
    </div>
  </div>
  <h3 class="about__how-title" data-aos="fade-up" data-aos-duration="1200">Заказать ландшафтный дизайн и
    благоустройство территории</h3>
  <div class="about__wrap">
    <div class="about__text-wrap">
      <p class="about__text" data-aos="fade-right" data-aos-duration="1300">Для того чтобы заказать ландшафтный
        проект и благоустройство территории в Рыбинске и Ярославской области достаточно связаться с нами по
        указанным на сайте телефонам или воспользоваться обратным звонком. Если у вас возникнут какие-либо вопросы
        — наш специалист готов предоставить подробную информацию по ландшафтному проектированию, обустройству
        территории, озеленению или прокладке инженерных систем. Вы можете задать свой вопрос по телефону,
        связаться с нами (viber, whatsapp) или воспользоваться электронной почтой.</p>
      <p class="about__text" data-aos="fade-right" data-aos-duration="1400">Сотрудничество с компанией «ЭКСПЕРТЫ»
        начинается с вашего желания сделать вид вокруг себя красивее и уютнее. Решив, что именно Вам хочется
        видеть на приусадебном участке – свободное пространство для детских игр, раскидистые деревья, беседки для
        спокойного отдыха, цветники или водоемы, строгий порядок, хаотичность или сад малого ухода – можно
        обращаться к нашим специалистам. При заключении договора выезд дизайнера бесплатный.</p>
    </div>
    <div class="about__img-wrap" data-aos="fade-up" data-aos-duration="1500">
      <img class="about__img-about" src="<?php echo get_template_directory_uri() ?>/img/about7.jpg" alt=""
        role="presentation" />
    </div>
  </div>
  <div class="about__wrap">
    <div class="formWrapper" id="form" data-aos="fade-up" data-aos-duration="1600">
      <form class="form">
        <p class="form__title">Остались вопросы?</p><label class="form__label">
          <p>Имя или название организации *</p><input class="form__input" type="text" name="name" placeholder=""
            required="required" />
        </label><label class="form__label">
          <p>Контактный телефон *</p><input class="form__input" type="text" name="phone" placeholder=""
            required="required" />
        </label>
        <div class="formConsent"><label class="formConsent__container"><input class="formConsent__input" type="checkbox"
              required="required" /><span class="formConsent__checkbox"><svg class="formConsent__icon"
                viewBox="0 0 426.67 426.67" width="24px" height="24px">
                <path
                  d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265  c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386  c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928  C170.827,363.533,162.165,366.839,153.504,366.839z"
                  fill="#B22917"></path>
              </svg></span></label>
          <p class="formConsent__text">Я ознакомлен и согласен с <a href="privacy.html">политикой
              конфиденциальности </a>оператора, подтверждаю свое <a href="consent.html">согласие </a>на обработку
            введенных мною персональных данных</p>
        </div><button class="form__btn btn" type="submit">Отправить</button>
      </form>
      <div class="ajaxMessage">
        <div class="ajaxMessage__success">
          <div class="ajaxMessage__title">
            <p>Спасибо!</p>
            <p>Ваша заявка принята</p>
          </div>
          <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время, что бы обсудить детали и ответить
            на вопросы</div>
        </div>
        <div class="ajaxMessage__error">
          <div class="ajaxMessage__title">Ошибка при отправке!</div>
          <div class="ajaxMessage__text">Попробуйте позднее</div>
        </div><button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
      </div>
    </div>
    <div class="about__text-wrap" data-aos="fade-right" data-aos-duration="1700">
      <h3 class="about__local">Работаем в Рыбинске и Ярославской области</h3>
      <p class="about__text">Создаем ландшафтный дизайн и облагораживаем территорию в городах и населенных пунктах
        Ярославской области: Ярославль, Рыбинск, Углич, Мышкин, Брейтово, Тутаев, Пошехонье, Арефино, Большое
        Село, Ростов, Гаврилов-Ям, Борок. А так же работаем в городе Череповец, Вологодская область.</p>
    </div>
  </div>
</section>
</main>
</div>

<?php get_footer(); ?>