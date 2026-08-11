// CRM Application State
let crmData = {
  users: {
    artha: { username: 'artha', password: 'artha123', name: 'ArthaInvest Admin', role: 'admin' },
    ravi: { username: 'ravi', password: 'ravi123', name: 'Ravi Sharma', role: 'employee' },
    priya: { username: 'priya', password: 'priya123', name: 'Priya Singh', role: 'employee' }
  },
  leads: {
    lead_001: { id: 'lead_001', name: 'Rajesh Kumar', phone: '+919876543210', email: 'rajesh@example.com', status: 'interested', budget: 500000, assignedTo: 'artha', createdAt: new Date().toISOString(), reminder: 'Follow up on Monday' },
    lead_002: { id: 'lead_002', name: 'Priya Singh', phone: '+919876543211', email: 'priya.singh@example.com', status: 'contacted', budget: 300000, assignedTo: 'ravi', createdAt: new Date().toISOString(), reminder: 'Send proposal' },
    lead_003: { id: 'lead_003', name: 'Amit Patel', phone: '+919876543212', email: 'amit.patel@example.com', status: 'new', budget: 750000, assignedTo: 'priya', createdAt: new Date().toISOString(), reminder: 'Initial call' }
  },
  clients: {},
  documents: {},
  marketingMaterials: {},
  deals: {
    deal_001: { id: 'deal_001', name: 'Rajesh SIP Investment', amount: 500000, stage: 'proposal', probability: 75, leadId: 'lead_001', createdAt: new Date().toISOString(), expectedClose: '2026-09-07' }
  },
  campaigns: {
    camp_001: { id: 'camp_001', name: 'Q3 Product Launch', type: 'Email', description: 'New mutual fund product launch', createdAt: new Date().toISOString(), sent: 0 }
  },
  tasks: {
    task_001: { id: 'task_001', name: 'Call Rajesh about SIP', dueDate: '2026-08-10', priority: 'high', status: 'open', createdAt: new Date().toISOString() }
  },
  contacts: {},
  leadScores: {},
  activityLogs: {},
  workflows: {},
  callHistory: {
    call_001: { id: 'call_001', number: '+919876543210', duration: 240, outcome: 'connected', user: 'artha', timestamp: new Date().toISOString() },
    call_002: { id: 'call_002', number: '+919876543211', duration: 180, outcome: 'voicemail', user: 'ravi', timestamp: new Date().toISOString() }
  },
  whatsappHistory: {},
  communicationLog: {},
  settings: {
    companyName: 'ArthaInvest Capital',
    agentMobileNumber: '+917021351181',
    agentName: 'Artha',
    companyPhone: '+917021351181',
    companyEmail: 'arthainvest.services@gmail.com',
    businessFilesPath: 'C:\\Users\\artha\\LaptopHub',
    license: 'ARN-267891 | POSP | DSA'
  }
};

let currentUser = null;
let currentEditLeadId = null;
let currentEditUserId = null;

// Initialize
window.addEventListener('DOMContentLoaded', () => {
  loadData();
  loadSettingsUI();
  showLoginScreen();
});

// ============ DATA MANAGEMENT ============
function loadData() {
  const saved = localStorage.getItem('crmData');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      const hasData = Object.keys(parsed.leads || {}).length > 0 ||
                      Object.keys(parsed.deals || {}).length > 0 ||
                      Object.keys(parsed.callHistory || {}).length > 0;

      if (hasData) {
        crmData = parsed;
      }
    } catch (e) {
      console.error('Error loading data:', e);
    }
  }

  // ABSOLUTE FALLBACK: Ensure demo data always exists
  if (!crmData.leads || Object.keys(crmData.leads).length === 0) {
    initializeDemoData();
  }
}

function initializeDemoData() {
  if (Object.keys(crmData.leads || {}).length > 0) return; // Don't overwrite real data

  crmData.leads = {
    lead_001: { id: 'lead_001', name: 'Rajesh Kumar', phone: '+919876543210', email: 'rajesh@example.com', status: 'interested', budget: 500000, assignedTo: 'artha', createdAt: new Date().toISOString(), reminder: 'Follow up on Monday' },
    lead_002: { id: 'lead_002', name: 'Priya Singh', phone: '+919876543211', email: 'priya.singh@example.com', status: 'contacted', budget: 300000, assignedTo: 'ravi', createdAt: new Date().toISOString(), reminder: 'Send proposal' },
    lead_003: { id: 'lead_003', name: 'Amit Patel', phone: '+919876543212', email: 'amit.patel@example.com', status: 'new', budget: 750000, assignedTo: 'priya', createdAt: new Date().toISOString(), reminder: 'Initial call' }
  };

  crmData.callHistory = {
    call_001: { id: 'call_001', number: '+919876543210', duration: 240, outcome: 'connected', user: 'artha', timestamp: new Date().toISOString() },
    call_002: { id: 'call_002', number: '+919876543211', duration: 180, outcome: 'voicemail', user: 'ravi', timestamp: new Date().toISOString() }
  };

  crmData.campaigns = {
    camp_001: { id: 'camp_001', name: 'Q3 Product Launch', type: 'Email', description: 'New mutual fund product launch', createdAt: new Date().toISOString(), sent: 0 }
  };

  crmData.deals = {
    deal_001: { id: 'deal_001', name: 'Rajesh SIP Investment', amount: 500000, stage: 'proposal', probability: 75, leadId: 'lead_001', createdAt: new Date().toISOString(), expectedClose: '2026-09-07' }
  };

  crmData.tasks = {
    task_001: { id: 'task_001', name: 'Call Rajesh about SIP', dueDate: '2026-08-10', priority: 'high', status: 'open', createdAt: new Date().toISOString() }
  };
}

function saveData() {
  localStorage.setItem('crmData', JSON.stringify(crmData));
}

// ============ AUTHENTICATION ============
function login() {
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;

  if (!username || !password) {
    alert('Please enter username and password');
    return;
  }

  const user = crmData.users[username];
  if (user && user.password === password) {
    currentUser = username;
    showAppScreen();
    updateUI();
    renderDashboard();
  } else {
    alert('Invalid username or password');
  }
}

function logout() {
  currentUser = null;
  document.getElementById('loginUsername').value = '';
  document.getElementById('loginPassword').value = '';
  showLoginScreen();
}

function showLoginScreen() {
  document.getElementById('loginScreen').classList.remove('hidden');
  document.getElementById('appScreen').classList.add('hidden');
}

function showAppScreen() {
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('appScreen').classList.remove('hidden');
  updateUI();
  navigateTo('dashboard');

  // Ensure demo data shows if no real data
  if (Object.keys(crmData.leads || {}).length === 0) {
    initializeDemoData();
  }

  loadBusinessData();
}

// ============ UI MANAGEMENT ============
function updateUI() {
  const user = crmData.users[currentUser];
  document.getElementById('userDisplay').textContent = `${user.name}\n${user.role}`;

  // Show/hide admin sections
  const adminSections = document.querySelectorAll('.admin-only');
  if (user.role === 'admin') {
    adminSections.forEach(el => el.classList.add('show'));
    document.querySelector('.nav-section.admin-only').style.display = 'block';
  } else {
    adminSections.forEach(el => el.classList.remove('show'));
    document.querySelector('.nav-section.admin-only').style.display = 'none';
  }

  // Show add button only in leads section for now
  updateAddButtonVisibility();
  updateAssigneeSelect();
}

function updateAddButtonVisibility() {
  // Show in leads and dashboard
  const section = document.querySelector('.nav-item.active');
  const addBtn = document.getElementById('addBtn');
  const isLeadsSection = section?.textContent.includes('Leads') ||
                        document.getElementById('leadsSection').classList.contains('hidden') === false;
  addBtn.style.display = isLeadsSection ? 'inline-block' : 'none';
}

function navigateTo(section) {
  // Update active nav item
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
  });
  event.target.closest('.nav-item').classList.add('active');

  // Hide all sections
  document.getElementById('dashboardSection').classList.add('hidden');
  document.getElementById('leadsSection').classList.add('hidden');
  document.getElementById('teamSection').classList.add('hidden');
  document.getElementById('reportsSection').classList.add('hidden');
  document.getElementById('documentsSection').classList.add('hidden');
  document.getElementById('marketingSection').classList.add('hidden');
  document.getElementById('dealsSection').classList.add('hidden');
  document.getElementById('campaignsSection').classList.add('hidden');
  document.getElementById('tasksSection').classList.add('hidden');
  document.getElementById('scoresSection').classList.add('hidden');
  document.getElementById('diallerSection').classList.add('hidden');
  document.getElementById('callMonitoringSection').classList.add('hidden');
  document.getElementById('usersSection').classList.add('hidden');
  document.getElementById('settingsSection').classList.add('hidden');

  // Update page title
  const titles = {
    dashboard: 'Dashboard',
    leads: 'All Leads',
    team: 'Team Members',
    reports: 'Reports & Analytics',
    documents: 'Client Documents',
    marketing: 'Marketing Materials',
    deals: 'Deals & Opportunities',
    campaigns: 'Campaigns',
    tasks: 'Tasks',
    scores: 'Lead Scoring',
    users: 'Manage Users',
    settings: 'Settings'
  };
  document.getElementById('pageTitle').textContent = titles[section];

  // Show selected section and render
  const sectionEl = document.getElementById(section + 'Section');
  if (sectionEl) {
    sectionEl.classList.remove('hidden');
  }

  switch (section) {
    case 'dashboard':
      renderDashboard();
      break;
    case 'leads':
      renderAllLeads();
      updateAddButtonVisibility();
      break;
    case 'team':
      renderTeam();
      break;
    case 'reports':
      renderReports();
      break;
    case 'documents':
      renderDocuments();
      break;
    case 'marketing':
      renderMarketing();
      break;
    case 'deals':
      renderDeals();
      break;
    case 'campaigns':
      renderCampaigns();
      break;
    case 'tasks':
      renderTasks();
      break;
    case 'scores':
      renderLeadScores();
      break;
    case 'dialler':
      renderDialler();
      break;
    case 'callMonitoring':
      renderCallMonitoring();
      break;
    case 'users':
      renderUsers();
      break;
    case 'settings':
      loadSettingsUI();
      break;
  }
}

