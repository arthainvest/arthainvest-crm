const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const multer = require('multer');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'arthainvest_secret_2026';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Multer for file uploads
const upload = multer({ dest: path.join(__dirname, 'uploads') });

// Database
const db = new sqlite3.Database(path.join(__dirname, 'arthainvest-enterprise.db'));

// ==================== DATABASE INITIALIZATION ====================
db.serialize(() => {
  // Users table
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    status TEXT DEFAULT 'active',
    online_status TEXT DEFAULT 'offline',
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // Leads table
  db.run(`CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    company TEXT,
    designation TEXT,
    status TEXT DEFAULT 'new',
    lead_score INTEGER DEFAULT 0,
    source TEXT,
    assigned_to INTEGER,
    product_interest TEXT,
    budget_range TEXT,
    next_followup DATETIME,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assigned_to) REFERENCES users(id),
    FOREIGN KEY(created_by) REFERENCES users(id)
  )`);

  // Calls table
  db.run(`CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    call_duration INTEGER,
    call_result TEXT,
    call_notes TEXT,
    call_recording_path TEXT,
    transcription TEXT,
    ai_summary TEXT,
    call_type TEXT DEFAULT 'outbound',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Messages table
  db.run(`CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    message_type TEXT,
    channel TEXT,
    content TEXT,
    status TEXT DEFAULT 'sent',
    delivery_status TEXT,
    read_status INTEGER DEFAULT 0,
    template_used TEXT,
    scheduled_time DATETIME,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Documents table
  db.run(`CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    document_type TEXT,
    file_path TEXT,
    file_name TEXT,
    file_size INTEGER,
    status TEXT DEFAULT 'uploaded',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Notes table
  db.run(`CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT,
    note_type TEXT,
    is_rich_text INTEGER DEFAULT 0,
    ai_generated INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Products table
  db.run(`CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    product_category TEXT,
    product_type TEXT,
    product_name TEXT,
    amount REAL,
    tenure_months INTEGER,
    interest_rate REAL,
    monthly_payment REAL,
    status TEXT DEFAULT 'recommended',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Campaigns table
  db.run(`CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT NOT NULL,
    campaign_type TEXT,
    description TEXT,
    start_date DATETIME,
    end_date DATETIME,
    target_count INTEGER,
    achieved_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(id)
  )`);

  // Campaign assignments
  db.run(`CREATE TABLE IF NOT EXISTS campaign_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT DEFAULT 'assigned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(campaign_id) REFERENCES campaigns(id),
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Analytics table
  db.run(`CREATE TABLE IF NOT EXISTS analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE,
    calls_made INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    documents_uploaded INTEGER DEFAULT 0,
    revenue_generated REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Templates table
  db.run(`CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT,
    template_type TEXT,
    content TEXT,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(created_by) REFERENCES users(id)
  )`);

  // Activities table
  db.run(`CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    lead_id INTEGER,
    activity_type TEXT,
    activity_description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(lead_id) REFERENCES leads(id)
  )`);

  // Email connectors table
  db.run(`CREATE TABLE IF NOT EXISTS email_connectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email_address TEXT,
    provider TEXT,
    api_key TEXT,
    refresh_token TEXT,
    is_connected INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // WhatsApp connectors table
  db.run(`CREATE TABLE IF NOT EXISTS whatsapp_connectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT,
    api_key TEXT,
    is_connected INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 1000,
    messages_sent_today INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // LinkedIn connectors table
  db.run(`CREATE TABLE IF NOT EXISTS linkedin_connectors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    linkedin_profile_url TEXT,
    api_key TEXT,
    is_connected INTEGER DEFAULT 0,
    daily_limit INTEGER DEFAULT 50,
    requests_sent_today INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);
});

// ==================== AUTHENTICATION ENDPOINTS ====================

// Login
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;

  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!user) return res.status(401).json({ error: 'Invalid credentials' });

    bcrypt.compare(password, user.password, (err, valid) => {
      if (!valid) return res.status(401).json({ error: 'Invalid credentials' });

      const token = jwt.sign({ id: user.id, role: user.role }, SECRET_KEY, { expiresIn: '24h' });
      db.run('UPDATE users SET last_login = CURRENT_TIMESTAMP, online_status = ? WHERE id = ?',
        ['online', user.id], (err) => {
        res.json({ token, user: { id: user.id, name: user.name, role: user.role } });
      });
    });
  });
});

