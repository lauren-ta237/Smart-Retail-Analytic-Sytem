// --- Fully robust fetch override for analytics endpoints ---
function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]));
  } catch (e) {
    return {};
  }
}

async function fetchToken(username, password) {
  const resp = await window.originalFetch('/api/auth/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
  });
  if (!resp.ok) throw new Error('Failed to refresh token');
  const data = await resp.json();
  localStorage.setItem('access_token', data.access_token);
  return data.access_token;
}

async function getGuaranteedToken(forceRefresh = false) {
  let token = localStorage.getItem('access_token');
  if (!forceRefresh && token) {
    const payload = parseJwt(token);
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp && payload.exp > now + 10) {
      return token;
    }
  }
  // Token missing or expired, or forceRefresh requested
  const username = localStorage.getItem('username');
  const password = localStorage.getItem('password');
  if (!username || !password) throw new Error('Missing credentials for token refresh');
  return await fetchToken(username, password);
}

window.originalFetch = window.fetch;
window.fetch = async function(input, init = {}) {
  let url = typeof input === 'string' ? input : input.url;
  // Always inject token for analytics endpoints
  if (url && url.includes('/api/analytics/')) {
    let token = await getGuaranteedToken();
    init = Object.assign({}, init); // avoid mutating caller's object
    init.headers = init.headers || {};
    if (init.headers instanceof Headers) {
      init.headers.set('Authorization', `Bearer ${token}`);
    } else {
      // Clone headers if it's a plain object
      init.headers = Object.assign({}, init.headers, { 'Authorization': `Bearer ${token}` });
    }
    try {
      let resp = await window.originalFetch(input, init);
      // If unauthorized, always retry ONCE with a fresh token
      if (resp.status === 401) {
        token = await getGuaranteedToken(true); // force refresh
        if (init.headers instanceof Headers) {
          init.headers.set('Authorization', `Bearer ${token}`);
        } else {
          init.headers['Authorization'] = `Bearer ${token}`;
        }
        resp = await window.originalFetch(input, init);
      }
      return resp;
    } catch (e) {
      return Promise.reject(e);
    }
  }
  // For non-analytics endpoints, just call original fetch
  return window.originalFetch(input, init);
};
// --- End fully robust fetch override ---
const dashboardSummaryUrl = '/api/analytics/dashboard-summary';
const alertsUrl = '/api/analytics/alerts';
const askUrl = '/api/analytics/ask';
const testOpenAiUrl = '/api/analytics/test-openai';

const totalCustomersEl = document.getElementById('totalCustomers');
const activeSessionsEl = document.getElementById('activeSessions');
const avgVisitDurationEl = document.getElementById('avgVisitDuration');
const entryExitCountEl = document.getElementById('entryExitCount');
const topZoneEl = document.getElementById('topZone');
const topProductEl = document.getElementById('topProduct');
const peakHourEl = document.getElementById('peakHour');
const liveSnapshotEl = document.getElementById('liveSnapshot');
const historicalSnapshotEl = document.getElementById('historicalSnapshot');
const statusTextEl = document.getElementById('statusText');
const aiAnswerEl = document.getElementById('aiAnswer');
const openAiTestResultEl = document.getElementById('openAiTestResult');
const questionInputEl = document.getElementById('questionInput');
const systemBadgesEl = document.getElementById('systemBadges');
const alertsListEl = document.getElementById('alertsList');
const alertBannerEl = document.getElementById('alertBanner');
const alertStatusEl = document.getElementById('alertStatus');
const enableAlertsBtn = document.getElementById('enableAlertsBtn');
const customerTrendEl = document.getElementById('customerTrend');
const productInterestEl = document.getElementById('productInterest');
const zoneTrafficEl = document.getElementById('zoneTraffic');
const actionListEl = document.getElementById('actionList');
const summaryHeadlineEl = document.getElementById('summaryHeadline');
const summarySubtextEl = document.getElementById('summarySubtext');
const summaryActionTitleEl = document.getElementById('summaryActionTitle');
const summaryActionDetailEl = document.getElementById('summaryActionDetail');
const summaryStatusTitleEl = document.getElementById('summaryStatusTitle');
const summaryStatusDetailEl = document.getElementById('summaryStatusDetail');

