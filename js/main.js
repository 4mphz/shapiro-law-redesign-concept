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
      alert('This is a design preview. The form is not connected to a backend, so nothing was sent.');
    });
  }
});
