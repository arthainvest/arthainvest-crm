# ArthaInvest Fintech CRM - Quick Start Guide

Get the CRM running in 5 minutes!

## ⚡ One-Liner Setup

```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\FinTech-CRM && npm install && cp .env.example .env && npm run dev
```

## 🚀 Step-by-Step (Recommended)

### 1. Prerequisites Check
```bash
node --version        # Should be v18+
npm --version         # Should be v8+
psql --version        # Should be v12+
```

If you don't have PostgreSQL, install it:
- **Windows**: https://www.postgresql.org/download/windows/
- **Mac**: `brew install postgresql@15`
- **Linux**: `sudo apt-get install postgresql`

### 2. Clone & Install
```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\FinTech-CRM
npm install
```

### 3. Configure Database
```bash
# Create database
createdb arthainvest_crm

# OR use psql
psql -U postgres
# \create DATABASE arthainvest_crm;
# \c arthainvest_crm;
```

### 4. Setup Environment
```bash
cp .env.example .env
```

Edit `.env` with your settings. Minimum required:
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/arthainvest_crm
JWT_SECRET=your-secret-key-123456
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

### 5. Database Migrations
```bash
npm run db:migrate
```

This creates all 15 tables automatically.

### 6. Start Development Servers
```bash
npm run dev
```

You'll see:
```
✓ Frontend running on http://localhost:3001
✓ Backend running on http://localhost:3000
✓ Database connected
```

### 7. Access Application
Open your browser to: **http://localhost:3001**

## 🔐 Default Login Credentials

```
Email: demo@arthainvest.com
Password: demo123
```

*These are created during initial migration*

## 📊 First Steps in the App

1. **Dashboard** - View KPIs and team performance
2. **Create Contact** - Add your first lead
3. **Create Pipeline** - Set up sales stages
4. **Create Deal** - Add opportunity to pipeline
5. **Make Call** - Click-to-call feature
6. **View Reports** - Check funnel and revenue

## 🛠️ Common Commands

```bash
# Start development
npm run dev

# Start just backend
npm run server:dev

# Start just frontend
npm run client:dev

# Build for production
npm run build

# Run database migrations
npm run db:migrate

# Seed sample data
npm run db:seed

# Run tests
npm run test

# Run linter
npm run lint
```

## 🔧 Troubleshooting

### "Cannot find module 'pg'"
```bash
npm install
```

### "Database connection error"
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check .env DATABASE_URL
cat .env | grep DATABASE_URL
```

### "Port 3000 already in use"
```bash
# Use different port
PORT=3002 npm run server:dev
```

### "Port 3001 already in use"
```bash
# Use different port
npm run client:dev -- -p 3002
```

## 📚 Next Steps

After getting it running:

1. **Read Documentation**
   - API docs: See `README.md`
   - Database: See `server/migrations/schema.sql`
   - Project structure: See `PROJECT_STRUCTURE.md`

2. **Configure Integrations**
   - Email (SMTP): Update `.env`
   - Twilio (Calls): Get API key, add to `.env`
   - WhatsApp: Configure API, add to `.env`

3. **Customize**
   - Add your logo in `public/images/logo.svg`
   - Update colors in `tailwind.config.ts`
   - Modify database schema in `server/migrations/schema.sql`

4. **Deploy**
   - Read `DEPLOYMENT_GUIDE.md`
   - Choose platform (Docker, Railway, Render, etc.)
   - Deploy both frontend and backend

## 💡 Pro Tips

### Hot Reload
Both frontend and backend auto-reload on file changes. No restart needed!

### Database Queries
```bash
# Connect directly to database
psql arthainvest_crm

# List tables
\dt

# View table structure
\d contacts

# Run raw SQL
SELECT * FROM contacts LIMIT 5;
```

### API Testing
Use Thunder Client or Postman:
- Base URL: `http://localhost:3000/api`
- Get list of contacts: `GET /api/contacts`
- Create contact: `POST /api/contacts`

### Check Logs
```bash
# Backend logs (in terminal running npm run server:dev)
# Frontend logs (in terminal running npm run client:dev)
# Browser console (F12 in browser)
```

## 🎯 Feature Checklist

After setup, you can use:

- ✅ Dashboard with live KPIs
- ✅ Contact management with dedup
- ✅ Pipeline & deal management
- ✅ Call logging
- ✅ Email & WhatsApp templates
- ✅ Task management
- ✅ Reports & analytics
- ✅ Import/Export
- ✅ Admin controls

## 🆘 Need Help?

### Check Status
```bash
curl http://localhost:3000/health
```

### View API Docs
Coming soon - Swagger docs at `/api-docs`

### Test Database
```bash
npm run test
```

### Read Source Code
- Frontend logic: `app/dashboard/page.tsx`
- Backend logic: `server/routes/contacts.js`
- Database: `server/migrations/schema.sql`

## 🚀 Ready for Production?

1. Follow `DEPLOYMENT_GUIDE.md`
2. Set up database backups
3. Configure SSL/HTTPS
4. Enable 2FA for admin users
5. Configure email service
6. Test all integrations

---

**That's it! You're ready to use ArthaInvest Fintech CRM!**

For detailed guides, see the main `README.md` or `DEPLOYMENT_GUIDE.md`.

**Happy selling! 📈**
