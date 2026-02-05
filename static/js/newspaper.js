/* Newspaper-like UI enhancements for hugo-theme-stack.
   - Adds click-to-open transition on list cards
   - Adds enter animation on article pages
   - Appends a consistent promo slogan at bottom of each article
*/

(function () {
  const PROMO_TEXT = '关注「AI智汇观察」，了解更多行业最新资讯';

  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn, { once: true });
    } else {
      fn();
    }
  }

  function isArticlePage() {
    return document.body && document.body.classList.contains('article-page');
  }

  function isListPage() {
    return document.querySelector('.article-list--compact, .article-list--tile, .article-list') != null;
  }

  function addEnterAnimation() {
    document.documentElement.classList.add('np-enter');
    // Let CSS transitions run.
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.documentElement.classList.add('np-enter-active');
      });
    });
    setTimeout(() => {
      document.documentElement.classList.remove('np-enter');
      document.documentElement.classList.remove('np-enter-active');
    }, 700);
  }

  function addPromoSlogan() {
    const content = document.querySelector('.article-content');
    if (!content) return;

    // Avoid duplicates (e.g., PJAX / theme scripts)
    if (content.querySelector('[data-np-promo="1"]')) return;

    const wrap = document.createElement('div');
    wrap.setAttribute('data-np-promo', '1');
    wrap.className = 'np-promo';
    wrap.innerHTML = `
      <div class="np-promo__rule"></div>
      <p class="np-promo__text">${PROMO_TEXT}</p>
    `;
    content.appendChild(wrap);
  }

  function setColorScheme(next) {
    // Stack theme uses localStorage key: StackColorScheme (auto|dark|light)
    try {
      localStorage.setItem('StackColorScheme', next);
    } catch (_) {}
    // Apply immediately (basic)
    if (next === 'dark') {
      document.documentElement.dataset.scheme = 'dark';
      document.documentElement.classList.add('np-lamp-on');
    } else if (next === 'light') {
      document.documentElement.dataset.scheme = 'light';
      document.documentElement.classList.remove('np-lamp-on');
    } else {
      // auto
      document.documentElement.dataset.scheme = '';
      document.documentElement.classList.remove('np-lamp-on');
    }
  }

  function currentScheme() {
    const d = document.documentElement && document.documentElement.dataset && document.documentElement.dataset.scheme;
    if (d === 'dark' || d === 'light') return d;
    // fallback to localStorage
    try {
      const v = localStorage.getItem('StackColorScheme');
      if (v === 'dark' || v === 'light') return v;
    } catch (_) {}
    // fallback to prefers
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function installLampToggle() {
    const holder = document.querySelector('#dark-mode-toggle');
    if (!holder) return;

    // Replace existing toggle UI with a vintage desk lamp + pull cord
    holder.innerHTML = `
      <div class="np-lamp" role="button" tabindex="0" aria-label="切换明暗模式">
        <div class="np-lamp__img" aria-hidden="true"></div>
        <div class="np-lamp__glow" aria-hidden="true"></div>
      </div>
    `;

    const lamp = holder.querySelector('.np-lamp');
    const toggle = () => {
      const cur = currentScheme();
      const next = cur === 'dark' ? 'light' : 'dark';
      setColorScheme(next);
      // Let Stack's own scripts re-init cleanly
      setTimeout(() => window.location.reload(), 120);
    };

    lamp.addEventListener('click', toggle);
    lamp.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggle();
      }
    });

    // set initial lamp state
    if (currentScheme() === 'dark') document.documentElement.classList.add('np-lamp-on');
  }

  function addBackPin() {
    if (!isArticlePage()) return;
    if (document.querySelector('[data-np-back="1"]')) return;

    const a = document.createElement('a');
    a.href = '/posts/';
    a.className = 'np-back-pin';
    a.setAttribute('data-np-back', '1');
    a.setAttribute('aria-label', '返回桌面');
    a.title = '返回桌面';
    a.innerHTML = '<span class="np-back-pin__head"></span><span class="np-back-pin__label">返回</span>';
    document.body.appendChild(a);
  }

  function wireCardOpenTransition() {
    const cards = document.querySelectorAll(
      'section.article-list--compact article > a, section.article-list--tile article > a, section.article-list article .article-title a'
    );
    if (!cards.length) return;

    cards.forEach((a) => {
      a.addEventListener('click', (e) => {
        // allow cmd/ctrl click, new tab, etc.
        if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        if (e.defaultPrevented) return;

        const href = a.getAttribute('href');
        if (!href || href.startsWith('#')) return;

        e.preventDefault();

        const article = a.closest('article');
        if (article) article.classList.add('np-opening');
        document.documentElement.classList.add('np-navigate');

        setTimeout(() => {
          window.location.href = href;
        }, 220);
      });
    });
  }

  onReady(() => {
    // Sidebar lamp toggle exists on most pages
    installLampToggle();

    if (isListPage()) {
      wireCardOpenTransition();
    }
    if (isArticlePage()) {
      addEnterAnimation();
      addPromoSlogan();
      addBackPin();
    }
  });
})();