let latestSummary = null;
let alertMonitoringPrimed = false;
const seenAlertIds = new Set();

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json();
}

function renderList(element, items, emptyText = 'No data yet') {
  element.innerHTML = '';

  if (!items || items.length === 0) {
    const li = document.createElement('li');
    li.textContent = emptyText;
    element.appendChild(li);
    return;
  }

  items.forEach((text) => {
    const li = document.createElement('li');
    li.textContent = text;
    element.appendChild(li);
  });
}

function renderBadges(llmStatus, alerts = []) {
  const activeAlertCount = (alerts || []).filter((alert) => alert.severity !== 'info').length;
  const badges = [
    { label: 'Backend', value: 'Live', tone: 'ok' },
    { label: 'Alerts', value: activeAlertCount ? `${activeAlertCount} active` : 'Clear', tone: activeAlertCount ? 'error' : 'ok' },
    { label: 'AI key', value: llmStatus?.configured ? 'Configured' : 'Missing', tone: llmStatus?.configured ? 'ok' : 'error' },
    { label: 'Mode', value: llmStatus?.mode || 'n/a', tone: 'neutral' },
    { label: 'Model', value: llmStatus?.model || 'n/a', tone: 'neutral' },
  ];

  systemBadgesEl.innerHTML = badges
    .map((badge) => `<span class="badge ${badge.tone}">${badge.label}: ${badge.value}</span>`)
    .join('');
}

function renderBars(element, items, labelKey, valueKey, emptyText, fillClass = '') {
  element.innerHTML = '';

  if (!items || items.length === 0) {
    element.innerHTML = `<p class="muted">${emptyText}</p>`;
    return;
  }

  const maxValue = Math.max(...items.map((item) => Number(item[valueKey] || 0)), 1);

  items.forEach((item) => {
    const row = document.createElement('div');
    row.className = 'bar-row';

    const label = document.createElement('div');
    label.className = 'bar-label';
    label.textContent = `${item[labelKey]} (${item[valueKey]})`;

    const track = document.createElement('div');
    track.className = 'bar-track';

    const fill = document.createElement('div');
    fill.className = 'bar-fill';
    if (fillClass) {
      fill.classList.add(fillClass);
    }
    fill.style.width = `${Math.max(12, (Number(item[valueKey] || 0) / maxValue) * 100)}%`;

    track.appendChild(fill);
    row.appendChild(label);
    row.appendChild(track);
    element.appendChild(row);
  });
}

function renderActions(actions) {
  renderList(
    actionListEl,
    (actions || []).map((action) => `[${String(action.priority || 'info').toUpperCase()}] ${action.title} — ${action.details}`),
    'No recommended actions yet'
  );
}

function formatMinutes(value) {
  const minutes = Number(value || 0);
  return `${minutes.toFixed(minutes >= 10 ? 0 : 1)} min`;
}

function updateAlertBanner(alerts = []) {
  const firstAlert = (alerts || [])[0];
  const severity = firstAlert?.severity || 'info';
  alertBannerEl.className = `alert-banner ${severity}`;

  if (!firstAlert) {
    alertBannerEl.textContent = 'Monitoring for new alerts...';
    return;
  }

  if (severity === 'info') {
    alertBannerEl.textContent = firstAlert.message;
    return;
  }

  alertBannerEl.textContent = `${firstAlert.title}: ${firstAlert.message}`;
}

