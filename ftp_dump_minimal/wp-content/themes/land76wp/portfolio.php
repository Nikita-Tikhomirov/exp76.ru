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

if (!function_exists('land76_portfolio_case_groups')) {
  function land76_portfolio_case_groups($post_id) {
    $text = mb_strtolower(
      get_the_title($post_id) . ' ' .
      get_the_excerpt($post_id) . ' ' .
      wp_strip_all_tags(get_post_field('post_content', $post_id))
    );
    $groups = array();

    if (preg_match('/дренаж|водоотвод|ливнев|осуш|канав|вода|лотк|дождеприем/u', $text)) {
      $groups[] = 'vodootvod';
    }
    if (preg_match('/плитк|брусчат|мощен|дорожк|площадк|парковк|бордюр|слип/u', $text)) {
      $groups[] = 'moshenie';
    }
    if (preg_match('/газон|посад|озелен|сад|пруд|водоем|дерев|кустар|цветник|растен/u', $text)) {
      $groups[] = 'ozelenenie';
    }
    if (preg_match('/автополив|полив|спринклер|капельн/u', $text)) {
      $groups[] = 'avtopoliv';
    }

    if (count($groups) > 1 || !$groups) {
      $groups[] = 'complex';
    }

    return array_unique($groups);
  }
}
?>

<?php get_header('page'); ?>

