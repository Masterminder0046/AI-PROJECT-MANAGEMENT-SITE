async function aiGenerateSubtasks(parentTask, projectContext) {
  const res = await API.api("/ai/", { method: "POST",
    body: { kind: "subtasks", prompt: parentTask.title, context: projectContext } });
  const subtasks = res.data?.subtasks || [];
  for (const s of subtasks) {
    if (!s.title) continue;
    try {
      await API.api("/tasks/", { method: "POST", body: {
        project: parentTask.project, 
        parent: parentTask.id,
        title: s.title.trim(), 
        description: s.description || "", 
        priority: (s.priority || "medium").toLowerCase(),
        ai_generated: true
      }});
    } catch (e) {
      console.warn("Failed to create AI subtask:", s.title, e);
    }
  }
  U.toast(`AI created ${subtasks.length} subtasks`, "success");
  return subtasks;
}

async function aiPlanProject(idea) {
  return API.api("/ai/", { method: "POST", body: { kind: "plan", prompt: idea } });
}

async function aiGetProjectHealth(projectId, projectTitle, taskList) {
    const context = { project_id: projectId, title: projectTitle, tasks: taskList.slice(0, 50).map(t => ({ title: t.title, status: t.status })) };
    return API.api("/ai/", { method: "POST", body: { kind: "suggest", prompt: `Analyze the health of project: ${projectTitle}`, context } });
}

window.AI = { aiGenerateSubtasks, aiPlanProject, aiGetProjectHealth };
