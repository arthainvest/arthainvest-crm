-- ============================================
-- ARTHAINVEST FINTECH CRM DATABASE SCHEMA
-- ============================================

-- Users Table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  phone VARCHAR(20),
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  role VARCHAR(50) DEFAULT 'EMPLOYEE',
  position VARCHAR(100),
  department VARCHAR(100),
  avatar_url VARCHAR(500),
  status VARCHAR(20) DEFAULT 'ACTIVE',
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Contacts Master Table
CREATE TABLE IF NOT EXISTS contacts (
  contact_id VARCHAR(50) PRIMARY KEY,
  dedup_hash VARCHAR(255) UNIQUE NOT NULL,
  source_ids JSONB DEFAULT '[]'::JSONB,

  -- Classification
  contact_type VARCHAR(50) NOT NULL,
  contact_subtype VARCHAR(100),
  tier VARCHAR(10) DEFAULT 'C',
  segment VARCHAR(50) NOT NULL,
  priority VARCHAR(10),

  -- Core Contact Info
  name VARCHAR(255) NOT NULL,
  mobile VARCHAR(15) NOT NULL,
  mobile_2 VARCHAR(15),
  email VARCHAR(255),
  city VARCHAR(100),

  -- Professional Profile
  employer VARCHAR(255),
  job_title VARCHAR(150),

  -- Workflow & Ownership
  status VARCHAR(50) NOT NULL DEFAULT 'Uncontacted',
  status_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  owner VARCHAR(100) DEFAULT 'Unassigned',
  whose VARCHAR(50),

  -- Source & Lead Origin
  source VARCHAR(20) NOT NULL,
  list VARCHAR(100),
  approach_strategy TEXT,
  already_in_db VARCHAR(10),

  -- Financial Profile
  budget DECIMAL(15,2),
  aum DECIMAL(15,2),
  monthly_commit DECIMAL(15,2),
  lifetime_commission DECIMAL(15,2),

  -- Products & Policies
  products JSONB DEFAULT '[]'::JSONB,
  policy_numbers JSONB DEFAULT '[]'::JSONB,

  -- Action & Follow-up
  next_action TEXT,
  next_action_date DATE,
  last_contact TIMESTAMP,
  last_contact_type VARCHAR(50),
  next_review DATE,

  -- Metadata
  date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_converted DATE,
  notes TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Indexes
  UNIQUE (dedup_hash)
);

-- Create Indexes for Contacts
CREATE INDEX idx_contacts_mobile ON contacts(mobile);
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_owner ON contacts(owner);
CREATE INDEX idx_contacts_status ON contacts(status);
CREATE INDEX idx_contacts_contact_type ON contacts(contact_type);
CREATE INDEX idx_contacts_tier ON contacts(tier);
CREATE INDEX idx_contacts_segment ON contacts(segment);
CREATE INDEX idx_contacts_date_added ON contacts(date_added);
CREATE INDEX idx_contacts_status_updated_at ON contacts(status_updated_at);
CREATE INDEX idx_contacts_next_action_date ON contacts(next_action_date);

-- Pipelines Table
CREATE TABLE IF NOT EXISTS pipelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,
  color VARCHAR(20),
  order_sequence INTEGER,
  is_active BOOLEAN DEFAULT true,
  created_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline Stages Table
CREATE TABLE IF NOT EXISTS pipeline_stages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  order_sequence INTEGER,
  color VARCHAR(20),
  is_terminal BOOLEAN DEFAULT false,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deals/Opportunities Table
CREATE TABLE IF NOT EXISTS deals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),
  pipeline_id UUID NOT NULL REFERENCES pipelines(id),
  stage_id UUID NOT NULL REFERENCES pipeline_stages(id),

  title VARCHAR(255) NOT NULL,
  description TEXT,
  amount DECIMAL(15,2),
  probability INTEGER DEFAULT 50,
  expected_close_date DATE,
  actual_close_date DATE,

  owner_id UUID REFERENCES users(id),
  assigned_to_id UUID REFERENCES users(id),

  product VARCHAR(100),
  status VARCHAR(50) DEFAULT 'OPEN',

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Communications History Table
CREATE TABLE IF NOT EXISTS communications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),
  deal_id UUID REFERENCES deals(id),

  type VARCHAR(50) NOT NULL,
  channel VARCHAR(50) NOT NULL,
  direction VARCHAR(20),

  subject VARCHAR(500),
  message TEXT,

  from_id UUID REFERENCES users(id),
  to_number VARCHAR(20),
  to_email VARCHAR(255),

  status VARCHAR(50) DEFAULT 'SENT',
  read_at TIMESTAMP,

  duration_seconds INTEGER,
  recording_url VARCHAR(500),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks/Activities Table
