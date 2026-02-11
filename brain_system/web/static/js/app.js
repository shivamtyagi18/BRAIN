// ============================
// Brain System — Frontend Logic
// ============================

const API = {
    init: (data) => fetch('/api/init', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) }).then(r => r.json()),
    chat: (msg) => fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: msg }) }).then(r => r.json()),
    persona: (file) => { const fd = new FormData(); fd.append('file', file); return fetch('/api/persona', { method: 'POST', body: fd }).then(r => r.json()); },
    clearPersona: () => fetch('/api/persona/clear', { method: 'POST' }).then(r => r.json()),
    config: () => fetch('/api/config').then(r => r.json()),
};

// State
let selectedProvider = 'ollama';
let isBusy = false;

// DOM Elements
const $ = (sel) => document.querySelector(sel);
const setupModal = $('#setup-modal');
const stepProvider = $('#step-provider');
const stepPersona = $('#step-persona');
const stepLoading = $('#step-loading');
const chatContainer = $('#chat-container');
const messagesDiv = $('#messages');
const userInput = $('#user-input');
const btnSend = $('#btn-send');
const loadingText = $('#loading-text');

// ============================
// Provider Selection
// ============================

document.querySelectorAll('.provider-card').forEach(card => {
    card.addEventListener('click', () => {
        document.querySelectorAll('.provider-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedProvider = card.dataset.provider;

        const modelGroup = $('#model-name-group');
        if (selectedProvider === 'ollama') {
            modelGroup.style.display = 'block';
        } else {
            modelGroup.style.display = 'none';
        }
    });
});

// Initialize Brain
$('#btn-init').addEventListener('click', async () => {
    const modelName = $('#model-name').value.trim() || null;

    showStep('loading');
    loadingText.textContent = 'Initializing neural pathways...';

    try {
        const res = await API.init({ provider: selectedProvider, model_name: modelName });
        if (res.status === 'ok') {
            // Update sidebar info
            $('#info-provider').textContent = selectedProvider;
            $('#info-model').textContent = modelName || 'default';

            loadingText.textContent = 'Brain initialized! Loading persona options...';
            setTimeout(() => showStep('persona'), 600);
        } else {
            alert('Error: ' + res.message);
            showStep('provider');
        }
    } catch (e) {
        alert('Failed to connect to server: ' + e.message);
        showStep('provider');
    }
});

// ============================
// Persona Upload
// ============================

const uploadZone = $('#upload-zone');
const fileInput = $('#file-input');
const uploadStatus = $('#upload-status');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileUpload(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFileUpload(fileInput.files[0]);
    }
});

async function handleFileUpload(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['txt', 'pdf'].includes(ext)) {
        uploadStatus.textContent = '❌ Unsupported file type. Use .txt or .pdf';
        uploadStatus.className = 'upload-status error';
        return;
    }

    uploadStatus.textContent = '📖 Loading and analyzing document...';
    uploadStatus.className = 'upload-status loading';

    try {
        const res = await API.persona(file);
        if (res.status === 'ok') {
            uploadStatus.textContent = `✅ Persona loaded: ${res.persona_name}`;
            uploadStatus.className = 'upload-status success';

            $('#info-persona').textContent = res.persona_name;
            $('#persona-badge').classList.remove('hidden');
            $('#persona-name-badge').textContent = res.persona_name;
            $('#chat-title').textContent = `🎭 ${res.persona_name}`;

            setTimeout(() => enterChat(), 1000);
        } else {
            uploadStatus.textContent = `❌ ${res.message}`;
            uploadStatus.className = 'upload-status error';
        }
    } catch (e) {
        uploadStatus.textContent = `❌ Upload failed: ${e.message}`;
        uploadStatus.className = 'upload-status error';
    }
}

// Skip persona
$('#btn-skip-persona').addEventListener('click', () => enterChat());

// ============================
// Chat Interface
// ============================

function enterChat() {
    setupModal.classList.remove('active');
    chatContainer.classList.remove('hidden');
    userInput.focus();
}

function showStep(step) {
    stepProvider.classList.remove('active');
    stepPersona.classList.remove('active');
    stepLoading.classList.remove('active');

    if (step === 'provider') stepProvider.classList.add('active');
    if (step === 'persona') stepPersona.classList.add('active');
    if (step === 'loading') stepLoading.classList.add('active');
}

// Auto-resize textarea
userInput.addEventListener('input', () => {
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    btnSend.disabled = !userInput.value.trim() || isBusy;
});

// Send message
btnSend.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (!btnSend.disabled) sendMessage();
    }
});

async function sendMessage() {
    const msg = userInput.value.trim();
    if (!msg || isBusy) return;

    isBusy = true;
    btnSend.disabled = true;
    userInput.value = '';
    userInput.style.height = 'auto';

    // Remove welcome message
    const welcome = messagesDiv.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user message
    addMessage('user', msg);

    // Show thinking indicator
    const thinkingEl = showThinking();

    // Animate agent chips
    animateAgents(true);

    try {
        const res = await API.chat(msg);
        thinkingEl.remove();
        animateAgents(false);

        if (res.status === 'ok') {
            addMessage('brain', res.response, res.agent_outputs);
        } else {
            addMessage('brain', `⚠️ Error: ${res.message}`);
        }
    } catch (e) {
        thinkingEl.remove();
        animateAgents(false);
        addMessage('brain', `⚠️ Connection error: ${e.message}`);
    }

    isBusy = false;
    btnSend.disabled = !userInput.value.trim();
    userInput.focus();
}

