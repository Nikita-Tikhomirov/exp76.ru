<?php
add_action( 'wp_enqueue_scripts', 'style_theme' );
add_action( 'wp_footer', 'scripts_theme' );

$land76_import_file = __DIR__ . '/inc/import-drenazh.php';
if (file_exists($land76_import_file)) {
  require_once $land76_import_file;
}

$land76_drenazh_blog_import_file = __DIR__ . '/inc/import-drenazh-blog.php';
if (file_exists($land76_drenazh_blog_import_file)) {
  require_once $land76_drenazh_blog_import_file;
}

$land76_otmostka_import_file = __DIR__ . '/inc/import-otmostka.php';
if (file_exists($land76_otmostka_import_file)) {
  require_once $land76_otmostka_import_file;
}

$land76_otmostka_blog_import_file = __DIR__ . '/inc/import-otmostka-blog.php';
if (file_exists($land76_otmostka_blog_import_file)) {
  require_once $land76_otmostka_blog_import_file;
}

$land76_plitka_import_file = __DIR__ . '/inc/import-plitka.php';
if (file_exists($land76_plitka_import_file)) {
  require_once $land76_plitka_import_file;
}

$land76_plitka_blog_import_file = __DIR__ . '/inc/import-plitka-blog.php';
if (file_exists($land76_plitka_blog_import_file)) {
  require_once $land76_plitka_blog_import_file;
}

$land76_osushenie_import_file = __DIR__ . '/inc/import-osushenie.php';
if (file_exists($land76_osushenie_import_file)) {
  require_once $land76_osushenie_import_file;
}

$land76_osushenie_blog_import_file = __DIR__ . '/inc/import-osushenie-blog.php';
if (file_exists($land76_osushenie_blog_import_file)) {
  require_once $land76_osushenie_blog_import_file;
}

$land76_livnevka_import_file = __DIR__ . '/inc/import-livnevka.php';
if (file_exists($land76_livnevka_import_file)) {
  require_once $land76_livnevka_import_file;
}

$land76_livnevka_blog_import_file = __DIR__ . '/inc/import-livnevka-blog.php';
if (file_exists($land76_livnevka_blog_import_file)) {
  require_once $land76_livnevka_blog_import_file;
}

$land76_autopoliv_import_file = __DIR__ . '/inc/import-autopoliv.php';
if (file_exists($land76_autopoliv_import_file)) {
  require_once $land76_autopoliv_import_file;
}

$land76_autopoliv_blog_import_file = __DIR__ . '/inc/import-autopoliv-blog.php';
if (file_exists($land76_autopoliv_blog_import_file)) {
  require_once $land76_autopoliv_blog_import_file;
}

$land76_case_seo_import_file = __DIR__ . '/inc/import-case-seo.php';
if (file_exists($land76_case_seo_import_file)) {
  require_once $land76_case_seo_import_file;
}

$land76_service_previews_import_file = __DIR__ . '/inc/import-service-previews.php';
if (file_exists($land76_service_previews_import_file)) {
  require_once $land76_service_previews_import_file;
}

$land76_seo_category_indexing_file = __DIR__ . '/inc/seo-category-indexing.php';
if (file_exists($land76_seo_category_indexing_file)) {
  require_once $land76_seo_category_indexing_file;
}

function land76_region_page_slugs() {
  return array('yaroslavl', 'rybinsk', 'uglich', 'tutaev', 'pereslavl');
}

function land76_regional_service_slugs() {
  return array('drenazh-uchastka', 'ukladka-trotuarnoy-plitki', 'osushenie-uchastka', 'otmostka-vokrug-doma', 'avtopoliv-na-uchastke', 'livnevaya-kanalizatsiya');
}

function land76_is_unknown_regional_service_request() {
  $path = isset($_SERVER['REQUEST_URI']) ? trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/') : '';
  if (!preg_match('#^([^/]+)/([^/]+)/?$#', $path, $matches)) {
    return false;
  }

  if ($matches[1] === 'category') {
    return false;
  }

  if (!in_array($matches[2], land76_regional_service_slugs(), true)) {
    return false;
  }

  return !in_array($matches[1], land76_region_page_slugs(), true);
}

add_filter('redirect_canonical', function ($redirect_url) {
  return land76_is_unknown_regional_service_request() ? false : $redirect_url;
}, 10, 1);

add_action('template_redirect', function () {
  if (!land76_is_unknown_regional_service_request()) {
    return;
  }

  global $wp_query;
  $wp_query->set_404();
  status_header(404);
  nocache_headers();
  $template = get_404_template();
  if ($template) {
    include $template;
  } else {
    echo '404';
  }
  exit;
}, 0);


