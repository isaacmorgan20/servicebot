/* ── NexSupport Web UI — Frontend Logic ────────────────────────────────────── */

const API = {
  session:  () => fetch('/api/session'),
  chat:     (session_id, message) => fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id, message }),
  }),
  reset:    (session_id) => fetch('/api/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id }),
  }),
};

// ── State ──────────────────────────────────────────────────────────────────
let sessionId   = localStorage.getItem('nexsupport_session') || null;
let isLoading   = false;
let sidebarOpen = true;

// ── DOM Refs ───────────────────────────────────────────────────────────────
const messagesEl    = document.getElementById('messages');
const userInputEl   = document.getElementById('userInput');
const sendBtn       = document.getElementById('sendBtn');
const resetBtn      = document.getElementById('resetBtn');
const statusDot     = document.getElementById('statusDot');
const statusLabel   = document.getElementById('statusLabel');
const modelName     = document.getElementById('modelName');
const topbarModel   = document.getElementById('topbarModelName');
const statusStrip   = document.getElementById('statusStrip');
const statusStripTx = document.getElementById('statusStripText');
const sidebar       = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebarOpenBtn= document.getElementById('sidebarOpenBtn');

// ── Markdown Renderer ──────────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';

  // Escape HTML entities first
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Fenced code blocks
  html = html.replace(/```([a-z]*)\n([\s\S]*?)```/g, (_, lang, code) =>
    `<pre><code class="language-${lang}">${code.trimEnd()}</code></pre>`
  );

  // Inline code
  html = html.replace(/`([^`\n]+)`/g, '<code>$1</code>');

  // Headings
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm,   '<h1>$1</h1>');

  // Bold & Italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g,     '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g,         '<em>$1</em>');
  html = html.replace(/_(.+?)_/g,           '<em>$1</em>');

  // Horizontal rule
  html = html.replace(/^---$/gm, '<hr>');

  // Unordered lists — group consecutive li's
  html = html.replace(/((?:^[ \t]*[-*+] .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(l =>
      `<li>${l.replace(/^[ \t]*[-*+] /, '')}</li>`
    ).join('');
    return `<ul>${items}</ul>`;
  });

  // Ordered lists
  html = html.replace(/((?:^[ \t]*\d+\. .+\n?)+)/gm, (block) => {
    const items = block.trim().split('\n').map(l =>
      `<li>${l.replace(/^[ \t]*\d+\. /, '')}</li>`
    ).join('');
    return `<ol>${items}</ol>`;
  });

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // Paragraphs — wrap non-tag lines in <p>
  html = html.split('\n').map(line => {
    const trimmed = line.trim();
    if (!trimmed) return '';
    if (/^<(h[1-3]|ul|ol|li|pre|hr|blockquote)/.test(trimmed)) return trimmed;
    return `<p>${trimmed}</p>`;
  }).join('\n');

  return html;
}

// ── UI Helpers ─────────────────────────────────────────────────────────────
function setStatus(state) {
  // states: 'loading' | 'online' | 'error'
  statusDot.className = 'status-dot ' + state;
  const labels = { loading: 'Connecting…', online: 'Online', error: 'Error' };
  statusLabel.textContent = labels[state] || state;
}

function setModel(name) {
  const display = name || '—';
  modelName.textContent   = display;
  topbarModel.textContent = display;
}

function showStatusStrip(messages) {
  if (!messages || messages.length === 0) {
    statusStrip.hidden = true;
    return;
  }
  statusStripTx.textContent = messages.join(' — ');
  statusStrip.hidden = false;
  // Auto-hide after 8 seconds
  setTimeout(() => { statusStrip.hidden = true; }, 8000);
}

function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function scrollToBottom(smooth = true) {
  const wrap = document.getElementById('messagesWrap');
  wrap.scrollTo({ top: wrap.scrollHeight, behavior: smooth ? 'smooth' : 'instant' });
}

function clearMessages() {
  messagesEl.innerHTML = '';
}

function showEmptyState() {
  clearMessages();
  messagesEl.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon"><i data-lucide="message-circle-heart"></i></div>
      <div class="empty-title">How can I help you?</div>
      <p class="empty-sub">Ask me anything — from order issues and refunds to business support. I'm here for you.</p>
    </div>`;
  lucide.createIcons();
}