function addMessage(role, text, agentOutputs) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const avatar = role === 'user' ? '👤' : '🧠';

    // Simple markdown-like formatting
    const formatted = text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');

    let agentPanelsHTML = '';
    if (role === 'brain' && agentOutputs) {
        const agentOrder = ['sensory', 'memory', 'logic', 'emotional', 'executive'];
        const panelItems = agentOrder.map(key => {
            const agent = agentOutputs[key];
            if (!agent) return '';
            return `
                <div class="agent-panel" data-agent="${key}">
                    <button class="agent-panel-header" onclick="this.parentElement.classList.toggle('open')">
                        <span class="agent-panel-dot ${key}"></span>
                        <span class="agent-panel-name">${agent.name}</span>
                        <span class="agent-panel-role">${agent.role}</span>
                        <span class="agent-panel-chevron">▼</span>
                    </button>
                    <div class="agent-panel-body">${agent.output}</div>
                </div>
            `;
        }).join('');

        agentPanelsHTML = `
            <div class="agent-panels">
                <button class="agent-panels-toggle" onclick="toggleAgentPanels(this)">
                    🧩 Show agent signals <span class="chevron">▼</span>
                </button>
                <div class="agent-panels-content">
                    ${panelItems}
                </div>
            </div>
        `;
    }

    div.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-body">${formatted}${agentPanelsHTML}</div>
    `;

    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function toggleAgentPanels(btn) {
    btn.classList.toggle('open');
    const content = btn.nextElementSibling;
    content.classList.toggle('open');
    btn.innerHTML = content.classList.contains('open')
        ? '🧩 Hide agent signals <span class="chevron">▼</span>'
        : '🧩 Show agent signals <span class="chevron">▼</span>';
}

function showThinking() {
    const div = document.createElement('div');
    div.className = 'thinking';
    div.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="thinking-dots">
            <span></span><span></span><span></span>
        </div>
        <span class="thinking-text">Processing through 5 brain agents...</span>
    `;
    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return div;
}

function animateAgents(active) {
    document.querySelectorAll('.agent-chip').forEach((chip, i) => {
        if (active) {
            setTimeout(() => chip.classList.add('active'), i * 200);
        } else {
            chip.classList.remove('active');
        }
    });
}

// ============================
// Sidebar Actions
// ============================

$('#btn-change-persona').addEventListener('click', () => {
    const overlay = document.createElement('div');
    overlay.className = 'persona-overlay';
    overlay.innerHTML = `
        <div class="modal-content">
            <h2 style="margin-bottom: 16px;">🎭 Change Persona</h2>
            <div class="upload-zone" id="overlay-upload-zone">
                <div class="upload-icon">📄</div>
                <p>Drop a <strong>.txt</strong> or <strong>.pdf</strong> file here</p>
                <p class="upload-hint">or click to browse</p>
                <input type="file" id="overlay-file-input" accept=".txt,.pdf" hidden>
            </div>
            <div id="overlay-upload-status" class="upload-status"></div>
            <button class="btn-secondary" id="overlay-cancel" style="margin-top: 8px;">Cancel</button>
        </div>
    `;
    document.body.appendChild(overlay);

    const zone = overlay.querySelector('#overlay-upload-zone');
    const input = overlay.querySelector('#overlay-file-input');
    const status = overlay.querySelector('#overlay-upload-status');

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        if (e.dataTransfer.files.length) overlayUpload(e.dataTransfer.files[0], status, overlay);
    });
    input.addEventListener('change', () => { if (input.files.length) overlayUpload(input.files[0], status, overlay); });
    overlay.querySelector('#overlay-cancel').addEventListener('click', () => overlay.remove());
});

async function overlayUpload(file, statusEl, overlay) {
    statusEl.textContent = '📖 Analyzing document...';
    statusEl.className = 'upload-status loading';
    try {
        const res = await API.persona(file);
        if (res.status === 'ok') {
            statusEl.textContent = `✅ Now responding as: ${res.persona_name}`;
            statusEl.className = 'upload-status success';
            $('#info-persona').textContent = res.persona_name;
            $('#persona-badge').classList.remove('hidden');
            $('#persona-name-badge').textContent = res.persona_name;
            $('#chat-title').textContent = `🎭 ${res.persona_name}`;
            setTimeout(() => overlay.remove(), 1000);
        } else {
            statusEl.textContent = `❌ ${res.message}`;
            statusEl.className = 'upload-status error';
        }
    } catch (e) {
        statusEl.textContent = `❌ ${e.message}`;
        statusEl.className = 'upload-status error';
    }
}

$('#btn-clear-persona').addEventListener('click', async () => {
    const res = await API.clearPersona();
    if (res.status === 'ok') {
        $('#info-persona').textContent = 'None';
        $('#persona-badge').classList.add('hidden');
        $('#chat-title').textContent = '🧠 Brain System';
    }
});
