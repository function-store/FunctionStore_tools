// Docs page behaviour: legacy anchor rescue + Pagefind search.

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
