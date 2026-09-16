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