// ============ DASHBOARD ============
function renderDashboard() {
  try {
    const leadIds = Object.keys(crmData.leads || {});
    const totalLeads = leadIds.length;
    const totalCalls = Object.keys(crmData.callHistory || {}).length;
    const totalCampaigns = Object.keys(crmData.campaigns || {}).length;
    const newLeads = leadIds.filter(id => crmData.leads[id] && crmData.leads[id].status === 'new').length;
    const active = leadIds.filter(id =>
      crmData.leads[id] && ['contacted', 'interested', 'meeting'].includes(crmData.leads[id].status)
    ).length;
    const dealsWon = Object.values(crmData.deals || {}).filter(deal => deal.stage === 'closed' || deal.stage === 'won').length;
    const dealsLost = Object.values(crmData.deals || {}).filter(deal => deal.stage === 'lost').length;

    // Calculate trend: 100% if first leads, else 0% (no historical comparison)
    const leadsTrendPercent = totalLeads > 0 ? 100 : 0;

    // Update Leads Created Card
    const totalLeadsEl = document.getElementById('totalLeads');
    if (totalLeadsEl) totalLeadsEl.textContent = totalLeads;

    const leadsTrendEl = document.getElementById('leadsTrend');
    if (leadsTrendEl) {
      leadsTrendEl.innerHTML = `<span class="trend-indicator ${leadsTrendPercent > 0 ? 'up' : 'down'}">↑ ${leadsTrendPercent}%</span>`;
    }

    const leadsComparisonEl = document.getElementById('leadsComparison');
    if (leadsComparisonEl) leadsComparisonEl.textContent = `Last Month: 0`;

    // Update Deals Won Card
    const dealsWonEl = document.getElementById('dealsWon');
    if (dealsWonEl) dealsWonEl.textContent = dealsWon;

    // Update Deals Lost Card
    const dealsLostEl = document.getElementById('dealsLost');
    if (dealsLostEl) dealsLostEl.textContent = dealsLost;

    // Update Active Conversations Card
    const activeEl = document.getElementById('activeConversations');
    if (activeEl) activeEl.textContent = active;

    const activeComparisonEl = document.getElementById('activeComparison');
    if (activeComparisonEl) activeComparisonEl.textContent = `Last Month: 0`;

    // Update Calls Completed Card
    const totalCallsEl = document.getElementById('totalCalls');
    if (totalCallsEl) totalCallsEl.textContent = totalCalls;

    const callsComparisonEl = document.getElementById('callsComparison');
    if (callsComparisonEl) callsComparisonEl.textContent = `Last Month: 0`;

    // Update Campaigns Card
    const totalCampaignsEl = document.getElementById('totalCampaigns');
    if (totalCampaignsEl) totalCampaignsEl.textContent = totalCampaigns;

    const campaignsComparisonEl = document.getElementById('campaignsComparison');
    if (campaignsComparisonEl) campaignsComparisonEl.textContent = `Total Running`;

    // Render Recent Leads Table
    const user = crmData.users[currentUser] || {};
    const recentLeads = Object.values(crmData.leads || {})
      .filter(lead => user.role === 'admin' || lead.assignedTo === currentUser)
      .sort((a, b) => new Date(b.createdAt || b.created || 0) - new Date(a.createdAt || a.created || 0))
      .slice(0, 10);

    const html = recentLeads.map(lead => `
      <tr>
        <td><strong>${escapeHtml(lead.name || 'Unknown')}</strong></td>
        <td>${lead.phone || '-'}</td>
        <td>${getEmployeeName(lead.assignedTo)}</td>
        <td><span class="status-badge status-${lead.status || 'new'}">${formatStatus(lead.status || 'new')}</span></td>
        <td>${lead.reminder ? lead.reminder : '-'}</td>
        <td>
          <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 12px;" onclick="editLead('${lead.id}')">Edit</button>
        </td>
      </tr>
    `).join('');

    const tbody = document.getElementById('recentLeadsBody');
    if (tbody) {
      tbody.innerHTML = html || '<tr><td colspan="6" style="text-align:center; color: #999; padding: 20px;">Start adding leads to see them here</td></tr>';
    }
  } catch (error) {
    console.error('Dashboard render error:', error);
  }
}

// ============ LEADS MANAGEMENT ============
function renderAllLeads() {
  const user = crmData.users[currentUser];
  let leads = Object.values(crmData.leads);

  // Employees only see their assigned leads
  if (user.role === 'employee') {
    leads = leads.filter(lead => lead.assignedTo === currentUser);
  }

  const searchTerm = document.getElementById('leadSearch')?.value.toLowerCase() || '';
  leads = leads.filter(lead =>
    lead.name.toLowerCase().includes(searchTerm) ||
    (lead.phone || '').includes(searchTerm)
  );

  const html = leads.map(lead => `
    <tr>
      <td><strong>${escapeHtml(lead.name)}</strong></td>
      <td>${lead.phone || '-'}</td>
      <td>${getEmployeeName(lead.assignedTo)}</td>
      <td><span class="status-badge status-${lead.status}">${formatStatus(lead.status)}</span></td>
      <td>${lead.callTime || '-'}</td>
      <td>${lead.reminder || '-'}</td>
      <td>${lead.notes ? lead.notes.substring(0, 30) + '...' : '-'}</td>
      <td>
        <button class="btn btn-secondary" style="padding: 6px 10px; font-size: 12px;" onclick="editLead('${lead.id}')">Edit</button>
        <button class="btn btn-danger" style="padding: 6px 10px; font-size: 12px; margin-left: 5px;" onclick="deleteLead('${lead.id}')">Delete</button>
      </td>
    </tr>
  `).join('');

  document.getElementById('leadsBody').innerHTML = html || '<tr><td colspan="8" style="text-align:center; color: #999;">No leads found</td></tr>';
}

function filterLeads() {
  renderAllLeads();
}

function openAddModal() {
  currentEditLeadId = null;
  document.getElementById('leadName').value = '';
  document.getElementById('leadPhone').value = '';
  document.getElementById('leadStatus').value = 'new';
  document.getElementById('leadCallTime').value = '';
  document.getElementById('leadReminder').value = '';
  document.getElementById('leadNotes').value = '';

  const user = crmData.users[currentUser];
  if (user.role === 'employee') {
    document.getElementById('leadAssignee').value = currentUser;
  } else {
    document.getElementById('leadAssignee').value = '';
  }

  document.getElementById('leadModal').classList.add('active');
}

function closeModal() {
  document.getElementById('leadModal').classList.remove('active');
  currentEditLeadId = null;
}

function editLead(id) {
  currentEditLeadId = id;
  const lead = crmData.leads[id];

  document.querySelector('.modal-title').textContent = 'Edit Lead';
  document.getElementById('leadName').value = lead.name;
  document.getElementById('leadPhone').value = lead.phone || '';
  document.getElementById('leadStatus').value = lead.status;
  document.getElementById('leadCallTime').value = lead.callTime || '';
  document.getElementById('leadReminder').value = lead.reminder || '';
  document.getElementById('leadNotes').value = lead.notes || '';
  document.getElementById('leadAssignee').value = lead.assignedTo || '';

  document.getElementById('leadModal').classList.add('active');
}

function saveLead() {
  const name = document.getElementById('leadName').value.trim();
  if (!name) {
    alert('Lead name is required');
    return;
  }

  const phone = document.getElementById('leadPhone').value.trim();
  const status = document.getElementById('leadStatus').value;
  const callTime = document.getElementById('leadCallTime').value;
  const reminder = document.getElementById('leadReminder').value;
  const notes = document.getElementById('leadNotes').value.trim();
  const assignedTo = document.getElementById('leadAssignee').value;

  const id = currentEditLeadId || 'lead_' + Date.now();

  crmData.leads[id] = {
    id,
    name,
    phone,
    status,
    callTime,
    reminder,
    notes,
    assignedTo,
    created: crmData.leads[id]?.created || new Date().toISOString(),
    updated: new Date().toISOString()
  };

  saveData();
  closeModal();
  renderAllLeads();
  renderDashboard();
  alert('Lead saved successfully!');
}

function deleteLead(id) {
  if (confirm('Are you sure you want to delete this lead?')) {
    delete crmData.leads[id];
    saveData();
    renderAllLeads();
    renderDashboard();
  }
}

function updateAssignee() {
  // Placeholder - can be used for dependent functionality
}

// ============ TEAM MANAGEMENT ============
function renderTeam() {
  const employees = Object.entries(crmData.users).filter(([_, user]) => user.role === 'employee');

  const html = employees.map(([username, user]) => {
    const assignedLeads = Object.values(crmData.leads).filter(l => l.assignedTo === username);
    return `
      <tr>
        <td><strong>${user.name}</strong></td>
        <td><span class="role-badge role-employee">Employee</span></td>
        <td>${assignedLeads.length}</td>
        <td>Active</td>
      </tr>
    `;
  }).join('');

  document.getElementById('teamBody').innerHTML = html || '<tr><td colspan="4" style="text-align:center; color: #999;">No team members</td></tr>';
}

