<?php
if (!defined('ABSPATH')) {
  exit;
}

function land76wp_drenazh_service_slugs() {
  return array(
    'cena-drenazha-uchastka',
    'vysokie-gruntovye-vody',
    'glinistaya-pochva',
    'vokrug-doma',
    'glubinnyy',
    'poverhnostnyy',
    '10-sotok',
    '6-sotok',
    's-uklonom',
  );
}

function land76wp_drenazh_category_seo() {
  return array(
    'title' => 'Дренаж участка под ключ в Ярославле и области — цена и монтаж',
    'description' => 'Проектируем и монтируем дренаж участка под ключ: грунтовые воды, глинистая почва, вода у дома, поверхностный и глубинный дренаж. Расчет стоимости за 1 день.',
  );
}

function land76wp_drenazh_post_seo() {
  return array(
    'cena-drenazha-uchastka' => array(
      'title' => 'Стоимость дренажа участка — цена под ключ и состав работ',
      'description' => 'Сколько стоит дренаж участка под ключ: от чего зависит цена, какие работы входят в смету, как рассчитываем глубинный и поверхностный дренаж.',
    ),
    'vysokie-gruntovye-vody' => array(
      'title' => 'Дренаж участка при высоких грунтовых водах под ключ',
      'description' => 'Дренаж участка при высоком уровне грунтовых вод: обследование, схема отвода воды, глубина траншей, колодцы и защита фундамента.',
    ),
    'glinistaya-pochva' => array(
      'title' => 'Дренаж глинистого участка — схема и монтаж',
      'description' => 'Делаем дренаж глинистого участка под ключ: подбираем схему, материалы и уклоны, чтобы убрать застой воды после дождей и таяния снега.',
    ),
    'vokrug-doma' => array(
      'title' => 'Дренаж вокруг дома — защита фундамента от воды',
      'description' => 'Монтаж дренажа вокруг дома для защиты фундамента, цоколя и отмостки от воды. Рассчитываем схему, глубину и точки отвода.',
    ),
    'glubinnyy' => array(
      'title' => 'Глубинный дренаж участка под ключ',
      'description' => 'Проектируем и монтируем глубинный дренаж участка под ключ: трубы, щебень, геотекстиль, колодцы, уклоны и безопасный отвод воды.',
    ),
    'poverhnostnyy' => array(
      'title' => 'Поверхностный дренаж участка под ключ',
      'description' => 'Поверхностный дренаж участка для отвода дождевой и талой воды от дома, дорожек, газона и въезда. Схема, монтаж и расчет стоимости.',
    ),
    '10-sotok' => array(
      'title' => 'Дренаж участка 10 соток — цена и схема работ',
      'description' => 'Дренаж участка 10 соток под ключ: схема трасс, расчет материалов, сроки монтажа и ориентировочная стоимость работ.',
    ),
    '6-sotok' => array(
      'title' => 'Дренаж участка 6 соток — стоимость и монтаж',
      'description' => 'Дренаж участка 6 соток с учетом плотной застройки, дорожек и посадок. Подбираем компактную схему и считаем стоимость монтажа.',
    ),
    's-uklonom' => array(
      'title' => 'Дренаж участка с уклоном — схема отвода воды',
      'description' => 'Дренаж участка с уклоном: проектируем перехват воды, правильные трассы, лотки и колодцы, чтобы вода не шла к дому и дорожкам.',
    ),
  );
}

