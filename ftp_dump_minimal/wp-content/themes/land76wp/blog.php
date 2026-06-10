<?php
/*
Template Name: Полезное
*/

add_filter('the_title', function ($title, $post_id) {
  if ((int) $post_id === (int) get_queried_object_id() && is_page_template('blog.php')) {
    return 'Полезное о благоустройстве участка';
  }

  return $title;
}, 10, 2);

add_filter('aioseo_title', function ($title) {
  return is_page_template('blog.php')
    ? 'Полезное о благоустройстве участка - дренаж, отмостка, плитка и автополив'
    : $title;
}, 30, 1);

add_filter('aioseo_description', function ($description) {
  return is_page_template('blog.php')
    ? 'Статьи по благоустройству участка: дренаж, осушение, ливневая канализация, отмостка, укладка тротуарной плитки и автополив. Разбираем схемы, ошибки, цены и монтаж.'
    : $description;
}, 30, 1);

if (!function_exists('land76_bloghub_topics')) {
  function land76_bloghub_topics() {
    return array(
      'all' => array(
        'label' => 'Все статьи',
        'cat_id' => 0,
        'url' => '#blog-posts',
      ),
      'drenazh' => array(
        'label' => 'Дренаж',
        'cat_id' => 87,
        'url' => '/category/drenazh-uchastka/',
      ),
      'osushenie' => array(
        'label' => 'Осушение',
        'cat_id' => 90,
        'url' => '/category/osushenie-uchastka/',
      ),
      'livnevka' => array(
        'label' => 'Ливневка',
        'cat_id' => 91,
        'url' => '/category/livnevaya-kanalizatsiya/',
      ),
      'otmostka' => array(
        'label' => 'Отмостка',
        'cat_id' => 88,
        'url' => '/category/otmostka-vokrug-doma/',
      ),
      'plitka' => array(
        'label' => 'Плитка',
        'cat_id' => 89,
        'url' => '/category/ukladka-trotuarnoy-plitki/',
      ),
      'avtopoliv' => array(
        'label' => 'Автополив',
        'cat_id' => 92,
        'url' => '/category/avtopoliv-na-uchastke/',
      ),
    );
  }
}

if (!function_exists('land76_bloghub_post_topics')) {
  function land76_bloghub_post_topics($post_id) {
    $topics = land76_bloghub_topics();
    $post_categories = wp_get_post_categories($post_id);
    $post_topics = array();

    foreach ($topics as $topic_key => $topic) {
      if ($topic_key === 'all' || empty($topic['cat_id'])) {
        continue;
      }
      if (in_array((int) $topic['cat_id'], $post_categories, true)) {
        $post_topics[] = $topic_key;
      }
    }

    if ($post_topics) {
      return $post_topics;
    }

    $text = mb_strtolower(get_the_title($post_id) . ' ' . get_the_excerpt($post_id));
    if (preg_match('/дренаж|грунтов|глинист|уклон|труб/u', $text)) {
      $post_topics[] = 'drenazh';
    }
    if (preg_match('/осуш|болот|сыр|низин|вода/u', $text)) {
      $post_topics[] = 'osushenie';
    }
    if (preg_match('/ливнев|дождеприем|лотк|водосток/u', $text)) {
      $post_topics[] = 'livnevka';
    }
    if (preg_match('/отмост/u', $text)) {
      $post_topics[] = 'otmostka';
    }
    if (preg_match('/плитк|мощен|брусчат|дорожк/u', $text)) {
      $post_topics[] = 'plitka';
    }
    if (preg_match('/автополив|полив|спринклер|капельн/u', $text)) {
      $post_topics[] = 'avtopoliv';
    }

    return $post_topics ? array_unique($post_topics) : array('drenazh');
  }
}

if (!function_exists('land76_bloghub_excerpt')) {
  function land76_bloghub_excerpt($post_id) {
    $excerpt = get_the_excerpt($post_id);

    if (!$excerpt && function_exists('get_field')) {
      $excerpt = get_field('blogseo_lead', $post_id);
    }

    return wp_trim_words(wp_strip_all_tags($excerpt), 24, '...');
  }
}

if (!function_exists('land76_bloghub_asset_url')) {
  function land76_bloghub_asset_url($filename) {
    return home_url('/wp-content/uploads/seo-service-photos/' . ltrim($filename, '/'));
  }
}

