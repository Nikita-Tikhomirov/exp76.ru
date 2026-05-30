<?php
/*
Template Name: Фотогалерея
*/

add_filter('the_title', function ($title, $post_id) {
  if ((int) $post_id === (int) get_queried_object_id() && is_page_template('portfolio.php')) {
    return 'Примеры работ по благоустройству участков';
  }

  return $title;
}, 10, 2);

add_filter('aioseo_title', function ($title) {
  return is_page_template('portfolio.php')
    ? 'Примеры работ по благоустройству участков в Рыбинске и области'
    : $title;
}, 30, 1);

add_filter('aioseo_description', function ($description) {
  return is_page_template('portfolio.php')
    ? 'Фото выполненных работ: дренаж участка, ливневая канализация, отмостка, тротуарная плитка, автополив, газон и благоустройство под ключ.'
    : $description;
}, 30, 1);
?>

<?php get_header('page'); ?>

<section class="portfolio wrapper">

  <div class="portfolio__bg-left" data-aos="fade-right" data-aos-duration="600"><img
      src="<?php echo get_template_directory_uri() ?>/img/bg-left.png" alt="" role="presentation"></div>
  <h2 class="portfolio__title" data-aos="fade-right" data-aos-duration="700">Фотогалерея выполненных работ</h2>
  <div class="portfolio-seo-intro" data-aos="fade-up" data-aos-duration="700">
    <p>В этом разделе собраны реальные примеры работ компании «Эксперты» по благоустройству частных участков в Рыбинске, Ярославле и Ярославской области. По фотографиям можно посмотреть качество мощения, дренажа, ливневой канализации, отмостки, автополива, газона, планировки и комплексных работ на участках.</p>
    <div class="portfolio-seo-intro__actions">
      <a href="/services/" class="portfolio-seo-btn">Каталог услуг</a>
      <a href="#portfolio-cases" class="portfolio-seo-btn portfolio-seo-btn--light">Смотреть работы</a>
      <a href="#form" class="portfolio-seo-btn portfolio-seo-btn--light openPopup" data-modal="#popup">Обсудить участок</a>
    </div>
  </div>

  <section class="portfolio-directions">
    <h2 class="portfolio-directions__title">Примеры работ по направлениям</h2>
    <div class="portfolio-directions__grid">
      <a href="/category/drenazh-uchastka/">Дренаж участка</a>
      <a href="/category/osushenie-uchastka/">Осушение участка</a>
      <a href="/category/livnevaya-kanalizatsiya/">Ливневая канализация</a>
      <a href="/category/otmostka-vokrug-doma/">Отмостка вокруг дома</a>
      <a href="/category/ukladka-trotuarnoy-plitki/">Укладка тротуарной плитки</a>
      <a href="/category/avtopoliv-na-uchastke/">Автополив на участке</a>
    </div>
  </section>

	<style>
    .portfolio-seo-intro {
      max-width: 1000px;
      margin-bottom: 36px;
      padding: 28px 32px;
      background: rgba(255,255,255,.92);
      border-left: 4px solid #0a9215;
      box-shadow: 0 5px 18px rgba(0,0,0,.12);
    }
    .portfolio-seo-intro p {
      margin: 0;
      color: #555;
      font-size: 19px;
      line-height: 1.65;
    }
    .portfolio-seo-intro__actions {
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-top: 22px;
    }
    .portfolio-seo-btn {
      display: inline-flex;
      min-height: 42px;
      align-items: center;
      justify-content: center;
      padding: 8px 22px;
      border: 2px solid #0a9215;
      border-radius: 24px;
      background: #0a9215;
      color: #fff;
      font-weight: 700;
      text-decoration: none;
      box-shadow: 0 5px 14px rgba(10,146,21,.2);
    }
    .portfolio-seo-btn--light {
      background: #fff;
      color: #0a9215;
    }
    .portfolio-directions {
      margin-bottom: 42px;
    }
    .portfolio-directions__title {
      margin: 0 0 22px;
      font-family: "Poiret One", cursive;
      font-size: 38px;
      font-weight: 800;
      color: #333;
      text-shadow: 1px 2px 3px #00000036;
    }
    .portfolio-directions__grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }
    .portfolio-directions__grid a {
      display: flex;
      align-items: center;
      min-height: 70px;
      padding: 16px 18px;
      background: #fff;
      border-left: 4px solid #ff5e00;
      color: #333;
      font-size: 18px;
      font-weight: 700;
      text-decoration: none;
      box-shadow: 0 4px 14px rgba(0,0,0,.12);
    }
    .case-container{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-gap: 30px;
      margin-top: 20px;
    }
    .case-container .case{
      height: 100%;
    }
    .case-container .case .case__img-wrap{
      height: 250px;
    }

    .case__title{
      font-size: 26px;
      margin-bottom: 10px;
      line-height: 1.2;
    }
    .case__description{
      font-size: 16px;
    }
    .portfolio-seo-bottom {
      margin-top: 42px;
      display: grid;
      grid-template-columns: 1.1fr .9fr;
      gap: 28px;
      align-items: start;
    }
    .portfolio-seo-bottom__box {
      background: rgba(255,255,255,.92);
      padding: 26px 30px;
      box-shadow: 0 5px 18px rgba(0,0,0,.12);
      border-top: 4px solid #0a9215;
    }
    .portfolio-seo-bottom h2 {
      margin: 0 0 18px;
      font-family: "Poiret One", cursive;
      font-size: 36px;
      font-weight: 800;
      color: #333;
    }
    .portfolio-seo-bottom p,
    .portfolio-seo-bottom li {
      color: #555;
      font-size: 17px;
      line-height: 1.6;
    }
    .portfolio-seo-bottom ul {
      margin: 0;
      padding-left: 20px;
    }
		
    @media only screen and (max-width: 991px) {
      .case-container{
        grid-template-columns: 1fr 1fr;
      }
      .portfolio-directions__grid,
      .portfolio-seo-bottom { grid-template-columns: 1fr; }
    }
		@media only screen and (max-width: 768px) {
			.case-container{
    		grid-template-columns: 1fr;
    		grid-gap: 30px;
			}
			.case-container .case .case__img-wrap{
				    height: 200px;
			}
      .portfolio-seo-intro { padding: 24px 20px; }
      .portfolio-directions__title { font-size: 31px; }
		}
		
	</style>

