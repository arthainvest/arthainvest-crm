# 🎯 ArthaInvest Enterprise CRM - API Documentation

## Complete API Reference for 50+ Endpoints

---

## 📋 Table of Contents

1. [Base URL & Authentication](#-base-url--authentication)
2. [Authentication Endpoints](#-authentication-endpoints)
3. [User Endpoints](#-user-endpoints)
4. [Lead Endpoints](#-lead-endpoints)
5. [Call Endpoints](#-call-endpoints)
6. [Deal Endpoints](#-deal-endpoints)
7. [Invoice Endpoints](#-invoice-endpoints)
8. [Document Endpoints](#-document-endpoints)
9. [Marketing Endpoints](#-marketing-endpoints)
10. [Error Handling](#-error-handling)

---

## 🌐 Base URL & Authentication

### Base URL
```
http://localhost:3000
```

### Headers Required
```
Content-Type: application/json
Authorization: Bearer {JWT_TOKEN}
```

### JWT Token
Obtained after login. Valid for the session duration.

---

## 🔐 Authentication Endpoints

### POST /login
Login to the CRM

**Request:**
```json
{
  "email": "admin@arthainvest.com",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "admin@arthainvest.com",
    "name": "Administrator",
    "role": "admin"
  }
}
```

**Error (401):**
```json
{
  "error": "Invalid credentials"
}
```

---

### POST /register
Register new user (Admin only)

**Request:**
```json
{
  "email": "newuser@arthainvest.com",
  "password": "SecurePass123",
  "name": "New User",
  "role": "employee",
  "department": "Sales"
}
```

**Response (201):**
```json
{
  "message": "User created successfully",
  "user_id": 2
}
```

---

### POST /logout
Logout from the CRM

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 👥 User Endpoints

### GET /api/users
Get all users (Admin only)

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "email": "admin@arthainvest.com",
      "name": "Administrator",
      "role": "admin",
      "status": "active"
    }
  ]
}
```

---

### GET /api/users/:id
Get specific user details

**Response (200):**
```json
{
  "id": 1,
  "email": "admin@arthainvest.com",
  "name": "Administrator",
  "role": "admin",
  "department": "Management",
  "status": "active",
  "online_status": "online",
  "last_login": "2026-08-13T13:00:00Z"
}
```

---

### PUT /api/users/:id
Update user profile

**Request:**
```json
{
  "name": "Updated Name",
  "phone": "+91-9876543210"
}
```

**Response (200):**
```json
{
  "message": "User updated successfully"
}
```

---

## 📝 Lead Endpoints

### GET /api/leads
Get all leads

**Query Parameters:**
- `status`: Filter by status (new, qualified, negotiating, won, lost)
- `assigned_to`: Filter by assigned user ID
- `limit`: Number of records (default: 20)
- `offset`: Pagination offset (default: 0)

**Response (200):**
```json
{
  "leads": [
    {
      "id": 1,
      "lead_name": "Rajesh Kumar",
      "email": "rajesh@example.com",
      "phone": "+91-9876543210",
      "company": "Tech Innovations Ltd",
      "status": "qualified",
      "lead_score": 85,
      "assigned_to": 2,
      "created_at": "2026-08-01T10:00:00Z"
    }
  ],
  "total": 156,
  "limit": 20,
  "offset": 0
}
```

---

### POST /api/leads
Create new lead

**Request:**
```json
{
  "lead_name": "John Doe",
  "email": "john@example.com",
  "phone": "+91-9876543210",
  "company": "Acme Corporation",
  "designation": "Manager",
  "product_interest": "SIP Investment",
  "budget_range": "500000-1000000"
}
```

**Response (201):**
```json
{
  "message": "Lead created successfully",
  "lead_id": 2
}
```

---

### PUT /api/leads/:id
Update lead

**Request:**
```json
{
  "status": "negotiating",
  "lead_score": 90,
  "next_followup": "2026-08-20T14:00:00Z"
}
```

**Response (200):**
```json
{
  "message": "Lead updated successfully"
}
```

---

### DELETE /api/leads/:id
Delete lead (Admin only)

**Response (200):**
```json
{
  "message": "Lead deleted successfully"
}
```

---

## ☎️ Call Endpoints

### GET /api/calls
Get all calls

**Query Parameters:**
- `lead_id`: Filter by lead
- `user_id`: Filter by user
- `limit`: Number of records
- `offset`: Pagination offset

**Response (200):**
```json
{
  "calls": [
    {
      "id": 1,
      "lead_id": 1,
      "user_id": 2,
      "call_duration": 1200,
      "call_result": "successful",
      "call_notes": "Client interested in SIP plans",
      "call_recording_path": "/recordings/call_001.wav",
      "transcription": "Full call transcription text...",
      "ai_summary": "AI-generated summary of the call",
      "created_at": "2026-08-13T10:30:00Z"
    }
  ],
  "total": 1250
}
```

---

### POST /api/calls
Log new call

**Request:**
```json
{
  "lead_id": 1,
  "call_duration": 1200,
  "call_result": "successful",
  "call_notes": "Discussed product features",
  "call_type": "outbound"
}
```

**Response (201):**
```json
{
  "message": "Call logged successfully",
  "call_id": 1251
}
```

---

## 💰 Invoice Endpoints

### GET /api/invoices
Get all invoices

**Response (200):**
```json
{
  "invoices": [
    {
      "id": 1,
      "lead_id": 1,
      "amount": 50000,
      "commission": 7500,
      "status": "paid",
      "due_date": "2026-09-13",
      "created_at": "2026-08-13T10:00:00Z"
    }
  ]
}
```

---

### POST /api/invoices
Create invoice

**Request:**
```json
{
  "lead_id": 1,
  "amount": 50000,
  "commission_rate": 15,
  "product": "SIP Investment",
  "due_date": "2026-09-13"
}
```

**Response (201):**
```json
{
  "message": "Invoice created successfully",
  "invoice_id": 1,
  "commission": 7500
}
```

---

## 📦 Document Endpoints

### GET /api/documents
Get all documents

**Response (200):**
```json
{
  "documents": [
    {
      "id": 1,
      "lead_id": 1,
      "document_name": "KYC Document",
      "file_type": "pdf",
      "file_size": 102400,
      "upload_date": "2026-08-13T10:00:00Z",
      "status": "verified"
    }
  ]
}
```

---

### POST /api/documents/upload
Upload document

**Request (multipart/form-data):**
```
lead_id: 1
document_name: "KYC Document"
file: [binary file content]
```

**Response (201):**
```json
{
  "message": "Document uploaded successfully",
  "document_id": 1,
  "file_path": "/documents/doc_001.pdf"
}
```

---

## 🎨 Marketing Endpoints

### GET /api/marketing/campaigns
Get all marketing campaigns

**Response (200):**
```json
{
  "campaigns": [
    {
      "id": 1,
      "campaign_name": "Summer Sale 2026",
      "status": "active",
      "start_date": "2026-08-01",
      "end_date": "2026-08-31",
      "leads_count": 150,
      "conversions": 45
    }
  ]
}
```

---

### POST /api/marketing/campaigns
Create campaign

**Request:**
```json
{
  "campaign_name": "Fall Campaign 2026",
  "description": "Seasonal promotion",
  "start_date": "2026-09-01",
  "end_date": "2026-09-30",
  "target_audience": "All leads"
}
```

**Response (201):**
```json
{
  "message": "Campaign created successfully",
  "campaign_id": 2
}
```

---

## 📊 Analytics Endpoints

### GET /api/analytics/dashboard
Get dashboard statistics

**Response (200):**
```json
{
  "total_leads": 156,
  "active_leads": 142,
  "total_deals": 42,
  "total_commission": 125000,
  "this_month_calls": 245,
  "conversion_rate": 28.5,
  "team_performance": {
    "rajesh": {
      "leads": 35,
      "deals": 8,
      "commission": 30000
    }
  }
}
```

---

### GET /api/analytics/reports
Get detailed reports

**Query Parameters:**
- `report_type`: leads, calls, commissions, performance
- `start_date`: From date (YYYY-MM-DD)
- `end_date`: To date (YYYY-MM-DD)
- `user_id`: Filter by user (optional)

**Response (200):**
```json
{
  "report_type": "commissions",
  "period": "2026-08-01 to 2026-08-13",
  "data": [
    {
      "user_name": "Rajesh Kumar",
      "total_commission": 15000,
      "deal_count": 4,
      "commission_rate": 15
    }
  ]
}
```

---

## ❌ Error Handling

### Standard Error Response

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| INVALID_CREDENTIALS | 401 | Login failed |
| UNAUTHORIZED | 403 | Access denied |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid request data |
| INTERNAL_ERROR | 500 | Server error |
| RATE_LIMIT | 429 | Too many requests |

---

## 📝 Request/Response Examples

### Example 1: Login and Get Leads

```bash
# Step 1: Login
curl -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@arthainvest.com",
    "password": "admin123"
  }'

# Response:
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "admin@arthainvest.com",
    "role": "admin"
  }
}

# Step 2: Get Leads (using token)
curl -X GET http://localhost:3000/api/leads \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🔒 Security Best Practices

1. **Always use HTTPS in production** - Use SSL certificates
2. **Store tokens securely** - Never expose in logs or client-side
3. **Validate input** - All requests are validated server-side
4. **Rate limiting** - API enforces rate limits (100 requests/minute)
5. **CORS enabled** - Only trusted origins allowed
6. **Password hashing** - All passwords are hashed with bcryptjs

---

## 📞 API Support

For API issues:
1. Check this documentation
2. Review error messages
3. Check server logs
4. Contact: support@arthainvest.com

---

**API Version:** 1.0.0-enterprise
**Last Updated:** August 13, 2026
**Status:** Production Ready ✅
