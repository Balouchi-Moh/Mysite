document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.querySelector('.nav-toggle');
  var links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', function () {
      links.classList.toggle('open');
    });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () { links.classList.remove('open'); });
    });
  }

  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && els.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { threshold: 0.12 });
    els.forEach(function (el) { io.observe(el); });
  } else {
    els.forEach(function (el) { el.classList.add('in'); });
  }

  renderProjects();
  renderPosts();
});

var POST_ICONS = {
  lean: '<svg viewBox="0 0 24 24"><path d="M3 17l4-5 4 3 6-8" stroke-linecap="round" stroke-linejoin="round"/><path d="M13 7h4v4" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 21h18" stroke-linecap="round"/></svg>',
  pm: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="17" rx="1.5"/><path d="M3 9h18M8 2v4M16 2v4" stroke-linecap="round"/><path d="M6.5 13h5M6.5 16.5h8" stroke-linecap="round"/></svg>',
  km: '<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2.3"/><circle cx="18" cy="6" r="2.3"/><circle cx="12" cy="18" r="2.3"/><path d="M7.8 7.3L10.5 16M16.2 7.3L13.5 16M8.3 6h7.4" stroke-linecap="round"/></svg>',
  risk: '<svg viewBox="0 0 24 24"><path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" stroke-linejoin="round"/><path d="M9 12l2 2 4-4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  training: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="12" rx="1"/><path d="M8 20h8M12 16v4" stroke-linecap="round"/><path d="M7 10l3 2 4-4 3 2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  expert: '<svg viewBox="0 0 24 24"><path d="M12 3v18M7 7h10M4 8l3-1 3 1-3 6-3-6zM14 8l3-1 3 1-3 6-3-6z" stroke-linecap="round" stroke-linejoin="round"/><path d="M4 14a3 3 0 006 0M14 14a3 3 0 006 0" stroke-linecap="round"/><path d="M8 21h8" stroke-linecap="round"/></svg>',
  generic: '<svg viewBox="0 0 24 24"><path d="M3 21h18M5 21V9l7-5 7 5v12M9 21v-6h6v6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
};

/**
 * Renders blog post cards from data/posts.json.
 * To add/edit/reorder posts, only edit data/posts.json — never this function.
 *
 * Requires a container: <div id="posts-grid" class="grid-3"></div>
 * Optional: add data-limit="3" on the container to cap how many posts show
 * (used on the homepage preview; omit/leave unset to show all, used on
 * the blog listing page).
 * Uses the same window.SITE_ROOT / window.SITE_LANG page config as renderProjects().
 */
function renderPosts() {
  var container = document.getElementById('posts-grid');
  if (!container) return;
  var root = window.SITE_ROOT || '';
  var lang = window.SITE_LANG || 'fa';
  var limit = parseInt(container.getAttribute('data-limit'), 10) || null;
  var moreLabel = lang === 'en' ? 'Read more →' : 'ادامه مطلب ←';

  fetch(root + 'data/posts.json')
    .then(function (res) { return res.json(); })
    .then(function (data) {
      var posts = data.posts || [];
      if (limit) posts = posts.slice(0, limit);
      container.innerHTML = posts.map(function (p) {
        var title = lang === 'en' ? p.title_en : p.title_fa;
        var excerpt = lang === 'en' ? p.excerpt_en : p.excerpt_fa;
        var tag = lang === 'en' ? p.tag_en : p.tag_fa;
        var link = lang === 'en' ? p.link_en : p.link_fa;
        var icon = POST_ICONS[p.icon] || POST_ICONS.generic;
        var isSoon = p.status !== 'published' || !link;
        return (
          '<div class="post-card' + (isSoon ? ' soon' : '') + '">' +
            '<div class="post-thumb">' + icon + '</div>' +
            '<div class="post-body">' +
              '<div class="post-meta">' + tag + '</div>' +
              '<h3>' + title + '</h3>' +
              '<p>' + excerpt + '</p>' +
              (isSoon ? '' : '<a class="more" href="' + root + link + '">' + moreLabel + '</a>') +
            '</div>' +
          '</div>'
        );
      }).join('');
    })
    .catch(function (err) {
      console.error('Could not load posts.json', err);
    });
}

/**
 * Renders the "Notable Projects" grid from data/projects.json.
 * To add/edit/remove a project, only edit data/projects.json — this
 * function and the HTML markup never need to change.
 *
 * Requires a container: <div id="projects-grid" class="grid-3"></div>
 * Page-level config (set BEFORE main.js is loaded):
 *   window.SITE_ROOT = "" for pages at the site root (index.html)
 *   window.SITE_ROOT = "../" for pages one level deep (en/index.html)
 *   window.SITE_LANG = "fa" or "en"
 */
function renderProjects() {
  var container = document.getElementById('projects-grid');
  if (!container) return;
  var root = window.SITE_ROOT || '';
  var lang = window.SITE_LANG || 'fa';

  fetch(root + 'data/projects.json')
    .then(function (res) { return res.json(); })
    .then(function (data) {
      var projects = data.projects || [];
      container.innerHTML = projects.map(function (p) {
        var title = lang === 'en' ? p.title_en : p.title_fa;
        return (
          '<div class="card" style="padding:0;overflow:hidden;">' +
            '<div class="post-thumb" style="height:190px;">' +
              '<img src="' + root + p.image + '" alt="' + title + '" ' +
                'style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;">' +
            '</div>' +
            '<div style="padding:16px 20px;">' +
              '<h3 style="font-size:15.5px;margin:0;font-weight:600;">' + title + '</h3>' +
            '</div>' +
          '</div>'
        );
      }).join('');
    })
    .catch(function (err) {
      console.error('Could not load projects.json', err);
    });
}
