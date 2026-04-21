<?php
/*
Template Name: Услуга
*/
?>

<?php get_header('service'); ?>


      <section class="servicepost wrapper">
        <article class="servicepost__article">
          <?php the_content();?>
        </article>



        <aside>
          <div class="slider">
            <div class="swiper-wrapper">
            <?php

            $posts = get_posts( array(
            'numberposts' => -1,
            'category'    => 74,
            'orderby'     => 'date',
            'order'       => 'DESC',
            'include'     => array(),
            'exclude'     => array(),
            'meta_key'    => '',
            'meta_value'  =>'',
            'post_type'   => 'page',
            'suppress_filters' => true, // подавление работы фильтров изменения SQL запроса
            ) );

                foreach( $posts as $post ){
                setup_postdata($post);
                    // формат вывода the_title() ...

                

            ?>

              <div class="service swiper-slide">
                <div class="service__img-wrap"><img class="service__img" src="<?php the_post_thumbnail_url(); ?>" alt="" role="presentation" />
                </div>

                <div class="service__text-wrap">

                  <h5 class="service__title"><?php the_title()?></h5>

                  <div class="service__exept"><?php the_excerpt() ?></div>

                </div>
                <div class="service__link-wrap"><a class="service__link" href="<?php the_permalink()?>">Подробнее</a></div>
              </div>
              
              <?php
              }

              wp_reset_postdata(); // сброс

              ?>



            </div>
          </div>



          <div class="swiper-button-next"></div>
          <div class="swiper-button-prev"></div>
        </aside>
      </section>


      <section class="action wrapper">
        <div class="formWrapper" id="form" data-aos="fade-up" data-aos-duration="1600">
          <form class="form">
            <p class="form__title">Остались вопросы?</p><label class="form__label">
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
        <div class="action__img-wrap"><img class="action__man" src="<?php echo get_template_directory_uri() ?>/img/man22.png" alt="" role="presentation" /></div>
      </section>
    </main>
  </div>



<?php get_footer(); ?>