// ── Char counter ────────────────────────────────────────────────
const input = document.getElementById('code-input');
const counter = document.getElementById('char-count');

input.addEventListener('input', () => {
  const len = input.value.length;
  counter.textContent = len;
  counter.style.color = len > 4500 ? '#ff4500' : '';
});

// ── Submit ───────────────────────────────────────────────────────
async function submitRoast() {
  const code = input.value.trim();
  if (!code) return showError('Paste some code first!');

  const language = document.getElementById('language').value;
  const btn = document.getElementById('roast-btn');

  // Loading state
  btn.disabled = true;
  btn.querySelector('.btn-text').hidden = true;
  btn.querySelector('.btn-loading').hidden = false;

  try {
    const res = await fetch('/api/roast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || `Server error ${res.status}`);
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

// ── Display results ──────────────────────────────────────────────
function showResults({ roast, feedback, rating }) {
  document.getElementById('roast-text').textContent = roast;
  document.getElementById('feedback-text').textContent = feedback;

  const ratingEl = document.getElementById('rating-number');
  const fill = document.getElementById('rating-fill');

  // Animate rating number counting up
  let current = 0;
  const target = Math.min(Math.max(Math.round(rating), 1), 10);
  const interval = setInterval(() => {
    current++;
    ratingEl.textContent = current;
    if (current >= target) clearInterval(interval);
  }, 80);

  // Animate bar fill (slight delay so animation is visible)
  setTimeout(() => {
    fill.style.width = `${target * 10}%`;
  }, 100);

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

// ── Error toast ───────────────────────────────────────────────────
function showError(msg) {
  const toast = document.getElementById('error-toast');
  toast.textContent = `⚠ ${msg}`;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}

// ── Keyboard shortcut: Cmd/Ctrl + Enter to submit ─────────────────
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') submitRoast();
});