<section class="portfolio wrapper">

  <div class="portfolio__bg-left" data-aos="fade-right" data-aos-duration="600"><img
      src="<?php echo get_template_directory_uri() ?>/img/bg-left.png" alt="" role="presentation"></div>
  <h2 class="portfolio__title" data-aos="fade-right" data-aos-duration="700">Фотогалерея выполненных работ</h2>
  <div class="portfolio-seo-intro" data-aos="fade-up" data-aos-duration="700">
    <p>Реальные объекты компании «Эксперты» по благоустройству частных участков в Рыбинске, Ярославле и области: мощение, водоотвод, озеленение, автополив и комплексные работы.</p>
    <div class="portfolio-seo-intro__actions">
      <a href="/services/" class="portfolio-seo-btn">Каталог услуг</a>
      <a href="#portfolio-cases" class="portfolio-seo-btn portfolio-seo-btn--light">Смотреть работы</a>
      <a href="#form" class="portfolio-seo-btn portfolio-seo-btn--light openPopup" data-modal="#popup">Обсудить участок</a>
    </div>
  </div>

  <section class="portfolio-directions">
    <h2 class="portfolio-directions__title">Выберите тип работ</h2>
    <div class="portfolio-tabs" aria-label="Фильтр примеров работ">
      <button class="portfolio-tabs__button is-active" type="button" data-case-filter="all">Все работы</button>
      <button class="portfolio-tabs__button" type="button" data-case-filter="moshenie">Мощение и дорожки</button>
      <button class="portfolio-tabs__button" type="button" data-case-filter="vodootvod">Водоотвод</button>
      <button class="portfolio-tabs__button" type="button" data-case-filter="ozelenenie">Озеленение</button>
      <button class="portfolio-tabs__button" type="button" data-case-filter="avtopoliv">Автополив</button>
      <button class="portfolio-tabs__button" type="button" data-case-filter="complex">Комплексные работы</button>
    </div>
  </section>

	<style>
    .portfolio-seo-intro {
      width: 100%;
      max-width: none;
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
      font-weight: 600;
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
      font-weight: 600;
      color: #333;
      text-shadow: 1px 2px 3px #00000036;
    }
    .portfolio-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }
    .portfolio-tabs__button {
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 44px;
      padding: 9px 18px;
      background: #fff;
      border: 2px solid #0a9215;
      border-radius: 24px;
      color: #333;
      font-size: 16px;
      font-weight: 600;
      box-shadow: 0 4px 14px rgba(0,0,0,.12);
    }
    .portfolio-tabs__button.is-active,
    .portfolio-tabs__button:hover {
      background: #0a9215;
      color: #fff;
    }
    .case-container{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-gap: 30px;
      align-items: start;
      margin-top: 20px;
    }
    .case-container .case{
      display: flex;
      flex-direction: column;
      height: auto;
      margin-bottom: 0;
    }
    .case-container .case .case__img-wrap{
      height: 250px;
      flex: 0 0 auto;
      width: 100%;
      flex-basis: auto;
    }
    .case-container .case .case__img{
      width: 100%;
      height: 100%;
      object-fit: cover;
    }
    .case-container .case .case__content{
      display: flex;
      flex: 0 0 auto;
      flex-direction: column;
      justify-content: flex-start;
      padding: 24px 28px 28px;
      border-left: 4px solid #ff5e00ce;
      border-top: 0;
    }

    .case__title{
      font-size: 26px;
      margin-bottom: 10px;
      line-height: 1.2;
    }
    .case__description{
      font-size: 16px;
      line-height: 1.55;
      margin-bottom: 18px;
    }
    .case-container .case .case__link{
      position: relative !important;
      left: 0 !important;
      bottom: 0 !important;
      display: inline-flex;
      width: fit-content;
      margin-top: 0;
    }
    .portfolio-case-pagination {
      display: flex;
      flex-wrap: wrap;
      justify-content: center;
      gap: 10px;
      margin: 34px 0 0;
    }
    .portfolio-case-pagination:empty {
      display: none;
    }
    .portfolio-case-pagination__button {
      min-width: 42px;
      min-height: 42px;
      padding: 7px 14px;
      border-radius: 10px;
      border: 2px solid #0a9215;
      background: #fff;
      color: #333;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0,0,0,.1);
    }
    .portfolio-case-pagination__button.is-active,
    .portfolio-case-pagination__button:hover {
      background: #0a9215;
      color: #fff;
    }
    .portfolio-empty {
      max-width: 760px;
      margin: 24px 0 0;
      padding: 18px 22px;
      background: rgba(255,255,255,.92);
      border-left: 4px solid #0a9215;
      color: #555;
      font-size: 17px;
      line-height: 1.55;
      box-shadow: 0 4px 14px rgba(0,0,0,.1);
    }
    .case.is-hidden {
      display: none;
    }
    .portfolio-empty.is-hidden {
      display: none;
    }
    .portfolio-services,
    .portfolio-seo-text {
      width: 100%;
      max-width: none;
      margin: 46px 0 0;
      padding: 28px 32px;
      background: rgba(255,255,255,.94);
      border-left: 4px solid #0a9215;
      box-shadow: 0 5px 18px rgba(0,0,0,.12);
      color: #555;
      font-size: 17px;
      line-height: 1.65;
    }
    .portfolio-services__lead,
    .portfolio-seo-text p {
      margin: 0 0 18px;
    }
    .portfolio-services__grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-top: 22px;
    }
    .portfolio-services__card {
      display: block;
      min-height: 116px;
      padding: 18px 20px;
      background: #fff;
      border-left: 4px solid #ff5e00ce;
      box-shadow: 0 4px 14px rgba(0,0,0,.12);
      color: #555;
      transition: .2s;
    }
    .portfolio-services__card:hover {
      transform: translateY(-3px);
      box-shadow: 0 7px 18px rgba(0,0,0,.16);
    }
    .portfolio-services__card strong {
      display: block;
      margin-bottom: 8px;
      color: #0a9215;
      font-size: 18px;
      line-height: 1.25;
    }
    .portfolio-services__card span {
      display: block;
      font-size: 15px;
      line-height: 1.5;
    }
    .portfolio-seo-list {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 10px 24px;
      margin: 18px 0;
      list-style: none;
    }
    .portfolio-seo-list li {
      position: relative;
      padding-left: 24px;
    }
    .portfolio-seo-list li:before {
      content: "";
      position: absolute;
      left: 0;
      top: .7em;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #0a9215;
      box-shadow: 0 0 0 4px rgba(10,146,21,.12);
    }
		
    @media only screen and (max-width: 991px) {
      .case-container{
        grid-template-columns: 1fr 1fr;
      }
      .portfolio-services__grid {
        grid-template-columns: repeat(2, 1fr);
      }
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
      .case-container .case .case__content { padding: 22px 20px 24px; }
      .portfolio-services,
      .portfolio-seo-text { padding: 24px 20px; }
      .portfolio-services__grid,
      .portfolio-seo-list {
        grid-template-columns: 1fr;
      }
		}
		
	</style>