CREATE TABLE IF NOT EXISTS tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),
  deal_id UUID REFERENCES deals(id),

  title VARCHAR(500) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,
  priority VARCHAR(20) DEFAULT 'MEDIUM',
  status VARCHAR(50) DEFAULT 'TODO',

  assigned_to_id UUID REFERENCES users(id),
  created_by_id UUID REFERENCES users(id),

  due_date DATE NOT NULL,
  due_time TIME,
  reminder_at TIMESTAMP,

  completion_date TIMESTAMP,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Call Logs Table
CREATE TABLE IF NOT EXISTS call_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),
  user_id UUID REFERENCES users(id),

  phone_number VARCHAR(20) NOT NULL,
  call_type VARCHAR(20) NOT NULL,
  call_status VARCHAR(50) NOT NULL,
  duration_seconds INTEGER,

  recording_url VARCHAR(500),
  transcript TEXT,
  ai_summary TEXT,

  notes TEXT,

  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  ended_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meeting Logs Table
CREATE TABLE IF NOT EXISTS meetings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),
  deal_id UUID REFERENCES deals(id),

  title VARCHAR(500) NOT NULL,
  description TEXT,

  meeting_type VARCHAR(50) NOT NULL,
  platform VARCHAR(50),
  meeting_link VARCHAR(500),

  organizer_id UUID NOT NULL REFERENCES users(id),
  participant_ids JSONB DEFAULT '[]'::JSONB,

  scheduled_at TIMESTAMP NOT NULL,
  started_at TIMESTAMP,
  ended_at TIMESTAMP,

  notes TEXT,
  outcome VARCHAR(255),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Templates Table
CREATE TABLE IF NOT EXISTS email_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100),

  subject VARCHAR(500) NOT NULL,
  body TEXT NOT NULL,

  variables JSONB DEFAULT '[]'::JSONB,

  created_by_id UUID REFERENCES users(id),
  is_active BOOLEAN DEFAULT true,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WhatsApp Templates Table
CREATE TABLE IF NOT EXISTS whatsapp_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  category VARCHAR(100),

  body TEXT NOT NULL,
  header_text VARCHAR(1024),
  footer_text VARCHAR(1024),

  variables JSONB DEFAULT '[]'::JSONB,
  buttons JSONB DEFAULT '[]'::JSONB,

  created_by_id UUID REFERENCES users(id),
  is_active BOOLEAN DEFAULT true,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Import/Export Logs Table
CREATE TABLE IF NOT EXISTS import_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),

  type VARCHAR(50) NOT NULL,
  file_name VARCHAR(500),
  file_size BIGINT,
  file_url VARCHAR(500),

  status VARCHAR(50) DEFAULT 'PENDING',
  total_records INTEGER,
  successful_records INTEGER,
  failed_records INTEGER,

  error_log TEXT,

  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports Table
CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(500) NOT NULL,
  description TEXT,
  type VARCHAR(100) NOT NULL,

  created_by_id UUID NOT NULL REFERENCES users(id),

  filters JSONB DEFAULT '{}'::JSONB,
  metrics JSONB DEFAULT '[]'::JSONB,

  is_scheduled BOOLEAN DEFAULT false,
  schedule_frequency VARCHAR(50),
  recipients JSONB DEFAULT '[]'::JSONB,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity Logs (Audit Trail)
CREATE TABLE IF NOT EXISTS activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  contact_id VARCHAR(50) REFERENCES contacts(contact_id),

  action VARCHAR(255) NOT NULL,
  entity_type VARCHAR(100),
  entity_id VARCHAR(255),

  old_values JSONB,
  new_values JSONB,

  ip_address VARCHAR(50),
  user_agent TEXT,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Marketing Blogs Table
