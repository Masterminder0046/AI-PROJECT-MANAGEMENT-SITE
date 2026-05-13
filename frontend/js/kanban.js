// Kanban board logic with SortableJS + realtime sync
const COLUMNS = [
  { key: "todo", label: "Todo" },
  { key: "in_progress", label: "In Progress" },
  { key: "testing", label: "Testing" },
  { key: "completed", label: "Completed" },
];

let projectId = null;
let tasks = [];
let socket = null;

function taskCardHtml(t) {
  const avs = (t.assignees || []).slice(0, 3).map(u =>
    `<span class="av" title="${U.escapeHtml(u.email)}">${U.initials(u)}</span>`).join("");
  
  return `
    <div class="task-card slide-up" data-id="${t.id}">
        <div class="title">${U.escapeHtml(t.title)}</div>
        <div class="meta">
            <span class="priority-tag priority-${t.priority}">${t.priority}</span>
            <div class="avatars">${avs || '<span class="av">?</span>'}</div>
        </div>
    </div>`;
}

function render() {
  const container = document.getElementById("kanbanContainer");
  if (!container) return;

  container.innerHTML = COLUMNS.map(col => {
    const colTasks = tasks.filter(t => t.status === col.key && !t.parent);
    return `
      <div class="column" data-column="${col.key}">
          <div class="column-header">
              <h3>${col.label} <span class="column-count">${colTasks.length}</span></h3>
          </div>
          <div class="task-list" id="list-${col.key}">
              ${colTasks.sort((a, b) => a.order - b.order).map(taskCardHtml).join("")}
          </div>
      </div>
    `;
  }).join("");

  wireSortables();
}

function wireSortables() {
  COLUMNS.forEach(col => {
    const list = document.getElementById(`list-${col.key}`);
    if (!list) return;
    new Sortable(list, {
      group: "kanban", 
      animation: 250, 
      ghostClass: "sortable-ghost",
      dragClass: "sortable-drag",
      fallbackOnBody: true,
      swapThreshold: 0.65,
      onEnd: async () => {
        const updates = [];
        COLUMNS.forEach(c => {
          const colList = document.getElementById(`list-${c.key}`);
          const countNode = document.querySelector(`[data-column="${c.key}"] .column-count`);
          const nodes = colList.querySelectorAll(`.task-card`);
          
          if (countNode) countNode.textContent = nodes.length;

          nodes.forEach((node, i) => {
            const id = +node.dataset.id;
            updates.push({ id, status: c.key, order: i });
            const t = tasks.find(x => x.id === id);
            if (t) { t.status = c.key; t.order = i; }
          });
        });
        try { await API.api("/tasks/reorder/", { method: "POST", body: updates }); }
        catch (e) { U.toast("Reorder failed", "error"); }
      },
    });
  });
}

async function load(pid) {
  projectId = pid;
  try {
    const proj = await API.api(`/projects/${pid}/`);
    if (document.getElementById("projectTitle")) {
        document.getElementById("projectTitle").textContent = proj.name;
    }
    const data = await API.api(`/tasks/?project=${pid}&page_size=200`);
    tasks = data.results || data;
    render();
    
    socket = WS.connectProject(pid, {
        "task.created": (t) => { tasks.push(t); render(); },
        "task.updated": (t) => { const i = tasks.findIndex(x => x.id === t.id); if (i>=0) tasks[i]=t; render(); },
        "task.deleted": ({ id }) => { tasks = tasks.filter(x => x.id !== id); render(); },
    });
  } catch (err) {
    U.toast("Failed to load project", "error");
  }
}