// ============ REPORTS ============
function renderReports() {
  const employees = Object.entries(crmData.users).filter(([_, user]) => user.role === 'employee');

  let totalClosed = 0;
  let totalLeads = Object.keys(crmData.leads).length;
  const conversionRate = totalLeads > 0 ? Math.round((totalClosed / totalLeads) * 100) : 0;

  const reportData = employees.map(([username, user]) => {
    const leads = Object.values(crmData.leads).filter(l => l.assignedTo === username);
    const closed = leads.filter(l => l.status === 'closed').length;
    totalClosed += closed;

    return {
      name: user.name,
      total: leads.length,
      new: leads.filter(l => l.status === 'new').length,
      contacted: leads.filter(l => l.status === 'contacted').length,
      closed: closed
    };
  }).sort((a, b) => b.closed - a.closed);

  document.getElementById('conversionRate').textContent = conversionRate + '%';

  if (reportData.length > 0) {
    document.getElementById('topEmployee').textContent = reportData[0].name;
  }

  const html = reportData.map(data => `
    <tr>
      <td><strong>${data.name}</strong></td>
      <td>${data.total}</td>
      <td>${data.new}</td>
      <td>${data.contacted}</td>
      <td>${data.closed}</td>
    </tr>
  `).join('');

  document.getElementById('reportBody').innerHTML = html || '<tr><td colspan="5" style="text-align:center; color: #999;">No data</td></tr>';
}

// ============ USER MANAGEMENT (ADMIN ONLY) ============
function renderUsers() {
  const html = Object.entries(crmData.users).map(([username, user]) => {
    const leadCount = Object.values(crmData.leads).filter(l => l.assignedTo === username).length;
    return `
      <tr>
        <td><strong>${username}</strong></td>
        <td>${user.name}</td>
        <td><span class="role-badge role-${user.role}">${user.role}</span></td>
        <td>${leadCount}</td>
        <td>
          <button class="btn btn-secondary" style="padding: 6px 10px; font-size: 12px;" onclick="editUser('${username}')">Edit</button>
          <button class="btn btn-danger" style="padding: 6px 10px; font-size: 12px; margin-left: 5px;" onclick="deleteUser('${username}')">Delete</button>
        </td>
      </tr>
    `;
  }).join('');

  document.getElementById('usersBody').innerHTML = html;
}

function openUserModal() {
  currentEditUserId = null;
  document.getElementById('userName').value = '';
  document.getElementById('userName').disabled = false;
  document.getElementById('userPassword').value = '';
  document.getElementById('userFullName').value = '';
  document.getElementById('userRole').value = 'employee';
  document.getElementById('userModal').classList.add('active');
  document.getElementById('userModal').classList.add('show');
}

function closeUserModal() {
  document.getElementById('userModal').classList.remove('active');
  currentEditUserId = null;
}

function editUser(username) {
  currentEditUserId = username;
  const user = crmData.users[username];
  document.getElementById('userName').value = username;
  document.getElementById('userName').disabled = true;
  document.getElementById('userPassword').value = user.password;
  document.getElementById('userFullName').value = user.name;
  document.getElementById('userRole').value = user.role;
  document.getElementById('userModal').classList.add('active');
}

function saveUser() {
  const username = document.getElementById('userName').value.trim();
  const password = document.getElementById('userPassword').value;
  const name = document.getElementById('userFullName').value.trim();
  const role = document.getElementById('userRole').value;

  if (!username || !password || !name) {
    alert('All fields are required');
    return;
  }

  if (currentEditUserId) {
    // Edit existing
    delete crmData.users[currentEditUserId];
  }

  crmData.users[username] = { username, password, name, role };
  saveData();
  closeUserModal();
  document.getElementById('userName').disabled = false;
  renderUsers();
  updateAssigneeSelect();
  alert('User saved successfully!');
}

function deleteUser(username) {
  if (username === currentUser) {
    alert('Cannot delete your own user');
    return;
  }
  if (confirm('Delete this user?')) {
    delete crmData.users[username];
    saveData();
    renderUsers();
    updateAssigneeSelect();
  }
}

function updateAssigneeSelect() {
  const select = document.getElementById('leadAssignee');
  const employees = Object.entries(crmData.users)
    .filter(([_, user]) => user.role === 'employee')
    .map(([username, user]) => `<option value="${username}">${user.name}</option>`)
    .join('');

  select.innerHTML = '<option value="">Select Employee</option>' + employees;
}

function saveSettings() {
  const companyName = document.getElementById('companyName').value;
  crmData.settings.companyName = companyName;
  saveData();
  alert('Settings saved!');
}

// ============ UTILITIES ============
function getEmployeeName(username) {
  return crmData.users[username]?.name || 'Unassigned';
}

function formatStatus(status) {
  const map = {
    'new': '🆕 New',
    'contacted': '✅ Contacted',
    'interested': '👍 Interested',
    'meeting': '📞 Meeting',
    'closed': '🎯 Won'
  };
  return map[status] || status;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function exportData() {
  const user = crmData.users[currentUser];
  let leads = Object.values(crmData.leads);

  if (user.role === 'employee') {
    leads = leads.filter(lead => lead.assignedTo === currentUser);
  }

  const headers = ['Name', 'Phone', 'Assigned To', 'Status', 'Call Time', 'Reminder', 'Notes', 'Created'];
  const rows = leads.map(lead => [
    lead.name,
    lead.phone || '',
    getEmployeeName(lead.assignedTo),
    lead.status || '',
    lead.callTime || '',
    lead.reminder || '',
    lead.notes || '',
    new Date(lead.created).toLocaleDateString()
  ]);

  let csv = headers.join(',') + '\n';
  csv += rows.map(row =>
    row.map(cell => {
      if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
        return `"${cell.replace(/"/g, '""')}"`;
      }
      return cell;
    }).join(',')
  ).join('\n');

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `leads-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

// ============ DOCUMENT MANAGEMENT (DIGILOCKER) ============
function renderDocuments() {
  const user = crmData.users[currentUser];
  const leads = Object.values(crmData.leads);

  let clients = Object.values(crmData.clients || {});
  if (user.role === 'employee') {
    clients = clients.filter(c => c.assignedTo === currentUser);
  }

  const html = clients.map(client => {
    const clientDocs = crmData.documents[client.id] || [];
    return `
      <div class="client-doc-card" style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #3498db;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <div>
            <strong>${escapeHtml(client.name)}</strong><br>
            <span style="font-size: 12px; color: #7f8c8d;">📂 ${clientDocs.length} documents</span>
          </div>
          <button class="btn btn-primary" style="padding: 8px 15px; font-size: 12px;" onclick="openDocumentUpload('${client.id}')">+ Add Document</button>
        </div>
        <div style="margin-top: 10px;">
          ${clientDocs.length > 0 ? `
            <div style="border-top: 1px solid #ecf0f1; padding-top: 10px;">
              ${clientDocs.map(doc => `
                <div style="display: flex; justify-content: space-between; padding: 8px; background: #f9f9f9; border-radius: 4px; margin-bottom: 5px; font-size: 12px;">
                  <span>📄 ${escapeHtml(doc.name)} (${doc.type})</span>
                  <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="deleteDocument('${client.id}', '${doc.id}')">Delete</button>
                </div>
              `).join('')}
            </div>
          ` : `<span style="color: #7f8c8d; font-size: 12px;">No documents yet</span>`}
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('documentsContainer').innerHTML = html || '<div style="text-align: center; color: #7f8c8d; padding: 40px;">No clients with documents yet</div>';
}

function openDocumentUpload(clientId) {
  const modal = document.getElementById('documentModal');
  modal.dataset.clientId = clientId;
  modal.classList.add('active');

  const client = crmData.clients[clientId];
  document.getElementById('documentModalTitle').textContent = `Add Document for ${client.name}`;
}

function closeDocumentModal() {
  document.getElementById('documentModal').classList.remove('active');
  document.getElementById('documentName').value = '';
  document.getElementById('documentType').value = 'Other';
}

function uploadDocument() {
  const clientId = document.getElementById('documentModal').dataset.clientId;
  const docName = document.getElementById('documentName').value.trim();
  const docType = document.getElementById('documentType').value;

  if (!docName) {
    alert('Please enter document name');
    return;
  }

  if (!crmData.documents[clientId]) {
    crmData.documents[clientId] = [];
  }

  crmData.documents[clientId].push({
    id: 'doc_' + Date.now(),
    name: docName,
    type: docType,
    uploadedAt: new Date().toISOString(),
    uploadedBy: currentUser
  });

  saveData();
  closeDocumentModal();
  renderDocuments();

  alert('✅ Document uploaded successfully!');
}

function deleteDocument(clientId, docId) {
  if (!confirm('Delete this document?')) return;

  if (crmData.documents[clientId]) {
    crmData.documents[clientId] = crmData.documents[clientId].filter(d => d.id !== docId);
    saveData();
    renderDocuments();
  }
}

