-- ============================================================================
-- ARTHAINVEST FIELD CRM - ENTERPRISE DATABASE SCHEMA (Bigin Level)
-- ============================================================================

-- Users & Team Management
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  role TEXT NOT NULL,
  department TEXT,
  status TEXT DEFAULT 'active',
  profile_photo TEXT,
  login_time DATETIME,
  logout_time DATETIME,
  is_online BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Campaigns & Products
CREATE TABLE IF NOT EXISTS campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  product_type TEXT NOT NULL,
  description TEXT,
  assigned_to TEXT NOT NULL,
  start_date DATE,
  end_date DATE,
  target_count INTEGER,
  achieved_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active',
  created_by TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assigned_to) REFERENCES users(username),
  FOREIGN KEY (created_by) REFERENCES users(username)
);

-- Clients/Contacts
CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT,
  whatsapp TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  pincode TEXT,
  product_interested TEXT,
  assigned_to TEXT NOT NULL,
  campaign_id INTEGER,
  status TEXT DEFAULT 'prospect',
  rating INTEGER,
  notes TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assigned_to) REFERENCES users(username),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- Calls Log & Activity Tracking
CREATE TABLE IF NOT EXISTS calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  caller_id TEXT NOT NULL,
  client_id INTEGER NOT NULL,
  campaign_id INTEGER,
  call_duration INTEGER,
  call_result TEXT,
  call_notes TEXT,
  voice_note_file TEXT,
  call_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  follow_up_date DATE,
  follow_up_time TIME,
  FOREIGN KEY (caller_id) REFERENCES users(username),
  FOREIGN KEY (client_id) REFERENCES clients(id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
);

-- Voice Notes
CREATE TABLE IF NOT EXISTS voice_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id INTEGER NOT NULL,
  user_id TEXT NOT NULL,
  file_path TEXT NOT NULL,
  duration INTEGER,
  transcription TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (call_id) REFERENCES calls(id),
  FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Documents (DigiLocker)
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  document_type TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_size INTEGER,
  uploaded_by TEXT NOT NULL,
  uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_id) REFERENCES clients(id),
  FOREIGN KEY (uploaded_by) REFERENCES users(username)
);

-- Communications Log (WhatsApp, Email, SMS)
CREATE TABLE IF NOT EXISTS communications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER NOT NULL,
  sender_id TEXT NOT NULL,
  channel TEXT NOT NULL,
  message TEXT,
  status TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (client_id) REFERENCES clients(id),
  FOREIGN KEY (sender_id) REFERENCES users(username)
);

-- Activities & Audit Log
CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  action TEXT NOT NULL,
  resource TEXT,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Performance Metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  date DATE,
  calls_made INTEGER DEFAULT 0,
  calls_converted INTEGER DEFAULT 0,
  conversion_rate DECIMAL(5,2),
  follow_ups_scheduled INTEGER DEFAULT 0,
  documents_uploaded INTEGER DEFAULT 0,
  login_duration INTEGER,
  FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Tasks & Follow-ups
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  assigned_to TEXT NOT NULL,
  client_id INTEGER,
  task_type TEXT,
  due_date DATE,
  due_time TIME,
  priority TEXT DEFAULT 'medium',
  status TEXT DEFAULT 'open',
  created_by TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  FOREIGN KEY (assigned_to) REFERENCES users(username),
  FOREIGN KEY (client_id) REFERENCES clients(id),
  FOREIGN KEY (created_by) REFERENCES users(username)
);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT,
  type TEXT,
  read_status BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Integrations Settings
CREATE TABLE IF NOT EXISTS integrations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL,
  service TEXT NOT NULL,
  api_key TEXT,
  enabled BOOLEAN DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(username)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_clients_assigned_to ON clients(assigned_to);
CREATE INDEX IF NOT EXISTS idx_calls_caller_id ON calls(caller_id);
CREATE INDEX IF NOT EXISTS idx_calls_client_id ON calls(client_id);
CREATE INDEX IF NOT EXISTS idx_calls_call_time ON calls(call_time);
CREATE INDEX IF NOT EXISTS idx_campaigns_assigned_to ON campaigns(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_activities_user_id ON activities(user_id);
CREATE INDEX IF NOT EXISTS idx_performance_user_date ON performance_metrics(user_id, date);

-- Insert default users
INSERT OR IGNORE INTO users (username, password, name, email, role, department) VALUES
('admin', '$2a$10$admin_hashed_password', 'ArthaInvest Admin', 'admin@arthainvest.com', 'admin', 'Management'),
('rajesh', '$2a$10$rajesh_hashed_password', 'Rajesh Kumar', 'rajesh@arthainvest.com', 'employee', 'Sales'),
('priya', '$2a$10$priya_hashed_password', 'Priya Sharma', 'priya@arthainvest.com', 'employee', 'Insurance'),
('amit', '$2a$10$amit_hashed_password', 'Amit Singh', 'amit@arthainvest.com', 'employee', 'Loans'),
('sneha', '$2a$10$sneha_hashed_password', 'Sneha Patel', 'sneha@arthainvest.com', 'employee', 'Funds'),
('vikram', '$2a$10$vikram_hashed_password', 'Vikram Desai', 'vikram@arthainvest.com', 'employee', 'Marketing');
