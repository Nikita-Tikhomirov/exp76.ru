<?php
/*
Template Name: Главная страница
*/
?>
<?php get_header(); ?>

<?php
if (!function_exists('land76_home_term_link')) {
  function land76_home_term_link($term_id, $fallback) {
    $term = get_term((int) $term_id, 'category');
    if ($term && !is_wp_error($term)) {
      $url = get_term_link($term);
      if (!is_wp_error($url)) {
        return $url;
      }
    }
    return home_url($fallback);
  }
}

if (!function_exists('land76_home_media_url')) {
  function land76_home_media_url($file_name) {
    return home_url('/wp-content/uploads/seo-service-photos/' . ltrim($file_name, '/'));
  }
}

$services_page = get_permalink(921);
$works_page = get_permalink(160);
$calc_page = get_permalink(9973);
$contacts_page = get_permalink(227);

$task_cards = array(
  array('title' => 'На участке стоит вода', 'text' => 'Подберем дренаж, осушение или ливневую канализацию, чтобы убрать лужи, сырость и воду у фундамента.', 'url' => land76_home_term_link(87, '/category/drenazh-uchastka/'), 'image' => land76_home_media_url('vysokie-gruntovye-vody.webp'), 'alt' => 'Дренаж и осушение участка с водой после дождя'),
  array('title' => 'Нужно защитить фундамент', 'text' => 'Сделаем отмостку, водоотвод и примыкания так, чтобы вода уходила от дома, а не под основание.', 'url' => land76_home_term_link(88, '/category/otmostka-vokrug-doma/'), 'image' => land76_home_media_url('otmostka-iz-plitki.webp'), 'alt' => 'Отмостка и водоотвод для защиты фундамента'),
  array('title' => 'Нужны дорожки и площадки', 'text' => 'Продумываем основание, уклоны, бордюры и покрытие для дорожек, двора, парковки и входной зоны.', 'url' => land76_home_term_link(89, '/category/ukladka-trotuarnoy-plitki/'), 'image' => land76_home_media_url('sadovye-dorozhki-iz-plitki.webp'), 'alt' => 'Садовые дорожки и площадки из тротуарной плитки'),
  array('title' => 'Нужно отвести воду с крыши', 'text' => 'Собираем дождевую воду через лотки, дождеприемники, трубы и колодцы без размыва участка.', 'url' => land76_home_term_link(91, '/category/livnevaya-kanalizatsiya/'), 'image' => land76_home_media_url('dozhdepriemniki-i-lotki.webp'), 'alt' => 'Ливневая канализация и отвод воды с крыши'),
  array('title' => 'Нужен полив без ручной работы', 'text' => 'Проектируем автополив газона, сада, теплицы и посадок с зонами, клапанами и контроллером.', 'url' => land76_home_term_link(92, '/category/avtopoliv-na-uchastke/'), 'image' => land76_home_media_url('montazh-avtopoliva.webp'), 'alt' => 'Автоматический полив газона и посадок на участке'),
  array('title' => 'Нужен понятный план работ', 'text' => 'Сначала смотрим рельеф, воду, подъезд и будущие покрытия, потом собираем этапы и смету.', 'url' => $services_page, 'image' => land76_home_media_url('proektirovanie-avtopoliva.webp'), 'alt' => 'План работ по благоустройству участка перед расчетом'),
);

