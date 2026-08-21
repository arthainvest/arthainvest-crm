const http = require('http');
const url = require('url');
const fs = require('fs');
const path = require('path');

const PORT = 3333;

const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI CRM - Phase 1 Testing Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      overflow: hidden;
    }

    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .header h1 {
      font-size: 28px;
      font-weight: 600;
    }

    .header p {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 5px;
    }

    .stats {
      display: flex;
      gap: 15px;
    }

    .stat {
      background: rgba(255,255,255,0.2);
      padding: 15px 20px;
      border-radius: 8px;
      text-align: center;
      backdrop-filter: blur(10px);
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
      margin: 5px 0 0;
    }

    .stat-label {
      font-size: 12px;
      opacity: 0.9;
    }

    .metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      padding: 25px;
      background: #f8f9fa;
      border-bottom: 1px solid #eee;
    }

    .metric {
      background: white;
      border-radius: 8px;
      padding: 15px;
      text-align: center;
      border-left: 4px solid;
    }

    .metric.pass { border-left-color: #10b981; }
    .metric.pending { border-left-color: #f59e0b; }
    .metric.fail { border-left-color: #ef4444; }

    .metric-value {
      font-size: 28px;
      font-weight: 700;
      margin: 8px 0 5px;
    }

    .metric-label {
      font-size: 12px;
      color: #666;
      font-weight: 500;
    }

    .metric.pass .metric-value { color: #10b981; }
    .metric.pending .metric-value { color: #f59e0b; }
    .metric.fail .metric-value { color: #ef4444; }

    .content {
      padding: 30px;
    }

    .section {
      background: white;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      margin-bottom: 20px;
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .section-header {
      background: #f3f4f6;
      padding: 16px 20px;
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      user-select: none;
      border-bottom: 1px solid #e5e7eb;
    }

    .section-header:hover {
      background: #e5e7eb;
    }

    .section-title {
      font-weight: 600;
      font-size: 15px;
      color: #1f2937;
    }

    .section-time {
      font-size: 12px;
      color: #999;
    }

    .section-icon {
      font-size: 20px;
      transition: transform 0.3s ease;
    }

    .section.open .section-icon {
      transform: rotate(180deg);
    }

    .section-content {
      display: none;
      padding: 20px;
    }

    .section.open .section-content {
      display: block;
    }

    .checklist {
      background: #f9fafb;
      padding: 15px;
      border-radius: 6px;
      margin-bottom: 15px;
    }

    .checklist-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 0;
      font-size: 14px;
      color: #374151;
    }

    .checklist-item input[type="checkbox"] {
      width: 18px;
      height: 18px;
      cursor: pointer;
      accent-color: #667eea;
    }

    .checklist-item input[type="checkbox"]:checked + label {
      color: #10b981;
      text-decoration: line-through;
      opacity: 0.7;
    }

    .checklist-item label {
      cursor: pointer;
      flex: 1;
      user-select: none;
    }

    .button-group {
      display: flex;
      gap: 10px;
      margin-top: 15px;
    }

    .btn {
      flex: 1;
      padding: 10px 15px;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s ease;
    }

    .btn-pass {
      background: #10b981;
      color: white;
    }

    .btn-pass:hover {
      background: #059669;
      transform: translateY(-1px);
    }

    .btn-fail {
      background: #ef4444;
      color: white;
    }

    .btn-fail:hover {
      background: #dc2626;
      transform: translateY(-1px);
    }

    .status {
      display: inline-block;
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-weight: 600;
      margin-left: 10px;
    }

    .status.pass { background: #d1fae5; color: #047857; }
    .status.fail { background: #fee2e2; color: #991b1b; }
    .status.pending { background: #fef3c7; color: #92400e; }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: #e5e7eb;
      border-radius: 4px;
      margin-top: 10px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea, #764ba2);
      transition: width 0.3s ease;
    }

    .footer {
      background: #f3f4f6;
      padding: 20px 30px;
      border-top: 1px solid #e5e7eb;
      text-align: center;
      color: #666;
      font-size: 13px;
    }

    .phase-ready {
      background: #dcfce7;
      border: 2px solid #10b981;
      color: #166534;
      padding: 15px;
      border-radius: 8px;
      margin-top: 20px;
      text-align: center;
      font-weight: 600;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <h1>🚀 AI CRM Testing Dashboard</h1>
        <p>Phase 1: Complete System Verification</p>
      </div>
      <div class="stats">
        <div class="stat">
          <div class="stat-label">Progress</div>
          <div class="stat-value" id="progress">0/7</div>
        </div>
        <div class="stat">
          <div class="stat-label">Status</div>
          <div class="stat-value" id="status">In Progress</div>
        </div>
      </div>
    </div>

    <div class="metrics">
      <div class="metric pass">
        <div class="metric-label">Passed</div>
        <div class="metric-value" id="passed">0</div>
      </div>
      <div class="metric pending">
        <div class="metric-label">Pending</div>
        <div class="metric-value" id="pending">7</div>
      </div>
      <div class="metric fail">
        <div class="metric-label">Failed</div>
        <div class="metric-value" id="failed">0</div>
      </div>
    </div>

    <div class="content">
      <div id="sections"></div>
      <div class="phase-ready" id="phaseReady" style="display:none;">
        ✅ Phase 1 Complete! Ready for Phase 2 (Team Training)
      </div>
    </div>

    <div class="footer">
      Testing Dashboard v1.0 | ArthaInvest CRM | Open Chrome to view actual CRM sheet
    </div>
  </div>

  <script>
    const sections = [
      {
        id: 'nav',
        title: 'Basic Navigation Test',
        time: '10 min',
        items: [
          'All 15 sheet tabs visible at bottom',
          'Sheet tabs load quickly (<2 seconds)',
          'Custom menus visible (5 automation menus)',
          'Google Apps Script editor accessible'
        ]
      },
      {
        id: 'dashboard',
        title: 'Dashboard Sheet Verification',
        time: '10 min',
        items: [
          'Dashboard sheet opens without errors',
          'KPI numbers display (27 clients, 12 prospects, etc.)',
          'All metrics formatted correctly (no #ERROR)',
          'Numbers show with proper commas'
        ]
      },
      {
        id: 'leads',
        title: 'Leads Sheet & Auto-Scoring',
        time: '15 min',
        items: [
          'All 15 columns visible (A-O)',
          'Existing leads show (Rajesh Patel, Priya Sharma)',
          'Scores visible (Rajesh ~85, Priya ~75)',
          'Add new test lead "TEST LEAD 001"',
          'Auto-score calculated after refresh',
          'Auto-tier assigned (HOT/WARM/COOL/COLD)',
          'Data validation dropdowns work'
        ]
      },
      {
        id: 'other',
        title: 'Other Core Sheets Check',
        time: '20 min',
        items: [
          'Clients sheet loads (17 columns, 27 clients)',
          'Deals sheet loads (14 columns, stage dropdown)',
          'Tasks sheet loads (11 columns, status/priority)',
          'Communications sheet loads (11 columns)',
          'Products sheet loads (4 products pre-loaded)',
          'All sheets have data, no errors'
        ]
      },
      {
        id: 'automation',
        title: 'Automation Menus (5 Phases)',
        time: '45 min',
        items: [
          'Phase A: Notifications menu accessible & shows options',
          'Phase B: Workflows menu accessible & shows options',
          'Phase C: Lead Scoring menu accessible & shows options',
          'Phase D: Email Sequences menu accessible & shows options',
          'Phase E: Communication Hub menu accessible & shows options',
          'All menus display without errors'
        ]
      },
      {
        id: 'formatting',
        title: 'Data Quality & Formatting',
        time: '15 min',
        items: [
          'Currency displays with ₹ symbol (₹50,00,000)',
          'Dates format correctly (YYYY-MM-DD)',
          'Formulas calculate correctly (no #ERROR)',
          'Data validation dropdowns work properly',
          'No broken references or circular formulas'
        ]
      },
      {
        id: 'issues',
        title: 'Issue Identification & Documentation',
        time: 'As needed',
        items: [
          'Identify any critical issues',
          'Document bugs with severity (Critical/Major/Minor)',
          'Note workarounds if available',
          'Take screenshots of any problems',
          'List all issues for Phase 2 fix'
        ]
      }
    ];

    function renderSections() {
      const container = document.getElementById('sections');
      container.innerHTML = sections.map((sec, idx) => \`
        <div class="section" data-id="\${sec.id}">
          <div class="section-header" onclick="toggleSection('\${sec.id}')">
            <div>
              <div class="section-title">\${idx + 1}. \${sec.title}</div>
              <div class="section-time">\${sec.time} | \${sec.items.length} items</div>
            </div>
            <div class="section-icon">▼</div>
          </div>
          <div class="section-content">
            <div class="checklist">
              \${sec.items.map((item, i) => \`
                <div class="checklist-item">
                  <input type="checkbox" id="\${sec.id}-\${i}" onchange="updateProgress()">
                  <label for="\${sec.id}-\${i}">\${item}</label>
                </div>
              \`).join('')}
            </div>
            <div class="button-group">
              <button class="btn btn-pass" onclick="markPass('\${sec.id}')">✓ Pass</button>
              <button class="btn btn-fail" onclick="markFail('\${sec.id}')">✗ Fail</button>
            </div>
            <span class="status pending" id="status-\${sec.id}">Pending</span>
          </div>
        </div>
      \`).join('');
    }

    function toggleSection(id) {
      const section = document.querySelector(\`[data-id="\${id}"]\`);
      section.classList.toggle('open');
    }

    let results = {};

    function markPass(id) {
      results[id] = 'pass';
      const statusEl = document.getElementById(\`status-\${id}\`);
      statusEl.className = 'status pass';
      statusEl.textContent = 'Passed ✓';
      updateProgress();
    }

    function markFail(id) {
      results[id] = 'fail';
      const statusEl = document.getElementById(\`status-\${id}\`);
      statusEl.className = 'status fail';
      statusEl.textContent = 'Failed ✗';
      updateProgress();
    }

    function updateProgress() {
      const total = sections.length;
      const passed = Object.values(results).filter(v => v === 'pass').length;
      const failed = Object.values(results).filter(v => v === 'fail').length;
      const pending = total - passed - failed;

      document.getElementById('progress').textContent = \`\${passed + failed}/\${total}\`;
      document.getElementById('passed').textContent = passed;
      document.getElementById('failed').textContent = failed;
      document.getElementById('pending').textContent = pending;

      const statusEl = document.getElementById('status');
      if (failed > 0) {
        statusEl.textContent = '⚠️ Issues';
      } else if (pending === 0) {
        statusEl.textContent = '✅ Complete';
        document.getElementById('phaseReady').style.display = 'block';
      } else {
        statusEl.textContent = '🔄 Testing';
      }
    }

    renderSections();
    updateProgress();
  </script>
</body>
</html>`;

const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);

  res.writeHead(200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Cache-Control': 'no-cache'
  });

  res.end(html);
});

server.listen(PORT, '127.0.0.1', () => {
  console.log('\n✅ AI CRM Testing Dashboard running at http://localhost:' + PORT);
  console.log('📱 Open your browser and navigate to: http://localhost:' + PORT);
  console.log('\n🧪 Phase 1 Testing Dashboard is ready!');
  console.log('Keep Chrome open with the actual CRM sheet in another window.\n');
});