function land76wp_drenazh_regions() {
  return array(
    'yaroslavl' => array(
      'name' => 'Ярославль',
      'locative' => 'Ярославле',
      'title' => 'Дренаж участка в Ярославле под ключ — цена и монтаж',
      'description' => 'Делаем дренаж участка в Ярославле и пригородах: осмотр, схема, смета, монтаж глубинного и поверхностного дренажа. Расчет стоимости за 1 день.',
      'lead' => 'Проектируем и монтируем дренаж для участков в Ярославле и пригородах: убираем воду от дома, дорожек, газона и зоны въезда.',
      'text' => array(
        'В Ярославле часто приходится работать на уже обжитых участках: рядом стоят дом, забор, дорожки, парковка и посадки. Поэтому мы сначала смотрим подъезд техники и трассы, чтобы дренаж решил проблему воды без лишних раскопок.',
        'Для плотной застройки подбираем схему точечно: где нужен глубинный дренаж, где достаточно поверхностного отвода, а где систему лучше связать с ливневкой.',
      ),
    ),
    'rybinsk' => array(
      'name' => 'Рыбинск',
      'locative' => 'Рыбинске',
      'title' => 'Дренаж участка в Рыбинске под ключ — цена и монтаж',
      'description' => 'Дренаж участка в Рыбинске и районе под ключ: глинистые почвы, низины, вода после дождя, расчет схемы и монтаж системы отвода воды.',
      'lead' => 'Помогаем убрать застой воды на участках в Рыбинске и районе, подбираем схему под рельеф, грунт и расположение дома.',
      'text' => array(
        'В Рыбинске и районе нередко встречаются низины и глинистые грунты, где вода стоит после дождя или таяния снега. В таких условиях важно не просто выкопать траншеи, а правильно вывести воду в рабочую точку сброса.',
        'Мы рассчитываем глубину, уклоны и количество колодцев так, чтобы система работала стабильно и не мешала дальнейшему благоустройству участка.',
      ),
    ),
    'uglich' => array(
      'name' => 'Углич',
      'locative' => 'Угличе',
      'title' => 'Дренаж участка в Угличе под ключ — расчет и монтаж',
      'description' => 'Проектируем и монтируем дренаж участка в Угличе: вода у дома и дорожек, перепады рельефа, схема отвода и расчет стоимости.',
      'lead' => 'Делаем дренаж на частных участках в Угличе, когда вода подходит к дому, стоит у дорожек или уходит не туда из-за рельефа.',
      'text' => array(
        'На участках в Угличе важны перепады рельефа и направление естественного стока. Если воду не перехватить заранее, она идет к фундаменту, дорожкам и зонам отдыха.',
        'Мы подбираем схему с учетом отметок участка: где ставить трубы, где нужны лотки, как вывести воду и сохранить удобство территории.',
      ),
    ),
    'tutaev' => array(
      'name' => 'Тутаев',
      'locative' => 'Тутаеве',
      'title' => 'Дренаж участка в Тутаеве под ключ — схема и стоимость',
      'description' => 'Дренаж участка в Тутаеве под ключ: защита фундамента, отвод воды с сырого грунта, схема работ, смета и монтаж.',
      'lead' => 'Монтируем дренаж в Тутаеве и пригороде, чтобы убрать сырость грунта и защитить фундамент, отмостку и дорожки.',
      'text' => array(
        'Для участков в Тутаеве часто актуальна сырость грунта рядом с домом: вода задерживается у фундамента, подмывает дорожки и мешает пользоваться территорией.',
        'Мы начинаем с осмотра и схемы: определяем, где нужен глубинный дренаж, где хватит поверхностного отвода, и как безопасно вывести воду за пределы проблемной зоны.',
      ),
    ),
    'pereslavl' => array(
      'name' => 'Переславль',
      'locative' => 'Переславле',
      'title' => 'Дренаж участка в Переславле под ключ — цена и монтаж',
      'description' => 'Дренаж участка в Переславле под ключ: глина, низины, вода после дождей, подготовка участка к благоустройству и расчет стоимости.',
      'lead' => 'Делаем дренаж участков в Переславле до благоустройства и на готовых территориях, где вода стоит после дождей или таяния снега.',
      'text' => array(
        'В Переславле дренаж лучше планировать до мощения, газона и посадок, особенно если участок расположен в низине или на глинистом грунте.',
        'Если благоустройство уже сделано, подбираем аккуратную схему с минимальным вмешательством и понятной логикой обслуживания системы.',
      ),
    ),
  );
}

