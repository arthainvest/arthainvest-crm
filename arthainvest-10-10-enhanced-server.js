const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcrypt');
const multer = require('multer');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const app = express();
const PORT = 3001;
const SECRET_KEY = 'arthainvest_secret_2026';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));

// Multer for file uploads
const upload = multer({ dest: path.join(__dirname, 'uploads') });

// Database
const db = new sqlite3.Database(path.join(__dirname, 'arthainvest-10-10.db'));

// ==================== ENHANCED DATABASE SCHEMA ====================
db.serialize(() => {
  // Users table with enhanced fields
  db.run(`CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL,
    department TEXT,
    status TEXT DEFAULT 'active',
    online_status TEXT DEFAULT 'offline',
    last_login DATETIME,
    commission_rate REAL DEFAULT 0,
    monthly_target REAL DEFAULT 0,
    call_target INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  )`);

  // Leads table (Enhanced)
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

  // Deals table (NEW - Bigin Pipeline)
  db.run(`CREATE TABLE IF NOT EXISTS deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    deal_name TEXT NOT NULL,
    lead_id INTEGER NOT NULL,
    stage TEXT DEFAULT 'new_lead',
    probability_percent INTEGER DEFAULT 10,
    expected_value REAL DEFAULT 0,
    actual_value REAL DEFAULT 0,
    owner_id INTEGER,
    expected_close_date DATETIME,
    closed_date DATETIME,
    status TEXT DEFAULT 'open',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(owner_id) REFERENCES users(id)
  )`);

  // Calls table (Enhanced with mobile linking)
  db.run(`CREATE TABLE IF NOT EXISTS calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    phone_number TEXT,
    whatsapp_number TEXT,
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
    phone_number TEXT,
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

  // Documents table (Google Drive Enhanced)
  db.run(`CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    document_type TEXT,
    file_path TEXT,
    google_drive_id TEXT,
    file_name TEXT,
    file_size INTEGER,
    status TEXT DEFAULT 'uploaded',
    access_level TEXT DEFAULT 'private',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(lead_id) REFERENCES leads(id),
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Phone-WhatsApp Mapping table (NEW)
  db.run(`CREATE TABLE IF NOT EXISTS phone_whatsapp_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT UNIQUE NOT NULL,
    whatsapp_number TEXT UNIQUE,
    user_id INTEGER,
    lead_id INTEGER,
    is_verified INTEGER DEFAULT 0,
    linked_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(lead_id) REFERENCES leads(id)
  )`);

  // Commission table (NEW)
  db.run(`CREATE TABLE IF NOT EXISTS commissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    deal_id INTEGER,
    amount REAL DEFAULT 0,
    rate_percent REAL DEFAULT 0,
    month TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(deal_id) REFERENCES deals(id)
  )`);

  // Call Targets table (NEW)
  db.run(`CREATE TABLE IF NOT EXISTS call_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT,
    target_count INTEGER DEFAULT 0,
    achieved_count INTEGER DEFAULT 0,
    achievement_percent REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);

  // Client Targets table (NEW)
  db.run(`CREATE TABLE IF NOT EXISTS client_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month TEXT,
    target_count INTEGER DEFAULT 0,
    achieved_count INTEGER DEFAULT 0,
    achievement_percent REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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

  // Google Drive Config table (NEW)
  db.run(`CREATE TABLE IF NOT EXISTS google_drive_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    access_token TEXT,
    refresh_token TEXT,
    folder_id TEXT,
    is_connected INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
  )`);
});

// ==================== AUTHENTICATION ====================

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
        res.json({
          token,
          user: {
            id: user.id,
            name: user.name,
            role: user.role,
            phone: user.phone,
            monthly_target: user.monthly_target,
            call_target: user.call_target
          }
        });
      });
    });
  });
});

// ==================== ROLE-BASED ENDPOINTS ====================

// ADMIN: Commission Report Only
app.get('/api/admin/commissions', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    if (decoded.role !== 'admin') return res.status(403).json({ error: 'Only admins can access' });

    db.all(`
      SELECT c.*, u.name, u.email, d.deal_name, d.expected_value
      FROM commissions c
      JOIN users u ON c.user_id = u.id
      LEFT JOIN deals d ON c.deal_id = d.id
      ORDER BY c.created_at DESC
    `, (err, commissions) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(commissions);
    });
  });
});

// TEAM LEADER: Assign Call Targets
app.post('/api/team-leader/assign-call-target', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    if (decoded.role !== 'team_leader') return res.status(403).json({ error: 'Only team leaders can assign targets' });

    const { user_id, target_count, month } = req.body;

    db.run(
      'INSERT OR REPLACE INTO call_targets (user_id, month, target_count) VALUES (?, ?, ?)',
      [user_id, month, target_count],
      (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Call target assigned' });
      }
    );
  });
});

// TEAM LEADER: Assign Client Targets
app.post('/api/team-leader/assign-client-target', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });
    if (decoded.role !== 'team_leader') return res.status(403).json({ error: 'Only team leaders can assign targets' });

    const { user_id, target_count, month } = req.body;

    db.run(
      'INSERT OR REPLACE INTO client_targets (user_id, month, target_count) VALUES (?, ?, ?)',
      [user_id, month, target_count],
      (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Client target assigned' });
      }
    );
  });
});