if (!function_exists('land76_bloghub_image_by_text')) {
  function land76_bloghub_image_by_text($post_id, $post_topics = array()) {
    $text = mb_strtolower(get_post_field('post_name', $post_id) . ' ' . get_the_title($post_id));
    $topic_key = !empty($post_topics[0]) ? $post_topics[0] : '';
    $topic_rules = array(
      'drenazh' => array(
        '/труб|trub/u' => 'glubinnyy.webp',
        '/схем|план|shema|plan/u' => 's-uklonom.webp',
        '/своими|svoimi|rukami/u' => 'glubinnyy.webp',
        '/высок|грунтов|gruntov|vysok/u' => 'vysokie-gruntovye-vody.webp',
        '/глин|glin/u' => 'glinistaya-pochva.webp',
        '/поверх|poverh/u' => 'poverhnostnyy.webp',
        '/глуб|glubin/u' => 'glubinnyy.webp',
        '/уклон|uklon/u' => 's-uklonom.webp',
        '/6-sotok|6-сот/u' => '6-sotok.webp',
        '/10-sotok|10-сот/u' => '10-sotok.webp',
      ),
      'osushenie' => array(
        '/болот|заболоч|bolot/u' => 'osushenie-zabolochennogo-uchastka.webp',
        '/грязн|луж|после-дожд|posle-dozhd|gryaz/u' => 'voda-posle-dozhdya-na-uchastke.webp',
        '/грунтов|высок|gruntov|vysok/u' => 'osushenie-pri-vysokih-gruntovyh-vodah.webp',
        '/глин|glin/u' => 'osushenie-glinistogo-uchastka.webp',
        '/дренаж|drenazh/u' => 'drenazh-dlya-osusheniya-uchastka.webp',
        '/дач|dach/u' => 'osushenie-dachnogo-uchastka.webp',
      ),
      'livnevka' => array(
        '/дождеприем|dozhdepriem/u' => 'dozhdepriemniki-i-lotki.webp',
        '/линей|lineyn/u' => 'lineynyy-vodootvod.webp',
        '/крыш|krysh/u' => 'otvod-vody-s-kryshi.webp',
        '/ремонт|remont/u' => 'remont-livnevoy-kanalizatsii.webp',
        '/дом|vokrug/u' => 'livnevka-vokrug-doma.webp',
        '/ливнев|livnev/u' => 'livnevka-na-uchastke.webp',
      ),
      'otmostka' => array(
        '/треш|tresh/u' => 'remont-staroy.webp',
        '/просел|prosel/u' => 'podgotovka-osnovaniya.webp',
        '/мягк|myag/u' => 'myagkaya-otmostka.webp',
        '/бетон|beton/u' => 'betonnaya-otmostka.webp',
        '/утепл|utepl/u' => 'uteplennaya-otmostka.webp',
        '/плит|plit/u' => 'otmostka-iz-plitki.webp',
        '/залив|montazh|монтаж/u' => 'zalivka.webp',
      ),
      'plitka' => array(
        '/брусчат|bruschat/u' => 'ukladka-bruschatki.webp',
        '/дорож|dorozh/u' => 'sadovye-dorozhki-iz-plitki.webp',
        '/авто|парков|ploshch/u' => 'ploshchadka-pod-avto-iz-plitki.webp',
        '/бордюр|водоотвод|bordyur/u' => 'bordyury-i-vodootvod-dlya-plitki.webp',
        '/ремонт|remont/u' => 'remont-trotuarnoy-plitki.webp',
        '/основан|podgotov/u' => 'podgotovka-osnovaniya-pod-plitku.webp',
      ),
      'avtopoliv' => array(
        '/капель|kapeln/u' => 'kapelnyy-poliv.webp',
        '/теплиц|teplits/u' => 'avtopoliv-teplitsy.webp',
        '/газон|gazon/u' => 'avtopoliv-gazona.webp',
        '/сад|дерев|derev|sada/u' => 'avtopoliv-sada.webp',
        '/насос|емкост|оборуд|nasos/u' => 'nasos-i-emkost-dlya-poliva.webp',
        '/не работает|ремонт|обслуж|remont/u' => 'obsluzhivanie-avtopoliva.webp',
        '/схем|проект|plan|shema/u' => 'proektirovanie-avtopoliva.webp',
        '/своими|svoimi|rukami/u' => 'montazh-avtopoliva.webp',
        '/автополив|poliv/u' => 'montazh-avtopoliva.webp',
      ),
    );

    if ($topic_key && !empty($topic_rules[$topic_key])) {
      foreach ($topic_rules[$topic_key] as $pattern => $image) {
        if (preg_match($pattern, $text)) {
          return $image;
        }
      }
    }

    return '';
  }
}