function style_theme() {

  // wp_enqueue_style('style1', get_template_directory_uri() . '/css/index.css');
  $main_styles_path = get_template_directory() . '/css/styles.css';
  $main_styles_version = file_exists($main_styles_path) ? filemtime($main_styles_path) : null;
  wp_enqueue_style('style2', get_template_directory_uri() . '/css/styles.css', array(), $main_styles_version);
  $mobile_card_slider_path = get_template_directory() . '/css/mobile-card-slider.css';
  $mobile_card_slider_version = file_exists($mobile_card_slider_path) ? filemtime($mobile_card_slider_path) : null;
  wp_enqueue_style('land76-mobile-card-slider', get_template_directory_uri() . '/css/mobile-card-slider.css', array('style2'), $mobile_card_slider_version);
  $mobile_card_slider_script_path = get_template_directory() . '/js/mobile-card-slider.js';
  $mobile_card_slider_script_version = file_exists($mobile_card_slider_script_path) ? filemtime($mobile_card_slider_script_path) : null;
  wp_enqueue_script('land76-mobile-card-slider', get_template_directory_uri() . '/js/mobile-card-slider.js', array(), $mobile_card_slider_script_version, true);
  if (is_singular('post') && has_category(72, get_queried_object_id())) {
    wp_enqueue_style('land76-services', get_template_directory_uri() . '/css/services.css', array(), null);
    wp_enqueue_style('land76-seoblog', get_template_directory_uri() . '/css/seoblog.css', array('land76-services'), null);
  }
  if (is_singular('post') && has_category(74, get_queried_object_id())) {
    $servicepost_styles_path = get_template_directory() . '/css/servicepost.css';
    $servicepost_styles_version = file_exists($servicepost_styles_path) ? filemtime($servicepost_styles_path) : null;
    wp_enqueue_style('land76-servicepost', get_template_directory_uri() . '/css/servicepost.css', array('style2'), $servicepost_styles_version);
  }

}


function scripts_theme() {

}




add_theme_support( 'post-thumbnails' );

function land76_get_card_image_url($post_id = null, $size = 'medium', $fallback = true) {
  $post_id = $post_id ? (int) $post_id : get_the_ID();

  if ($post_id && has_post_thumbnail($post_id)) {
    $thumbnail_url = get_the_post_thumbnail_url($post_id, $size);
    if ($thumbnail_url) {
      return $thumbnail_url;
    }
  }

  if ($post_id && function_exists('get_field')) {
    $field_names = array(
      'service_card_image',
      'card_image',
      'ns87_card_image',
      'ns87_hero_image',
      'image',
      'blogseo_main_image_url',
    );

    foreach ($field_names as $field_name) {
      $image = get_field($field_name, $post_id);
      if (empty($image)) {
        continue;
      }

      if (is_array($image) && !empty($image['sizes'][$size])) {
        return $image['sizes'][$size];
      }

      if (is_array($image) && !empty($image['url'])) {
        return $image['url'];
      }

      if (is_numeric($image)) {
        $attachment_url = wp_get_attachment_image_url((int) $image, $size);
        if ($attachment_url) {
          return $attachment_url;
        }
      }

      if (is_string($image)) {
        return $image;
      }
    }
  }

  return $fallback ? 'https://exp76.ru/wp-content/uploads/2020/02/001-02-1.webp' : '';
}

function land76_get_card_image_alt($post_id = null, $fallback = '') {
  $post_id = $post_id ? (int) $post_id : get_the_ID();
  $fallback = $fallback ? $fallback : ($post_id ? get_the_title($post_id) : '');

  if (!$post_id) {
    return $fallback;
  }

  $custom_alt = get_post_meta($post_id, '_land76_service_preview_alt', true);
  if ($custom_alt) {
    return $custom_alt;
  }

  $thumbnail_id = get_post_thumbnail_id($post_id);
  if ($thumbnail_id) {
    $attachment_alt = get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true);
    if ($attachment_alt) {
      return $attachment_alt;
    }
  }

  return $fallback;
}

