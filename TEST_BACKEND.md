# 🧪 Backend Testing Guide

**Test your backend API without PostgreSQL (using SQLite)**

---

## 🚀 Step 1: Start the Backend

### Option A: Double-Click (Easiest)
Navigate to `backend` folder and **double-click:**
```
START_BACKEND_SQLITE.bat
```

### Option B: Manual Start
```bash
# Go to backend folder
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\backend

# Activate environment
venv\Scripts\activate

# Start with SQLite
python main_sqlite.py
```

**You should see:**
```
✓ SQLite database initialized successfully!
Uvicorn running on http://127.0.0.1:8000
```

---

## 🌐 Step 2: Open Interactive API Docs

**Go to:** http://localhost:8000/docs

You'll see Swagger UI with all your endpoints listed!

---

## ✅ Step 3: Test Each Endpoint

### Test 1: Health Check (Should work immediately)

1. Click **GET /api/health**
2. Click **"Try it out"**
3. Click **"Execute"**

**Expected Response:**
```json
{
  "status": "ok",
  "message": "ArthaInvest API is running"
}
```

✅ **If you see this, your backend is working!**

---

### Test 2: Register a User

1. Click **POST /api/auth/register**
2. Click **"Try it out"**
3. Fill in the request body with test data:

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "TestPassword123",
  "full_name": "Test User",
  "role": "admin"
}
```

4. Click **"Execute"**

**Expected Response:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "full_name": "Test User",
  "role": "admin",
  "is_active": true
}
```

✅ **User created successfully!**

---

### Test 3: Login

1. Click **POST /api/auth/login**
2. Click **"Try it out"**
3. Fill in:

```json
{
  "username": "testuser",
  "password": "TestPassword123"
}
```

4. Click **"Execute"**

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "testuser",
  "role": "admin"
}
```

✅ **Got token! Copy this token for next tests.**

---

### Test 4: Create a Lead

1. Click **POST /api/leads**
2. Click **"Try it out"**
3. **IMPORTANT:** Scroll to top of the dialog and find **"token"** field
4. Paste your token there (from Test 3)
5. Fill in request body:

```json
{
  "name": "John Doe",
  "company": "Tech Solutions Inc",
  "email": "john@techsolutions.com",
  "phone": "9876543210",
  "product": "Health Insurance",
  "source": "Referral"
}
```

6. Click **"Execute"**

**Expected Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "company": "Tech Solutions Inc",
  "email": "john@techsolutions.com",
  "phone": "9876543210",
  "product": "Health Insurance",
  "ai_score": null,
  "lead_tier": null,
  "status": "new",
  "source": "Referral",
  "created_at": "2026-08-20T...",
  "updated_at": "2026-08-20T..."
}
```

✅ **Lead created!**

---

### Test 5: Create Another Lead (for testing)

Do the same as Test 4, but with different data:

```json
{
  "name": "Sarah Smith",
  "company": "Global Enterprises",
  "email": "sarah@global.com",
  "phone": "9123456789",
  "product": "Life Insurance",
  "source": "LinkedIn"
}
```

---

### Test 6: Get All Leads

1. Click **GET /api/leads**
2. Click **"Try it out"**
3. Paste your token in "token" field
4. Click **"Execute"**

**Expected Response:**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    ...
  },
  {
    "id": 2,
    "name": "Sarah Smith",
    ...
  }
]
```

✅ **Both leads returned!**

---

### Test 7: Update a Lead

1. Click **PUT /api/leads/{lead_id}**
2. Click **"Try it out"**
3. Enter `lead_id`: **1**
4. Paste token
5. Fill request body:

```json
{
  "status": "qualified",
  "ai_score": 85,
  "lead_tier": "HOT"
}
```

6. Click **"Execute"**

**Expected Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "status": "qualified",
  "ai_score": 85,
  "lead_tier": "HOT",
  ...
}
```

✅ **Lead updated!**

---

### Test 8: Create a Deal

