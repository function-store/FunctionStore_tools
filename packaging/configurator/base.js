/* FNSTools UI base script -- the ONE source for behaviour every shell
   shares. Inlined between FNS:UIBASEJS markers by sync_base.py, exactly
   like base.css: edit HERE, then run

       python packaging/configurator/sync_base.py --write

   Tooltips. TouchDesigner's Web Render (CEF) never draws a native `title`
   tooltip, so every hover text in the family rides `data-tip` and this one
   element draws it: a short delay, it follows the cursor, stays inside the
   viewport, and pre-line keeps a multi-line tip's breaks (a card's tip is
   its full description plus "Adds: ..."). Set text with
   el.setAttribute('data-tip', text) or window.fnsTip(el, text); never
   `title`. Inside an open modal <dialog> the element is moved into that
   dialog, because the top layer covers everything appended to body. */
(function () {
  if (window.fnsTip) return;
  var tip = null, cur = null, timer = 0, lastX = 0, lastY = 0, lastPress = 0;
  var DELAY = 350, GAP = 14, EDGE = 8;
  function tipEl(host) {
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'fns-tip';
      tip.setAttribute('role', 'tooltip');
      tip.hidden = true;
    }
    host = host || document.body;
    if (tip.parentNode !== host) host.appendChild(tip);
    return tip;
  }
  function place(x, y) {
    if (!tip || tip.hidden) return;
    var w = tip.offsetWidth, h = tip.offsetHeight;
    var vw = window.innerWidth, vh = window.innerHeight;
    var left = x + GAP, top = y + GAP;
    if (left + w > vw - EDGE) left = Math.max(EDGE, x - GAP - w);
    if (top + h > vh - EDGE) top = Math.max(EDGE, y - GAP - h);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function show(target, x, y) {
    var text = target.getAttribute('data-tip');
    if (!text) return;
    var host = target.closest('dialog[open]') || document.body;
    var t = tipEl(host);
    t.textContent = text;
    t.hidden = false;
    place(x, y);
  }
  function hide() {
    clearTimeout(timer); timer = 0; cur = null;
    if (tip) tip.hidden = true;
  }
  function tipTarget(e) {
    var n = e.target;
    return n && n.closest ? n.closest('[data-tip]') : null;
  }
  document.addEventListener('mouseover', function (e) {
    var target = tipTarget(e);
    if (target === cur) return;
    hide();
    if (!target) return;
    cur = target;
    lastX = e.clientX; lastY = e.clientY;
    timer = setTimeout(function () {
      if (cur === target) show(target, lastX, lastY);
    }, DELAY);
  });
  document.addEventListener('mousemove', function (e) {
    lastX = e.clientX; lastY = e.clientY;
    if (cur) place(lastX, lastY);
  });
  // keyboard focus shows the tip at the element; a click's focus does not
  document.addEventListener('mousedown', function () { lastPress = Date.now(); hide(); });
  document.addEventListener('focusin', function (e) {
    var target = tipTarget(e);
    if (!target || Date.now() - lastPress < 500) return;
    hide();
    cur = target;
    var r = target.getBoundingClientRect();
    show(target, r.left, r.bottom);
  });
  document.addEventListener('focusout', hide);
  document.addEventListener('keydown', hide);
  document.addEventListener('scroll', hide, true);
  document.documentElement.addEventListener('mouseleave', hide);
  window.addEventListener('blur', hide);
  window.fnsTip = function (node, text) {
    if (text) node.setAttribute('data-tip', text);
    else node.removeAttribute('data-tip');
    return node;
  };
})();

/* Tools by other creators (docs/CommunityHighlights.md): the card and its
   actions, shared by the console's Community view and anything else that
   lists them. window.fnsCommunity.card(row, {served}) builds one card;
   .load({url, served}, cb) fetches the list. A card is never selectable:
   nothing here enters an install plan. Served inside TouchDesigner, a
   pinned tox gets Place and a locked Python package gets Install, both
   answered through the installer's /community/* routes; links open in the
   system browser through /open (a Web Render ignores target=_blank). */