function renderAlerts(alerts = []) {
  alertsListEl.innerHTML = '';

  (alerts || []).forEach((alert) => {
    const card = document.createElement('article');
    card.className = `alert-card ${alert.severity || 'info'}`;

    const title = document.createElement('h3');
    title.textContent = `${String(alert.severity || 'info').toUpperCase()} — ${alert.title || 'Alert'}`;

    const meta = document.createElement('p');
    meta.className = 'alert-meta';
    meta.textContent = `Updated ${new Date(alert.timestamp || Date.now()).toLocaleTimeString()}${alert.value !== null && alert.value !== undefined ? ` • value: ${alert.value}` : ''}`;

    const message = document.createElement('p');
    message.textContent = alert.message || 'No alert details available.';

    const action = document.createElement('p');
    action.className = 'alert-action';
    action.textContent = `Action: ${alert.action || 'Keep monitoring the dashboard.'}`;

    card.appendChild(title);
    card.appendChild(meta);
    card.appendChild(message);
    card.appendChild(action);
    alertsListEl.appendChild(card);
  });

  updateAlertBanner(alerts);
}

function notifyForNewAlerts(alerts = []) {
  if (!('Notification' in window)) {
    return;
  }

  if (!alertMonitoringPrimed) {
    alerts.forEach((alert) => seenAlertIds.add(alert.id));
    alertMonitoringPrimed = true;
    return;
  }

  if (Notification.permission !== 'granted') {
    return;
  }

  alerts
    .filter((alert) => alert.severity === 'high' || alert.severity === 'medium')
    .forEach((alert) => {
      if (seenAlertIds.has(alert.id)) {
        return;
      }

      seenAlertIds.add(alert.id);
      new Notification(`Smart Retail Alert: ${alert.title}`, {
        body: alert.message,
      });
    });
}

async function enableBrowserAlerts() {
  if (!('Notification' in window)) {
    alertStatusEl.textContent = 'Browser notifications are not supported here.';
    return;
  }

  const permission = await Notification.requestPermission();
  if (permission === 'granted') {
    alertStatusEl.textContent = 'Browser alerts enabled.';
    enableAlertsBtn.textContent = 'Browser alerts enabled';
    return;
  }

  alertStatusEl.textContent = 'Browser alerts remain disabled.';
}

async function refreshAlerts() {
  try {
    const payload = await fetchJson(alertsUrl);
    const alerts = payload.alerts || [];
    renderAlerts(alerts);
    notifyForNewAlerts(alerts);
    alertStatusEl.textContent = `Monitoring every 5 seconds • ${alerts.filter((alert) => alert.severity !== 'info').length} active alerts`;
  } catch (error) {
    alertStatusEl.textContent = `Alert monitoring issue: ${error.message}`;
    alertBannerEl.className = 'alert-banner high';
    alertBannerEl.textContent = `Alert feed error: ${error.message}`;
  }
}

function renderSummaryCards(summary) {
  const overview = summary.overview || {};
  const actions = summary.recommended_actions || [];
  const llmStatus = summary.llm_status || {};
  const topProduct = overview.top_product?.product || 'No product hotspot yet';
  const peakHour = overview.peak_hour?.hour || 'No peak hour data yet';
  const topZone = overview.top_zone?.zone || 'No zone hotspot yet';
  const topAction = actions[0];

  summaryHeadlineEl.textContent = `${overview.active_sessions ?? 0} active shoppers, ${overview.entries_today ?? 0} entries today`;
  summarySubtextEl.textContent = `Top zone: ${topZone}. Avg visit: ${formatMinutes(overview.avg_visit_minutes)}. Peak hour signal: ${peakHour}. Top product: ${topProduct}. Alerts active: ${overview.alert_count ?? 0}.`;

  summaryActionTitleEl.textContent = topAction?.title || 'Monitor the store floor';
  summaryActionDetailEl.textContent = topAction?.details || 'Keep collecting more data to sharpen recommendations.';

  summaryStatusTitleEl.textContent = llmStatus?.configured ? `AI model ready: ${llmStatus.model}` : 'Fallback mode active';
  summaryStatusDetailEl.textContent = llmStatus?.configured
    ? `Backend is connected and using ${llmStatus.mode} mode with a ${llmStatus.timeout}s timeout.`
    : 'No API key detected, so only fallback store summaries are available.';
}