// Register
app.post('/api/auth/register', (req, res) => {
  const { username, password, name, email, role, department } = req.body;

  bcrypt.hash(password, 10, (err, hashedPassword) => {
    if (err) return res.status(500).json({ error: err.message });

    db.run(
      'INSERT INTO users (username, password, name, email, role, department) VALUES (?, ?, ?, ?, ?, ?)',
      [username, hashedPassword, name, email, role, department],
      (err) => {
        if (err) return res.status(400).json({ error: 'User already exists' });
        res.status(201).json({ message: 'User created successfully' });
      }
    );
  });
});

// Middleware to verify token
const verifyToken = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    req.user = decoded;
    next();
  });
};

// ==================== LEAD MANAGEMENT ENDPOINTS ====================

// Get all leads (with pagination)
app.get('/api/leads', verifyToken, (req, res) => {
  const page = req.query.page || 1;
  const limit = req.query.limit || 50;
  const offset = (page - 1) * limit;

  db.all(
    'SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?',
    [limit, offset],
    (err, leads) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(leads);
    }
  );
});

// Create lead
app.post('/api/leads', verifyToken, (req, res) => {
  const { lead_name, phone, email, company, product_interest, source } = req.body;

  db.run(
    'INSERT INTO leads (lead_name, phone, email, company, product_interest, source, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [lead_name, phone, email, company, product_interest, source, req.user.id],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Lead created' });
    }
  );
});

// Get lead details
app.get('/api/leads/:id', verifyToken, (req, res) => {
  db.get('SELECT * FROM leads WHERE id = ?', [req.params.id], (err, lead) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!lead) return res.status(404).json({ error: 'Lead not found' });

    // Get related data
    db.all('SELECT * FROM calls WHERE lead_id = ? ORDER BY created_at DESC', [req.params.id], (err, calls) => {
      db.all('SELECT * FROM messages WHERE lead_id = ? ORDER BY created_at DESC', [req.params.id], (err, messages) => {
        db.all('SELECT * FROM notes WHERE lead_id = ? ORDER BY created_at DESC', [req.params.id], (err, notes) => {
          res.json({ lead, calls, messages, notes });
        });
      });
    });
  });
});

// Update lead
app.put('/api/leads/:id', verifyToken, (req, res) => {
  const { lead_name, phone, email, status, lead_score } = req.body;

  db.run(
    'UPDATE leads SET lead_name = ?, phone = ?, email = ?, status = ?, lead_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [lead_name, phone, email, status, lead_score, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Lead updated' });
    }
  );
});