function land76_render_header_popup() {
  ?>
  <div class="formWrapper" id="header-popup">
    <form class="form">
      <p class="form__title">Оставить заявку</p>
      <label class="form__label">
        <p>Имя или название организации *</p>
        <input class="form__input" type="text" name="name" placeholder="" required="required" />
      </label>
      <label class="form__label">
        <p>Контактный телефон *</p>
        <input class="form__input" type="text" name="phone" placeholder="" required="required" />
      </label>
      <div class="formConsent">
        <label class="formConsent__container">
          <input class="formConsent__input" type="checkbox" required="required" />
          <span class="formConsent__checkbox">
            <svg class="formConsent__icon" viewBox="0 0 426.67 426.67" width="24px" height="24px">
              <path d="M153.504,366.839c-8.657,0-17.323-3.302-23.927-9.911L9.914,237.265c-13.218-13.218-13.218-34.645,0-47.863c13.218-13.218,34.645-13.218,47.863,0l95.727,95.727l215.39-215.386c13.218-13.214,34.65-13.218,47.859,0c13.222,13.218,13.222,34.65,0,47.863L177.436,356.928C170.827,363.533,162.165,366.839,153.504,366.839z" fill="#B22917"></path>
            </svg>
          </span>
        </label>
        <p class="formConsent__text">Я ознакомлен и согласен с <a href="<?php echo esc_url(home_url('/privacy/')); ?>">политикой конфиденциальности</a> оператора, подтверждаю свое согласие на обработку введенных мною персональных данных</p>
      </div>
      <button class="form__btn btn" type="submit">Отправить</button>
    </form>
    <div class="ajaxMessage">
      <div class="ajaxMessage__success">
        <div class="ajaxMessage__title">
          <p>Спасибо!</p>
          <p>Ваша заявка принята</p>
        </div>
        <div class="ajaxMessage__text">Мы свяжемся с вами в ближайшее время, чтобы обсудить детали и ответить на вопросы</div>
      </div>
      <div class="ajaxMessage__error">
        <div class="ajaxMessage__title">Ошибка при отправке!</div>
        <div class="ajaxMessage__text">Попробуйте позднее</div>
      </div>
      <button class="ajaxMessage__btn btn closeModal" type="button">закрыть</button>
    </div>
  </div>
  <?php
}

add_filter('aioseo_title', function ($title) {
  if (!is_singular('post') || !in_category(72) || !function_exists('get_field')) {
    return $title;
  }

  $seo_title = get_field('blogseo_seo_title', get_the_ID());
  return $seo_title ? $seo_title : $title;
}, 20, 1);

add_filter('aioseo_description', function ($description) {
  if (!is_singular('post') || !in_category(72) || !function_exists('get_field')) {
    return $description;
  }

  $seo_description = get_field('blogseo_seo_description', get_the_ID());
  return $seo_description ? $seo_description : $description;
}, 20, 1);

function land76_is_case_seo_template() {
  return is_page_template('casenew.php') && function_exists('get_field');
}

function land76_schema_is_case_template() {
  return is_page_template(array('casenew.php', 'portfoliopost.php'));
}

function land76_schema_is_service_page_template() {
  return is_page_template('servicepost.php');
}

add_filter('aioseo_title', function ($title) {
  if (!land76_is_case_seo_template()) {
    return $title;
  }

  $seo_title = get_field('cs87_seo_title', get_the_ID());
  return $seo_title ? $seo_title : $title;
}, 20, 1);

add_filter('aioseo_description', function ($description) {
  if (!land76_is_case_seo_template()) {
    return $description;
  }

  $seo_description = get_field('cs87_seo_description', get_the_ID());
  return $seo_description ? $seo_description : $description;
}, 20, 1);

add_filter('aioseo_title', function ($title) {
  return is_front_page()
    ? 'Благоустройство участков под ключ в Рыбинске и Ярославской области — Эксперты'
    : $title;
}, 30, 1);

add_filter('aioseo_description', function ($description) {
  return is_front_page()
    ? 'Проектируем и выполняем благоустройство частных участков: дренаж, ливневая канализация, отмостка, тротуарная плитка, газон, автополив и озеленение. Работаем в Рыбинске, Ярославле и области.'
    : $description;
}, 30, 1);

function land76_schema_strip($value) {
  return trim(wp_strip_all_tags((string) $value));
}

function land76_schema_limit($value, $limit = 320) {
  $value = land76_schema_strip($value);
  if ($value === '') {
    return '';
  }

  return function_exists('mb_substr') && function_exists('mb_strlen') && mb_strlen($value, 'UTF-8') > $limit
    ? rtrim(mb_substr($value, 0, $limit - 1, 'UTF-8')) . '…'
    : $value;
}

function land76_schema_current_url() {
  if (is_front_page()) {
    return home_url('/');
  }

  if (is_singular()) {
    return get_permalink();
  }

  if (is_category()) {
    $term_link = get_category_link(get_queried_object_id());
    return is_wp_error($term_link) ? home_url('/') : $term_link;
  }

  if (is_home()) {
    return get_permalink((int) get_option('page_for_posts'));
  }

  if (is_search()) {
    return get_search_link();
  }

  global $wp;
  $request = isset($wp->request) ? $wp->request : '';
  return $request ? home_url('/' . trim($request, '/') . '/') : home_url('/');
}

