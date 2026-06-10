<?php
/*
Template Name: Калькулятор
*/

add_filter('the_title', function ($title, $post_id) {
  if ((int) $post_id === (int) get_queried_object_id() && is_page_template('calc.php')) {
    return 'Калькулятор стоимости благоустройства участка';
  }

  return $title;
}, 10, 2);

add_filter('aioseo_title', function ($title) {
  return is_page_template('calc.php')
    ? 'Калькулятор стоимости благоустройства участка - дренаж, плитка, газон'
    : $title;
}, 30, 1);

add_filter('aioseo_description', function ($description) {
  return is_page_template('calc.php')
    ? 'Рассчитайте примерную стоимость работ на участке: проектирование, дренаж, мощение тротуарной плиткой и газон. Точная цена после осмотра и подбора решения.'
    : $description;
}, 30, 1);
?>

<?php get_header('page'); ?>



           <section class="calc wrapper">
        <style>
          .calc-seo__lead,
          .calc-seo__panel,
          .calc-seo__links,
          .calc-seo__faq {
            margin-bottom: 34px;
            padding: 26px 30px;
            background: #fff;
            border-left: 4px solid #0a9215;
            box-shadow: 0 5px 18px rgba(0,0,0,.12);
          }
          .calc .calc__total {
            margin-bottom: 46px;
            background: #fff;
            border-bottom: 2px solid #ff5e00ce;
            box-shadow: 0 5px 18px rgba(0,0,0,.12);
          }
          .calc #form1 {
            width: 100%;
            max-width: 100%;
            margin: 0;
            padding: 34px 30px 30px;
          }
          .calc #form1 .calc-contact-form {
            display: grid !important;
            grid-template-columns: minmax(250px, 1fr) minmax(250px, 1fr) minmax(160px, auto);
            gap: 20px 26px;
            align-items: start;
            width: 100%;
            margin-top: 26px;
          }
          .calc #form1 .calc-contact-form .form__label {
            display: block !important;
            margin: 0;
            text-align: left;
            line-height: 1.35;
          }
          .calc #form1 .calc-contact-form .form__label p {
            margin: 0 0 9px;
            color: #222;
            font-size: 16px;
            font-weight: 500;
            line-height: 1.35;
          }
          .calc #form1 .calc-contact-form .form__input {
            width: 100% !important;
            height: 42px;
            min-width: 0;
            margin: 0 !important;
            padding: 8px 14px;
            border: 1px solid rgba(255, 94, 0, .55);
            border-radius: 0;
            font-size: 16px;
          }
          .calc #form1 .calc-contact-form .formConsent {
            grid-column: 1 / 3;
            display: grid !important;
            grid-template-columns: 18px minmax(0, 1fr);
            gap: 10px;
            align-items: start;
            max-width: 760px;
            margin: 2px 0 0;
          }
          .calc #form1 .calc-contact-form .formConsent__container {
            min-width: 18px;
            margin: 3px 0 0 !important;
          }
          .calc #form1 .calc-contact-form .formConsent__input {
            width: auto !important;
          }
          .calc #form1 .calc-contact-form .formConsent__text {
            margin: 0;
            max-width: 720px;
            font-size: 13px;
            line-height: 1.45;
            text-align: left;
            color: #444;
          }
          .calc #form1 .calc-contact-form .form__btn {
            grid-column: 3;
            grid-row: 2;
            justify-self: end;
            align-self: start;
            min-width: 160px;
            margin: 0 !important;
            padding: 8px 28px;
            font-size: 18px;
          }
          .calc #form1 .calc__info {
            margin-top: 24px;
            padding-top: 18px;
            border-top: 1px solid rgba(0,0,0,.25);
          }
          .calc-seo__lead p,
          .calc-seo__panel p,
          .calc-seo__links p,
          .calc-seo__faq p,
          .calc-seo__list li {
            color: #555;
            font-size: 17px;
            line-height: 1.65;
          }
          .calc-seo__lead p,
          .calc-seo__panel p,
          .calc-seo__links p,
          .calc-seo__faq p {
            margin: 0 0 16px;
          }
          .calc-seo__actions,
          .calc-seo__grid,
          .calc-seo__price-grid,
          .calc-seo__faq-grid {
            display: grid;
            gap: 16px;
          }
          .calc-seo__actions {
            grid-template-columns: repeat(3, 1fr);
            margin-top: 22px;
          }
          .calc-seo__button,
          .calc-seo__card,
          .calc-seo__price {
            display: block;
            background: #fff;
            color: #555;
            box-shadow: 0 4px 14px rgba(0,0,0,.12);
            transition: .2s;
          }
          .calc-seo__button {
            padding: 12px 18px;
            border: 2px solid #0a9215;
            border-radius: 25px;
            color: #0a9215;
            font-weight: 600;
            text-align: center;
          }
          .calc-seo__button:hover {
            background: #0a9215;
            color: #fff;
          }
          .calc-seo__title {
            margin: 0 0 20px;
            font-family: "Poiret One", cursive;
            font-size: 38px;
            font-weight: 600;
            color: #333;
            text-shadow: 1px 2px 3px #00000036;
          }
          .calc-seo__grid,
          .calc-seo__price-grid {
            grid-template-columns: repeat(3, 1fr);
          }
          .calc-seo__card,
          .calc-seo__price {
            min-height: 116px;
            padding: 18px 20px;
            border-left: 4px solid #ff5e00ce;
          }
          .calc-seo__card:hover,
          .calc-seo__price:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 18px rgba(0,0,0,.16);
          }
          .calc-seo__card strong,
          .calc-seo__price strong {
            display: block;
            margin-bottom: 8px;
            color: #0a9215;
            font-size: 18px;
            line-height: 1.25;
          }
          .calc-seo__card span,
          .calc-seo__price span {
            display: block;
            font-size: 15px;
            line-height: 1.5;
          }
          .calc-seo__list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px 26px;
            margin: 18px 0 0;
            list-style: none;
          }
          .calc-seo__list li {
            position: relative;
            padding-left: 25px;
          }
          .calc-seo__list li:before {
            content: "";
            position: absolute;
            left: 0;
            top: .72em;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background: #0a9215;
            box-shadow: 0 0 0 4px rgba(10,146,21,.12);
          }
          .calc-seo__faq-item {
            overflow: hidden;
            background: #fff;
            border-left: 4px solid #ff5e00ce;
            box-shadow: 0 4px 14px rgba(0,0,0,.1);
            transition: box-shadow .2s, transform .2s;
          }
          .calc-seo__faq-item[open] {
            box-shadow: 0 7px 18px rgba(0,0,0,.14);
          }
          .calc-seo__faq-question {
            position: relative;
            display: block;
            padding: 18px 56px 18px 20px;
            color: #0a9215;
            font-weight: 600;
            font-size: 19px;
            line-height: 1.3;
            cursor: pointer;
            list-style: none;
          }
          .calc-seo__faq-question::-webkit-details-marker {
            display: none;
          }
          .calc-seo__faq-question:after {
            content: "+";
            position: absolute;
            right: 20px;
            top: 50%;
            width: 28px;
            height: 28px;
            border: 2px solid #0a9215;
            border-radius: 50%;
            color: #0a9215;
            font-size: 22px;
            font-weight: 600;
            line-height: 24px;
            text-align: center;
            transform: translateY(-50%);
            transition: .2s;
          }
          .calc-seo__faq-item[open] .calc-seo__faq-question:after {
            content: "-";
            color: #fff;
            background: #0a9215;
          }
          .calc-seo__faq-answer {
            padding: 0 20px 20px;
          }
          .calc-seo__faq-answer p {
            margin: 0;
            font-size: 16px;
          }
          @media only screen and (max-width: 991px) {
            .calc #form1 .calc-contact-form {
              grid-template-columns: 1fr 1fr;
              align-items: start;
            }
            .calc #form1 .calc-contact-form .formConsent {
              grid-column: 1 / -1;
            }
            .calc #form1 .calc-contact-form .form__btn {
              grid-column: 1 / -1;
              grid-row: auto;
              justify-self: center;
              margin: 0 !important;
            }
            .calc-seo__actions,
            .calc-seo__grid,
            .calc-seo__price-grid,
            .calc-seo__faq-grid {
              grid-template-columns: repeat(2, 1fr);
            }
          }
          @media only screen and (max-width: 767px) {
            .calc #form1 {
              padding: 26px 20px;
            }
            .calc #form1 .calc-contact-form {
              grid-template-columns: 1fr;
              gap: 16px;
            }
            .calc #form1 .calc-contact-form .form__label {
              grid-template-columns: 1fr;
              gap: 8px;
              text-align: left;
            }
            .calc #form1 .calc-contact-form .form__btn {
              grid-row: auto;
              width: 100%;
            }
            .calc-seo__lead,
            .calc-seo__panel,
            .calc-seo__links,
            .calc-seo__faq {
              padding: 24px 20px;
            }
            .calc-seo__actions,
            .calc-seo__grid,
            .calc-seo__price-grid,
            .calc-seo__faq-grid,
            .calc-seo__list {
              grid-template-columns: 1fr;
            }
            .calc-seo__title {
              font-size: 31px;
            }
            .calc-seo__faq-question {
              padding: 16px 48px 16px 16px;
              font-size: 17px;
            }
            .calc-seo__faq-answer {
              padding: 0 16px 18px;
            }
          }
        </style>

        <h2 class="calc__title">Расчет примерной стоимости работ</h2>

        <div class="calc-seo__lead">
          <p>Калькулятор помогает быстро прикинуть бюджет на основные работы по участку: ландшафтное проектирование, дренаж, мощение тротуарной плиткой и газон. Расчет предварительный, но он дает понятный ориентир перед заявкой и помогает понять порядок стоимости.</p>
          <p>Для отмостки, ливневой канализации, осушения участка и автополива стоимость лучше считать индивидуально: там важны площадь, уклоны, точки отвода воды, оборудование, материалы и привязка к уже существующим покрытиям. По этим направлениям можно открыть подробную страницу услуги или оставить заявку на расчет.</p>
          <div class="calc-seo__actions">
            <a class="calc-seo__button" href="#form1">Рассчитать в калькуляторе</a>
            <a class="calc-seo__button" href="/services/">Каталог услуг</a>
            <a class="calc-seo__button openPopup" href="#form" data-modal="#popup">Получить консультацию</a>
          </div>
        </div>
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
            <form class="form calc-contact-form"><label class="form__label">
                <p>Имя или название организации *</p><input class="form__input" type="text" name="name" placeholder="Ваше имя"
                  required="required" />
              </label><label class="form__label">
                <p>Контактный телефон *</p><input class="form__input" type="text" name="phone"
                  placeholder="Ваш номер телефона" required="required" />
              </label>
            <div class="formConsent"><label class="formConsent__container"><input class="formConsent__input" type="checkbox" required="required" /><span class="formConsent__checkbox"><svg class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px"><path d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928C170.827,363.533,162.165,366.839,153.504,366.839z" fill="#B22917"></path></svg></span></label><p class="formConsent__text">Я ознакомлен и согласен с <a href="privacy.html">политикой конфиденциальности</a> оператора, подтверждаю свое <a href="consent.html">согласие</a> на обработку введенных мною персональных данных</p></div><button class="form__btn btn" type="submit">Отправить</button></form>
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
        <div class="calc-seo__panel">
          <h2 class="calc-seo__title">Что влияет на стоимость работ на участке</h2>
          <p>Онлайн-расчет не заменяет осмотр, потому что цена зависит не только от площади. На одном участке достаточно локального решения, а на другом приходится учитывать грунтовые воды, уклоны, готовые дорожки, подъезд техники и будущую планировку.</p>
          <ul class="calc-seo__list">
            <li>площадь участка, длина трасс, метраж траншей и покрытий;</li>
            <li>тип грунта, уровень воды, уклон и места сброса воды;</li>
            <li>материалы: труба, щебень, геотекстиль, лотки, плитка, бордюр;</li>
            <li>наличие дома, забора, дорожек, посадок и других ограничений;</li>
            <li>необходимость проектирования, разметки и поэтапного монтажа;</li>
            <li>комплекс работ: дренаж, ливневка, отмостка, плитка, газон, автополив.</li>
          </ul>
        </div>

        <div class="calc-seo__links">
          <h2 class="calc-seo__title">Подробные цены по направлениям</h2>
          <p>Если нужен расчет по конкретной услуге, откройте нужное направление. Там собраны состав работ, этапы, частые вопросы и страницы под отдельные задачи.</p>
          <div class="calc-seo__price-grid">
            <a class="calc-seo__price" href="/category/drenazh-uchastka/"><strong>Дренаж участка</strong><span>Глубинный и поверхностный дренаж, участки 6 и 10 соток, глинистая почва, высокий УГВ.</span></a>
            <a class="calc-seo__price" href="/category/osushenie-uchastka/"><strong>Осушение участка</strong><span>Решения для сырых, заболоченных и низких участков, где вода долго стоит после дождя.</span></a>
            <a class="calc-seo__price" href="/category/livnevaya-kanalizatsiya/"><strong>Ливневая канализация</strong><span>Лотки, дождеприемники, трубы и отвод воды с крыши, дорожек, площадок и въезда.</span></a>
            <a class="calc-seo__price" href="/category/otmostka-vokrug-doma/"><strong>Отмостка вокруг дома</strong><span>Бетонная, мягкая, утепленная и плиточная отмостка с уклоном и водоотводом.</span></a>
            <a class="calc-seo__price" href="/category/ukladka-trotuarnoy-plitki/"><strong>Укладка тротуарной плитки</strong><span>Дорожки, площадки, парковки, бордюры, подготовка основания и водоотвод.</span></a>
            <a class="calc-seo__price" href="/category/avtopoliv-na-uchastke/"><strong>Автополив на участке</strong><span>Полив газона, сада, теплицы, клумб, капельные линии, насос и автоматика.</span></a>
          </div>
        </div>

        <div class="calc-seo__panel">
          <h2 class="calc-seo__title">Когда лучше считать работы комплексом</h2>
          <p>Часть работ выгоднее планировать вместе. Например, дренаж и ливневку лучше увязать до устройства дорожек, отмостку - с водоотводом от дома, а газон - после планировки участка и подготовки полива.</p>
          <div class="calc-seo__grid">
            <a class="calc-seo__card" href="/category/drenazh-uchastka/"><strong>Дренаж + ливневка</strong><span>Снижаем риск луж, сырости и подтопления, заранее связываем трассы отвода воды.</span></a>
            <a class="calc-seo__card" href="/category/otmostka-vokrug-doma/"><strong>Отмостка + водоотвод</strong><span>Защищаем фундамент и не оставляем воду у цоколя после дождя и таяния снега.</span></a>
            <a class="calc-seo__card" href="/category/ukladka-trotuarnoy-plitki/"><strong>Плитка + бордюры</strong><span>Сразу учитываем основание, уклоны, лотки, примыкания и высоты покрытий.</span></a>
            <a class="calc-seo__card" href="/category/avtopoliv-na-uchastke/"><strong>Газон + автополив</strong><span>Полив проще заложить до финишного газона, посадок и декоративных покрытий.</span></a>
            <a class="calc-seo__card" href="/services/"><strong>Проект + благоустройство</strong><span>Сначала фиксируем схему участка, потом считаем работы без лишних переделок.</span></a>
            <a class="calc-seo__card" href="/fotogalereja/"><strong>Расчет по примеру</strong><span>Можно посмотреть готовые объекты и обсудить похожее решение для вашего участка.</span></a>
          </div>
        </div>

        <div class="calc-seo__faq">
          <h2 class="calc-seo__title">Вопросы по расчету стоимости</h2>
          <div class="calc-seo__faq-grid">
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Можно ли точно рассчитать стоимость онлайн?</summary>
              <div class="calc-seo__faq-answer">
                <p>Нет, онлайн-калькулятор дает ориентир. Точная цена зависит от грунта, уклонов, материалов, доступа к участку и схемы работ.</p>
              </div>
            </details>
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Какие работы сейчас считает калькулятор?</summary>
              <div class="calc-seo__faq-answer">
                <p>Сейчас доступны проектирование, дренаж, мощение и газон. По остальным направлениям стоимость считаем индивидуально после уточнения задачи и вводных по участку.</p>
              </div>
            </details>
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Можно ли рассчитать отмостку, ливневку или автополив?</summary>
              <div class="calc-seo__faq-answer">
                <p>Да, но пока через заявку. Для этих работ нужно больше вводных: площадь, точки воды, трассы, уклоны, оборудование и материалы.</p>
              </div>
            </details>
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Что отправить для предварительной оценки?</summary>
              <div class="calc-seo__faq-answer">
                <p>Подойдут фото участка, примерные размеры, описание проблемы, адрес или населенный пункт и пожелания по срокам.</p>
              </div>
            </details>
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Вы работаете по Ярославской области?</summary>
              <div class="calc-seo__faq-answer">
                <p>Да, выезжаем по Рыбинску, Ярославлю, Угличу, Тутаеву, Переславлю и другим населенным пунктам области.</p>
              </div>
            </details>
            <details class="calc-seo__faq-item">
              <summary class="calc-seo__faq-question">Почему цена может измениться после осмотра?</summary>
              <div class="calc-seo__faq-answer">
                <p>На объекте могут выявиться высокий уровень воды, сложный грунт, ограничения по технике, готовые покрытия или необходимость другой схемы.</p>
              </div>
            </details>
          </div>
        </div>
      </section>

      <script>
        document.addEventListener('DOMContentLoaded', function () {
          var faqItems = document.querySelectorAll('.calc-seo__faq-item');
          faqItems.forEach(function (item) {
            item.addEventListener('toggle', function () {
              if (!item.open) {
                return;
              }
              faqItems.forEach(function (other) {
                if (other !== item) {
                  other.open = false;
                }
              });
            });
          });
        });
      </script>

      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "Можно ли точно рассчитать стоимость онлайн?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Онлайн-калькулятор дает ориентир. Точная цена зависит от грунта, уклонов, материалов, доступа к участку и схемы работ."
            }
          },
          {
            "@type": "Question",
            "name": "Какие работы сейчас считает калькулятор?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Сейчас доступны проектирование, дренаж, мощение и газон. По остальным направлениям стоимость рассчитывается индивидуально после уточнения задачи и вводных по участку."
            }
          },
          {
            "@type": "Question",
            "name": "Можно ли рассчитать отмостку, ливневую канализацию или автополив?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Да, но пока через заявку. Для этих работ нужны площадь, точки воды, трассы, уклоны, оборудование и материалы."
            }
          },
          {
            "@type": "Question",
            "name": "Что отправить для предварительной оценки?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Для предварительной оценки подойдут фото участка, примерные размеры, описание проблемы, адрес или населенный пункт и пожелания по срокам."
            }
          },
          {
            "@type": "Question",
            "name": "Вы работаете по Ярославской области?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Компания выполняет работы по Рыбинску, Ярославлю, Угличу, Тутаеву, Переславлю и другим населенным пунктам Ярославской области."
            }
          }
        ]
      }
      </script>






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