1. Click **POST /api/deals**
2. Click **"Try it out"**
3. Paste token
4. Fill request body:

```json
{
  "lead_id": 1,
  "deal_value": 50000,
  "probability": 0.75
}
```

5. Click **"Execute"**

**Expected Response:**
```json
{
  "id": 1,
  "lead_id": 1,
  "deal_value": 50000,
  "stage": "new",
  "probability": 0.75,
  "expected_close_date": null,
  "created_at": "2026-08-20T..."
}
```

✅ **Deal created!**

---

### Test 9: Move Deal to Different Stage (Kanban)

1. Click **PUT /api/deals/{deal_id}/move**
2. Click **"Try it out"**
3. Enter `deal_id`: **1**
4. Paste token
5. Fill request body:

```json
{
  "stage": "qualified"
}
```

6. Click **"Execute"**

**Expected Response:**
```json
{
  "id": 1,
  "stage": "qualified",  ← Changed!
  ...
}
```

✅ **Deal moved!**

Try moving to other stages: `proposal`, `negotiation`, `closed`

---

### Test 10: Get All Deals

1. Click **GET /api/deals**
2. Click **"Try it out"**
3. Paste token
4. Click **"Execute"**

**Expected Response:**
```json
[
  {
    "id": 1,
    "lead_id": 1,
    "deal_value": 50000,
    "stage": "qualified",
    ...
  }
]
```

✅ **All deals returned!**

---

### Test 11: Dashboard Analytics

1. Click **GET /api/analytics/dashboard**
2. Click **"Try it out"**
3. Paste token
4. Click **"Execute"**

**Expected Response:**
```json
{
  "total_leads": 2,
  "qualified_leads": 1,
  "active_deals": 1,
  "closed_deals": 0
}
```

✅ **Analytics working!**

---

### Test 12: Conversion Rate

1. Click **GET /api/analytics/conversion-rate**
2. Click **"Try it out"**
3. Paste token
4. Click **"Execute"**

**Expected Response:**
```json
{
  "total_leads": 2,
  "total_deals": 1,
  "conversion_rate": 50.0
}
```

✅ **Conversion rate calculated!**

---

### Test 13: Delete a Lead

1. Click **DELETE /api/leads/{lead_id}**
2. Click **"Try it out"**
3. Enter `lead_id`: **2**
4. Paste token
5. Click **"Execute"**

**Expected Response:**
```json
{
  "message": "Lead deleted"
}
```

✅ **Lead deleted!**

---

## 📊 Test Summary

| Endpoint | Status | Notes |
|----------|--------|-------|
| Health Check | ✅ | Should always work |
| Register User | ✅ | Creates new user |
| Login | ✅ | Returns token |
| Create Lead | ✅ | Add test data |
| Get Leads | ✅ | Lists all leads |
| Update Lead | ✅ | Changes status/tier |
| Delete Lead | ✅ | Removes lead |
| Create Deal | ✅ | Links to lead |
| Move Deal | ✅ | Changes stage |
| Get Deals | ✅ | Lists all deals |
| Dashboard Analytics | ✅ | KPI data |
| Conversion Rate | ✅ | Lead to deal % |

---

## 🎉 All Tests Passed?

**Congratulations!** Your backend is fully functional! ✅

---

## 🆘 Troubleshooting

### Error: "Connection refused"
- Make sure backend is still running in terminal
- Don't close the terminal window

### Error: "Invalid token"
- Token may have expired (30 min limit)
- Login again and get new token
- Copy entire token without quotes

### Error: "Lead not found"
- Make sure lead_id exists
- Try getting all leads first to see IDs

### Error: "Module not found"
- Virtual environment not activated
- Run: `venv\Scripts\activate`

---

## 🚀 Next Steps

1. **✅ Backend tested and working!**
2. **Now build the React frontend** (next guide)
3. **Connect frontend to backend**
4. **Deploy to Hostinger**

---

**Questions? Let me know! Backend is ready for frontend integration.** 🎯