function land76_schema_description() {
  if (is_front_page()) {
    return 'Ландшафтно-строительная компания «Эксперты» выполняет благоустройство участков под ключ в Рыбинске, Ярославле и Ярославской области: дренаж, ливневая канализация, отмостка, плитка, газон, автополив и озеленение.';
  }

  if (is_singular()) {
    if (function_exists('get_field')) {
      $acf_description = get_field('blogseo_seo_description', get_the_ID());
      if (!$acf_description && land76_is_case_seo_template()) {
        $acf_description = get_field('cs87_seo_description', get_the_ID());
      }
      if ($acf_description) {
        return land76_schema_limit($acf_description);
      }
    }

    if (is_page()) {
      $region_description = get_post_meta(get_the_ID(), '_land76_region_description', true);
      if ($region_description) {
        return land76_schema_limit($region_description);
      }
    }

    $excerpt = get_the_excerpt();
    if ($excerpt) {
      return land76_schema_limit($excerpt);
    }

    return land76_schema_limit(get_post_field('post_content', get_the_ID()));
  }

  if (is_category()) {
    $term = get_queried_object();
    if ($term && !empty($term->description)) {
      return land76_schema_limit($term->description);
    }
  }

  return land76_schema_limit(get_bloginfo('description'));
}

function land76_schema_area_served() {
  $cities = array('Рыбинск', 'Ярославль', 'Углич', 'Тутаев', 'Переславль-Залесский', 'Ярославская область');
  $places = array();

  foreach ($cities as $city) {
    $places[] = array(
      '@type' => 'Place',
      'name' => $city,
    );
  }

  return $places;
}

function land76_schema_service_categories() {
  return array(
    87 => array(
      'name' => 'Дренаж участка',
      'serviceType' => 'Дренаж участка под ключ',
      'description' => 'Проектирование и монтаж дренажа участка: глубинный и поверхностный дренаж, отвод воды от дома, дорожек, газона и зон посадок.',
    ),
    88 => array(
      'name' => 'Отмостка вокруг дома',
      'serviceType' => 'Отмостка вокруг дома под ключ',
      'description' => 'Устройство бетонной, мягкой, утепленной и плиточной отмостки вокруг дома с подготовкой основания, уклоном и водоотводом.',
    ),
    89 => array(
      'name' => 'Укладка тротуарной плитки',
      'serviceType' => 'Укладка тротуарной плитки под ключ',
      'description' => 'Укладка тротуарной плитки, дорожек, площадок, парковок и бордюров с подготовкой основания и водоотводом.',
    ),
    90 => array(
      'name' => 'Осушение участка',
      'serviceType' => 'Осушение участка под ключ',
      'description' => 'Осушение сырого, заболоченного или низкого участка: дренаж, канавы, лотки, колодцы, водоотвод и корректировка уклонов.',
    ),
    91 => array(
      'name' => 'Ливневая канализация',
      'serviceType' => 'Ливневая канализация на участке под ключ',
      'description' => 'Монтаж ливневой канализации, дождеприемников, лотков, труб и колодцев для отвода воды с крыши, дорожек, парковки и двора.',
    ),
    92 => array(
      'name' => 'Автополив на участке',
      'serviceType' => 'Автоматический полив участка под ключ',
      'description' => 'Проектирование и монтаж автоматического полива газона, сада, клумб, теплиц и посадок: зоны, трубы, спринклеры, клапаны, контроллер и насосное оборудование.',
    ),
  );
}

function land76_schema_region_template_map() {
  return array(
    'page-drenazh-region.php' => 87,
    'page-otmostka-region.php' => 88,
    'page-plitka-region.php' => 89,
    'page-osushenie-region.php' => 90,
    'page-livnevka-region.php' => 91,
    'page-autopoliv-region.php' => 92,
  );
}

function land76_schema_current_service_category_id() {
  $service_categories = land76_schema_service_categories();

  if (is_category()) {
    $term_id = (int) get_queried_object_id();
    return isset($service_categories[$term_id]) ? $term_id : 0;
  }

  if (is_singular('post')) {
    if (has_category(72, get_the_ID()) && !has_category(74, get_the_ID())) {
      return 0;
    }

    foreach (array_keys($service_categories) as $term_id) {
      if (has_category($term_id, get_the_ID())) {
        return (int) $term_id;
      }
    }
  }

  if (is_page()) {
    foreach (land76_schema_region_template_map() as $template => $term_id) {
      if (is_page_template($template)) {
        return (int) $term_id;
      }
    }
  }

  return 0;
}

