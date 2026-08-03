const state = {
  method: "recursive",
  documents: [],
  result: null,
  view: "chunks",
};

const methodConfig = {
  fixed: {
    label: "Fixed",
    color: "#187f78",
    fields: [
      { key: "chunk_size", label: "Chunk size", min: 100, max: 1500, step: 50, value: 500 },
      { key: "overlap", label: "Overlap", min: 0, max: 400, step: 10, value: 50 },
    ],
  },
  sentence: {
    label: "Sentence",
    color: "#3569b8",
    fields: [{ key: "sentences", label: "Câu / chunk", min: 1, max: 10, step: 1, value: 3 }],
  },
  recursive: {
    label: "Recursive",
    color: "#4e7d3a",
    fields: [{ key: "chunk_size", label: "Chunk size", min: 100, max: 1500, step: 50, value: 500 }],
  },
  custom: {
    label: "Custom",
    color: "#76559a",
    fields: [
      { key: "max_chunk_size", label: "Max chunk", min: 200, max: 2000, step: 100, value: 1000 },
      { key: "min_chunk_size", label: "Min chunk", min: 0, max: 300, step: 10, value: 50 },
    ],
  },
};

const el = (id) => document.getElementById(id);

function updateSourceMeta() {
  const text = el("sourceText").value;
  el("characterCount").textContent = text.length.toLocaleString("vi-VN");
  el("wordCount").textContent = (text.trim() ? text.trim().split(/\s+/).length : 0).toLocaleString("vi-VN");
}

function renderParameters() {
  const container = el("parameterControls");
  container.innerHTML = "";
  methodConfig[state.method].fields.forEach((field) => {
    const wrapper = document.createElement("div");
    wrapper.className = "parameter-field";
    wrapper.innerHTML = `
      <label for="param-${field.key}">${field.label}</label>
      <input id="range-${field.key}" type="range" min="${field.min}" max="${field.max}" step="${field.step}" value="${field.value}">
      <input id="param-${field.key}" data-param="${field.key}" type="number" min="${field.min}" max="${field.max}" step="${field.step}" value="${field.value}">
    `;
    container.appendChild(wrapper);
    const range = wrapper.querySelector("input[type=range]");
    const number = wrapper.querySelector("input[type=number]");
    range.addEventListener("input", () => { number.value = range.value; });
    number.addEventListener("input", () => { range.value = number.value; });
  });
}

function parametersFor(method = state.method) {
  const config = methodConfig[method];
  const values = {};
  config.fields.forEach((field) => {
    const input = method === state.method ? document.querySelector(`[data-param="${field.key}"]`) : null;
    values[field.key] = Number(input?.value ?? field.value);
  });
  return values;
}

async function requestChunks(method, parameters) {
  const response = await fetch("/api/chunk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: el("sourceText").value, method, parameters }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Không thể chạy chunking");
  return payload;
}

function renderResult(result) {
  state.result = result;
  el("statCount").textContent = result.stats.count.toLocaleString("vi-VN");
  el("statAverage").textContent = Math.round(result.stats.average).toLocaleString("vi-VN");
  el("statMinimum").textContent = result.stats.minimum.toLocaleString("vi-VN");
  el("statMaximum").textContent = result.stats.maximum.toLocaleString("vi-VN");
  el("emptyState").classList.toggle("hidden", result.chunks.length > 0);

  const total = result.chunks.reduce((sum, chunk) => sum + chunk.length, 0) || 1;
  el("chunkMap").innerHTML = result.chunks.map((chunk) => `
    <button type="button" data-jump="${chunk.index}" style="flex:${chunk.length / total}" title="Chunk ${chunk.index}: ${chunk.length} ký tự"></button>
  `).join("");
  renderChunkList();
}

function renderChunkList() {
  if (!state.result) return;
  const query = el("chunkSearch").value.trim().toLocaleLowerCase("vi");
  const chunks = state.result.chunks.filter((chunk) => !query || chunk.content.toLocaleLowerCase("vi").includes(query));
  el("chunkList").innerHTML = chunks.map((chunk) => `
    <article class="chunk-item" id="chunk-${chunk.index}">
      <header class="chunk-header">
        <span class="chunk-id">CHUNK ${String(chunk.index).padStart(2, "0")}</span>
        <span class="chunk-metrics"><span>${chunk.length} ký tự</span><span>${chunk.words} từ</span><button class="copy-button" data-copy="${chunk.index}" type="button">Copy</button></span>
      </header>
      <pre class="chunk-content"></pre>
    </article>
  `).join("");
  chunks.forEach((chunk) => {
    const item = el(`chunk-${chunk.index}`);
    if (item) item.querySelector("pre").textContent = chunk.content;
  });
}

async function runCurrent() {
  try {
    el("runButton").disabled = true;
    const result = await requestChunks(state.method, parametersFor());
    renderResult(result);
  } catch (error) {
    showToast(error.message);
  } finally {
    el("runButton").disabled = false;
  }
}