// ============ MARKETING MATERIALS ============
function renderMarketing() {
  const materials = Object.values(crmData.marketingMaterials || {});

  if (materials.length === 0) {
    document.getElementById('marketingContainer').innerHTML = `
      <div style="text-align: center; color: #7f8c8d; padding: 40px;">
        No marketing materials yet. Click "+ Add Marketing Material" to get started.
      </div>
    `;
    return;
  }

  const html = materials.map(material => `
    <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <h3 style="margin: 0 0 5px 0; color: #2c3e50;">${escapeHtml(material.name)}</h3>
          <p style="margin: 0 0 8px 0; font-size: 12px; color: #7f8c8d;">
            <strong>Type:</strong> ${material.type} | <strong>Created:</strong> ${new Date(material.createdAt).toLocaleDateString()}
          </p>
          <p style="margin: 0 0 10px 0; color: #555; font-size: 13px;">${escapeHtml(material.description)}</p>
          ${material.link ? `<p style="margin: 0 0 10px 0; font-size: 12px;"><a href="${material.link}" target="_blank" style="color: #667eea;">View Link →</a></p>` : ''}
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn" style="background: #25D366; color: white; padding: 8px 12px; font-size: 12px;" onclick="prepareShare('${material.id}', 'whatsapp')">📱 WhatsApp</button>
          <button class="btn" style="background: #1F4788; color: white; padding: 8px 12px; font-size: 12px;" onclick="prepareShare('${material.id}', 'email')">✉️ Email</button>
          <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="deleteMaterial('${material.id}')">🗑️</button>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('marketingContainer').innerHTML = html;
}

function openMarketingModal() {
  document.getElementById('materialName').value = '';
  document.getElementById('materialType').value = 'Brochure';
  document.getElementById('materialDescription').value = '';
  document.getElementById('materialLink').value = '';
  document.getElementById('marketingModal').style.display = 'flex';
}

function closeMarketingModal() {
  document.getElementById('marketingModal').style.display = 'none';
}

function saveMaterial() {
  const name = document.getElementById('materialName').value.trim();
  const type = document.getElementById('materialType').value;
  const description = document.getElementById('materialDescription').value.trim();
  const link = document.getElementById('materialLink').value.trim();

  if (!name) {
    alert('Please enter material name');
    return;
  }

  const materialId = 'mat_' + Date.now();
  crmData.marketingMaterials[materialId] = {
    id: materialId,
    name: name,
    type: type,
    description: description,
    link: link,
    createdAt: new Date().toISOString(),
    createdBy: currentUser
  };

  saveData();
  closeMarketingModal();
  renderMarketing();
  alert('✅ Marketing material added successfully!');
}

function deleteMaterial(materialId) {
  if (!confirm('Delete this marketing material?')) return;
  delete crmData.marketingMaterials[materialId];
  saveData();
  renderMarketing();
}

function prepareShare(materialId, platform) {
  const material = crmData.marketingMaterials[materialId];
  if (!material) return;

  const leads = Object.values(crmData.leads);
  const clientsList = document.getElementById('clientsList');

  clientsList.innerHTML = leads.map(lead => `
    <div style="padding: 10px; border-bottom: 1px solid #eee;">
      <label style="display: flex; align-items: center; cursor: pointer;">
        <input type="checkbox" data-lead-id="${lead.id}" style="margin-right: 10px;">
        <span>${escapeHtml(lead.name)} - ${lead.phone || 'No phone'}</span>
      </label>
    </div>
  `).join('');

  document.getElementById('materialPreview').innerHTML = `
    <strong>${escapeHtml(material.name)}</strong><br>
    <small style="color: #7f8c8d;">${material.type}</small><br><br>
    <p>${escapeHtml(material.description)}</p>
    ${material.link ? `<a href="${material.link}" target="_blank" style="color: #667eea;">View: ${material.link}</a>` : ''}
  `;

  window.currentShareMaterial = { id: materialId, platform: platform };
  document.getElementById('shareMarketingModal').style.display = 'flex';
}

function closeShareModal() {
  document.getElementById('shareMarketingModal').style.display = 'none';
  window.currentShareMaterial = null;
}

function shareViaWhatsApp() {
  const material = crmData.marketingMaterials[window.currentShareMaterial.id];
  const selectedLeads = Array.from(document.querySelectorAll('#clientsList input[type="checkbox"]:checked'))
    .map(cb => crmData.leads[cb.dataset.leadId]);

  if (selectedLeads.length === 0) {
    alert('Please select at least one client');
    return;
  }

  selectedLeads.forEach(lead => {
    if (!lead.phone) {
      alert(`${lead.name} doesn't have a phone number`);
      return;
    }

    const message = `Hi ${lead.name},\n\n📢 ${material.name}\n\n${material.description}${material.link ? `\n\nView: ${material.link}` : ''}\n\n- ArthaInvest`;
    const encoded = encodeURIComponent(message);
    const whatsappUrl = `https://wa.me/${lead.phone}?text=${encoded}`;
    window.open(whatsappUrl, '_blank');
  });

  closeShareModal();
  alert('✅ WhatsApp links opened for selected clients');
}

function shareViaEmail() {
  const material = crmData.marketingMaterials[window.currentShareMaterial.id];
  const selectedLeads = Array.from(document.querySelectorAll('#clientsList input[type="checkbox"]:checked'))
    .map(cb => crmData.leads[cb.dataset.leadId]);

  if (selectedLeads.length === 0) {
    alert('Please select at least one client');
    return;
  }

  selectedLeads.forEach(lead => {
    if (!lead.email) {
      alert(`${lead.name} doesn't have an email address`);
      return;
    }

    const subject = encodeURIComponent(`${material.name} - ArthaInvest`);
    const body = encodeURIComponent(`Hi ${lead.name},\n\n${material.description}${material.link ? `\n\nView: ${material.link}` : ''}\n\nBest regards,\nArthaInvest Team`);
    const mailtoUrl = `mailto:${lead.email}?subject=${subject}&body=${body}`;
    window.open(mailtoUrl);
  });

  closeShareModal();
  alert('✅ Email clients opened for selected clients');
}

