(function () {
  const { apiFetch, escapeHtml, showToast } = window.ResolveHub || {};

  function initIcons() {
    if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } });
  }

  function setupNavigation() {
    const header = document.getElementById('site-header');
    const shell = document.querySelector('.nav-shell');
    const menuButton = document.querySelector('.mobile-menu-button');
    window.addEventListener('scroll', () => header?.classList.toggle('scrolled', window.scrollY > 12), { passive: true });
    menuButton?.addEventListener('click', () => {
      const open = shell.classList.toggle('menu-open');
      menuButton.setAttribute('aria-expanded', String(open));
    });
    document.querySelectorAll('.nav-links a').forEach((link) => link.addEventListener('click', () => shell?.classList.remove('menu-open')));
  }

  function setupReveals() {
    const items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { items.forEach((item) => item.classList.add('visible')); return; }
    const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); }
    }), { threshold: .08 });
    items.forEach((item) => observer.observe(item));
  }

  function renderStats(stats) {
    document.querySelectorAll('[data-stat="supported_sectors"]').forEach((node) => node.textContent = String(stats.supported_sectors ?? '—').padStart(2, '0'));
    document.querySelectorAll('[data-stat="complaint_categories"]').forEach((node) => node.textContent = String(stats.complaint_categories ?? '—').padStart(2, '0'));
  }

  function renderSectors(sectors) {
    const grid = document.getElementById('sector-grid');
    if (!grid) return;
    if (!sectors.length) { grid.innerHTML = '<div class="loading-state">Sectors will appear once the ResolveHub database is seeded.</div>'; return; }
    grid.innerHTML = sectors.map((sector, index) => {
      const color = { cyan: '#35E0FF', pink: '#FF4FD8', green: '#39E6A5', purple: '#A855F7' }[sector.accent] || '#A855F7';
      return `<article class="sector-card reveal visible" style="--accent:${color};--accent-color:${color}">
        <div class="sector-top"><span class="sector-icon"><i data-lucide="${escapeHtml(sector.icon || 'layers')}"></i></span><span class="sector-index">0${index + 1}</span></div>
        <h3>${escapeHtml(sector.name)}</h3><p>${escapeHtml(sector.description)}</p>
        <div class="sector-footer"><span class="category-count"><strong>${escapeHtml(sector.category_count)}</strong> categories</span><a href="/sectors.html?sector=${sector.id}">View categories <i data-lucide="arrow-up-right"></i></a></div>
      </article>`;
    }).join('');
    initIcons();
  }

  async function loadLandingData() {
    if (!apiFetch) return;
    const [sectorResult, statResult] = await Promise.allSettled([apiFetch('/api/sectors/'), apiFetch('/api/public/stats/')]);
    if (sectorResult.status === 'fulfilled') renderSectors(sectorResult.value);
    else document.getElementById('sector-grid')?.replaceChildren(Object.assign(document.createElement('div'), { className: 'loading-state', textContent: 'Connect the database and run seed_demo to load sectors.' }));
    if (statResult.status === 'fulfilled') renderStats(statResult.value);
  }

  document.addEventListener('DOMContentLoaded', () => { initIcons(); setupNavigation(); setupReveals(); loadLandingData(); });
})();
