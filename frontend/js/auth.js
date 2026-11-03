(function () {
  const { apiFetch, showToast, saveUser, redirectForRole } = window.ResolveHub || {};

  function initIcons() { if (window.lucide) lucide.createIcons({ attrs: { 'stroke-width': 1.7 } }); }

  function setupPasswordToggles() {
    document.querySelectorAll('.password-toggle').forEach((button) => button.addEventListener('click', () => {
      const input = button.parentElement.querySelector('input');
      input.type = input.type === 'password' ? 'text' : 'password';
      button.setAttribute('aria-label', input.type === 'password' ? 'Show password' : 'Hide password');
      button.innerHTML = `<i data-lucide="${input.type === 'password' ? 'eye' : 'eye-off'}"></i>`;
      initIcons();
    }));
  }

  function clearErrors(form) { form.querySelectorAll('.field-error').forEach((node) => node.textContent = ''); }

  function showErrors(form, payload) {
    if (!payload || typeof payload !== 'object') return;
    Object.entries(payload).forEach(([key, value]) => {
      const input = form.querySelector(`[name="${key}"]`);
      const error = input?.closest('label')?.querySelector('.field-error');
      if (error) error.textContent = Array.isArray(value) ? value[0] : String(value);
    });
  }

  function formDataObject(form) { return Object.fromEntries(new FormData(form).entries()); }

  async function handleLogin(form) {
    clearErrors(form);
    const data = formDataObject(form);
    try {
      const response = await apiFetch('/api/auth/login/', { method: 'POST', body: { identifier: data.identifier, password: data.password, remember: form.querySelector('[name="remember"]')?.checked || false } });
      saveUser(response.user);
      showToast(response.message || 'Signed in successfully.');
      setTimeout(() => redirectForRole(response.user), 350);
    } catch (error) {
      showErrors(form, error.payload);
      showToast(error.payload?.detail || 'Unable to sign in. Check your details and try again.', 'error');
    }
  }

  async function handleRegister(form) {
    clearErrors(form);
    const data = formDataObject(form);
    data.terms_accepted = form.querySelector('[name="terms_accepted"]').checked;
    try {
      const response = await apiFetch('/api/auth/register/', { method: 'POST', body: data });
      saveUser(response.user);
      showToast(response.message || 'Account created.');
      setTimeout(() => redirectForRole(response.user), 450);
    } catch (error) {
      showErrors(form, error.payload);
      showToast(error.payload?.detail || 'Please correct the highlighted fields.', 'error');
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    initIcons(); setupPasswordToggles();
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    loginForm?.addEventListener('submit', (event) => { event.preventDefault(); handleLogin(loginForm); });
    registerForm?.addEventListener('submit', (event) => { event.preventDefault(); handleRegister(registerForm); });
    document.getElementById('forgot-password')?.addEventListener('click', async () => {
      const email = window.prompt('Enter the email address on your ResolveHub account:');
      if (!email) return;
      try { const response = await apiFetch('/api/auth/password-reset/', { method: 'POST', body: { email } }); showToast(response.message); } catch (error) { showToast(error.payload?.detail || 'Unable to process that request.', 'error'); }
    });
  });
})();