// ============ CAMPAIGN MANAGEMENT ============
function renderCampaigns() {
  const campaigns = Object.values(crmData.campaigns || {}).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  if (campaigns.length === 0) {
    document.getElementById('campaignsContainer').innerHTML = `
      <div style="text-align: center; color: #7f8c8d; padding: 40px;">
        No campaigns yet. Click "+ Create Campaign" to get started.
      </div>
    `;
    return;
  }

  const html = campaigns.map(campaign => `
    <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <h3 style="margin: 0 0 5px 0; color: #2c3e50;">${escapeHtml(campaign.name)}</h3>
          <p style="margin: 0 0 8px 0; font-size: 12px; color: #7f8c8d;">
            <strong>Type:</strong> ${campaign.type} | <strong>Sent:</strong> ${campaign.recipients ? Object.keys(campaign.recipients).length : 0} | <strong>Created:</strong> ${new Date(campaign.createdAt).toLocaleDateString()}
          </p>
          <p style="margin: 0 0 10px 0; color: #555; font-size: 13px;">${escapeHtml(campaign.description)}</p>
          ${campaign.scheduledDate ? `<p style="margin: 0; font-size: 12px; color: #667eea;"><strong>Scheduled:</strong> ${campaign.scheduledDate}</p>` : ''}
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="viewCampaignDetails('${campaign.id}')">👁️ View</button>
          <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="deleteCampaign('${campaign.id}')">🗑️</button>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('campaignsContainer').innerHTML = html;
}

function openCampaignModal() {
  document.getElementById('campaignName').value = '';
  document.getElementById('campaignType').value = 'Email';
  document.getElementById('campaignDescription').value = '';
  document.getElementById('campaignScheduleDate').value = '';
  document.getElementById('campaignModal').style.display = 'flex';
}

function closeCampaignModal() {
  document.getElementById('campaignModal').style.display = 'none';
}

function saveCampaign() {
  const name = document.getElementById('campaignName').value.trim();
  const type = document.getElementById('campaignType').value;
  const description = document.getElementById('campaignDescription').value.trim();
  const scheduledDate = document.getElementById('campaignScheduleDate').value;

  if (!name || !description) {
    alert('Campaign name and description are required');
    return;
  }

  const campaignId = 'camp_' + Date.now();
  crmData.campaigns[campaignId] = {
    id: campaignId,
    name: name,
    type: type,
    description: description,
    scheduledDate: scheduledDate,
    createdAt: new Date().toISOString(),
    createdBy: currentUser,
    recipients: {},
    status: scheduledDate ? 'Scheduled' : 'Draft'
  };

  saveData();
  closeCampaignModal();
  renderCampaigns();
  alert('✅ Campaign created successfully!');
}

function deleteCampaign(campaignId) {
  if (!confirm('Delete this campaign?')) return;
  delete crmData.campaigns[campaignId];
  saveData();
  renderCampaigns();
}

function viewCampaignDetails(campaignId) {
  const campaign = crmData.campaigns[campaignId];
  if (!campaign) return;

  const recipientCount = Object.keys(campaign.recipients || {}).length;
  const details = `
    Campaign: ${campaign.name}
    Type: ${campaign.type}
    Status: ${campaign.status}
    Recipients Sent: ${recipientCount}
    Created: ${new Date(campaign.createdAt).toLocaleString()}
    Created By: ${getEmployeeName(campaign.createdBy)}
    Description: ${campaign.description}
  `;
  alert(details);
}

// ============ DEAL/OPPORTUNITY TRACKING ============
function renderDeals() {
  const deals = Object.values(crmData.deals || {}).sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  if (deals.length === 0) {
    document.getElementById('dealsContainer').innerHTML = `
      <div style="text-align: center; color: #7f8c8d; padding: 40px;">
        No deals yet. Create a deal from a lead to get started.
      </div>
    `;
    return;
  }

  const html = deals.map(deal => {
    const lead = crmData.leads[deal.leadId];
    return `
    <div style="background: white; border-left: 4px solid ${deal.stage === 'closed' ? '#27ae60' : deal.stage === 'negotiation' ? '#f39c12' : '#3498db'}; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <h3 style="margin: 0 0 5px 0; color: #2c3e50;">${escapeHtml(deal.name)}</h3>
          <p style="margin: 0 0 5px 0; font-size: 12px; color: #7f8c8d;">Client: ${lead ? escapeHtml(lead.name) : 'Unknown'}</p>
          <p style="margin: 0 0 5px 0; font-size: 14px; color: #27ae60;"><strong>Amount: ₹${deal.amount.toLocaleString()}</strong></p>
          <p style="margin: 0 0 5px 0; font-size: 12px; color: #7f8c8d;">
            Stage: <strong>${deal.stage}</strong> | Probability: <strong>${deal.probability}%</strong> | Expected Close: ${deal.expectedCloseDate}
          </p>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="editDeal('${deal.id}')">✏️ Edit</button>
          <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="deleteDeal('${deal.id}')">🗑️</button>
        </div>
      </div>
    </div>
  `;
  }).join('');

  document.getElementById('dealsContainer').innerHTML = html;
}

function openDealModal() {
  const leadId = prompt('Enter Lead ID (or leave blank to create new):');
  if (leadId === null) return;

  document.getElementById('dealName').value = '';
  document.getElementById('dealAmount').value = '';
  document.getElementById('dealStage').value = 'proposal';
  document.getElementById('dealProbability').value = 50;
  document.getElementById('dealExpectedClose').value = '';
  document.getElementById('dealLeadId').value = leadId || '';
  document.getElementById('dealModal').style.display = 'flex';
}

function closeDealModal() {
  document.getElementById('dealModal').style.display = 'none';
}

function saveDeal() {
  const name = document.getElementById('dealName').value.trim();
  const amount = parseFloat(document.getElementById('dealAmount').value);
  const stage = document.getElementById('dealStage').value;
  const probability = parseInt(document.getElementById('dealProbability').value);
  const expectedCloseDate = document.getElementById('dealExpectedClose').value;
  const leadId = document.getElementById('dealLeadId').value;

  if (!name || !amount || !leadId) {
    alert('Deal name, amount, and lead are required');
    return;
  }

  const dealId = 'deal_' + Date.now();
  crmData.deals[dealId] = {
    id: dealId,
    name: name,
    amount: amount,
    stage: stage,
    probability: probability,
    expectedCloseDate: expectedCloseDate,
    leadId: leadId,
    createdAt: new Date().toISOString(),
    createdBy: currentUser,
    status: 'open'
  };

  saveData();
  closeDealModal();
  renderDeals();
  alert('✅ Deal created successfully!');
}

function editDeal(dealId) {
  const deal = crmData.deals[dealId];
  if (!deal) return;

  document.getElementById('dealName').value = deal.name;
  document.getElementById('dealAmount').value = deal.amount;
  document.getElementById('dealStage').value = deal.stage;
  document.getElementById('dealProbability').value = deal.probability;
  document.getElementById('dealExpectedClose').value = deal.expectedCloseDate;
  document.getElementById('dealLeadId').value = deal.leadId;
  window.currentEditDealId = dealId;
  document.getElementById('dealModal').style.display = 'flex';
}

function deleteDeal(dealId) {
  if (!confirm('Delete this deal?')) return;
  delete crmData.deals[dealId];
  saveData();
  renderDeals();
}

// ============ LEAD SCORING ============
function calculateLeadScore(leadId) {
  const lead = crmData.leads[leadId];
  if (!lead) return 0;

  let score = 0;

  // Budget scoring (max 30 points)
  const budget = parseInt(lead.budget) || 0;
  score += Math.min(30, (budget / 100000) * 10);

  // Status scoring (max 40 points)
  const statusScores = { new: 5, contacted: 15, interested: 25, meeting: 35, closed: 40 };
  score += statusScores[lead.status] || 0;

  // Days since contact (max 20 points)
  if (lead.lastContact) {
    const daysSince = Math.floor((Date.now() - new Date(lead.lastContact)) / (1000 * 60 * 60 * 24));
    score += Math.max(0, 20 - (daysSince / 10));
  }

  // Documents uploaded (max 10 points)
  const docCount = (crmData.documents[leadId] || []).length;
  score += Math.min(10, docCount * 2);

  crmData.leadScores[leadId] = Math.round(score);
  return Math.round(score);
}

function renderLeadScores() {
  const leads = Object.values(crmData.leads || {});
  const scores = leads.map(lead => ({
    ...lead,
    score: calculateLeadScore(lead.id)
  })).sort((a, b) => b.score - a.score);

  if (scores.length === 0) {
    document.getElementById('scoresContainer').innerHTML = '<div style="text-align: center; color: #7f8c8d; padding: 40px;">No leads to score.</div>';
    return;
  }

  const html = scores.map(lead => {
    const scoreColor = lead.score >= 80 ? '#27ae60' : lead.score >= 50 ? '#f39c12' : '#e74c3c';
    return `
    <div style="background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <h4 style="margin: 0 0 5px 0;">${escapeHtml(lead.name)}</h4>
        <p style="margin: 0; font-size: 12px; color: #7f8c8d;">Budget: ₹${lead.budget || 'N/A'} | Status: ${lead.status}</p>
      </div>
      <div style="text-align: center; background: ${scoreColor}; color: white; padding: 10px 15px; border-radius: 8px; font-weight: bold; font-size: 18px;">
        ${lead.score}/100
      </div>
    </div>
  `;
  }).join('');

  document.getElementById('scoresContainer').innerHTML = html;
}

// ============ TASK MANAGEMENT ============
function renderTasks() {
  const tasks = Object.values(crmData.tasks || {}).sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate));
  const user = crmData.users[currentUser];

  const myTasks = tasks.filter(t => t.assignedTo === currentUser || t.createdBy === currentUser);

  if (myTasks.length === 0) {
    document.getElementById('tasksContainer').innerHTML = '<div style="text-align: center; color: #7f8c8d; padding: 40px;">No tasks. Create one to get started!</div>';
    return;
  }

  const html = myTasks.map(task => {
    const isPriority = task.priority === 'high';
    return `
    <div style="background: white; border-left: 4px solid ${isPriority ? '#e74c3c' : '#3498db'}; padding: 15px; margin-bottom: 10px; border-radius: 4px;">
      <div style="display: flex; justify-content: space-between; align-items: start;">
        <div style="flex: 1;">
          <h4 style="margin: 0 0 5px 0; text-decoration: ${task.status === 'completed' ? 'line-through' : 'none'};  color: #2c3e50;">${escapeHtml(task.name)}</h4>
          <p style="margin: 0 0 5px 0; font-size: 12px; color: #7f8c8d;">Due: ${task.dueDate} | Priority: <strong>${task.priority}</strong> | Status: <strong>${task.status}</strong></p>
        </div>
        <button class="btn btn-secondary" style="padding: 8px 12px; font-size: 12px;" onclick="completeTask('${task.id}')">${task.status === 'completed' ? '✓ Done' : 'Mark Done'}</button>
      </div>
    </div>
  `;
  }).join('');

  document.getElementById('tasksContainer').innerHTML = html;
}

function openTaskModal() {
  document.getElementById('taskName').value = '';
  document.getElementById('taskDueDate').value = '';
  document.getElementById('taskPriority').value = 'medium';
  document.getElementById('taskModal').style.display = 'flex';
}

function closeTaskModal() {
  document.getElementById('taskModal').style.display = 'none';
}

function saveTask() {
  const name = document.getElementById('taskName').value.trim();
  const dueDate = document.getElementById('taskDueDate').value;
  const priority = document.getElementById('taskPriority').value;

  if (!name || !dueDate) {
    alert('Task name and due date are required');
    return;
  }

  const taskId = 'task_' + Date.now();
  crmData.tasks[taskId] = {
    id: taskId,
    name: name,
    dueDate: dueDate,
    priority: priority,
    status: 'open',
    createdBy: currentUser,
    assignedTo: currentUser,
    createdAt: new Date().toISOString()
  };

  saveData();
  closeTaskModal();
  renderTasks();
  alert('✅ Task created successfully!');
}

function completeTask(taskId) {
  const task = crmData.tasks[taskId];
  if (!task) return;
  task.status = task.status === 'completed' ? 'open' : 'completed';
  saveData();
  renderTasks();
}

// ============ DIALLER SYSTEM ============
let diallerState = {
  currentNumber: '',
  isCallActive: false,
  callStartTime: null,
  callDuration: 0,
  currentCallId: null,
  timerInterval: null
};

function renderDialler() {
  updateDialDisplay();
  renderQuickContacts();
  renderCallHistory();
  updateCallStats();
}

function dialPad(digit) {
  if (diallerState.currentNumber.length < 15) {
    diallerState.currentNumber += digit;
    updateDialDisplay();
  }
}

function updateDialDisplay() {
  const display = document.getElementById('dialDisplay');
  if (display) {
    display.textContent = diallerState.currentNumber || '0';
  }
}

function clearDial() {
  diallerState.currentNumber = '';
  updateDialDisplay();
}

function startCall() {
  const number = diallerState.currentNumber.trim();

  if (!number) {
    alert('Please enter a phone number');
    return;
  }

  if (!/^\d+[-.\s]?\d+/.test(number)) {
    alert('Please enter a valid phone number');
    return;
  }

  diallerState.isCallActive = true;
  diallerState.callStartTime = Date.now();
  diallerState.currentCallId = 'call_' + Date.now();

  document.querySelector('[onclick="startCall()"]').textContent = '📞 Calling...';
  document.querySelector('[onclick="startCall()"]').disabled = true;

  startCallTimer();

  setTimeout(() => {
    alert(`📞 Initiating call to: ${number}\n\n(In a real system, this would use Twilio or similar API)`);
  }, 500);
}

function startCallTimer() {
  diallerState.timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - diallerState.callStartTime) / 1000);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;

    const display = document.getElementById('dialDisplay');
    if (display) {
      display.textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    }
  }, 1000);
}

function endCall() {
  if (!diallerState.isCallActive) {
    return;
  }

  clearInterval(diallerState.timerInterval);

  const duration = Math.floor((Date.now() - diallerState.callStartTime) / 1000);
  const mins = Math.floor(duration / 60);
  const secs = duration % 60;

  const callRecord = {
    id: diallerState.currentCallId,
    number: diallerState.currentNumber,
    duration: duration,
    durationFormatted: `${mins}m ${secs}s`,
    timestamp: new Date().toISOString(),
    type: 'outgoing',
    status: 'completed',
    outcome: '',
    priority: 'none',
    callNotes: '',
    user: currentUser
  };

  if (!crmData.callHistory) crmData.callHistory = {};
  crmData.callHistory[callRecord.id] = callRecord;

  saveData();

  diallerState.isCallActive = false;
  diallerState.currentNumber = '';
  diallerState.callStartTime = null;

  document.querySelector('[onclick="startCall()"]').textContent = '📞 Call';
  document.querySelector('[onclick="startCall()"]').disabled = false;

  updateDialDisplay();

  setTimeout(() => {
    showCallNotesModal();
  }, 500);
}

function renderQuickContacts() {
  const container = document.getElementById('quickContactsList');
  if (!container) return;

  const leads = Object.values(crmData.leads || {}).slice(0, 5);

  if (leads.length === 0) {
    container.innerHTML = '<div style="color: #7f8c8d; text-align: center; padding: 20px;">No contacts available</div>';
    return;
  }

  const html = leads.map(lead => `
    <div style="padding: 10px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: bold; color: #2c3e50;">${lead.name}</div>
        <div style="font-size: 12px; color: #7f8c8d;">${lead.phone}</div>
      </div>
      <button class="btn" onclick="quickDial('${lead.phone}')" style="padding: 5px 10px; font-size: 12px;">Call</button>
    </div>
  `).join('');

  container.innerHTML = html;
}

function quickDial(phone) {
  diallerState.currentNumber = phone;
  updateDialDisplay();
  startCall();
}

function renderCallHistory() {
  const container = document.getElementById('callHistoryContainer');
  if (!container) return;

  const calls = Object.values(crmData.callHistory || {}).sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  if (calls.length === 0) {
    container.innerHTML = '<div style="color: #7f8c8d; text-align: center; padding: 30px;">No calls yet</div>';
    return;
  }

  const html = calls.map(call => {
    const date = new Date(call.timestamp);
    const timeStr = date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    const dateStr = date.toLocaleDateString('en-IN');

    return `
      <div style="padding: 12px; border: 1px solid #f0f0f0; border-radius: 6px; margin-bottom: 10px; background: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: start;">
          <div>
            <div style="font-weight: bold; color: #2c3e50; font-size: 14px;">📞 ${call.number}</div>
            <div style="font-size: 12px; color: #7f8c8d; margin-top: 4px;">
              ${dateStr} at ${timeStr}
            </div>
            <div style="font-size: 12px; color: #27ae60; margin-top: 4px;">
              ⏱️ ${call.durationFormatted}
            </div>
          </div>
          <button class="btn btn-secondary" onclick="deleteCallRecord('${call.id}')" style="padding: 5px 10px; font-size: 11px;">Delete</button>
        </div>
        ${call.notes ? `<div style="margin-top: 8px; font-size: 12px; color: #555; background: white; padding: 8px; border-radius: 4px;">📝 ${call.notes}</div>` : ''}
      </div>
    `;
  }).join('');

  container.innerHTML = html;
}

function updateCallStats() {
  const calls = Object.values(crmData.callHistory || {});
  const totalCalls = calls.length;
  const totalDuration = calls.reduce((sum, call) => sum + (call.duration || 0), 0);
  const hours = Math.floor(totalDuration / 3600);
  const mins = Math.floor((totalDuration % 3600) / 60);

  const callsCountEl = document.getElementById('totalCallsCount');
  const durationEl = document.getElementById('totalDurationCount');

  if (callsCountEl) callsCountEl.textContent = totalCalls;
  if (durationEl) {
    if (hours > 0) {
      durationEl.textContent = `${hours}h ${mins}m`;
    } else {
      durationEl.textContent = `${mins}m`;
    }
  }
}

function deleteCallRecord(callId) {
  if (confirm('Delete this call record?')) {
    delete crmData.callHistory[callId];
    saveData();
    renderDialler();
  }
}

// ============ CALL NOTES ============
function showCallNotesModal() {
  const phone = diallerState.currentNumber;
  const duration = document.getElementById('dialDisplay').textContent;
  const now = new Date().toLocaleString('en-IN');

  document.getElementById('callNotesPhone').textContent = phone || '-';
  document.getElementById('callNotesDuration').textContent = duration;
  document.getElementById('callNotesTime').textContent = now;

  document.getElementById('callOutcome').value = '';
  document.getElementById('callPriority').value = 'none';
  document.getElementById('callNotesText').value = '';

  document.getElementById('callNotesModal').style.display = 'flex';
}

function closeCallNotesModal() {
  document.getElementById('callNotesModal').style.display = 'none';
}

function saveCallNotes() {
  const outcome = document.getElementById('callOutcome').value;
  const priority = document.getElementById('callPriority').value;
  const notes = document.getElementById('callNotesText').value;

  if (!outcome) {
    alert('Please select a call outcome');
    return;
  }

  const callId = diallerState.currentCallId;
  if (crmData.callHistory && crmData.callHistory[callId]) {
    crmData.callHistory[callId].outcome = outcome;
    crmData.callHistory[callId].priority = priority;
    crmData.callHistory[callId].callNotes = notes;
  }

  saveData();
  closeCallNotesModal();
  renderDialler();
}

// ============ CALL MONITORING (ADMIN) ============
function renderCallMonitoring() {
  populateAgentFilter();
  updateCallMonitoringStats();
  filterCallMonitoring();
  displayCallHistoryTable(Object.values(crmData.callHistory || {}).sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  ));
}

function populateAgentFilter() {
  const select = document.getElementById('callMonitoringAgentFilter');
  if (!select) return;

  const agents = new Set();
  Object.values(crmData.callHistory || {}).forEach(call => {
    if (call.user) agents.add(call.user);
  });

  const options = Array.from(agents).sort();
  const currentValue = select.value;

  select.innerHTML = '<option value="">All Agents</option>' +
    options.map(agent => `<option value="${agent}">${crmData.users[agent]?.name || agent}</option>`).join('');

  select.value = currentValue;
}

function filterCallMonitoring() {
  const agent = document.getElementById('callMonitoringAgentFilter')?.value || '';
  const fromDate = document.getElementById('callMonitoringFromDate')?.value || '';
  const toDate = document.getElementById('callMonitoringToDate')?.value || '';
  const status = document.getElementById('callMonitoringStatusFilter')?.value || '';

  let calls = Object.values(crmData.callHistory || {});

  if (agent) calls = calls.filter(c => c.user === agent);
  if (status) calls = calls.filter(c => {
    if (status === 'completed') return c.status === 'completed';
    if (status === 'missed') return c.outcome === 'noresponse' || c.outcome === 'voicemail';
    if (status === 'pending') return c.priority && c.priority !== 'none';
    return true;
  });

  if (fromDate) {
    const from = new Date(fromDate);
    calls = calls.filter(c => new Date(c.timestamp) >= from);
  }

  if (toDate) {
    const to = new Date(toDate);
    to.setHours(23, 59, 59);
    calls = calls.filter(c => new Date(c.timestamp) <= to);
  }

  displayCallHistoryTable(calls.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)));
  updateCallMonitoringStats();
  renderAgentPerformance(calls);
}

function displayCallHistoryTable(calls) {
  const tbody = document.getElementById('callHistoryTableBody');
  if (!tbody) return;

  if (calls.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: #7f8c8d;">No calls found</td></tr>';
    return;
  }

  const html = calls.map(call => {
    const date = new Date(call.timestamp);
    const timeStr = date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    const dateStr = date.toLocaleDateString('en-IN');
    const agentName = crmData.users[call.user]?.name || call.user || 'Unknown';
    const outcome = call.outcome ? call.outcome.replace(/_/g, ' ').toUpperCase() : 'NOT RECORDED';
    const outcomeEmoji = {
      'CONNECTED & TALKED': '✅',
      'LEFT VOICEMAIL': '📧',
      'LINE BUSY': '📞',
      'NO RESPONSE': '❌',
      'WRONG NUMBER': '❓',
      'WILL CALL BACK': '⏳'
    };

    return `
      <tr style="border-bottom: 1px solid #f0f0f0;">
        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${agentName}</td>
        <td style="padding: 12px; color: #2c3e50;">${call.number}</td>
        <td style="padding: 12px; color: #7f8c8d; font-size: 12px;">${dateStr} ${timeStr}</td>
        <td style="padding: 12px; color: #27ae60; font-weight: 500;">${call.durationFormatted || '0m'}</td>
        <td style="padding: 12px; color: #2c3e50;">${outcomeEmoji[outcome] || ''} ${outcome}</td>
        <td style="padding: 12px; font-size: 12px;">${call.callNotes || '-'}</td>
        <td style="padding: 12px;">
          <button class="btn btn-secondary" onclick="viewCallDetail('${call.id}')" style="padding: 5px 10px; font-size: 11px;">View</button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = html;
}

function displayCallMonitoringTable(calls) {
  const tbody = document.getElementById('callMonitoringTableBody');
  if (!tbody) return;

  if (calls.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: #7f8c8d;">No calls found</td></tr>';
    return;
  }

  const html = calls.map(call => {
    const date = new Date(call.timestamp);
    const timeStr = date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    const dateStr = date.toLocaleDateString('en-IN');
    const agentName = crmData.users[call.user]?.name || call.user || 'Unknown';
    const outcome = call.outcome ? call.outcome.replace('_', ' ').toUpperCase() : '-';
    const outcomeEmoji = {
      'CONNECTED & TALKED': '✅',
      'LEFT VOICEMAIL': '📧',
      'LINE BUSY': '📞',
      'NO RESPONSE': '❌',
      'WRONG NUMBER': '❓',
      'WILL CALL BACK': '⏳'
    };

    return `
      <tr style="border-bottom: 1px solid #f0f0f0;">
        <td style="padding: 12px; color: #2c3e50; font-weight: 500;">${agentName}</td>
        <td style="padding: 12px; color: #2c3e50;">${call.number}</td>
        <td style="padding: 12px; color: #7f8c8d; font-size: 12px;">${dateStr} ${timeStr}</td>
        <td style="padding: 12px; color: #27ae60; font-weight: 500;">${call.durationFormatted || '0m'}</td>
        <td style="padding: 12px; color: #2c3e50;">${outcomeEmoji[outcome] || ''} ${outcome}</td>
        <td style="padding: 12px; color: #555; font-size: 12px;">${call.callNotes || '-'}</td>
        <td style="padding: 12px;">
          <button class="btn btn-secondary" onclick="viewCallDetail('${call.id}')" style="padding: 5px 10px; font-size: 11px;">View</button>
        </td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = html;
}

function updateCallMonitoringStats() {
  const calls = Object.values(crmData.callHistory || {});
  const totalCalls = calls.length;
  const totalDuration = calls.reduce((sum, c) => sum + (c.duration || 0), 0);
  const avgDuration = totalCalls > 0 ? Math.floor(totalDuration / totalCalls) : 0;

  const agents = new Set(calls.map(c => c.user));

  const hours = Math.floor(totalDuration / 3600);
  const mins = Math.floor((totalDuration % 3600) / 60);
  const avgMins = Math.floor(avgDuration / 60);
  const avgSecs = avgDuration % 60;

  const els = {
    totalCallsAdmin: document.getElementById('totalCallsAdmin'),
    totalDurationAdmin: document.getElementById('totalDurationAdmin'),
    avgCallDurationAdmin: document.getElementById('avgCallDurationAdmin'),
    agentCountAdmin: document.getElementById('agentCountAdmin')
  };

  if (els.totalCallsAdmin) els.totalCallsAdmin.textContent = totalCalls;
  if (els.totalDurationAdmin) els.totalDurationAdmin.textContent = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  if (els.avgCallDurationAdmin) els.avgCallDurationAdmin.textContent = `${avgMins}m ${avgSecs}s`;
  if (els.agentCountAdmin) els.agentCountAdmin.textContent = agents.size;
}

function renderAgentPerformance(filteredCalls = null) {
  const container = document.getElementById('agentPerformanceContainer');
  if (!container) return;

  const calls = filteredCalls || Object.values(crmData.callHistory || {});
  const agentStats = {};

  calls.forEach(call => {
    const agent = call.user || 'Unknown';
    if (!agentStats[agent]) {
      agentStats[agent] = {
        name: crmData.users[agent]?.name || agent,
        calls: 0,
        duration: 0,
        outcomes: {}
      };
    }
    agentStats[agent].calls++;
    agentStats[agent].duration += call.duration || 0;
    if (call.outcome) {
      agentStats[agent].outcomes[call.outcome] = (agentStats[agent].outcomes[call.outcome] || 0) + 1;
    }
  });

  const html = Object.entries(agentStats).map(([agent, stats]) => {
    const avgDuration = stats.calls > 0 ? Math.floor(stats.duration / stats.calls) : 0;
    const hours = Math.floor(stats.duration / 3600);
    const mins = Math.floor((stats.duration % 3600) / 60);

    return `
      <div style="padding: 15px; border: 1px solid #f0f0f0; border-radius: 6px; margin-bottom: 12px; background: #fafafa;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <div style="font-weight: bold; color: #2c3e50;">${stats.name}</div>
          <div style="font-size: 12px; color: #7f8c8d;">${stats.calls} calls • ${hours}h ${mins}m total</div>
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 12px;">
          <div><span style="color: #7f8c8d;">Avg Duration:</span> <span style="font-weight: bold; color: #2c3e50;">${Math.floor(avgDuration / 60)}m ${avgDuration % 60}s</span></div>
          <div><span style="color: #7f8c8d;">Connected:</span> <span style="font-weight: bold; color: #27ae60;">${stats.outcomes['connected'] || 0}</span></div>
          <div><span style="color: #7f8c8d;">No Response:</span> <span style="font-weight: bold; color: #e74c3c;">${stats.outcomes['noresponse'] || 0}</span></div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = html || '<div style="color: #7f8c8d; text-align: center; padding: 30px;">No performance data available</div>';
}


async function loadBusinessData() {
  try {
    if (window.electronAPI && window.electronAPI.importBusinessData) {
      const result = await window.electronAPI.importBusinessData();
      if (result.success && result.leadsCount > 0) {
        processImportedLeads(result.data);
      }
    }
  } catch (error) {
    console.log('Auto-import: Data already loaded or no external files');
  }
}

async function importDataFromFiles() {
  try {
    const result = await window.electronAPI.importBusinessData();
    if (result.success) {
      processImportedLeads(result.data);
      renderDashboard();
      updateUI();
      console.log(`✅ Synced: ${result.leadsCount} leads, ${result.dealsCount} opportunities`);
    }
  } catch (error) {
    console.error('Import error:', error);
  }
}

function processImportedLeads(leadsData) {
  if (!leadsData || leadsData.length === 0) return;

  leadsData.forEach((lead, index) => {
    const leadId = `imported_${Date.now()}_${index}`;
    if (!crmData.leads[leadId]) {
      crmData.leads[leadId] = {
        id: leadId,
        name: lead.name || lead.Name || lead.CLIENT_NAME || 'Unknown',
        phone: lead.phone || lead.Phone || lead.MOBILE || '',
        email: lead.email || lead.Email || '',
        status: lead.status || 'contacted',
        budget: parseFloat(lead.budget || lead.Budget || 0),
        source: 'business_data',
        createdAt: new Date().toISOString(),
        lastContact: new Date().toISOString()
      };
    }
  });

  saveData();
}

function viewCallDetail(callId) {
  const call = crmData.callHistory[callId];
  if (!call) return;

  const agentName = crmData.users[call.user]?.name || call.user;
  const date = new Date(call.timestamp);
  alert(`Call Details\n\nAgent: ${agentName}\nNumber: ${call.number}\nDuration: ${call.durationFormatted}\nOutcome: ${call.outcome || 'Not recorded'}\nNotes: ${call.callNotes || 'No notes'}`);
}

// ============ WHATSAPP LOGGING ============
function openWhatsAppLogger() {
  const now = new Date().toISOString().slice(0, 16);
  document.getElementById('whatsappPhone').value = '';
  document.getElementById('whatsappContactName').value = '';
  document.getElementById('whatsappMessageType').value = '';
  document.getElementById('whatsappMessagePreview').value = '';
  document.getElementById('whatsappStatus').value = 'delivered';
  document.getElementById('whatsappDateTime').value = now;
  document.getElementById('whatsappNotes').value = '';
  document.getElementById('whatsappLoggerModal').style.display = 'flex';
}

function closeWhatsAppLogger() {
  document.getElementById('whatsappLoggerModal').style.display = 'none';
}

function saveWhatsAppMessage() {
  const phone = document.getElementById('whatsappPhone').value.trim();
  const contactName = document.getElementById('whatsappContactName').value.trim();
  const messageType = document.getElementById('whatsappMessageType').value;
  const messageText = document.getElementById('whatsappMessagePreview').value.trim();
  const status = document.getElementById('whatsappStatus').value;
  const dateTime = document.getElementById('whatsappDateTime').value;
  const notes = document.getElementById('whatsappNotes').value.trim();

  if (!phone || !messageType || !messageText) {
    alert('Please fill in phone number, message type, and message');
    return;
  }

  const whatsappId = 'wa_' + Date.now();
  const timestamp = dateTime ? new Date(dateTime).toISOString() : new Date().toISOString();

  const whatsappRecord = {
    id: whatsappId,
    phone: phone,
    contactName: contactName || phone,
    messageType: messageType,
    messagePreview: messageText,
    status: status,
    timestamp: timestamp,
    notes: notes,
    user: currentUser
  };

  if (!crmData.whatsappHistory) crmData.whatsappHistory = {};
  crmData.whatsappHistory[whatsappId] = whatsappRecord;

  saveData();
  closeWhatsAppLogger();
  alert('✅ WhatsApp message logged successfully!');
  renderDialler();
}

function openCommunicationHistory() {
  navigateTo('callMonitoring');
}

function startDiallerMode() {
  navigateTo('dialler');
}

// ============ UNIFIED COMMUNICATION LOG ============
function renderCommunicationLog() {
  const calls = Object.values(crmData.callHistory || {}).map(call => ({
    ...call,
    type: 'call',
    contact: 'Phone Call',
    displayTime: new Date(call.timestamp).toLocaleString('en-IN')
  }));

  const whatsapps = Object.values(crmData.whatsappHistory || {}).map(wa => ({
    ...wa,
    type: 'whatsapp',
    contact: wa.contactName || wa.phone,
    displayTime: new Date(wa.timestamp).toLocaleString('en-IN')
  }));

  const allComm = [...calls, ...whatsapps].sort((a, b) =>
    new Date(b.timestamp) - new Date(a.timestamp)
  );

  return allComm;
}

function filterCommunicationType(type) {
  document.getElementById('commTypeAll').style.background = type === 'all' ? '#667eea' : '#95a5a6';
  document.getElementById('commTypeCall').style.background = type === 'call' ? '#667eea' : '#95a5a6';
  document.getElementById('commTypeWhatsapp').style.background = type === 'whatsapp' ? '#667eea' : '#95a5a6';

  const allComm = renderCommunicationLog();
  const filtered = type === 'all' ? allComm : allComm.filter(c => c.type === type);

  displayCommunicationTable(filtered);
}

function displayCommunicationTable(communications) {
  const tbody = document.getElementById('communicationTableBody');
  if (!tbody) return;

  if (communications.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 30px; color: #7f8c8d;">No communication found</td></tr>';
    return;
  }

  const html = communications.map(comm => {
    if (comm.type === 'call') {
      const agentName = crmData.users[comm.user]?.name || comm.user || 'Unknown';
      return `
        <tr style="border-bottom: 1px solid #f0f0f0;">
          <td style="padding: 12px; color: #2c3e50; font-weight: 500;">☎️ Call</td>
          <td style="padding: 12px; color: #2c3e50;">${agentName}</td>
          <td style="padding: 12px; color: #2c3e50;">${comm.number}</td>
          <td style="padding: 12px; color: #7f8c8d; font-size: 12px;">${comm.displayTime}</td>
          <td style="padding: 12px; color: #27ae60; font-weight: 500;">${comm.durationFormatted || '0m'}</td>
          <td style="padding: 12px; font-size: 12px;">
            <div style="color: #2c3e50;">Outcome: ${comm.outcome ? comm.outcome.replace(/_/g, ' ') : 'Not recorded'}</div>
            <div style="color: #7f8c8d; margin-top: 4px;">📝 ${comm.callNotes || 'No notes'}</div>
          </td>
          <td style="padding: 12px;">
            <button class="btn btn-secondary" onclick="viewCallDetail('${comm.id}')" style="padding: 5px 10px; font-size: 11px;">View</button>
          </td>
        </tr>
      `;
    } else {
      const agentName = crmData.users[comm.user]?.name || comm.user || 'Unknown';
      const typeEmoji = comm.messageType === 'sent' ? '📤' : comm.messageType === 'received' ? '📥' : '🎵';
      const statusIcon = comm.status === 'read' ? '👁️' : comm.status === 'delivered' ? '✅' : '⏳';

      return `
        <tr style="border-bottom: 1px solid #f0f0f0;">
          <td style="padding: 12px; color: #2c3e50; font-weight: 500;">💬 WhatsApp</td>
          <td style="padding: 12px; color: #2c3e50;">${comm.contactName || comm.phone}</td>
          <td style="padding: 12px; color: #2c3e50;">${comm.phone}</td>
          <td style="padding: 12px; color: #7f8c8d; font-size: 12px;">${comm.displayTime}</td>
          <td style="padding: 12px; color: #25D366; font-weight: 500;">${statusIcon} ${comm.status}</td>
          <td style="padding: 12px; font-size: 12px;">
            <div style="color: #2c3e50;">${typeEmoji} ${comm.messageType.replace(/_/g, ' ')}</div>
            <div style="color: #7f8c8d; margin-top: 4px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${comm.messagePreview}</div>
            ${comm.notes ? `<div style="color: #e74c3c; margin-top: 4px;">⚠️ ${comm.notes}</div>` : ''}
          </td>
          <td style="padding: 12px;">
            <button class="btn btn-secondary" onclick="viewWhatsAppDetail('${comm.id}')" style="padding: 5px 10px; font-size: 11px;">View</button>
          </td>
        </tr>
      `;
    }
  }).join('');

  tbody.innerHTML = html;
}

function viewWhatsAppDetail(waId) {
  const wa = crmData.whatsappHistory[waId];
  if (!wa) return;

  const agentName = crmData.users[wa.user]?.name || wa.user;
  alert(`WhatsApp Message\n\nAgent: ${agentName}\nContact: ${wa.contactName}\nPhone: ${wa.phone}\nType: ${wa.messageType}\nStatus: ${wa.status}\n\nMessage:\n${wa.messagePreview}\n\nNotes: ${wa.notes || 'No notes'}`);
}

// ============ SETTINGS ============
function saveMobileNumberSettings() {
  const mobileNumber = document.getElementById('settingsMobileNumber')?.value.trim();
  const agentName = document.getElementById('settingsAgentName')?.value.trim();

  if (!mobileNumber) {
    alert('Please enter a mobile number');
    return;
  }

  crmData.settings.agentMobileNumber = mobileNumber;
  crmData.settings.agentName = agentName || 'Agent';

  saveData();

  const statusEl = document.getElementById('mobileNumberStatus');
  if (statusEl) {
    statusEl.textContent = `✅ Mobile number ${mobileNumber} registered for tracking!`;
  }

  alert(`✅ Mobile number registered!\n\nAll calls and WhatsApp messages from ${mobileNumber} will now be tracked in the admin dashboard.`);
}

function saveCompanySettings() {
  const companyName = document.getElementById('settingsCompanyName')?.value.trim();
  const companyPhone = document.getElementById('settingsCompanyPhone')?.value.trim();
  const companyEmail = document.getElementById('settingsCompanyEmail')?.value.trim();
  const license = document.getElementById('settingsLicense')?.value.trim();

  crmData.settings.companyName = companyName || 'ArthaInvest Capital';
  crmData.settings.companyPhone = companyPhone;
  crmData.settings.companyEmail = companyEmail;
  crmData.settings.license = license;

  saveData();
  alert('✅ Company settings saved!');
}

function loadSettingsUI() {
  const settings = crmData.settings || {};

  const els = {
    settingsMobileNumber: document.getElementById('settingsMobileNumber'),
    settingsAgentName: document.getElementById('settingsAgentName'),
    settingsCompanyName: document.getElementById('settingsCompanyName'),
    settingsCompanyPhone: document.getElementById('settingsCompanyPhone'),
    settingsCompanyEmail: document.getElementById('settingsCompanyEmail'),
    settingsLicense: document.getElementById('settingsLicense')
  };

  if (els.settingsMobileNumber) els.settingsMobileNumber.value = settings.agentMobileNumber || '';
  if (els.settingsAgentName) els.settingsAgentName.value = settings.agentName || '';
  if (els.settingsCompanyName) els.settingsCompanyName.value = settings.companyName || 'ArthaInvest Capital';
  if (els.settingsCompanyPhone) els.settingsCompanyPhone.value = settings.companyPhone || '';
  if (els.settingsCompanyEmail) els.settingsCompanyEmail.value = settings.companyEmail || 'arthainvest.services@gmail.com';
  if (els.settingsLicense) els.settingsLicense.value = settings.license || 'ARN-267891 | POSP | DSA';

  if (settings.agentMobileNumber) {
    const statusEl = document.getElementById('mobileNumberStatus');
    if (statusEl) {
      statusEl.textContent = `✅ Tracking number: ${settings.agentMobileNumber}`;
    }
  }
}

// ============ DATA INTEGRATION ============

function exportAllData() {
  const dataExport = {
    exportDate: new Date().toLocaleString('en-IN'),
    settings: crmData.settings,
    summary: {
      totalLeads: Object.keys(crmData.leads || {}).length,
      totalDeals: Object.keys(crmData.deals || {}).length,
      totalCalls: Object.keys(crmData.callHistory || {}).length,
      totalWhatsAppMessages: Object.keys(crmData.whatsappHistory || {}).length,
      totalTasks: Object.keys(crmData.tasks || {}).length,
      totalCampaigns: Object.keys(crmData.campaigns || {}).length
    },
    data: crmData
  };

  const dataStr = JSON.stringify(dataExport, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `arthainvest-crm-backup-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  alert('✅ Data exported successfully!');
}

function clearAllData() {
  if (!confirm('⚠️ WARNING: This will delete ALL data in the CRM!\n\nAre you absolutely sure?\n\nClick OK to permanently delete all data.')) {
    return;
  }

  if (!confirm('⚠️ FINAL WARNING: This cannot be undone!\n\nClick OK to confirm deletion.')) {
    return;
  }

  crmData = {
    users: {
      artha: { username: 'artha', password: 'artha123', name: 'ArthaInvest Admin', role: 'admin' },
      ravi: { username: 'ravi', password: 'ravi123', name: 'Ravi Sharma', role: 'employee' },
      priya: { username: 'priya', password: 'priya123', name: 'Priya Singh', role: 'employee' }
    },
    leads: {},
    clients: {},
    documents: {},
    marketingMaterials: {},
    deals: {},
    campaigns: {},
    tasks: {},
    contacts: {},
    leadScores: {},
    activityLogs: {},
    workflows: {},
    callHistory: {},
    whatsappHistory: {},
    communicationLog: {},
    settings: { companyName: 'ArthaInvest Capital' }
  };

  saveData();
  alert('✅ All data cleared. The system has been reset to default state.');
  window.location.reload();
}
