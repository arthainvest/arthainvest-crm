const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'arthainvest-secret-key-2024';

// Middleware
app.use(express.json());
app.use(cors());
app.use(express.static(path.join(__dirname)));

// Multer setup for file uploads
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir);

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + '-' + file.originalname);
  }
});
const upload = multer({ storage, limits: { fileSize: 50 * 1024 * 1024 } });

// Database
const db = new sqlite3.Database(path.join(__dirname, 'arthainvest.db'));
db.serialize(() => {
  fs.readFile(path.join(__dirname, 'ARTHAINVEST_CRM_SCHEMA.sql'), 'utf8', (err, sql) => {
    if (!err) db.exec(sql);
  });
});

// Rate limiting
const rateLimit = {};
const checkRateLimit = (ip) => {
  const now = Date.now();
  if (!rateLimit[ip]) rateLimit[ip] = [];
  rateLimit[ip] = rateLimit[ip].filter(time => now - time < 15 * 60 * 1000);
  if (rateLimit[ip].length >= 100) return false;
  rateLimit[ip].push(now);
  return true;
};

// Auth middleware
const verifyToken = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1];
  if (!token) return res.status(401).json({ success: false, error: 'No token provided' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ success: false, error: 'Invalid token' });
    req.user = decoded;
    next();
  });
};

// Check role
const checkRole = (allowedRoles) => {
  return (req, res, next) => {
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ success: false, error: 'Insufficient permissions' });
    }
    next();
  };
};

// ==================== AUTH ENDPOINTS ====================

app.post('/api/auth/login', (req, res) => {
  if (!checkRateLimit(req.ip)) return res.status(429).json({ success: false, error: 'Too many requests' });

  const { username, password } = req.body;
  db.get('SELECT * FROM users WHERE username = ?', [username], async (err, user) => {
    if (err || !user) return res.json({ success: false, error: 'Invalid credentials' });

    const validPassword = await bcrypt.compare(password, user.password);
    if (!validPassword) return res.json({ success: false, error: 'Invalid credentials' });

    const token = jwt.sign({ id: user.id, username: user.username, role: user.role }, SECRET_KEY, { expiresIn: '24h' });
    db.run('UPDATE users SET is_online = 1, last_login = CURRENT_TIMESTAMP WHERE id = ?', [user.id]);

    res.json({
      success: true,
      token,
      user: { id: user.id, name: user.name, role: user.role, email: user.email, department: user.department }
    });
  });
});

app.post('/api/auth/logout', verifyToken, (req, res) => {
  db.run('UPDATE users SET is_online = 0 WHERE id = ?', [req.user.id]);
  res.json({ success: true, message: 'Logged out successfully' });
});

// ==================== CLIENTS ENDPOINTS ====================

app.get('/api/clients', verifyToken, (req, res) => {
  let query = 'SELECT * FROM clients';
  const params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE assigned_to = ?';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, clients: rows || [] });
  });
});

app.post('/api/clients', verifyToken, (req, res) => {
  const { name, phone, email, pan, aadhar, family_head, sub_broker, aum, status, assigned_to } = req.body;

  db.run(
    'INSERT INTO clients (name, phone, email, pan, aadhar, family_head, sub_broker, aum, status, assigned_to, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [name, phone, email, pan, aadhar, family_head, sub_broker, aum, status, assigned_to, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.put('/api/clients/:id', verifyToken, (req, res) => {
  const { name, phone, email, status, aum } = req.body;
  db.run(
    'UPDATE clients SET name = ?, phone = ?, email = ?, status = ?, aum = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [name, phone, email, status, aum, req.params.id],
    (err) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, message: 'Client updated' });
    }
  );
});

// ==================== OPPORTUNITIES ENDPOINTS ====================

app.get('/api/opportunities', verifyToken, (req, res) => {
  let query = 'SELECT * FROM opportunities ORDER BY follow_up_date ASC';
  const params = [];

  if (req.user.role === 'employee') {
    query = 'SELECT * FROM opportunities WHERE assigned_to = ? ORDER BY follow_up_date ASC';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, opportunities: rows || [] });
  });
});

app.post('/api/opportunities', verifyToken, (req, res) => {
  const { title, client_id, follow_up_date, status, expected_value, product_type, assigned_to } = req.body;

  db.run(
    'INSERT INTO opportunities (title, client_id, follow_up_date, status, expected_value, product_type, assigned_to, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    [title, client_id, follow_up_date, status || 'New', expected_value, product_type, assigned_to, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.put('/api/opportunities/:id', verifyToken, (req, res) => {
  const { title, status, follow_up_date, expected_value } = req.body;
  db.run(
    'UPDATE opportunities SET title = ?, status = ?, follow_up_date = ?, expected_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [title, status, follow_up_date, expected_value, req.params.id],
    (err) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, message: 'Opportunity updated' });
    }
  );
});

// ==================== CALLS ENDPOINTS ====================

