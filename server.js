/**
 * ArthaInvest CRM - Production Backend Server
 * Node.js + Express + SQLite
 *
 * This is the REAL backend that handles:
 * - User authentication with JWT tokens
 * - Data persistence in SQLite database
 * - API endpoints for all features
 * - Error handling and validation
 * - Rate limiting and security
 * - Real file storage
 * - Audit logging
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

// Initialize Express app
const app = express();
const PORT = 3000;
const JWT_SECRET = 'arthainvest_jwt_secret_key_2026';

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ limit: '50mb', extended: true }));
app.use(cors());
app.use(express.static(path.join(__dirname))); // Serve static HTML files

// Rate limiting - Prevent DoS attacks
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = path.join(__dirname, 'uploads');
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    cb(null, `${Date.now()}_${file.originalname}`);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50MB max
  fileFilter: (req, file, cb) => {
    // Validate file types
    const allowedTypes = /jpeg|jpg|png|pdf|doc|docx|xls|xlsx/;
    const mimetype = allowedTypes.test(file.mimetype);
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());

    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Invalid file type. Only images, PDFs and office documents allowed.'));
    }
  }
});

// Initialize SQLite database
const db = new sqlite3.Database(path.join(__dirname, 'arthainvest.db'), (err) => {
  if (err) {
    console.error('Database connection error:', err);
  } else {
    console.log('✓ SQLite database connected');
    initializeDatabase();
  }
});

// Initialize database tables
function initializeDatabase() {
  db.serialize(() => {
    // Users table
    db.run(`
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        department TEXT,
        phone TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
      )
    `);

    // Clients table
    db.run(`
      CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        portfolio_value REAL DEFAULT 0,
        status TEXT DEFAULT 'Active',
        assigned_to TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(assigned_to) REFERENCES users(username)
      )
    `);

    // Invoices table
    db.run(`
      CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id TEXT UNIQUE NOT NULL,
        client_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        gst_rate REAL DEFAULT 18,
        gst_amount REAL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'Draft',
        payment_method TEXT,
        due_date DATE,
        paid_date DATE,
        created_by TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(created_by) REFERENCES users(username)
      )
    `);

    // DigiLocker documents table
    db.run(`
      CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        document_type TEXT NOT NULL,
        file_size INTEGER,
        uploaded_by TEXT NOT NULL,
        visibility TEXT DEFAULT 'private',
        expiry_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(client_id) REFERENCES clients(id),
        FOREIGN KEY(uploaded_by) REFERENCES users(username)
      )
    `);

    // Voice commands activity log
    db.run(`
      CREATE TABLE IF NOT EXISTS voice_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        client_id INTEGER,
        command TEXT NOT NULL,
        status_updated_to TEXT NOT NULL,
        confidence REAL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(username),
        FOREIGN KEY(client_id) REFERENCES clients(id)
      )
    `);

    // Marketing campaigns
    db.run(`
      CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'Planning',
        budget REAL,
        channels TEXT,
        created_by TEXT NOT NULL,
        start_date DATE,
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(created_by) REFERENCES users(username)
      )
    `);

    // Audit log
    db.run(`
      CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        resource TEXT,
        details TEXT,
        ip_address TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(username)
      )
    `);

    console.log('✓ Database tables initialized');
    createDefaultUsers();
  });
}

// Create default users (with proper password hashing)
function createDefaultUsers() {
  const users = [
    { username: 'admin', password: 'admin123', name: 'Artha Admin', email: 'admin@arthainvest.com', role: 'admin', phone: '9876543200' },
    { username: 'rajesh', password: 'rajesh123', name: 'Rajesh Kumar', email: 'rajesh@arthainvest.com', role: 'employee', department: 'Sales', phone: '9876543201' },
    { username: 'priya', password: 'priya123', name: 'Priya Sharma', email: 'priya@arthainvest.com', role: 'employee', department: 'Insurance', phone: '9876543202' },
    { username: 'amit', password: 'amit123', name: 'Amit Patel', email: 'amit@arthainvest.com', role: 'employee', department: 'Loans & DSA', phone: '9876543203' },
    { username: 'sneha', password: 'sneha123', name: 'Sneha Desai', email: 'sneha@arthainvest.com', role: 'employee', department: 'Mutual Funds', phone: '9876543204' },
    { username: 'vikram', password: 'vikram123', name: 'Vikram Singh', email: 'vikram@arthainvest.com', role: 'employee', department: 'Marketing', phone: '9876543205' }
  ];

  users.forEach(user => {
    const hashedPassword = bcrypt.hashSync(user.password, 10);
    db.run(
      'INSERT OR IGNORE INTO users (username, password, name, email, role, department, phone) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [user.username, hashedPassword, user.name, user.email, user.role, user.department || null, user.phone],
      (err) => {
        if (err) console.error('Error creating user:', err);
      }
    );
  });
}

// Middleware: Authenticate JWT token
function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
}

// Middleware: Audit logging
function auditLog(action, resource) {
  return (req, res, next) => {
    const originalSend = res.send;
    res.send = function(data) {
      if (req.user) {
        db.run(
          'INSERT INTO audit_log (user_id, action, resource, ip_address) VALUES (?, ?, ?, ?)',
          [req.user.username, action, resource, req.ip]
        );
      }
      res.send = originalSend;
      return res.send(data);
    };
    next();
  };
}

// ============ AUTH ENDPOINTS ============

// Login endpoint
app.post('/api/auth/login', (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }

  db.get(
    'SELECT * FROM users WHERE username = ?',
    [username],
    (err, user) => {
      if (err) {
        return res.status(500).json({ error: 'Database error' });
      }

      if (!user) {
        return res.status(401).json({ error: 'Invalid username or password' });
      }

      // Verify password
      if (!bcrypt.compareSync(password, user.password)) {
        return res.status(401).json({ error: 'Invalid username or password' });
      }

      // Update last login
      db.run('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', [user.id]);

      // Generate JWT token
      const token = jwt.sign(
        { id: user.id, username: user.username, role: user.role, name: user.name },
        JWT_SECRET,
        { expiresIn: '24h' }
      );

      res.json({
        success: true,
        token: token,
        user: {
          id: user.id,
          username: user.username,
          name: user.name,
          email: user.email,
          role: user.role,
          department: user.department
        }
      });
    }
  );
});

// ============ CLIENT ENDPOINTS ============

// Get all clients (with access control)
app.get('/api/clients', authenticateToken, auditLog('VIEW', 'clients'), (req, res) => {
  let query = 'SELECT * FROM clients';
  let params = [];

  // Non-admin users only see their own clients
  if (req.user.role !== 'admin') {
    query += ' WHERE assigned_to = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, clients) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch clients' });
    }
    res.json({ success: true, clients: clients || [] });
  });
});

// Create client
app.post('/api/clients', authenticateToken, auditLog('CREATE', 'client'), (req, res) => {
  const { name, email, phone, portfolio_value, status } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Client name required' });
  }

  db.run(
    'INSERT INTO clients (name, email, phone, portfolio_value, status, assigned_to) VALUES (?, ?, ?, ?, ?, ?)',
    [name, email, phone, portfolio_value || 0, status || 'Active', req.user.username],
    (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to create client' });
      }
      res.json({ success: true, message: 'Client created successfully' });
    }
  );
});

// ============ INVOICE ENDPOINTS ============

// Get invoices
app.get('/api/invoices', authenticateToken, auditLog('VIEW', 'invoices'), (req, res) => {
  let query = 'SELECT * FROM invoices';
  let params = [];

  if (req.user.role !== 'admin') {
    query += ' WHERE created_by = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, invoices) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch invoices' });
    }
    res.json({ success: true, invoices: invoices || [] });
  });
});

// Create invoice
app.post('/api/invoices', authenticateToken, auditLog('CREATE', 'invoice'), (req, res) => {
  const { client_id, amount, gst_rate, description } = req.body;

  if (!client_id || !amount) {
    return res.status(400).json({ error: 'Client and amount required' });
  }

  const gst = gst_rate || 18;
  const gst_amount = (amount * gst) / 100;
  const total = amount + gst_amount;
  const invoiceId = `ARTH-${Date.now()}`;

  db.run(
    'INSERT INTO invoices (invoice_id, client_id, amount, gst_rate, gst_amount, total_amount, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
    [invoiceId, client_id, amount, gst, gst_amount, total, req.user.username],
    (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to create invoice' });
      }
      res.json({ success: true, invoice_id: invoiceId, total: total });
    }
  );
});

// ============ DIGILOCKER ENDPOINTS ============

// Upload document
app.post('/api/digilocker/upload', authenticateToken, upload.single('document'), auditLog('UPLOAD', 'document'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'File required' });
  }

  const { client_id, document_type } = req.body;

  if (!client_id || !document_type) {
    return res.status(400).json({ error: 'Client ID and document type required' });
  }

  db.run(
    'INSERT INTO documents (client_id, file_name, file_path, document_type, file_size, uploaded_by) VALUES (?, ?, ?, ?, ?, ?)',
    [client_id, req.file.filename, req.file.path, document_type, req.file.size, req.user.username],
    (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to upload document' });
      }
      res.json({ success: true, message: 'Document uploaded successfully', file: req.file.filename });
    }
  );
});

// Get documents (with access control)
app.get('/api/digilocker/:clientId', authenticateToken, auditLog('VIEW', 'documents'), (req, res) => {
  const { clientId } = req.params;

  let query = 'SELECT * FROM documents WHERE client_id = ?';
  let params = [clientId];

  // Non-admin users only see their own documents
  if (req.user.role !== 'admin') {
    query += ' AND uploaded_by = ?';
    params.push(req.user.username);
  }

  db.all(query, params, (err, documents) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch documents' });
    }
    res.json({ success: true, documents: documents || [] });
  });
});

// ============ VOICE LOGGING ENDPOINTS ============

// Log voice command
app.post('/api/voice/log', authenticateToken, auditLog('VOICE', 'command'), (req, res) => {
  const { client_id, command, status, confidence } = req.body;

  if (!command || !status) {
    return res.status(400).json({ error: 'Command and status required' });
  }

  db.run(
    'INSERT INTO voice_logs (user_id, client_id, command, status_updated_to, confidence) VALUES (?, ?, ?, ?, ?)',
    [req.user.username, client_id || null, command, status, confidence || 0],
    (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to log voice command' });
      }
      res.json({ success: true, message: 'Voice command logged' });
    }
  );
});

// ============ MARKETING ENDPOINTS ============

// Get campaigns
app.get('/api/marketing/campaigns', authenticateToken, auditLog('VIEW', 'campaigns'), (req, res) => {
  db.all('SELECT * FROM campaigns', (err, campaigns) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch campaigns' });
    }
    res.json({ success: true, campaigns: campaigns || [] });
  });
});

// Create campaign
app.post('/api/marketing/campaigns', authenticateToken, auditLog('CREATE', 'campaign'), (req, res) => {
  const { name, description, budget, channels } = req.body;

  if (!name) {
    return res.status(400).json({ error: 'Campaign name required' });
  }

  db.run(
    'INSERT INTO campaigns (name, description, budget, channels, created_by) VALUES (?, ?, ?, ?, ?)',
    [name, description, budget, JSON.stringify(channels), req.user.username],
    (err) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to create campaign' });
      }
      res.json({ success: true, message: 'Campaign created successfully' });
    }
  );
});

// ============ ANALYTICS ENDPOINTS ============

// Get user analytics
app.get('/api/analytics/user', authenticateToken, (req, res) => {
  const username = req.user.role === 'admin' ? (req.query.user || req.user.username) : req.user.username;

  db.all('SELECT * FROM audit_log WHERE user_id = ? ORDER BY created_at DESC LIMIT 50', [username], (err, logs) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch analytics' });
    }

    db.all('SELECT COUNT(*) as count FROM clients WHERE assigned_to = ?', [username], (err, result) => {
      if (err) {
        return res.status(500).json({ error: 'Failed to fetch client count' });
      }

      db.all('SELECT COUNT(*) as count, SUM(total_amount) as total FROM invoices WHERE created_by = ?', [username], (err, invResult) => {
        if (err) {
          return res.status(500).json({ error: 'Failed to fetch invoice data' });
        }

        res.json({
          success: true,
          analytics: {
            total_clients: result[0].count,
            total_invoiced: invResult[0].total || 0,
            recent_activity: logs
          }
        });
      });
    });
  });
});

// ============ ERROR HANDLING ============

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Global error handler
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ error: 'Internal server error', message: err.message });
});

// ============ START SERVER ============

app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════════════╗
║   🚀 ArthaInvest CRM Backend Server Started              ║
║   ✓ Production-Grade API Ready                           ║
║   ✓ Database: SQLite (arthainvest.db)                    ║
║   ✓ Authentication: JWT Tokens                           ║
║   ✓ Rate Limiting: Enabled                               ║
║   ✓ Audit Logging: Enabled                               ║
║   ✓ File Storage: Enabled (uploads/)                     ║
║                                                           ║
║   Server running on: http://localhost:${PORT}            ║
║   API Base URL: http://localhost:${PORT}/api             ║
║                                                           ║
║   Endpoints:                                              ║
║   - POST   /api/auth/login                               ║
║   - GET    /api/clients                                  ║
║   - POST   /api/clients                                  ║
║   - GET    /api/invoices                                 ║
║   - POST   /api/invoices                                 ║
║   - POST   /api/digilocker/upload                        ║
║   - GET    /api/digilocker/:clientId                     ║
║   - POST   /api/voice/log                                ║
║   - GET    /api/marketing/campaigns                      ║
║   - POST   /api/marketing/campaigns                      ║
║   - GET    /api/analytics/user                           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
  `);
});

module.exports = app;
