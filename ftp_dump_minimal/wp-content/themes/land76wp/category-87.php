<?php
/*
Template Name: Категория Дренаж участка
*/
?>

<?php get_header('seo'); ?>
<link rel="stylesheet" href="<?php bloginfo('template_directory'); ?>/css/index.css" />
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
    .advantages {
    padding-top: 50px;
    padding-bottom: 50px;
    -webkit-box-shadow: inset 0 5px 5px rgba(0,0,0,.1);
    box-shadow: inset 0 5px 5px rgba(0,0,0,.1);
    background: #fff;
    border-top: 2px solid #0a9215
}

.advantages__title {
    margin-bottom: 50px;
    font-family: "Poiret One",cursive;
    font-size: 50px;
    font-weight: 800;
    color: #333;
    text-shadow: 1px 2px 3px #00000036
}

.advantages__how {
    margin-top: 70px;
    margin-bottom: 70px;
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-pack: justify;
    -ms-flex-pack: justify;
    justify-content: space-between;
    -webkit-box-align: start;
    -ms-flex-align: start;
    align-items: flex-start
}

.advantages__step {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-orient: vertical;
    -webkit-box-direction: normal;
    -ms-flex-direction: column;
    flex-direction: column;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    -webkit-box-pack: center;
    -ms-flex-pack: center;
    justify-content: center;
    -ms-flex-preferred-size: 15%;
    flex-basis: 15%
}

.advantages__step p {
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: #333
}

.advantages__svg-wrap {
    display: -webkit-box;
    display: -ms-flexbox;
    display: flex;
    -webkit-box-pack: center;
    -ms-flex-pack: center;
    justify-content: center;
    -webkit-box-align: center;
    -ms-flex-align: center;
    align-items: center;
    width: 110px;
    margin-bottom: 15px;
    padding: 19px;
    border: 2px solid #ff5e00;
    border-radius: 50%;
    -webkit-box-shadow: 2px 3px 4px rgba(0,0,0,.4);
    box-shadow: 2px 3px 4px rgba(0,0,0,.4);
    background: #ffffff3b
}

.advantages__svg-wrap svg {
    width: 100%;
    height: auto
}

.advantages__arrow {
    width: 50px;
    height: 50px;
    background: url(<?php echo get_template_directory_uri(); ?>/img/arrow-step.svg) center/cover no-repeat;
    -ms-flex-item-align: center;
    align-self: center;
    margin-bottom: 40px
}

.advantages__text {
    color: #333;
    text-shadow: 1px 1px 1px #00000026;
    line-height: 180%;
    width: 50%
}

.advantages__text-wrap {
    width: 50%
}

.advantages__text-wrap p {
    margin-bottom: 15px;
    width: 100%
}

.advantages__how-title {
    margin-bottom: 30px;
    font-family: "Poiret One",cursive;
    font-size: 40px;
    font-weight: 800;
    color: #0a9215;
    text-shadow: 1px 2px 3px #00000036
}