app.post('/api/calls/log', verifyToken, (req, res) => {
  const { client_id, opportunity_id, call_duration, result, notes, call_type } = req.body;

  db.run(
    'INSERT INTO calls (client_id, opportunity_id, caller_id, call_duration, result, notes, call_type) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [client_id, opportunity_id, req.user.id, call_duration, result, notes, call_type],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.get('/api/calls/history/:clientId', verifyToken, (req, res) => {
  db.all('SELECT * FROM calls WHERE client_id = ? ORDER BY call_date DESC', [req.params.clientId], (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, calls: rows || [] });
  });
});

// ==================== VOICE NOTES ENDPOINTS ====================

app.post('/api/voice-notes/upload/:callId', verifyToken, upload.single('audio'), (req, res) => {
  if (!req.file) return res.json({ success: false, error: 'No file uploaded' });

  db.run(
    'INSERT INTO voice_notes (call_id, file_path, duration, created_by) VALUES (?, ?, ?, ?)',
    [req.params.callId, req.file.path, req.body.duration || 0, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID, path: req.file.path });
    }
  );
});

// ==================== CAMPAIGNS ENDPOINTS ====================

app.get('/api/campaigns', verifyToken, (req, res) => {
  let query = 'SELECT * FROM campaigns';
  const params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE assigned_to = ?';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, campaigns: rows || [] });
  });
});

app.post('/api/campaigns', verifyToken, checkRole(['admin', 'team_leader', 'marketing']), (req, res) => {
  const { name, description, product_type, assigned_to, target_count, start_date, end_date } = req.body;

  db.run(
    'INSERT INTO campaigns (name, description, product_type, assigned_to, target_count, start_date, end_date, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    [name, description, product_type, assigned_to, target_count, start_date, end_date, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.put('/api/campaigns/:id', verifyToken, (req, res) => {
  const { achieved_count, status } = req.body;
  db.run(
    'UPDATE campaigns SET achieved_count = ?, status = ? WHERE id = ?',
    [achieved_count, status, req.params.id],
    (err) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, message: 'Campaign updated' });
    }
  );
});

// ==================== TASKS/REMINDERS ENDPOINTS ====================

app.get('/api/tasks', verifyToken, (req, res) => {
  let query = 'SELECT * FROM tasks ORDER BY due_date ASC';
  const params = [];

  if (req.user.role === 'employee') {
    query = 'SELECT * FROM tasks WHERE assigned_to = ? ORDER BY due_date ASC';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, tasks: rows || [] });
  });
});