// ── Message Rendering ──────────────────────────────────────────────────────
function appendMessage(role, content, animate = true) {
  // Remove empty state if present
  const empty = messagesEl.querySelector('.empty-state');
  if (empty) empty.remove();

  const isBot = role === 'bot';
  const wrapper = document.createElement('div');
  wrapper.className = `msg ${role}`;
  if (!animate) wrapper.style.animation = 'none';

  const avatarIcon = isBot ? 'bot' : 'user';
  const timeStr    = formatTime();

  wrapper.innerHTML = `
    <div class="msg-avatar"><i data-lucide="${avatarIcon}"></i></div>
    <div class="msg-col">
      <div class="msg-bubble">${isBot ? renderMarkdown(content) : escapeHtml(content)}</div>
      <div class="msg-time">${timeStr}</div>
    </div>`;

  messagesEl.appendChild(wrapper);
  lucide.createIcons();
  scrollToBottom();
  return wrapper;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── Typing Indicator ───────────────────────────────────────────────────────
let typingEl = null;

function showTyping() {
  const empty = messagesEl.querySelector('.empty-state');
  if (empty) empty.remove();

  typingEl = document.createElement('div');
  typingEl.className = 'msg bot';
  typingEl.id = 'typingIndicator';
  typingEl.innerHTML = `
    <div class="msg-avatar"><i data-lucide="bot"></i></div>
    <div class="msg-col">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  messagesEl.appendChild(typingEl);
  lucide.createIcons();
  scrollToBottom();
}

function hideTyping() {
  if (typingEl) { typingEl.remove(); typingEl = null; }
}

// ── Input Management ───────────────────────────────────────────────────────
function setInputDisabled(disabled) {
  isLoading           = disabled;
  userInputEl.disabled = disabled;
  sendBtn.disabled     = disabled || !userInputEl.value.trim();
  resetBtn.disabled    = disabled;
}

function autoResizeInput() {
  userInputEl.style.height = 'auto';
  userInputEl.style.height = Math.min(userInputEl.scrollHeight, 160) + 'px';
}

// ── Send Message ───────────────────────────────────────────────────────────
async function sendMessage(text) {
  const message = (text || userInputEl.value).trim();
  if (!message || isLoading || !sessionId) return;

  userInputEl.value = '';
  userInputEl.style.height = 'auto';
  sendBtn.disabled = true;
  setInputDisabled(true);

  appendMessage('user', message);
  showTyping();

  try {
    const res  = await API.chat(sessionId, message);
    const data = await res.json();

    hideTyping();

    if (!res.ok) {
      appendMessage('bot', `⚠️ Error: ${data.detail || 'Something went wrong. Please try again.'}`);
      return;
    }

    appendMessage('bot', data.reply);
    setModel(data.model);
    showStatusStrip(data.status_messages);

  } catch (err) {
    hideTyping();
    appendMessage('bot', '⚠️ Could not reach the server. Make sure the backend is running.');
  } finally {
    setInputDisabled(false);
    userInputEl.focus();
  }
}

// ── Session Init ───────────────────────────────────────────────────────────
async function initSession() {
  setStatus('loading');
  setInputDisabled(true);

  try {
    const res  = await API.session();
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Session init failed');

    sessionId = data.session_id;
    localStorage.setItem('nexsupport_session', sessionId);

    setModel(data.model);
    setStatus('online');

    clearMessages();
    appendMessage('bot', data.greeting);

  } catch (err) {
    setStatus('error');
    showEmptyState();
    appendMessage('bot', `⚠️ Could not connect to the server.\n\nMake sure the backend is running with:\n\`\`\`\nuv run python run_web.py\n\`\`\``);
  } finally {
    setInputDisabled(false);
    userInputEl.focus();
  }
}

// ── Reset Conversation ─────────────────────────────────────────────────────
async function resetConversation() {
  if (isLoading) return;

  setInputDisabled(true);
  setStatus('loading');
  clearMessages();

  try {
    const res  = await API.reset(sessionId);
    const data = await res.json();

    if (!res.ok) throw new Error(data.detail || 'Reset failed');

    sessionId = data.session_id;
    localStorage.setItem('nexsupport_session', sessionId);

    setModel(data.model);
    setStatus('online');
    appendMessage('bot', data.greeting);

  } catch (err) {
    setStatus('error');
    appendMessage('bot', '⚠️ Could not reset the session. Please refresh the page.');
  } finally {
    setInputDisabled(false);
    userInputEl.focus();
  }
}

// ── Sidebar Toggle ─────────────────────────────────────────────────────────
function toggleSidebar(open) {
  sidebarOpen = (open !== undefined) ? open : !sidebarOpen;
  if (sidebarOpen) {
    sidebar.classList.remove('hidden');
    sidebarOpenBtn.style.display = 'none';
  } else {
    sidebar.classList.add('hidden');
    sidebarOpenBtn.style.display = 'flex';
  }
}

// ── Event Listeners ────────────────────────────────────────────────────────
sendBtn.addEventListener('click', () => sendMessage());

userInputEl.addEventListener('input', () => {
  autoResizeInput();
  sendBtn.disabled = isLoading || !userInputEl.value.trim();
});

userInputEl.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

resetBtn.addEventListener('click', resetConversation);

sidebarToggle.addEventListener('click', () => toggleSidebar(false));
sidebarOpenBtn.addEventListener('click', () => toggleSidebar(true));

// Quick starter chips
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const prompt = chip.dataset.prompt;
    if (prompt) sendMessage(prompt);
  });
});

// Close sidebar on mobile when clicking chat area
document.getElementById('chatPanel').addEventListener('click', (e) => {
  if (window.innerWidth <= 640 && sidebarOpen && !sidebar.contains(e.target)) {
    toggleSidebar(false);
  }
});

// ── Boot ───────────────────────────────────────────────────────────────────
(async () => {
  lucide.createIcons();
  sidebarOpenBtn.style.display = 'none';

  // Always start a fresh session for simplicity (avoids stale session errors)
  // If you want to persist session across page reloads, use the session ID from localStorage
  // and add a GET /api/history endpoint. For now, always init fresh.
  localStorage.removeItem('nexsupport_session');
  sessionId = null;

  await initSession();
})();
