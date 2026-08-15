// Mobile menu toggle for the shared site header.
//
// Merged from the two sibling sites, which had drifted apart: the
// delegated click handler and getElementById lookup come from launcher,
// the aria-label flip and the close-on-resize guard from tdmap. Without
// the resize guard the drawer stays "open" in the DOM when the viewport
// grows past the breakpoint, which leaves body scroll locked.
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (!toggle || !nav) return;

  var backdrop = document.createElement('div');
  backdrop.className = 'nav-backdrop';
  backdrop.setAttribute('aria-hidden', 'true');
  document.body.appendChild(backdrop);

  function setOpen(open) {
    toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    nav.classList.toggle('is-open', open);
    backdrop.classList.toggle('is-open', open);
    document.body.classList.toggle('site-nav-open', open);
  }

  toggle.addEventListener('click', function () {
    setOpen(toggle.getAttribute('aria-expanded') !== 'true');
  });
  backdrop.addEventListener('click', function () { setOpen(false); });
  nav.addEventListener('click', function (e) {
    if (e.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setOpen(false);
  });

  var mq = window.matchMedia('(min-width: 901px)');
  function onWide(e) { if (e.matches) setOpen(false); }
  if (mq.addEventListener) mq.addEventListener('change', onWide);
  else if (mq.addListener) mq.addListener(onWide);
})();
