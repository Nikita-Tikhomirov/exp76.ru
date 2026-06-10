(function () {
  var mobileQuery = window.matchMedia('(max-width: 768px)');
  var selectors = [
    '.home-task-grid',
    '.home-service-grid',
    '.home-work-grid',
    '.services-hub__cards',
    '.services__cards.columns3'
  ];

  function visibleSlides(slides) {
    return slides.filter(function (slide) {
      return !slide.classList.contains('is-hidden') && slide.offsetParent !== null;
    });
  }

  function setupSlider(container) {
    if (!container || container.dataset.mobileCardSlider === 'ready') {
      return;
    }

    if (container.closest('.home-cat-carousel') || !container.querySelector('img')) {
      return;
    }

    var slides = Array.prototype.slice.call(container.children);
    if (slides.length < 2) {
      return;
    }

    container.dataset.mobileCardSlider = 'ready';
    container.classList.add('land76-mobile-slider');

    var shell = document.createElement('div');
    shell.className = 'land76-mobile-slider-shell';

    var viewport = document.createElement('div');
    viewport.className = 'land76-mobile-slider-viewport';

    var controls = document.createElement('div');
    controls.className = 'land76-mobile-slider-controls';

    var prev = document.createElement('button');
    prev.className = 'land76-mobile-slider-arrow land76-mobile-slider-arrow--prev';
    prev.type = 'button';
    prev.setAttribute('aria-label', 'Предыдущая карточка');
    prev.innerHTML = '<span aria-hidden="true">‹</span>';

    var next = document.createElement('button');
    next.className = 'land76-mobile-slider-arrow land76-mobile-slider-arrow--next';
    next.type = 'button';
    next.setAttribute('aria-label', 'Следующая карточка');
    next.innerHTML = '<span aria-hidden="true">›</span>';

    var dots = document.createElement('div');
    dots.className = 'land76-mobile-slider-dots';
    dots.setAttribute('aria-label', 'Навигация по карточкам');

    container.parentNode.insertBefore(shell, container);
    viewport.appendChild(container);
    controls.appendChild(prev);
    controls.appendChild(dots);
    controls.appendChild(next);
    shell.appendChild(viewport);
    shell.appendChild(controls);

    var index = 0;
    var startX = 0;
    var deltaX = 0;
    var dragging = false;

    function getSlides() {
      return visibleSlides(Array.prototype.slice.call(container.children));
    }

    function buildDots(count) {
      dots.innerHTML = '';
      for (var i = 0; i < count; i += 1) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.className = 'land76-mobile-slider-dot';
        dot.setAttribute('aria-label', 'Показать карточку ' + (i + 1));
        dot.addEventListener('click', function (page) {
          return function () {
            index = page;
            update();
          };
        }(i));
        dots.appendChild(dot);
      }
    }

    function update() {
      var activeSlides = getSlides();
      if (!mobileQuery.matches || activeSlides.length < 2) {
        container.style.transform = '';
        shell.classList.toggle('is-active', false);
        return;
      }

      shell.classList.toggle('is-active', true);
      index = Math.max(0, Math.min(index, activeSlides.length - 1));

      if (dots.children.length !== activeSlides.length) {
        buildDots(activeSlides.length);
      }

      var firstOffset = activeSlides[0].offsetLeft;
      var offset = activeSlides[index].offsetLeft - firstOffset;
      container.style.transform = 'translate3d(-' + offset + 'px, 0, 0)';

      prev.disabled = index === 0;
      next.disabled = index >= activeSlides.length - 1;

      Array.prototype.forEach.call(dots.children, function (dot, dotIndex) {
        dot.classList.toggle('is-active', dotIndex === index);
      });
    }

    function change(direction) {
      index += direction;
      update();
    }

    function clientX(event) {
      if (event.touches && event.touches.length) {
        return event.touches[0].clientX;
      }
      if (event.changedTouches && event.changedTouches.length) {
        return event.changedTouches[0].clientX;
      }
      return event.clientX;
    }

    function startDrag(event) {
      if (!mobileQuery.matches) {
        return;
      }
      dragging = true;
      startX = clientX(event);
      deltaX = 0;
      container.classList.add('is-dragging');
    }

    function moveDrag(event) {
      if (!dragging || !mobileQuery.matches) {
        return;
      }
      deltaX = clientX(event) - startX;
    }

    function endDrag() {
      if (!dragging) {
        return;
      }
      dragging = false;
      container.classList.remove('is-dragging');

      if (Math.abs(deltaX) > 45) {
        change(deltaX < 0 ? 1 : -1);
        return;
      }

      update();
    }

    prev.addEventListener('click', function () { change(-1); });
    next.addEventListener('click', function () { change(1); });
    viewport.addEventListener('touchstart', startDrag, { passive: true });
    viewport.addEventListener('touchmove', moveDrag, { passive: true });
    viewport.addEventListener('touchend', endDrag);
    viewport.addEventListener('touchcancel', endDrag);

    window.addEventListener('resize', update);
    window.addEventListener('load', update);
    update();
  }

  function init() {
    selectors.forEach(function (selector) {
      Array.prototype.forEach.call(document.querySelectorAll(selector), setupSlider);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
}());
