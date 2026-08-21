# 🚀 Quick Start - Backend Setup (5 Minutes)

**You have everything you need! Let's get started.**

---

## ✅ Step 1: Check Python is Installed

Open PowerShell and run:

```bash
python --version
```

**You should see:** `Python 3.9.x` or higher

If not installed: Download from https://www.python.org/ (check "Add Python to PATH")

---

## ✅ Step 2: Create Virtual Environment

```bash
# Navigate to backend folder
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see (venv) at the start of your terminal
```

---

## ✅ Step 3: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# This will take 1-2 minutes...
# Wait until you see: Successfully installed...
```

---

## ✅ Step 4: Setup Local PostgreSQL (for testing)

**Option A: If you have PostgreSQL installed locally**

```bash
# Create database
psql -U postgres

# In postgres prompt, type:
CREATE DATABASE arthainvest_crm;
\q
```

**Option B: If you don't have PostgreSQL**
- Download from https://www.postgresql.org/download/windows/
- Install with default settings
- During setup, remember the password for "postgres" user
- Update .env file with password

---

## ✅ Step 5: Start Your Backend!

**Option A: Double-click the batch file**

Simply double-click: `backend/START_BACKEND.bat`

**Option B: Manual start**

```bash
# Make sure you're in backend folder and venv is activated
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend
venv\Scripts\activate

# Start the server
python main.py
```

You should see:
```
✓ Database ready!
Uvicorn running on http://127.0.0.1:8000
```

---

## ✅ Step 6: Test Your API

**Open browser and go to:**

```
http://localhost:8000/docs
```

You'll see a beautiful interactive API documentation page!

### Quick Test:

1. **Health Check** (first endpoint)
   - Click "GET /api/health"
   - Click "Try it out"
   - Click "Execute"
   - Should return: `{"status": "ok"}`

2. **Register a User**
   - Click "POST /api/auth/register"
   - Click "Try it out"
   - Fill in test data:
     ```json
     {
       "username": "testuser",
       "email": "test@example.com",
       "password": "TestPassword123",
       "full_name": "Test User",
       "role": "admin"
     }
     ```
   - Click "Execute"
   - Should return the user data

3. **Login**
   - Click "POST /api/auth/login"
   - Click "Try it out"
   - Fill in:
     ```json
     {
       "username": "testuser",
       "password": "TestPassword123"
     }
     ```
   - Click "Execute"
   - Copy the `access_token` from response

4. **Create a Lead**
   - Click "POST /api/leads"
   - In the "token" field (at top right), paste your token
   - Fill in lead data:
     ```json
     {
       "name": "John Doe",
       "company": "Tech Corp",
       "email": "john@techcorp.com",
       "phone": "9876543210",
       "product": "Health Insurance",
       "source": "Referral"
     }
     ```
   - Click "Execute"
   - Should return the created lead

5. **Get All Leads**
   - Click "GET /api/leads"
   - Paste token in the token field
   - Click "Execute"
   - Should return your leads

---

## 🎯 All Available Endpoints

Your backend now has these endpoints ready:

**Authentication:**
- `POST /api/auth/login` - Login user
- `POST /api/auth/register` - Register new user

**Leads:**
- `GET /api/leads` - Get all leads
- `POST /api/leads` - Create new lead
- `GET /api/leads/{id}` - Get single lead
- `PUT /api/leads/{id}` - Update lead
- `DELETE /api/leads/{id}` - Delete lead

**Deals (Pipeline):**
- `GET /api/deals` - Get all deals
- `POST /api/deals` - Create new deal
- `PUT /api/deals/{id}/move` - Move deal to different stage (Kanban)

**Analytics:**
- `GET /api/analytics/dashboard` - Get KPI data
- `GET /api/analytics/conversion-rate` - Get conversion metrics

---

## 🔧 Troubleshooting

### "python: command not found"
- Python not installed or not in PATH
- Reinstall Python and check "Add Python to PATH"

### "ModuleNotFoundError: No module named 'fastapi'"
- Virtual environment not activated
- Run: `venv\Scripts\activate`

### "Connection refused" to database
- PostgreSQL not running
- Start PostgreSQL service or install it

### "Port 8000 already in use"
- Another process using port 8000
- Either close it or change port in main.py last line:
  ```python
  uvicorn.run(app, host="0.0.0.0", port=8001)
  ```

---

## 📝 .env File (Current Settings)

Your `.env` file is set for local PostgreSQL:
```
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=arthainvest_crm
DB_PORT=5432
```

**When moving to Hostinger**, update with Hostinger credentials!

---

## 🎓 What You Just Built

✅ Complete REST API with:
- User authentication (login/register)
- Lead management (CRUD operations)
- Deal/Pipeline management (Kanban support)
- Analytics endpoints
- Automatic database schema setup
- CORS enabled for frontend

**Total lines of code: ~600**

---

## 🚀 Next Steps

1. **Test all endpoints** - Make sure everything works
2. **Data migration** - When ready, migrate your SQLite data to PostgreSQL
3. **Build Frontend** - Next step is React.js frontend
4. **Deploy to Hostinger** - Week 5-6

---

## 💡 Pro Tips

1. **Keep this terminal open** - Your backend runs here
2. **Open another PowerShell** - For building frontend later
3. **Docs auto-update** - Change code, reload browser at localhost:8000/docs
4. **Token expires in 30 mins** - Re-login if testing takes long

---

**Your backend is ready! 🎉**

Any errors? Check troubleshooting above or let me know.

Next: Frontend setup is similar - I'll guide you through React when you're ready.