app.post('/api/tasks', verifyToken, (req, res) => {
  const { title, description, client_id, opportunity_id, assigned_to, due_date, priority, reminder_time } = req.body;

  db.run(
    'INSERT INTO tasks (title, description, client_id, opportunity_id, assigned_to, due_date, priority, reminder_time, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [title, description, client_id, opportunity_id, assigned_to, due_date, priority, reminder_time, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== DOCUMENTS/DIGILOCKER ENDPOINTS ====================

app.post('/api/documents/upload', verifyToken, upload.single('document'), (req, res) => {
  if (!req.file) return res.json({ success: false, error: 'No file uploaded' });

  const { client_id, document_type, visibility } = req.body;
  db.run(
    'INSERT INTO documents (client_id, document_type, file_path, file_name, uploaded_by, visibility) VALUES (?, ?, ?, ?, ?, ?)',
    [client_id, document_type, req.file.path, req.file.filename, req.user.id, visibility || 'private'],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.get('/api/documents/:clientId', verifyToken, (req, res) => {
  db.all(
    'SELECT * FROM documents WHERE client_id = ?',
    [req.params.clientId],
    (err, rows) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, documents: rows || [] });
    }
  );
});

// ==================== COMMUNICATIONS ENDPOINTS ====================

app.post('/api/communications/send', verifyToken, (req, res) => {
  const { client_id, opportunity_id, communication_type, message_text, scheduled_time } = req.body;

  db.run(
    'INSERT INTO communications (client_id, opportunity_id, communication_type, message_text, scheduled_time, sent_by) VALUES (?, ?, ?, ?, ?, ?)',
    [client_id, opportunity_id, communication_type, message_text, scheduled_time, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

app.get('/api/communications/:clientId', verifyToken, (req, res) => {
  db.all(
    'SELECT * FROM communications WHERE client_id = ? ORDER BY sent_at DESC',
    [req.params.clientId],
    (err, rows) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, communications: rows || [] });
    }
  );
});

// ==================== EMAIL TEMPLATES ====================

app.get('/api/email-templates', verifyToken, (req, res) => {
  db.all('SELECT * FROM email_templates', (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, templates: rows || [] });
  });
});

app.post('/api/email-templates', verifyToken, checkRole(['admin', 'marketing']), (req, res) => {
  const { name, subject, body, product_type, is_ai_generated } = req.body;

  db.run(
    'INSERT INTO email_templates (name, subject, body, product_type, is_ai_generated, created_by) VALUES (?, ?, ?, ?, ?, ?)',
    [name, subject, body, product_type, is_ai_generated, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== WHATSAPP TEMPLATES ====================

app.get('/api/whatsapp-templates', verifyToken, (req, res) => {
  db.all('SELECT * FROM whatsapp_templates', (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, templates: rows || [] });
  });
});

app.post('/api/whatsapp-templates', verifyToken, checkRole(['admin', 'marketing']), (req, res) => {
  const { name, message, product_type, is_ai_generated } = req.body;

  db.run(
    'INSERT INTO whatsapp_templates (name, message, product_type, is_ai_generated, created_by) VALUES (?, ?, ?, ?, ?)',
    [name, message, product_type, is_ai_generated, req.user.id],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== INSURANCE ENDPOINTS ====================

app.get('/api/insurance', verifyToken, (req, res) => {
  let query = 'SELECT * FROM insurance_policies';
  const params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE client_id IN (SELECT id FROM clients WHERE assigned_to = ?)';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, policies: rows || [] });
  });
});

app.post('/api/insurance', verifyToken, (req, res) => {
  const { client_id, policy_number, policy_holder, policy_name, issue_date, renewal_date, premium, sum_assured, product_type } = req.body;

  db.run(
    'INSERT INTO insurance_policies (client_id, policy_number, policy_holder, policy_name, issue_date, renewal_date, premium, sum_assured, product_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [client_id, policy_number, policy_holder, policy_name, issue_date, renewal_date, premium, sum_assured, product_type],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== LOANS ENDPOINTS ====================

app.get('/api/loans', verifyToken, (req, res) => {
  let query = 'SELECT * FROM loan_applications';
  const params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE client_id IN (SELECT id FROM clients WHERE assigned_to = ?)';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, loans: rows || [] });
  });
});

app.post('/api/loans', verifyToken, (req, res) => {
  const { client_id, loan_type, loan_amount, application_date, status, tenure_months, interest_rate } = req.body;

  db.run(
    'INSERT INTO loan_applications (client_id, loan_type, loan_amount, application_date, status, tenure_months, interest_rate) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [client_id, loan_type, loan_amount, application_date, status || 'Applied', tenure_months, interest_rate],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== MUTUAL FUNDS ENDPOINTS ====================

app.get('/api/mutual-funds', verifyToken, (req, res) => {
  let query = 'SELECT * FROM mutual_funds';
  const params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE client_id IN (SELECT id FROM clients WHERE assigned_to = ?)';
    params.push(req.user.id);
  }

  db.all(query, params, (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, funds: rows || [] });
  });
});

app.post('/api/mutual-funds', verifyToken, (req, res) => {
  const { client_id, folio_number, fund_name, investment_amount, investment_date, sip_active, sip_amount, sip_frequency } = req.body;

  db.run(
    'INSERT INTO mutual_funds (client_id, folio_number, fund_name, investment_amount, investment_date, sip_active, sip_amount, sip_frequency) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    [client_id, folio_number, fund_name, investment_amount, investment_date, sip_active, sip_amount, sip_frequency],
    function(err) {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, id: this.lastID });
    }
  );
});

// ==================== PERFORMANCE METRICS ====================

app.get('/api/performance/:userId', verifyToken, (req, res) => {
  db.get(
    'SELECT * FROM performance_metrics WHERE user_id = ? ORDER BY metric_date DESC LIMIT 1',
    [req.params.userId],
    (err, row) => {
      if (err) return res.json({ success: false, error: err.message });
      res.json({ success: true, performance: row });
    }
  );
});

app.get('/api/team/status', verifyToken, (req, res) => {
  db.all('SELECT id, name, department, is_online, last_login FROM users WHERE role = "employee"', (err, rows) => {
    if (err) return res.json({ success: false, error: err.message });
    res.json({ success: true, team: rows || [] });
  });
});

// ==================== BULK UPLOAD ====================

app.post('/api/bulk-upload/clients', verifyToken, checkRole(['admin', 'team_leader']), upload.single('file'), (req, res) => {
  if (!req.file) return res.json({ success: false, error: 'No file uploaded' });

  const csv = require('csv-parser');
  const results = [];

  fs.createReadStream(req.file.path)
    .pipe(csv())
    .on('data', (data) => results.push(data))
    .on('end', () => {
      let inserted = 0;
      results.forEach(row => {
        db.run(
          'INSERT INTO clients (name, phone, email, pan, status, created_by) VALUES (?, ?, ?, ?, ?, ?)',
          [row.name, row.phone, row.email, row.pan, 'New', req.user.id]
        );
        inserted++;
      });
      res.json({ success: true, inserted });
    });
});

// ==================== START SERVER ====================

app.listen(PORT, () => {
  console.log(`\n✅ ArthaInvest CRM Server running on http://localhost:${PORT}`);
  console.log('📊 Dashboard: http://localhost:3000/admin-dashboard.html\n');
});
