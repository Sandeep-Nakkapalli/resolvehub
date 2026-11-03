(function () {
  const { apiFetch, showToast, saveUser, getSavedUser, redirectForRole, escapeHtml, formatDate } = window.ResolveHub || {};
  const role = document.body.dataset.dashboardRole;
  let rows = [];
  let currentComplaintId = null;

  function icons() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } }); }
  function setText(id, value) { const node = document.getElementById(id); if (node) node.textContent = value ?? '—'; }
  function statusClass(status) { return `status-${String(status || '').replaceAll('-', '_')}`; }

  function renderRows(items) {
    const body = document.getElementById('complaints-table');
    if (!body) return;
    if (!items.length) { body.innerHTML = `<tr><td colspan="7" class="empty-state">No complaints match these filters.</td></tr>`; return; }
    const organization = role === 'admin';
    body.innerHTML = items.map((item) => `<tr><td>${escapeHtml(item.public_id)}</td><td>${organization ? escapeHtml(item.sector_name) : escapeHtml(item.title)}</td><td>${organization ? escapeHtml(item.organization_name) : escapeHtml(item.category_name)}</td><td>${organization ? escapeHtml(item.category_name) : formatDate(item.created_at)}</td><td>${organization ? formatDate(item.created_at) : `<span class="status-badge ${statusClass(item.status)}">${escapeHtml(item.status_label)}</span>`}</td>${organization ? `<td><span class="status-badge ${statusClass(item.status)}">${escapeHtml(item.status_label)}</span></td>` : ''}<td><button class="row-action" data-view-complaint="${item.id}">View <i data-lucide="arrow-up-right"></i></button></td></tr>`).join('');
    body.querySelectorAll('[data-view-complaint]').forEach((button) => button.addEventListener('click', () => openDetail(button.dataset.viewComplaint)));
    icons();
  }

  function filterRows() {
    const query = (document.getElementById('complaint-search')?.value || '').toLowerCase();
    const status = document.getElementById('complaint-status-filter')?.value || '';
    renderRows(rows.filter((item) => (!status || item.status === status) && (!query || `${item.public_id} ${item.title} ${item.sector_name} ${item.organization_name} ${item.category_name}`.toLowerCase().includes(query))));
  }

  function renderUser(data) {
    const user = data.user;
    const firstName = (user.name || 'there').split(' ')[0];
    setText('welcome-title', `Good morning, ${firstName}.`); setText('sidebar-name', user.name); setText('sidebar-avatar', (user.name || 'U')[0].toUpperCase()); setText('top-avatar', (user.name || 'U')[0].toUpperCase());
    setText('count-total', data.counts.total); setText('count-pending', data.counts.pending); setText('count-progress', data.counts.in_progress); setText('count-resolved', data.counts.resolved); rows = data.recent || []; renderRows(rows); setText('nav-notification-count', data.notifications_unread || '');
  }

  function renderOrganization(data) {
    const user = getSavedUser(); setText('sidebar-name', user?.name || 'Representative'); setText('sidebar-avatar', (user?.name || 'O')[0].toUpperCase()); setText('top-avatar', (user?.name || 'O')[0].toUpperCase());
    setText('count-received', data.counts.received); setText('count-pending', data.counts.pending); setText('count-assigned', data.counts.assigned); setText('count-resolved', data.counts.resolved); setText('insight-pending', data.counts.pending); setText('insight-assigned', data.counts.assigned); setText('insight-resolved', data.counts.resolved); rows = data.recent || []; renderRows(rows);
    const departments = document.getElementById('department-list'); if (departments) departments.innerHTML = data.departments?.length ? data.departments.map((item) => `<div class="insight-item"><span><i class="insight-dot" style="--dot-color:var(--purple)"></i>${escapeHtml(item.name)}</span><b>Active</b></div>`).join('') : '<div class="empty-state">No departments configured.</div>';
  }

  function renderAdmin(data) {
    const user = getSavedUser(); setText('sidebar-name', user?.name || 'Administrator'); setText('sidebar-avatar', 'A'); setText('top-avatar', 'A');
    Object.entries(data.counts).forEach(([key, value]) => setText(`count-${key}`, value)); rows = data.recent || []; renderRows(rows); renderCharts(data);
  }

  function renderCharts(data) {
    if (!window.Chart) return;
    const colors = ['#a855f7', '#35e0ff', '#ff4fd8', '#39e6a5', '#526bff', '#ffc857', '#ff647c', '#8b7cff', '#75f0ff'];
    const sectorCanvas = document.getElementById('sector-chart');
    if (sectorCanvas) new Chart(sectorCanvas, { type: 'bar', data: { labels: data.sector_data.map((item) => item.label.replace(' & ', ' / ')), datasets: [{ data: data.sector_data.map((item) => item.value), backgroundColor: colors, borderRadius: 5, borderSkipped: false }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#8f87aa', font: { size: 8 } }, grid: { display: false } }, y: { ticks: { color: '#8f87aa', font: { size: 9 }, precision: 0 }, grid: { color: 'rgba(255,255,255,.06)' }, beginAtZero: true } } } });
    const statusCanvas = document.getElementById('status-chart');
    if (statusCanvas) { const labels = data.status_data.map((item) => item.status.replaceAll('_', ' ')); new Chart(statusCanvas, { type: 'doughnut', data: { labels, datasets: [{ data: data.status_data.map((item) => item.value), backgroundColor: colors, borderColor: '#1c1635', borderWidth: 3 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { color: '#b9b2d0', boxWidth: 9, font: { size: 9 }, padding: 12 } } } } }); }
  }

  async function openDetail(id) {
    try {
      const item = await apiFetch(`/api/complaints/${id}/`); currentComplaintId = id;
      ensureOrganizationComposer();
      ensureFeedbackArea(item);
      setText('modal-title', item.title); setText('modal-id', item.public_id); setText('modal-org', role === 'organization' ? item.category_name : item.organization_name); setText('modal-status', item.status_label); setText('modal-description', item.description || 'Status-only view.');
      const history = document.getElementById('modal-history'); if (history) history.innerHTML = (item.history || []).map((entry) => `<div class="status-node done"><i data-lucide="check"></i><b>${escapeHtml(entry.status_label)}</b><small>${formatDate(entry.created_at)}</small></div>`).join('');
      const statusSelect = document.getElementById('modal-status-select'); if (statusSelect) statusSelect.value = item.status;
      document.getElementById('detail-modal').classList.add('open'); icons();
    } catch (error) { showToast(error.payload?.detail || 'Unable to open this complaint.', 'error'); }
  }

  async function updateStatus() {
    if (!currentComplaintId) return;
    try { await apiFetch(`/api/complaints/${currentComplaintId}/status/`, { method: 'PATCH', body: { status: document.getElementById('modal-status-select').value, note: document.getElementById('modal-status-note').value } }); showToast('Complaint status updated.'); document.getElementById('detail-modal').classList.remove('open'); await loadDashboard(); } catch (error) { showToast(error.payload?.detail || 'Unable to update the complaint.', 'error'); }
  }

  async function sendResponse() {
    const field = document.getElementById('modal-response-body');
    if (!currentComplaintId || !field?.value.trim()) { showToast('Write a response before sending.', 'error'); return; }
    try {
      await apiFetch(`/api/complaints/${currentComplaintId}/responses/`, { method: 'POST', body: { body: field.value.trim(), is_internal: false } });
      field.value = '';
      showToast('Response sent to the complainant.');
      await loadDashboard();
    } catch (error) { showToast(error.payload?.detail || 'Unable to send the response.', 'error'); }
  }

  function ensureOrganizationComposer() {
    if (role !== 'organization' || document.getElementById('modal-response-body')) return;
    const card = document.querySelector('#detail-modal .modal-card');
    if (!card) return;
    const composer = document.createElement('div');
    composer.innerHTML = '<label class="form-label" style="margin-top:18px">Response to complainant<textarea class="form-control" id="modal-response-body" placeholder="Share an update or resolution note..."></textarea></label><button class="button button-outline" id="modal-send-response" style="margin-top:12px">Send response <i data-lucide="send"></i></button>';
    card.appendChild(composer);
    composer.querySelector('#modal-send-response').addEventListener('click', sendResponse);
    icons();
  }

  function ensureFeedbackArea(item) {
    if (role !== 'user') return;
    if (item.status !== 'resolved') { document.getElementById('feedback-area')?.remove(); return; }
    if (document.getElementById('feedback-area')) return;
    const card = document.querySelector('#detail-modal .modal-card');
    if (!card) return;
    const area = document.createElement('div');
    area.id = 'feedback-area';
    area.innerHTML = '<label class="form-label" style="margin-top:18px">How did this resolution feel?<select class="form-control" id="feedback-rating"><option value="5">5 — Excellent</option><option value="4">4 — Good</option><option value="3">3 — Okay</option><option value="2">2 — Needs work</option><option value="1">1 — Poor</option></select><textarea class="form-control" id="feedback-comment" style="margin-top:8px" placeholder="Optional note about your experience"></textarea></label><button class="button button-outline" id="send-feedback" style="margin-top:12px">Share feedback <i data-lucide="star"></i></button>';
    card.appendChild(area);
    area.querySelector('#send-feedback').addEventListener('click', async () => {
      try {
        await apiFetch(`/api/complaints/${currentComplaintId}/feedback/`, { method: 'POST', body: { rating: area.querySelector('#feedback-rating').value, comment: area.querySelector('#feedback-comment').value } });
        showToast('Thank you for sharing your feedback.'); area.remove();
      } catch (error) { showToast(error.payload?.detail || 'Unable to save feedback.', 'error'); }
    });
    icons();
  }

  async function loadNotifications() {
    try { const items = await apiFetch('/api/notifications/'); const list = document.getElementById('notification-list'); if (!list) return; list.innerHTML = items.length ? items.map((item) => `<button class="notification-item ${item.read ? '' : 'unread'}" data-notification-id="${item.id}"><b>${escapeHtml(item.title)}</b><span>${escapeHtml(item.message)}</span><small>${formatDate(item.created_at)}</small></button>`).join('') : '<div class="empty-state">You are all caught up.</div>'; document.getElementById('notification-dot')?.classList.toggle('hidden', !items.some((item) => !item.read)); list.querySelectorAll('[data-notification-id]').forEach((button) => button.addEventListener('click', async () => { await apiFetch('/api/notifications/', { method: 'PATCH', body: { id: button.dataset.notificationId } }); button.classList.remove('unread'); })); } catch { /* Notification access is optional on an empty demo workspace. */ }
  }

  async function loadDashboard() {
    try {
      let user = getSavedUser(); if (!user) { const me = await apiFetch('/api/auth/me/'); user = me.user; saveUser(user); }
      const endpoint = role === 'admin' ? '/api/dashboard/admin/' : role === 'organization' ? '/api/dashboard/organization/' : '/api/dashboard/user/';
      const data = await apiFetch(endpoint); if (role === 'admin') renderAdmin(data); else if (role === 'organization') renderOrganization(data); else renderUser(data); loadNotifications();
    } catch (error) { if ([401, 403].includes(error.status)) { showToast('Please sign in to open this workspace.', 'error'); setTimeout(() => { window.location.href = '/login.html'; }, 700); } else showToast(error.payload?.detail || 'Unable to load workspace data.', 'error'); }
  }

  function setup() {
    icons(); document.getElementById('complaint-search')?.addEventListener('input', filterRows); document.getElementById('complaint-status-filter')?.addEventListener('change', filterRows);
    document.getElementById('mobile-side-button')?.addEventListener('click', () => document.getElementById('dashboard-sidebar').classList.toggle('open'));
    document.querySelectorAll('[data-close-modal]').forEach((button) => button.addEventListener('click', () => document.getElementById('detail-modal').classList.remove('open')));
    document.getElementById('detail-modal')?.addEventListener('click', (event) => { if (event.target.id === 'detail-modal') event.currentTarget.classList.remove('open'); }); document.getElementById('modal-update-status')?.addEventListener('click', updateStatus);
    document.getElementById('notification-button')?.addEventListener('click', () => document.getElementById('notification-panel').classList.toggle('open')); document.querySelectorAll('.js-notifications').forEach((item) => item.addEventListener('click', (event) => { event.preventDefault(); document.getElementById('notification-panel')?.classList.add('open'); }));
    document.querySelectorAll('.js-messages').forEach((item) => item.addEventListener('click', (event) => { event.preventDefault(); document.getElementById('complaints')?.scrollIntoView({ behavior: 'smooth' }); showToast('Open a complaint to view its linked response thread.'); }));
    document.querySelectorAll('.js-logout').forEach((button) => button.addEventListener('click', async () => { try { await apiFetch('/api/auth/logout/', { method: 'POST' }); } finally { sessionStorage.removeItem('resolvehub_user'); window.location.href = '/'; } }));
    loadDashboard();
  }
  document.addEventListener('DOMContentLoaded', setup);
})();
