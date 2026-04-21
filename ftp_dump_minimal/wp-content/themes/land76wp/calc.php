<?php
/*
Template Name: Калькулятор
*/
?>

<?php get_header('page'); ?>



           <section class="calc wrapper">
        <h2 class="calc__title">Расчет примерной стоимости</h2>
        <div class="tabs tabsWrapJs">
          <div class="tabs__nav tabsNavJs">
            <div class="tabs__link">Проект</div>
            <div class="tabs__link">Дренаж</div>
            <div class="tabs__link">Мощение</div>
            <div class="tabs__link">Газоны</div>
          </div>
          <div class="tabs__container tabsJs">
            <div class="tabs__item">
              <div class="tabs__ls">
                <p class="tabs__type">Тип проекта</p>
                <div class="tabs1 tabsWrapJs1">
                  <div class="tabs1__nav tabsNavJs1">
                    <div class="tabs1__link" id="projectButton">Эскизный</div>
                    <div class="tabs1__link" id="projectButton1">Базовый</div>
                    <div class="tabs1__link" id="projectButton2">Детализированный</div>
                  </div>
                  <div class="tabs1__container tabsJs1">
                    <div class="tabs1__item">- Эскизный план до 2х вариантов <br>- Ассортиментная ведомость <br>-
                      Дендропологический план</div>
                    <div class="tabs1__item">+ к эскизному <br>- Генеральный план <br>- Разбивочный чертеж <br>-
                      Посадочный чертеж <br>- План освещения <br>- Данные по площадкам и материалам</div>
                    <div class="tabs1__item">+ к эскизному и базовому <br>- Карта мощения <br>- Инженерные узлы и
                      разрезы <br>- 3D визуализация <br>- Детальная смета <br>- План организации рельефа</div>
                  </div>
                </div>
                <div class="tabs__project-total-wrap"><span class="tabs__project-total">Стоимость проекта:</span><span
                    class="tabs__project-count" id="tab-project-total">0</span></div>
              </div>
              <div class="tabs__rs">
                <p class="tabs__square-title">Площадь участка</p>
                <div class="tabs__squre"><span class="tabs__square-description">Количество соток</span><input
                    class="tabs__square-input" id="project-square" type="text" name="square" placeholder="0" /></div>
              </div>
            </div>
            <div class="tabs__item dren-tab">
              <div class="tabs__ls">
                <p class="tabs__type">Тип дренажа</p>
                <div class="tabs1">
                  <div class="tabs1__nav">
                    <div class="tabs1__link active" id="drenButton">Поверхностный</div>
                    <div class="tabs1__link" id="drenButton1">глубинный</div>
                  </div>
                </div>
                <div class="tabs__services-wrap">
                  <div class="tabs__squre dren"><span class="tabs__square-description">Траншеи, пог.м.</span><input
                      class="tabs__square-input" id="dren-square" type="text" name="square" placeholder="0" /></div>
                </div>
              </div>
              <div class="tabs__rs"></div>
              <div class="tabs__project-total-wrap dren-total"><span class="tabs__project-total">Стоимость
                  дренажа:</span><span class="tabs__project-count" id="tab-dren-total">0</span></div>
            </div>
            <div class="tabs__item mosh">
              <div class="tabs__ls">
                <p class="tabs__square-title">Площадь покрытий</p>
                <div class="tabs__squre"><span class="tabs__square-description">Количество м2</span><input
                    class="tabs__square-input" id="mosh-square" type="text" name="square" placeholder="0" /></div>
                <p class="tabs__square-title">Установка бордюрного камня </p>
                <div class="tabs__squre"><span class="tabs__square-description">пог.м.</span><input
                    class="tabs__square-input" id="border" type="text" name="square" placeholder="0" /></div>
              </div>
              <div class="tabs__rs mosh-tabs">
                <p class="tabs__rs-title">Доп. параметры</p>
                <div class="tabs1">
                  <div class="tabs1__nav mosh-nav">
                    <div class="tabs1__link active" id="moshButton">Тротуарная плитка</div>
                    <div class="tabs1__link" id="moshButton1">Натуральный камень</div>
                    <div class="tabs1__link" id="moshButton2">Гранитная брусчатка</div>
                  </div>
                </div>
                <div class="tabs__project-total-wrap"><span class="tabs__project-total">Стоимость мощения:</span><span
                    class="tabs__project-count" id="tab-mosh-total">0</span></div>
              </div>
            </div>
            <div class="tabs__item mosh">
              <div class="tabs__ls">
                <p class="tabs__square-title">Площадь участка</p>
                <div class="tabs__squre"><span class="tabs__square-description">Количество м2</span><input
                    class="tabs__square-input" id="grass-square" type="text" name="square" placeholder="0" /></div>
              </div>
              <div class="tabs__rs grass">
                <p class="tabs__square-title">Параметры</p>
                <div class="tabs1">
                  <div class="tabs1__nav">
                    <div class="tabs1__link active" id="grassButton">Рулонный</div>
                    <div class="tabs1__link" id="grassButton1">Посевной</div>
                  </div>
                </div>
                <div class="tabs__project-total-wrap"><span class="tabs__project-total">Стоимость газона:</span><span
                    class="tabs__project-count" id="tab-grass-total">0</span></div>
              </div>
            </div>
          </div>
        </div>
        <div class="calc__total">
          <div class="formWrapper" id="form1">
            <p class="calc__calc-title">Оставьте контактные данные, мы свяжемся с вами в ближайшее время и начнем
              разработку проекта</p>
            <form class="form"><label class="form__label">
                <p>Имя *</p><input class="form__input" type="text" name="name" placeholder="Ваше имя"
                  required="required" />
              </label><label class="form__label">
                <p>Контактный телефон *</p><input class="form__input" type="text" name="phone"
                  placeholder="Ваш номер телефона" required="required" />
              </label><button class="form__btn btn" type="submit">Отправить</button></form>
            <p class="calc__info">Стоимость работ является оценочной. Точную стоимость можно узнать по телефону или
              заказав выезд нашего специалиста на участок.</p>
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