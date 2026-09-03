// Emojify — macOS Ventura Aqua Glass Frontend

// ---------------- View Switching ----------------
const tabChat = document.querySelector('#tab-chat');
const tabSolo = document.querySelector('#tab-solo');
const viewChat = document.querySelector('#view-chat');
const viewSolo = document.querySelector('#view-solo');

function switchTab(target) {
  if (target === 'chat') {
    tabChat.classList.add('active');
    tabSolo.classList.remove('active');
    viewChat.hidden = false;
    viewSolo.hidden = true;
  } else {
    tabSolo.classList.add('active');
    tabChat.classList.remove('active');
    viewSolo.hidden = false;
    viewChat.hidden = true;
  }
}

if (tabChat && tabSolo) {
  tabChat.addEventListener('click', () => switchTab('chat'));
  tabSolo.addEventListener('click', () => switchTab('solo'));
}

// ---------------- Theme Management ----------------
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem('emojify-theme', theme);
  const themeToggle = document.querySelector('#theme-toggle');
  if (themeToggle) {
    themeToggle.textContent = theme === 'dark' ? '☾' : '☼';
  }
}
setTheme(localStorage.getItem('emojify-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
const themeBtn = document.querySelector('#theme-toggle');
if (themeBtn) {
  themeBtn.addEventListener('click', () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'));
}

// ---------------- 2-Person Chat Room Logic ----------------
let socket = null;
let currentRoomId = document.body.dataset.initialRoom || "";

const contactDisplayName = document.querySelector('#contact-display-name');
const roomStatusText = document.querySelector('#room-status-text');
const roomStatusDot = document.querySelector('#room-status-dot');
const roomParticipantsBadge = document.querySelector('#room-participants-badge');
const btnCreateRoom = document.querySelector('#btn-create-room');
const btnCopyRoom = document.querySelector('#btn-copy-room');
const inviteBanner = document.querySelector('#invite-banner');
const inviteLinkInput = document.querySelector('#invite-link-input');
const btnCopyInvite = document.querySelector('#btn-copy-invite');
const btnOpenTab = document.querySelector('#btn-open-tab');
const btnNativeShare = document.querySelector('#btn-native-share');
const copyToast = document.querySelector('#copy-toast');
const chatMessages = document.querySelector('#chat-messages');
const chatEmpty = document.querySelector('#chat-empty');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const chatSend = document.querySelector('#chat-send');

// Show native share button on mobile / supported devices
if (navigator.share && btnNativeShare) {
  btnNativeShare.hidden = false;
}

function updateInviteBanner(count = 1) {
  if (!currentRoomId) {
    if (inviteBanner) inviteBanner.hidden = true;
    if (contactDisplayName) contactDisplayName.textContent = 'Emoji Messages';
    if (roomStatusText) roomStatusText.textContent = 'iMessage • No room active';
    return;
  }
  const roomUrl = `${window.location.origin}/room/${currentRoomId}`;
  if (inviteLinkInput) inviteLinkInput.value = roomUrl;

  if (contactDisplayName) contactDisplayName.textContent = `Room #${currentRoomId}`;
  if (roomStatusText) {
    roomStatusText.textContent = count >= 2 ? 'iMessage • 2/2 Online' : 'iMessage • Waiting for friend (1/2)';
  }

  // Show invite banner if only 1 person online
  if (inviteBanner) {
    inviteBanner.hidden = count >= 2;
  }
}

function initSocket() {
  if (socket) return;
  if (typeof io === 'undefined') {
    console.warn('Socket.IO not loaded. Falling back to HTTP.');
    return;
  }

  try {
    socket = io(window.location.origin);

    socket.on('connect', () => {
      if (currentRoomId) {
        joinRoom(currentRoomId);
      }
    });

    socket.on('room_joined', (data) => {
      if (roomStatusDot) roomStatusDot.className = 'status-indicator-dot connected';
      if (roomParticipantsBadge) {
        roomParticipantsBadge.textContent = `${data.participant_count}/2 Online`;
        roomParticipantsBadge.hidden = false;
      }
      if (btnCopyRoom) btnCopyRoom.hidden = false;
      if (btnCreateRoom) btnCreateRoom.textContent = '⚡ New Room';

      updateInviteBanner(data.participant_count);

      // Render past message history
      if (data.messages && data.messages.length > 0 && chatMessages) {
        if (chatEmpty) chatEmpty.hidden = true;
        chatMessages.querySelectorAll('.chat-bubble-row').forEach(el => el.remove());
        data.messages.forEach(msg => appendMessageBubble({
          is_self: msg.sender_sid === socket.id,
          original_text: msg.original_text,
          emojis: msg.emojis,
        }));
      }
    });

    socket.on('peer_joined', (data) => {
      if (roomParticipantsBadge) roomParticipantsBadge.textContent = `${data.participant_count}/2 Online`;
      updateInviteBanner(data.participant_count);
    });

    socket.on('peer_left', (data) => {
      if (roomParticipantsBadge) roomParticipantsBadge.textContent = `${data.participant_count}/2 Online`;
      updateInviteBanner(data.participant_count);
    });

    socket.on('message_sent', (data) => {
      appendMessageBubble(data);
      if (chatSend) chatSend.disabled = false;
      if (chatInput) {
        chatInput.value = '';
        chatInput.focus();
      }
    });

    socket.on('message_received', (data) => {
      appendMessageBubble(data);
    });

    socket.on('error', (err) => {
      console.error('Socket error:', err);
      if (chatSend) chatSend.disabled = false;
    });
  } catch (err) {
    console.warn('Socket init failed:', err);
  }
}

function joinRoom(roomId) {
  currentRoomId = roomId;
  if (!socket) initSocket();
  if (socket) {
    socket.emit('join_room', { room_id: roomId });
  }
  window.history.pushState({}, '', `/room/${roomId}`);
  updateInviteBanner(1);
}

async function createRoom() {
  try {
    const res = await fetch('/api/rooms', { method: 'POST', headers: { 'Content-Type': 'application/json' } });
    const data = await res.json();
    if (data.room_id) {
      joinRoom(data.room_id);
    }
  } catch (err) {
    alert('Could not create room. Try again.');
  }
}

if (btnCreateRoom) btnCreateRoom.addEventListener('click', createRoom);

// Copy action with multi-tier fallback
async function copyLinkAction() {
  const roomUrl = currentRoomId ? `${window.location.origin}/room/${currentRoomId}` : window.location.href;

  let success = false;
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(roomUrl);
      success = true;
    } catch (e) {}
  }

  if (!success && inviteLinkInput) {
    inviteLinkInput.focus();
    inviteLinkInput.select();
    try {
      success = document.execCommand('copy');
    } catch (e) {}
  }

  if (btnCopyInvite) {
    btnCopyInvite.textContent = '✓ Copied!';
    setTimeout(() => { btnCopyInvite.textContent = '📋 Copy Link'; }, 2000);
  }
  if (copyToast) {
    copyToast.hidden = false;
    setTimeout(() => { copyToast.hidden = true; }, 3000);
  }
}

if (btnCopyInvite) btnCopyInvite.addEventListener('click', copyLinkAction);
if (btnCopyRoom) btnCopyRoom.addEventListener('click', copyLinkAction);

if (inviteLinkInput) {
  inviteLinkInput.addEventListener('click', () => inviteLinkInput.select());
}

if (btnOpenTab) {
  btnOpenTab.addEventListener('click', () => {
    const roomUrl = currentRoomId ? `${window.location.origin}/room/${currentRoomId}` : window.location.href;
    window.open(roomUrl, '_blank');
  });
}

if (btnNativeShare) {
  btnNativeShare.addEventListener('click', async () => {
    const roomUrl = currentRoomId ? `${window.location.origin}/room/${currentRoomId}` : window.location.href;
    try {
      await navigator.share({
        title: 'Emojify Messages',
        text: 'Chat with me in Apple iOS emojis on Emojify!',
        url: roomUrl,
      });
    } catch (err) {
      copyLinkAction();
    }
  });
}

function appendMessageBubble(data) {
  if (chatEmpty) chatEmpty.hidden = true;
  if (!chatMessages) return;

  const bubbleRow = document.createElement('div');
  bubbleRow.className = `chat-bubble-row ${data.is_self ? 'self' : 'other'}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble-content';
  bubble.textContent = data.emojis;

  bubbleRow.appendChild(bubble);

  // Subtitle / Delivery receipt
  const subtitle = document.createElement('div');
  subtitle.className = 'bubble-subtitle';
  if (data.is_self) {
    subtitle.textContent = data.original_text ? `${data.original_text} • Delivered` : 'Delivered';
  } else {
    subtitle.textContent = 'Received';
  }
  bubbleRow.appendChild(subtitle);

  chatMessages.appendChild(bubbleRow);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

if (chatForm) {
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!chatInput) return;
    const text = chatInput.value.trim();
    if (!text) return;

    if (!currentRoomId) {
      createRoom().then(() => {
        setTimeout(() => {
          if (socket) socket.emit('send_message', { room_id: currentRoomId, text });
        }, 300);
      });
      return;
    }

    if (chatSend) chatSend.disabled = true;
    if (socket) {
      socket.emit('send_message', { room_id: currentRoomId, text });
    } else {
      fetch('/api/translate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      })
      .then(res => res.json())
      .then(data => {
        appendMessageBubble({ is_self: true, original_text: text, emojis: data.emojis });
        if (chatSend) chatSend.disabled = false;
        chatInput.value = '';
      })
      .catch(err => {
        if (chatSend) chatSend.disabled = false;
        alert(err.message || 'Translation error');
      });
    }
  });
}

// Auto-join on load if URL has room ID
initSocket();

// ---------------- Solo Translator Mode ----------------
const message = document.querySelector('#message');
const submit = document.querySelector('#submit');
const submitLabel = document.querySelector('#submit-label');
const error = document.querySelector('#error');
const resultCard = document.querySelector('#result-card');
const result = document.querySelector('#result');
const concepts = document.querySelector('#concepts');
const emotion = document.querySelector('#emotion');
const explanation = document.querySelector('#explanation');
const count = document.querySelector('#count');

const clientCache = new Map();

if (message && count) {
  message.addEventListener('input', () => {
    count.textContent = `${message.value.length} / ${message.maxLength}`;
  });
}

function showError(text) {
  if (error) {
    error.textContent = text;
    error.hidden = false;
  }
}

function renderSolo(data) {
  if (!result || !resultCard) return;
  result.textContent = data.emojis;
  if (concepts) {
    concepts.replaceChildren(...(data.concepts || []).map(item => {
      const li = document.createElement('li');
      li.textContent = `${item.emoji} ${item.name}`;
      return li;
    }));
  }
  if (emotion) emotion.textContent = data.emotion || 'None';
  if (explanation) explanation.textContent = data.explanation || 'Semantic mapping completed.';
  resultCard.hidden = false;
  resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function translateSolo() {
  if (!message) return;
  const text = message.value.trim();
  if (!text) {
    showError("Write something first — even a tiny thought counts.");
    return;
  }

  if (error) error.hidden = true;
  const cacheKey = text.toLowerCase();

  if (clientCache.has(cacheKey)) {
    renderSolo(clientCache.get(cacheKey));
    return;
  }

  if (submit && submitLabel) {
    submit.disabled = true;
    submitLabel.textContent = 'THINKING…';
  }

  try {
    const response = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Something went sideways.');

    clientCache.set(cacheKey, data);
    renderSolo(data);
  } catch (err) {
    showError(err.message || 'Could not contact Emojify.');
  } finally {
    if (submit && submitLabel) {
      submit.disabled = false;
      submitLabel.textContent = 'EMOJIFY THOUGHT';
    }
  }
}

if (submit) {
  submit.addEventListener('click', translateSolo);
}
if (message) {
  message.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') translateSolo();
  });
}

const copyBtn = document.querySelector('#copy');
if (copyBtn) {
  copyBtn.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(result.textContent);
      copyBtn.textContent = '✓ Copied';
      setTimeout(() => { copyBtn.textContent = '⧉ Copy'; }, 1500);
    } catch {
      showError('Copy is unavailable in this browser. Select the result and copy it manually.');
    }
  });
}