$service_cards = array(
  array('title' => 'Дренаж участка', 'text' => 'Глубинный и поверхностный дренаж, решения для глинистой почвы, высоких грунтовых вод, воды у дома и участков с уклоном.', 'url' => land76_home_term_link(87, '/category/drenazh-uchastka/'), 'image' => land76_home_media_url('cena-drenazha-uchastka.webp'), 'alt' => 'Дренаж участка под ключ в Ярославской области'),
  array('title' => 'Осушение участка', 'text' => 'Работы для сырых, заболоченных и низких участков: дренаж, водоотвод, колодцы, лотки, канавы и корректировка уклонов.', 'url' => land76_home_term_link(90, '/category/osushenie-uchastka/'), 'image' => land76_home_media_url('osushenie-zabolochennogo-uchastka.webp'), 'alt' => 'Осушение участка и отвод воды'),
  array('title' => 'Ливневая канализация', 'text' => 'Дождеприемники, лотки, трубы и колодцы для отвода воды с крыши, отмостки, дорожек, парковки и двора.', 'url' => land76_home_term_link(91, '/category/livnevaya-kanalizatsiya/'), 'image' => land76_home_media_url('livnevka-na-uchastke.webp'), 'alt' => 'Ливневая канализация на участке'),
  array('title' => 'Отмостка вокруг дома', 'text' => 'Бетонная, мягкая, утепленная и плиточная отмостка с уклоном, основанием, примыканием и связкой с водоотводом.', 'url' => land76_home_term_link(88, '/category/otmostka-vokrug-doma/'), 'image' => land76_home_media_url('otmostka-iz-plitki.webp'), 'alt' => 'Отмостка вокруг дома под ключ'),
  array('title' => 'Укладка тротуарной плитки', 'text' => 'Дорожки, двор, парковка, площадки и бордюры с подготовкой основания, уклонами и водоотводом.', 'url' => land76_home_term_link(89, '/category/ukladka-trotuarnoy-plitki/'), 'image' => land76_home_media_url('cena-ukladki-trotuarnoy-plitki.webp'), 'alt' => 'Укладка тротуарной плитки на участке'),
  array('title' => 'Автополив на участке', 'text' => 'Спринклеры, капельные линии, насос, емкость, клапаны и контроллер для газона, сада, теплицы и посадок.', 'url' => land76_home_term_link(92, '/category/avtopoliv-na-uchastke/'), 'image' => land76_home_media_url('montazh-avtopoliva.webp'), 'alt' => 'Монтаж автополива на участке'),
);

$land76_home_hub_links = array(
  array('service_id' => 'S1', 'title' => 'Ландшафтное проектирование', 'url' => '/services/landshaftnoe-proektirovanie/'),
  array('service_id' => 'S2', 'title' => 'Газон под ключ', 'url' => '/services/gazon-posevnojj-i-gazon-rulonnyjj/'),
  array('service_id' => 'S3', 'title' => 'Посадка деревьев и кустарников', 'url' => '/services/posadka-derevev-i-kustarnikov/'),
  array('service_id' => 'S4', 'title' => 'Уход за садом', 'url' => '/services/ukhod-za-sadom/'),
  array('service_id' => 'S5', 'title' => 'Планировка территории', 'url' => '/services/planirovka-territorii/'),
  array('service_id' => 'S6', 'title' => 'Подпорные стенки', 'url' => '/services/podpornye-stenki/'),
  array('service_id' => 'S7', 'title' => 'Освещение участка', 'url' => '/services/ulichnoe-osveshhenie-uchastka/'),
  array('service_id' => 'S8', 'title' => 'Въезд на участок через канаву', 'url' => '/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/'),
  array('service_id' => 'S9', 'title' => 'Расчистка участка и корчевание', 'url' => '/services/vykorchevyvanie-pnejj-spil-derevev/'),
  array('service_id' => 'S10', 'title' => 'Пруды, водоёмы и водопады', 'url' => '/services/sozdanie-ujutnogo-ugolka-s-pomoshhju-vodopada-vodoema-ili-ruchev/'),
  array('service_id' => 'S11', 'title' => 'Системы туманообразования', 'url' => '/services/sistemy-tumanoobrazovaniya/'),
  array('service_id' => 'S12', 'title' => 'Фундамент на железобетонных сваях', 'url' => '/services/fundament-na-zhelezobetonnykh-svajakh/'),
  array('service_id' => 'S13', 'title' => 'Металлические навесы', 'url' => '/services/navesy-iz-metalla/'),
  array('service_id' => 'S14', 'title' => 'Камины, печи и барбекю', 'url' => '/services/kaminy-pechi-barbekju/'),
  array('service_id' => 'S15', 'title' => 'Снос домов и демонтаж', 'url' => '/services/snos-i-demontazh-zdanijj-domov/'),
);

$works = get_posts(array(
  'numberposts' => 6,
  'category' => 75,
  'orderby' => 'date',
  'order' => 'DESC',
  'post_type' => 'page',
  'post_status' => 'publish',
  'suppress_filters' => true,
));
?>