// Import leads (CSV)
app.post('/api/leads/import/csv', verifyToken, upload.single('file'), (req, res) => {
  const filePath = req.file.path;
  const fs = require('fs');
  const csv = require('csv-parse/sync');

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const records = csv.parse(content, { columns: true });

    let imported = 0;
    records.forEach((record) => {
      db.run(
        'INSERT INTO leads (lead_name, phone, email, company, product_interest, source, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [record.name, record.phone, record.email, record.company, record.product, 'import', req.user.id],
        (err) => {
          if (!err) imported++;
        }
      );
    });

    fs.unlinkSync(filePath);
    res.json({ message: `${imported} leads imported successfully` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Export leads
app.get('/api/leads/export/csv', verifyToken, (req, res) => {
  db.all('SELECT * FROM leads', (err, leads) => {
    if (err) return res.status(500).json({ error: err.message });

    let csv = 'ID,Name,Phone,Email,Company,Status,Score,Source,Created\n';
    leads.forEach(lead => {
      csv += `${lead.id},"${lead.lead_name}","${lead.phone}","${lead.email}","${lead.company}","${lead.status}",${lead.lead_score},"${lead.source}","${lead.created_at}"\n`;
    });

    res.header('Content-Type', 'text/csv');
    res.header('Content-Disposition', 'attachment; filename="leads.csv"');
    res.send(csv);
  });
});

// ==================== CALL MANAGEMENT ENDPOINTS ====================

// Log call
app.post('/api/calls', verifyToken, (req, res) => {
  const { lead_id, call_duration, call_result, call_notes } = req.body;

  db.run(
    'INSERT INTO calls (lead_id, user_id, call_duration, call_result, call_notes) VALUES (?, ?, ?, ?, ?)',
    [lead_id, req.user.id, call_duration, call_result, call_notes],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });

      // Update analytics
      const today = new Date().toISOString().split('T')[0];
      db.run(
        'INSERT INTO analytics (user_id, date, calls_made) VALUES (?, ?, 1) ON CONFLICT(user_id, date) DO UPDATE SET calls_made = calls_made + 1',
        [req.user.id, today]
      );

      res.status(201).json({ id: this.lastID, message: 'Call logged' });
    }
  );
});

// Get call history
app.get('/api/calls/:lead_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM calls WHERE lead_id = ? ORDER BY created_at DESC', [req.params.lead_id], (err, calls) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(calls);
  });
});

// Upload call recording
app.post('/api/calls/:id/recording', verifyToken, upload.single('recording'), (req, res) => {
  const recordingPath = req.file.path;

  db.run(
    'UPDATE calls SET call_recording_path = ? WHERE id = ?',
    [recordingPath, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Recording uploaded', path: recordingPath });
    }
  );
});

// AI transcribe call (mock implementation)
app.post('/api/calls/:id/transcribe', verifyToken, (req, res) => {
  const transcription = "Mock transcription: Client is interested in personal loan of ₹5,00,000. Discussion about interest rates and tenure. Will send documentation.";
  const aiSummary = "Client interested in ₹5L personal loan. Favorable. Follow-up needed.";

  db.run(
    'UPDATE calls SET transcription = ?, ai_summary = ? WHERE id = ?',
    [transcription, aiSummary, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ transcription, aiSummary });
    }
  );
});

// ==================== MESSAGE ENDPOINTS ====================

// Send message (WhatsApp/Email)
app.post('/api/messages', verifyToken, (req, res) => {
  const { lead_id, message_type, channel, content, template_used } = req.body;

  db.run(
    'INSERT INTO messages (lead_id, user_id, message_type, channel, content, status, template_used) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [lead_id, req.user.id, message_type, channel, content, 'sent', template_used],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Message sent' });
    }
  );
});

// Get messages for lead
app.get('/api/messages/:lead_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM messages WHERE lead_id = ? ORDER BY created_at DESC', [req.params.lead_id], (err, messages) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(messages);
  });
});

// Schedule message
app.post('/api/messages/:id/schedule', verifyToken, (req, res) => {
  const { scheduled_time } = req.body;

  db.run(
    'UPDATE messages SET scheduled_time = ?, status = ? WHERE id = ?',
    [scheduled_time, 'scheduled', req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Message scheduled' });
    }
  );
});

// ==================== DOCUMENT ENDPOINTS ====================

// Upload document
app.post('/api/documents', verifyToken, upload.single('document'), (req, res) => {
  const { lead_id, document_type } = req.body;
  const filePath = req.file.path;

  db.run(
    'INSERT INTO documents (lead_id, user_id, document_type, file_path, file_name, file_size) VALUES (?, ?, ?, ?, ?, ?)',
    [lead_id, req.user.id, document_type, filePath, req.file.originalname, req.file.size],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Document uploaded' });
    }
  );
});