if (!function_exists('land76_bloghub_topic_images')) {
  function land76_bloghub_topic_images() {
    return array(
      'drenazh' => array('vysokie-gruntovye-vody.webp', 'glinistaya-pochva.webp', 'glubinnyy.webp', 'poverhnostnyy.webp', 's-uklonom.webp', 'vokrug-doma.webp'),
      'osushenie' => array('cena-osusheniya-uchastka.webp', 'osushenie-zabolochennogo-uchastka.webp', 'voda-posle-dozhdya-na-uchastke.webp', 'otvod-vody-s-uchastka.webp', 'osushenie-glinistogo-uchastka.webp'),
      'livnevka' => array('montazh-livnevoy-kanalizatsii.webp', 'livnevka-na-uchastke.webp', 'livnevka-vokrug-doma.webp', 'dozhdepriemniki-i-lotki.webp', 'lineynyy-vodootvod.webp'),
      'otmostka' => array('betonnaya-otmostka.webp', 'myagkaya-otmostka.webp', 'uteplennaya-otmostka.webp', 'otmostka-iz-plitki.webp', 'remont-staroy.webp', 'podgotovka-osnovaniya.webp'),
      'plitka' => array('sadovye-dorozhki-iz-plitki.webp', 'ploshchadka-pod-avto-iz-plitki.webp', 'ukladka-bruschatki.webp', 'bordyury-i-vodootvod-dlya-plitki.webp', 'remont-trotuarnoy-plitki.webp'),
      'avtopoliv' => array('avtopoliv-gazona.webp', 'montazh-avtopoliva.webp', 'kapelnyy-poliv.webp', 'avtopoliv-sada.webp', 'avtopoliv-teplitsy.webp', 'nasos-i-emkost-dlya-poliva.webp'),
    );
  }
}