<section class="home-section home-problems wrapper" id="tasks">
  <div class="home-section__head">
    <span class="home-eyebrow">С чего начинается работа</span>
    <h2>С какой задачей к нам обращаются</h2>
    <p>На частном участке редко бывает одна изолированная работа. Вода, уклоны, основание, дорожки и посадки связаны между собой, поэтому мы сначала разбираемся в задаче, а потом предлагаем состав работ.</p>
  </div>
  <div class="home-task-grid">
    <?php foreach ($task_cards as $card): ?>
      <a class="home-task-card" href="<?php echo esc_url($card['url']); ?>">
        <span class="home-task-card__image">
          <img src="<?php echo esc_url($card['image']); ?>" alt="<?php echo esc_attr($card['alt']); ?>" loading="lazy" />
        </span>
        <span class="home-task-card__body">
          <h3><?php echo esc_html($card['title']); ?></h3>
          <p><?php echo esc_html($card['text']); ?></p>
        </span>
      </a>
    <?php endforeach; ?>
  </div>
</section>

<section class="home-section home-services wrapper" id="services">
  <div class="home-section__head home-section__head--split">
    <div>
      <span class="home-eyebrow">Каталог направлений</span>
      <h2>Услуги по благоустройству участка</h2>
    </div>
  </div>
  <div class="home-service-grid">
    <?php foreach ($service_cards as $card): ?>
      <article class="home-service-card">
        <a class="home-service-card__image" href="<?php echo esc_url($card['url']); ?>">
          <img src="<?php echo esc_url($card['image']); ?>" alt="<?php echo esc_attr($card['alt']); ?>" loading="lazy" />
        </a>
        <div class="home-service-card__body">
          <h3><a href="<?php echo esc_url($card['url']); ?>"><?php echo esc_html($card['title']); ?></a></h3>
          <p><?php echo esc_html($card['text']); ?></p>
          <a class="home-inline-link" href="<?php echo esc_url($card['url']); ?>">Перейти в раздел</a>
        </div>
      </article>
    <?php endforeach; ?>
  </div>
  <nav class="home-hub-directory" aria-label="Все направления услуг">
    <h3 class="home-hub-directory__title">Все направления работ</h3>
    <div class="home-hub-directory__links">
      <?php foreach ($land76_home_hub_links as $hub_link): ?>
        <a class="home-hub-directory__link" data-service-id="<?php echo esc_attr($hub_link['service_id']); ?>" href="<?php echo esc_url(home_url($hub_link['url'])); ?>">
          <?php echo esc_html($hub_link['title']); ?>
        </a>
      <?php endforeach; ?>
    </div>
  </nav>
  <div class="home-section-note">
    <p>Здесь собраны основные направления работ, с которых обычно начинается благоустройство участка. В каждом разделе можно посмотреть состав услуг, варианты монтажа, цены, этапы работ и ответы на частые вопросы по конкретной задаче.</p>
    <p>Если на участке несколько проблем сразу, например вода у дома, будущие дорожки и газон, лучше смотреть не отдельную карточку, а связку работ. Так проще заранее заложить дренаж, ливневку, основание и уклоны без переделок.</p>
  </div>
</section>

<section class="home-section home-logic wrapper">
  <div class="home-section__head">
    <span class="home-eyebrow">Правильная последовательность</span>
    <h2>Почему сначала вода, уклоны и основание</h2>
    <p>Красивое покрытие быстро теряет вид, если под ним стоит вода или неправильно собран пирог основания. Поэтому инженерные решения мы увязываем с мощением, отмосткой, газоном и посадками.</p>
  </div>
  <div class="home-logic-grid">
    <article>
      <h3>Вода</h3>
      <p>Проверяем, куда уходит дождевая и талая вода, где высокий уровень грунтовых вод, где нужен дренаж или ливневка.</p>
    </article>
    <article>
      <h3>Основание</h3>
      <p>Подбираем глубину выемки, щебень, песок, геотекстиль, уклоны и бордюры под грунт и будущую нагрузку.</p>
    </article>
    <article>
      <h3>Финиш</h3>
      <p>После инженерной подготовки делаем отмостку, дорожки, площадки, газон, посадки и автополив без лишних переделок.</p>
    </article>
  </div>
</section>

