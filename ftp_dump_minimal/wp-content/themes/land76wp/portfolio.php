<?php
/*
Template Name: Фотогалерея
*/
?>

<?php get_header('page'); ?>

<section class="portfolio wrapper">

  <div class="portfolio__bg-left" data-aos="fade-right" data-aos-duration="600"><img
      src="<?php echo get_template_directory_uri() ?>/img/bg-left.png"></div>
  <h2 class="portfolio__title" data-aos="fade-right" data-aos-duration="700">Наши работы </h2>

	<style>
		.case-container{
			display: grid;
    		grid-template-columns: 1fr 1fr;
    		grid-gap: 40px;
		}
		.case-container .case{
			height: fit-content;
		}
		.case-container .case .case__img-wrap{
			height: 300px;
		}
		
		.case__title{
			    font-size: 26px;
    			margin-bottom: 10px;
		}
		.case__description{
			font-size: 16px;
		}
		
		@media only screen and (max-width: 768px) {
			.case-container{
			display: grid;
    		grid-template-columns: 1fr;
    		grid-gap: 30px;
			}
			.case-container .case .case__img-wrap{
				    height: 200px;
			}
		}
		
	</style>

<?php
$paged = (get_query_var('paged')) ? get_query_var('paged') : 1;

$query = new WP_Query(array(
  'post_type'      => 'page',
  'posts_per_page' => 4, // Количество постов на странице
  'category__in'   => array(75),
  'orderby'        => 'date',
  'order'          => 'DESC',
  'paged'          => $paged,
));

if ($query->have_posts()): ?>

  <div class="case-container"> <!-- Обертка для карточек -->

    <?php while ($query->have_posts()):
      $query->the_post(); ?>

      <div class="case swiper-slide">
        <div class="case__img-wrap">
          <?php
          $thumb_large  = get_the_post_thumbnail_url(null, 'large'); // Для десктопа
          $thumb_medium = get_the_post_thumbnail_url(null, 'medium'); // Для мобильных
          $alt          = get_the_title(); // Используем название поста как alt
          ?>
          <img class="case__img" src="<?php echo $thumb_medium; ?>"
            srcset="<?php echo $thumb_medium; ?> 768w, <?php echo $thumb_large; ?> 1200w"
            sizes="(max-width: 768px) 768px, 1200px" alt="<?php echo esc_attr($alt); ?>" />
        </div>

        <div class="case__content">
          <p class="case__title"><?php the_title(); ?></p>
          <div class="case__description"><?php the_excerpt(); ?></div>
          <a class="case__link" href="<?php the_permalink(); ?>">Подробнее</a>
        </div>
      </div>

    <?php endwhile; ?>

  </div> <!-- Закрытие case-container -->

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

