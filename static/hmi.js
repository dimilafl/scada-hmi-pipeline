const API_BASE = "http://localhost:8000"; // adjust if needed

const pt101History = [];
const PT101_HISTORY_LIMIT = 20;
let pt101Chart = null;

async function fetchPoints() {
  const resp = await fetch(`${API_BASE}/api/points`);
  if (!resp.ok) {
    console.error("Failed to fetch points", resp.status);
    return;
  }
  const data = await resp.json();
  renderPoints(data.points);
}

async function fetchPt101History(limit = 50) {
  try {
    const resp = await fetch(`${API_BASE}/api/history/PT_101?limit=${limit}`);
    if (!resp.ok) {
      console.error("Failed to fetch PT_101 history", resp.status);
      return;
    }
    const data = await resp.json();
    renderPt101History(data.samples || []);
  } catch (e) {
    console.error("Error fetching PT_101 history", e);
  }
}

function renderPt101History(samples) {
  const trendEl = document.getElementById("pt101-trend");
  if (!trendEl) return;

  if (!samples.length) {
    trendEl.textContent = "No history available.";
    return;
  }

  // Render as simple timestamp:value rows
  const lines = samples.map(s => {
    const ts = s.timestamp || "";
    const val = s.value;
    const q = s.quality || "";
    const alarm = s.alarm_state || "";
    return `${ts}  value=${val}  quality=${q}  alarm=${alarm}`;
  });

  trendEl.textContent = lines.join("\n");
}

function renderPoints(points) {
  const tbody = document.getElementById("points-body");
  tbody.innerHTML = "";

  points.forEach(pt => {
    const tr = document.createElement("tr");

    const alarmClass = alarmToClass(pt.alarm_state, pt.quality);

    tr.className = alarmClass;

    tr.innerHTML = `
      <td>${pt.tag}</td>
      <td>${pt.description}</td>
      <td>${pt.value}</td>
      <td>${pt.eng_unit}</td>
      <td>${pt.quality}</td>
      <td>${pt.alarm_state}</td>
      <td>${pt.timestamp || ""}</td>
    `;
    tbody.appendChild(tr);

    // Track PT_101 values for live chart
    if (pt.tag === "PT_101") {
      pt101History.push(pt.value);
      if (pt101History.length > PT101_HISTORY_LIMIT) {
        pt101History.shift();
      }
    }
  });

  // Update live chart with in-memory data
  updatePt101Chart();
}

function alarmToClass(alarmState, quality) {
  if (quality !== "GOOD") {
    return "quality-bad";
  }
  if (alarmState === "ALARM_HIGH" || alarmState === "ALARM_LOW") {
    return "alarm-high";
  }
  if (alarmState === "NORMAL") {
    return "normal";
  }
  return "";
}

function initPt101Chart() {
  const ctx = document.getElementById("pt101-chart");
  if (!ctx) return;

  pt101Chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],       // will fill from history length
      datasets: [{
        label: "PT_101 (psi)",
        data: [],
        tension: 0.2,
      }],
    },
    options: {
      animation: false,
      scales: {
        x: { display: false },
        y: { beginAtZero: true },
      },
    },
  });
}

function updatePt101Chart() {
  if (pt101Chart) {
    const labels = pt101History.map((_, i) => i.toString());
    pt101Chart.data.labels = labels;
    pt101Chart.data.datasets[0].data = pt101History;
    pt101Chart.update();
  }
}

async function commandValve(value) {
  const statusSpan = document.getElementById("valve-status");
  statusSpan.textContent = "Sending command...";

  try {
    const resp = await fetch(`${API_BASE}/api/points/VALVE_1_CMD`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        value: value,
        quality: "GOOD"
      })
    });

    if (!resp.ok) {
      statusSpan.textContent = "Command failed";
      return;
    }

    const data = await resp.json();
    statusSpan.textContent = `Command success. New value=${data.value}, alarm=${data.alarm_state}`;
  } catch (e) {
    console.error(e);
    statusSpan.textContent = "Error sending command";
  }
}

// Polling loop: bind HMI to backend points
function startPolling() {
  fetchPoints();
  setInterval(fetchPoints, 1000); // 1s poll
}

// wire up buttons
window.addEventListener("DOMContentLoaded", () => {
  initPt101Chart();
  document.getElementById("valve-open").addEventListener("click", () => commandValve(1));
  document.getElementById("valve-close").addEventListener("click", () => commandValve(0));

  const refreshBtn = document.getElementById("pt101-refresh");
  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      fetchPt101History(50);
    });
  }

  // Initial load of PT_101 history
  fetchPt101History(50);

  startPolling();
});