<?php if ($works): ?>
<section class="home-section home-works wrapper" id="works">
  <div class="home-section__head home-section__head--split">
    <div>
      <span class="home-eyebrow">Реальные объекты</span>
      <h2>Выполненные работы</h2>
    </div>
  </div>
  <div class="home-work-grid">
    <?php foreach ($works as $post): setup_postdata($post);
      $thumb = get_the_post_thumbnail_url($post, 'large');
      if (!$thumb) {
        $thumb = get_template_directory_uri() . '/img/foto1.jpg';
      }
      $work_alt = sprintf('Выполненные работы по благоустройству участка: %s', get_the_title($post));
    ?>
      <article class="home-work-card">
        <a class="home-work-card__image" href="<?php the_permalink(); ?>">
          <img src="<?php echo esc_url($thumb); ?>" alt="<?php echo esc_attr($work_alt); ?>" loading="lazy" />
        </a>
        <div class="home-work-card__body">
          <h3><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
          <p><?php echo esc_html(wp_trim_words(get_the_excerpt(), 24, '...')); ?></p>
          <a class="home-inline-link" href="<?php the_permalink(); ?>">Смотреть работу</a>
        </div>
      </article>
    <?php endforeach; wp_reset_postdata(); ?>
  </div>
  <div class="home-section-note home-section-note--works">
    <p>В примерах работ важно смотреть не только на финальную картинку. Хороший объект держится на подготовке: правильных уклонах, водоотводе, основании под мощение, удобных проходах, подъезде и понятной связке с газоном и посадками.</p>
    <p>Мы показываем реальные объекты, чтобы было проще оценить уровень исполнения и понять, какие решения подходят для частного участка в Рыбинске, Ярославле и области.</p>
  </div>
  <div class="home-actions">
    <a class="home-btn home-btn--primary" href="<?php echo esc_url($works_page); ?>">Все работы</a>
    <a class="home-btn home-btn--outline" href="#request">Обсудить участок</a>
  </div>
</section>
<?php endif; ?>

<section class="home-section home-process wrapper">
  <div class="home-section__head">
    <span class="home-eyebrow">Этапы</span>
    <h2>Как проходит работа</h2>
  </div>
  <ol class="home-process-list">
    <li><span>01</span><h3>Осмотр участка</h3><p>Смотрим рельеф, воду, грунт, готовые строения, подъезд техники и места будущих дорожек.</p></li>
    <li><span>02</span><h3>Схема и смета</h3><p>Предлагаем состав работ, материалы, очередность этапов и понятный расчет без лишних позиций.</p></li>
    <li><span>03</span><h3>Подготовка</h3><p>Делаем разметку, земляные работы, основание, дренаж, ливневку и уклоны под будущие покрытия.</p></li>
    <li><span>04</span><h3>Монтаж и сдача</h3><p>Выполняем финишные работы, проверяем водоотвод, показываем результат и даем рекомендации по эксплуатации.</p></li>
  </ol>
</section>

<section class="home-section home-cost wrapper" id="prices">
  <div class="home-cost__content">
    <span class="home-eyebrow">Смета</span>
    <h2>От чего зависит стоимость благоустройства</h2>
    <p>Стоимость нельзя честно назвать только по площади. На цену влияет вода на участке, уклоны, грунт, глубина подготовки, выбранные материалы и то, нужно ли делать работы поэтапно.</p>
    <ul class="home-check-list">
      <li>площадь участка, длина трасс и объем земляных работ;</li>
      <li>тип грунта, уровень воды, уклон и место сброса;</li>
      <li>материалы: трубы, щебень, геотекстиль, лотки, плитка, бордюр;</li>
      <li>наличие дома, забора, дорожек, посадок и других ограничений;</li>
      <li>связка работ: дренаж, ливневка, отмостка, плитка, газон и автополив.</li>
    </ul>
    <div class="home-actions home-actions--left">
      <a class="home-btn home-btn--primary" href="<?php echo esc_url($calc_page); ?>">Открыть расчет</a>
      <a class="home-btn home-btn--outline" href="#request">Получить смету</a>
    </div>
  </div>
</section>

<section class="home-section home-trust wrapper">
  <div class="home-section__head">
    <span class="home-eyebrow">Подход</span>
    <h2>Почему нам доверяют благоустройство участков</h2>
  </div>
  <div class="home-trust-grid">
    <article><h3>Работаем комплексно</h3><p>Не разделяем участок на случайные работы: вода, основание, покрытие, газон и полив должны работать вместе.</p></article>
    <article><h3>Считаем до начала монтажа</h3><p>Объясняем состав работ, варианты материалов и места, где экономия приведет к переделке.</p></article>
    <article><h3>Учитываем эксплуатацию</h3><p>Делаем так, чтобы по участку было удобно ходить, заезжать, обслуживать водоотвод и ухаживать за посадками.</p></article>
  </div>
