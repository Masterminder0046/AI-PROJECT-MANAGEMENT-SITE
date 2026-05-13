async function renderAnalytics(projectId) {
  const data = await API.api(projectId ? `/analytics/?project=${projectId}` : "/analytics/");
  const ctx1 = document.getElementById("statusChart");
  if (ctx1 && data.by_status) {
    new Chart(ctx1, {
      type: "doughnut",
      data: {
        labels: Object.keys(data.by_status),
        datasets: [{ data: Object.values(data.by_status),
          backgroundColor: ["#7c5cff", "#22d3ee", "#f59e0b", "#22c55e"] }],
      },
      options: { plugins: { legend: { labels: { color: "#e8ecf3" } } } },
    });
  }
  const ctx2 = document.getElementById("trendChart");
  if (ctx2 && data.completed_by_day) {
    new Chart(ctx2, {
      type: "line",
      data: {
        labels: data.completed_by_day.map(d => d.day),
        datasets: [{ label: "Completed", data: data.completed_by_day.map(d => d.c),
          borderColor: "#22d3ee", backgroundColor: "rgba(34,211,238,.15)", fill: true, tension: .35 }],
      },
      options: { plugins: { legend: { labels: { color: "#e8ecf3" } } },
                 scales: { x: { ticks: { color: "#9aa3b2" } }, y: { ticks: { color: "#9aa3b2" } } } },
    });
  }
}
window.Analytics = { renderAnalytics };
