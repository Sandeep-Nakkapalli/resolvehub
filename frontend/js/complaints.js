(function () {
  const { apiFetch, showToast, getSavedUser, escapeHtml } = window.ResolveHub || {};
  let currentStep = 1;
  let sectors = [];

  function icons() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } }); }
  function form() { return document.getElementById('complaint-form'); }
  function selected(name) { return form().querySelector(`[name="${name}"]`)?.value || ''; }
  function setStep(step) {
    currentStep = step;
    document.querySelectorAll('.form-panel').forEach((panel) => panel.classList.toggle('active', Number(panel.dataset.panel) === step));
    document.querySelectorAll('.form-step').forEach((item) => { const value = Number(item.dataset.stepLabel); item.classList.toggle('active', value === step); item.classList.toggle('done', value < step); });
    document.getElementById('previous-step').disabled = step === 1;
    document.getElementById('next-step').hidden = step === 6;
    document.getElementById('submit-complaint').hidden = step !== 6;
    if (step === 6) fillReview();
    window.scrollTo({ top: document.querySelector('.form-shell').offsetTop - 85, behavior: 'smooth' });
  }

  function validateStep() {
    const panel = document.querySelector(`[data-panel="${currentStep}"]`);
    if (currentStep === 1 && !selected('account_type')) return false;
    let valid = true;
    panel.querySelectorAll('[required]').forEach((field) => { if (!field.value.trim()) { field.classList.add('invalid'); valid = false; } else field.classList.remove('invalid'); });
    if (!valid) showToast('Complete the highlighted field before continuing.', 'error');
    return valid;
  }

  async function loadSelections() {
    try {
      sectors = await apiFetch('/api/sectors/');
      document.getElementById('sector-select').innerHTML = '<option value="">Choose a sector</option>' + sectors.map((sector) => `<option value="${sector.id}">${escapeHtml(sector.name)}</option>`).join('');
    } catch { showToast('Unable to load sectors. Please try again.', 'error'); }
  }

  async function loadSectorChildren() {
    const id = document.getElementById('sector-select').value;
    const organizationSelect = document.getElementById('organization-select'); const categorySelect = document.getElementById('category-select');
    organizationSelect.innerHTML = '<option value="">Loading organizations...</option>'; categorySelect.innerHTML = '<option value="">Loading categories...</option>';
    if (!id) { organizationSelect.innerHTML = '<option value="">Choose a sector first</option>'; categorySelect.innerHTML = '<option value="">Choose a sector first</option>'; return; }
    try {
      const [organizations, categoryResponse] = await Promise.all([apiFetch(`/api/organizations/?sector=${id}`), apiFetch(`/api/sectors/${id}/categories/`)]);
      organizationSelect.innerHTML = '<option value="">Choose an organization</option>' + organizations.map((item) => `<option value="${item.id}">${escapeHtml(item.name)}${item.is_verified ? ' · Verified' : ''}</option>`).join('');
      categorySelect.innerHTML = '<option value="">Choose a category</option>' + categoryResponse.categories.map((item) => `<option value="${item.id}" data-description="${escapeHtml(item.description)}">${escapeHtml(item.name)}</option>`).join('');
      document.getElementById('category-hint').textContent = `${categoryResponse.categories.length} categories are available for this sector.`;
    } catch { organizationSelect.innerHTML = '<option value="">Unable to load organizations</option>'; categorySelect.innerHTML = '<option value="">Unable to load categories</option>'; }
  }

  function fillReview() {
    const value = (name) => form().querySelector(`[name="${name}"]`)?.selectedOptions?.[0]?.textContent || selected(name) || '—';
    const title = form().querySelector('[name="title"]')?.value || '—'; const description = form().querySelector('[name="description"]')?.value || '—';
    document.getElementById('review-card').innerHTML = `<div class="review-line"><span>Account type</span><span>${escapeHtml(selected('account_type'))}</span></div><div class="review-line"><span>Sector</span><span>${escapeHtml(value('sector'))}</span></div><div class="review-line"><span>Organization</span><span>${escapeHtml(value('organization'))}</span></div><div class="review-line"><span>Category</span><span>${escapeHtml(value('category'))}</span></div><div class="review-line"><span>Complaint title</span><span>${escapeHtml(title)}</span></div><div class="review-line"><span>Description</span><span>${escapeHtml(description.slice(0, 150))}${description.length > 150 ? '…' : ''}</span></div>`;
  }

  async function submit(event) {
    event.preventDefault();
    const data = new FormData(form());
    try {
      const response = await apiFetch('/api/complaints/', { method: 'POST', body: data });
      document.getElementById('complaint-form').style.display = 'none'; document.getElementById('form-success').classList.add('open'); document.getElementById('success-id').textContent = response.tracking_id; document.getElementById('success-track').href = `/track-complaint.html?id=${encodeURIComponent(response.tracking_id)}`; icons();
    } catch (error) { showToast(error.payload?.detail || 'Unable to submit this complaint.', 'error'); }
  }

  async function requestOrganization() {
    const user = getSavedUser(); if (!user) { showToast('Sign in to request an organization.', 'error'); return; }
    const name = window.prompt('Organization name:'); if (!name) return; const website = window.prompt('Website (optional):') || ''; const sector = selected('sector');
    if (!sector) { showToast('Choose a sector first.', 'error'); return; }
    try { const response = await apiFetch('/api/organizations/', { method: 'POST', body: { name, website, sector, reason: 'Requested while registering a complaint.' } }); showToast(response.message); } catch (error) { showToast(error.payload?.detail || 'Unable to send the request.', 'error'); }
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!getSavedUser()) { showToast('Sign in to register a complaint.', 'error'); setTimeout(() => { window.location.href = '/login.html'; }, 900); return; }
    icons(); loadSelections();
    document.getElementById('sector-select').addEventListener('change', loadSectorChildren);
    document.getElementById('next-step').addEventListener('click', () => { if (validateStep()) setStep(Math.min(6, currentStep + 1)); });
    document.getElementById('previous-step').addEventListener('click', () => setStep(Math.max(1, currentStep - 1)));
    form().addEventListener('submit', submit); document.getElementById('request-org-button').addEventListener('click', requestOrganization);
    document.getElementById('evidence-input').addEventListener('change', (event) => { document.getElementById('file-list').innerHTML = Array.from(event.target.files).map((file) => `<span class="file-item"><span>${escapeHtml(file.name)}</span><span>${(file.size / 1024 / 1024).toFixed(1)} MB</span></span>`).join(''); });
    document.querySelector('.js-logout')?.addEventListener('click', async () => { try { await apiFetch('/api/auth/logout/', { method: 'POST' }); } finally { sessionStorage.removeItem('resolvehub_user'); window.location.href = '/'; } });
  });
})();
