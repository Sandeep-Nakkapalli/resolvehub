(function () {
  const { apiFetch, showToast, escapeHtml, formatDate } = window.ResolveHub || {};
  const steps = [
    ['submitted', 'Submitted'], ['under_review', 'Under Review'], ['assigned', 'Assigned'], ['investigating', 'Investigation in Progress'], ['action_taken', 'Action Taken'], ['resolved', 'Resolved'],
  ];
  function icons() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } }); }
  function render(result) {
    document.getElementById('result-id').textContent = result.public_id;
    document.getElementById('result-sector').textContent = result.sector_name;
    document.getElementById('result-organization').textContent = result.organization_name;
    document.getElementById('result-status').innerHTML = `<span class="status-pill-large">${escapeHtml(result.status_label)}</span>`;
    const current = steps.findIndex(([key]) => key === result.status);
    const history = result.history || [];
    const timeline = steps.map(([key, label], index) => { const item = history.find((entry) => entry.to_status === key); return `<div class="status-node ${index < current ? 'done' : ''} ${index === current ? 'active' : ''}"><i data-lucide="${index <= current ? 'check' : 'circle'}"></i><b>${label}</b><small>${item ? formatDate(item.created_at) : index <= current ? 'Updated' : 'Pending'}</small></div>`; }).join('');
    const extra = current === -1 ? `<div class="status-node active"><i data-lucide="circle-alert"></i><b>${escapeHtml(result.status_label)}</b><small>Current status</small></div>` : '';
    document.getElementById('status-timeline').innerHTML = timeline + extra;
    document.getElementById('tracking-result').classList.add('open'); icons();
  }
  async function track(event) { event.preventDefault(); const form = event.target; try { render(await apiFetch('/api/complaints/track/', { method: 'POST', body: { complaint_id: form.complaint_id.value, verifier: form.verifier.value } })); } catch (error) { showToast(error.payload?.detail || 'We could not verify those tracking details.', 'error'); } }
  document.addEventListener('DOMContentLoaded', () => { icons(); document.getElementById('tracking-form').addEventListener('submit', track); const id = new URLSearchParams(window.location.search).get('id'); if (id) document.getElementById('tracking-id').value = id; });
})();