function downloadFile(filename, content, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function buildCsv(summary) {
  const rows = [
    ['section', 'label', 'value'],
    ['overview', 'total_customers', summary.overview?.total_customers ?? ''],
    ['overview', 'active_sessions', summary.overview?.active_sessions ?? ''],
    ['overview', 'entries_today', summary.overview?.entries_today ?? ''],
    ['overview', 'exits_today', summary.overview?.exits_today ?? ''],
    ['overview', 'avg_visit_minutes', summary.overview?.avg_visit_minutes ?? ''],
    ['overview', 'top_zone', summary.overview?.top_zone?.zone ?? ''],
    ['overview', 'top_product', summary.overview?.top_product?.product ?? ''],
    ['overview', 'peak_hour', summary.overview?.peak_hour?.hour ?? ''],
  ];

  (summary.recommended_actions || []).forEach((action, index) => {
    rows.push(['recommended_action', `action_${index + 1}`, `${action.priority}: ${action.title} - ${action.details}`]);
  });

  (summary.historical_data?.customer_trend || []).forEach((item) => {
    rows.push(['customer_trend', item.day, item.visits]);
  });

  (summary.historical_data?.zone_analytics || summary.live_data?.zone_traffic || []).forEach((item) => {
    rows.push(['zone_traffic', item.zone, item.visits]);
  });

  (summary.alerts || []).forEach((alert) => {
    rows.push(['alert', alert.title, `${alert.severity}: ${alert.message}`]);
  });

  return rows
    .map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(','))
    .join('\n');
}

async function ensureSummaryLoaded() {
  if (!latestSummary) {
    latestSummary = await fetchJson(dashboardSummaryUrl);
  }
  return latestSummary;
}

async function refreshDashboard() {
  statusTextEl.textContent = 'Refreshing results...';
  statusTextEl.className = 'status';

  try {
    const summary = await fetchJson(dashboardSummaryUrl);
    latestSummary = summary;

    const overview = summary.overview || {};
    const liveData = summary.live_data || {};
    const historicalData = summary.historical_data || {};
    const entryExit = liveData.entry_exit || historicalData.entry_exit_summary || {};
    const zoneAnalytics = historicalData.zone_analytics || liveData.zone_traffic || [];

    totalCustomersEl.textContent = overview.total_customers ?? '--';
    activeSessionsEl.textContent = overview.active_sessions ?? '--';
    avgVisitDurationEl.textContent = formatMinutes(overview.avg_visit_minutes ?? historicalData.average_visit_duration?.avg_minutes ?? 0);
    entryExitCountEl.textContent = `${entryExit.entries_today ?? overview.entries_today ?? 0} / ${entryExit.exits_today ?? overview.exits_today ?? 0}`;
    topZoneEl.textContent = overview.top_zone?.zone ?? zoneAnalytics[0]?.zone ?? 'No data yet';
    topProductEl.textContent = overview.top_product?.product ?? 'No data yet';
    peakHourEl.textContent = overview.peak_hour?.hour ?? 'No data yet';

    renderList(liveSnapshotEl, [
      `Recent tracked customers: ${(liveData.customers?.recent_customers || []).length}`,
      `Entries today: ${entryExit.entries_today ?? 0}`,
      `Exits today: ${entryExit.exits_today ?? 0}`,
      `Busiest zone right now: ${zoneAnalytics[0]?.zone || 'No zone data yet'}`,
      `Top product activity: ${(liveData.top_products || []).map((item) => item.product).join(', ') || 'No product interactions yet'}`,
      `Latest backend log: ${(liveData.recent_logs || []).slice(-1)[0] || 'No logs available yet'}`,
    ]);

    renderList(historicalSnapshotEl, [
      `Historical customer trend points: ${(historicalData.customer_trend || []).length}`,
      `Average visit duration: ${formatMinutes(historicalData.average_visit_duration?.avg_minutes ?? 0)}`,
      `Completed visits: ${entryExit.completed_visits ?? 0}`,
      `Repeat customer signals: ${(historicalData.repeat_customers || []).length}`,
      `Tracked zones: ${zoneAnalytics.map((item) => item.zone).join(', ') || 'No zone data yet'}`,
      `All-time top products: ${(historicalData.top_products_all_time || []).map((item) => item.product).join(', ') || 'No historical product data yet'}`,
    ]);

    renderBadges(summary.llm_status || {}, summary.alerts || []);
    renderSummaryCards(summary);
    renderActions(summary.recommended_actions || []);
    renderAlerts(summary.alerts || []);
    notifyForNewAlerts(summary.alerts || []);
    renderBars(customerTrendEl, historicalData.customer_trend || [], 'day', 'visits', 'No trend data yet', 'trend');
    renderBars(productInterestEl, historicalData.top_products_all_time || liveData.top_products || [], 'product', 'interactions', 'No product trend data yet', 'product');
    renderBars(zoneTrafficEl, zoneAnalytics, 'zone', 'visits', 'No zone traffic data yet', 'zone');

    statusTextEl.textContent = `Results updated at ${new Date().toLocaleTimeString()}`;
    statusTextEl.className = 'status ok';
  } catch (error) {
    statusTextEl.textContent = `Dashboard error: ${error.message}`;
    statusTextEl.className = 'status error';
  }
}