// ==================== PHONE-WHATSAPP LINKING ====================

// Link Phone Number to WhatsApp
app.post('/api/phone/link-whatsapp', (req, res) => {
  const { phone_number, whatsapp_number, user_id, lead_id } = req.body;

  if (!phone_number || !whatsapp_number) {
    return res.status(400).json({ error: 'Phone and WhatsApp numbers required' });
  }

  db.run(
    'INSERT OR REPLACE INTO phone_whatsapp_mapping (phone_number, whatsapp_number, user_id, lead_id, is_verified) VALUES (?, ?, ?, ?, 1)',
    [phone_number, whatsapp_number, user_id, lead_id],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({
        id: this.lastID,
        message: 'Phone-WhatsApp mapping created successfully',
        phone: phone_number,
        whatsapp: whatsapp_number
      });
    }
  );
});

// Get WhatsApp Number by Phone
app.get('/api/phone/:phone_number/whatsapp', (req, res) => {
  const phone = req.params.phone_number;

  db.get('SELECT * FROM phone_whatsapp_mapping WHERE phone_number = ?', [phone], (err, mapping) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!mapping) return res.status(404).json({ error: 'Mapping not found' });
    res.json(mapping);
  });
});

// Get All Phone-WhatsApp Mappings for User
app.get('/api/user/:user_id/phone-mappings', (req, res) => {
  db.all('SELECT * FROM phone_whatsapp_mapping WHERE user_id = ?', [req.params.user_id], (err, mappings) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(mappings);
  });
});

// ==================== GOOGLE DRIVE INTEGRATION ====================

// Save Google Drive Config
app.post('/api/google-drive/config', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    const { access_token, refresh_token, folder_id } = req.body;

    db.run(
      'INSERT OR REPLACE INTO google_drive_config (user_id, access_token, refresh_token, folder_id, is_connected) VALUES (?, ?, ?, ?, 1)',
      [decoded.id, access_token, refresh_token, folder_id],
      (err) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ message: 'Google Drive configured successfully' });
      }
    );
  });
});

// Upload Document to Google Drive
app.post('/api/documents/google-drive/upload', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    const { lead_id, document_type, file_path, file_name } = req.body;

    // Mock Google Drive upload (In production, use Google Drive API)
    const google_drive_id = `gd_${Date.now()}`;

    db.run(
      'INSERT INTO documents (lead_id, user_id, document_type, file_path, google_drive_id, file_name, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [lead_id, decoded.id, document_type, file_path, google_drive_id, file_name, 'uploaded'],
      function(err) {
        if (err) return res.status(500).json({ error: err.message });
        res.json({
          id: this.lastID,
          message: 'Document uploaded to Google Drive',
          google_drive_id: google_drive_id
        });
      }
    );
  });
});

// Export Documents from Google Drive
app.get('/api/documents/export/google-drive', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    db.all(
      'SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC',
      [decoded.id],
      (err, documents) => {
        if (err) return res.status(500).json({ error: err.message });

        // Generate export data
        const exportData = {
          exported_at: new Date().toISOString(),
          user_id: decoded.id,
          documents: documents,
          total_documents: documents.length
        };

        res.json(exportData);
      }
    );
  });
});

// Import Documents from Google Drive
app.post('/api/documents/import/google-drive', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    const { documents } = req.body;

    let imported = 0;
    documents.forEach(doc => {
      db.run(
        'INSERT INTO documents (lead_id, user_id, document_type, file_path, google_drive_id, file_name, status) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [doc.lead_id, decoded.id, doc.document_type, doc.file_path, doc.google_drive_id, doc.file_name, 'imported'],
        (err) => {
          if (!err) imported++;
        }
      );
    });

    setTimeout(() => {
      res.json({ message: `${imported} documents imported from Google Drive` });
    }, 500);
  });
});

// ==================== CALL MANAGEMENT (Enhanced) ====================

// Log Call with Phone-WhatsApp Linking
app.post('/api/calls', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    const { lead_id, phone_number, whatsapp_number, call_duration, call_result, call_notes } = req.body;

    db.run(
      'INSERT INTO calls (lead_id, user_id, phone_number, whatsapp_number, call_duration, call_result, call_notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [lead_id, decoded.id, phone_number, whatsapp_number, call_duration, call_result, call_notes],
      function(err) {
        if (err) return res.status(500).json({ error: err.message });

        // If phone numbers provided, create mapping
        if (phone_number && whatsapp_number) {
          db.run(
            'INSERT OR IGNORE INTO phone_whatsapp_mapping (phone_number, whatsapp_number, user_id, lead_id, is_verified) VALUES (?, ?, ?, ?, 1)',
            [phone_number, whatsapp_number, decoded.id, lead_id]
          );
        }

        // Update call target achievement
        const today = new Date().toISOString().split('T')[0];
        const month = today.substring(0, 7);

        db.run(
          `UPDATE call_targets SET achieved_count =
           (SELECT COUNT(*) FROM calls WHERE user_id = ? AND strftime('%Y-%m', created_at) = ?)
           WHERE user_id = ? AND month = ?`,
          [decoded.id, month, decoded.id, month]
        );

        res.json({ id: this.lastID, message: 'Call logged with phone-WhatsApp mapping' });
      }
    );
  });
});

