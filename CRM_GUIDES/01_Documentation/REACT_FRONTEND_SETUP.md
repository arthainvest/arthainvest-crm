# ArthaInvest CRM - React Frontend Setup Guide

**Build a beautiful web interface for your backend API**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Create React App

```bash
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest
npx create-react-app frontend
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install axios react-router-dom react-beautiful-dnd chart.js react-chartjs-2
```

### Step 3: Copy Component Files

I've created all the components for you. Copy them to `frontend/src/`

### Step 4: Start Development Server

```bash
npm start
```

**Open browser:** http://localhost:3000

---

## 📁 Project Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Login.jsx          (Login page)
│   │   ├── Dashboard.jsx       (KPI cards & overview)
│   │   ├── LeadsList.jsx       (Leads management)
│   │   ├── KanbanBoard.jsx     (Drag-drop pipeline)
│   │   ├── Analytics.jsx       (Charts & metrics)
│   │   └── Navigation.jsx      (Sidebar menu)
│   ├── services/
│   │   └── api.js              (API calls to backend)
│   ├── App.jsx                 (Main app routing)
│   ├── App.css                 (Styling)
│   └── index.js                (Entry point)
├── package.json
└── .env                        (API configuration)
```

---

## 🔧 Configuration

### .env File

Create `frontend/.env`:

```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=ArthaInvest CRM
```

For production (Hostinger):
```
REACT_APP_API_URL=https://api.yourdomain.com
```

---

## 📱 Features Included

### 1. Login Page
- Username & password authentication
- JWT token management
- Automatic redirects

### 2. Dashboard
- 4 KPI cards (Total Leads, Qualified, Active Deals, Closed)
- Real-time metrics from backend
- Recent activity summary

### 3. Leads Management
- View all leads in table format
- Create new lead modal
- Edit lead information
- Update lead status & tier
- Delete leads
- Filter by status

### 4. Kanban Board (Pipeline)
- Visual pipeline with 5 stages
- Drag-and-drop deal cards
- Move deals between stages
- Real-time updates

### 5. Analytics
- Conversion rate chart
- Deal value analysis
- Lead source breakdown
- Performance metrics

### 6. Navigation
- Sidebar menu
- User profile info
- Logout functionality

---

## 🎨 Tech Stack

| Component | Technology |
|-----------|-----------|
| UI Framework | React 18 |
| Routing | React Router v6 |
| HTTP Client | Axios |
| Drag-Drop | react-beautiful-dnd |
| Charts | Chart.js + react-chartjs-2 |
| Styling | CSS3 + Flexbox |
| State Management | React Hooks |

---

## 📋 Component Details

### Login.jsx
- Email/password form
- Backend authentication
- JWT token storage (localStorage)
- Redirect to dashboard on success

### Dashboard.jsx
- KPI cards with real-time data
- Summary statistics
- Recent leads/deals
- Quick actions

### LeadsList.jsx
- Table with all leads
- Add new lead button
- Edit/delete actions
- Filter & search
- Pagination

### KanbanBoard.jsx
- 5 pipeline stages (New → Closed)
- Drag-drop cards
- Drop updates backend
- Real-time sync

### Analytics.jsx
- Conversion funnel
- Deal value chart
- Lead source pie chart
- Performance metrics

---

## 🔗 API Integration

All components connect to your backend:

```javascript
// Example API call from component
import { loginUser, getLeads, createLead } from '../services/api';

const handleLogin = async (username, password) => {
  const response = await loginUser(username, password);
  localStorage.setItem('token', response.access_token);
  // Redirect to dashboard
};

const handleGetLeads = async () => {
  const token = localStorage.getItem('token');
  const leads = await getLeads(token);
  setLeads(leads);
};
```

---

## 🚀 Development Workflow

### Terminal 1: Backend
```bash
cd backend
python main_sqlite.py
# Runs on http://localhost:8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm start
# Runs on http://localhost:3000
```

### Terminal 3: Testing (Optional)
```bash
npm test
```

---

## 📊 Testing the Frontend

### 1. Login
- Username: `testuser`
- Password: `TestPass123`

### 2. Create Leads
- Click "New Lead"
- Fill in details
- Submit

### 3. Try Kanban Board
- Click "Pipeline"
- Drag deal cards between stages
- Changes sync to backend

### 4. View Analytics
- Click "Analytics"
- See real-time charts

---

## 🛠️ Common Issues & Solutions

### Issue: "Cannot find module 'axios'"
```bash
npm install axios
```

### Issue: "API connection refused"
- Make sure backend is running
- Check API_URL in .env
- Check CORS settings in backend

### Issue: "Login not working"
- Verify backend is running
- Check token is being stored
- Open DevTools → Console for errors

### Issue: "Blank page after login"
- Clear localStorage: `localStorage.clear()`
- Check browser console for errors
- Verify routes in App.jsx

---

## 📦 Build for Production

```bash
npm run build

# Creates optimized build in 'build/' folder
# Deploy this folder to Hostinger
```

---

## 🎯 Next Steps

1. ✅ Install dependencies
2. ✅ Copy component files
3. ✅ Setup .env
4. ✅ Start development server
5. ✅ Test login
6. ✅ Test all features
7. ✅ Build for production
8. ✅ Deploy to Hostinger

---

**You now have a complete CRM system!**

- Backend: Running ✓
- Frontend: Ready to build
- Database: SQLite (testing) / PostgreSQL (production)
- Deployment: Ready for Hostinger

---

*Last Updated: August 20, 2026*
