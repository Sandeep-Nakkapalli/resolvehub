(function () {
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    return parts.length === 2 ? parts.pop().split(';').shift() : '';
  }

  function csrfToken() {
    return getCookie('csrftoken');
  }

  async function ensureCsrfToken() {
    let token = csrfToken();
    if (token) return token;

    const response = await fetch('/api/auth/csrf/', {
      credentials: 'same-origin',
      headers: { Accept: 'application/json' },
    });
    if (!response.ok) throw new Error('Could not initialize secure form submission.');

    token = csrfToken();
    if (!token) throw new Error('The security cookie was not set. Please reload and try again.');
    return token;
  }

  async function apiFetch(url, options = {}) {
    const config = { credentials: 'same-origin', ...options };
    const method = (config.method || 'GET').toUpperCase();
    const headers = { Accept: 'application/json', ...(config.headers || {}) };
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) headers['X-CSRFToken'] = await ensureCsrfToken();
    if (config.body && !(config.body instanceof FormData) && typeof config.body !== 'string') {
      headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(config.body);
    }
    config.headers = headers;
    const response = await fetch(url, config);
    const contentType = response.headers.get('content-type') || '';
    const payload = contentType.includes('application/json') ? await response.json() : await response.text();
    if (!response.ok) {
      const error = new Error(typeof payload === 'string' ? payload : payload.detail || 'Something went wrong.');
      error.status = response.status;
      error.payload = payload;
      throw error;
    }
    return payload;
  }

  function showToast(message, type = 'success') {
    const region = document.getElementById('toast-region');
    if (!region) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'error' : ''}`;
    toast.innerHTML = `<i data-lucide="${type === 'error' ? 'circle-alert' : 'check-circle-2'}"></i><span>${escapeHtml(message)}</span>`;
    region.appendChild(toast);
    if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.8 } });
    setTimeout(() => toast.remove(), 4500);
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[character]));
  }

  function formatDate(value) {
    if (!value) return '—';
    return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(value));
  }

  function saveUser(user) {
    sessionStorage.setItem('resolvehub_user', JSON.stringify(user));
  }

  function getSavedUser() {
    try { return JSON.parse(sessionStorage.getItem('resolvehub_user') || 'null'); } catch { return null; }
  }

  function redirectForRole(user) {
    if (user?.role === 'platform_admin') window.location.href = '/admin-dashboard.html';
    else if (['organization_admin', 'organization_agent'].includes(user?.role)) window.location.href = '/organization-dashboard.html';
    else window.location.href = '/user-dashboard.html';
  }

  window.ResolveHub = { apiFetch, showToast, escapeHtml, formatDate, saveUser, getSavedUser, redirectForRole, getCookie };
})();
