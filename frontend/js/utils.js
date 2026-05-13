function toast(msg, type = "") {
  let stack = document.querySelector(".toast-stack");
  if (!stack) { stack = document.createElement("div"); stack.className = "toast-stack"; document.body.appendChild(stack); }
  const el = document.createElement("div");
  el.className = `toast ${type}`; el.textContent = msg;
  stack.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

function initials(user) {
  const n = (user?.first_name || user?.email || "?").trim();
  return n.slice(0, 2).toUpperCase();
}

function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

window.U = { toast, initials, escapeHtml };
