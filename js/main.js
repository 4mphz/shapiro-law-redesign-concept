document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.nav-toggle');
  var rit = document.querySelector('.header-rit');
  if (toggle && rit) {
    toggle.addEventListener('click', function () {
      rit.classList.toggle('open');
    });
  }

  var header = document.getElementById('site-header');
  if (header) {
    var threshold = 400;
    window.addEventListener('scroll', function () {
      if (window.innerWidth <= 992) { header.classList.remove('is-sticky'); return; }
      if (window.scrollY > threshold) {
        header.classList.add('is-sticky');
      } else {
        header.classList.remove('is-sticky');
      }
    }, { passive: true });
  }

  /* iPhone / touch phones: "Book your free consultation" must do something
     tangible on tap. On this preview the contact form is inert (no backend),
     which feels like a dead button. Coarse-pointer devices get the dialer
     instead — same number already used for the Call CTA. Desktop keeps the
     contact page. */
  var coarse = window.matchMedia('(hover: none) and (pointer: coarse)');
  if (coarse.matches) {
    document.querySelectorAll('a.cmn-btn[href]').forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (!/contact\.html(?:#.*)?$/i.test(href)) return;
      var label = (a.textContent || '').replace(/\s+/g, ' ').trim();
      // Match consultation CTAs only — not "Purchase The Book"
      if (!/^(book your free consultation|reserve su consulta)/i.test(label)) return;
      a.setAttribute('href', 'tel:7182957000');
      a.setAttribute('data-preview-mobile-cta', 'tel');
    });
  }

  var testiItems = document.querySelectorAll('.hm-testi-list .testi-item');
  var testiPrev = document.querySelector('.testi-prev');
  var testiNext = document.querySelector('.testi-next');
  if (testiItems.length && testiPrev && testiNext) {
    var idx = 0;
    var show = function (i) {
      testiItems.forEach(function (el, j) { el.classList.toggle('active', j === i); });
    };
    testiPrev.addEventListener('click', function () { idx = (idx - 1 + testiItems.length) % testiItems.length; show(idx); });
    testiNext.addEventListener('click', function () { idx = (idx + 1) % testiItems.length; show(idx); });
  }

  var form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var go = window.confirm(
        'This is a design preview — the form is not connected yet, so nothing was sent.\n\nCall 718.295.7000 now instead?'
      );
      if (go) window.location.href = 'tel:7182957000';
    });
  }
});