</section>

<section class="home-section home-geo wrapper">
  <div class="home-section__head">
    <span class="home-eyebrow">География</span>
    <h2>Работаем в Рыбинске, Ярославле и области</h2>
    <p>Выезжаем на частные участки в Рыбинске, Ярославле, Угличе, Тутаеве, Переславле-Залесском и других населенных пунктах Ярославской области. Для удаленных объектов заранее согласуем осмотр, логистику и этапность работ.</p>
  </div>
</section>

<section class="home-section home-faq wrapper">
  <div class="home-section__head">
    <span class="home-eyebrow">Вопросы</span>
    <h2>FAQ по благоустройству участка</h2>
  </div>
  <div class="home-faq-list">
    <details>
      <summary>Можно заказать только одну услугу?</summary>
      <p>Да. Можно заказать отдельный дренаж, отмостку, ливневку, плитку, автополив или газон. Если работы связаны между собой, мы покажем, что лучше предусмотреть сразу.</p>
    </details>
    <details>
      <summary>Нужно ли начинать с проекта?</summary>
      <p>Для небольших задач часто достаточно осмотра, схемы и сметы. Для комплексного благоустройства лучше сначала согласовать план работ, уклоны, покрытия и инженерные системы.</p>
    </details>
    <details>
      <summary>Можно ли делать благоустройство поэтапно?</summary>
      <p>Да. Главное заранее заложить дренаж, ливневку, выводы под автополив и уровни покрытий, чтобы следующий этап не ломал уже выполненные работы.</p>
    </details>
    <details>
      <summary>Вы рассчитываете стоимость по фото?</summary>
      <p>Предварительный ориентир можно дать по фото, размерам и описанию проблемы. Точную смету готовим после осмотра участка или подробной схемы.</p>
    </details>
  </div>
</section>

<section class="home-section home-request wrapper" id="request">
  <div class="home-request__text">
    <span class="home-eyebrow">Заявка</span>
    <h2>Рассчитать благоустройство участка</h2>
    <p>Опишите, что нужно сделать: убрать воду, сделать дорожки, отмостку, ливневку, автополив, газон или комплекс работ. Мы свяжемся, уточним задачу и подскажем следующий шаг.</p>
  </div>
  <div class="formWrapper home-request__form" id="form">
    <form class="form" method="post" action="<?php echo esc_url(home_url('/server.php')); ?>">
      <?php land76_render_form_security_fields('home-request-v3'); ?>
      <p class="form__title">Оставить заявку</p>
      <label class="form__label">
        <p>Имя или название организации *</p>
        <input class="form__input" type="text" name="name" required="required" />
      </label>
      <label class="form__label">
        <p>Контактный телефон *</p>
        <input class="form__input" type="text" name="phone" required="required" />
      </label>
      <div class="formConsent">
        <label class="formConsent__container">
          <input class="formConsent__input" type="checkbox" name="consent" value="1" required="required" />
          <span class="formConsent__checkbox">
            <svg class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px">
              <path d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265  c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386  c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928  C170.827,363.533,162.165,366.839,153.504,366.839z" fill="#B22917"></path>
            </svg>
          </span>
        </label>
        <p class="formConsent__text">Я согласен с <a href="<?php echo esc_url(home_url('/privacy/')); ?>">политикой конфиденциальности</a> и <a href="<?php echo esc_url(home_url('/consent/')); ?>">обработкой персональных данных</a>.</p>
      </div>
      <button class="form__btn btn" type="submit">Отправить</button>
    </form>
    <div class="ajaxMessage">
      <div class="ajaxMessage__success">
        <div class="ajaxMessage__title"><p>Спасибо!</p><p>Ваша заявка принята</p></div>
        <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время.</div>
      </div>
      <div class="ajaxMessage__error">
        <div class="ajaxMessage__title">Ошибка при отправке!</div>
        <div class="ajaxMessage__text">Попробуйте позднее</div>
      </div>
      <button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
    </div>
  </div>
</section>

</main>
</div>

<?php get_footer(); ?>