<?php
$paged = (get_query_var('paged')) ? get_query_var('paged') : 1;

$query = new WP_Query(array(
  'post_type'      => 'page',
  'posts_per_page' => 9,
  'category__in'   => array(75),
  'orderby'        => 'date',
  'order'          => 'DESC',
  'paged'          => $paged,
));

if ($query->have_posts()): ?>

  <h2 class="portfolio-directions__title" id="portfolio-cases">Реализованные объекты</h2>
  <div class="case-container">

    <?php while ($query->have_posts()):
      $query->the_post(); ?>

      <div class="case swiper-slide">
        <div class="case__img-wrap">
          <?php
          $thumb_large  = get_the_post_thumbnail_url(null, 'large');
          $thumb_medium = get_the_post_thumbnail_url(null, 'medium');
          $alt          = sprintf('Пример работ по благоустройству участка: %s', get_the_title());
          ?>
          <img class="case__img" src="<?php echo $thumb_medium; ?>"
            srcset="<?php echo $thumb_medium; ?> 768w, <?php echo $thumb_large; ?> 1200w"
            sizes="(max-width: 768px) 768px, 1200px" alt="<?php echo esc_attr($alt); ?>" />
        </div>

        <div class="case__content">
          <h3 class="case__title"><?php the_title(); ?></h3>
          <div class="case__description"><?php the_excerpt(); ?></div>
          <a class="case__link" href="<?php the_permalink(); ?>">Подробнее</a>
        </div>
      </div>

    <?php endwhile; ?>

  </div>

  <!-- Пагинация -->
  <div class="pagination">
    <?php
    echo paginate_links(array(
      'total'     => $query->max_num_pages,
      'current'   => $paged,
      'prev_text' => '«',
      'next_text' => '»',
    ));
    ?>
  </div>

<?php endif;

wp_reset_postdata();
?>

  <section class="portfolio-seo-bottom">
    <div class="portfolio-seo-bottom__box">
      <h2>Что показывают примеры работ</h2>
      <p>Фотогалерея помогает оценить не только внешний вид участка после благоустройства, но и состав работ: подготовку основания, уклоны, водоотвод, мощение, газон, посадки, дренажные и ливневые системы. Для новых объектов мы подбираем решение под грунт, рельеф, дом, дорожки и будущую эксплуатацию участка.</p>
    </div>
    <div class="portfolio-seo-bottom__box">
      <h2>Какие работы можно заказать</h2>
      <ul>
        <li>комплексное благоустройство участка под ключ;</li>
        <li>дренаж, осушение и ливневая канализация;</li>
        <li>отмостка, тротуарная плитка, дорожки и площадки;</li>
        <li>газон, посадки, автополив и уход за участком.</li>
      </ul>
    </div>
  </section>

  <script type="application/ld+json">
  <?php
  echo wp_json_encode(array(
    '@context' => 'https://schema.org',
    '@type' => 'CollectionPage',
    'name' => 'Примеры работ по благоустройству участков',
    'description' => 'Фото выполненных работ компании Эксперты по благоустройству участков в Рыбинске и Ярославской области.',
    'url' => get_permalink(),
    'about' => array(
      'дренаж участка',
      'осушение участка',
      'ливневая канализация',
      'отмостка вокруг дома',
      'укладка тротуарной плитки',
      'автополив',
      'благоустройство участка'
    ),
  ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  ?>
  </script>


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

<?php get_footer(); ?>
