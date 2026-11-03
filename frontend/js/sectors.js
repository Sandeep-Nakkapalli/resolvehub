(function () {
  const { apiFetch, escapeHtml, showToast } = window.ResolveHub || {};
  let sectors = [];

  function iconRefresh() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } }); }

  function render(items) {
    const grid = document.getElementById('all-sector-grid');
    if (!items.length) { grid.innerHTML = '<div class="empty-state">No sectors match that search.</div>'; return; }
    grid.innerHTML = items.map((sector, index) => `<article class="sector-card visible" data-sector-id="${sector.id}"><div class="sector-top"><span class="sector-icon"><i data-lucide="${escapeHtml(sector.icon || 'layers')}"></i></span><span class="sector-index">${String(index + 1).padStart(2, '0')}</span></div><h3>${escapeHtml(sector.name)}</h3><p>${escapeHtml(sector.description)}</p><div class="sector-footer"><span class="category-count"><strong>${sector.category_count}</strong> categories</span><a href="#category-detail" data-open-sector="${sector.id}">View categories <i data-lucide="arrow-down"></i></a></div></article>`).join('');
    grid.querySelectorAll('[data-open-sector]').forEach((link) => link.addEventListener('click', () => openDetails(Number(link.dataset.openSector))));
    iconRefresh();
  }

  function openDetails(id) {
    const sector = sectors.find((item) => item.id === id);
    if (!sector) return;
    document.getElementById('detail-title').textContent = sector.name;
    document.getElementById('detail-description').textContent = sector.description;
    document.getElementById('category-list').innerHTML = (sector.categories || []).map((category) => `<div class="category-item"><i>✓</i><span>${escapeHtml(category.name)}</span></div>`).join('');
    const detail = document.getElementById('category-detail'); detail.classList.add('open'); detail.scrollIntoView({ behavior: 'smooth', block: 'center' }); iconRefresh();
  }

  function filter() {
    const query = document.getElementById('sector-search').value.toLowerCase();
    const selected = document.getElementById('sector-filter').value;
    render(sectors.filter((sector) => (!selected || String(sector.id) === selected) && (!query || `${sector.name} ${sector.description} ${(sector.categories || []).map((item) => item.name).join(' ')}`.toLowerCase().includes(query))));
  }

  async function init() {
    try {
      const base = await apiFetch('/api/sectors/');
      sectors = await Promise.all(base.map(async (sector) => ({ ...sector, categories: (await apiFetch(`/api/sectors/${sector.id}/categories/`)).categories })));
      const selector = document.getElementById('sector-filter'); selector.innerHTML += sectors.map((sector) => `<option value="${sector.id}">${escapeHtml(sector.name)}</option>`).join('');
      render(sectors);
      const preselected = new URLSearchParams(window.location.search).get('sector'); if (preselected) openDetails(Number(preselected));
    } catch { document.getElementById('all-sector-grid').innerHTML = '<div class="empty-state">Connect the database and run seed_demo to view sectors.</div>'; showToast('Unable to load sectors right now.', 'error'); }
    document.getElementById('sector-search').addEventListener('input', filter); document.getElementById('sector-filter').addEventListener('change', filter); document.getElementById('close-detail').addEventListener('click', () => document.getElementById('category-detail').classList.remove('open'));
  }
  document.addEventListener('DOMContentLoaded', init);
})();
