<?php
/*
Template Name: Кейс
*/
?>



<?php get_header('gallery'); ?>

<section class="portfoliopost wrapper">

  <article class="portfoliopost__article">




    <?php if (have_rows('slider')): ?>
      <div class="slider2 slider2Top">
        <div class="swiper-wrapper">
          <?php while (have_rows('slider')):
            the_row();
            $image = get_sub_field('image');
            if (!empty($image)):
              // Задаём размеры для разных устройств
              $size_desktop = 'large'; // Большие изображения для десктопов
              $size_mobile = 'medium'; // Оптимизированные изображения для мобильных
              $thumb_desktop = $image['sizes'][$size_desktop];
              $thumb_mobile = $image['sizes'][$size_mobile];
              $alt = $image['alt'] ? $image['alt'] : 'Слайд';
              ?>
              <img class="swiper-slide swiper-slide-top" src="<?php echo $thumb_mobile; ?>"
                srcset="<?php echo $thumb_mobile; ?> 768w, <?php echo $thumb_desktop; ?> 1200w"
                sizes="(max-width: 768px) 768px, 1200px" alt="<?php echo esc_attr($alt); ?>" />
            <?php endif; ?>
          <?php endwhile; ?>
        </div>
      </div>


      <div class="slider2-thumbs">
        <div class="swiper-wrapper">
          <?php while (have_rows('slider')):
            the_row();
            $image = get_sub_field('image');
            if (!empty($image)):
              // Миниатюра для превью
              $thumb_size = 'medium';
              $thumb = $image['sizes'][$thumb_size];
              ?>
              <img class="swiper-slide swiper-slide-bottom" src="<?php echo $thumb; ?>"
                alt="<?php echo esc_attr($image['alt']); ?>" />
            <?php endif; ?>
          <?php endwhile; ?>
        </div>
      </div>
    <?php endif; ?>


    <div class="swiper-button-next"></div>
    <div class="swiper-button-prev"></div>

    <?php the_content(); ?>
  </article>
  <!-- 
        <div class="portfoliopost__description">
          <p>Проектирование и монтаж системы автополива.</p>
          <p>Место расположения: коттеджный поселок Ярославское взморье</p>
          <p>Размер: 40 соток</p>
          <p>Срок реализации : 14 дней</p>
          <p>Время строительства: июнь 2018г.</p>
        </div> -->

</section>

<section class="action wrapper">
  <div class="formWrapper" id="form">
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
  <div class="action__img-wrap"><img class="action__man" src="<?php echo get_template_directory_uri() ?>/img/man22.png"
      alt="" role="presentation" /></div>
</section>
</main>
</div>
<style>
  .slider2Top {
    padding: 0 !important;
    margin: 0 !important;
  }

  .swiper-slide-top {
    width: 100% !important;
    height: 500px !important;
    object-fit: cover;

  }

  .swiper-button-prev,
  .swiper-button-next {
    top: 35% !important;
  }

  .swiper-slide-bottom {
    height: 140px !important;
    object-fit: cover;
  }

  @media only screen and (max-width: 767px) {
    .swiper-slide-top {
      height: 300px !important;
    }

    .swiper-button-next,
    .swiper-button-next:after,
    .swiper-button-prev,
    .swiper-button-prev:after {
      display: block !important;
      top: 170px !important;
    }

    .swiper-button-next {
      right: 0 !important;
    }

    .swiper-button-prev {
      left: 0 !important;
    }

  }

  /* 
   */
  /* .slider2Top .swiper-slide img{
    width: 100%;
    height: 100%;
  } */
</style>
<?php get_footer(); ?>