function land76_schema_is_named_page($template, $page_ids = array()) {
  if (is_page_template($template)) {
    return true;
  }

  return is_page() && in_array((int) get_queried_object_id(), array_map('intval', $page_ids), true);
}

function land76_schema_is_services_page() {
  return land76_schema_is_named_page('services.php', array(921));
}

function land76_schema_is_blog_page() {
  return land76_schema_is_named_page('blog.php', array(9962));
}

function land76_schema_is_portfolio_page() {
  return land76_schema_is_named_page('portfolio.php', array(160));
}

function land76_schema_is_calculator_page() {
  return land76_schema_is_named_page('calc.php', array(9973));
}

function land76_schema_is_contacts_page() {
  return land76_schema_is_named_page('contacts.php', array(227));
}

function land76_schema_is_about_page() {
  return land76_schema_is_named_page('about.php', array(119));
}

function land76_schema_image_object($post_id = 0, $fallback_url = '') {
  $image_url = '';
  $alt = '';

  if ($post_id && has_post_thumbnail($post_id)) {
    $image_url = get_the_post_thumbnail_url($post_id, 'full');
    $thumbnail_id = get_post_thumbnail_id($post_id);
    $alt = $thumbnail_id ? get_post_meta($thumbnail_id, '_wp_attachment_image_alt', true) : '';
  }

  if (!$image_url && $post_id) {
    $image_url = land76_get_card_image_url($post_id, 'full', false);
    $alt = land76_get_card_image_alt($post_id, get_the_title($post_id));
  }

  if (!$image_url && $fallback_url) {
    $image_url = $fallback_url;
  }

  if (!$image_url) {
    return null;
  }

  return array_filter(array(
    '@type' => 'ImageObject',
    'url' => esc_url_raw($image_url),
    'caption' => land76_schema_strip($alt),
  ));
}

function land76_schema_organization_node() {
  $theme_uri = get_template_directory_uri();

  return array(
    '@type' => array('Organization', 'LocalBusiness', 'HomeAndConstructionBusiness'),
    '@id' => home_url('/#organization'),
    'name' => 'Эксперты',
    'alternateName' => 'Ландшафтно-строительная компания «Эксперты»',
    'url' => home_url('/'),
    'logo' => array(
      '@type' => 'ImageObject',
      'url' => $theme_uri . '/img/logo4.webp',
    ),
    'image' => $theme_uri . '/img/h11.webp',
    'telephone' => '+7-915-978-88-09',
    'priceRange' => '₽₽',
    'address' => array(
      '@type' => 'PostalAddress',
      'addressLocality' => 'Рыбинск',
      'addressRegion' => 'Ярославская область',
      'addressCountry' => 'RU',
    ),
    'areaServed' => land76_schema_area_served(),
    'sameAs' => array('https://vk.com/exp_76'),
  );
}

function land76_schema_website_node() {
  return array(
    '@type' => 'WebSite',
    '@id' => home_url('/#website'),
    'url' => home_url('/'),
    'name' => 'Эксперты',
    'description' => 'Благоустройство участков под ключ в Рыбинске, Ярославле и Ярославской области.',
    'publisher' => array('@id' => home_url('/#organization')),
    'inLanguage' => 'ru-RU',
  );
}