CREATE TABLE IF NOT EXISTS marketing_blogs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(500) NOT NULL,
  slug VARCHAR(500) UNIQUE NOT NULL,
  description TEXT,
  content TEXT NOT NULL,

  featured_image_url VARCHAR(500),

  author_id UUID REFERENCES users(id),
  category VARCHAR(100),
  tags JSONB DEFAULT '[]'::JSONB,

  is_published BOOLEAN DEFAULT false,
  published_at TIMESTAMP,

  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,

  seo_title VARCHAR(500),
  seo_description VARCHAR(1000),

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document Management (DigiLocker)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),

  file_name VARCHAR(500) NOT NULL,
  file_url VARCHAR(500) NOT NULL,
  file_type VARCHAR(50),
  file_size BIGINT,

  document_type VARCHAR(100),
  category VARCHAR(100),

  uploaded_by_id UUID REFERENCES users(id),

  is_verified BOOLEAN DEFAULT false,
  verified_by_id UUID REFERENCES users(id),
  verified_at TIMESTAMP,

  expiry_date DATE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lead Assignment History
CREATE TABLE IF NOT EXISTS lead_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id VARCHAR(50) NOT NULL REFERENCES contacts(contact_id),

  assigned_from_id UUID REFERENCES users(id),
  assigned_to_id UUID NOT NULL REFERENCES users(id),

  assignment_type VARCHAR(50),
  reason TEXT,

  status VARCHAR(50) DEFAULT 'ACTIVE',

  assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  unassigned_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dashboard Views/Saved Filters
CREATE TABLE IF NOT EXISTS saved_views (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),

  name VARCHAR(255) NOT NULL,
  description TEXT,

  entity_type VARCHAR(100) NOT NULL,
  filters JSONB DEFAULT '{}'::JSONB,
  columns JSONB DEFAULT '[]'::JSONB,
  sort_by JSONB,

  is_default BOOLEAN DEFAULT false,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX idx_deals_contact_id ON deals(contact_id);
CREATE INDEX idx_deals_pipeline_id ON deals(pipeline_id);
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_communications_contact_id ON communications(contact_id);
CREATE INDEX idx_communications_type ON communications(type);
CREATE INDEX idx_tasks_contact_id ON tasks(contact_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_call_logs_contact_id ON call_logs(contact_id);
CREATE INDEX idx_meetings_contact_id ON meetings(contact_id);
CREATE INDEX idx_activity_logs_user_id ON activity_logs(user_id);
CREATE INDEX idx_documents_contact_id ON documents(contact_id);

-- Create Views for Common Queries

-- Active Contacts Summary
CREATE OR REPLACE VIEW v_active_contacts_summary AS
SELECT
  contact_type,
  tier,
  segment,
  status,
  COUNT(*) as count,
  SUM(CASE WHEN aum IS NOT NULL THEN aum ELSE 0 END) as total_aum,
  SUM(CASE WHEN budget IS NOT NULL THEN budget ELSE 0 END) as total_budget
FROM contacts
WHERE status != 'Dead'
GROUP BY contact_type, tier, segment, status;

-- Funnel Analysis View
CREATE OR REPLACE VIEW v_funnel_analysis AS
SELECT
  contact_type,
  status,
  owner,
  COUNT(*) as count,
  COUNT(DISTINCT owner) as team_count,
  AVG(EXTRACT(DAY FROM (CURRENT_TIMESTAMP - status_updated_at))) as avg_days_in_stage
FROM contacts
WHERE contact_type IN ('LEAD', 'PROSPECT')
GROUP BY contact_type, status, owner;

-- Revenue Forecast View
CREATE OR REPLACE VIEW v_revenue_forecast AS
SELECT
  segment,
  tier,
  COUNT(*) as contact_count,
  SUM(CASE WHEN contact_type = 'CLIENT' THEN aum ELSE 0 END) as current_aum,
  SUM(CASE WHEN contact_type = 'LEAD' THEN budget ELSE 0 END) as potential_budget,
  SUM(CASE WHEN contact_type = 'CLIENT' THEN lifetime_commission ELSE 0 END) as commission_earned
FROM contacts
GROUP BY segment, tier;

GRANT SELECT ON v_active_contacts_summary TO postgres;
GRANT SELECT ON v_funnel_analysis TO postgres;
GRANT SELECT ON v_revenue_forecast TO postgres;