<?php
$paged = (get_query_var('paged')) ? get_query_var('paged') : 1;

$query = new WP_Query(array(
  'post_type'      => 'page',
  'posts_per_page' => -1,
  'category__in'   => array(75),
  'orderby'        => 'date',
  'order'          => 'DESC',
  'paged'          => $paged,
));

if ($query->have_posts()): ?>

  <h2 class="portfolio-directions__title" id="portfolio-cases">Реализованные объекты</h2>
  <div class="case-container">

    <?php while ($query->have_posts()):
      $query->the_post();
      $case_groups = land76_portfolio_case_groups(get_the_ID());
      ?>

      <div class="case swiper-slide" data-case-groups="<?php echo esc_attr(implode(' ', $case_groups)); ?>">
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
          <div class="case__description"><?php echo esc_html(wp_trim_words(get_the_excerpt(), 14, '...')); ?></div>
          <a class="case__link" href="<?php the_permalink(); ?>">Подробнее</a>
        </div>
      </div>

    <?php endwhile; ?>

  </div>
  <p class="portfolio-empty is-hidden">В этом разделе пока нет выбранных работ. Посмотрите все объекты или оставьте заявку, и мы подберем похожие примеры под вашу задачу.</p>
  <div class="portfolio-case-pagination" aria-label="Навигация по примерам работ"></div>

<?php endif;

