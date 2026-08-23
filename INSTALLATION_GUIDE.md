# 🎯 ArthaInvest Enterprise CRM - Installation Guide

## Complete Setup Instructions for Your Team

---

## 📋 Table of Contents

1. [System Requirements](#-system-requirements)
2. [Installation Methods](#-installation-methods)
3. [Step-by-Step Setup](#-step-by-step-setup)
4. [Verification](#-verification)
5. [Troubleshooting](#-troubleshooting)
6. [First Login](#-first-login)

---

## ✅ System Requirements

### Minimum Requirements
- **OS:** Windows 7+, macOS 10.12+, or Linux
- **Node.js:** v16 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Disk Space:** 500MB free
- **Browser:** Chrome, Firefox, Safari, or Edge (latest versions)

### Installation Check
```bash
# Verify Node.js installation
node --version    # Should be v16+
npm --version     # Should be v8+
```

---

## 📥 Installation Methods

### Method 1: GitHub Clone (Recommended)

```bash
# Clone the repository
git clone https://github.com/arthainvest/arthainvest-crm.git

# Navigate to folder
cd arthainvest-crm

# Install dependencies
npm install

# Start the server
node arthainvest-crm-enterprise-server.js
```

**Access:** http://localhost:3000

---

### Method 2: ZIP Download

1. Visit: https://github.com/arthainvest/arthainvest-crm
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Open terminal/PowerShell in the folder
5. Run:
   ```bash
   npm install
   node arthainvest-crm-enterprise-server.js
   ```

**Access:** http://localhost:3000

---

### Method 3: Docker (For Advanced Users)

```bash
# Build Docker image
docker build -t arthainvest-crm .

# Run container
docker run -p 3000:3000 -v $(pwd):/app arthainvest-crm

# Access via browser
http://localhost:3000
```

---

## 🚀 Step-by-Step Setup

### Step 1: Install Node.js
- Download from: https://nodejs.org/ (LTS version)
- Run installer and follow prompts
- Restart your computer
- Verify: `node --version`

### Step 2: Clone Repository
```bash
# Windows (PowerShell)
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm

# macOS/Linux (Terminal)
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm
```

### Step 3: Install Dependencies
```bash
npm install
```

**Expected output:**
```
added XXX packages in X.XXs
```

### Step 4: Start the Server
```bash
node arthainvest-crm-enterprise-server.js
```

**Expected output:**
```
🚀 ArthaInvest Enterprise CRM running on http://localhost:3000
✅ Features: Marketing, DigiLocker, Invoices, Voice Assistant...
```

### Step 5: Open in Browser
- URL: http://localhost:3000
- You should see the login page

---

## ✅ Verification

### Server Running Check
```bash
# Test if server is responding
curl http://localhost:3000

# Should return: 200 OK and HTML content
```

### Database Check
Verify database files exist:
- `arthainvest-enterprise.db` (Primary)
- `arthainvest.db` (Backup)
- `arthainvest-10-10.db` (Alternative)

---

## 👤 First Login

### Login Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| Admin | admin@arthainvest.com | admin123 | Full Access |
| Sales | rajesh@arthainvest.com | rajesh123 | Sales Manager |
| Insurance | priya@arthainvest.com | priya123 | Insurance Manager |
| Loans | amit@arthainvest.com | amit123 | Loans Manager |
| MF | sneha@arthainvest.com | sneha123 | Mutual Funds Manager |
| Marketing | vikram@arthainvest.com | vikram123 | Marketing Manager |

### First Login Steps

1. Open http://localhost:3000
2. Enter email: `admin@arthainvest.com`
3. Enter password: `admin123`
4. Click "Login"
5. You'll be redirected to dashboard

### IMPORTANT: Change Password

On first login:
1. Go to Settings (top-right menu)
2. Click "Change Password"
3. Enter current password: `admin123`
4. Create new strong password
5. Confirm new password
6. Click "Save"

---

## 🆘 Troubleshooting

### "Port 3000 Already In Use"

**Problem:** Error says port is already in use

**Solution:**
```bash
# Windows (PowerShell)
netstat -ano | findstr :3000
taskkill /PID [PID_NUMBER] /F

# macOS/Linux (Terminal)
lsof -i :3000
kill -9 [PID]
```

Then restart the server.

---

### "npm: command not found"

**Problem:** Node.js not installed properly

**Solution:**
1. Download Node.js from https://nodejs.org/
2. Install LTS version
3. Restart computer
4. Verify: `node --version`

---

### "Cannot find module"

**Problem:** Dependencies not installed

**Solution:**
```bash
# Delete node_modules and package-lock
rm -rf node_modules package-lock.json

# Reinstall
npm install

# Start again
node arthainvest-crm-enterprise-server.js
```

---

### "Database Connection Failed"

**Problem:** Database files missing

**Solution:**
1. Check if database files exist in the folder:
   - arthainvest-enterprise.db
   - arthainvest.db
   - arthainvest-10-10.db
2. If missing, clone fresh from GitHub
3. Restart server

---

### "Cannot Connect to localhost:3000"

**Problem:** Server not responding

**Solution:**
1. Check if server is running (you should see output in terminal)
2. Try http://127.0.0.1:3000 instead of localhost
3. Check firewall settings
4. Try different browser
5. Clear browser cache (Ctrl+Shift+Delete)

---

## 🎯 Features Available After Login

Once logged in, you have access to:

✅ Dashboard - Overview of all metrics
✅ Leads - Full lead management
✅ Calls - Call logging with AI
✅ Deals - Sales pipeline
✅ Contacts - Client database
✅ Reports - Analytics & insights
✅ Marketing - Campaigns (Canva + AI)
✅ DigiLocker - Secure documents
✅ Invoices - Invoice generation
✅ Voice Assistant - Mobile commands
✅ Team Management - Staff & permissions
✅ Settings - System configuration

---

## 📱 Mobile Access

### Local Network (Same WiFi)

1. Find your computer's IP:
   ```bash
   # Windows (PowerShell)
   ipconfig | findstr IPv4
   
   # macOS/Linux (Terminal)
   ifconfig | grep inet
   ```

2. On mobile device, open browser:
   ```
   http://[YOUR_IP]:3000
   Example: http://192.168.1.100:3000
   ```

3. Login with same credentials

### Requirements
- Mobile device on SAME WiFi network
- Server running on computer
- Modern browser (Safari for iOS, Chrome for Android)

---

## 🔐 Security Best Practices

1. **Change Default Passwords** - Change all default passwords on first login
2. **Keep Node.js Updated** - Run `npm update` regularly
3. **Use HTTPS in Production** - Configure SSL certificates
4. **Regular Backups** - Backup database files weekly
5. **Strong Passwords** - Use complex passwords (12+ characters)
6. **Access Control** - Only give employees their own credentials

---

## 📞 Getting Help

### Resources

- **Installation Guide:** This file (INSTALLATION_GUIDE.md)
- **Features Guide:** ENTERPRISE_FEATURES_GUIDE.md
- **Production Setup:** PRODUCTION_RUNBOOK.txt
- **API Documentation:** API_DOCS.md (if available)

### Common Issues

1. Check troubleshooting section above
2. Review documentation files
3. Check server console for error messages
4. Verify all system requirements met

---

## ✅ Installation Checklist

Before using in production, verify:

- [ ] Node.js v16+ installed
- [ ] All dependencies installed (`npm install` completed)
- [ ] Server starts without errors
- [ ] Browser can access http://localhost:3000
- [ ] Login page loads
- [ ] Can login with admin credentials
- [ ] Changed admin password
- [ ] Database files exist and have data
- [ ] All 6 employee accounts created
- [ ] Mobile access tested (optional)

---

## 🎊 Ready to Go!

Once installation is complete:

1. **For Admin:** Setup other team members and configure preferences
2. **For Employees:** Each employee logs in and changes their password
3. **For Users:** Start using CRM for your business processes

Your ArthaInvest Enterprise CRM is fully operational!

---

**Version:** 1.0.0-enterprise
**Last Updated:** August 13, 2026
**Status:** Production Ready ✅
