window.pharma_vn = window.pharma_vn || {};

(() => {
  const AI_METHOD = "pharma_vn.api.ai_assistant.chat";
  const BOOTSTRAP_METHOD = "pharma_vn.api.ai_assistant.get_bootstrap";
  const MAX_HISTORY = 8;
  const PANEL_ID = "pharma-ai-assistant";
  const STYLE_ID = "pharma-ai-assistant-inline-style";
  const INPUT_ID = "pharma-ai-assistant-input";
  const STATIC_DATE_LABEL = "October 15, 2024";
  const POSITION_STORAGE_PREFIX = "pharma-ai-assistant-position";
  const DRAG_THRESHOLD = 6;
  const VIEWPORT_PADDING = 16;

  const INLINE_STYLES = `
    #${PANEL_ID}.pharma-ai-assistant {
      --chat-purple: #7c3aed;
      --chat-purple-soft: #a855f7;
      --chat-purple-ghost: rgba(124, 58, 237, 0.12);
      --chat-text: #18181b;
      --chat-muted: #7c7c88;
      --chat-line: rgba(24, 24, 27, 0.1);
      --chat-panel: rgba(255, 255, 255, 0.94);
      --chat-shadow: 0 28px 70px rgba(124, 58, 237, 0.18);
      position: fixed !important;
      right: 20px;
      bottom: 20px;
      z-index: 1040;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 14px;
      pointer-events: none;
      font-family: "SF Pro Display", "Inter", "Segoe UI", sans-serif;
    }

    #${PANEL_ID}.pharma-ai-assistant * {
      box-sizing: border-box;
    }

    #${PANEL_ID}.pharma-ai-assistant button,
    #${PANEL_ID}.pharma-ai-assistant textarea {
      font: inherit;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__panel,
    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger {
      pointer-events: auto;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__panel {
      width: min(530px, calc(100vw - 28px));
      min-height: 680px;
      max-height: min(82vh, 760px);
      display: flex;
      flex-direction: column;
      border: 1px solid rgba(255, 255, 255, 0.62);
      border-radius: 28px;
      overflow: hidden;
      background:
        radial-gradient(circle at top, rgba(216, 180, 254, 0.54), transparent 42%),
        linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(252, 250, 255, 0.98));
      box-shadow: var(--chat-shadow);
      backdrop-filter: blur(20px);
      opacity: 0;
      visibility: hidden;
      transform: translateY(16px) scale(0.985);
      transition: opacity 180ms ease, transform 180ms ease, visibility 180ms ease;
    }

    #${PANEL_ID}.pharma-ai-assistant.pharma-ai-assistant--open .pharma-ai-assistant__panel {
      opacity: 1;
      visibility: visible;
      transform: translateY(0) scale(1);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__header {
      padding: 24px 28px 16px;
      border-bottom: 1px solid rgba(24, 24, 27, 0.06);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 255, 255, 0.88));
      cursor: grab;
      user-select: none;
      touch-action: none;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__header-row {
      display: flex;
      align-items: center;
      gap: 14px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__icon {
      width: 44px;
      height: 44px;
      border: none;
      border-radius: 18px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, var(--chat-purple), #5b21b6);
      color: #ffffff;
      font-size: 15px;
      font-weight: 700;
      flex-shrink: 0;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__brand {
      min-width: 0;
      flex: 1;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__eyebrow {
      margin: 0 0 2px;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #5b21b6;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__title {
      margin: 0;
      font-size: 20px;
      font-weight: 800;
      color: var(--chat-text);
      line-height: 1.1;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__header-actions {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__icon-button {
      width: 36px;
      height: 36px;
      border: none;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.9);
      color: var(--chat-muted);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 8px 18px rgba(124, 58, 237, 0.08);
      transition: transform 120ms ease, color 120ms ease, background 120ms ease;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__icon-button:hover {
      transform: translateY(-1px);
      background: rgba(255, 255, 255, 1);
      color: var(--chat-purple);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__status {
      padding: 12px 28px 8px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      font-weight: 600;
      color: #676772;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: #10b981;
      box-shadow: 0 0 0 6px rgba(16, 185, 129, 0.12);
      flex-shrink: 0;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__divider {
      padding: 0 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      color: #a1a1aa;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.02em;
      text-align: center;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__divider::before,
    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__divider::after {
      content: "";
      flex: 1;
      height: 1px;
      background: rgba(24, 24, 27, 0.08);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__messages {
      flex: 1;
      min-height: 220px;
      padding: 16px 24px 10px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
      scrollbar-width: thin;
      scrollbar-color: rgba(24, 24, 27, 0.14) transparent;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__messages::-webkit-scrollbar {
      width: 8px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__messages::-webkit-scrollbar-thumb {
      border-radius: 999px;
      background: rgba(24, 24, 27, 0.12);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-row {
      display: flex;
      width: 100%;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-row--user {
      justify-content: flex-end;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-row--assistant {
      justify-content: flex-start;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-bubble {
      max-width: 82%;
      padding: 20px 22px;
      border-radius: 24px;
      font-size: 14px;
      line-height: 1.5;
      color: var(--chat-text);
      word-break: break-word;
      box-shadow: 0 20px 44px rgba(124, 58, 237, 0.08);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-row--assistant .pharma-ai-assistant__message-bubble {
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(249, 250, 251, 0.96));
      border-top-left-radius: 12px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-row--user .pharma-ai-assistant__message-bubble {
      color: #ffffff;
      background: linear-gradient(135deg, #7c3aed, #9333ea 45%, #5b21b6);
      border-top-right-radius: 12px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-actions {
      margin-top: 14px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__action {
      border: 1px solid rgba(124, 58, 237, 0.18);
      border-radius: 999px;
      padding: 8px 12px;
      background: rgba(124, 58, 237, 0.08);
      color: var(--chat-purple);
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 120ms ease, background 120ms ease;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__action:hover {
      transform: translateY(-1px);
      background: rgba(124, 58, 237, 0.13);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__composer {
      padding: 14px 24px 22px;
      border-top: 1px solid rgba(24, 24, 27, 0.06);
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.96));
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__input-shell {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px 10px 8px 18px;
      border-radius: 999px;
      background: linear-gradient(180deg, rgba(245, 245, 245, 0.92), rgba(255, 255, 255, 0.92));
      border: 1px solid rgba(24, 24, 27, 0.06);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__textarea {
      min-height: 26px;
      max-height: 110px;
      flex: 1;
      border: none;
      outline: none;
      resize: none;
      background: transparent;
      color: var(--chat-text);
      font-size: 15px;
      line-height: 1.45;
      overflow-y: auto;
      padding: 6px 0;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__textarea::placeholder {
      color: #a1a1aa;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__send {
      width: 48px;
      height: 48px;
      border: none;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #7c3aed, #9333ea);
      color: #ffffff;
      cursor: pointer;
      box-shadow: 0 14px 26px rgba(124, 58, 237, 0.24);
      transition: transform 120ms ease, opacity 120ms ease;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__send:hover:not(:disabled) {
      transform: translateY(-1px);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__send:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__composer-meta {
      margin-top: 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__aux-actions {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      color: #b0b0bb;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__aux-button {
      border: none;
      background: transparent;
      color: inherit;
      cursor: pointer;
      padding: 0;
      font-size: 22px;
      line-height: 1;
      transition: color 120ms ease, transform 120ms ease;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__aux-button:hover {
      color: var(--chat-purple);
      transform: translateY(-1px);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__hint {
      font-size: 12px;
      color: var(--chat-muted);
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px 10px 10px;
      border: none;
      border-radius: 999px;
      background: linear-gradient(135deg, #ffffff, rgba(255, 255, 255, 0.84));
      color: var(--chat-text);
      box-shadow: 0 18px 44px rgba(124, 58, 237, 0.18);
      cursor: pointer;
      transition: transform 140ms ease, box-shadow 140ms ease;
      backdrop-filter: blur(16px);
      user-select: none;
      touch-action: none;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger:hover {
      transform: translateY(-1px);
    }

    #${PANEL_ID}.pharma-ai-assistant.pharma-ai-assistant--dragging .pharma-ai-assistant__header,
    #${PANEL_ID}.pharma-ai-assistant.pharma-ai-assistant--dragging .pharma-ai-assistant__trigger {
      cursor: grabbing;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger-icon {
      width: 42px;
      height: 42px;
      border-radius: 999px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #7c3aed, #5b21b6);
      color: #ffffff;
      font-size: 15px;
      font-weight: 700;
      flex-shrink: 0;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger-copy {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 2px;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger-label {
      font-size: 11px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      font-weight: 700;
      color: #8b5cf6;
    }

    #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__trigger-title {
      font-size: 15px;
      font-weight: 800;
      color: var(--chat-text);
    }

    @media (max-width: 768px) {
      #${PANEL_ID}.pharma-ai-assistant {
        right: 12px;
        left: 12px;
        bottom: 12px;
      }

      #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__panel {
        width: 100%;
        min-height: min(78vh, 620px);
      }

      #${PANEL_ID}.pharma-ai-assistant .pharma-ai-assistant__message-bubble {
        max-width: 92%;
      }

    }
  `;

  const state = {
    isMounted: false,
    isOpen: false,
    isLoading: false,
    history: [],
    bootstrap: null,
    position: null,
    drag: {
      active: false,
      pointerId: null,
      startX: 0,
      startY: 0,
      startLeft: 0,
      startTop: 0,
      moved: false,
      suppressClick: false,
    },
  };

  function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, (char) => {
      const map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return map[char] || char;
    });
  }

  function getRoot() {
    return document.getElementById(PANEL_ID);
  }

  function getPositionStorageKey() {
    return `${POSITION_STORAGE_PREFIX}:${frappe?.session?.user || "guest"}`;
  }

  function loadSavedPosition() {
    try {
      const rawValue = window.localStorage.getItem(getPositionStorageKey());
      if (!rawValue) {
        return null;
      }
      const parsed = JSON.parse(rawValue);
      const left = Number(parsed?.left);
      const top = Number(parsed?.top);
      if (!Number.isFinite(left) || !Number.isFinite(top)) {
        return null;
      }
      return { left, top };
    } catch (error) {
      return null;
    }
  }

  function savePosition(position) {
    if (!position) {
      return;
    }
    try {
      window.localStorage.setItem(getPositionStorageKey(), JSON.stringify(position));
    } catch (error) {
      // Keep widget usable even if storage fails.
    }
  }

  function getRootRect(root) {
    const rect = root?.getBoundingClientRect?.();
    if (!rect) {
      return { width: 0, height: 0, left: 0, top: 0 };
    }
    return {
      width: rect.width || root.offsetWidth || 0,
      height: rect.height || root.offsetHeight || 0,
      left: rect.left || 0,
      top: rect.top || 0,
    };
  }

  function clampPosition(root, left, top) {
    const rect = getRootRect(root);
    const maxLeft = Math.max(VIEWPORT_PADDING, window.innerWidth - rect.width - VIEWPORT_PADDING);
    const maxTop = Math.max(VIEWPORT_PADDING, window.innerHeight - rect.height - VIEWPORT_PADDING);
    return {
      left: Math.min(Math.max(VIEWPORT_PADDING, left), maxLeft),
      top: Math.min(Math.max(VIEWPORT_PADDING, top), maxTop),
    };
  }

  function applyPosition(root, position) {
    if (!root || !position) {
      return;
    }
    const safePosition = clampPosition(root, Number(position.left) || 0, Number(position.top) || 0);
    root.style.left = `${safePosition.left}px`;
    root.style.top = `${safePosition.top}px`;
    root.style.right = "auto";
    root.style.bottom = "auto";
    state.position = safePosition;
  }

  function syncPosition(root, persist = false) {
    if (!root || !state.position) {
      return;
    }
    applyPosition(root, state.position);
    if (persist) {
      savePosition(state.position);
    }
  }

  function handleDragMove(event) {
    if (!state.drag.active || event.pointerId !== state.drag.pointerId) {
      return;
    }
    const root = getRoot();
    if (!root) {
      return;
    }
    const deltaX = event.clientX - state.drag.startX;
    const deltaY = event.clientY - state.drag.startY;
    if (!state.drag.moved && (Math.abs(deltaX) >= DRAG_THRESHOLD || Math.abs(deltaY) >= DRAG_THRESHOLD)) {
      state.drag.moved = true;
      root.classList.add("pharma-ai-assistant--dragging");
    }
    if (!state.drag.moved) {
      return;
    }
    const nextPosition = clampPosition(root, state.drag.startLeft + deltaX, state.drag.startTop + deltaY);
    applyPosition(root, nextPosition);
  }

  function stopDrag(event) {
    if (!state.drag.active || (event && event.pointerId !== state.drag.pointerId)) {
      return;
    }
    const root = getRoot();
    if (root) {
      root.classList.remove("pharma-ai-assistant--dragging");
    }
    if (state.drag.moved) {
      state.drag.suppressClick = true;
      savePosition(state.position);
    }
    state.drag.active = false;
    state.drag.pointerId = null;
    state.drag.startX = 0;
    state.drag.startY = 0;
    state.drag.startLeft = 0;
    state.drag.startTop = 0;
    state.drag.moved = false;
    window.removeEventListener("pointermove", handleDragMove);
    window.removeEventListener("pointerup", stopDrag);
    window.removeEventListener("pointercancel", stopDrag);
  }

  function startDrag(event) {
    if (event.button !== 0) {
      return;
    }
    if (
      event.target.closest(
        ".pharma-ai-assistant__close, .pharma-ai-assistant__refresh, .pharma-ai-assistant__send, .pharma-ai-assistant__action, .pharma-ai-assistant__textarea, .pharma-ai-assistant__aux-button",
      )
    ) {
      return;
    }
    const root = getRoot();
    if (!root) {
      return;
    }
    const rect = getRootRect(root);
    state.drag.active = true;
    state.drag.pointerId = event.pointerId;
    state.drag.startX = event.clientX;
    state.drag.startY = event.clientY;
    state.drag.startLeft = rect.left;
    state.drag.startTop = rect.top;
    state.drag.moved = false;
    if (!state.position) {
      state.position = { left: rect.left, top: rect.top };
    }
    window.addEventListener("pointermove", handleDragMove);
    window.addEventListener("pointerup", stopDrag);
    window.addEventListener("pointercancel", stopDrag);
  }

  function bindDragHandles(root) {
    root.querySelector(".pharma-ai-assistant__trigger")?.addEventListener("pointerdown", startDrag);
    root.querySelector(".pharma-ai-assistant__header")?.addEventListener("pointerdown", startDrag);
  }

  function getStatusText() {
    if (!state.bootstrap) {
      return "We’re loading ...";
    }
    if (!state.bootstrap.enabled) {
      return "Assistant is disabled.";
    }
    if (!state.bootstrap.configured) {
      return "OpenAI API key is missing.";
    }
    return `Connected to ${state.bootstrap.model || "OpenAI"}.`;
  }

  function ensureStyles() {
    if (document.getElementById(STYLE_ID)) {
      return;
    }
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = INLINE_STYLES;
    document.head.appendChild(style);
  }

  function ensureRoot() {
    ensureStyles();
    let root = getRoot();
    if (root) {
      return root;
    }

    root = document.createElement("div");
    root.id = PANEL_ID;
    root.className = "pharma-ai-assistant";
    root.innerHTML = `
      <section class="pharma-ai-assistant__panel" aria-label="AI Assistant">
        <header class="pharma-ai-assistant__header">
          <div class="pharma-ai-assistant__header-row">
            <div class="pharma-ai-assistant__icon">AI</div>
            <div class="pharma-ai-assistant__brand">
              <div class="pharma-ai-assistant__eyebrow">Desk Copilot</div>
              <h3 class="pharma-ai-assistant__title">ERPNext Bot</h3>
            </div>
            <div class="pharma-ai-assistant__header-actions">
              <button class="pharma-ai-assistant__icon-button pharma-ai-assistant__refresh" type="button" aria-label="Refresh assistant">↻</button>
              <button class="pharma-ai-assistant__icon-button pharma-ai-assistant__close" type="button" aria-label="Minimize assistant">×</button>
            </div>
          </div>
        </header>
        <div class="pharma-ai-assistant__status">
          <span class="pharma-ai-assistant__status-dot"></span>
          <span class="pharma-ai-assistant__status-text">We’re loading ...</span>
        </div>
        <div class="pharma-ai-assistant__divider">${STATIC_DATE_LABEL}</div>
        <div class="pharma-ai-assistant__messages"></div>
        <div class="pharma-ai-assistant__composer">
          <div class="pharma-ai-assistant__input-shell">
            <textarea id="${INPUT_ID}" class="pharma-ai-assistant__textarea" rows="1" placeholder="Enter message"></textarea>
            <button class="pharma-ai-assistant__send" type="button" aria-label="Send message">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="M21 3L10 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
                <path d="M21 3L14 21L10 14L3 10L21 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
              </svg>
            </button>
          </div>
          <div class="pharma-ai-assistant__composer-meta">
            <div class="pharma-ai-assistant__aux-actions">
              <button class="pharma-ai-assistant__aux-button" type="button" aria-label="Emoji">☺</button>
              <button class="pharma-ai-assistant__aux-button" type="button" aria-label="Attachment">⌕</button>
            </div>
            <div class="pharma-ai-assistant__hint">Enter to send. Shift+Enter for a new line.</div>
          </div>
        </div>
      </section>
      <button class="pharma-ai-assistant__trigger" type="button" aria-label="Open AI Assistant">
        <span class="pharma-ai-assistant__trigger-icon">AI</span>
        <span class="pharma-ai-assistant__trigger-copy">
          <span class="pharma-ai-assistant__trigger-label">Desk Copilot</span>
          <span class="pharma-ai-assistant__trigger-title">ERPNext Bot</span>
        </span>
      </button>
    `;

    document.body.appendChild(root);
    bindEvents(root);
    bindDragHandles(root);
    return root;
  }

  function autoresizeTextarea(textarea) {
    if (!textarea) {
      return;
    }
    textarea.style.height = "26px";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 110)}px`;
  }

  function renderMessages(root) {
    const messages = root.querySelector(".pharma-ai-assistant__messages");
    messages.innerHTML = state.history
      .map((entry) => {
        const role = entry.role === "user" ? "user" : "assistant";
        const actions = (entry.actions || [])
          .map(
            (action) =>
              `<button class="pharma-ai-assistant__action" type="button" data-route='${escapeHtml(JSON.stringify(action.route || []))}'>${escapeHtml(action.label || "Open")}</button>`,
          )
          .join("");

        return `<div class="pharma-ai-assistant__message-row pharma-ai-assistant__message-row--${role}"><div class="pharma-ai-assistant__message-bubble">${escapeHtml(entry.content || "").replace(/\n/g, "<br>")}${actions ? `<div class="pharma-ai-assistant__message-actions">${actions}</div>` : ""}</div></div>`;
      })
      .join("");

    messages.querySelectorAll(".pharma-ai-assistant__action").forEach((button) => {
      button.addEventListener("click", () => {
        const route = JSON.parse(button.dataset.route || "[]");
        if (route.length) {
          frappe.set_route(...route);
        }
      });
    });

    messages.scrollTop = messages.scrollHeight;
  }

  function render() {
    const root = getRoot();
    if (!root) {
      return;
    }

    root.classList.toggle("pharma-ai-assistant--open", state.isOpen);
    root.querySelector(".pharma-ai-assistant__status-text").textContent = getStatusText();

    const textarea = root.querySelector(".pharma-ai-assistant__textarea");
    const sendButton = root.querySelector(".pharma-ai-assistant__send");
    const ready = Boolean(state.bootstrap?.enabled && state.bootstrap?.configured);
    textarea.disabled = state.isLoading || (Boolean(state.bootstrap) && !ready);
    sendButton.disabled = state.isLoading || !textarea.value.trim() || (Boolean(state.bootstrap) && !ready);

    if (!ready && state.bootstrap) {
      textarea.placeholder = "Configure OPENAI_API_KEY in .env to enable the assistant.";
    } else {
      textarea.placeholder = "Enter message";
    }

    renderMessages(root);
    autoresizeTextarea(textarea);
  }

  function pushMessage(role, content, actions) {
    state.history.push({
      role,
      content,
      actions: actions || [],
    });
    render();
  }

  async function loadBootstrap(force = false) {
    if (state.bootstrap && !force) {
      return state.bootstrap;
    }

    try {
      const response = await frappe.call({
        method: BOOTSTRAP_METHOD,
      });
      state.bootstrap = response?.message?.data || {};
    } catch (error) {
      state.bootstrap = {
        enabled: false,
        configured: false,
        welcome_message: "The assistant could not load its settings.",
        sample_prompts: [],
      };
    }

    if (!state.history.length) {
      pushMessage(
        "assistant",
        state.bootstrap?.welcome_message ||
          "Ask me about sales, purchase, warehouse, invoice flows, stock checks, or let me create customers, draft orders, and reports.",
      );
    } else {
      render();
    }

    return state.bootstrap;
  }

  function compactHistory() {
    return state.history.slice(-MAX_HISTORY).map((entry) => ({
      role: entry.role,
      content: entry.content,
    }));
  }

  async function submitPrompt() {
    const root = getRoot();
    if (!root || state.isLoading) {
      return;
    }

    const textarea = root.querySelector(".pharma-ai-assistant__textarea");
    const message = (textarea.value || "").trim();
    if (!message) {
      return;
    }

    textarea.value = "";
    state.isLoading = true;
    const priorHistory = compactHistory();
    pushMessage("user", message);

    try {
      const response = await frappe.call({
        method: AI_METHOD,
        args: {
          payload: JSON.stringify({
            message,
            history: priorHistory,
          }),
        },
      });
      const data = response?.message?.data || {};
      const actions = [];
      if (data.primary_action?.route) {
        actions.push(data.primary_action);
      }
      (data.secondary_actions || []).forEach((action) => actions.push(action));
      pushMessage(
        "assistant",
        data.reply || "No response received from AI Assistant.",
        actions,
      );
    } catch (error) {
      const messageText =
        error?.message ||
        error?.exc_type ||
        "The assistant could not complete that request.";
      pushMessage("assistant", messageText);
    } finally {
      state.isLoading = false;
      render();
    }
  }

  function resetConversation() {
    state.history = [];
    state.bootstrap = null;
    render();
    loadBootstrap(true);
  }

  function bindEvents(root) {
    const trigger = root.querySelector(".pharma-ai-assistant__trigger");
    const closeButton = root.querySelector(".pharma-ai-assistant__close");
    const refreshButton = root.querySelector(".pharma-ai-assistant__refresh");
    const sendButton = root.querySelector(".pharma-ai-assistant__send");
    const textarea = root.querySelector(".pharma-ai-assistant__textarea");

    trigger.addEventListener("click", async () => {
      if (state.drag.suppressClick) {
        state.drag.suppressClick = false;
        return;
      }
      state.isOpen = !state.isOpen;
      render();
      if (state.isOpen) {
        await loadBootstrap();
        textarea.focus();
      }
    });

    closeButton.addEventListener("click", () => {
      state.isOpen = false;
      render();
    });

    refreshButton.addEventListener("click", () => {
      resetConversation();
    });

    sendButton.addEventListener("click", () => {
      submitPrompt();
    });

    textarea.addEventListener("input", () => {
      autoresizeTextarea(textarea);
      render();
    });

    textarea.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitPrompt();
      }
    });

    document.addEventListener("click", (event) => {
      if (!state.isOpen) {
        return;
      }
      const currentRoot = getRoot();
      if (!currentRoot || currentRoot.contains(event.target)) {
        return;
      }
      state.isOpen = false;
      render();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && state.isOpen) {
        state.isOpen = false;
        render();
      }
    });
  }

  function init() {
    if (!window.frappe || !frappe.session?.user) {
      return;
    }

    if (state.isMounted && getRoot()) {
      render();
      return;
    }

    ensureRoot();
    state.position = state.position || loadSavedPosition();
    state.isMounted = true;
    render();
  }

  if (document.readyState === "interactive" || document.readyState === "complete") {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", () => {
      init();
    });
  }

  $(document).on("app_ready", () => {
    init();
  });

  $(document).on("page-change form-refresh", () => {
    init();
  });

  frappe.router?.on?.("change", () => {
    init();
  });

  window.addEventListener("load", () => {
    init();
  });

  window.addEventListener("resize", () => {
    const root = getRoot();
    if (!root || !state.position) {
      return;
    }
    syncPosition(root, true);
  });
})();
