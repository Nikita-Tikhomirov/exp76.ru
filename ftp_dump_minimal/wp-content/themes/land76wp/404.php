<?php
/**
 * 404 Page — Страница не найдена
 */
?>

<?php get_header('page'); ?>

      <section class="error-404 wrapper">
        <div class="hero__content wrapper">
          <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800">404</h1>
          <p class="hero__description">Страница не найдена</p>
        </div>

        <div class="error-404__content" style="text-align:center; padding: 60px 20px; max-width: 600px; margin: 0 auto;">
          <p style="font-size: 18px; line-height: 1.6; color: #4a4a4a; margin-bottom: 30px;">
            Запрашиваемая страница не существует или была удалена. 
            Возможно, вы перешли по устаревшей ссылке или допустили ошибку в адресе.
          </p>
          <p style="margin-bottom: 30px;">
            <a href="<?php echo get_home_url(); ?>" 
               style="display: inline-block; padding: 14px 40px; background: #0a9215; color: #fff; 
                      text-decoration: none; border-radius: 4px; font-size: 16px; 
                      transition: background 0.3s ease;">
              Вернуться на главную
            </a>
          </p>
          <p style="font-size: 15px; color: #777;">
            Или выберите нужный раздел в меню выше.
          </p>
        </div>
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
              <p class="formConsent__text">Я ознакомлен и согласен с <a href="/privacy/">политикой конфиденциальности
                </a>оператора, подтверждаю свое <a href="/consent/">согласие </a>на обработку введенных мною
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