async function openTaskModal(taskId) {
  const t = tasks.find(x => x.id === taskId);
  if (!t) return;
  
  const back = Modal.openModal(`
    <div style="padding: 8px;">
        <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2">
                <span class="priority-tag priority-${t.priority}">${t.priority}</span>
                <span class="text-dim text-xs">TASK-${t.id}</span>
            </div>
            <button id="delTaskBtn" class="btn btn-ghost" style="color: var(--danger); padding: 4px;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
            </button>
        </div>

        <form id="etf" style="display:grid; gap:20px;">
            <div style="display:grid; gap:8px;">
                <label class="text-xs font-medium text-dim uppercase tracking-wider">Title</label>
                <input class="input" name="title" value="${U.escapeHtml(t.title)}" required />
            </div>
            
            <div style="display:grid; gap:8px;">
                <label class="text-xs font-medium text-dim uppercase tracking-wider">Description</label>
                <textarea class="input" name="description" rows="4" placeholder="Add a more detailed description...">${U.escapeHtml(t.description || "")}</textarea>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
                <div style="display:grid; gap:8px;">
                    <label class="text-xs font-medium text-dim uppercase tracking-wider">Status</label>
                    <select class="input" name="status">
                        ${COLUMNS.map(c => `<option value="${c.key}" ${c.key===t.status?'selected':''}>${c.label}</option>`).join('')}
                    </select>
                </div>
                <div style="display:grid; gap:8px;">
                    <label class="text-xs font-medium text-dim uppercase tracking-wider">Priority</label>
                    <select class="input" name="priority">
                        <option value="low" ${t.priority==='low'?'selected':''}>Low</option>
                        <option value="medium" ${t.priority==='medium'?'selected':''}>Medium</option>
                        <option value="high" ${t.priority==='high'?'selected':''}>High</option>
                        <option value="urgent" ${t.priority==='urgent'?'selected':''}>Urgent</option>
                    </select>
                </div>
            </div>

            <div class="flex gap-2 justify-end mt-4">
                <button class="btn" type="button" onclick="this.closest('.modal-backdrop').remove()">Cancel</button>
                <button class="btn btn-primary" type="submit">Save Changes</button>
            </div>
        </form>

        <div class="mt-8 pt-6" style="border-top: 1px solid var(--border);">
            <div class="flex items-center justify-between mb-4">
                <h3 style="font-size: 14px;">AI Tools</h3>
            </div>
            <button class="btn" id="aiSubtasksBtn" style="width: 100%; justify-content: flex-start; color: var(--accent); border-color: var(--accent);">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:8px;"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
                Generate Subtasks with AI
            </button>
        </div>
    </div>
  `);

  back.querySelector("#etf").addEventListener("submit", async (e) => {
    e.preventDefault(); 
    const f = e.target;
    const btn = f.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.textContent = "Updating...";
    try {
        await API.api(`/tasks/${taskId}/`, { method: "PATCH", body: {
            title: f.title.value, 
            description: f.description.value, 
            priority: f.priority.value, 
            status: f.status.value
        }});
        U.toast("Task updated", "success");
        back.remove();
        location.reload();
    } catch (err) { 
        U.toast(err.message, "error"); 
        btn.disabled = false;
        btn.textContent = "Save Changes";
    }
  });

  back.querySelector("#delTaskBtn").addEventListener("click", async () => {
    if (!confirm("Are you sure you want to delete this task?")) return;
    try {
        await API.api(`/tasks/${taskId}/`, { method: "DELETE" });
        U.toast("Task deleted", "success");
        back.remove();
        location.reload();
    } catch (err) { U.toast(err.message, "error"); }
  });

  back.querySelector("#aiSubtasksBtn").addEventListener("click", async (e) => {
    const btn = e.target.closest('button');
    const originalContent = btn.innerHTML;
    btn.textContent = "AI is thinking...";
    btn.disabled = true;
    try {
        await window.AI.aiGenerateSubtasks(t, { "project": projectId, "status": t.status });
        U.toast("Subtasks generated", "success");
        back.remove();
        location.reload();
    } catch (err) {
        U.toast(err.message, "error");
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
  });
}

document.addEventListener('click', e => {
  const card = e.target.closest('.task-card');
  if (card) {
    const taskId = +card.dataset.id;
    openTaskModal(taskId);
  }
});

window.Kanban = { load, COLUMNS, openTaskModal };
