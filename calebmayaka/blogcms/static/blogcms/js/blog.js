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

// Article reading progress bar
(function () {
    var progressLine = document.querySelector('.progress-line');
    var article = document.querySelector('article.blog-article');
    if (!progressLine || !article) return;

    // Cached bounds — recalculated on resize so late-loading images don't skew results
    var articleTop = 0;
    var readableEnd = 0;
    var ticking = false;

    function recalcBounds() {
        // getBoundingClientRect is viewport-relative; add scrollY for document-absolute top
        articleTop = article.getBoundingClientRect().top + window.scrollY;
        // readableEnd: the scroll position at which the article bottom
        // reaches the bottom of the viewport (i.e. the reader has finished)
        readableEnd = articleTop + article.offsetHeight - window.innerHeight;
    }

    function updateProgress() {
        var scale = readableEnd > articleTop
            ? Math.max(0, Math.min(1, (window.scrollY - articleTop) / (readableEnd - articleTop)))
            : 0;
        progressLine.style.transform = 'scaleX(' + scale + ')';
        ticking = false;
    }

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(updateProgress);
            ticking = true;
        }
    }

    function onResize() {
        recalcBounds();
        updateProgress();
    }

    recalcBounds();
    updateProgress();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onResize, { passive: true });
})();

// Lazy-load Twitter/X widget only when tweet embeds are on the page
(function () {
    if (!document.querySelector('.blog-stream-tweet')) return;
    var s = document.createElement('script');
    s.src = 'https://platform.twitter.com/widgets.js';
    s.charset = 'utf-8';
    s.async = true;
    document.body.appendChild(s);
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
