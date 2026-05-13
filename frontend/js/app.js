// App entry — page-level bootstrapping
document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;

  if (["dashboard", "kanban", "analytics", "profile", "settings", "project-details"].includes(page)) {
    Auth.requireAuth();
    Notif.startLiveNotifications();
  }

  if (page === "dashboard") loadDashboard();
  if (page === "kanban") {
    const pid = new URLSearchParams(location.search).get("project");
    if (pid) Kanban.load(+pid);
  }
  if (page === "analytics") {
    const pid = new URLSearchParams(location.search).get("project");
    Analytics.renderAnalytics(pid ? +pid : null);
  }

  // Sidebar Toggle for Mobile
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.getElementById("sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("active"));
    sidebar.addEventListener("click", (e) => {
      if (e.target === sidebar) sidebar.classList.remove("active");
    });
  }
});

async function loadDashboard() {
  try {
    const [me, projects, analytics] = await Promise.all([
      API.api("/auth/me/"),
      API.api("/projects/"),
      API.api("/analytics/"),
    ]);
    const meEl = document.getElementById("greeting");
    if (meEl) meEl.textContent = `Welcome back, ${me.first_name || me.email.split("@")[0]}`;

    const stats = document.getElementById("stats");
    if (stats) stats.innerHTML = `
      <div class="glass stat-card"><div class="label">Projects</div><div class="value">${analytics.projects ?? 0}</div></div>
      <div class="glass stat-card"><div class="label">Open Tasks</div><div class="value">${analytics.open ?? 0}</div></div>
      <div class="glass stat-card"><div class="label">Completed (30d)</div><div class="value">${analytics.completed_30d ?? 0}</div></div>
      <div class="glass stat-card"><div class="label">Streak</div><div class="value gradient-text">🔥</div></div>`;

    const grid = document.getElementById("projectGrid");
    const list = projects.results || projects;
    if (grid) grid.innerHTML = list.map(p => `
      <div class="glass project-card slide-up" style="position:relative">
        <a href="/pages/project-details.html?id=${p.id}" style="position:absolute; top:10px; right:10px; text-decoration:none; color:var(--text-dim);" title="Settings">⚙️</a>
        <a href="/pages/kanban.html?project=${p.id}" style="display:block; text-decoration:none; color:inherit;">
            <div style="height:6px;border-radius:6px;background:${p.color};margin-bottom:.7rem;margin-right:20px;"></div>
            <div style="font-weight:600">${U.escapeHtml(p.name)}</div>
            <div style="color:var(--text-dim);font-size:.85rem;margin-top:.2rem">${p.task_count ?? 0} tasks</div>
        </a>
      </div>`).join("") || `<div class="glass" style="padding:1rem">No projects yet — create your first.</div>`;

    initGlobalSearch();
    initActivityFeed();
  } catch (e) { U.toast(e.message, "error"); }
}

function initGlobalSearch() {
  const input = document.getElementById("globalSearch");
  const results = document.getElementById("searchResults");
  if (!input) return;

  let timeout = null;
  input.addEventListener("input", (e) => {
    clearTimeout(timeout);
    const q = e.target.value.trim();
    if (q.length < 2) {
      results.style.display = "none";
      return;
    }

    timeout = setTimeout(async () => {
      try {
        const data = await API.api(`/search/?q=${encodeURIComponent(q)}`);
        renderSearchResults(data);
      } catch (err) { console.error(err); }
    }, 3000);
  });

  // Hide dropdown on click outside
  document.addEventListener("click", (e) => {
    if (!input.contains(e.target) && !results.contains(e.target)) {
      results.style.display = "none";
    }
  });
}

function renderSearchResults(data) {
  const results = document.getElementById("searchResults");
  results.style.display = "block";
  
  let html = "";
  if (data.projects.length) {
    html += `<div class="text-xs font-bold uppercase tracking-wider text-dim mb-2">Projects</div>`;
    html += data.projects.map(p => `
      <a href="/pages/kanban.html?project=${p.id}" class="search-item block p-2 rounded hover:bg-surface-strong">
        <div class="flex items-center gap-2">
          <div style="width:8px; height:8px; border-radius:50%; background:${p.color}"></div>
          <span>${U.escapeHtml(p.name)}</span>
        </div>
      </a>`).join("");
  }
  
  if (data.tasks.length) {
    html += `<div class="text-xs font-bold uppercase tracking-wider text-dim mt-4 mb-2">Tasks</div>`;
    html += data.tasks.map(t => `
      <a href="/pages/kanban.html?project=${t.project}" class="search-item block p-2 rounded hover:bg-surface-strong">
        <div class="flex flex-col">
          <span class="text-sm font-medium">${U.escapeHtml(t.title)}</span>
          <span class="text-xs text-dim">${t.status} • ${t.priority}</span>
        </div>
      </a>`).join("");
  }

  if (!html) html = `<div class="p-4 text-center text-dim">No results found</div>`;
  results.innerHTML = html;
}

function initActivityFeed() {
    // Activities will be pushed via WebSocket (broadcasted in ProjectConsumer)
    // Here we can just listen for activity.created events
    WS.connectNotifications((msg) => {
        if (msg.event === "activity.created") {
            addActivityToUI(msg.data);
        }
    });
}

function addActivityToUI(data) {
    const list = document.getElementById("activityList");
    if (!list) return;
    
    // Remove "No recent activity" if it exists
    if (list.querySelector(".text-dim")) list.innerHTML = "";

    const div = document.createElement("div");
    div.className = "activity-item slide-in";
    div.innerHTML = `
        <div class="flex gap-2">
            <div class="w-2 h-2 rounded-full mt-1.5" style="background:var(--primary)"></div>
            <div class="flex-1">
                <div class="text-sm"><strong>${data.actor}</strong> ${data.verb}</div>
                ${data.payload?.title ? `<div class="text-xs text-dim italic">"${data.payload.title}"</div>` : ""}
                <div class="text-xs text-dim mt-1">${new Date(data.created_at).toLocaleTimeString()}</div>
            </div>
        </div>
    `;
    list.prepend(div);
    if (list.children.length > 20) list.lastElementChild.remove();
}
