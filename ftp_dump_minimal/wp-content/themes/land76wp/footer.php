<footer class="footer wrapper"><img class="footer__logo" src="<?php echo get_template_directory_uri() ?>/img/logo4.png" alt="" role="presentation" />
    <div class="footer__services-wrap"><span class="footer__title">Услуги</span>
      <ul class="footer__services columns2">
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/services/landshaftnoe-proektirovanie/">Ландшафтное проектирование</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/drenazh-uchastka/">Дренаж участка </a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/ukladka-trotuarnoy-plitki/">Укладка тротуарной плитки</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/livnevaya-kanalizatsiya/">Ливневая канализация</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/services/posadka-derevev-i-kustarnikov/">Посадка деревьев и кустарников</a></li>
        <li class="footer__item"><a class="footer__link" href="https://exp76.ru/category/avtopoliv-na-uchastke/">Системы автоматического полива</a></li>
      </ul>
    </div>
    <div class="footer__wrap"><a class="footer__number" href="tel:89159788809"><span class="footer__number">8(915)-978-88-09</span><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300" width="20" height="20">
          <circle class="active-path" cx="150" cy="226.1" r="11.7" data-original="#000000" data-old_color="#000000"
            fill="#a2f9a9"></circle>
          <path class="active-path svg-path"
            d="M182.7 68.2h-65.4a6.5 6.5 0 00-6.6 6.4v123.6c0 3.5 3 6.3 6.6 6.3h65.4c3.7 0 6.6-2.8 6.6-6.3V74.6c0-3.5-3-6.4-6.6-6.4z"
            data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
          <path class="active-path svg-path"
            d="M150 0a150 150 0 100 300 150 150 0 000-300zm58.4 224c0 11.5-9.3 20.8-20.8 20.8h-75.2A20.8 20.8 0 0191.6 224V75.3c0-11.4 9.3-20.7 20.8-20.7h75.2c11.5 0 20.8 9.3 20.8 20.7V224z"
            data-original="#000000" data-old_color="#000000" fill="#a2f9a9"></path>
        </svg></a><span class="footer__copiryght">© 2018 Компания "Эксперты"</span></div>

 <script src="https://unpkg.com/aos@2.3.1/dist/aos.js"></script> 
