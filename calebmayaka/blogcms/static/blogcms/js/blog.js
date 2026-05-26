// Table of contents
(function () {
  var toc = document.getElementById('blog-toc');
  var content = document.querySelector('.blog-content');
  if (!toc || !content) return;

  var headings = content.querySelectorAll('h2, h3');
  if (headings.length < 3) { toc.remove(); return; }

  var list = document.createElement('ol');
  list.className = 'blog-toc-list';

  headings.forEach(function (h, i) {
    if (!h.id) {
      h.id = 'heading-' + i + '-' + h.textContent.trim()
        .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    }
    var li = document.createElement('li');
    li.className = h.tagName === 'H3' ? 'blog-toc-item blog-toc-item--sub' : 'blog-toc-item';
    var a = document.createElement('a');
    a.href = '#' + h.id;
    a.textContent = h.textContent;
    li.appendChild(a);
    list.appendChild(li);
  });

  var label = document.createElement('p');
  label.className = 'blog-toc-heading';
  label.textContent = 'On this page';
  toc.appendChild(label);
  toc.appendChild(list);

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var link = toc.querySelector('a[href="#' + e.target.id + '"]');
        if (link) link.classList.toggle('active', e.isIntersecting);
      });
    }, { rootMargin: '-10% 0px -80% 0px' });
    headings.forEach(function (h) { observer.observe(h); });
  }
})();

// Sync Giscus theme with site dark/light toggle
(function () {
  var root = document.documentElement;
  var prevTheme = root.classList.contains('light') ? 'light' : 'dark';

  var mo = new MutationObserver(function () {
    var theme = root.classList.contains('light') ? 'light' : 'dark';
    if (theme === prevTheme) return;
    prevTheme = theme;
    var frame = document.querySelector('.giscus-frame');
    if (frame) {
      frame.contentWindow.postMessage(
        { giscus: { setConfig: { theme: theme } } },
        'https://giscus.app'
      );
    }
  });
  mo.observe(root, { attributes: true, attributeFilter: ['class'] });
})();
