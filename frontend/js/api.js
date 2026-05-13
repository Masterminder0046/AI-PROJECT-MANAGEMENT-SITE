// Centralized API client
const API_BASE = window.API_BASE || "/api/v1";

function getAccess() { return localStorage.getItem("access"); }
function getRefresh() { return localStorage.getItem("refresh"); }
function setTokens(a, r) {
  if (a) localStorage.setItem("access", a);
  if (r) localStorage.setItem("refresh", r);
}
function clearTokens() { localStorage.removeItem("access"); localStorage.removeItem("refresh"); }

async function refreshAccess() {
  const r = getRefresh();
  if (!r) return null;
  const res = await fetch(`${API_BASE}/auth/refresh/`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh: r }),
  });
  if (!res.ok) { clearTokens(); return null; }
  const data = await res.json();
  setTokens(data.access, data.refresh);
  return data.access;
}

async function api(path, { method = "GET", body, headers = {}, isForm = false } = {}) {
  const doFetch = async (token) => {
    const h = { ...headers };
    if (token) h["Authorization"] = `Bearer ${token}`;
    if (!isForm && body && !h["Content-Type"]) h["Content-Type"] = "application/json";
    return fetch(`${API_BASE}${path}`, {
      method,
      headers: h,
      body: isForm ? body : (body ? JSON.stringify(body) : undefined),
    });
  };

  let token = getAccess();
  let res = await doFetch(token);
  if (res.status === 401 && getRefresh()) {
    token = await refreshAccess();
    if (token) res = await doFetch(token);
  }
  if (res.status === 401) {
    clearTokens();
    if (!location.pathname.includes("login.html") && !location.pathname.includes("register.html")) {
      location.href = "/pages/login.html?expired=1";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    let errorData;
    try {
      errorData = await res.json();
    } catch (e) {
      errorData = await res.text();
    }
    
    let msg = `HTTP ${res.status}`;
    if (typeof errorData === 'object') {
      // Extract the first error message from DRF style errors
      const firstKey = Object.keys(errorData)[0];
      const firstError = errorData[firstKey];
      msg = Array.isArray(firstError) ? firstError[0] : (typeof firstError === 'string' ? firstError : JSON.stringify(errorData));
      
      // Map common errors to friendly text
      if (msg === "Unable to log in with provided credentials.") msg = "Invalid email or password";
      if (firstKey === "old_password") msg = "Current password is incorrect";
    } else if (typeof errorData === 'string') {
      msg = errorData;
    }
    
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}

window.API = { api, setTokens, clearTokens, getAccess, getRefresh, refreshAccess, API_BASE };
