// ── Token storage ────────────────────────────────────────────────
// localStorage persists across page refreshes
const getToken = () => localStorage.getItem('token');
const setToken = t => localStorage.setItem('token', t);
const removeToken = () => localStorage.removeItem('token');

// ── Auth state ───────────────────────────────────────────────────
function updateAuthUI(email) {
  const isLoggedIn = !!email;
  document.getElementById('auth-guest').hidden = isLoggedIn;
  document.getElementById('auth-user').hidden = !isLoggedIn;
  if (email) document.getElementById('auth-email').textContent = email;
}

// On page load — check if already logged in
async function initAuth() {
  const token = getToken();
  if (!token) return;

  try {
    const res = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const user = await res.json();
      updateAuthUI(user.email);
    } else {
      removeToken(); // token expired or invalid
    }
  } catch {
    removeToken();
  }
}

// ── Modal ────────────────────────────────────────────────────────
function openModal(tab) {
  document.getElementById('modal-overlay').classList.add('open');
  document.getElementById('auth-modal').classList.add('open');
  document.getElementById('modal-login').hidden = tab !== 'login';
  document.getElementById('modal-register').hidden = tab !== 'register';
  document.getElementById('modal-error').textContent = '';

  // Focus first input
  const id = tab === 'login' ? 'login-email' : 'register-email';
  setTimeout(() => document.getElementById(id).focus(), 50);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.getElementById('auth-modal').classList.remove('open');
}

// Close on Escape key
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeModal();
});

// ── Register ─────────────────────────────────────────────────────
async function handleRegister() {
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;
  const errEl = document.getElementById('modal-error');
  const btn = document.querySelector('#modal-register .modal-btn');

  errEl.textContent = '';
  btn.disabled = true;
  btn.textContent = 'Creating account...';

  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Registration failed');

    setToken(data.access_token);
    updateAuthUI(email);
    closeModal();
    showToast('Welcome! You\'re all set 🔥');
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Create account';
  }
}

// ── Login ────────────────────────────────────────────────────────
async function handleLogin() {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;
  const errEl = document.getElementById('modal-error');
  const btn = document.querySelector('#modal-login .modal-btn');

  errEl.textContent = '';
  btn.disabled = true;
  btn.textContent = 'Logging in...';

  try {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Login failed');

    setToken(data.access_token);
    updateAuthUI(email);
    closeModal();
    showToast('Logged in! Now go roast some code 🔥');
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Login';
  }
}

// ── Logout ───────────────────────────────────────────────────────
function logout() {
  removeToken();
  updateAuthUI(null);
  showToast('Logged out');
}

// ── Char counter ─────────────────────────────────────────────────
const input = document.getElementById('code-input');
const counter = document.getElementById('char-count');
input.addEventListener('input', () => {
  const len = input.value.length;
  counter.textContent = len;
  counter.style.color = len > 4500 ? '#ff4500' : '';
});

// ── Submit roast ─────────────────────────────────────────────────
async function submitRoast() {
  const code = input.value.trim();
  if (!code) return showError('Paste some code first!');

  // Gate behind auth
  if (!getToken()) {
    openModal('login');
    showError('Login first to roast code!');
    return;
  }

  const language = document.getElementById('language').value;
  const btn = document.getElementById('roast-btn');

  btn.disabled = true;
  btn.querySelector('.btn-text').hidden = true;
  btn.querySelector('.btn-loading').hidden = false;

  try {
    const res = await fetch('/api/roast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${getToken()}`,  // send token with every request
      },
      body: JSON.stringify({ code, language }),
    });

    if (res.status === 401) {
      removeToken();
      updateAuthUI(null);
      openModal('login');
      throw new Error('Session expired — please login again');
    }

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `Error ${res.status}`);
    }

    const data = await res.json();
    showResults(data);
  } catch (err) {
    showError(err.message);
  } finally {
    btn.disabled = false;
    btn.querySelector('.btn-text').hidden = false;
    btn.querySelector('.btn-loading').hidden = true;
  }
}

// ── Display results ───────────────────────────────────────────────
function showResults({ roast, feedback, rating }) {
  document.getElementById('roast-text').textContent = roast;
  document.getElementById('feedback-text').textContent = feedback;

  const ratingEl = document.getElementById('rating-number');
  const fill = document.getElementById('rating-fill');

  let current = 0;
  const target = Math.min(Math.max(Math.round(rating), 1), 10);
  const interval = setInterval(() => {
    current++;
    ratingEl.textContent = current;
    if (current >= target) clearInterval(interval);
  }, 80);

  setTimeout(() => { fill.style.width = `${target * 10}%`; }, 100);

  const resultSection = document.getElementById('result-section');
  resultSection.hidden = false;
  resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Reset ─────────────────────────────────────────────────────────
function reset() {
  document.getElementById('result-section').hidden = true;
  input.value = '';
  counter.textContent = '0';
  input.focus();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Toast (success messages) ──────────────────────────────────────
function showToast(msg) {
  const toast = document.getElementById('error-toast');
  toast.textContent = msg;
  toast.style.borderColor = 'var(--green)';
  toast.style.color = 'var(--green)';
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
    toast.style.borderColor = '';
    toast.style.color = '';
  }, 3000);
}

// ── Error toast ───────────────────────────────────────────────────
function showError(msg) {
  const toast = document.getElementById('error-toast');
  toast.textContent = `⚠ ${msg}`;
  toast.style.borderColor = '';
  toast.style.color = '';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── Keyboard shortcut ─────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submitRoast();
});

// ── Init ──────────────────────────────────────────────────────────
initAuth();