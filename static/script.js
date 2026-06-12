/* ═══════════════════════════════════════════════════════════════
   FlowTask — Frontend Logic
   static/script.js
   All data lives in MySQL via Flask. No localStorage for tasks.
   API key is NEVER in this file — it stays in db_config.py.
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── State ─────────────────────────────────────────────────────────
let tasks  = [];
let filter = 'all';

// ── Quotes ────────────────────────────────────────────────────────
const QUOTES = [
  { text: 'The secret of getting ahead is getting started.',               author: 'Mark Twain' },
  { text: 'Focus on being productive instead of busy.',                    author: 'Tim Ferriss' },
  { text: 'Do the hard jobs first. The easy jobs will take care of themselves.', author: 'Dale Carnegie' },
  { text: 'Your future is created by what you do today, not tomorrow.',    author: 'Robert Kiyosaki' },
  { text: 'Small daily improvements are the key to staggering long-term results.', author: 'Robin Sharma' },
  { text: 'Energy and persistence conquer all things.',                    author: 'Benjamin Franklin' },
  { text: 'Action is the foundational key to all success.',                author: 'Pablo Picasso' },
  { text: 'The way to get started is to quit talking and begin doing.',    author: 'Walt Disney' },
  { text: 'You don\'t have to be great to start, but you have to start to be great.', author: 'Zig Ziglar' },
  { text: 'Dream big. Start small. Act now.',                              author: 'Robin Sharma' },
];
let qIdx = 0;

function nextQuote() {
  qIdx = (qIdx + 1) % QUOTES.length;
  const q = QUOTES[qIdx];
  document.getElementById('quote-text').textContent   = q.text;
  document.getElementById('quote-author').textContent = '— ' + q.author;
}

// ── API helpers ───────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Load tasks from server ────────────────────────────────────────
async function loadTasks() {
  try {
    tasks = await apiFetch(`/api/tasks?filter=${filter}`);
    render();
    loadStats();
  } catch (err) {
    console.error('[loadTasks]', err.message);
  }
}

// ── Load stats separately ─────────────────────────────────────────
async function loadStats() {
  try {
    const s = await apiFetch('/api/stats');
    document.getElementById('stat-total').textContent = s.total;
    document.getElementById('stat-done').textContent  = s.done;
    document.getElementById('stat-high').textContent  = s.high;
    document.getElementById('stat-pct').textContent   = s.completion + '%';
    document.getElementById('prog-fill').style.width  = s.completion + '%';
    document.getElementById('prog-pct').textContent   = s.completion + '%';
  } catch (_) {}
}

// ── Add task ──────────────────────────────────────────────────────
async function addTask() {
  const inp  = document.getElementById('task-input');
  const text = inp.value.trim();
  if (!text) { inp.focus(); return; }

  const priority = document.getElementById('pri-select').value;
  inp.value = '';

  // Optimistic local prepend
  const temp = { id: '__tmp__' + Date.now(), text, priority, done: false, _temp: true };
  tasks.unshift(temp);
  render();

  try {
    const saved = await apiFetch('/api/tasks', {
      method: 'POST',
      body:   JSON.stringify({ text, priority }),
    });
    // Replace temp with real record
    const idx = tasks.findIndex(t => t.id === temp.id);
    if (idx !== -1) tasks[idx] = saved;
    render();
    loadStats();
  } catch (err) {
    // Rollback
    tasks = tasks.filter(t => t.id !== temp.id);
    render();
    showToast('⚠️ Could not add task: ' + err.message, 'error');
  }
}

// ── Toggle done ───────────────────────────────────────────────────
async function toggleTask(id) {
  if (String(id).startsWith('__tmp__')) return;
  const task = tasks.find(t => t.id === id);
  if (!task) return;

  task.done = !task.done;   // optimistic
  render();

  try {
    const updated = await apiFetch(`/api/tasks/${id}`, {
      method: 'PATCH',
      body:   JSON.stringify({ done: task.done }),
    });
    Object.assign(task, updated);
    render();
    loadStats();
  } catch (err) {
    task.done = !task.done;  // rollback
    render();
  }
}

// ── Delete task ───────────────────────────────────────────────────
async function deleteTask(id) {
  if (String(id).startsWith('__tmp__')) return;
  const backup = [...tasks];
  tasks = tasks.filter(t => t.id !== id);
  render();

  try {
    await apiFetch(`/api/tasks/${id}`, { method: 'DELETE' });
    loadStats();
  } catch (err) {
    tasks = backup;
    render();
  }
}

// ── Filter ────────────────────────────────────────────────────────
function setFilter(btn, f) {
  filter = f;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  loadTasks();
}

// ── Render task list ──────────────────────────────────────────────
function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function render() {
  const list = document.getElementById('task-list');

  if (!tasks.length) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">✦</div>
        <div>No tasks here — add one above!</div>
      </div>`;
    return;
  }

  list.innerHTML = tasks.map(t => `
    <div class="task-item ${t.done ? 'done' : ''}" id="task-${t.id}">
      <div class="check-ring" onclick="toggleTask(${JSON.stringify(t.id)})">
        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
          <path d="M1 4l2.5 2.5L9 1" stroke="#fff" stroke-width="1.8"
            stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <span class="task-text">${escHtml(t.text)}</span>
      <span class="pri-dot ${t.priority}" title="${t.priority} priority"></span>
      <button class="btn-del" onclick="deleteTask(${JSON.stringify(t.id)})" title="Delete">✕</button>
    </div>
  `).join('');
}

// ── Toast notification ────────────────────────────────────────────
function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed; bottom:1.5rem; right:1.5rem; z-index:999;
    padding:0.7rem 1.2rem; border-radius:10px; font-size:0.8rem;
    background:${type === 'error' ? 'rgba(251,113,133,0.15)' : 'rgba(52,211,153,0.15)'};
    border:1px solid ${type === 'error' ? 'rgba(251,113,133,0.3)' : 'rgba(52,211,153,0.3)'};
    color:#fff; backdrop-filter:blur(12px);
    animation:taskIn 0.3s ease both;
  `;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3500);
}

// ── AI Assistant ──────────────────────────────────────────────────
async function sendAI() {
  const inp = document.getElementById('ai-input');
  const msg = inp.value.trim();
  if (!msg) return;
  inp.value = '';
  appendMsg(msg, 'user');
  await callAI(msg);
}

function quickPrompt(msg) {
  appendMsg(msg, 'user');
  callAI(msg);
}

function appendMsg(text, role) {
  const box = document.getElementById('ai-msgs');
  const div = document.createElement('div');
  div.className   = 'msg ' + role;
  div.textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
  return div;
}

async function callAI(userMsg) {
  const box    = document.getElementById('ai-msgs');
  const loader = appendMsg('Thinking…', 'bot loading');

  try {
    // 🔐 Only the message is sent — API key is handled by Flask (db_config.py)
    const data = await apiFetch('/api/ai', {
      method: 'POST',
      body:   JSON.stringify({ message: userMsg }),
    });
    loader.remove();
    appendMsg(data.reply || 'No response received.', 'bot');
  } catch (err) {
    loader.remove();
    appendMsg('⚠️ ' + err.message, 'bot');
  }
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadTasks();

  // Enter keys
  document.getElementById('task-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') addTask();
  });
  document.getElementById('ai-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') sendAI();
  });

  // Shuffle first quote randomly on load
  qIdx = Math.floor(Math.random() * QUOTES.length);
  const q = QUOTES[qIdx];
  document.getElementById('quote-text').textContent   = q.text;
  document.getElementById('quote-author').textContent = '— ' + q.author;
});