// Auth helpers + page wiring
async function login(email, password) {
  const data = await API.api("/auth/login/", { method: "POST", body: { email, password } });
  API.setTokens(data.access, data.refresh);
  location.href = "/pages/dashboard.html";
}

async function register(payload) {
  await API.api("/auth/register/", { method: "POST", body: payload });
  await login(payload.email, payload.password);
}

async function logout() {
  try { await API.api("/auth/logout/", { method: "POST", body: { refresh: API.getRefresh() } }); } catch {}
  API.clearTokens();
  location.href = "/pages/login.html";
}

async function requireAuth() {
  if (API.getAccess()) return;
  if (API.getRefresh()) {
    const ok = await API.refreshAccess();
    if (ok) return;
  }
  location.href = "/pages/login.html";
}

window.Auth = { login, register, logout, requireAuth };