async function runComparison() {
  if (!el("sourceText").value.trim()) return showToast("Văn bản đầu vào đang trống");
  const button = el("compareButton");
  button.disabled = true;
  try {
    const methods = Object.keys(methodConfig);
    const results = await Promise.all(methods.map((method) => requestChunks(method, parametersFor(method))));
    const maxChunks = Math.max(...results.map((result) => result.stats.count), 1);
    el("compareBody").innerHTML = results.map((result) => `
      <tr>
        <td><span class="method-name">${methodConfig[result.method].label}</span></td>
        <td>${result.stats.count}</td>
        <td>${Math.round(result.stats.average)}</td>
        <td>${result.stats.minimum}</td>
        <td>${result.stats.maximum}</td>
        <td><div class="mini-bar"><span style="width:${result.stats.count / maxChunks * 100}%;background:${methodConfig[result.method].color}"></span></div></td>
      </tr>
    `).join("");
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
  }
}

function switchView(view) {
  state.view = view;
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === view));
  el("chunksView").classList.toggle("hidden", view !== "chunks");
  el("compareView").classList.toggle("hidden", view !== "compare");
  el("chatView").classList.toggle("hidden", view !== "chat");
  el("chunkSearch").closest("label").classList.toggle("hidden", view !== "chunks");
}

function showToast(message) {
  const toast = el("toast");
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

async function sendChatMessage(questionText) {
  const text = (questionText || el("chatInput").value).trim();
  if (!text) return;

  const messagesContainer = el("chatMessages");
  const welcome = messagesContainer.querySelector(".chat-welcome");
  if (welcome) welcome.remove();

  const userMsgId = `msg-${Date.now()}`;
  messagesContainer.insertAdjacentHTML("beforeend", `
    <div class="chat-bubble user" id="${userMsgId}">
      <div class="chat-bubble-header">Bạn</div>
      <div class="chat-message-content">${escapeHtml(text)}</div>
    </div>
  `);

  el("chatInput").value = "";
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const botMsgId = `bot-${Date.now()}`;
  messagesContainer.insertAdjacentHTML("beforeend", `
    <div class="chat-bubble assistant" id="${botMsgId}">
      <div class="chat-bubble-header">🤖 RAG Chatbot</div>
      <div class="chat-message-content"><em>Đang thực hiện Chunking, tính Embedding & tổng hợp câu trả lời từ Database...</em></div>
    </div>
  `);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  const sendBtn = el("chatSendButton");
  sendBtn.disabled = true;

  try {
    const selectedMethod = el("chatMethodSelect")?.value || state.method;
    const scope = el("chatScopeSelect")?.value || "all";

    let docId = null;
    let customText = null;

    if (scope === "current") {
      docId = el("documentSelect").value || null;
      customText = el("sourceText").value || null;
    } else if (scope !== "all") {
      docId = scope;
    }

    const bodyPayload = {
      question: text,
      method: selectedMethod,
      parameters: parametersFor(selectedMethod),
      top_k: Number(el("chatTopK").value || 3),
      model: el("chatModelSelect").value || "gpt-4o-mini",
      document_id: docId,
      custom_text: customText,
    };

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyPayload),
    });

    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Không thể thực hiện RAG chat");

    const botMsg = el(botMsgId);
    if (!botMsg) return;

    let retrievedHtml = "";
    if (payload.retrieved_chunks && payload.retrieved_chunks.length > 0) {
      retrievedHtml = `
        <div class="retrieval-inspector">
          <div class="retrieval-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
            <div class="retrieval-title">
              <span class="retrieval-badge">${payload.retrieved_chunks.length} Chunks Trích Xuất</span>
              <span>Vector Context Inspector (${payload.total_chunks_indexed} chunks trong Database store)</span>
            </div>
            <span class="toggle-icon">▼</span>
          </div>
          <div class="retrieval-body">
            ${payload.retrieved_chunks.map((c, i) => `
              <div class="retrieval-chunk">
                <div class="retrieval-chunk-meta">
                  <span>#${i + 1} · ${escapeHtml(c.title || c.doc_id)} (Chunk ${c.chunk_index + 1})</span>
                  <span class="score-tag">Độ tương đồng: ${(c.score * 100).toFixed(1)}%</span>
                </div>
                <pre class="retrieval-chunk-text">${escapeHtml(c.content)}</pre>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    const methodLabels = {
      recursive: "Recursive",
      fixed: "Fixed Size",
      sentence: "Sentence",
      custom: "Custom / Structured"
    };
    const methodName = methodLabels[payload.method] || payload.method;

    botMsg.innerHTML = `
      <div class="chat-bubble-header">
        🤖 RAG Agent · <span class="chat-tag">${escapeHtml(payload.model)}</span>
        · <span class="chat-tag">Chunking: ${escapeHtml(methodName)}</span>
      </div>
      <div class="chat-message-content">${escapeHtml(payload.answer)}</div>
      ${retrievedHtml}
    `;

  } catch (error) {
    const botMsg = el(botMsgId);
    if (botMsg) {
      botMsg.classList.add("error");
      botMsg.querySelector(".chat-message-content").textContent = `⚠️ Lỗi RAG: ${error.message}`;
    }
  } finally {
    sendBtn.disabled = false;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
}