wp_reset_postdata();
?>

  <section class="portfolio-services">
    <h2 class="portfolio-directions__title">Услуги по благоустройству участка</h2>
    <p class="portfolio-services__lead">Фотогалерея показывает готовые объекты, а для выбора решения лучше перейти в нужное направление услуг. Там собраны состав работ, варианты монтажа, цены, этапы и ответы на частые вопросы.</p>
    <div class="portfolio-services__grid">
      <a class="portfolio-services__card" href="/category/drenazh-uchastka/">
        <strong>Дренаж участка</strong>
        <span>Отвод грунтовых и дождевых вод, защита фундамента, газона, дорожек и посадок.</span>
      </a>
      <a class="portfolio-services__card" href="/category/osushenie-uchastka/">
        <strong>Осушение участка</strong>
        <span>Работы для сырых, заболоченных и низких участков, где вода долго стоит после дождя.</span>
      </a>
      <a class="portfolio-services__card" href="/category/livnevaya-kanalizatsiya/">
        <strong>Ливневая канализация</strong>
        <span>Лотки, дождеприемники и трубы для отвода воды с крыши, дорожек и площадок.</span>
      </a>
      <a class="portfolio-services__card" href="/category/otmostka-vokrug-doma/">
        <strong>Отмостка вокруг дома</strong>
        <span>Бетонная, мягкая и плиточная отмостка с уклоном, основанием и водоотводом.</span>
      </a>
      <a class="portfolio-services__card" href="/category/ukladka-trotuarnoy-plitki/">
        <strong>Укладка тротуарной плитки</strong>
        <span>Дорожки, площадки, парковки, бордюры, подготовка основания и водоотвод.</span>
      </a>
      <a class="portfolio-services__card" href="/category/avtopoliv-na-uchastke/">
        <strong>Автополив на участке</strong>
        <span>Автоматический полив газона, сада, теплицы, клумб и живой изгороди.</span>
      </a>
    </div>
  </section>

  <section class="portfolio-seo-text">
    <h2 class="portfolio-directions__title">Что видно по примерам работ</h2>
    <p>Примеры работ помогают оценить не только внешний вид участка после благоустройства. По фотографиям можно понять, как решены уклоны, водоотвод, подготовка основания, мощение, озеленение и привязка дорожек к дому, забору, въезду и зонам отдыха.</p>
    <ul class="portfolio-seo-list">
      <li>какие материалы и покрытия подходят под стиль дома и нагрузку;</li>
      <li>как дренаж и ливневая канализация защищают участок от воды;</li>
      <li>где нужна отмостка, бордюр, лоток или дополнительный уклон;</li>
      <li>как совмещаются тротуарная плитка, газон, посадки и автополив;</li>
      <li>какие работы лучше делать вместе, чтобы не переделывать участок;</li>
      <li>как выглядит результат после комплексного благоустройства под ключ.</li>
    </ul>
    <p>Работаем в Рыбинске, Ярославле и по Ярославской области. Для предварительного расчета можно прислать фото участка, размеры, адрес, задачу и примеры работ, которые вам близки по стилю.</p>
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

  <script>
  document.addEventListener('DOMContentLoaded', function() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.portfolio-tabs__button'));
    var cards = Array.prototype.slice.call(document.querySelectorAll('.case-container .case'));
    var pagination = document.querySelector('.portfolio-case-pagination');
    var empty = document.querySelector('.portfolio-empty');
    var casesTitle = document.getElementById('portfolio-cases');
    var activeFilter = 'all';
    var activePage = 1;

    function getPerPage() {
      return window.matchMedia('(max-width: 768px)').matches ? 6 : 9;
    }

    function cardMatchesFilter(card, filter) {
      var groups = card.getAttribute('data-case-groups') || '';
      return filter === 'all' || groups.indexOf(filter) !== -1;
    }

    function getFilteredCards() {
      return cards.filter(function(card) {
        return cardMatchesFilter(card, activeFilter);
      });
    }

    function createPageButton(label, page, isActive) {
      var button = document.createElement('button');
      button.type = 'button';
      button.className = 'portfolio-case-pagination__button' + (isActive ? ' is-active' : '');
      button.textContent = label;
      button.setAttribute('aria-label', 'Страница ' + page);
      button.addEventListener('click', function() {
        activePage = page;
        renderCases(true);
      });
      return button;
    }

    function renderPagination(totalPages) {
      if (!pagination) {
        return;
      }

      pagination.innerHTML = '';

      if (totalPages <= 1) {
        return;
      }

      for (var page = 1; page <= totalPages; page += 1) {
        pagination.appendChild(createPageButton(String(page), page, page === activePage));
      }
    }

    function renderCases(shouldScroll) {
      var perPage = getPerPage();
      var filteredCards = getFilteredCards();
      var totalPages = Math.max(1, Math.ceil(filteredCards.length / perPage));

      if (activePage > totalPages) {
        activePage = totalPages;
      }

      var start = (activePage - 1) * perPage;
      var end = start + perPage;

      cards.forEach(function(card) {
        card.classList.add('is-hidden');
      });

      filteredCards.slice(start, end).forEach(function(card) {
        card.classList.remove('is-hidden');
      });

      if (empty) {
        empty.classList.toggle('is-hidden', filteredCards.length > 0);
      }

      renderPagination(totalPages);

      if (shouldScroll && casesTitle) {
        casesTitle.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    buttons.forEach(function(button) {
      button.addEventListener('click', function() {
        activeFilter = button.getAttribute('data-case-filter') || 'all';
        activePage = 1;

        buttons.forEach(function(item) {
          item.classList.toggle('is-active', item === button);
        });

        renderCases(true);
      });
    });

    window.addEventListener('resize', function() {
      renderCases(false);
    });

    renderCases(false);
  });
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
