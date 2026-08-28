const $ = (sel) => document.querySelector(sel);

async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  return res.json();
}

function badge(decision) {
  return `<span class="badge ${decision}">${decision}</span>`;
}

async function loadScenarios() {
  const scenarios = await fetchJSON("/api/scenarios");
  const container = $("#scenarioButtons");
  container.innerHTML = "";
  Object.entries(scenarios).forEach(([key, s]) => {
    const btn = document.createElement("button");
    btn.className = "scenario-btn";
    btn.innerHTML = `${key.replace(/_/g, " ")}<span class="exp">expects: ${s.expected}</span>`;
    btn.onclick = () => runScenario(key, s);
    container.appendChild(btn);
  });
}

async function runScenario(key, scenario) {
  $("#scenarioResult").textContent = `Running ${key}...`;
  const result = await fetchJSON("/agent/intent", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${scenario.token}`,
    },
    body: JSON.stringify(scenario.payload),
  });
  $("#scenarioResult").textContent = JSON.stringify(result, null, 2);
  refreshAll();
}

async function loadOverview() {
  const data = await fetchJSON("/api/overview");
  const pill = $("#ledgerStatus");
  pill.textContent = data.ledger_integrity_ok ? "Ledger: intact ✓" : "Ledger: TAMPERED";
  pill.className = "ledger-pill " + (data.ledger_integrity_ok ? "ok" : "bad");

  const dist = data.decision_distribution || {};
  const stats = [
    ["EXECUTE", dist.EXECUTE || 0],
    ["CONSTRAIN", dist.CONSTRAIN || 0],
    ["ESCALATE", dist.ESCALATE || 0],
    ["BLOCK", dist.BLOCK || 0],
  ];
  $("#overviewStats").innerHTML = stats.map(([label, val]) => `
    <div class="stat-card">
      <div class="num">${val}</div>
      <div class="lbl">${label}</div>
    </div>`).join("") + `
    <div class="stat-card" style="grid-column: span 4">
      <div class="num">${data.escalation_rate}%</div>
      <div class="lbl">Escalation rate</div>
    </div>`;

  renderIncidentChart(data.agent_incidents || []);
}

let incidentChart;
function renderIncidentChart(rows) {
  const ctx = $("#incidentChart");
  const labels = rows.map(r => r.agent_id);
  const values = rows.map(r => r.incident_count);
  if (incidentChart) incidentChart.destroy();
  incidentChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.length ? labels : ["No incidents yet"],
      datasets: [{
        label: "Incidents",
        data: values.length ? values : [0],
        backgroundColor: "#e5484d",
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#8b98a5" }, grid: { color: "#1a222c" } },
        y: { ticks: { color: "#8b98a5" }, grid: { color: "#1a222c" }, beginAtZero: true },
      },
    },
  });
}

async function loadTransactions() {
  const rows = await fetchJSON("/api/transactions");
  const tbody = $("#txnTable tbody");
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${r.txn_id || "-"}</td>
      <td>${r.agent_id}</td>
      <td>${r.currency} ${r.amount.toLocaleString()}</td>
      <td>${r.counterparty_id || "-"}</td>
      <td>${r.risk_score ?? "-"}</td>
      <td>${badge(r.decision || "BLOCK")}</td>
    </tr>`).join("") || `<tr><td colspan="6" class="empty-state">No transactions yet — run a scenario above.</td></tr>`;
}

async function loadAgents() {
  const rows = await fetchJSON("/api/agents");
  const tbody = $("#agentTable tbody");
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${r.agent_id}</td>
      <td>${r.role_id}</td>
      <td>₹${Math.round(r.mean_amount || 0).toLocaleString()} ± ${Math.round(r.std_amount || 0).toLocaleString()}</td>
      <td>₹${(r.daily_spent || 0).toLocaleString()}</td>
      <td>${r.txn_count_today || 0}</td>
    </tr>`).join("");
}

async function loadReviewQueue() {
  const rows = await fetchJSON("/api/review-queue");
  const container = $("#reviewList");
  container.innerHTML = rows.map(r => `
    <div class="review-item">
      <div class="row"><strong>${r.txn_id}</strong><span>risk ${r.risk_score}</span></div>
      <div>${r.agent_id} → ${r.counterparty_id} · ${r.amount}</div>
      <div style="color:#8b98a5">${r.reason}</div>
      <div class="actions">
        <button class="btn-approve" onclick="reviewTxn('${r.txn_id}', 'approve')">Approve</button>
        <button class="btn-reject" onclick="reviewTxn('${r.txn_id}', 'reject')">Reject</button>
      </div>
    </div>`).join("") || `<div class="empty-state">No pending human review.</div>`;
}

async function reviewTxn(txnId, action) {
  await fetchJSON(`/api/review/${txnId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, reviewed_by: "demo_reviewer" }),
  });
  refreshAll();
}
window.reviewTxn = reviewTxn;

async function loadBlocked() {
  const rows = await fetchJSON("/api/blocked");
  const container = $("#blockedList");
  container.innerHTML = rows.map(r => `
    <div class="blocked-item">
      <div class="row"><strong>${r.txn_id}</strong><span>risk ${r.risk_score}</span></div>
      <div>${r.agent_id} → ${r.counterparty_id} · ${r.amount}</div>
      <div style="color:#8b98a5">${r.reason}</div>
    </div>`).join("") || `<div class="empty-state">No blocked transactions yet.</div>`;
}

async function loadLedger() {
  const rows = await fetchJSON("/api/ledger");
  const container = $("#ledgerList");
  container.innerHTML = rows.map(r => `
    <div class="ledger-item">
      #${r.log_id} · ${r.created_at}<br>
      hash: <span class="hash">${r.entry_hash.slice(0, 24)}...</span>
    </div>`).join("") || `<div class="empty-state">Ledger is empty.</div>`;
}

async function refreshAll() {
  await Promise.all([loadOverview(), loadTransactions(), loadAgents(), loadReviewQueue(), loadBlocked(), loadLedger()]);
}

$("#refreshBtn").addEventListener("click", refreshAll);

loadScenarios();
refreshAll();
setInterval(refreshAll, 8000);