.advantages__local {
    margin-bottom: 30px;
    font-family: "Poiret One",cursive;
    font-size: 35px;
    font-weight: 800;
    color: #0a9215;
    text-shadow: 1px 2px 3px #00000036
}
.casesCustom{
  background: #fff;
  border-top: 2px solid #0a9215;
}
.howWorkCustom{
  border-bottom: 2px solid #0a9215;
}
.faq-answer{
  background: #fff;
}
.seo-text h2{
  margin-bottom: 20px;
  font-family: "Poiret One",cursive;
  font-size: 35px;
  font-weight: 800;
  color: #0a9215;
  text-shadow: 1px 2px 3px #00000036;
}
.seo-text p{
  margin-bottom: 20px;
  line-height: 1.8;
  color: #333;
  font-size: 16px;
}
.seo-text ul{
  margin-bottom: 20px;
  padding-left: 25px;
}
.seo-text ul li{
  margin-bottom: 10px;
  line-height: 1.6;
  color: #333;
}
.btn--primary-custom{
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
.btn--primary-custom:hover{
  background: #0a7b12;
  color: #fff;
  text-decoration: none;
  border-color: #0a7b12;
}
.btn--outline-custom{
  display: inline-block;
  padding: 15px 30px;
  background: transparent;
  color: #0a9215;
  text-decoration: none;
  border-radius: 25px;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
  border: 2px solid #0a9215;
}
.btn--outline-custom:hover{
  background: #0a9215;
  color: #fff;
  text-decoration: none;
}
.cta-btn-custom{
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
  cursor: pointer;
}
.cta-btn-custom:hover{
  background: #0a7b12;
  color: #fff;
  text-decoration: none;
  border-color: #0a7b12;
}
.price-example{
  background: #f9f9f9;
  padding: 30px;
  border-radius: 10px;
  margin-bottom: 30px;
}
.price-example h3{
  margin-bottom: 20px;
  font-family: "Poiret One",cursive;
  font-size: 24px;
  font-weight: 700;
  color: #333;
}
.price-example ul{
  margin: 20px 0;
  padding-left: 25px;
  list-style: none;
}
.price-example ul li{
  margin-bottom: 15px;
  line-height: 1.6;
  color: #333;
  position: relative;
  padding-left: 20px;
}
.price-example ul li:before{
  content: "•";
  color: #0a9215;
  font-weight: bold;
  position: absolute;
  left: 0;
  font-size: 18px;
}
.price-example ul li strong{
  color: #0a9215;
  font-weight: 700;
}
.faq-toggle{
  margin: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  font-weight: 700;
}
.faq-toggle span{
  font-size: 24px;
  margin-left: 20px;
  flex-shrink: 0;
}
.cta-title{
  font-weight: 700;
  margin-bottom: 35px;
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
  .advantages__title {
    font-size: 35px;
  }
      .hero__breadcramps{
      flex-wrap: wrap;
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
}
</style>
<?php
$cat87_term_context = 'category_' . get_queried_object_id();
$cat87_hero_title = function_exists('get_field') ? get_field('cat87_hero_title', $cat87_term_context) : '';
$cat87_hero_subtitle = function_exists('get_field') ? get_field('cat87_hero_subtitle', $cat87_term_context) : '';
$cat87_hero_btn_primary_text = function_exists('get_field') ? get_field('cat87_hero_btn_primary_text', $cat87_term_context) : '';
$cat87_hero_btn_primary_url = function_exists('get_field') ? get_field('cat87_hero_btn_primary_url', $cat87_term_context) : '';
$cat87_hero_btn_secondary_text = function_exists('get_field') ? get_field('cat87_hero_btn_secondary_text', $cat87_term_context) : '';
$cat87_hero_btn_secondary_url = function_exists('get_field') ? get_field('cat87_hero_btn_secondary_url', $cat87_term_context) : '';
$cat87_offer_title = function_exists('get_field') ? get_field('cat87_offer_title', $cat87_term_context) : '';
$cat87_trust_items = function_exists('get_field') ? get_field('cat87_trust_items', $cat87_term_context) : array();
$cat87_prices_title = function_exists('get_field') ? get_field('cat87_prices_title', $cat87_term_context) : '';
$cat87_price_rows = function_exists('get_field') ? get_field('cat87_price_rows', $cat87_term_context) : array();
$cat87_estimate_title = function_exists('get_field') ? get_field('cat87_estimate_title', $cat87_term_context) : '';
$cat87_estimate_items = function_exists('get_field') ? get_field('cat87_estimate_items', $cat87_term_context) : array();
$cat87_estimate_total = function_exists('get_field') ? get_field('cat87_estimate_total', $cat87_term_context) : '';
$cat87_prices_link_text = function_exists('get_field') ? get_field('cat87_prices_link_text', $cat87_term_context) : '';
$cat87_prices_link_url = function_exists('get_field') ? get_field('cat87_prices_link_url', $cat87_term_context) : '';
$cat87_faq_title = function_exists('get_field') ? get_field('cat87_faq_title', $cat87_term_context) : '';
$cat87_faq_items = function_exists('get_field') ? get_field('cat87_faq_items', $cat87_term_context) : array();

$cat87_default_trust_titles = array('Авторский дизайн', 'Индивидуальный подход', 'Профессионализм', 'Высокое качество');
$cat87_trust_titles = $cat87_default_trust_titles;
if (!empty($cat87_trust_items) && is_array($cat87_trust_items)) {
    foreach ($cat87_default_trust_titles as $idx => $fallback_title) {
        if (!empty($cat87_trust_items[$idx]['title'])) {
            $cat87_trust_titles[$idx] = $cat87_trust_items[$idx]['title'];
        }
    }
}

if (empty($cat87_price_rows) || !is_array($cat87_price_rows)) {
    $cat87_price_rows = array(
        array('service' => 'Глубинный дренаж', 'price' => 'от 3 500 ₽', 'term' => '3-5 дней'),
        array('service' => 'Поверхностный дренаж', 'price' => 'от 2 800 ₽', 'term' => '2-4 дня'),
        array('service' => 'Пристенный дренаж', 'price' => 'от 4 200 ₽', 'term' => '4-6 дней'),
    );
}

if (empty($cat87_estimate_items) || !is_array($cat87_estimate_items)) {
    $cat87_estimate_items = array(
        array('item' => 'Проектирование системы - 15 000 ₽'),
        array('item' => 'Монтаж дренажных труб (150 м) - 525 000 ₽'),
        array('item' => 'Установка дренажных колодцев (3 шт) - 45 000 ₽'),
        array('item' => 'Обратная засыпка и трамбовка - 30 000 ₽'),
    );
}

if (empty($cat87_faq_items) || !is_array($cat87_faq_items)) {
    $cat87_faq_items = array(
        array(
            'question' => 'Сколько стоит дренаж участка?',
            'answer' => 'Стоимость дренажа участка зависит от площади, типа почвы и сложности работ. В среднем цена варьируется от 2 800 до 4 200 рублей за погонный метр. Точную стоимость мы рассчитываем после бесплатного выезда на объект.',
        ),
        array(
            'question' => 'Какая глубина дренажной системы?',
            'answer' => 'Глубина заложения дренажных труб составляет 0.8-1.5 метра для поверхностного дренажа и 1.5-3 метра для глубинного дренажа.',
        ),
        array(
            'question' => 'Сколько времени занимает монтаж?',
            'answer' => 'Сроки монтажа дренажной системы зависят от площади участка и сложности работ. В среднем на стандартный участок 10-15 соток уходит от 3 до 7 рабочих дней.',
        ),
    );
}
?>
    <!-- 1. Hero блок с полной структурой из header-page.php -->
      <section class="hero">
        <div class="hero__scene" id="scene">
          <div class="hero__bg" data-depth="0.4"></div>
        </div>
        <div class="hero__content wrapper">
          <h1 class="hero__title" data-aos="fade-right" data-aos-duration="800"><?php echo esc_html($cat87_hero_title ? $cat87_hero_title : 'Дренаж участка под ключ в Ярославской области'); ?></h1>
          <p class="hero__subtitle" data-aos="fade-up" data-aos-duration="900"><?php echo esc_html($cat87_hero_subtitle ? $cat87_hero_subtitle : 'Проектируем и выполняем монтаж дренажных систем любой сложности. Гарантия, расчет стоимости за 1 день.'); ?></p>
          <div class="hero__buttons" data-aos="fade-up" data-aos-duration="1000">
            <a href="<?php echo esc_url($cat87_hero_btn_primary_url ? $cat87_hero_btn_primary_url : '#calc'); ?>" class="hero__btn"><?php echo esc_html($cat87_hero_btn_primary_text ? $cat87_hero_btn_primary_text : 'Рассчитать стоимость'); ?></a>
            <a href="<?php echo esc_url($cat87_hero_btn_secondary_url ? $cat87_hero_btn_secondary_url : '#consultation'); ?>" class="hero__btn openPopup" data-modal="#popup" style="margin-left: 15px;"><?php echo esc_html($cat87_hero_btn_secondary_text ? $cat87_hero_btn_secondary_text : 'Получить консультацию'); ?></a>
          </div>
          <div class="hero__breadcramps"><a class="hero__home" href="<?php echo get_home_url(); ?>">Компания "Эксперты"
              | </a><span class="hero__active-page">Дренаж участка</span></div>
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

    <!-- 2. Краткий оффер + доверие -->
<section class="advantages wrapper">
        <h2 class="advantages__title"><?php echo esc_html($cat87_offer_title ? $cat87_offer_title : 'Наши преимущества'); ?></h2>
        <div class="advantages__how">
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="512" width="512">
                <path class="active-path" d="M505 50H271V8c0-5-4-8-8-8h-47c-4 0-7 3-7 8v42h-92c-4 0-7 3-7 7v65c-5 2-10 6-14 10v-22c0-14-13-25-34-29V65c0-4-3-8-7-8-13 0-27 6-37 14a51 51 0 00-18 40v31c0 10 15 10 15 0v-31c0-17 12-34 32-38v288c-11 1-23 6-32 14V182c0-10-15-10-15 0v234c1 22 21 39 48 39 13 0 25-4 33-10v27c0 26 26 40 48 40 24 0 48-14 48-40V366h214L235 499c-5 4-2 13 5 13h226c4 0 8-3 8-8v-36c0-10-15-10-15 0v29H261l198-169v99c0 9 15 9 15 0v-61h31c4 0 7-3 7-7V57c0-4-3-7-7-7zm-8 15v182H321V65zM256 15v192h-32v-19h5c10 0 10-15 0-15h-5v-20h12c10 0 10-15 0-15h-12v-20h5a8 8 0 000-15h-5V84h12c10 0 10-15 0-15h-12V49h5c10 0 10-15 0-15h-5V15zM118 134c4-2 7-3 11-3v287c-9 1-22 5-33 15V168c0-13 8-28 22-34zm44 316c-9-5-20-7-32-7v-10h6c5-1 7-3 8-8V154c10 3 18 8 18 13zM81 110v283c-8-5-20-8-32-8v-9l6-1c4 0 7-2 7-7V97c12 2 19 8 19 13zm0 308c0 12-15 22-33 22-19 0-33-11-33-25s5-28 19-35v13c0 5 3 7 8 7 10-1 22 1 31 6 5 3 9 6 8 12zm48 79c-18 0-33-11-33-25s5-27 19-34v12c0 5 3 8 8 8 13-1 40 1 39 18 0 11-15 21-33 21zm48-330c0-13-13-25-33-28v-17c-1-4-3-7-8-7l-11 1V65h84v149c0 5 3 8 7 8h47c4 0 8-3 8-8V65h35v286H177zm292 138c-2-1-6 0-8 1l-52 45h-88v-89h176v89h-23v-39c0-3-2-5-5-7z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M357 215h69l6-2 34-35c2-1 3-3 3-5l-1-69c0-4-3-8-7-8h-69c-2 0-4 1-5 3l-35 34-2 5v69c0 5 3 8 7 8zm8-69h54v54h-54zm69 43v-47l20-20v48zm-39-78h48l-20 20h-48zM393 314h-25c-10 0-10 15 0 15h25c10 0 10-15 0-15zM432 284h-64c-10 0-10 15 0 15h64c9 0 9-15 0-15zM425 385l-91 77c-5 5-2 14 5 14h91c4 0 7-4 7-8v-77c0-6-7-10-12-6zm-3 76h-63l63-54z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description"><?php echo esc_html($cat87_trust_titles[0]); ?></p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
                <path class="active-path" d="M110 496l-15-21a10 10 0 10-17 12l16 21a10 10 0 1016-12zM225 500l-16-78c-8-38-30-71-62-93l-35-23c-14-10-33-8-45 4V190c0-16-11-29-26-33a33 33 0 00-41 33v155c0 20 6 40 18 56l18 25a10 10 0 1016-11l-18-25c-9-13-14-29-14-45V190a13 13 0 0116-13c7 1 11 7 11 13v123a70 70 0 0020 49l21 23 11 11 15 16a10 10 0 0015-13l-26-27-22-25h-1c-5-6-5-16 1-22 5-6 13-7 19-3l35 24c28 19 47 47 54 80l17 78a10 10 0 0019-4z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M74 446a10 10 0 00-16 11 10 10 0 1016-11zM499 164c-7-7-18-9-28-7-15 4-26 17-26 33v120a35 35 0 00-45-4l-35 23c-32 22-54 55-62 93l-16 78a10 10 0 1019 4l17-78c7-33 26-61 54-80l35-24c6-4 14-3 19 3 6 6 6 16 1 22h-1l-48 52a10 10 0 0015 13l47-50 2-2c12-13 18-30 18-47V190c0-6 4-12 11-13a13 13 0 0116 13v155c0 16-5 32-14 45l-76 106a10 10 0 0016 12l76-107c12-16 18-36 18-56V190c0-10-5-20-13-26z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M383 192l-18-5v-3c11-8 19-21 19-36v-24a45 45 0 00-74-34 58 58 0 00-108 0c-8-6-18-10-29-10-25 0-45 20-45 44v24c0 15 8 28 19 36v3l-18 5c-21 5-36 24-36 45v19c0 6 5 10 10 10h46v40c0 5 5 10 10 10h60a10 10 0 000-20h-10v-21a10 10 0 00-20 0v21h-20v-26c0-20 13-36 32-41l28-6 18 42c1 3 5 6 9 6s8-3 9-6l19-42 27 6c19 5 32 21 32 41v26h-20v-21a10 10 0 00-20 0v21h-11a10 10 0 000 20h61c5 0 10-5 10-10v-36-4h46c5 0 10-4 10-10v-19c0-21-15-40-36-45zm-44-92c13 0 24 10 25 23h-14c-12 0-23-3-33-8 3-9 12-15 22-15zm-24 46v-10c11 4 23 7 35 7h14v5a25 25 0 01-49 0v-2zm-97-34a38 38 0 0176-6l-17-10c-4-2-9-1-13 3-8 9-20 15-33 15h-13v-2zm-45-12c10 0 19 6 23 15-11 5-22 8-34 8h-14c1-13 12-23 25-23zm-25 43h14c12 0 24-3 36-7v12a25 25 0 01-50 0v-5zm48 67c-19 5-35 18-42 36h-41v-9c0-12 9-23 21-26l26-6c4-1 7-5 7-10v-3a45 45 0 0011 0v3a10 10 0 009 10l14 4-5 1zm28-16l-8-2-18-5v-3c4-2 7-5 9-8 5 7 10 13 17 18zm44 15l-12 27-12-27v-7a58 58 0 0024 0v7zm-12-26c-21 0-38-17-38-38v-11h13c16 0 31-6 43-16l20 12v16c0 21-17 37-38 37zm32 11c7-5 13-11 17-18 3 3 5 6 9 8v3l-18 5-8 2zm111 52h-41c-7-18-23-31-42-36l-5-1 15-4a10 10 0 008-10v-3a45 45 0 0011 0v3c0 5 3 9 8 10l25 6c12 3 21 14 21 26v9z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M263 299a10 10 0 00-14 0 10 10 0 000 14 10 10 0 0014 0c2-2 3-5 3-7 0-3-1-6-3-7zM256 0c-6 0-10 4-10 10v15a10 10 0 0020 0V10c0-6-4-10-10-10zM219 33l-10-11a10 10 0 10-14 14l10 11a10 10 0 0014 0c4-4 4-10 0-14zM317 22c-4-4-10-4-14 0l-10 11a10 10 0 0014 14l10-10c4-4 4-11 0-15z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description"><?php echo esc_html($cat87_trust_titles[1]); ?></p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" height="512" viewBox="0 0 516 516" width="512">
                <path class="active-path" d="M409 411a10 10 0 10-13 16l18 13a10 10 0 0013-1l33-36a10 10 0 10-15-13l-27 29z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M515 358c0-5-4-9-9-10-24-2-53-18-75-40-2-2-4-4-7-4s-5 2-7 4c-10 10-21 19-33 25a181 181 0 00-82-52c25-25 41-57 41-86v-16a33 33 0 00-1-61c-5-50-40-92-89-106-1-7-7-12-14-12h-37c-7 0-12 5-14 11a124 124 0 00-91 107 33 33 0 00-2 61v16c0 29 17 61 42 86a205 205 0 00-8 3c-33 11-60 31-82 58-20 26-35 58-43 95-3 14-5 31 4 42s24 12 37 12h66a10 10 0 000-20H45c-12 0-19-1-22-5-3-3-3-11 0-24 11-47 36-104 97-133-2 34 17 56 28 70a10 10 0 0015 0l56-54 57 54a10 10 0 0014 0c12-14 30-36 28-70 18 8 34 20 47 34-8 3-16 5-23 5-5 1-9 5-9 10a168 168 0 0035 113H201a10 10 0 000 20h183c12 14 26 25 40 25 32 0 69-66 70-67 16-30 22-55 21-91zM322 115h-56c-10-27-12-49-12-82 36 13 62 45 68 82zM207 20h27c0 39 1 65 11 95h-49c10-30 11-56 11-95zm-20 12c0 34-2 56-12 83h-58c6-38 34-71 70-83zm-78 103h221a13 13 0 010 27H109a13 13 0 010-27zm6 60v-13h208v13c0 38-37 85-79 101-18 6-31 6-50 0-42-16-79-63-79-101zm42 162a68 68 0 01-16-57l14-3a134 134 0 0043 21zm125 0l-41-39a120 120 0 0043-21l13 3c5 26-5 44-15 57zm194 83c-12 22-40 56-52 56s-40-34-52-56c-13-25-19-45-19-73a126 126 0 0034-12c13-7 26-16 37-26 21 19 47 33 71 38 0 28-6 48-19 73z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M156 471a10 10 0 000 20 10 10 0 100-20z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description"><?php echo esc_html($cat87_trust_titles[2]); ?></p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 516 516" width="512" height="512">
                <path class="active-path" d="M473 461l36-37a9 9 0 00-6-15h-68v-34c0-9-7-17-17-17H94c-10 0-17 8-17 17v34H9a9 9 0 00-6 15l36 37-36 36a9 9 0 006 15h153c5 0 9-4 9-9v-42h170v42c0 5 4 9 9 9h153a9 9 0 006-15l-36-36zm-319 34H29l28-28a9 9 0 000-12l-28-29h48v18c0 9 7 17 17 17h60v34zm-60-51v-69h324v69H94zm264 51v-34h60c10 0 17-8 17-17v-18h48l-28 29a9 9 0 000 12l28 28H358zM33 272l-7 42a9 9 0 0013 9l38-20 38 20a9 9 0 0012-9l-7-42 31-29a9 9 0 00-5-15l-42-6-20-38a9 9 0 00-15 0l-19 38-43 6a9 9 0 00-4 15l30 29zm24-34c3 0 5-2 6-4l14-27 13 27c2 2 4 4 7 4l30 4-22 21c-2 2-3 5-2 8l5 29-27-14h-8l-27 14 5-29c1-3 0-6-2-8l-22-21 30-4zM359 234c-1 3 0 6 2 9l31 29-7 42a9 9 0 0012 9l38-20 38 20a9 9 0 0013-9l-7-42 30-29a9 9 0 00-4-15l-43-6-19-38a9 9 0 00-15 0l-20 38-42 6c-4 0-6 3-7 6zm56 4c3 0 5-2 7-4l13-27 14 27c1 2 3 4 6 4l30 4-22 21c-2 2-3 5-2 8l5 29-27-14h-8l-27 14 5-29c1-3 0-6-2-8l-22-21 30-4zM187 148l-13 72a9 9 0 0012 9l70-34 70 34a9 9 0 0012-9l-13-72 56-52a9 9 0 00-4-15l-79-10-34-67a9 9 0 00-16 0l-34 67-79 10a9 9 0 00-4 15l56 52zm33-61c3 0 5-2 7-4l29-56 29 56c2 2 4 4 7 4l64 9-46 42c-2 2-3 5-3 8l11 61-58-29c-3-2-5-2-8 0l-58 29 11-61c0-3-1-6-3-8l-46-42 64-9z" data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description"><?php echo esc_html($cat87_trust_titles[3]); ?></p>
          </div>
        </div>
      </section>

    <!-- 3. Блок "Когда нужен дренаж" -->
    <section class="services wrapper">
      <h2 class="services__title">Когда нужен дренаж</h2>
      <div class="services__cards columns3">
        <?php
        $posts = get_posts(array(
          'numberposts' => -1,
          'post_type' => 'post',
          'orderby' => 'date',
          'order' => 'DESC',
          'suppress_filters' => true,
          'tax_query' => array(
            array(
              'taxonomy' => 'category',
              'field' => 'term_id',
              'terms' => array(87, 72),
              'operator' => 'AND'
            )
          )
        ));

        foreach ($posts as $post) {
          setup_postdata($post);
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="<?php the_post_thumbnail_url(); ?>" alt="<?php the_title(); ?>">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title"><?php the_title(); ?></h5>
            <?php the_excerpt(); ?>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php the_permalink(); ?>">Подробнее</a>
            </div>
          </div>
        </div>
        <?php } wp_reset_postdata(); ?>
      </div>
    </section>

    <!-- 4. Виды дренажа (ключевой SEO блок) -->
    <section class="services wrapper">
      <h2 class="services__title">Виды дренажа</h2>
      <div class="services__cards columns3">
        <?php
        $drainage_posts = get_posts(array(
          'numberposts' => -1,
          'post_type' => 'post',
          'orderby' => 'date',
          'order' => 'DESC',
          'suppress_filters' => true,
          'tax_query' => array(
            array(
              'taxonomy' => 'category',
              'field' => 'term_id',
              'terms' => array(87, 74),
              'operator' => 'AND'
            )
          )
        ));

        foreach ($drainage_posts as $post) {
          setup_postdata($post);
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="<?php the_post_thumbnail_url(); ?>" alt="<?php the_title(); ?>">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title"><?php the_title(); ?></h5>
            <?php the_excerpt(); ?>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php the_permalink(); ?>">Подробнее</a>
            </div>
          </div>
        </div>
        <?php } wp_reset_postdata(); ?>
      </div>
    </section>

    <!-- 5. Our Works with ACF field selection -->
    <section class="services wrapper casesCustom">
      <h2 class="services__title">Наши работы</h2>
      <div class="services__cards columns3">
        <?php
        // Get selected posts from ACF field
        $selected_posts = get_field('selected_works_posts', 'category_' . get_queried_object_id());
        
        if ($selected_posts && !empty($selected_posts)) {
          foreach ($selected_posts as $post_id) {
            $post = get_post($post_id);
            setup_postdata($post);
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <?php if (has_post_thumbnail($post_id)): ?>
              <img class="service__img" src="<?php echo get_the_post_thumbnail_url($post_id); ?>" alt="<?php echo get_the_title($post_id); ?>">
            <?php else: ?>
              <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/default-case.jpg" alt="<?php echo get_the_title($post_id); ?>">
            <?php endif; ?>
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title"><?php echo get_the_title($post_id); ?></h5>
            <?php 
            $excerpt = get_the_excerpt($post_id);
            if (empty($excerpt)) {
              $excerpt = wp_trim_words(get_post_field('post_content', $post_id), 15);
            }
            echo '<p>' . $excerpt . '</p>';
            ?>
            <p><strong><?php echo get_field('price', $post_id) ? 'от ' . get_field('price', $post_id) : 'Цена по запросу'; ?></strong></p>
            <div class="service__link-wrap">
              <a class="service__link" href="<?php echo get_permalink($post_id); ?>">Подробнее</a>
            </div>
          </div>
        </div>
        <?php 
          }
          wp_reset_postdata();
        } else {
          // Fallback to default static cards if no posts selected
        ?>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/case1.jpg" alt="Дренаж 6 соток">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title">Дренаж 6 соток</h5>
            <p>Комплексный дренаж частного дома с установкой колодцев и дренажа в ливневую канализацию</p>
            <p><strong>от 250 000 РУБ</strong></p>
          </div>
        </div>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/case2.jpg" alt="Дренаж вокруг дома">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title">Дренаж вокруг дома</h5>
            <p>Пристенный дренаж для защиты фундамента от грунтовых вод с установкой дренажных труб</p>
            <p><strong>от 180 000 ₽</strong></p>
          </div>
        </div>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/case3.jpg" alt="Поверхностный дренаж">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title">Поверхностный дренаж</h5>
            <p>Ливневая канализация для отвода дождевых и талых вод с участка</p>
            <p><strong>от 120 000 ₽</strong></p>
          </div>
        </div>
        <div class="service" data-aos="fade-up" data-aos-duration="400">
          <div class="service__img-wrap">
            <img class="service__img" src="/wp-content/themes/theme/assets/img/cases/case4.jpg" alt="Дренаж заболоченного участка">
          </div>
          <div class="service__text-wrap">
            <h5 class="service__title">Дренаж заболоченного участка</h5>
            <p>Комплексное осушение проблемного участка с глубоким дренажом и системой колодцев</p>
            <p><strong>от 450 000 ₽</strong></p>
          </div>
        </div>
        <?php } ?>
      </div>
      <div style="text-align: center; margin-top: 30px;">
        <a href="/fotogalereja/" class="btn--primary-custom">Смотреть все работы</a>
      </div>
    </section>

    <!-- 6. Цены (укороченная версия) -->
    <section class="services wrapper portfolio">
      <h2 class="services__title"><?php echo esc_html($cat87_prices_title ? $cat87_prices_title : 'Стоимость дренажа участка'); ?></h2>
      <div style="overflow-x: auto; margin-bottom: 30px;">
        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #fff;">
          <thead>
            <tr style="background: #f5f5f5;">
              <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Услуга</th>
              <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Цена за метр</th>
              <th style="padding: 15px; text-align: left; border: 1px solid #ddd; font-weight: 700; font-size: 16px;">Сроки</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($cat87_price_rows as $cat87_price_row) : ?>
            <tr>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($cat87_price_row['service']) ? $cat87_price_row['service'] : ''); ?></td>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($cat87_price_row['price']) ? $cat87_price_row['price'] : ''); ?></td>
              <td style="padding: 15px; border: 1px solid #ddd; background: #fff;"><?php echo esc_html(!empty($cat87_price_row['term']) ? $cat87_price_row['term'] : ''); ?></td>
            </tr>
            <?php endforeach; ?>
          </tbody>
        </table>
      </div>
      <div class="price-example">
        <h3><?php echo esc_html($cat87_estimate_title ? $cat87_estimate_title : 'Пример сметы на дренаж участка 10 соток'); ?></h3>
        <ul>
          <?php foreach ($cat87_estimate_items as $cat87_estimate_item) : ?>
          <li><?php echo esc_html(!empty($cat87_estimate_item['item']) ? $cat87_estimate_item['item'] : ''); ?></li>
          <?php endforeach; ?>
          <li><strong><?php echo esc_html($cat87_estimate_total ? $cat87_estimate_total : 'Итого: 615 000 ₽'); ?></strong></li>
        </ul>
        <a href="<?php echo esc_url($cat87_prices_link_url ? $cat87_prices_link_url : '/drenazh-uchastka/cena/'); ?>" class="btn--outline-custom"><?php echo esc_html($cat87_prices_link_text ? $cat87_prices_link_text : 'Подробные цены'); ?></a>
      </div>
    </section>

    <!-- 7. Как мы работаем -->
    <section class="advantages wrapper howWorkCustom">
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
    </section>

    

    <!-- 8. Блок SEO текста -->
    <section class="services wrapper">
      <div class="seo-text" style="line-height: 1.6; margin-bottom: 40px;">
       <?php the_content(); ?>
      </div>
    </section>

    <!-- 9. FAQ -->
    <section class="services wrapper">
      <h2 class="services__title"><?php echo esc_html($cat87_faq_title ? $cat87_faq_title : 'Ответы на частые вопросы'); ?></h2>
      <div style="margin-bottom: 30px;">
        <?php foreach ($cat87_faq_items as $cat87_faq_item) : ?>
        <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
          <div style="background: #f5f5f5; padding: 20px; cursor: pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'block' ? 'none' : 'block'">
            <h3 class="faq-toggle">
              <?php echo esc_html(!empty($cat87_faq_item['question']) ? $cat87_faq_item['question'] : ''); ?>
              <span>+</span>
            </h3>
          </div>
          <div class="faq-answer" style="padding: 20px; display: none; border-top: 1px solid #ddd;">
            <p><?php echo esc_html(!empty($cat87_faq_item['answer']) ? $cat87_faq_item['answer'] : ''); ?></p>
          </div>
        </div>
        <?php endforeach; ?>
      </div>
    </section>

    <section class="advantages wrapper">
      <div style="text-align: center; background: #f9f9f9; padding: 40px; border-radius: 10px;">
        <h2 class="cta-title">Получите расчет дренажа участка за 1 день</h2>
        <p style="margin-bottom: 30px;">Оставьте заявку и наш специалист свяжется с вами для бесплатной консультации</p>
        <form class="cta-form" id="calc" style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
          <input type="text" placeholder="Ваше имя" required style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
          <input type="tel" placeholder="Ваш телефон" required style="padding: 15px; border: 1px solid #ddd; border-radius: 5px; min-width: 200px;">
          <button type="submit" class="cta-btn-custom">Получить расчет</button>
        </form>
      </div>
    </section>
    

<?php get_footer(); ?>
