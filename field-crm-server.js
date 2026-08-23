/**
 * ARTHAINVEST FIELD CRM - ENTERPRISE BACKEND (Bigin Level)
 * Field team tracking, call management, document storage, communication hub
 */

const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const multer = require('multer');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'arthainvest_crm_secret_2026';

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));
app.use(cors());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: 'Too many requests, please try again later.'
});
app.use(limiter);

// File upload
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}_${file.originalname}`);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|pdf|doc|docx|mp3|wav|m4a/;
    const mimetype = allowedTypes.test(file.mimetype);
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    if (mimetype && extname) return cb(null, true);
    cb(new Error('Invalid file type'));
  }
});

// Database
const db = new sqlite3.Database(path.join(__dirname, 'arthainvest.db'), (err) => {
  if (err) console.error('Database error:', err);
  else {
    console.log('✓ Database connected');
    initializeDatabase();
  }
});

// Initialize database
function initializeDatabase() {
  const schema = fs.readFileSync(path.join(__dirname, 'FIELD_CRM_SCHEMA.sql'), 'utf8');
  db.exec(schema, (err) => {
    if (err) console.error('Schema error:', err);
    else console.log('✓ Database schema ready');
  });
}

// Auth middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) return res.status(401).json({ error: 'No token provided' });

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
};

// ============================================================================
// AUTHENTICATION APIs
// ============================================================================

app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;

  db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
    if (err || !user) return res.status(401).json({ error: 'Invalid credentials' });

    // Simple password check (in production use bcrypt)
    const passwordMatch = password === username; // Temporary for testing
    if (!passwordMatch) return res.status(401).json({ error: 'Invalid credentials' });

    const token = jwt.sign({ username: user.username, role: user.role }, JWT_SECRET, { expiresIn: '24h' });

    // Update login time and online status
    db.run('UPDATE users SET login_time = CURRENT_TIMESTAMP, is_online = 1 WHERE username = ?', [username]);

    res.json({
      success: true,
      token,
      user: {
        username: user.username,
        name: user.name,
        email: user.email,
        role: user.role,
        department: user.department
      }
    });
  });
});

app.post('/api/auth/logout', authenticateToken, (req, res) => {
  db.run('UPDATE users SET logout_time = CURRENT_TIMESTAMP, is_online = 0 WHERE username = ?', [req.user.username]);
  res.json({ success: true });
});

// ============================================================================
// TEAM MANAGEMENT APIs
// ============================================================================

app.get('/api/team/status', authenticateToken, (req, res) => {
  db.all('SELECT username, name, is_online, login_time, logout_time, department FROM users', (err, users) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, team: users });
  });
});

app.get('/api/team/performance', authenticateToken, (req, res) => {
  const date = new Date().toISOString().split('T')[0];

  db.all(`
    SELECT
      user_id,
      calls_made,
      calls_converted,
      conversion_rate,
      follow_ups_scheduled,
      documents_uploaded
    FROM performance_metrics
    WHERE date = ?
  `, [date], (err, metrics) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, metrics });
  });
});

// ============================================================================
// CAMPAIGN APIs
// ============================================================================

app.post('/api/campaigns', authenticateToken, (req, res) => {
  const { name, product_type, assigned_to, start_date, end_date, target_count } = req.body;

  db.run(
    'INSERT INTO campaigns (name, product_type, assigned_to, start_date, end_date, target_count, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [name, product_type, assigned_to, start_date, end_date, target_count, req.user.username],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Campaign created' });
    }
  );
});

app.get('/api/campaigns', authenticateToken, (req, res) => {
  let query = 'SELECT * FROM campaigns';
  let params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE assigned_to = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, campaigns) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, campaigns });
  });
});

// ============================================================================
// CLIENT/CONTACT APIs
// ============================================================================

app.post('/api/clients', authenticateToken, (req, res) => {
  const { name, phone, email, whatsapp, product_interested, campaign_id } = req.body;

  db.run(
    'INSERT INTO clients (name, phone, email, whatsapp, product_interested, assigned_to, campaign_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [name, phone, email, whatsapp, product_interested, req.user.username, campaign_id || null],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Client added' });
    }
  );
});

app.get('/api/clients', authenticateToken, (req, res) => {
  let query = 'SELECT * FROM clients';
  let params = [];

  if (req.user.role === 'employee') {
    query += ' WHERE assigned_to = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, clients) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, clients });
  });
});

app.put('/api/clients/:id', authenticateToken, (req, res) => {
  const { status, notes } = req.body;

  db.run(
    'UPDATE clients SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
    [status, notes, req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true });
    }
  );
});

// ============================================================================
// CALL LOGGING & VOICE NOTES
// ============================================================================

app.post('/api/calls/log', authenticateToken, (req, res) => {
  const { client_id, campaign_id, call_duration, call_result, call_notes, follow_up_date } = req.body;

  db.run(
    'INSERT INTO calls (caller_id, client_id, campaign_id, call_duration, call_result, call_notes, follow_up_date) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [req.user.username, client_id, campaign_id, call_duration, call_result, call_notes, follow_up_date],
    function(err) {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, call_id: this.lastID });
    }
  );
});

app.post('/api/calls/voice-note/:callId', authenticateToken, upload.single('audio'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No audio file' });

  db.run(
    'INSERT INTO voice_notes (call_id, user_id, file_path, duration) VALUES (?, ?, ?, ?)',
    [req.params.callId, req.user.username, req.file.path, req.body.duration || 0],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, file_path: req.file.path });
    }
  );
});

app.get('/api/calls/history/:clientId', authenticateToken, (req, res) => {
  db.all(
    'SELECT * FROM calls WHERE client_id = ? ORDER BY call_time DESC',
    [req.params.clientId],
    (err, calls) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, calls });
    }
  );
});

// ============================================================================
// DOCUMENTS (DigiLocker)
// ============================================================================

app.post('/api/documents/upload', authenticateToken, upload.single('document'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No document' });

  const { client_id, document_type } = req.body;

  db.run(
    'INSERT INTO documents (client_id, document_type, file_name, file_path, file_size, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)',
    [client_id, document_type, req.file.originalname, req.file.path, req.file.size, req.user.username],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Document uploaded' });
    }
  );
});

app.get('/api/documents/:clientId', authenticateToken, (req, res) => {
  db.all(
    'SELECT * FROM documents WHERE client_id = ?',
    [req.params.clientId],
    (err, documents) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, documents });
    }
  );
});

// ============================================================================
// COMMUNICATIONS (WhatsApp, Email, SMS)
// ============================================================================

app.post('/api/communications/send', authenticateToken, (req, res) => {
  const { client_id, channel, message } = req.body;

  db.run(
    'INSERT INTO communications (client_id, sender_id, channel, message, status) VALUES (?, ?, ?, ?, ?)',
    [client_id, req.user.username, channel, message, 'sent'],
    async (err) => {
      if (err) return res.status(500).json({ error: err.message });

      // TODO: Integrate with WhatsApp/Email/SMS APIs
      // Example: Send via Twilio for WhatsApp/SMS
      // Example: Send via SendGrid for Email

      res.json({ success: true, message: 'Message sent' });
    }
  );
});

app.get('/api/communications/:clientId', authenticateToken, (req, res) => {
  db.all(
    'SELECT * FROM communications WHERE client_id = ? ORDER BY created_at DESC',
    [req.params.clientId],
    (err, communications) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, communications });
    }
  );
});

// ============================================================================
// TASKS & FOLLOW-UPS
// ============================================================================

app.post('/api/tasks', authenticateToken, (req, res) => {
  const { title, description, assigned_to, client_id, due_date, priority } = req.body;

  db.run(
    'INSERT INTO tasks (title, description, assigned_to, client_id, due_date, priority, created_by, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
    [title, description, assigned_to, client_id, due_date, priority || 'medium', req.user.username, 'open'],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, message: 'Task created' });
    }
  );
});

app.get('/api/tasks', authenticateToken, (req, res) => {
  let query = 'SELECT * FROM tasks WHERE status = ?';
  let params = ['open'];

  if (req.user.role === 'employee') {
    query += ' AND assigned_to = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, tasks) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ success: true, tasks });
  });
});

app.put('/api/tasks/:id/complete', authenticateToken, (req, res) => {
  db.run(
    'UPDATE tasks SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?',
    ['completed', req.params.id],
    (err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true });
    }
  );
});

// ============================================================================
// ANALYTICS & REPORTS
// ============================================================================

app.get('/api/analytics/daily/:userId', authenticateToken, (req, res) => {
  const date = new Date().toISOString().split('T')[0];

  db.get(
    'SELECT * FROM performance_metrics WHERE user_id = ? AND date = ?',
    [req.params.userId, date],
    (err, metrics) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, metrics: metrics || {} });
    }
  );
});

app.get('/api/analytics/team', authenticateToken, (req, res) => {
  if (req.user.role !== 'admin') return res.status(403).json({ error: 'Unauthorized' });

  const date = new Date().toISOString().split('T')[0];

  db.all(
    'SELECT user_id, calls_made, calls_converted, conversion_rate FROM performance_metrics WHERE date = ? ORDER BY calls_converted DESC',
    [date],
    (err, metrics) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ success: true, metrics });
    }
  );
});

// ============================================================================
// HEALTH CHECK
// ============================================================================

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).json({ error: err.message || 'Server error' });
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log(`\n╔════════════════════════════════════════════════════════╗`);
  console.log(`║   🚀 ARTHAINVEST FIELD CRM SERVER STARTED             ║`);
  console.log(`║                                                        ║`);
  console.log(`║   Bigin-Level Enterprise Capabilities                  ║`);
  console.log(`║   Field Team Tracking • Call Management                ║`);
  console.log(`║   Document Storage • Communication Hub                 ║`);
  console.log(`║                                                        ║`);
  console.log(`║   Running on: http://localhost:${PORT}                   ║`);
  console.log(`║   API Base: http://localhost:${PORT}/api                 ║`);
  console.log(`╚════════════════════════════════════════════════════════╝\n`);
});

module.exports = app;
