<?php
/*
Template Name: Услуги
*/

add_filter('the_title', function ($title, $post_id) {
  if ((int) $post_id === (int) get_queried_object_id() && is_page_template('services.php')) {
    return 'Услуги по благоустройству участков в Рыбинске и Ярославской области';
  }

  return $title;
}, 10, 2);

add_filter('aioseo_title', function ($title) {
  return is_page_template('services.php')
    ? 'Услуги по благоустройству участков в Рыбинске и Ярославской области'
    : $title;
});

add_filter('aioseo_description', function ($description) {
  return is_page_template('services.php')
    ? 'Каталог услуг по благоустройству участков: дренаж, осушение, ливневая канализация, отмостка, плитка, автополив и проектирование.'
    : $description;
});

if (!function_exists('land76_services_url')) {
  function land76_services_url($path) {
    return esc_url(home_url($path));
  }
}

if (!function_exists('land76_services_asset')) {
  function land76_services_asset($path) {
    return esc_url(home_url('/wp-content/uploads/seo-service-photos/' . ltrim($path, '/')));
  }
}

$land76_services_tasks = array(
  array('label' => 'Убрать воду с участка', 'url' => '/category/drenazh-uchastka/'),
  array('label' => 'Осушить сырой участок', 'url' => '/category/osushenie-uchastka/'),
  array('label' => 'Защитить фундамент', 'url' => '/category/otmostka-vokrug-doma/'),
  array('label' => 'Сделать дорожки и площадку', 'url' => '/category/ukladka-trotuarnoy-plitki/'),
  array('label' => 'Организовать ливневку', 'url' => '/category/livnevaya-kanalizatsiya/'),
  array('label' => 'Настроить автополив', 'url' => '/category/avtopoliv-na-uchastke/'),
  array('label' => 'Сделать проект участка', 'url' => '/services/landshaftnoe-proektirovanie/'),
);

