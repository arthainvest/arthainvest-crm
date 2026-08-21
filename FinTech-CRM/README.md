# ArthaInvest Fintech CRM
### Production-Grade CRM for Financial Services Distribution

A comprehensive CRM solution combining Kylas.io design philosophy with advanced fintech features specifically built for insurance distributors, mutual fund advisors, and financial service professionals.

## Key Features

### 1. **Dashboard & Analytics** 
- Real-time KPI tracking (Leads, Clients, Conversions)
- Revenue forecasting and commission tracking
- Funnel velocity analysis
- Team performance metrics
- Segment-wise revenue analysis

### 2. **Contact Management**
- Master contact database (Leads, Clients, Warm Network)
- Automatic deduplication with merge capabilities
- 10-priority workflow fields for complete contact history
- Tier-based segmentation (A/B/C priority)
- Flexible customer segments (HNI, NRI, Doctor, Salaried, Business, Channel)

### 3. **Sales Pipelines**
- Customizable multiple pipelines (Marketing, Pre-sales, Sales, Customer Success)
- Kanban board view with drag-and-drop
- Deal probability tracking
- Expected close date forecasting
- Pipeline velocity metrics

### 4. **Click-to-Call Center**
- One-click dialing from contact records
- Automatic call logging with duration
- Call recording & transcription (with AI voice model)
- Instant follow-up task creation after calls
- Call analytics and statistics

### 5. **Multi-Channel Communications**
- **Email**: Template-based outreach with tracking
- **WhatsApp API**: Direct customer engagement
- **SMS**: Bulk messaging capabilities
- **In-App Chat**: Team collaboration
- Message read receipts and delivery status

### 6. **Lead Management & Distribution**
- Auto-assign leads based on location/criteria
- Team leader lead assignment controls
- Lead scoring and prioritization
- Round-robin distribution algorithm
- Capacity-based allocation

### 7. **Task & Activity Management**
- Auto-generated follow-up tasks from calls
- Calendar integration
- Task reminders and notifications
- Priority levels (High/Medium/Low)
- Task assignment to team members

### 8. **Import/Export Functionality**
- **Import**: CSV/Excel bulk lead import with deduplication
- **Export**: Data export to PDF, Excel, CSV
- Import validation and error reporting
- Automatic duplicate detection
- Import history and audit trail

### 9. **Document Management (DigiLocker)**
- Secure document upload and storage
- Policy number tracking
- Document expiry alerts
- Verification workflows
- Audit trail for document access

### 10. **Marketing Blogs**
- In-app blog/content section
- Published and draft status
- SEO optimization
- Content sharing to WhatsApp/Email
- View and engagement tracking

### 11. **Reports & Business Intelligence**
- Funnel analysis by contact type/owner
- Revenue reports by segment/tier
- User performance reports
- Deal forecast reports
- Custom report builder (admin only)
- Scheduled report generation

### 12. **Admin Controls**
- Full employee data & activity tracking
- Role-based access control (RBAC)
- User management and permissions
- System configuration
- Audit logs and compliance tracking

### 13. **Mobile CRM**
- Responsive web design (works on all devices)
- Mobile-optimized UI
- Offline support (PWA ready)
- Touch-friendly interface

## Technology Stack

### Backend
- **Runtime**: Node.js (ES6+)
- **Framework**: Express.js
- **Database**: PostgreSQL
- **Authentication**: JWT
- **APIs**: RESTful

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Charts**: Recharts
- **Animations**: Framer Motion
- **Icons**: Lucide React

### Infrastructure
- **Database**: PostgreSQL with indexed queries
- **Caching**: Ready for Redis integration
- **File Storage**: S3-compatible storage ready
- **API Documentation**: Swagger/OpenAPI ready

## Database Schema

### Core Tables
- **contacts** - Master contact database with dedup tracking
- **users** - Team members and roles
- **pipelines** - Sales pipeline configurations
- **pipeline_stages** - Individual pipeline stages
- **deals** - Opportunities/deals in pipeline
- **communications** - Email, SMS, WhatsApp history
- **tasks** - Activities and follow-ups
- **call_logs** - Call center integration
- **meetings** - Meeting records and outcomes
- **documents** - DigiLocker files
- **email_templates** - Pre-defined email templates
- **whatsapp_templates** - WhatsApp message templates
- **reports** - Saved reports
- **activity_logs** - Audit trail
- **import_logs** - Import history

### Views
- `v_active_contacts_summary` - Quick contact stats
- `v_funnel_analysis` - Funnel velocity metrics
- `v_revenue_forecast` - Revenue potential by segment

## Installation & Setup

### Prerequisites
- Node.js 18+ and npm/yarn
- PostgreSQL 12+
- Git

### 1. Clone Repository
```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\FinTech-CRM
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your configuration:
```
DATABASE_URL=postgresql://user:password@localhost:5432/arthainvest_crm
JWT_SECRET=your-secure-secret-key
NEXT_PUBLIC_API_URL=http://localhost:3000/api
PORT=3000
```

### 4. Database Setup
```bash
# Create database
createdb arthainvest_crm

# Run migrations
npm run db:migrate

# Seed sample data (optional)
npm run db:seed
```

### 5. Start Development Servers
```bash
# Run both frontend and backend
npm run dev