function land76wp_register_regional_drenazh_routes() {
  add_rewrite_rule(
    '^drenazh-regiony-sitemap\.xml$',
    'index.php?land76_drenazh_regions_sitemap=1',
    'top'
  );
  add_rewrite_rule(
    '^drenazh-regiony/?$',
    'index.php?land76_drenazh_regions_sitemap=1',
    'top'
  );

  add_rewrite_rule(
    '^(?!category/)([^/]+)/drenazh-uchastka/?$',
    'index.php?land76_city=$matches[1]&land76_service=drenazh-uchastka',
    'top'
  );
}
add_action('init', 'land76wp_register_regional_drenazh_routes');

function land76wp_regional_drenazh_query_vars($vars) {
  $vars[] = 'land76_city';
  $vars[] = 'land76_service';
  $vars[] = 'land76_drenazh_regions_sitemap';
  return $vars;
}
add_filter('query_vars', 'land76wp_regional_drenazh_query_vars');

function land76wp_render_drenazh_regions_sitemap() {
  if (get_query_var('land76_drenazh_regions_sitemap') !== '1') {
    return;
  }

  status_header(200);
  header('Content-Type: application/xml; charset=utf-8');
  echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
  echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
  foreach (land76wp_drenazh_regions() as $slug => $region) {
    echo "  <url>\n";
    echo '    <loc>' . esc_url(home_url('/' . $slug . '/drenazh-uchastka/')) . "</loc>\n";
    echo "    <changefreq>monthly</changefreq>\n";
    echo "    <priority>0.8</priority>\n";
    echo "  </url>\n";
  }
  echo "</urlset>\n";
  exit;
}
add_action('template_redirect', 'land76wp_render_drenazh_regions_sitemap', 1);

function land76wp_get_current_drenazh_region() {
  $city = get_query_var('land76_city');
  $service = get_query_var('land76_service');
  if ($service !== 'drenazh-uchastka' || empty($city)) {
    return null;
  }

  $regions = land76wp_drenazh_regions();
  return isset($regions[$city]) ? array_merge(array('slug' => $city), $regions[$city]) : null;
}

function land76wp_regional_drenazh_template($template) {
  $service = get_query_var('land76_service');
  if (empty($service)) {
    return $template;
  }

  $region = land76wp_get_current_drenazh_region();
  if ($region) {
    $regional_template = get_template_directory() . '/inc/regional-drenazh-template.php';
    return file_exists($regional_template) ? $regional_template : $template;
  }

  global $wp_query;
  $wp_query->set_404();
  status_header(404);
  nocache_headers();
  return get_404_template();
}
add_filter('template_include', 'land76wp_regional_drenazh_template', 20);

function land76wp_drenazh_aioseo_title($title) {
  $region = land76wp_get_current_drenazh_region();
  if ($region) {
    return $region['title'];
  }

  if (is_category(87)) {
    $seo = land76wp_drenazh_category_seo();
    return $seo['title'];
  }

  if (is_singular('post')) {
    $post = get_post();
    $post_seo = land76wp_drenazh_post_seo();
    if ($post && has_category(87, $post) && isset($post_seo[$post->post_name])) {
      return $post_seo[$post->post_name]['title'];
    }
  }

  return $title;
}
add_filter('aioseo_title', 'land76wp_drenazh_aioseo_title', 20);
add_filter('pre_get_document_title', 'land76wp_drenazh_aioseo_title', 20);

function land76wp_drenazh_aioseo_description($description) {
  $region = land76wp_get_current_drenazh_region();
  if ($region) {
    return $region['description'];
  }

  if (is_category(87)) {
    $seo = land76wp_drenazh_category_seo();
    return $seo['description'];
  }

  if (is_singular('post')) {
    $post = get_post();
    $post_seo = land76wp_drenazh_post_seo();
    if ($post && has_category(87, $post) && isset($post_seo[$post->post_name])) {
      return $post_seo[$post->post_name]['description'];
    }
  }

  return $description;
}
add_filter('aioseo_description', 'land76wp_drenazh_aioseo_description', 20);

function land76wp_drenazh_region_canonical($canonical) {
  $region = land76wp_get_current_drenazh_region();
  if ($region) {
    return home_url('/' . $region['slug'] . '/drenazh-uchastka/');
  }

  return $canonical;
}
add_filter('aioseo_canonical_url', 'land76wp_drenazh_region_canonical', 20);