$land76_services_groups = array(
  array(
    'title' => 'Инженерные системы и отвод воды',
    'items' => array(
      array(
        'title' => 'Дренаж участка',
        'url' => '/category/drenazh-uchastka/',
        'image' => land76_services_asset('vysokie-gruntovye-vody.webp'),
        'alt' => 'Дренаж участка под ключ в Ярославской области',
        'text' => 'Проектируем и монтируем дренаж участка под ключ: глубинные и поверхностные системы, дренаж вокруг дома, решения для глинистой почвы и высокого уровня грунтовых вод.',
        'links' => array(
          array('Цена дренажа участка', '/cena-drenazha-uchastka/'),
          array('Дренаж при высоких грунтовых водах', '/vysokie-gruntovye-vody/'),
          array('Дренаж на глинистой почве', '/glinistaya-pochva/'),
          array('Дренаж вокруг дома', '/vokrug-doma/'),
          array('Глубинный дренаж', '/glubinnyy/'),
          array('Поверхностный дренаж', '/poverhnostnyy/'),
        ),
      ),
      array(
        'title' => 'Осушение участка',
        'url' => '/category/osushenie-uchastka/',
        'image' => land76_services_asset('osushenie-zabolochennogo-uchastka.webp'),
        'alt' => 'Осушение заболоченного участка в Ярославской области',
        'text' => 'Подбираем схему осушения для заболоченных, глинистых и дачных участков: дренаж, водоотвод, лотки, колодцы, уклоны и локальные решения по проблемным зонам.',
        'links' => array(
          array('Стоимость осушения участка', '/cena-osusheniya-uchastka/'),
          array('Дренаж для осушения участка', '/drenazh-dlya-osusheniya-uchastka/'),
          array('Осушение при высоких грунтовых водах', '/osushenie-pri-vysokih-gruntovyh-vodah/'),
          array('Осушение заболоченного участка', '/osushenie-zabolochennogo-uchastka/'),
          array('Отвод воды с участка', '/otvod-vody-s-uchastka/'),
        ),
      ),
      array(
        'title' => 'Ливневая канализация',
        'url' => '/category/livnevaya-kanalizatsiya/',
        'image' => land76_services_asset('montazh-livnevoy-kanalizatsii.webp'),
        'alt' => 'Ливневая канализация на участке под ключ',
        'text' => 'Собираем дождевую и талую воду с крыши, отмостки, дорожек, двора и парковки: дождеприемники, лотки, трубы, колодцы и линейный водоотвод.',
        'links' => array(
          array('Цена ливневой канализации', '/cena-livnevoy-kanalizatsii/'),
          array('Монтаж ливневой канализации', '/montazh-livnevoy-kanalizatsii/'),
          array('Ливневка вокруг дома', '/livnevka-vokrug-doma/'),
          array('Линейный водоотвод', '/lineynyy-vodootvod/'),
          array('Отвод воды с крыши', '/otvod-vody-s-kryshi/'),
        ),
      ),
    ),
  ),
  array(
    'title' => 'Дом, покрытия и мощение',
    'items' => array(
      array(
        'title' => 'Отмостка вокруг дома',
        'url' => '/category/otmostka-vokrug-doma/',
        'image' => land76_services_asset('betonnaya-otmostka.webp'),
        'alt' => 'Отмостка вокруг дома под ключ',
        'text' => 'Делаем бетонную, мягкую, утепленную и плиточную отмостку вокруг дома. Учитываем уклон, грунт, водоотвод, примыкание к цоколю и будущие дорожки.',
        'links' => array(
          array('Стоимость отмостки вокруг дома', '/cena/'),
          array('Бетонная отмостка', '/betonnaya-otmostka/'),
          array('Мягкая отмостка', '/myagkaya-otmostka/'),
          array('Утепленная отмостка', '/uteplennaya-otmostka/'),
          array('Отмостка из плитки', '/otmostka-iz-plitki/'),
        ),
      ),
      array(
        'title' => 'Укладка тротуарной плитки',
        'url' => '/category/ukladka-trotuarnoy-plitki/',
        'image' => land76_services_asset('sadovye-dorozhki-iz-plitki.webp'),
        'alt' => 'Укладка тротуарной плитки на участке',
        'text' => 'Укладываем плитку и брусчатку на дорожках, площадках, парковках и во дворе. Готовим основание, бордюры, уклоны и водоотвод, чтобы покрытие служило без просадок.',
        'links' => array(
          array('Стоимость укладки плитки', '/cena-ukladki-trotuarnoy-plitki/'),
          array('Подготовка основания', '/podgotovka-osnovaniya-pod-plitku/'),
          array('Садовые дорожки из плитки', '/sadovye-dorozhki-iz-plitki/'),
          array('Площадка под авто', '/ploshchadka-pod-avto-iz-plitki/'),
          array('Бордюры и водоотвод', '/bordyury-i-vodootvod-dlya-plitki/'),
        ),
      ),
    ),
  ),
  array(
    'title' => 'Озеленение, полив и уход',
    'items' => array(
      array(
        'title' => 'Автополив на участке',
        'url' => '/category/avtopoliv-na-uchastke/',
        'image' => land76_services_asset('avtopoliv-gazona.webp'),
        'alt' => 'Автополив газона и сада под ключ',
        'text' => 'Проектируем и монтируем автоматический полив газона, сада, клумб, теплиц и посадок: зоны полива, спринклеры, капельные линии, контроллер, насос и емкость.',
        'links' => array(
          array('Стоимость автополива', '/cena-avtopoliva-na-uchastke/'),
          array('Монтаж автополива', '/montazh-avtopoliva/'),
          array('Автополив газона', '/avtopoliv-gazona/'),
          array('Капельный полив', '/kapelnyy-poliv/'),
          array('Проектирование автополива', '/proektirovanie-avtopoliva/'),
        ),
      ),
      array(
        'title' => 'Газон, посадки и уход',
        'url' => '/services/gazon-posevnojj-i-gazon-rulonnyjj/',
        'image' => esc_url(get_template_directory_uri() . '/img/about7.jpg'),
        'alt' => 'Газон, посадки и уход за участком',
        'text' => 'Устраиваем газоны, подбираем растения, высаживаем деревья и кустарники, ухаживаем за садом и помогаем поддерживать участок в аккуратном состоянии.',
        'links' => array(
          array('Посадка деревьев и кустарников', '/services/posadka-derevev-i-kustarnikov/'),
          array('Уход за садом', '/services/ukhod-za-sadom/'),
          array('Автополив сада', '/avtopoliv-sada/'),
          array('Автополив теплицы', '/avtopoliv-teplitsy/'),
        ),
      ),
    ),
  ),
  array(
    'title' => 'Проектирование и комплексные работы',
    'items' => array(
      array(
        'title' => 'Ландшафтное проектирование',
        'url' => '/services/landshaftnoe-proektirovanie/',
        'image' => esc_url(get_template_directory_uri() . '/img/h11.jpg'),
        'alt' => 'Ландшафтное проектирование и благоустройство участка',
        'text' => 'Готовим проект благоустройства участка: планировку, посадки, покрытия, освещение, водоотвод, автополив и очередность работ.',
        'links' => array(
          array('Планировка территории', '/services/planirovka-territorii/'),
          array('Подпорные стенки', '/services/podpornye-stenki/'),
          array('Освещение участка', '/services/ulichnoe-osveshhenie-uchastka/'),
          array('Въезд через канаву', '/services/vezd-zaezd-na-uchastok-cherez-kanavu-pod-kljuch/'),
        ),
      ),
    ),
  ),
);

$land76_price_rows = array(
  array('Дренаж участка', 'от расчета по схеме и метражу', '/category/drenazh-uchastka/'),
  array('Осушение участка', 'после осмотра и выбора способа отвода воды', '/category/osushenie-uchastka/'),
  array('Ливневая канализация', 'по длине трасс, лоткам и точкам сбора', '/category/livnevaya-kanalizatsiya/'),
  array('Отмостка вокруг дома', 'по площади, типу основания и финишному покрытию', '/category/otmostka-vokrug-doma/'),
  array('Укладка тротуарной плитки', 'по площади, основанию, бордюрам и водоотводу', '/category/ukladka-trotuarnoy-plitki/'),
  array('Автополив', 'по количеству зон, оборудованию и источнику воды', '/category/avtopoliv-na-uchastke/'),
);
?>