function land76_schema_breadcrumb_node($current_url) {
  if (is_front_page()) {
    return null;
  }

  $items = array(
    array(
      '@type' => 'ListItem',
      'position' => 1,
      'name' => 'Главная',
      'item' => home_url('/'),
    ),
  );

  if (is_category()) {
    $term = get_queried_object();
    if ($term) {
      $items[] = array(
        '@type' => 'ListItem',
        'position' => count($items) + 1,
        'name' => $term->name,
        'item' => $current_url,
      );
    }
  } elseif (is_singular('post')) {
    $service_term_id = land76_schema_current_service_category_id();
    if ($service_term_id) {
      $term = get_category($service_term_id);
      $term_url = get_category_link($service_term_id);
      if ($term && !is_wp_error($term_url)) {
        $items[] = array(
          '@type' => 'ListItem',
          'position' => count($items) + 1,
          'name' => $term->name,
          'item' => $term_url,
        );
      }
    } elseif (has_category(72, get_the_ID())) {
      $blog_url = get_permalink(9962);
      $items[] = array(
        '@type' => 'ListItem',
        'position' => count($items) + 1,
        'name' => 'Полезное',
        'item' => $blog_url ? $blog_url : home_url('/'),
      );
    }

    $items[] = array(
      '@type' => 'ListItem',
      'position' => count($items) + 1,
      'name' => get_the_title(),
      'item' => $current_url,
    );
  } elseif (is_page()) {
    $ancestors = array_reverse(get_post_ancestors(get_the_ID()));
    foreach ($ancestors as $ancestor_id) {
      $items[] = array(
        '@type' => 'ListItem',
        'position' => count($items) + 1,
        'name' => get_the_title($ancestor_id),
        'item' => get_permalink($ancestor_id),
      );
    }

    $items[] = array(
      '@type' => 'ListItem',
      'position' => count($items) + 1,
      'name' => get_the_title(),
      'item' => $current_url,
    );
  } else {
    $items[] = array(
      '@type' => 'ListItem',
      'position' => count($items) + 1,
      'name' => wp_get_document_title(),
      'item' => $current_url,
    );
  }

  return count($items) > 1 ? array(
    '@type' => 'BreadcrumbList',
    '@id' => trailingslashit($current_url) . '#breadcrumb',
    'itemListElement' => $items,
  ) : null;
}

function land76_schema_service_node($current_url) {
  $service_categories = land76_schema_service_categories();
  $service_term_id = land76_schema_current_service_category_id();
  $is_legacy_service_page = land76_schema_is_service_page_template();

  if (!$service_term_id && !$is_legacy_service_page) {
    return null;
  }

  $service = $service_term_id && !empty($service_categories[$service_term_id])
    ? $service_categories[$service_term_id]
    : array(
      'name' => 'Благоустройство участка',
      'serviceType' => 'Благоустройство участка под ключ',
      'description' => 'Ландшафтные, инженерные и строительные работы на частном участке: подготовка, монтаж, благоустройство и уход.',
    );
  $name = $service['name'];
  $description = $service['description'];

  if (is_singular()) {
    $name = get_the_title();
    $description = land76_schema_description();
  } elseif (is_category()) {
    $term = get_queried_object();
    if ($term && !empty($term->name)) {
      $name = $term->name;
    }
    $category_description = land76_schema_description();
    if ($category_description) {
      $description = $category_description;
    }
  } elseif (is_page()) {
    $name = get_the_title();
    $description = land76_schema_description();
  }

  return array_filter(array(
    '@type' => 'Service',
    '@id' => trailingslashit($current_url) . '#service',
    'name' => land76_schema_strip($name),
    'serviceType' => $service['serviceType'],
    'description' => land76_schema_limit($description),
    'provider' => array('@id' => home_url('/#organization')),
    'areaServed' => land76_schema_area_served(),
    'url' => $current_url,
    'category' => $service['name'],
  ));
}

function land76_schema_article_node($current_url) {
  if (!is_singular('post') || land76_schema_current_service_category_id()) {
    return null;
  }

  $image = land76_schema_image_object(get_the_ID());

  return array_filter(array(
    '@type' => has_category(72, get_the_ID()) ? 'BlogPosting' : 'Article',
    '@id' => trailingslashit($current_url) . '#article',
    'headline' => land76_schema_strip(get_the_title()),
    'description' => land76_schema_description(),
    'image' => $image,
    'datePublished' => get_the_date(DATE_W3C, get_the_ID()),
    'dateModified' => get_the_modified_date(DATE_W3C, get_the_ID()),
    'author' => array(
      '@type' => 'Organization',
      '@id' => home_url('/#organization'),
    ),
    'publisher' => array('@id' => home_url('/#organization')),
    'mainEntityOfPage' => array('@id' => trailingslashit($current_url) . '#webpage'),
    'inLanguage' => 'ru-RU',
  ));
}

function land76_schema_case_node($current_url) {
  if (!land76_schema_is_case_template()) {
    return null;
  }

  return array_filter(array(
    '@type' => 'CreativeWork',
    '@id' => trailingslashit($current_url) . '#case',
    'name' => land76_schema_strip(get_the_title()),
    'description' => land76_schema_description(),
    'image' => land76_schema_image_object(get_the_ID()),
    'creator' => array('@id' => home_url('/#organization')),
    'provider' => array('@id' => home_url('/#organization')),
    'url' => $current_url,
    'inLanguage' => 'ru-RU',
  ));
}

