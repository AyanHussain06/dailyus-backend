const API = "/api";
let token = localStorage.getItem("dailyus_token") || null;

// ---------- helpers ----------
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function showView(id) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
  document.getElementById(id).classList.add("active");
  document.querySelector(`.nav-btn[data-view="${id}"]`).classList.add("active");
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(API + path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

function setToken(t) {
  token = t;
  localStorage.setItem("dailyus_token", t);
}

function clearToken() {
  token = null;
  localStorage.removeItem("dailyus_token");
}

// ---------- boot ----------
async function boot() {
  if (!token) {
    showScreen("auth-screen");
    return;
  }
  try {
    const me = await api("/auth/me");
    if (me.paired) {
      enterMainApp();
    } else {
      showScreen("pairing-screen");
    }
  } catch (e) {
    clearToken();
    showScreen("auth-screen");
  }
}

// ---------- auth tabs ----------
document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".auth-form").forEach(f => f.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`${btn.dataset.tab}-form`).classList.add("active");
  });
});

document.getElementById("login-form").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl = document.getElementById("login-error");
  errEl.textContent = "";
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email: document.getElementById("login-email").value,
        password: document.getElementById("login-password").value,
      }),
    });
    setToken(data.token);
    boot();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("signup-form").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl = document.getElementById("signup-error");
  errEl.textContent = "";
  try {
    const data = await api("/auth/signup", {
      method: "POST",
      body: JSON.stringify({
        name: document.getElementById("signup-name").value,
        email: document.getElementById("signup-email").value,
        password: document.getElementById("signup-password").value,
      }),
    });
    setToken(data.token);
    showScreen("pairing-screen");
  } catch (err) {
    errEl.textContent = err.message;
  }
});

// ---------- pairing ----------
document.getElementById("create-invite-btn").addEventListener("click", async () => {
  try {
    const data = await api("/couple/create-invite", { method: "POST" });
    document.getElementById("invite-code-display").textContent = data.invite_code;
    document.getElementById("invite-result").classList.remove("hidden");
    pollForPartner();
  } catch (err) {
    alert(err.message);
  }
});

function pollForPartner() {
  const interval = setInterval(async () => {
    try {
      const status = await api("/couple/status");
      if (status.paired) {
        clearInterval(interval);
        enterMainApp();
      }
    } catch (e) { /* ignore transient errors while polling */ }
  }, 3000);
}

document.getElementById("join-form").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl = document.getElementById("join-error");
  errEl.textContent = "";
  try {
    await api("/couple/join", {
      method: "POST",
      body: JSON.stringify({ invite_code: document.getElementById("join-code").value }),
    });
    enterMainApp();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("logout-from-pairing").addEventListener("click", () => {
  clearToken();
  showScreen("auth-screen");
});
document.getElementById("logout-btn").addEventListener("click", () => {
  clearToken();
  showScreen("auth-screen");
});

// ---------- main app ----------
function enterMainApp() {
  showScreen("main-screen");
  showView("timeline-view");
  loadTimeline();
  loadStreak();
}

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    showView(btn.dataset.view);
    if (btn.dataset.view === "chat-view") loadMessages();
  });
});

async function loadStreak() {
  try {
    const status = await api("/couple/status");
    document.getElementById("streak-badge").textContent = `🔥 ${status.streak_count || 0} day streak`;
  } catch (e) { /* non-critical */ }
}

// ---- timeline ----
document.getElementById("photo-input").addEventListener("change", () => {
  const file = document.getElementById("photo-input").files[0];
  document.querySelector(".upload-label").textContent = file ? `📷 ${file.name}` : "📷 Upload today's photo";
});

document.getElementById("upload-btn").addEventListener("click", async () => {
  const fileInput = document.getElementById("photo-input");
  const statusEl = document.getElementById("upload-status");
  if (!fileInput.files[0]) {
    statusEl.textContent = "Choose a photo first";
    return;
  }
  const form = new FormData();
  form.append("photo", fileInput.files[0]);
  form.append("caption", document.getElementById("caption-input").value);

  statusEl.textContent = "Uploading...";
  try {
    await api("/photos/upload", { method: "POST", body: form });
    statusEl.textContent = "Uploaded! 🎉";
    fileInput.value = "";
    document.getElementById("caption-input").value = "";
    document.querySelector(".upload-label").textContent = "📷 Upload today's photo";
    loadTimeline();
  } catch (err) {
    statusEl.textContent = err.message;
  }
});

async function loadTimeline() {
  const grid = document.getElementById("timeline-grid");
  try {
    const data = await api("/photos/timeline");
    if (!data.photos.length) {
      grid.innerHTML = `<p class="hint">No photos yet — upload your first one above!</p>`;
      return;
    }
    grid.innerHTML = data.photos.map(p => `
      <div class="photo-tile">
        <img src="/api/photos/view/${p.id}?token=${p.access_token}" alt="Photo from ${p.day}" loading="lazy">
        <div class="photo-meta">
          ${p.caption ? `<span class="caption">${escapeHtml(p.caption)}</span>` : ""}
          ${p.is_mine ? "You" : escapeHtml(p.uploader_name)} · ${p.day}
        </div>
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

// ---- chat ----
async function loadMessages() {
  const list = document.getElementById("messages-list");
  try {
    const data = await api("/messages");
    list.innerHTML = data.messages.map(m => `
      <div class="msg-bubble ${m.is_mine ? "mine" : "theirs"}">
        ${escapeHtml(m.text)}
        <span class="msg-time">${new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
      </div>
    `).join("");
    list.scrollTop = list.scrollHeight;
  } catch (err) {
    list.innerHTML = `<p class="error">${err.message}</p>`;
  }
}

document.getElementById("message-form").addEventListener("submit", async e => {
  e.preventDefault();
  const input = document.getElementById("message-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  try {
    await api("/messages", { method: "POST", body: JSON.stringify({ text }) });
    loadMessages();
  } catch (err) {
    alert(err.message);
  }
});

// ---- collage ----
document.getElementById("generate-collage-btn").addEventListener("click", async () => {
  const days = document.getElementById("collage-days").value;
  const resultEl = document.getElementById("collage-result");
  resultEl.innerHTML = `<p class="hint">Generating...</p>`;
  try {
    const data = await api("/collage/generate", {
      method: "POST",
      body: JSON.stringify({ days: parseInt(days, 10) }),
    });
    resultEl.innerHTML = `
      <p class="hint">${data.photo_count} photos included</p>
      <img src="/api/collage/view/${data.collage_filename}?token=${data.collage_token}" alt="Collage">
    `;
  } catch (err) {
    resultEl.innerHTML = `<p class="error">${err.message}</p>`;
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

boot();