# Or separately:
npm run server:dev      # Terminal 1 - Backend on port 3000
npm run client:dev      # Terminal 2 - Frontend on port 3001
```

### 6. Access Application
- Frontend: http://localhost:3001
- API: http://localhost:3000/api
- Health Check: http://localhost:3000/health

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/verify` - Verify token
- `GET /api/auth/me` - Get current user

### Contacts
- `GET /api/contacts` - List contacts with filters
- `POST /api/contacts` - Create contact
- `GET /api/contacts/:id` - Get contact details
- `PUT /api/contacts/:id` - Update contact
- `DELETE /api/contacts/:id` - Delete contact (soft)
- `GET /api/contacts/:id/activity` - Contact activity history
- `GET /api/contacts/stats/summary` - Contact statistics

### Deals
- `GET /api/deals` - List deals
- `POST /api/deals` - Create deal
- `PUT /api/deals/:id` - Update deal
- `PUT /api/deals/:id/move-stage` - Move deal between stages

### Pipelines
- `GET /api/pipelines` - List all pipelines
- `GET /api/pipelines/:id` - Get pipeline with stages
- `POST /api/pipelines/:id/stages` - Create stage
- `GET /api/pipelines/:id/funnel` - Pipeline funnel data

### Communications
- `POST /api/communications` - Log communication
- `GET /api/communications` - Get communications history
- `GET /api/communications/templates/email` - Email templates
- `GET /api/communications/templates/whatsapp` - WhatsApp templates

### Tasks
- `GET /api/tasks` - List tasks
- `POST /api/tasks` - Create task
- `PUT /api/tasks/:id` - Update task
- `PUT /api/tasks/:id/complete` - Complete task

### Calls
- `POST /api/calls` - Log call
- `POST /api/calls/initiate` - Click-to-call
- `GET /api/calls` - Call history
- `GET /api/calls/stats/:userId` - Call statistics

### Reports & Analytics
- `GET /api/analytics/dashboard` - Dashboard KPIs
- `GET /api/analytics/top-performers` - Top performing users
- `GET /api/reports/funnel` - Funnel analysis
- `GET /api/reports/revenue` - Revenue reports
- `GET /api/reports/forecast` - Deal forecasts

### Import/Export
- `POST /api/import-export/contacts/import` - Bulk import
- `POST /api/import-export/contacts/export` - Bulk export
- `GET /api/import-export/import-logs` - Import history

## Features Breakdown by User Role

### Sales Representative
- ✅ View assigned contacts and leads
- ✅ Click-to-call and auto-logging
- ✅ Send emails/WhatsApp via templates
- ✅ Create and update deals
- ✅ Create follow-up tasks
- ✅ View personal performance metrics
- ✅ Manage own documents (DigiLocker)

### Team Leader
- ✅ All Sales Rep features
- ✅ View team member activities
- ✅ Assign leads to team members
- ✅ View team performance reports
- ✅ Monitor pipeline velocity
- ✅ Approve/reject document verification

### Admin
- ✅ All features
- ✅ User management and roles
- ✅ System configuration
- ✅ Import/Export bulk data
- ✅ Access all reports and analytics
- ✅ Audit logs and compliance
- ✅ Create email/WhatsApp templates

## Deployment

### Docker Deployment
```bash
# Build image
docker build -t arthainvest-crm .

# Run container
docker run -p 3000:3000 -e DATABASE_URL=... arthainvest-crm
```

### Vercel/Netlify (Frontend)
```bash
npm run build
# Deploy `out` directory
```

### Railway/Render (Backend)
```bash
# Set environment variables and deploy
# Database will be hosted on Railway/Render/neon
```

## Configuration

### Twilio Integration (Call Center)
```env
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
```

### WhatsApp Business API
```env
WHATSAPP_API_KEY=your-key
WHATSAPP_PHONE_NUMBER=+1234567890
```

### Email Service (SMTP)
```env
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Payment Integration (Razorpay)
```env
RAZORPAY_KEY_ID=your-key
RAZORPAY_KEY_SECRET=your-secret
```

## Performance Optimization

### Database Indexes
All critical search fields are indexed:
- `contacts(mobile)` - For dedup
- `contacts(email)` - For dedup
- `contacts(owner)` - For user filtering
- `contacts(status)` - For funnel
- `deals(pipeline_id, stage_id)` - For board view

### Query Optimization
- Pagination with limit/offset
- Lazy loading for related data
- Database views for common aggregations
- Query result caching ready

### Frontend Optimization
- Image lazy loading
- Code splitting with Next.js
- CSS-in-JS for dynamic styles
- SVG icons for performance

## Security Features

- ✅ JWT token-based authentication
- ✅ Password hashing (bcryptjs)
- ✅ Role-based access control (RBAC)
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection
- ✅ CORS configuration
- ✅ Audit trail for all changes
- ✅ Secure document storage

## Testing

```bash
# Run tests
npm run test

# Run linting
npm run lint
```

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Commit changes: `git commit -m 'Add amazing feature'`
3. Push to branch: `git push origin feature/amazing-feature`
4. Open Pull Request

## Support & Documentation

- **API Docs**: Available at `/api-docs` (Swagger)
- **User Guide**: See `/docs` folder
- **Issues**: Report bugs on GitHub Issues
- **Email**: support@arthainvest.com

## License

MIT License - See LICENSE file for details

## Version

**Current**: 1.0.0 (Production Ready)

---

**Built with ❤️ for ArthaInvest | Production-Grade Fintech CRM**

Combined Kylas.io design philosophy with financial services expertise and modern development practices.