async function askAi() {
  const question = questionInputEl.value.trim();
  if (!question) {
    aiAnswerEl.textContent = 'Enter a question first.';
    return;
  }

  aiAnswerEl.textContent = 'Waiting for AI response...';

  try {
    const result = await fetchJson(askUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    });

    aiAnswerEl.textContent = `${result.answer}\n\nSource: ${result.source}`;
  } catch (error) {
    aiAnswerEl.textContent = `AI request failed: ${error.message}`;
  }
}

async function testOpenAi() {
  openAiTestResultEl.textContent = 'Running OpenAI backend test...';
  try {
    const result = await fetchJson(testOpenAiUrl);
    openAiTestResultEl.textContent = JSON.stringify(result, null, 2);
  } catch (error) {
    openAiTestResultEl.textContent = `OpenAI test failed: ${error.message}`;
  }
}

async function downloadJsonReport() {
  const summary = await ensureSummaryLoaded();
  downloadFile(`smart-retail-report-${new Date().toISOString().slice(0, 10)}.json`, JSON.stringify(summary, null, 2), 'application/json');
}

async function downloadCsvReport() {
  const summary = await ensureSummaryLoaded();
  downloadFile(`smart-retail-report-${new Date().toISOString().slice(0, 10)}.csv`, buildCsv(summary), 'text/csv;charset=utf-8');
}

function printReport() {
  window.print();
}

document.getElementById('refreshBtn').addEventListener('click', refreshDashboard);
document.getElementById('askBtn').addEventListener('click', askAi);
document.getElementById('testOpenAiBtn').addEventListener('click', testOpenAi);
document.getElementById('downloadJsonBtn').addEventListener('click', downloadJsonReport);
document.getElementById('downloadCsvBtn').addEventListener('click', downloadCsvReport);
document.getElementById('printReportBtn').addEventListener('click', printReport);
enableAlertsBtn.addEventListener('click', enableBrowserAlerts);

questionInputEl.value = 'What should I do with current customer traffic?';
refreshDashboard();
refreshAlerts();
setInterval(refreshDashboard, 15000);
setInterval(refreshAlerts, 5000);