function land76_schema_calculator_node($current_url) {
  if (!land76_schema_is_calculator_page()) {
    return null;
  }

  return array(
    '@type' => 'WebApplication',
    '@id' => trailingslashit($current_url) . '#calculator',
    'name' => 'Калькулятор стоимости благоустройства участка',
    'applicationCategory' => 'BusinessApplication',
    'operatingSystem' => 'Web',
    'url' => $current_url,
    'provider' => array('@id' => home_url('/#organization')),
    'inLanguage' => 'ru-RU',
  );
}

function land76_schema_services_item_list_node($current_url) {
  if (!land76_schema_is_services_page()) {
    return null;
  }

  $items = array();
  foreach (land76_schema_service_categories() as $term_id => $service) {
    $url = get_category_link((int) $term_id);
    if (is_wp_error($url)) {
      continue;
    }

    $items[] = array(
      '@type' => 'ListItem',
      'position' => count($items) + 1,
      'url' => $url,
      'name' => $service['name'],
    );
  }

  return array(
    '@type' => 'ItemList',
    '@id' => trailingslashit($current_url) . '#services-list',
    'name' => 'Каталог услуг по благоустройству участка',
    'itemListElement' => $items,
  );
}

function land76_schema_front_faq_node($current_url) {
  if (!is_front_page()) {
    return null;
  }

  $faq_items = array(
    array(
      'question' => 'Можно заказать только одну услугу?',
      'answer' => 'Да, можно заказать отдельную работу: дренаж, ливневую канализацию, отмостку, укладку плитки, автополив, газон или озеленение. Если задачи связаны между собой, мы заранее объясняем, какие работы лучше объединить.',
    ),
    array(
      'question' => 'Нужно ли начинать с проекта?',
      'answer' => 'Для небольших работ иногда достаточно осмотра и схемы. Для комплексного благоустройства, дренажа, ливневки, мощения и автополива проект помогает не ошибиться с уклонами, материалами и очередностью этапов.',
    ),
    array(
      'question' => 'Можно ли делать благоустройство поэтапно?',
      'answer' => 'Да, работы можно разделить на этапы. Важно сразу заложить общую логику участка: водоотвод, основание, дорожки, зоны посадок, газон и полив, чтобы потом не переделывать готовые покрытия.',
    ),
    array(
      'question' => 'Вы рассчитываете стоимость по фото?',
      'answer' => 'По фото можно дать предварительную оценку и список вопросов. Точную смету обычно считаем после осмотра участка, потому что на цену влияют грунт, уклоны, вода, подъезд техники, материалы и объем земляных работ.',
    ),
  );

  $entities = array();
  foreach ($faq_items as $item) {
    $entities[] = array(
      '@type' => 'Question',
      'name' => $item['question'],
      'acceptedAnswer' => array(
        '@type' => 'Answer',
        'text' => $item['answer'],
      ),
    );
  }

  return array(
    '@type' => 'FAQPage',
    '@id' => trailingslashit($current_url) . '#faq',
    'mainEntity' => $entities,
  );
}

function land76_schema_faq_entities($items) {
  if (empty($items) || !is_array($items)) {
    return array();
  }

  $entities = array();
  foreach ($items as $item) {
    $question = isset($item['question']) ? land76_schema_strip($item['question']) : '';
    $answer = isset($item['answer']) ? land76_schema_strip($item['answer']) : '';

    if ($question === '' || $answer === '') {
      continue;
    }

    $entities[] = array(
      '@type' => 'Question',
      'name' => $question,
      'acceptedAnswer' => array(
        '@type' => 'Answer',
        'text' => $answer,
      ),
    );
  }

  return $entities;
}

function land76_schema_acf_faq_node($current_url) {
  if (!function_exists('get_field') || is_front_page()) {
    return null;
  }

  $items = array();

  if (is_category()) {
    $term_id = (int) get_queried_object_id();
    $service_categories = land76_schema_service_categories();
    if (isset($service_categories[$term_id])) {
      $items = get_field('cat87_faq_items', 'category_' . $term_id);
    }
  } elseif (is_singular('post') && land76_schema_current_service_category_id()) {
    $items = get_field('ns87_faq_items', get_the_ID());
  }

  $entities = land76_schema_faq_entities($items);
  if (empty($entities)) {
    return null;
  }

  return array(
    '@type' => 'FAQPage',
    '@id' => trailingslashit($current_url) . '#faq',
    'mainEntity' => $entities,
  );
}

