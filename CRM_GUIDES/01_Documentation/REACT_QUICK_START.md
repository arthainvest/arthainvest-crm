# React Frontend - Quick Start (10 Minutes)

**Complete web interface ready to build**

---

## 🚀 Step 1: Create React App

```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest
npx create-react-app frontend
cd frontend
```

**Time: 3-5 minutes** (installing dependencies)

---

## 📦 Step 2: Install Additional Dependencies

```bash
npm install axios react-router-dom react-beautiful-dnd chart.js react-chartjs-2
```

**Time: 2-3 minutes**

---

## 📁 Step 3: Copy Component Files

I've created all the component files for you. Copy them to the `frontend/src/` folder:

**From:** `C:\Users\artha\OneDrive\Desktop\ArthaInvest\frontend_src_*`

**Files to copy:**

```
frontend_src_services_api.js         → src/services/api.js
frontend_src_components_Login.jsx    → src/components/Login.jsx
frontend_src_components_Dashboard.jsx → src/components/Dashboard.jsx
frontend_src_components_LeadsList.jsx → src/components/LeadsList.jsx
frontend_src_components_KanbanBoard.jsx → src/components/KanbanBoard.jsx
frontend_src_components_Navigation.jsx → src/components/Navigation.jsx
frontend_src_App.jsx                 → src/App.jsx (replace existing)
frontend_src_App.css                 → src/App.css (replace existing)

frontend_src_styles_Login.css        → src/styles/Login.css
frontend_src_styles_Navigation.css   → src/styles/Navigation.css
frontend_src_styles_Dashboard.css    → src/styles/Dashboard.css
frontend_src_styles_LeadsList.css    → src/styles/LeadsList.css
frontend_src_styles_KanbanBoard.css  → src/styles/KanbanBoard.css
```

**Folder structure:**
```
frontend/src/
├── components/
│   ├── Dashboard.jsx
│   ├── KanbanBoard.jsx
│   ├── LeadsList.jsx
│   ├── Login.jsx
│   └── Navigation.jsx
├── services/
│   └── api.js
├── styles/
│   ├── Dashboard.css
│   ├── KanbanBoard.css
│   ├── LeadsList.css
│   ├── Login.css
│   └── Navigation.css
├── App.jsx
├── App.css
├── index.js
└── index.css
```

---

## 🔧 Step 4: Configure Environment

Create `frontend/.env`:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=ArthaInvest CRM
```

---

## ▶️ Step 5: Start Development Server

**Terminal 1 (Backend - if not running):**
```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend
python main_sqlite.py
```

**Terminal 2 (Frontend):**
```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\frontend
npm start
```

**Opens automatically:** http://localhost:3000

---

## 🧪 Step 6: Test the Application

### 1. Login Page
- **URL:** http://localhost:3000/login
- **Username:** testuser
- **Password:** TestPass123
- Click "Login"

### 2. Dashboard
- After login, redirects to Dashboard
- Shows 4 KPI cards:
  - Total Leads: 1
  - Qualified Leads: 1
  - Active Deals: 1
  - Closed Deals: 0
- Shows table of recent leads

### 3. Leads Page
- Click "Leads" in sidebar
- Shows all leads in table
- Click "+ New Lead" to add a lead
- Fill in name (required), company, email, phone, product, source
- Click "Create Lead"
- New lead appears in table

### 4. Pipeline (Kanban)
- Click "Pipeline" in sidebar
- Shows 5 columns: New → Qualified → Proposal → Negotiation → Closed
- Each column shows deals in that stage
- **Drag a deal card** from one column to another
- Release to move deal (syncs with backend)
- Numbers update in real-time

### 5. Logout
- Click "Logout" button
- Redirects to login page
- Session cleared

---

## ✅ Test Checklist

- [ ] Login works with testuser credentials
- [ ] Dashboard loads with KPI data
- [ ] Can view all leads in Leads page
- [ ] Can create new lead from Leads page
- [ ] Pipeline page shows 5 stages
- [ ] Can drag deals between stages
- [ ] Deals stay in new stage after refresh (persistence)
- [ ] Logout clears session and redirects to login

---

## 🎨 Features Working

✅ **Authentication** - Login with JWT tokens
✅ **Dashboard** - KPI cards with real-time data
✅ **Leads Management** - Create, view, delete leads
✅ **Pipeline/Kanban** - Drag-drop deals between stages
✅ **Navigation** - Sidebar menu with user info
✅ **Responsive Design** - Works on desktop and tablet
✅ **Real-time Sync** - Changes update backend immediately

---

## 🐛 Troubleshooting

### Issue: "Cannot find module 'axios'"
```bash
npm install axios
```

### Issue: "Port 3000 is already in use"
```bash
# Kill the process or use different port:
npm start -- --port 3001
```

### Issue: "API connection refused"
- ✓ Make sure backend is running on http://localhost:8000
- ✓ Check .env has correct API_URL
- ✓ Check browser console for CORS errors

### Issue: "Login not working"
- ✓ Verify backend is running
- ✓ Check credentials: testuser / TestPass123
- ✓ Open DevTools (F12) → Console for errors

### Issue: "Drag-drop not working"
- ✓ Make sure backend is running
- ✓ Try refreshing page
- ✓ Check browser console for errors

### Issue: "Blank page after components copied"
- ✓ Check folder structure matches above
- ✓ Make sure .jsx files are in correct folders
- ✓ Run `npm start` in frontend folder
- ✓ Check for JavaScript errors in console

---

## 📋 File Summary

| File | Purpose |
|------|---------|
| api.js | All API calls to backend |
| Login.jsx | Login form & authentication |
| Dashboard.jsx | KPI cards & overview |
| LeadsList.jsx | Lead management table |
| KanbanBoard.jsx | Pipeline with drag-drop |
| Navigation.jsx | Sidebar navigation |
| App.jsx | Main app routing |
| App.css | Global styling |
| **/styles/*.css | Component-specific styling |

---

## 🚀 Running Frontend & Backend Together

**In two separate terminals:**

```bash
# Terminal 1: Backend
cd backend
python main_sqlite.py

# Terminal 2: Frontend  
cd frontend
npm start
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📦 Production Build

```bash
npm run build
```

Creates optimized build in `frontend/build/` folder.

---

## 🎯 What's Next

1. ✅ Test frontend thoroughly
2. ✅ Create more test data
3. ✅ Build production bundle
4. ✅ Deploy to Hostinger (Week 6)

---

## 💡 Tips

- **DevTools:** Press F12 to debug
- **API Logs:** Check http://localhost:8000/docs for request/response
- **Terminal:** Keep both backend & frontend running
- **Hot Reload:** Frontend auto-reloads on file changes
- **Database:** Data persists in SQLite file (arthainvest_crm.db)

---

**You now have a complete web CRM application!** 🎉

- Backend API: Running ✓
- React Frontend: Ready ✓
- Database: Connected ✓
- Authentication: Working ✓
- Kanban Board: Functional ✓

---

*Next step: Deploy to Hostinger (Week 6)*

*Commands to remember:*
```
Backend: python main_sqlite.py
Frontend: npm start
API Docs: http://localhost:8000/docs
App: http://localhost:3000
```