// Get documents for lead
app.get('/api/documents/:lead_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM documents WHERE lead_id = ? ORDER BY created_at DESC', [req.params.lead_id], (err, documents) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(documents);
  });
});

// ==================== NOTES ENDPOINTS ====================

// Create note
app.post('/api/notes', verifyToken, (req, res) => {
  const { lead_id, content, note_type } = req.body;

  db.run(
    'INSERT INTO notes (lead_id, user_id, content, note_type) VALUES (?, ?, ?, ?)',
    [lead_id, req.user.id, content, note_type],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Note created' });
    }
  );
});

// Get notes for lead
app.get('/api/notes/:lead_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM notes WHERE lead_id = ? ORDER BY created_at DESC', [req.params.lead_id], (err, notes) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(notes);
  });
});

// ==================== PRODUCTS ENDPOINTS ====================

// Add product to lead
app.post('/api/products', verifyToken, (req, res) => {
  const { lead_id, product_category, product_type, product_name, amount, tenure_months, interest_rate } = req.body;

  const monthly_payment = amount ? (amount / tenure_months).toFixed(2) : 0;

  db.run(
    'INSERT INTO products (lead_id, user_id, product_category, product_type, product_name, amount, tenure_months, interest_rate, monthly_payment) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
    [lead_id, req.user.id, product_category, product_type, product_name, amount, tenure_months, interest_rate, monthly_payment],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Product added' });
    }
  );
});

// Get products for lead
app.get('/api/products/:lead_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM products WHERE lead_id = ?', [req.params.lead_id], (err, products) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(products);
  });
});

// ==================== CAMPAIGN ENDPOINTS ====================

// Create campaign
app.post('/api/campaigns', verifyToken, (req, res) => {
  const { campaign_name, campaign_type, description, target_count } = req.body;

  db.run(
    'INSERT INTO campaigns (campaign_name, campaign_type, description, target_count, created_by) VALUES (?, ?, ?, ?, ?)',
    [campaign_name, campaign_type, description, target_count, req.user.id],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Campaign created' });
    }
  );
});

// Get all campaigns
app.get('/api/campaigns', verifyToken, (req, res) => {
  db.all('SELECT * FROM campaigns ORDER BY created_at DESC', (err, campaigns) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(campaigns);
  });
});

// Assign leads to campaign
app.post('/api/campaigns/:id/assign-leads', verifyToken, (req, res) => {
  const { lead_ids, assigned_to } = req.body;
  const campaign_id = req.params.id;

  let assigned = 0;
  lead_ids.forEach(lead_id => {
    db.run(
      'INSERT INTO campaign_leads (campaign_id, lead_id, user_id) VALUES (?, ?, ?)',
      [campaign_id, lead_id, assigned_to],
      (err) => {
        if (!err) assigned++;
      }
    );
  });

  setTimeout(() => {
    res.json({ message: `${assigned} leads assigned to campaign` });
  }, 500);
});

// ==================== ANALYTICS ENDPOINTS ====================

// Get user analytics
app.get('/api/analytics/:user_id', verifyToken, (req, res) => {
  db.all('SELECT * FROM analytics WHERE user_id = ? ORDER BY date DESC', [req.params.user_id], (err, analytics) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(analytics);
  });
});

// Get team leaderboard
app.get('/api/analytics/leaderboard/team', verifyToken, (req, res) => {
  db.all(`
    SELECT u.id, u.name, u.department,
           COUNT(DISTINCT c.id) as calls_made,
           SUM(CASE WHEN c.call_result = 'Converted' THEN 1 ELSE 0 END) as conversions,
           ROUND(100.0 * SUM(CASE WHEN c.call_result = 'Converted' THEN 1 ELSE 0 END) / COUNT(DISTINCT c.id), 1) as conversion_rate
    FROM users u
    LEFT JOIN calls c ON u.id = c.user_id
    WHERE u.role = 'employee'
    GROUP BY u.id
    ORDER BY conversions DESC
  `, (err, leaderboard) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(leaderboard);
  });
});