<?php get_header('page'); ?>


      <section class="services services-hub wrapper">
        <div class="services-hub__intro">
          <h2 class="services__title">Каталог услуг по благоустройству участка</h2>
          <p>Компания «Эксперты» выполняет инженерные, строительные и ландшафтные работы на частных участках в Рыбинске, Ярославле и Ярославской области: дренаж, осушение, ливневую канализацию, отмостку, укладку тротуарной плитки, автополив, газоны, проектирование и комплексное благоустройство.</p>
          <div class="services-hub__cta">
            <a class="services-hub__btn" href="#services-calc">Рассчитать стоимость</a>
            <a class="services-hub__btn services-hub__btn--light" href="#services-cases">Посмотреть работы</a>
            <a class="services-hub__btn services-hub__btn--light openPopup" data-modal="#popup" href="#form">Получить консультацию</a>
          </div>
        </div>

        <div class="services-hub__tasks">
          <h2 class="services-hub__subtitle">Выберите задачу на участке</h2>
          <div class="services-hub__task-grid">
            <?php foreach ($land76_services_tasks as $task) : ?>
              <a class="services-hub__task" href="<?php echo land76_services_url($task['url']); ?>"><?php echo esc_html($task['label']); ?></a>
            <?php endforeach; ?>
          </div>
        </div>

        <section class="services-hub__order">
          <h2 class="services-hub__subtitle">С чего начать благоустройство участка</h2>
          <p>Если на участке есть вода, уклоны, будущая отмостка, дорожки, газон и автополив, порядок работ важнее отдельной услуги. Сначала смотрим рельеф и водоотвод, потом основание и покрытия, после этого газон, посадки и полив.</p>
          <ol>
            <li><span>1</span><strong>Осмотр и схема</strong><em>Понимаем, куда уходит вода, где будут дорожки, дом, парковка и посадки.</em></li>
            <li><span>2</span><strong>Инженерные работы</strong><em>Дренаж, ливневка, осушение, колодцы, лотки и уклоны делаются до финишных покрытий.</em></li>
            <li><span>3</span><strong>Покрытия и озеленение</strong><em>Отмостка, плитка, газон, растения и автополив собираются в единую систему.</em></li>
          </ol>
        </section>

        <div class="services-hub__groups">
          <?php foreach ($land76_services_groups as $group) : ?>
            <section class="services-hub__group">
              <h2 class="services-hub__group-title"><?php echo esc_html($group['title']); ?></h2>
              <div class="services-hub__cards">
                <?php foreach ($group['items'] as $item) : ?>
                  <article class="services-hub__card">
                    <?php if (!empty($item['image'])) : ?>
                      <a class="services-hub__card-image" href="<?php echo land76_services_url($item['url']); ?>">
                        <img src="<?php echo esc_url($item['image']); ?>" alt="<?php echo esc_attr(!empty($item['alt']) ? $item['alt'] : $item['title']); ?>" loading="lazy">
                      </a>
                    <?php endif; ?>
                    <h3><a href="<?php echo land76_services_url($item['url']); ?>"><?php echo esc_html($item['title']); ?></a></h3>
                    <p><?php echo esc_html($item['text']); ?></p>
                    <?php if (!empty($item['links'])) : ?>
                      <ul>
                        <?php foreach ($item['links'] as $link) : ?>
                          <li><a href="<?php echo land76_services_url($link[1]); ?>"><?php echo esc_html($link[0]); ?></a></li>
                        <?php endforeach; ?>
                      </ul>
                    <?php endif; ?>
                    <a class="services-hub__more" href="<?php echo land76_services_url($item['url']); ?>">Перейти в раздел</a>
                  </article>
                <?php endforeach; ?>
              </div>
            </section>
          <?php endforeach; ?>
        </div>

        <section class="services-hub__prices">
          <h2 class="services-hub__subtitle">Популярные услуги и ориентиры по стоимости</h2>
          <div class="services-hub__price-table">
            <?php foreach ($land76_price_rows as $row) : ?>
              <a class="services-hub__price-row" href="<?php echo land76_services_url($row[2]); ?>">
                <span><?php echo esc_html($row[0]); ?></span>
                <strong><?php echo esc_html($row[1]); ?></strong>
              </a>
            <?php endforeach; ?>
          </div>
        </section>

        <section class="services-hub__complex">
          <h2 class="services-hub__subtitle">Комплексные решения</h2>
          <p>Часто выгоднее делать работы связкой: сначала решить воду и уклоны, затем выполнить отмостку, мощение, газон, посадки и автополив. Так участок получается цельным, а переделок после благоустройства меньше.</p>
          <ul>
            <li>дренаж участка + ливневая канализация;</li>
            <li>отмостка вокруг дома + водоотвод с крыши;</li>
            <li>тротуарная плитка + бордюры + лотки;</li>
            <li>газон + автополив + посадки;</li>
            <li>планировка территории + дренаж + мощение.</li>
          </ul>
        </section>
      </section>

      <style>
        .services-hub { background-attachment: fixed; }
        .services-hub__intro { max-width: 980px; margin-bottom: 38px; }
        .services-hub__intro p,
        .services-hub__complex p { font-size: 19px; line-height: 1.65; color: #555; }
        .services-hub__cta { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 26px; }
        .services-hub__btn,
        .services-hub__more {
          display: inline-flex; align-items: center; justify-content: center;
          min-height: 44px; padding: 10px 24px; border-radius: 24px;
          background: #0a9215; border: 2px solid #0a9215; color: #fff;
          font-weight: 600; text-decoration: none; box-shadow: 0 5px 14px rgba(10,146,21,.2);
        }
        .services-hub__btn--light { background: #fff; color: #0a9215; }
        .services-hub__subtitle,
        .services-hub__group-title {
          font-family: "Poiret One", cursive; font-size: 38px; font-weight: 600;
          margin: 38px 0 24px; color: #333; text-shadow: 1px 2px 3px #00000024;
        }
        .services-hub__task-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
        .services-hub__task {
          display: flex; align-items: center; min-height: 74px; padding: 18px 20px;
          background: #fff; border-left: 4px solid #ff5e00; color: #333;
          font-size: 18px; font-weight: 600; text-decoration: none; box-shadow: 0 4px 14px rgba(0,0,0,.12);
        }
        .services-hub__order {
          max-width: 1120px; margin-top: 42px; padding: 32px;
          background: rgba(255,255,255,.9); box-shadow: 0 5px 18px rgba(0,0,0,.12);
          border-left: 4px solid #ff5e00;
        }
        .services-hub__order p { max-width: 920px; margin: 0 0 22px; font-size: 19px; line-height: 1.65; color: #555; }
        .services-hub__order ol { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 0; padding: 0; list-style: none; }
        .services-hub__order li {
          display: grid; grid-template-columns: 44px 1fr; gap: 8px 14px; align-items: start;
          padding: 18px; background: #fff; box-shadow: 0 3px 12px rgba(0,0,0,.08);
        }
        .services-hub__order span {
          grid-row: span 2; display: inline-flex; align-items: center; justify-content: center;
          width: 44px; height: 44px; border-radius: 50%; background: #0a9215; color: #fff; font-weight: 600;
        }
        .services-hub__order strong { color: #333; font-size: 18px; }
        .services-hub__order em { color: #666; font-style: normal; line-height: 1.45; }
        .services-hub__cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .services-hub__card {
          display: flex; flex-direction: column; min-height: 100%;
          overflow: hidden; background: #fff; box-shadow: 0 5px 18px rgba(0,0,0,.15);
          border-top: 4px solid #0a9215;
        }
        .services-hub__card-image { display: block; aspect-ratio: 16 / 9; overflow: hidden; background: #eef2ed; }
        .services-hub__card-image img { width: 100%; height: 100%; object-fit: cover; transition: transform .25s ease; }
        .services-hub__card:hover .services-hub__card-image img { transform: scale(1.04); }
        .services-hub__card h3 { margin: 22px 26px 14px; font-size: 25px; line-height: 1.2; color: #333; }
        .services-hub__card h3 a { color: inherit; text-decoration: none; }
        .services-hub__card p { margin: 0 26px 18px; color: #666; font-size: 17px; line-height: 1.55; }
        .services-hub__card ul,
        .services-hub__complex ul { list-style: none; margin: 0 26px 22px; padding: 0; display: grid; gap: 9px; }
        .services-hub__card li,
        .services-hub__complex li { position: relative; padding-left: 24px; color: #555; line-height: 1.45; }
        .services-hub__card li:before,
        .services-hub__complex li:before {
          content: ""; position: absolute; left: 0; top: .55em; width: 9px; height: 9px;
          border: 2px solid #0a9215; border-radius: 50%; background: #fff;
        }
        .services-hub__card li a { color: #0a9215; text-decoration: none; }
        .services-hub__more { margin: auto 26px 26px; align-self: flex-start; min-height: 38px; padding: 8px 18px; }
        .services-hub__price-table { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .services-hub__price-row {
          display: flex; justify-content: space-between; gap: 16px; padding: 16px 18px;
          background: #fff; color: #333; text-decoration: none; border-left: 4px solid #0a9215;
          box-shadow: 0 3px 10px rgba(0,0,0,.1);
        }
        .services-hub__price-row strong { color: #666; font-weight: 600; text-align: right; }
        .services-hub__complex { max-width: 980px; }
        .services-contact-form#form1 {
          width: 100%;
          max-width: 100%;
          margin: 0;
          padding: 34px 30px 30px;
        }
        .services-contact-form#form1 .calc-contact-form {
          display: grid !important;
          grid-template-columns: minmax(250px, 1fr) minmax(250px, 1fr) minmax(160px, auto);
          gap: 20px 26px;
          align-items: start;
          width: 100%;
          margin-top: 26px;
        }
        .services-contact-form#form1 .calc-contact-form .form__label {
          display: block !important;
          margin: 0;
          text-align: left;
          line-height: 1.35;
        }
        .services-contact-form#form1 .calc-contact-form .form__label p {
          margin: 0 0 9px;
          color: #222;
          font-size: 16px;
          font-weight: 500;
          line-height: 1.35;
        }
        .services-contact-form#form1 .calc-contact-form .form__input {
          width: 100% !important;
          height: 42px;
          min-width: 0;
          margin: 0 !important;
          padding: 8px 14px;
          border: 1px solid rgba(255, 94, 0, .55);
          border-radius: 0;
          font-size: 16px;
        }
        .services-contact-form#form1 .calc-contact-form .formConsent {
          grid-column: 1 / 3;
          display: grid !important;
          grid-template-columns: 18px minmax(0, 1fr);
          gap: 10px;
          align-items: start;
          max-width: 760px;
          margin: 2px 0 0;
        }
        .services-contact-form#form1 .calc-contact-form .formConsent__container {
          min-width: 18px;
          margin: 3px 0 0 !important;
        }
        .services-contact-form#form1 .calc-contact-form .formConsent__input {
          width: auto !important;
        }
        .services-contact-form#form1 .calc-contact-form .formConsent__text {
          margin: 0;
          max-width: 720px;
          font-size: 13px;
          line-height: 1.45;
          text-align: left;
          color: #444;
        }
        .services-contact-form#form1 .calc-contact-form .form__btn {
          grid-column: 3;
          grid-row: 2;
          justify-self: end;
          align-self: start;
          min-width: 160px;
          margin: 0 !important;
          padding: 8px 28px;
          font-size: 18px;
        }
        .services-contact-form#form1 .calc__info {
          margin-top: 24px;
          padding-top: 18px;
          border-top: 1px solid rgba(0,0,0,.25);
        }
        @media (max-width: 1100px) {
          .services-hub__cards { grid-template-columns: repeat(2, 1fr); }
          .services-hub__task-grid { grid-template-columns: repeat(2, 1fr); }
          .services-hub__order ol { grid-template-columns: 1fr; }
          .services-contact-form#form1 .calc-contact-form {
            grid-template-columns: 1fr 1fr;
            align-items: start;
          }
          .services-contact-form#form1 .calc-contact-form .formConsent {
            grid-column: 1 / -1;
          }
          .services-contact-form#form1 .calc-contact-form .form__btn {
            grid-column: 1 / -1;
            grid-row: auto;
            justify-self: center;
            margin: 0 !important;
          }
        }
        @media (max-width: 700px) {
          .services-hub__cards,
          .services-hub__task-grid,
          .services-hub__price-table { grid-template-columns: 1fr; }
          .services-hub__price-row { flex-direction: column; }
          .services-hub__price-row strong { text-align: left; }
          .services-hub__subtitle,
          .services-hub__group-title { font-size: 31px; }
          .services-contact-form#form1 {
            padding: 26px 20px;
          }
          .services-contact-form#form1 .calc-contact-form {
            grid-template-columns: 1fr;
            gap: 16px;
          }
          .services-contact-form#form1 .calc-contact-form .form__label {
            grid-template-columns: 1fr;
            gap: 8px;
            text-align: left;
          }
          .services-contact-form#form1 .calc-contact-form .form__btn {
            grid-row: auto;
            width: 100%;
          }
        }
      </style>

      <section class="advantages wrapper">
        <h2 class="advantages__title">Наши преимущества</h2>
        <div class="advantages__how">
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="512"
                width="512">
                <path class="active-path"
                  d="M505 50H271V8c0-5-4-8-8-8h-47c-4 0-7 3-7 8v42h-92c-4 0-7 3-7 7v65c-5 2-10 6-14 10v-22c0-14-13-25-34-29V65c0-4-3-8-7-8-13 0-27 6-37 14a51 51 0 00-18 40v31c0 10 15 10 15 0v-31c0-17 12-34 32-38v288c-11 1-23 6-32 14V182c0-10-15-10-15 0v234c1 22 21 39 48 39 13 0 25-4 33-10v27c0 26 26 40 48 40 24 0 48-14 48-40V366h214L235 499c-5 4-2 13 5 13h226c4 0 8-3 8-8v-36c0-10-15-10-15 0v29H261l198-169v99c0 9 15 9 15 0v-61h31c4 0 7-3 7-7V57c0-4-3-7-7-7zm-8 15v182H321V65zM256 15v192h-32v-19h5c10 0 10-15 0-15h-5v-20h12c10 0 10-15 0-15h-12v-20h5a8 8 0 000-15h-5V84h12c10 0 10-15 0-15h-12V49h5c10 0 10-15 0-15h-5V15zM118 134c4-2 7-3 11-3v287c-9 1-22 5-33 15V168c0-13 8-28 22-34zm44 316c-9-5-20-7-32-7v-10h6c5-1 7-3 8-8V154c10 3 18 8 18 13zM81 110v283c-8-5-20-8-32-8v-9l6-1c4 0 7-2 7-7V97c12 2 19 8 19 13zm0 308c0 12-15 22-33 22-19 0-33-11-33-25s5-28 19-35v13c0 5 3 7 8 7 10-1 22 1 31 6 5 3 9 6 8 12zm48 79c-18 0-33-11-33-25s5-27 19-34v12c0 5 3 8 8 8 13-1 40 1 39 18 0 11-15 21-33 21zm48-330c0-13-13-25-33-28v-17c-1-4-3-7-8-7l-11 1V65h84v149c0 5 3 8 7 8h47c4 0 8-3 8-8V65h35v286H177zm292 138c-2-1-6 0-8 1l-52 45h-88v-89h176v89h-23v-39c0-3-2-5-5-7z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path"
                  d="M357 215h69l6-2 34-35c2-1 3-3 3-5l-1-69c0-4-3-8-7-8h-69c-2 0-4 1-5 3l-35 34-2 5v69c0 5 3 8 7 8zm8-69h54v54h-54zm69 43v-47l20-20v48zm-39-78h48l-20 20h-48zM393 314h-25c-10 0-10 15 0 15h25c10 0 10-15 0-15zM432 284h-64c-10 0-10 15 0 15h64c9 0 9-15 0-15zM425 385l-91 77c-5 5-2 14 5 14h91c4 0 7-4 7-8v-77c0-6-7-10-12-6zm-3 76h-63l63-54z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description">Авторский дизайн</p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512"
                height="512">
                <path class="active-path"
                  d="M110 496l-15-21a10 10 0 10-17 12l16 21a10 10 0 1016-12zM225 500l-16-78c-8-38-30-71-62-93l-35-23c-14-10-33-8-45 4V190c0-16-11-29-26-33a33 33 0 00-41 33v155c0 20 6 40 18 56l18 25a10 10 0 1016-11l-18-25c-9-13-14-29-14-45V190a13 13 0 0116-13c7 1 11 7 11 13v123a70 70 0 0020 49l21 23 11 11 15 16a10 10 0 0015-13l-26-27-22-25h-1c-5-6-5-16 1-22 5-6 13-7 19-3l35 24c28 19 47 47 54 80l17 78a10 10 0 0019-4z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path"
                  d="M74 446a10 10 0 00-16 11 10 10 0 1016-11zM499 164c-7-7-18-9-28-7-15 4-26 17-26 33v120a35 35 0 00-45-4l-35 23c-32 22-54 55-62 93l-16 78a10 10 0 1019 4l17-78c7-33 26-61 54-80l35-24c6-4 14-3 19 3 6 6 6 16 1 22h-1l-48 52a10 10 0 0015 13l47-50 2-2c12-13 18-30 18-47V190c0-6 4-12 11-13a13 13 0 0116 13v155c0 16-5 32-14 45l-76 106a10 10 0 0016 12l76-107c12-16 18-36 18-56V190c0-10-5-20-13-26z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path"
                  d="M383 192l-18-5v-3c11-8 19-21 19-36v-24a45 45 0 00-74-34 58 58 0 00-108 0c-8-6-18-10-29-10-25 0-45 20-45 44v24c0 15 8 28 19 36v3l-18 5c-21 5-36 24-36 45v19c0 6 5 10 10 10h46v40c0 5 5 10 10 10h60a10 10 0 000-20h-10v-21a10 10 0 00-20 0v21h-20v-26c0-20 13-36 32-41l28-6 18 42c1 3 5 6 9 6s8-3 9-6l19-42 27 6c19 5 32 21 32 41v26h-20v-21a10 10 0 00-20 0v21h-11a10 10 0 000 20h61c5 0 10-5 10-10v-36-4h46c5 0 10-4 10-10v-19c0-21-15-40-36-45zm-44-92c13 0 24 10 25 23h-14c-12 0-23-3-33-8 3-9 12-15 22-15zm-24 46v-10c11 4 23 7 35 7h14v5a25 25 0 01-49 0v-2zm-97-34a38 38 0 0176-6l-17-10c-4-2-9-1-13 3-8 9-20 15-33 15h-13v-2zm-45-12c10 0 19 6 23 15-11 5-22 8-34 8h-14c1-13 12-23 25-23zm-25 43h14c12 0 24-3 36-7v12a25 25 0 01-50 0v-5zm48 67c-19 5-35 18-42 36h-41v-9c0-12 9-23 21-26l26-6c4-1 7-5 7-10v-3a45 45 0 0011 0v3a10 10 0 009 10l14 4-5 1zm28-16l-8-2-18-5v-3c4-2 7-5 9-8 5 7 10 13 17 18zm44 15l-12 27-12-27v-7a58 58 0 0024 0v7zm-12-26c-21 0-38-17-38-38v-11h13c16 0 31-6 43-16l20 12v16c0 21-17 37-38 37zm32 11c7-5 13-11 17-18 3 3 5 6 9 8v3l-18 5-8 2zm111 52h-41c-7-18-23-31-42-36l-5-1 15-4a10 10 0 008-10v-3a45 45 0 0011 0v3c0 5 3 9 8 10l25 6c12 3 21 14 21 26v9z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path"
                  d="M263 299a10 10 0 00-14 0 10 10 0 000 14 10 10 0 0014 0c2-2 3-5 3-7 0-3-1-6-3-7zM256 0c-6 0-10 4-10 10v15a10 10 0 0020 0V10c0-6-4-10-10-10zM219 33l-10-11a10 10 0 10-14 14l10 11a10 10 0 0014 0c4-4 4-10 0-14zM317 22c-4-4-10-4-14 0l-10 11a10 10 0 0014 14l10-10c4-4 4-11 0-15z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description">Индивидуальный подход</p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" height="512" viewBox="0 0 516 516"
                width="512">
                <path class="active-path"
                  d="M409 411a10 10 0 10-13 16l18 13a10 10 0 0013-1l33-36a10 10 0 10-15-13l-27 29z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path"
                  d="M515 358c0-5-4-9-9-10-24-2-53-18-75-40-2-2-4-4-7-4s-5 2-7 4c-10 10-21 19-33 25a181 181 0 00-82-52c25-25 41-57 41-86v-16a33 33 0 00-1-61c-5-50-40-92-89-106-1-7-7-12-14-12h-37c-7 0-12 5-14 11a124 124 0 00-91 107 33 33 0 00-2 61v16c0 29 17 61 42 86a205 205 0 00-8 3c-33 11-60 31-82 58-20 26-35 58-43 95-3 14-5 31 4 42s24 12 37 12h66a10 10 0 000-20H45c-12 0-19-1-22-5-3-3-3-11 0-24 11-47 36-104 97-133-2 34 17 56 28 70a10 10 0 0015 0l56-54 57 54a10 10 0 0014 0c12-14 30-36 28-70 18 8 34 20 47 34-8 3-16 5-23 5-5 1-9 5-9 10a168 168 0 0035 113H201a10 10 0 000 20h183c12 14 26 25 40 25 32 0 69-66 70-67 16-30 22-55 21-91zM322 115h-56c-10-27-12-49-12-82 36 13 62 45 68 82zM207 20h27c0 39 1 65 11 95h-49c10-30 11-56 11-95zm-20 12c0 34-2 56-12 83h-58c6-38 34-71 70-83zm-78 103h221a13 13 0 010 27H109a13 13 0 010-27zm6 60v-13h208v13c0 38-37 85-79 101-18 6-31 6-50 0-42-16-79-63-79-101zm42 162a68 68 0 01-16-57l14-3a134 134 0 0043 21zm125 0l-41-39a120 120 0 0043-21l13 3c5 26-5 44-15 57zm194 83c-12 22-40 56-52 56s-40-34-52-56c-13-25-19-45-19-73a126 126 0 0034-12c13-7 26-16 37-26 21 19 47 33 71 38 0 28-6 48-19 73z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
                <path class="active-path" d="M156 471a10 10 0 000 20 10 10 0 100-20z" data-original="#000000"
                  data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description">Профессионализм</p>
          </div>
          <div class="advantages__arrow"></div>
          <div class="advantages__step">
            <div class="advantages__svg-wrap"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 516 516" width="512"
                height="512">
                <path class="active-path"
                  d="M473 461l36-37a9 9 0 00-6-15h-68v-34c0-9-7-17-17-17H94c-10 0-17 8-17 17v34H9a9 9 0 00-6 15l36 37-36 36a9 9 0 006 15h153c5 0 9-4 9-9v-42h170v42c0 5 4 9 9 9h153a9 9 0 006-15l-36-36zm-319 34H29l28-28a9 9 0 000-12l-28-29h48v18c0 9 7 17 17 17h60v34zm-60-51v-69h324v69H94zm264 51v-34h60c10 0 17-8 17-17v-18h48l-28 29a9 9 0 000 12l28 28H358zM33 272l-7 42a9 9 0 0013 9l38-20 38 20a9 9 0 0012-9l-7-42 31-29a9 9 0 00-5-15l-42-6-20-38a9 9 0 00-15 0l-19 38-43 6a9 9 0 00-4 15l30 29zm24-34c3 0 5-2 6-4l14-27 13 27c2 2 4 4 7 4l30 4-22 21c-2 2-3 5-2 8l5 29-27-14h-8l-27 14 5-29c1-3 0-6-2-8l-22-21 30-4zM359 234c-1 3 0 6 2 9l31 29-7 42a9 9 0 0012 9l38-20 38 20a9 9 0 0013-9l-7-42 30-29a9 9 0 00-4-15l-43-6-19-38a9 9 0 00-15 0l-20 38-42 6c-4 0-6 3-7 6zm56 4c3 0 5-2 7-4l13-27 14 27c1 2 3 4 6 4l30 4-22 21c-2 2-3 5-2 8l5 29-27-14h-8l-27 14 5-29c1-3 0-6-2-8l-22-21 30-4zM187 148l-13 72a9 9 0 0012 9l70-34 70 34a9 9 0 0012-9l-13-72 56-52a9 9 0 00-4-15l-79-10-34-67a9 9 0 00-16 0l-34 67-79 10a9 9 0 00-4 15l56 52zm33-61c3 0 5-2 7-4l29-56 29 56c2 2 4 4 7 4l64 9-46 42c-2 2-3 5-3 8l11 61-58-29c-3-2-5-2-8 0l-58 29 11-61c0-3-1-6-3-8l-46-42 64-9z"
                  data-original="#000000" data-old_color="#000000" fill="#0A9215"></path>
              </svg></div>
            <p class="advantages__step-description">Высокое качество</p>
          </div>
        </div>
      </section>


       <section class="calc wrapper" id="services-calc">
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
          <div class="formWrapper services-contact-form" id="form1">
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
      </section>

      <section class="services wrapper services-hub__cases" id="services-cases">
        <h2 class="services__title">Примеры работ</h2>
        <div class="services__cards columns3">
          <?php
          $case_posts = get_posts(array(
            'numberposts' => 6,
            'category' => 75,
            'orderby' => 'date',
            'order' => 'DESC',
            'post_type' => 'page',
            'post_status' => 'publish',
            'suppress_filters' => true,
          ));

          foreach ($case_posts as $post) :
            setup_postdata($post);
            $case_img = get_the_post_thumbnail_url($post, 'medium');
          ?>
            <div class="service" data-aos="fade-up" data-aos-duration="400">
              <?php if ($case_img) : ?>
                <div class="service__img-wrap">
                  <img class="service__img" src="<?php echo esc_url($case_img); ?>" alt="<?php echo esc_attr(get_the_title()); ?>" loading="lazy" />
                </div>
              <?php endif; ?>
              <div class="service__text-wrap">
                <h3 class="service__title"><?php the_title(); ?></h3>
                <?php the_excerpt(); ?>
              </div>
              <div class="service__link-wrap">
                <a class="service__link" href="<?php the_permalink(); ?>">Подробнее</a>
              </div>
            </div>
          <?php endforeach; wp_reset_postdata(); ?>
        </div>
      </section>

      <section class="services wrapper services-hub__geo">
        <h2 class="services__title">Работаем по Рыбинску и Ярославской области</h2>
        <p>Выезжаем на участки в Рыбинске, Ярославле, Угличе, Тутаеве, Переславле-Залесском и ближайших населенных пунктах. Для инженерных работ сначала смотрим рельеф, грунт, существующие дорожки, дом, забор, посадки и место отвода воды.</p>
      </section>

      <section class="services wrapper services-hub__faq">
        <h2 class="services__title">Вопросы по услугам благоустройства</h2>
        <div class="services-hub__faq-grid">
          <article>
            <h3>Можно заказать одну услугу?</h3>
            <p>Да. Можно заказать только дренаж, отмостку, плитку, автополив или другую отдельную работу. Если видим, что без смежной системы результат будет слабым, объясняем это до начала работ.</p>
          </article>
          <article>
            <h3>Можно делать благоустройство поэтапно?</h3>
            <p>Да. Часто сначала делают дренаж, ливневку и планировку, затем отмостку, мощение, газон, посадки и автополив. Так легче распределить бюджет и не переделывать готовые покрытия.</p>
          </article>
          <article>
            <h3>Выезжаете на осмотр участка?</h3>
            <p>Да. Для точного расчета важно увидеть уклоны, грунт, воду после дождя, подъезд техники и существующие постройки. По фото можно дать только предварительный ориентир.</p>
          </article>
          <article>
            <h3>Какие работы лучше делать вместе?</h3>
            <p>Чаще всего связывают дренаж с ливневой канализацией, отмостку с водоотводом, плитку с бордюрами и лотками, газон с автополивом.</p>
          </article>
        </div>
        <script type="application/ld+json">
        <?php
        echo wp_json_encode(array(
          '@context' => 'https://schema.org',
          '@type' => 'FAQPage',
          'mainEntity' => array(
            array(
              '@type' => 'Question',
              'name' => 'Можно заказать одну услугу?',
              'acceptedAnswer' => array(
                '@type' => 'Answer',
                'text' => 'Да. Можно заказать отдельную работу: дренаж, отмостку, укладку тротуарной плитки, автополив, ливневую канализацию или другую услугу благоустройства.'
              ),
            ),
            array(
              '@type' => 'Question',
              'name' => 'Можно делать благоустройство поэтапно?',
              'acceptedAnswer' => array(
                '@type' => 'Answer',
                'text' => 'Да. Часто сначала делают дренаж, ливневую канализацию и планировку, затем отмостку, мощение, газон, посадки и автополив.'
              ),
            ),
            array(
              '@type' => 'Question',
              'name' => 'Выезжаете на осмотр участка?',
              'acceptedAnswer' => array(
                '@type' => 'Answer',
                'text' => 'Да. Для точного расчета важно увидеть уклоны, грунт, воду после дождя, подъезд техники, существующие постройки и место отвода воды.'
              ),
            ),
            array(
              '@type' => 'Question',
              'name' => 'Какие работы лучше делать вместе?',
              'acceptedAnswer' => array(
                '@type' => 'Answer',
                'text' => 'Чаще всего объединяют дренаж с ливневой канализацией, отмостку с водоотводом, плитку с бордюрами и лотками, газон с автополивом.'
              ),
            ),
          ),
        ), JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        ?>
        </script>
      </section>

      <style>
        .services-hub__cases .service__title { font-size: 23px; }
        .services-hub__geo p {
          max-width: 980px; font-size: 19px; line-height: 1.7; color: #555;
        }
        .services-hub__faq-grid {
          display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px;
        }
        .services-hub__faq-grid article {
          background: #fff; padding: 24px; box-shadow: 0 4px 14px rgba(0,0,0,.12);
          border-left: 4px solid #ff5e00;
        }
        .services-hub__faq-grid h3 { margin: 0 0 12px; font-size: 23px; color: #333; }
        .services-hub__faq-grid p { margin: 0; font-size: 17px; line-height: 1.55; color: #666; }
        @media (max-width: 767px) {
          .services-hub__faq-grid { grid-template-columns: 1fr; }
        }
      </style>

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
