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

/* Preview review mode.
   Reviewers can pin notes to page elements, submit them to the shared review
   inbox, and browse both local drafts and previously submitted comments. */
(function () {
  'use strict';

  // The Worker allows only this Pages project and its pull-request preview
  // domains. GitHub credentials remain only in Worker secrets.
  var config = window.SHAPIRO_REVIEW_CONFIG || {
    endpoint: 'https://shapiro-preview-feedback.aehun.workers.dev',
    reviewer: 'Jason'
  };
  var endpoint = config.endpoint || '';
  var storageKey = 'shapiro-preview-feedback-v1';
  var notes = [];
  var submittedNotes = [];
  var selecting = false;
  var selectedElement = null;
  var hoverTarget = null;
  var modal = null;

  try { notes = JSON.parse(window.localStorage.getItem(storageKey) || '[]'); } catch (_) { notes = []; }

  function normalText(element) {
    return (element.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 280);
  }

  function selectorFor(element) {
    if (element.id) return '#' + CSS.escape(element.id);
    var segments = [];
    var node = element;
    while (node && node.nodeType === 1 && node !== document.body && segments.length < 6) {
      var name = node.tagName.toLowerCase();
      var classes = Array.prototype.slice.call(node.classList || []).filter(function (item) {
        return !/^review-/.test(item);
      }).slice(0, 2);
      if (classes.length) name += '.' + classes.map(CSS.escape).join('.');
      var parent = node.parentElement;
      if (parent) {
        var siblings = Array.prototype.filter.call(parent.children, function (child) { return child.tagName === node.tagName; });
        if (siblings.length > 1) name += ':nth-of-type(' + (siblings.indexOf(node) + 1) + ')';
      }
      segments.unshift(name);
      node = parent;
    }
    return segments.join(' > ');
  }

  function selectedSummary(element) {
    var text = normalText(element);
    if (text) return text;
    if (element.alt) return 'Image: ' + element.alt;
    if (element.getAttribute('aria-label')) return element.getAttribute('aria-label');
    return element.tagName.toLowerCase();
  }

  function persist() {
    window.localStorage.setItem(storageKey, JSON.stringify(notes));
  }

  function make(tag, className, text) {
    var element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  }

  function renderCount() {
    var count = document.querySelector('[data-review-count]');
    if (count) count.textContent = 'Comments (' + (notes.length + submittedNotes.length) + ')';
  }

  function renderPins() {
    document.querySelectorAll('[data-review-pin]').forEach(function (pin) { pin.remove(); });
    notes.concat(submittedNotes).forEach(function (note, index) {
      if (!note.selector || !note.pageUrl) return;
      var noteUrl;
      try { noteUrl = new URL(note.pageUrl, window.location.href); } catch (_) { return; }
      if (noteUrl.pathname !== window.location.pathname) return;
      var target;
      try { target = document.querySelector(note.selector); } catch (_) { return; }
      if (!target || target.closest('.review-bar, .review-notice, .review-modal-backdrop')) return;
      var rect = target.getBoundingClientRect();
      var pin = make('button', 'review-pin', String(index + 1));
      pin.type = 'button';
      pin.setAttribute('data-review-pin', '');
      pin.setAttribute('aria-label', 'Open comment: ' + (note.comment || 'Website comment'));
      pin.style.left = Math.max(4, Math.round(rect.left + window.scrollX - 12)) + 'px';
      pin.style.top = Math.max(4, Math.round(rect.top + window.scrollY - 12)) + 'px';
      pin.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        openFeedbackList();
      });
      document.body.appendChild(pin);
    });
  }

  function noteCard(note, isDraft) {
    var card = make('article', 'review-comment-card');
    var meta = make('div', 'review-comment-meta');
    meta.appendChild(make('span', 'review-comment-status ' + (isDraft ? 'is-draft' : 'is-submitted'), isDraft ? 'Draft' : 'Submitted'));
    var date = note.createdAt ? new Date(note.createdAt) : null;
    if (date && !isNaN(date.getTime())) meta.appendChild(make('time', '', date.toLocaleString()));
    var target = make('p', 'review-comment-target', note.selectedText || note.title || note.element || 'Website element');
    var comment = make('p', 'review-comment-text', note.comment || 'No comment supplied.');
    card.append(meta, target, comment);
    if (note.pageUrl) {
      var page = make('a', 'review-comment-link', 'Open page');
      page.href = note.pageUrl;
      card.appendChild(page);
    }
    if (note.url) {
      var issue = make('a', 'review-comment-link', 'View issue #' + note.number);
      issue.href = note.url;
      issue.target = '_blank';
      issue.rel = 'noopener';
      card.appendChild(issue);
    }
    if (isDraft) {
      var remove = make('button', 'review-comment-remove', 'Delete draft');
      remove.type = 'button';
      remove.addEventListener('click', function () {
        notes = notes.filter(function (item) { return item.id !== note.id; });
        persist();
        renderCount();
        renderPins();
        card.remove();
        var draftList = document.querySelector('[data-review-drafts]');
        if (draftList && !notes.length) draftList.innerHTML = '<p class="review-empty">No unsent drafts.</p>';
      });
      card.appendChild(remove);
    }
    return card;
  }

  function openFeedbackList() {
    closeModal();
    modal = make('div', 'review-modal-backdrop');
    var panel = make('section', 'review-modal review-comments-modal');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    var close = make('button', 'review-modal-close', '×');
    close.type = 'button';
    close.setAttribute('aria-label', 'Close comments');
    close.addEventListener('click', closeModal);
    panel.append(close, make('h2', '', 'Website comments'));
    panel.appendChild(make('p', 'review-comments-intro', 'Drafts stay in this browser. Submitted comments are shared and remain visible here.'));

    var draftsTitle = make('h3', '', 'Drafts (' + notes.length + ')');
    var drafts = make('div', 'review-comment-list');
    drafts.setAttribute('data-review-drafts', '');
    if (notes.length) notes.forEach(function (note) { drafts.appendChild(noteCard(note, true)); });
    else drafts.appendChild(make('p', 'review-empty', 'No unsent drafts.'));

    var submittedTitle = make('h3', '', 'Submitted (' + submittedNotes.length + ')');
    var submitted = make('div', 'review-comment-list');
    if (submittedNotes.length) submittedNotes.forEach(function (note) { submitted.appendChild(noteCard(note, false)); });
    else submitted.appendChild(make('p', 'review-empty', 'No submitted comments yet.'));
    panel.append(draftsTitle, drafts, submittedTitle, submitted);
    modal.appendChild(panel);
    modal.addEventListener('click', function (event) { if (event.target === modal) closeModal(); });
    document.body.appendChild(modal);
  }

  function loadSubmittedFeedback() {
    if (!endpoint) return Promise.resolve();
    return fetch(endpoint, { headers: { Accept: 'application/json' } })
      .then(function (response) {
        return response.json().catch(function () { return {}; }).then(function (body) {
          if (!response.ok) throw new Error(body.error || 'Unable to load submitted comments.');
          return body;
        });
      })
      .then(function (body) {
        submittedNotes = Array.isArray(body.issues) ? body.issues : [];
        renderCount();
        renderPins();
      })
      .catch(function () {
        submittedNotes = [];
        renderCount();
      });
  }

  function closeModal() {
    if (modal) modal.remove();
    modal = null;
    selectedElement = null;
  }

  function openNoteForm(element) {
    selectedElement = element;
    selecting = false;
    document.body.classList.remove('review-selecting');
    document.querySelectorAll('.review-target').forEach(function (item) { item.classList.remove('review-target'); });

    modal = make('div', 'review-modal-backdrop');
    var panel = make('section', 'review-modal');
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'true');
    var close = make('button', 'review-modal-close', '×');
    close.type = 'button';
    close.setAttribute('aria-label', 'Close comment form');
    close.addEventListener('click', closeModal);
    var title = make('h2', '', 'Add comment');
    var detail = make('p', 'review-modal-target', selectedSummary(element));
    var label = make('label', '', 'What would you like us to know?');
    var input = document.createElement('textarea');
    input.required = true;
    input.placeholder = 'Write your comment here.';
    label.appendChild(input);
    var actions = make('div', 'review-modal-actions');
    var cancel = make('button', 'review-button review-button-secondary', 'Cancel');
    cancel.type = 'button';
    cancel.addEventListener('click', closeModal);
    var save = make('button', 'review-button', 'Save comment');
    save.type = 'button';
    save.addEventListener('click', function () {
      var message = input.value.trim();
      if (!message) { input.focus(); return; }
      var rect = element.getBoundingClientRect();
      notes.push({
        id: String(Date.now()),
        pageUrl: window.location.href,
        pageTitle: document.title,
        selector: selectorFor(element),
        element: element.tagName.toLowerCase(),
        selectedText: selectedSummary(element),
        imageSrc: element.tagName === 'IMG' ? element.currentSrc || element.src || '' : '',
        viewport: { width: window.innerWidth, height: window.innerHeight },
        position: { x: Math.round(rect.left + window.scrollX), y: Math.round(rect.top + window.scrollY) },
        comment: message,
        createdAt: new Date().toISOString()
      });
      persist();
      renderCount();
      renderPins();
      closeModal();
    });
    actions.append(cancel, save);
    panel.append(close, title, detail, label, actions);
    modal.appendChild(panel);
    modal.addEventListener('click', function (event) { if (event.target === modal) closeModal(); });
    document.body.appendChild(modal);
    input.focus();
  }

  function toggleSelection() {
    selecting = !selecting;
    document.body.classList.toggle('review-selecting', selecting);
    var message = document.querySelector('[data-review-status]');
    if (message) message.textContent = selecting ? 'Click anything on the page to leave feedback. Press Escape to cancel.' : '';
  }

  function submitFeedback() {
    if (!notes.length) return;
    if (!endpoint) {
      window.alert('Your comments are saved in this browser, but the shared review inbox is not connected yet.');
      return;
    }
    var send = document.querySelector('[data-review-send]');
    if (send) { send.disabled = true; send.textContent = 'Submitting comments…'; }
    fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes: notes, reviewer: config.reviewer || 'Preview reviewer' })
    }).then(function (response) {
      return response.json().catch(function () { return {}; }).then(function (body) {
        if (!response.ok) throw new Error(body.detail || body.error || 'Unable to send feedback.');
        return body;
      });
    }).then(function (body) {
      notes = [];
      persist();
      renderCount();
      return loadSubmittedFeedback().then(function () {
        window.alert('Comments submitted. They are now saved in the shared review list.');
        openFeedbackList();
      });
    }).catch(function (error) {
      window.alert(error.message || 'Unable to send feedback. Please try again.');
    }).finally(function () {
      if (send) { send.disabled = false; send.textContent = 'Submit comments'; }
    });
  }

  function createOverlay() {
    var notice = make('aside', 'review-notice');
    notice.setAttribute('aria-label', 'Preview notice');
    notice.innerHTML = '<strong>Review mode</strong><span>Click anything to leave a comment. Comments are collected for the site owner and do not change the website automatically.</span>';
    var bar = make('aside', 'review-bar');
    bar.setAttribute('aria-label', 'Website review');
    var badge = make('span', 'review-badge', 'Preview');
    var add = make('button', 'review-button', 'Add comment');
    add.type = 'button';
    add.addEventListener('click', toggleSelection);
    var count = make('button', 'review-button review-button-secondary', 'Comments (' + (notes.length + submittedNotes.length) + ')');
    count.type = 'button';
    count.setAttribute('data-review-count', '');
    count.addEventListener('click', openFeedbackList);
    var send = make('button', 'review-button review-button-send', 'Submit comments');
    send.type = 'button';
    send.setAttribute('data-review-send', '');
    send.addEventListener('click', submitFeedback);
    var status = make('p', 'review-status');
    status.setAttribute('data-review-status', '');
    bar.append(badge, add, count, send, status);
    document.body.append(notice, bar);
    loadSubmittedFeedback();
    renderPins();
  }

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      if (modal) closeModal();
      if (selecting) toggleSelection();
    }
  });

  document.addEventListener('pointerover', function (event) {
    if (!selecting) return;
    if (event.target.closest('.review-pin')) return;
    var target = event.target.closest('body *:not(.review-notice):not(.review-bar):not(.review-modal-backdrop)');
    if (!target || target === hoverTarget) return;
    if (hoverTarget) hoverTarget.classList.remove('review-target');
    hoverTarget = target;
    hoverTarget.classList.add('review-target');
  });

  document.addEventListener('click', function (event) {
    if (!selecting) return;
    if (event.target.closest('.review-pin')) return;
    var target = event.target.closest('body *:not(.review-notice):not(.review-bar):not(.review-modal-backdrop)');
    if (!target || target.closest('.review-bar, .review-notice, .review-modal-backdrop')) return;
    event.preventDefault();
    event.stopPropagation();
    openNoteForm(target);
  }, true);

  document.addEventListener('DOMContentLoaded', createOverlay);
}());