<script src="https://cdnjs.cloudflare.com/ajax/libs/parallax/3.1.0/parallax.min.js"></script> 
  <script src="https://unpkg.com/swiper/swiper-bundle.js"></script>
  <script src="<?php bloginfo('template_directory'); ?>/js/main.js?v=20260511"></script>
  <?php if (is_front_page()): ?>
  <script>
  document.addEventListener('DOMContentLoaded', function() {
    var carousels = document.querySelectorAll('.home-cat-carousel');

    carousels.forEach(function(carousel) {
      var viewport = carousel.querySelector('.home-cat-viewport');
      var track = carousel.querySelector('.home-cat-track');
      var slides = Array.prototype.slice.call(carousel.querySelectorAll('.home-cat-slide'));
      var prev = carousel.querySelector('.home-cat-arrow--prev');
      var next = carousel.querySelector('.home-cat-arrow--next');
      var pagination = carousel.querySelector('.home-cat-pagination');
      var index = 0;
      var perView = 1;
      var maxIndex = 0;
      var currentOffset = 0;
      var dragStartX = 0;
      var dragDeltaX = 0;
      var dragging = false;

      function getPerView() {
        if (window.innerWidth < 600) return 1;
        if (window.innerWidth <= 768) return 2;
        return 3;
      }

      function buildPagination() {
        pagination.innerHTML = '';
        for (var i = 0; i <= maxIndex; i++) {
          var dot = document.createElement('button');
          dot.type = 'button';
          dot.setAttribute('aria-label', 'Показать услуги ' + (i + 1));
          dot.addEventListener('click', function(page) {
            return function() {
              index = page;
              update();
            };
          }(i));
          pagination.appendChild(dot);
        }
      }

      function normalizeCardHeights() {
        var services = slides.map(function(slide) {
          return slide.querySelector('.service');
        }).filter(Boolean);

        services.forEach(function(service) {
          service.style.height = 'auto';
        });

        var maxServiceHeight = services.reduce(function(maxHeight, service) {
          return Math.max(maxHeight, service.offsetHeight);
        }, 0);

        services.forEach(function(service) {
          service.style.height = maxServiceHeight + 'px';
        });

        return maxServiceHeight;
      }

      function update() {
        perView = getPerView();
        maxIndex = Math.max(0, slides.length - perView);
        index = Math.min(index, maxIndex);

        var maxServiceHeight = normalizeCardHeights();
        var offset = slides[index] ? slides[index].offsetLeft - slides[0].offsetLeft : 0;
        currentOffset = offset;
        track.style.transform = 'translate3d(-' + currentOffset + 'px, 0, 0)';
        viewport.style.height = maxServiceHeight ? (maxServiceHeight + 80) + 'px' : '';

        prev.classList.toggle('is-disabled', index === 0);
        next.classList.toggle('is-disabled', index >= maxIndex);

        if (pagination.children.length !== maxIndex + 1) {
          buildPagination();
        }

        Array.prototype.forEach.call(pagination.children, function(dot, dotIndex) {
          dot.classList.toggle('is-active', dotIndex === index);
        });
      }

      carousel.land76Update = update;

      prev.addEventListener('click', function() {
        index = Math.max(0, index - 1);
        update();
      });

      next.addEventListener('click', function() {
        index = Math.min(maxIndex, index + 1);
        update();
      });

      function clientX(event) {
        return event.touches && event.touches.length ? event.touches[0].clientX : event.clientX;
      }

      function startDrag(event) {
        dragging = true;
        dragStartX = clientX(event);
        dragDeltaX = 0;
        track.classList.add('is-dragging');
      }

      function moveDrag(event) {
        if (!dragging) return;
        dragDeltaX = clientX(event) - dragStartX;
        track.style.transform = 'translate3d(' + (-currentOffset + dragDeltaX) + 'px, 0, 0)';
      }

      function endDrag() {
        if (!dragging) return;
        dragging = false;
        track.classList.remove('is-dragging');

        if (Math.abs(dragDeltaX) > 45) {
          index += dragDeltaX < 0 ? 1 : -1;
          index = Math.max(0, Math.min(maxIndex, index));
        }

        update();
      }

      viewport.addEventListener('mousedown', startDrag);
      viewport.addEventListener('mousemove', moveDrag);
      viewport.addEventListener('mouseup', endDrag);
      viewport.addEventListener('mouseleave', endDrag);
      viewport.addEventListener('touchstart', startDrag, { passive: true });
      viewport.addEventListener('touchmove', moveDrag, { passive: true });
      viewport.addEventListener('touchend', endDrag);
      viewport.addEventListener('touchcancel', endDrag);

      window.addEventListener('resize', update);
      window.addEventListener('load', update);
      update();
    });

    var tabs = Array.prototype.slice.call(document.querySelectorAll('.home-services-tabs__button'));
    var panels = Array.prototype.slice.call(document.querySelectorAll('.home-cat-panel'));

    tabs.forEach(function(tab) {
      tab.addEventListener('click', function() {
        var tabIndex = tab.getAttribute('data-home-tab');

        tabs.forEach(function(item) {
          var isActive = item === tab;
          item.classList.toggle('is-active', isActive);
          item.setAttribute('aria-selected', isActive ? 'true' : 'false');
        });

        panels.forEach(function(panel) {
          var isActive = panel.getAttribute('data-home-panel') === tabIndex;
          panel.classList.toggle('is-active', isActive);

          if (isActive) {
            var carousel = panel.querySelector('.home-cat-carousel');
            if (carousel && typeof carousel.land76Update === 'function') {
              setTimeout(carousel.land76Update, 20);
            }
          }
        });
      });
    });
  });
  </script>
  <?php endif; ?>
<!-- Yandex.Metrika counter --> <script type="text/javascript"> (function (d, w, c) { (w[c] = w[c] || []).push(function() { try { w.yaCounter42305934 = new Ya.Metrika({ id:42305934, clickmap:true, trackLinks:true, accurateTrackBounce:true, webvisor:true }); } catch(e) { } }); var n = d.getElementsByTagName("script")[0], s = d.createElement("script"), f = function () { n.parentNode.insertBefore(s, n); }; s.type = "text/javascript"; s.async = true; s.src = "https://mc.yandex.ru/metrika/watch.js"; if (w.opera == "[object Opera]") { d.addEventListener("DOMContentLoaded", f, false); } else { f(); } })(document, window, "yandex_metrika_callbacks"); </script> <noscript><div><img src="https://mc.yandex.ru/watch/42305934" style="position:absolute; left:-9999px;" alt="" /></div></noscript> <!-- /Yandex.Metrika counter -->
  <?php wp_footer(); ?>
    <link href="https://unpkg.com/aos@2.3.1/dist/aos.css" rel="stylesheet">
  <link link rel="stylesheet" href="https://unpkg.com/swiper/swiper-bundle.css">
  </footer>

<style>
	.hero__breadcramps{
		z-index:99999
	}

  @media only screen and (max-width: 767px) {
    [data-aos],
    [data-aos][data-aos][data-aos-delay],
    [data-aos][data-aos][data-aos-duration] {
      opacity: 1 !important;
      visibility: visible !important;
      transform: none !important;
      transition: none !important;
    }
  }
</style>

</body>

</html>