(function () {
  if (window.fnsCommunity) return;
  var SITE = 'https://functionstore.tools';
  var PLATFORM = {github: 'on GitHub', patreon: 'on Patreon', gumroad: 'on Gumroad',
                  itch: 'on itch.io', pypi: 'on PyPI'};

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function pinned(r) { return !!(r && r.tox_url && /^[0-9a-f]{64}$/.test(String(r.sha256 || ''))); }
  function locked(r) { return !!(r && r.tdp && r.tdp.package && Array.isArray(r.tdp.lock) && r.tdp.lock.length); }
  function postUrl(r) { return r.slug ? SITE + '/community/' + encodeURIComponent(r.slug) + '/' : ''; }
  function json(url, body) {
    var o = body === undefined ? {cache: 'no-store'}
      : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)};
    return fetch(url, o).then(function (x) { return x.json(); });
  }

  function link(href, text, cls, served) {
    var a = el('a', cls || 'chip rec', text);
    a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer';
    if (served) {
      a.addEventListener('click', function (e) {
        e.preventDefault(); e.stopPropagation();
        json('/open', {url: href}).catch(function () {});
      });
    }
    return a;
  }

  function failed(btn, e, text) {
    btn.disabled = false;
    btn.textContent = text;
    btn.setAttribute('data-tip', String(e && e.message || e));
  }

  /** Follow the updater's answer for this tool until placed or failed. */
  function follow(r, btn, maxTries, doneText) {
    var tries = 0;
    (function poll() {
      tries++;
      json('/community/place').then(function (st) {
        if (st.name === r.name && st.state === 'placed') {
          btn.textContent = doneText;
          btn.setAttribute('data-tip', 'Placed at ' + st.placed + '. Yours to keep: FNSTools never updates it.'
            + (st.note ? ' ' + st.note : ''));
          btn.disabled = false;
        } else if (st.name === r.name && (st.state === 'failed' || st.state === 'noenv')) {
          throw new Error(st.why);
        } else if (tries < maxTries) {
          setTimeout(poll, 1000);
        } else {
          throw new Error('no answer yet; check the Textport');
        }
      }).catch(function (e) { failed(btn, e, 'failed · retry'); });
    })();
  }

  function place(r, btn) {
    btn.disabled = true;
    btn.textContent = 'placing…';
    json('/community/place', {name: r.name}).then(function (a) {
      if (!a.ok) throw new Error(a.why || 'could not place it');
      follow(r, btn, 90, 'placed ✓');
    }).catch(function (e) { failed(btn, e, 'place failed · retry'); });
  }

  function install(r, btn) {
    btn.disabled = true;
    btn.textContent = 'installing…';
    json('/community/install', {name: r.name}).then(function (a) {
      if (a.noenv) return offerEnv(btn, a.env || {});
      if (!a.ok) throw new Error(a.why || 'could not install it');
      follow(r, btn, 600, 'installed and placed ✓');
    }).catch(function (e) { failed(btn, e, 'install failed · retry'); });
  }

  /** No Python environment: offer TouchDesigner's own manager, which shows
   *  Derivative's disclaimer before it creates one. */
  function offerEnv(btn, env) {
    btn.disabled = false;
    if (env.state === 'creating') {
      btn.textContent = 'Python environment is being set up · try again';
      btn.setAttribute('data-tip', env.status || 'TouchDesigner is creating the environment.');
      return;
    }
    btn.textContent = 'set up a Python environment first';
    btn.setAttribute('data-tip', 'This project has no Python environment for packages yet. This opens '
      + "TouchDesigner's own environment manager, which asks for your OK (Derivative's disclaimer) "
      + 'and creates .venv beside your project. Then press Install again.');
    btn.onclick = function (e) {
      e.preventDefault(); e.stopPropagation();
      btn.onclick = null;
      btn.disabled = true;
      btn.textContent = 'answer the dialog in TouchDesigner…';
      json('/community/pyenv', {}).catch(function () {});
      var tries = 0;
      (function poll() {
        tries++;
        json('/community/pyenv').then(function (st) {
          if (st.state === 'ready') {
            btn.disabled = false;
            btn.textContent = 'environment ready · install';
            btn.setAttribute('data-tip', 'Python environment at ' + st.env);
          } else if (st.state === 'error') {
            failed(btn, new Error(st.status || 'the environment could not be created'), 'environment failed');
          } else if (tries < 240) {
            setTimeout(poll, 1500);
          } else {
            failed(btn, new Error('no environment yet'), 'no environment · retry');
          }
        }).catch(function (e) { failed(btn, e, 'environment failed'); });
      })();
    };
  }

  function actionButton(text, tip, run) {
    var b = el('button', 'chip placebtn', text);
    b.type = 'button';
    b.setAttribute('data-tip', tip);
    b.addEventListener('click', function (e) {
      e.preventDefault(); e.stopPropagation();
      if (!b.disabled && !b.onclick) run(b);
    });
    return b;
  }

  /** One card. The author is named on it: we are pointing, not shipping. */
  function card(r, opts) {
    var served = !!(opts && opts.served);
    var c = el('div', 'card rec');
    var body = el('div', 'body');
    var n = el('div', 'name');
    var post = postUrl(r);
    if (post) n.appendChild(link(post, r.name, 'post', served));
    else n.textContent = r.name;
    body.appendChild(n);
    if (r.author) body.appendChild(el('div', 'rec-by', 'by ' + r.author));
    if (r.description) body.appendChild(el('div', 'desc', r.description));
    var chips = el('div', 'chips');
    if (post) chips.appendChild(link(post, 'our write-up ↗', null, served));
    chips.appendChild(link(r.url, (PLATFORM[r.platform] || 'their site') + ' ↗', null, served));
    if (served && pinned(r)) {
      chips.appendChild(actionButton('place in this project',
        'Downloads the exact file we checked into the network you are working in. '
        + 'If the author has changed it since, nothing is placed. FNSTools never updates it.',
        function (b) { place(r, b); }));
    }
    if (locked(r)) {
      if (served) {
        chips.appendChild(actionButton('install in this project',
          'A Python package (' + r.tdp.package + '). Installs the exact versions we checked into this '
          + "project's Python environment, then places the tool in the network you are working in. "
          + 'FNSTools never updates it.',
          function (b) { install(r, b); }));
      } else {
        chips.appendChild(el('span', 'chip rec', 'Python package'));
      }
    }
    body.appendChild(chips);
    c.appendChild(body);
    return c;
  }

  /** Fetch the list: {intro, tools}. Served, the installer answers `retry`
   *  while its store copy is being refreshed. Rows without a name or an
   *  https link are dropped, whatever the file says. */
  function load(opts, cb) {
    var tries = 0;
    (function ask() {
      tries++;
      fetch(opts.url, {cache: 'no-store'})
        .then(function (x) { return x.ok ? x.json() : null; })
        .then(function (doc) {
          if (!doc) return cb(null);
          if (opts.served && doc.retry && tries < 8) setTimeout(ask, 3000);
          var tools = (Array.isArray(doc.tools) ? doc.tools : []).filter(function (t) {
            return t && t.name && String(t.url || '').indexOf('https://') === 0;
          });
          cb({intro: String(doc.intro || ''), tools: tools});
        })
        .catch(function () { cb(null); });
    })();
  }

  window.fnsCommunity = {card: card, load: load, pinned: pinned, locked: locked, SITE: SITE};
})();