function land76_schema_page_node($current_url, $main_entity_id = '') {
  $page_type = 'WebPage';

  if (is_category() || land76_schema_is_portfolio_page() || land76_schema_is_blog_page() || land76_schema_is_services_page()) {
    $page_type = 'CollectionPage';
  } elseif (land76_schema_is_contacts_page()) {
    $page_type = 'ContactPage';
  } elseif (land76_schema_is_about_page()) {
    $page_type = 'AboutPage';
  }

  $page = array_filter(array(
    '@type' => $page_type,
    '@id' => trailingslashit($current_url) . '#webpage',
    'url' => $current_url,
    'name' => land76_schema_strip(wp_get_document_title()),
    'description' => land76_schema_description(),
    'isPartOf' => array('@id' => home_url('/#website')),
    'about' => array('@id' => home_url('/#organization')),
    'publisher' => array('@id' => home_url('/#organization')),
    'breadcrumb' => !is_front_page() ? array('@id' => trailingslashit($current_url) . '#breadcrumb') : null,
    'mainEntity' => $main_entity_id ? array('@id' => $main_entity_id) : null,
    'inLanguage' => 'ru-RU',
  ));

  return $page;
}

function land76_output_structured_data() {
  if (is_admin() || is_404()) {
    return;
  }

  $current_url = land76_schema_current_url();
  $graph = array(
    land76_schema_organization_node(),
    land76_schema_website_node(),
  );

  $main_entity_id = '';
  $service_node = land76_schema_service_node($current_url);
  $article_node = land76_schema_article_node($current_url);
  $case_node = land76_schema_case_node($current_url);
  $calculator_node = land76_schema_calculator_node($current_url);
  $services_item_list_node = land76_schema_services_item_list_node($current_url);
  $faq_node = is_front_page() ? land76_schema_front_faq_node($current_url) : land76_schema_acf_faq_node($current_url);

  if ($article_node) {
    $main_entity_id = $article_node['@id'];
  } elseif ($service_node) {
    $main_entity_id = $service_node['@id'];
  } elseif ($case_node) {
    $main_entity_id = $case_node['@id'];
  } elseif ($calculator_node) {
    $main_entity_id = $calculator_node['@id'];
  } elseif ($services_item_list_node) {
    $main_entity_id = $services_item_list_node['@id'];
  }

  $graph[] = land76_schema_page_node($current_url, $main_entity_id);

  foreach (array($service_node, $article_node, $case_node, $calculator_node, $services_item_list_node, land76_schema_breadcrumb_node($current_url), $faq_node) as $node) {
    if ($node) {
      $graph[] = $node;
    }
  }

  $schema = array(
    '@context' => 'https://schema.org',
    '@graph' => $graph,
  );

  echo "\n<script type=\"application/ld+json\" class=\"land76-schema\">";
  echo wp_json_encode($schema, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
  echo "</script>\n";
}
add_action('wp_head', 'land76_output_structured_data', 30);



if ( function_exists('acf_add_options_page') ) {

  acf_add_options_page(array(
      'page_title' 	=> 'Настройка темы',
      'menu_title'	=> 'Настройка темы',
      'menu_slug' 	=> 'theme-general-settings',
      'capability'	=> 'edit_posts',
      'redirect'		=> false
    ));
}

// ACF: Секции категорий на главной (repeater на странице Настройка темы)
add_action('acf/init', 'land76_register_home_category_sections_acf');
function land76_register_home_category_sections_acf() {
  if (!function_exists('acf_add_local_field_group')) return;

  acf_add_local_field_group(array(
    'key' => 'group_home_category_sections',
    'title' => 'Секции категорий на главной',
    'fields' => array(
      array(
        'key' => 'field_home_category_sections',
        'label' => 'Секции',
        'name' => 'home_category_sections',
        'type' => 'repeater',
        'layout' => 'block',
        'button_label' => 'Добавить секцию категории',
        'sub_fields' => array(
          array(
            'key' => 'field_home_sec_title',
            'label' => 'Заголовок секции (H2)',
            'name' => 'title',
            'type' => 'text',
          ),
          array(
            'key' => 'field_home_sec_text',
            'label' => 'Текстовый блок',
            'name' => 'text',
            'type' => 'wysiwyg',
            'tabs' => 'visual',
            'media_upload' => 1,
          ),
          array(
            'key' => 'field_home_sec_cat',
            'label' => 'Категория услуг',
            'name' => 'category',
            'type' => 'taxonomy',
            'taxonomy' => 'category',
            'field_type' => 'select',
            'return_format' => 'id',
          ),
        ),
      ),
    ),
    'location' => array(
      array(
        array(
          'param' => 'options_page',
          'operator' => '==',
          'value' => 'theme-general-settings',
        ),
      ),
    ),
    'position' => 'normal',
    'style' => 'default',
    'label_placement' => 'top',
  ));
}
