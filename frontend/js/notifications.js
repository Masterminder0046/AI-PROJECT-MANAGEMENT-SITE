async function loadNotifications() {
  const data = await API.api("/notifications/");
  const list = document.getElementById("notifList");
  if (!list) return;
  list.innerHTML = (data.results || data).map(n => `
    <div class="glass" style="padding:.8rem;margin-bottom:.5rem">
      <strong>${U.escapeHtml(n.title)}</strong>
      <div style="color:var(--text-dim);font-size:.85rem">${U.escapeHtml(n.body || "")}</div>
    </div>`).join("");
}

function startLiveNotifications() {
  WS.connectNotifications((n) => {
    U.toast(n.title, "success");
    loadNotifications();
  });
}

window.Notif = { loadNotifications, startLiveNotifications };
