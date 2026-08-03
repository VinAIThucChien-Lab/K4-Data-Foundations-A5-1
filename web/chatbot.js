const methodConfig = {
  fixed: {
    label: "Fixed Size",
    fields: [
      { key: "chunk_size", label: "Chunk Size (Ký tự)", min: 100, max: 1500, step: 50, value: 500 },
      { key: "overlap", label: "Overlap (Ký tự gối)", min: 0, max: 400, step: 10, value: 50 },
    ],
  },
  sentence: {
    label: "Sentence",
    fields: [{ key: "sentences", label: "Số câu / Chunk", min: 1, max: 10, step: 1, value: 3 }],
  },
  recursive: {
    label: "Recursive",
    fields: [{ key: "chunk_size", label: "Chunk Size (Ký tự)", min: 100, max: 1500, step: 50, value: 500 }],
  },
  custom: {
    label: "Custom / Structured",
    fields: [
      { key: "max_chunk_size", label: "Max Chunk Size", min: 200, max: 2000, step: 100, value: 1000 },
      { key: "min_chunk_size", label: "Min Chunk Size", min: 0, max: 300, step: 10, value: 50 },
    ],
  },
};

const el = (id) => document.getElementById(id);

function showToast(message) {
  const toast = el("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text || "";
  return div.innerHTML;
}

function renderParameters() {
  const container = el("dynamicParameters");
  if (!container) return;
  const method = el("chatMethodSelect").value;
  const config = methodConfig[method] || methodConfig.recursive;

  container.innerHTML = "";
  config.fields.forEach((field) => {
    const wrapper = document.createElement("div");
    wrapper.className = "field-group";
    wrapper.innerHTML = `
      <label for="param-${field.key}">${field.label}</label>
      <div class="slider-with-val">
        <input id="param-${field.key}" data-param="${field.key}" type="range" min="${field.min}" max="${field.max}" step="${field.step}" value="${field.value}">
        <span id="val-${field.key}">${field.value}</span>
      </div>
    `;
    container.appendChild(wrapper);

    const range = wrapper.querySelector("input[type=range]");
    const valDisplay = wrapper.querySelector("span");
    range.addEventListener("input", () => {
      valDisplay.textContent = range.value;
    });
  });
}

function getParameters() {
  const method = el("chatMethodSelect").value;
  const config = methodConfig[method] || methodConfig.recursive;
  const params = {};
  config.fields.forEach((field) => {
    const input = document.querySelector(`[data-param="${field.key}"]`);
    params[field.key] = Number(input?.value ?? field.value);
  });
  return params;
}

async function sendChatMessage(questionText) {
  const text = (questionText || el("chatInput").value).trim();
  if (!text) return;

  const messagesContainer = el("chatMessages");

  // Remove welcome card on first query
  const welcome = messagesContainer.querySelector(".welcome-card");
  if (welcome) welcome.remove();

  // Append user bubble
  const userMsgId = `user-${Date.now()}`;
  messagesContainer.insertAdjacentHTML("beforeend", `
    <div class="chat-bubble user" id="${userMsgId}">
      <div class="bubble-meta">Bạn</div>
      <div class="bubble-body">${escapeHtml(text)}</div>
    </div>
  `);

  el("chatInput").value = "";
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Append bot waiting bubble
  const botMsgId = `bot-${Date.now()}`;
  messagesContainer.insertAdjacentHTML("beforeend", `
    <div class="chat-bubble assistant" id="${botMsgId}">
      <div class="bubble-meta">
        🤖 Shopee RAG Assistant
      </div>
      <div class="bubble-body"><em>Đang thực hiện Chunking, Embedding & truy vấn câu trả lời từ Database...</em></div>
    </div>
  `);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const sendBtn = el("sendBtn");
  sendBtn.disabled = true;

  try {
    const selectedMethod = el("chatMethodSelect").value;
    const scope = el("chatScopeSelect").value;
    const topK = Number(el("chatTopK").value || 3);
    const model = el("chatModelSelect").value || "gpt-4o-mini";

    const bodyPayload = {
      question: text,
      method: selectedMethod,
      parameters: getParameters(),
      top_k: topK,
      model: model,
      document_id: scope === "all" ? null : scope,
      custom_text: null,
    };

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyPayload),
    });

    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Không thể xử lý yêu cầu RAG Chat");

    const botMsg = el(botMsgId);
    if (!botMsg) return;

    let retrievedHtml = "";
    if (payload.retrieved_chunks && payload.retrieved_chunks.length > 0) {
      retrievedHtml = `
        <div class="context-inspector">
          <div class="inspector-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
            <div class="inspector-title">
              <span class="inspector-badge">${payload.retrieved_chunks.length} Chunks Trích Xuất</span>
              <span>Vector Context Inspector (${payload.total_chunks_indexed} chunks trong Database store)</span>
            </div>
            <span>▼</span>
          </div>
          <div class="inspector-body">
            ${payload.retrieved_chunks.map((c, i) => `
              <div class="inspector-chunk">
                <div class="chunk-meta-row">
                  <span>#${i + 1} · ${escapeHtml(c.title || c.doc_id)} (Chunk ${c.chunk_index + 1})</span>
                  <span class="similarity-tag">Độ tương đồng: ${(c.score * 100).toFixed(1)}%</span>
                </div>
                <pre class="chunk-text-content">${escapeHtml(c.content)}</pre>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    const methodName = methodConfig[payload.method]?.label || payload.method;

    botMsg.innerHTML = `
      <div class="bubble-meta">
        🤖 Shopee RAG Assistant
        <span class="meta-badge">Model: ${escapeHtml(payload.model)}</span>
        <span class="meta-badge">Chunking: ${escapeHtml(methodName)}</span>
      </div>
      <div class="bubble-body">${escapeHtml(payload.answer)}</div>
      ${retrievedHtml}
    `;

  } catch (error) {
    const botMsg = el(botMsgId);
    if (botMsg) {
      botMsg.classList.add("error");
      botMsg.querySelector(".bubble-body").textContent = `⚠️ Lỗi RAG Assistant: ${error.message}`;
    }
  } finally {
    sendBtn.disabled = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

async function loadDatabaseDocuments() {
  try {
    const response = await fetch("/api/documents");
    const payload = await response.json();
    const docs = payload.documents || [];

    const scopeSelect = el("chatScopeSelect");
    if (scopeSelect) {
      scopeSelect.innerHTML = `<option value="all">🗄️ Toàn bộ Database (Shopee Returns KB)</option>`;
      docs.forEach((doc) => {
        scopeSelect.insertAdjacentHTML("beforeend", `<option value="${doc.id}">📄 DB: ${doc.title}</option>`);
      });
    }
  } catch (err) {
    showToast("Không thể tải danh sách tài liệu từ Database");
  }
}

async function loadRuntimeStatus() {
  const statusContainer = el("runtimeStatus");
  if (!statusContainer) return;
  try {
    const response = await fetch("/api/status");
    const payload = await response.json();
    const isConfigured = payload.api_key_configured;
    statusContainer.querySelector("span:last-child").textContent = isConfigured
      ? "OpenAI API · Ready"
      : "Local Mode · Chưa cấu hình API Key";
    statusContainer.querySelector(".status-dot").style.background = isConfigured ? "#10b981" : "#f59e0b";
  } catch {
    statusContainer.querySelector("span:last-child").textContent = "API Status Error";
  }
}

// Event Listeners initialization
document.addEventListener("DOMContentLoaded", () => {
  renderParameters();
  loadRuntimeStatus();
  loadDatabaseDocuments();

  el("chatMethodSelect")?.addEventListener("change", renderParameters);

  el("chatTopK")?.addEventListener("input", (e) => {
    el("topKVal").textContent = `${e.target.value} chunks`;
  });

  el("chatForm")?.addEventListener("submit", (e) => {
    e.preventDefault();
    sendChatMessage();
  });

  el("chatInput")?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  document.querySelectorAll(".suggestion-card").forEach((card) => {
    card.addEventListener("click", () => {
      sendChatMessage(card.dataset.prompt);
    });
  });

  el("clearChatBtn")?.addEventListener("click", () => {
    const container = el("chatMessages");
    if (container) {
      container.innerHTML = `
        <div class="welcome-card">
          <div class="welcome-avatar">🤖</div>
          <h2>Xin chào! Tôi là Trợ lý AI Shopee Returns</h2>
          <p>Tôi có thể giúp bạn giải đáp mọi thắc mắc về chính sách Trả hàng/Hoàn tiền, quy trình xử lý, thời hạn và phí vận chuyển dựa trên dữ liệu chuẩn từ Database.</p>

          <div class="suggestion-grid">
            <button class="suggestion-card" type="button" data-prompt="Thời hạn yêu cầu Trả hàng/Hoàn tiền là bao nhiêu ngày?">
              <span class="card-icon">⏱️</span>
              <div class="card-text">
                <strong>Thời hạn trả hàng</strong>
                <span>Số ngày tối đa để gửi yêu cầu</span>
              </div>
            </button>

            <button class="suggestion-card" type="button" data-prompt="Điều kiện để được duyệt trả hàng bị hư hỏng hoặc móp vỡ là gì?">
              <span class="card-icon">📦</span>
              <div class="card-text">
                <strong>Hàng bị hư hỏng</strong>
                <span>Điều kiện và bằng chứng cần có</span>
              </div>
            </button>

            <button class="suggestion-card" type="button" data-prompt="Ai sẽ chịu phí vận chuyển khi hoàn trả hàng về cho người bán?">
              <span class="card-icon">🚚</span>
              <div class="card-text">
                <strong>Phí vận chuyển</strong>
                <span>Quy định ai trả phí hoàn hàng</span>
              </div>
            </button>

            <button class="suggestion-card" type="button" data-prompt="Quy trình hoàn tiền cho Người mua sau khi Trả hàng thành công?">
              <span class="card-icon">💳</span>
              <div class="card-text">
                <strong>Quy trình hoàn tiền</strong>
                <span>Hình thức và thời gian nhận lại tiền</span>
              </div>
            </button>
          </div>
        </div>
      `;
      // Rebind click events to newly created suggestion cards
      container.querySelectorAll(".suggestion-card").forEach((card) => {
        card.addEventListener("click", () => {
          sendChatMessage(card.dataset.prompt);
        });
      });
    }
  });
});
