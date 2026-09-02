// Docs page behaviour: mobile sidebar accordion + legacy anchor rescue
// + Pagefind search.

// The GitHub wiki generated anchors with a leading hyphen (#-swap-ops)
// because those headings began with an inline icon image. Links of that
// shape are still out in the wild — in older toolkit builds and in other
// people's posts — so accept them and land on the real heading.
(function () {
  function rescue() {
    var hash = decodeURIComponent(location.hash || '');
    if (!hash || hash.length < 3 || hash.charAt(1) !== '-') return;
    if (document.getElementById(hash.slice(1))) return;
    var el = document.getElementById(hash.slice(2));
    if (el) el.scrollIntoView();
  }
  rescue();
  window.addEventListener('hashchange', rescue);
})();

// Pagefind ships with the generated bundle; if the search index has not
// been built yet the import fails and the page is simply search-less.
(function () {
  var mount = document.getElementById('search');
  if (!mount || !window.PagefindUI) return;
  new window.PagefindUI({
    element: '#search',
    baseUrl: '/',
    showSubResults: true,
    showImages: false,
    resetStyles: false,
    translations: { placeholder: 'Search the docs' },
  });
})();

// The sidebar groups ship as <details open>: with no JavaScript a reader
// gets the full list, which is what desktop wants and is no worse than
// what mobile had. Here we close them below the layout breakpoint, where
// 53 expanded packages pushed the first line of every page off the third
// screen -- tapping a tool landed you back on the menu.
//
// ALL of them close, the current one included: the crumb and the <h1> two
// rows below already say where you are, and leaving that group open put
// its category (5 to 11 packages) back between the reader and the article.
// Re-opened on the way back to desktop, because a collapsed group there
// has no affordance to open it (the summary is styled as a plain heading
// and the chevron is mobile-only).
(function () {
  var side = document.getElementById('docs-side');
  if (!side) return;
  var groups = [].slice.call(side.querySelectorAll('.side-group'));
  if (!groups.length) return;

  var mq = window.matchMedia('(max-width: 900px)');
  var touched = false;   // once a reader opens or closes one, stop steering

  function apply(narrow) {
    if (touched) return;
    groups.forEach(function (g) {
      g.open = !narrow;
    });
  }

  side.addEventListener('toggle', function (e) {
    if (e.target.classList.contains('side-group')) touched = true;
  }, true);

  apply(mq.matches);
  var onChange = function (e) { apply(e.matches); };
  if (mq.addEventListener) mq.addEventListener('change', onChange);
  else if (mq.addListener) mq.addListener(onChange);
})();