if (!function_exists('land76_bloghub_card_image')) {
  function land76_bloghub_card_image($post_id, $post_topics) {
    $default_image_marker = '001-02-1';
    $image_url = function_exists('land76_get_card_image_url') ? land76_get_card_image_url($post_id, 'medium') : get_the_post_thumbnail_url($post_id, 'medium');
    $image_alt = function_exists('land76_get_card_image_alt') ? land76_get_card_image_alt($post_id, '') : '';

    if ($image_url && strpos($image_url, $default_image_marker) === false) {
      return array(
        'url' => $image_url,
        'alt' => $image_alt ? $image_alt : 'Статья: ' . get_the_title($post_id),
      );
    }

    $image = land76_bloghub_image_by_text($post_id, $post_topics);
    if (!$image) {
      $topic_key = !empty($post_topics[0]) ? $post_topics[0] : 'drenazh';
      $topic_images = land76_bloghub_topic_images();
      $pool = !empty($topic_images[$topic_key]) ? $topic_images[$topic_key] : $topic_images['drenazh'];
      $index = abs(crc32((string) get_post_field('post_name', $post_id))) % count($pool);
      $image = $pool[$index];
    }

    $topics = land76_bloghub_topics();
    $topic_key = !empty($post_topics[0]) ? $post_topics[0] : 'drenazh';
    $topic_label = isset($topics[$topic_key]) ? $topics[$topic_key]['label'] : 'благоустройство участка';

    return array(
      'url' => land76_bloghub_asset_url($image),
      'alt' => $topic_label . ': ' . get_the_title($post_id),
    );
  }
}
?>
<?php get_header('page'); ?>

      <section class="blog blog-hub wrapper">
        <style>
          .blog-hub {
            color: #333;
          }
          .blog-hub__intro,
          .blog-hub__services,
          .blog-hub__seo {
            width: 100%;
            margin-bottom: 38px;
            padding: 28px 32px;
            background: rgba(255,255,255,.94);
            border-left: 4px solid #0a9215;
            box-shadow: 0 5px 18px rgba(0,0,0,.12);
          }
          .blog-hub__intro p,
          .blog-hub__services p,
          .blog-hub__seo p,
          .blog-hub__seo li {
            font-size: 17px;
            line-height: 1.65;
            color: #555;
          }
          .blog-hub__intro p,
          .blog-hub__services p,
          .blog-hub__seo p {
            margin: 0 0 18px;
          }
          .blog-hub__actions,
          .blog-hub__tabs,
          .blog-hub__pagination {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          .blog-hub__actions {
            margin-top: 22px;
          }
          .blog-hub__button,
          .blog-hub__tab,
          .blog-hub__pagination-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-height: 42px;
            padding: 8px 18px;
            border: 2px solid #0a9215;
            border-radius: 24px;
            background: #fff;
            color: #0a9215;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(0,0,0,.1);
            cursor: pointer;
          }
          .blog-hub__button:first-child,
          .blog-hub__tab.is-active,
          .blog-hub__tab:hover,
          .blog-hub__pagination-button.is-active,
          .blog-hub__pagination-button:hover {
            background: #0a9215;
            color: #fff;
          }
          .blog-hub__button {
            text-decoration: none;
          }
          .blog-hub__topics {
            margin-bottom: 34px;
          }
          .blog-hub__subtitle {
            margin: 0 0 20px;
            font-family: "Poiret One", cursive;
            font-size: 38px;
            font-weight: 600;
            color: #333;
            text-shadow: 1px 2px 3px #00000036;
          }
          .blog-hub__grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 30px;
            align-items: start;
          }
          .blog-card {
            display: flex;
            flex-direction: column;
            min-height: 100%;
            background: #fff;
            box-shadow: 0 5px 14px rgba(0,0,0,.18);
          }
          .blog-card.is-hidden {
            display: none;
          }
          .blog-card__image-wrap {
            width: 100%;
            height: 220px;
            overflow: hidden;
            border-bottom: 4px solid #ff5e00ce;
          }
          .blog-card__image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: .3s;
          }
          .blog-card:hover .blog-card__image {
            transform: scale(1.04);
          }
          .blog-card__body {
            display: flex;
            flex: 1 1 auto;
            flex-direction: column;
            padding: 22px 24px 24px;
          }
          .blog-card__tag {
            display: inline-flex;
            width: fit-content;
            margin-bottom: 12px;
            padding: 4px 11px;
            border-radius: 18px;
            background: rgba(10,146,21,.1);
            color: #0a9215;
            font-size: 13px;
            font-weight: 600;
          }
          .blog-card__title {
            margin: 0 0 12px;
            color: #0a9215;
            font-size: 22px;
            font-weight: 600;
            line-height: 1.25;
          }
          .blog-card__text {
            margin-bottom: 20px;
            color: #555;
            font-size: 16px;
            line-height: 1.55;
          }
          .blog-card__button {
            display: inline-flex;
            width: fit-content;
            margin-top: auto;
            padding: 7px 18px;
            border: 2px solid #0a9215;
            border-radius: 25px;
            color: #0a9215;
            font-size: 17px;
            font-family: "Poiret One", cursive;
            font-weight: 600;
            box-shadow: 0 2px 2px rgba(0,0,0,.2);
          }
          .blog-card__button:hover {
            background: #0a9215;
            color: #fff;
          }
          .blog-hub__pagination {
            justify-content: center;
            margin: 38px 0 46px;
          }
          .blog-hub__pagination:empty {
            display: none;
          }
          .blog-hub__empty {
            margin: 24px 0 0;
            padding: 18px 22px;
            background: rgba(255,255,255,.94);
            border-left: 4px solid #0a9215;
            color: #555;
            box-shadow: 0 4px 14px rgba(0,0,0,.1);
          }
          .blog-hub__empty.is-hidden {
            display: none;
          }
          .blog-hub__service-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
          }
          .blog-hub__service-card {
            display: block;
            min-height: 104px;
            padding: 18px 20px;
            background: #fff;
            border-left: 4px solid #ff5e00ce;
            color: #555;
            box-shadow: 0 4px 14px rgba(0,0,0,.12);
            transition: .2s;
          }
          .blog-hub__service-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 7px 18px rgba(0,0,0,.16);
          }
          .blog-hub__service-card strong {
            display: block;
            margin-bottom: 8px;
            color: #0a9215;
            font-size: 18px;
            line-height: 1.25;
          }
          .blog-hub__service-card span {
            display: block;
            font-size: 15px;
            line-height: 1.5;
          }
          .blog-hub__seo-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px 24px;
            margin: 18px 0;
            list-style: none;
          }
          .blog-hub__seo-list li {
            position: relative;
            padding-left: 24px;
          }
          .blog-hub__seo-list li:before {
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
            .blog-hub__grid,
            .blog-hub__service-grid {
              grid-template-columns: repeat(2, 1fr);
            }
          }
          @media only screen and (max-width: 768px) {
            .blog-hub__intro,
            .blog-hub__services,
            .blog-hub__seo {
              padding: 24px 20px;
            }
            .blog-hub__subtitle {
              font-size: 31px;
            }
            .blog-hub__grid,
            .blog-hub__service-grid,
            .blog-hub__seo-list {
              grid-template-columns: 1fr;
            }
            .blog-card__image-wrap {
              height: 200px;
            }
          }
        </style>

        <h2 class="blog__title">Статьи по благоустройству участка</h2>

        <section class="blog-hub__intro" data-aos="fade-up" data-aos-duration="700">
          <p>Здесь собраны полезные материалы по работам на частном участке: дренаж, осушение, ливневая канализация, отмостка, укладка тротуарной плитки и автополив. Пишем не ради общих советов, а чтобы владелец участка понимал схему работ, частые ошибки, примерный состав материалов и когда лучше сразу считать монтаж под ключ.</p>
          <div class="blog-hub__actions">
            <a href="#blog-posts" class="blog-hub__button">Читать статьи</a>
            <a href="/services/" class="blog-hub__button">Каталог услуг</a>
            <a href="#form" class="blog-hub__button openPopup" data-modal="#popup">Задать вопрос</a>
          </div>
        </section>

        <section class="blog-hub__topics" aria-label="Темы полезных статей">
          <h2 class="blog-hub__subtitle">Выберите тему</h2>
          <div class="blog-hub__tabs">
            <?php foreach (land76_bloghub_topics() as $topic_key => $topic) : ?>
              <button class="blog-hub__tab<?php echo $topic_key === 'all' ? ' is-active' : ''; ?>" type="button" data-blog-filter="<?php echo esc_attr($topic_key); ?>"><?php echo esc_html($topic['label']); ?></button>
            <?php endforeach; ?>
          </div>
        </section>

        <?php
        $posts = get_posts(array(
          'numberposts' => -1,
          'category__in' => array(72),
          'orderby' => 'date',
          'order' => 'DESC',
          'post_type' => 'post',
          'post_status' => 'publish',
          'suppress_filters' => false,
        ));
        ?>

        <h2 class="blog-hub__subtitle" id="blog-posts">Полезные статьи и разборы</h2>
        <div class="blog-hub__grid">
          <?php foreach ($posts as $post) : ?>
            <?php
            setup_postdata($post);
            $post_id = get_the_ID();
            $post_topics = land76_bloghub_post_topics($post_id);
            $topics = land76_bloghub_topics();
            $first_topic = reset($post_topics);
            $topic_label = isset($topics[$first_topic]) ? $topics[$first_topic]['label'] : 'Благоустройство';
            $image = land76_bloghub_card_image($post_id, $post_topics);
            ?>
            <article class="blog-card" data-blog-topics="<?php echo esc_attr(implode(' ', $post_topics)); ?>">
              <a class="blog-card__image-wrap" href="<?php the_permalink(); ?>">
                <img class="blog-card__image" src="<?php echo esc_url($image['url']); ?>" alt="<?php echo esc_attr($image['alt']); ?>" loading="lazy">
              </a>
              <div class="blog-card__body">
                <span class="blog-card__tag"><?php echo esc_html($topic_label); ?></span>
                <h3 class="blog-card__title"><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h3>
                <div class="blog-card__text"><?php echo esc_html(land76_bloghub_excerpt($post_id)); ?></div>
                <a class="blog-card__button" href="<?php the_permalink(); ?>">Подробнее</a>
              </div>
            </article>
          <?php endforeach; ?>
          <?php wp_reset_postdata(); ?>
        </div>
        <p class="blog-hub__empty is-hidden">В этой теме пока нет опубликованных материалов. Посмотрите все статьи или перейдите в каталог услуг.</p>
        <div class="blog-hub__pagination" aria-label="Навигация по статьям"></div>

        <section class="blog-hub__services">
          <h2 class="blog-hub__subtitle">Связанные услуги</h2>
          <p>Если статья помогает понять задачу, следующий шаг - перейти в нужную услугу и посмотреть состав работ, цены, этапы и примеры объектов.</p>
          <div class="blog-hub__service-grid">
            <a class="blog-hub__service-card" href="/category/drenazh-uchastka/"><strong>Дренаж участка</strong><span>Грунтовые воды, глинистая почва, дренаж вокруг дома, 6 и 10 соток.</span></a>
            <a class="blog-hub__service-card" href="/category/osushenie-uchastka/"><strong>Осушение участка</strong><span>Решения для сырых, заболоченных и низких территорий.</span></a>
            <a class="blog-hub__service-card" href="/category/livnevaya-kanalizatsiya/"><strong>Ливневая канализация</strong><span>Водоотвод с крыши, дорожек, площадок и въезда.</span></a>
            <a class="blog-hub__service-card" href="/category/otmostka-vokrug-doma/"><strong>Отмостка вокруг дома</strong><span>Защита фундамента, уклон, основание и отвод воды.</span></a>
            <a class="blog-hub__service-card" href="/category/ukladka-trotuarnoy-plitki/"><strong>Укладка тротуарной плитки</strong><span>Дорожки, парковки, площадки, бордюры и подготовка основания.</span></a>
            <a class="blog-hub__service-card" href="/category/avtopoliv-na-uchastke/"><strong>Автополив на участке</strong><span>Полив газона, сада, теплицы, клумб и живой изгороди.</span></a>
          </div>
        </section>

        <section class="blog-hub__seo">
          <h2 class="blog-hub__subtitle">Как пользоваться разделом</h2>
          <p>Раздел «Полезное» нужен, чтобы быстро разобраться в проблеме участка до заявки: почему стоит вода, когда нужен дренаж или ливневка, чем отличается мягкая отмостка от бетонной, как готовят основание под плитку и почему автополив начинают со схемы.</p>
          <ul class="blog-hub__seo-list">
            <li>выберите тему по направлению работ или смотрите все статьи подряд;</li>
            <li>сравните признаки проблемы с тем, что происходит на вашем участке;</li>
            <li>откройте связанную услугу, если нужна цена, монтаж или расчет;</li>
            <li>посмотрите примеры работ, чтобы понять формат готового результата;</li>
            <li>не копируйте схемы вслепую: грунт, уклон и дом меняют решение;</li>
            <li>для расчета подготовьте фото участка, размеры и описание проблемы.</li>
          </ul>
          <p>Мы работаем в Рыбинске, Ярославле и Ярославской области. Материалы в блоге помогают сориентироваться, но окончательную схему дренажа, осушения, ливневой канализации, отмостки, плитки или автополива лучше подбирать после осмотра участка.</p>
        </section>

        <script>
          document.addEventListener('DOMContentLoaded', function() {
            var buttons = Array.prototype.slice.call(document.querySelectorAll('.blog-hub__tab'));
            var cards = Array.prototype.slice.call(document.querySelectorAll('.blog-card'));
            var pagination = document.querySelector('.blog-hub__pagination');
            var empty = document.querySelector('.blog-hub__empty');
            var title = document.getElementById('blog-posts');
            var activeFilter = 'all';
            var activePage = 1;

            function getPerPage() {
              return window.matchMedia('(max-width: 768px)').matches ? 6 : 9;
            }

            function cardMatchesFilter(card, filter) {
              var groups = card.getAttribute('data-blog-topics') || '';
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
              button.className = 'blog-hub__pagination-button' + (isActive ? ' is-active' : '');
              button.textContent = label;
              button.setAttribute('aria-label', 'Страница ' + page);
              button.addEventListener('click', function() {
                activePage = page;
                renderPosts(true);
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

            function renderPosts(shouldScroll) {
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

              if (shouldScroll && title) {
                title.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }
            }

            buttons.forEach(function(button) {
              button.addEventListener('click', function() {
                activeFilter = button.getAttribute('data-blog-filter') || 'all';
                activePage = 1;

                buttons.forEach(function(item) {
                  item.classList.toggle('is-active', item === button);
                });

                renderPosts(true);
              });
            });

            window.addEventListener('resize', function() {
              renderPosts(false);
            });

            renderPosts(false);
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
