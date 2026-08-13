-- ARTHAINVEST CRM - COMPREHENSIVE DATABASE SCHEMA
-- Enterprise-grade CRM with multi-role access, AI scoring, and integrations

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  name TEXT NOT NULL,
  email TEXT,
  role TEXT NOT NULL CHECK(role IN ('admin', 'marketing', 'employee', 'team_leader')),
  department TEXT,
  is_active INTEGER DEFAULT 1,
  is_online INTEGER DEFAULT 0,
  last_login DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  phone TEXT UNIQUE,
  email TEXT,
  pan TEXT UNIQUE,
  aadhar TEXT,
  family_head TEXT,
  sub_broker TEXT,
  aum REAL DEFAULT 0,
  status TEXT DEFAULT 'New' CHECK(status IN ('New', 'Interested', 'Not Interested', 'Follow-up', 'Converted')),
  assigned_to INTEGER REFERENCES users(id),
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS opportunities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  client_id INTEGER REFERENCES clients(id),
  follow_up_date DATE,
  status TEXT DEFAULT 'New' CHECK(status IN ('New', 'In Progress', 'Requirements Gathered', 'Documentation', 'Converted', 'Lost')),
  expected_value REAL DEFAULT 0,
  ai_score INTEGER DEFAULT 0,
  source TEXT,
  product_type TEXT CHECK(product_type IN ('Insurance', 'Loans', 'Mutual Funds', 'Brokerage')),
  assigned_to INTEGER REFERENCES users(id),
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  opportunity_id INTEGER REFERENCES opportunities(id),
  caller_id INTEGER REFERENCES users(id),
  call_date DATETIME DEFAULT CURRENT_TIMESTAMP,
  call_duration INTEGER,
  result TEXT CHECK(result IN ('Interested', 'Not Interested', 'Follow-up', 'Converted', 'Meeting Scheduled')),
  notes TEXT,
  call_type TEXT CHECK(call_type IN ('Inbound', 'Outbound', 'Scheduled')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  call_id INTEGER REFERENCES calls(id),
  file_path TEXT,
  duration INTEGER,
  transcription TEXT,
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS campaigns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  product_type TEXT CHECK(product_type IN ('Insurance', 'Loans', 'Mutual Funds', 'Brokerage')),
  assigned_to INTEGER REFERENCES users(id),
  target_count INTEGER DEFAULT 0,
  achieved_count INTEGER DEFAULT 0,
  start_date DATE,
  end_date DATE,
  status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Paused', 'Completed', 'Cancelled')),
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT,
  client_id INTEGER REFERENCES clients(id),
  opportunity_id INTEGER REFERENCES opportunities(id),
  assigned_to INTEGER REFERENCES users(id),
  due_date DATE,
  status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'In Progress', 'Completed', 'Overdue')),
  priority TEXT CHECK(priority IN ('Low', 'Medium', 'High', 'Urgent')),
  reminder_time DATETIME,
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  document_type TEXT CHECK(document_type IN ('PAN', 'Aadhar', 'Bank Statement', 'Income Proof', 'KYC', 'Other')),
  file_path TEXT,
  file_name TEXT,
  uploaded_by INTEGER REFERENCES users(id),
  visibility TEXT DEFAULT 'private' CHECK(visibility IN ('private', 'team', 'admin')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS communications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  opportunity_id INTEGER REFERENCES opportunities(id),
  communication_type TEXT CHECK(communication_type IN ('Email', 'WhatsApp', 'SMS', 'LinkedIn', 'Call')),
  message_text TEXT,
  status TEXT DEFAULT 'Sent' CHECK(status IN ('Sent', 'Delivered', 'Read', 'Failed', 'Scheduled')),
  scheduled_time DATETIME,
  sent_by INTEGER REFERENCES users(id),
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  subject TEXT,
  body TEXT,
  product_type TEXT,
  is_ai_generated INTEGER DEFAULT 0,
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whatsapp_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  message TEXT NOT NULL,
  product_type TEXT,
  is_ai_generated INTEGER DEFAULT 0,
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS insurance_policies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  policy_number TEXT UNIQUE,
  policy_holder TEXT,
  policy_name TEXT,
  issue_date DATE,
  renewal_date DATE,
  premium REAL DEFAULT 0,
  sum_assured REAL DEFAULT 0,
  status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Lapsed', 'Expired', 'Renewed')),
  product_type TEXT CHECK(product_type IN ('Life Insurance', 'General Insurance', 'Health Insurance')),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loan_applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  loan_type TEXT CHECK(loan_type IN ('Personal Loan', 'Home Loan', 'Auto Loan', 'Business Loan')),
  loan_amount REAL DEFAULT 0,
  application_date DATE,
  status TEXT DEFAULT 'Applied' CHECK(status IN ('Applied', 'In Progress', 'Approved', 'Rejected', 'Disbursed')),
  tenure_months INTEGER,
  interest_rate REAL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mutual_funds (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  folio_number TEXT UNIQUE,
  fund_name TEXT,
  investment_amount REAL DEFAULT 0,
  current_value REAL DEFAULT 0,
  investment_date DATE,
  status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Redeemed', 'Matured')),
  sip_active INTEGER DEFAULT 0,
  sip_amount REAL DEFAULT 0,
  sip_frequency TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brokerage_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_id INTEGER REFERENCES clients(id),
  broker_name TEXT,
  account_number TEXT,
  account_type TEXT,
  arn_number TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_metrics (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  metric_date DATE,
  calls_made INTEGER DEFAULT 0,
  conversions INTEGER DEFAULT 0,
  conversion_rate REAL DEFAULT 0,
  opportunities_created INTEGER DEFAULT 0,
  tasks_completed INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_automations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  automation_type TEXT CHECK(automation_type IN ('Email', 'WhatsApp', 'SMS', 'LinkedIn')),
  trigger_type TEXT CHECK(trigger_type IN ('Lead Created', 'Follow-up Due', 'Status Change', 'Manual')),
  template_id INTEGER,
  is_active INTEGER DEFAULT 1,
  created_by INTEGER REFERENCES users(id),
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  activity_type TEXT,
  entity_type TEXT,
  entity_id INTEGER,
  description TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS linkedin_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  linkedin_id TEXT,
  access_token TEXT,
  is_connected INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES FOR PERFORMANCE
CREATE INDEX idx_clients_assigned_to ON clients(assigned_to);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_assigned_to ON opportunities(assigned_to);
CREATE INDEX idx_calls_caller_id ON calls(caller_id);
CREATE INDEX idx_campaigns_assigned_to ON campaigns(assigned_to);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_documents_client_id ON documents(client_id);
CREATE INDEX idx_communications_client_id ON communications(client_id);
CREATE INDEX idx_performance_user_date ON performance_metrics(user_id, metric_date);

-- INSERT DEFAULT ADMIN USER
INSERT OR IGNORE INTO users (username, password, name, email, role, department, is_active)
VALUES ('admin', '$2b$10$YourHashedPasswordHere', 'Admin User', 'admin@arthainvest.com', 'admin', 'Management', 1);

-- INSERT DEFAULT TEAM MEMBERS
INSERT OR IGNORE INTO users (username, password, name, email, role, department, is_active)
VALUES
('rajesh', '$2b$10$YourHashedPasswordHere', 'Rajesh Kumar', 'rajesh@arthainvest.com', 'employee', 'Sales', 1),
('priya', '$2b$10$YourHashedPasswordHere', 'Priya Sharma', 'priya@arthainvest.com', 'employee', 'Insurance', 1),
('amit', '$2b$10$YourHashedPasswordHere', 'Amit Singh', 'amit@arthainvest.com', 'employee', 'Loans', 1),
('sneha', '$2b$10$YourHashedPasswordHere', 'Sneha Patel', 'sneha@arthainvest.com', 'employee', 'Mutual Funds', 1),
('vikram', '$2b$10$YourHashedPasswordHere', 'Vikram Desai', 'vikram@arthainvest.com', 'employee', 'Marketing', 1),
('team_leader', '$2b$10$YourHashedPasswordHere', 'Team Leader', 'leader@arthainvest.com', 'team_leader', 'Management', 1),
('marketing_user', '$2b$10$YourHashedPasswordHere', 'Marketing User', 'marketing@arthainvest.com', 'marketing', 'Marketing', 1);
