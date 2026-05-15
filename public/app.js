const BASE = "/api";

// ── Auth ─────────────────────────────────────────────────────────────────────
function getToken() { return localStorage.getItem("token"); }
function getUser()  { return JSON.parse(localStorage.getItem("user") || "null"); }
function setAuth(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}
function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

// ── Route Guards ──────────────────────────────────────────────────────────────
function requireAuth() {
  if (!getToken()) { location.href = "/login.html"; return false; }
  return true;
}
function requireNoTeam() {
  if (!requireAuth()) return false;
  const u = getUser();
  if (u?.team_id) { location.href = "/kanban.html"; return false; }
  return true;
}
function requireTeam() {
  if (!requireAuth()) return false;
  const u = getUser();
  if (!u?.team_id) { location.href = "/team.html"; return false; }
  return true;
}

// ── API wrapper ───────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const token = getToken();
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (token) opts.headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) opts.body = JSON.stringify(body);

  let res;
  try { res = await fetch(BASE + path, opts); }
  catch { throw { code: "NETWORK_ERROR", message: "네트워크 오류가 발생했습니다" }; }

  if (res.status === 401) { clearAuth(); location.href = "/login.html"; return; }

  const data = await res.json();
  if (!res.ok) throw data.error || { code: "UNKNOWN", message: "오류가 발생했습니다" };
  return data;
}

// ── UI Helpers ────────────────────────────────────────────────────────────────
function showError(el, msg) {
  if (!el) return;
  el.textContent = msg;
  el.classList.remove("hidden");
}
function hideError(el) {
  if (!el) return;
  el.textContent = "";
  el.classList.add("hidden");
}
function setLoading(btn, loading, text = "처리 중…") {
  if (!btn) return;
  btn.disabled = loading;
  btn.dataset.orig = btn.dataset.orig || btn.textContent;
  btn.textContent = loading ? text : btn.dataset.orig;
  btn.classList.toggle("opacity-60", loading);
}
function toast(msg, type = "info") {
  const t = document.createElement("div");
  const colors = { info: "bg-teal-600", error: "bg-red-500", success: "bg-green-600" };
  t.className = `fixed bottom-4 right-4 z-50 px-4 py-2 rounded-lg text-white text-sm shadow-lg ${colors[type] || colors.info}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}