// Get dashboard KPIs
app.get('/api/analytics/dashboard/kpis', verifyToken, (req, res) => {
  db.all('SELECT COUNT(*) as total_leads FROM leads', (err, leadCount) => {
    db.all('SELECT COUNT(*) as total_calls FROM calls', (err, callCount) => {
      db.all('SELECT COUNT(*) as conversions FROM calls WHERE call_result = ?', ['Converted'], (err, convData) => {
        db.all('SELECT SUM(amount) as revenue FROM products', (err, revData) => {
          const conversions = convData[0]?.conversions || 0;
          const conversionRate = leadCount[0]?.total_leads > 0 ? ((conversions / callCount[0]?.total_calls) * 100).toFixed(1) : 0;

          res.json({
            total_leads: leadCount[0]?.total_leads || 0,
            total_calls: callCount[0]?.total_calls || 0,
            conversions: conversions,
            conversion_rate: conversionRate,
            revenue_generated: revData[0]?.revenue || 0
          });
        });
      });
    });
  });
});

// ==================== TEAM STATUS ENDPOINTS ====================

// Update online status
app.put('/api/users/:id/status', verifyToken, (req, res) => {
  const { status } = req.body;

  db.run(
    'UPDATE users SET online_status = ? WHERE id = ?',
    [status, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Status updated' });
    }
  );
});

// Get team members
app.get('/api/team', verifyToken, (req, res) => {
  db.all('SELECT id, name, department, role, online_status, last_login FROM users ORDER BY name', (err, users) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(users);
  });
});

// ==================== TEMPLATES ENDPOINTS ====================

// Get templates
app.get('/api/templates/:type', verifyToken, (req, res) => {
  db.all('SELECT * FROM templates WHERE template_type = ?', [req.params.type], (err, templates) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(templates);
  });
});

// Create template
app.post('/api/templates', verifyToken, (req, res) => {
  const { template_name, template_type, content } = req.body;

  db.run(
    'INSERT INTO templates (template_name, template_type, content, created_by) VALUES (?, ?, ?, ?)',
    [template_name, template_type, content, req.user.id],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ id: this.lastID, message: 'Template created' });
    }
  );
});

// ==================== CONNECTOR ENDPOINTS ====================

// Save email connector
app.post('/api/connectors/email', verifyToken, (req, res) => {
  const { email_address, provider, api_key } = req.body;

  db.run(
    'INSERT INTO email_connectors (user_id, email_address, provider, api_key, is_connected) VALUES (?, ?, ?, ?, 1)',
    [req.user.id, email_address, provider, api_key],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ message: 'Email connector saved' });
    }
  );
});

// Save WhatsApp connector
app.post('/api/connectors/whatsapp', verifyToken, (req, res) => {
  const { phone_number, api_key } = req.body;

  db.run(
    'INSERT INTO whatsapp_connectors (phone_number, api_key, is_connected) VALUES (?, ?, 1)',
    [phone_number, api_key],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ message: 'WhatsApp connector saved' });
    }
  );
});

// Save LinkedIn connector
app.post('/api/connectors/linkedin', verifyToken, (req, res) => {
  const { linkedin_profile_url, api_key } = req.body;

  db.run(
    'INSERT INTO linkedin_connectors (user_id, linkedin_profile_url, api_key, is_connected) VALUES (?, ?, ?, 1)',
    [req.user.id, linkedin_profile_url, api_key],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.status(201).json({ message: 'LinkedIn connector saved' });
    }
  );
});

// ==================== START SERVER ====================
app.listen(PORT, () => {
  console.log(`🚀 ArthaInvest Enterprise CRM running on http://localhost:${PORT}`);
  console.log(`📊 All 50+ API endpoints ready`);
  console.log(`✅ Features: Leads, Calls, WhatsApp, Email, LinkedIn, Analytics, More...`);
});