// ==================== DEALS PIPELINE (NEW) ====================

// Create Deal
app.post('/api/deals', (req, res) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token' });

  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ error: 'Invalid token' });

    const { lead_id, deal_name, expected_value, expected_close_date } = req.body;

    db.run(
      'INSERT INTO deals (deal_name, lead_id, owner_id, expected_value, expected_close_date) VALUES (?, ?, ?, ?, ?)',
      [deal_name, lead_id, decoded.id, expected_value, expected_close_date],
      function(err) {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ id: this.lastID, message: 'Deal created' });
      }
    );
  });
});

// Update Deal Stage
app.put('/api/deals/:id/stage', (req, res) => {
  const { stage, probability_percent } = req.body;

  db.run(
    'UPDATE deals SET stage = ?, probability_percent = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [stage, probability_percent, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ message: 'Deal stage updated' });
    }
  );
});

// Get All Deals
app.get('/api/deals', (req, res) => {
  db.all('SELECT * FROM deals ORDER BY created_at DESC', (err, deals) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(deals);
  });
});

// ==================== TARGETS ====================

// Get Call Targets for User
app.get('/api/targets/calls/:user_id/:month', (req, res) => {
  db.get('SELECT * FROM call_targets WHERE user_id = ? AND month = ?',
    [req.params.user_id, req.params.month], (err, target) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(target || { target_count: 0, achieved_count: 0 });
  });
});

// Get Client Targets for User
app.get('/api/targets/clients/:user_id/:month', (req, res) => {
  db.get('SELECT * FROM client_targets WHERE user_id = ? AND month = ?',
    [req.params.user_id, req.params.month], (err, target) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(target || { target_count: 0, achieved_count: 0 });
  });
});

// ==================== DATA ENDPOINTS (FOR DASHBOARD) ====================

// Get All Leads
app.get('/api/leads', (req, res) => {
  db.all('SELECT * FROM leads ORDER BY created_at DESC', (err, leads) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(leads || []);
  });
});

// Get All Calls
app.get('/api/calls', (req, res) => {
  db.all('SELECT * FROM calls ORDER BY created_at DESC', (err, calls) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(calls || []);
  });
});

// Get All Commissions
app.get('/api/commissions', (req, res) => {
  db.all('SELECT * FROM commissions ORDER BY created_at DESC', (err, commissions) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json(commissions || []);
  });
});

// Get System Statistics
app.get('/api/stats', (req, res) => {
  db.serialize(() => {
    let stats = {};

    db.get('SELECT COUNT(*) as count FROM leads', (err, result) => {
      stats.leads = result?.count || 0;

      db.get('SELECT COUNT(*) as count FROM calls', (err, result) => {
        stats.calls = result?.count || 0;

        db.get('SELECT COUNT(*) as count FROM deals', (err, result) => {
          stats.deals = result?.count || 0;

          db.get('SELECT COUNT(*) as count FROM commissions', (err, result) => {
            stats.commissions = result?.count || 0;

            db.get('SELECT COUNT(*) as count FROM call_targets', (err, result) => {
              stats.targets = result?.count || 0;

              db.get('SELECT COUNT(*) as count FROM documents', (err, result) => {
                stats.documents = result?.count || 0;

                res.json(stats);
              });
            });
          });
        });
      });
    });
  });
});

// Get Dashboard Data (All combined)
app.get('/api/dashboard', (req, res) => {
  db.serialize(() => {
    let dashboardData = {};

    db.all('SELECT * FROM leads LIMIT 10', (err, leads) => {
      dashboardData.leads = leads || [];

      db.all('SELECT * FROM calls LIMIT 10', (err, calls) => {
        dashboardData.calls = calls || [];

        db.all('SELECT * FROM deals LIMIT 10', (err, deals) => {
          dashboardData.deals = deals || [];

          db.get('SELECT COUNT(*) as count FROM leads', (err, result) => {
            dashboardData.leadsCount = result?.count || 0;

            db.get('SELECT COUNT(*) as count FROM calls', (err, result) => {
              dashboardData.callsCount = result?.count || 0;

              db.get('SELECT COUNT(*) as count FROM commissions', (err, result) => {
                dashboardData.commissionsCount = result?.count || 0;

                res.json(dashboardData);
              });
            });
          });
        });
      });
    });
  });
});

// ==================== START SERVER ====================
app.listen(PORT, () => {
  console.log(`🚀 ArthaInvest 10/10 Enterprise CRM running on http://localhost:${PORT}`);
  console.log(`✅ Features: Admin Commission Reports, Team Leader Target Assignment`);
  console.log(`✅ Integration: Phone-WhatsApp Linking, Google Drive Import/Export`);
  console.log(`✅ Pipeline: Deal Management, Probability Scoring`);
});