async function loadDocuments() {
  try {
    const response = await fetch("/api/documents");
    const payload = await response.json();
    state.documents = payload.documents || [];

    // Populate Editor document select
    el("documentSelect").insertAdjacentHTML("beforeend", state.documents.map((doc) => `<option value="${doc.id}">${doc.title}</option>`).join(""));

    // Populate Chatbot Database source select
    const chatScopeSelect = el("chatScopeSelect");
    if (chatScopeSelect) {
      chatScopeSelect.innerHTML = `
        <option value="all">🗄️ Toàn bộ Database (Shopee KB)</option>
        <option value="current">📝 Văn bản Editor hiện tại</option>
      `;
      state.documents.forEach((doc) => {
        chatScopeSelect.insertAdjacentHTML("beforeend", `<option value="${doc.id}">📄 DB: ${doc.title}</option>`);
      });
    }

    if (state.documents.length) {
      el("documentSelect").value = state.documents[0].id;
      el("sourceText").value = state.documents[0].content;
      updateSourceMeta();
      await runCurrent();
    }
  } catch (error) {
    showToast("Không tải được corpus; vẫn có thể dán văn bản thủ công");
  }
}

async function loadRuntimeStatus() {
  const status = el("runtimeStatus");
  try {
    const response = await fetch("/api/status");
    if (!response.ok) throw new Error("Status request failed");
    const payload = await response.json();
    status.querySelector("span:last-child").textContent = payload.api_key_configured
      ? "OpenAI · API key configured"
      : "Local · No API key";
    status.title = payload.api_key_configured
      ? `Embedding model: ${payload.embedding_model}`
      : "Chunking chạy hoàn toàn cục bộ";
    status.classList.toggle("is-local", !payload.api_key_configured);
  } catch {
    status.querySelector("span:last-child").textContent = "Local · Status unavailable";
    status.classList.add("is-local");
  }
}

document.querySelectorAll("[data-method]").forEach((button) => button.addEventListener("click", async () => {
  state.method = button.dataset.method;
  document.querySelectorAll("[data-method]").forEach((item) => {
    const active = item === button;
    item.classList.toggle("active", active);
    item.setAttribute("aria-selected", String(active));
  });
  renderParameters();
  if (el("sourceText").value.trim()) await runCurrent();
}));

el("documentSelect").addEventListener("change", async (event) => {
  const documentData = state.documents.find((doc) => doc.id === event.target.value);
  if (documentData) el("sourceText").value = documentData.content;
  updateSourceMeta();
  if (documentData) await runCurrent();
});
el("sourceText").addEventListener("input", () => { el("documentSelect").value = ""; updateSourceMeta(); });
el("clearButton").addEventListener("click", () => { el("sourceText").value = ""; el("documentSelect").value = ""; updateSourceMeta(); });
el("runButton").addEventListener("click", runCurrent);
el("compareButton").addEventListener("click", runComparison);
el("chunkSearch").addEventListener("input", renderChunkList);
document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
el("chunkMap").addEventListener("click", (event) => {
  const button = event.target.closest("[data-jump]");
  if (!button) return;
  const item = el(`chunk-${button.dataset.jump}`);
  item?.scrollIntoView({ behavior: "smooth", block: "center" });
  item?.classList.add("highlight");
  window.setTimeout(() => item?.classList.remove("highlight"), 900);
});
el("chunkList").addEventListener("click", async (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button || !state.result) return;
  const chunk = state.result.chunks.find((item) => item.index === Number(button.dataset.copy));
  if (chunk) { await navigator.clipboard.writeText(chunk.content); showToast(`Đã copy chunk ${chunk.index}`); }
});

// RAG Chat Event Listeners
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

document.querySelectorAll(".prompt-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    sendChatMessage(chip.dataset.prompt);
  });
});

el("clearChatButton")?.addEventListener("click", () => {
  const container = el("chatMessages");
  if (container) {
    container.innerHTML = `
      <div class="chat-welcome">
        <div class="welcome-icon">⚡</div>
        <h3>Demo RAG Chat & Retrieval System</h3>
        <p>Hệ thống tự động chunking dữ liệu, tính toán Vector Embedding, tìm kiếm Top-K chunks phù hợp nhất và sử dụng OpenAI model để tổng hợp câu trả lời.</p>
      </div>
    `;
  }
});

renderParameters();
loadRuntimeStatus();
loadDocuments();

