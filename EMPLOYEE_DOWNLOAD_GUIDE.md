# 🎯 ArthaInvest Capital CRM - Employee Download & Installation Guide

**Version:** 10/10 Production Ready  
**Last Updated:** August 13, 2026  
**Status:** ✅ Live & Operational

---

## 📱 Quick Access

### **Web Application (Recommended)**
🌐 **URL:** http://localhost:3001  
📊 **Access:** Any modern web browser (Chrome, Firefox, Safari, Edge)  
⚡ **Performance:** Instant access, no installation needed

### **GitHub Repository**
🔗 **Repository:** https://github.com/arthainvest/arthainvest-crm  
📥 **Clone:** `git clone https://github.com/arthainvest/arthainvest-crm.git`  
✅ **Branch:** main (Latest version with ArthaInvest Capital branding)

---

## 💻 LAPTOP INSTALLATION

### **Option 1: Quick Start (Recommended)**

#### **Step 1: Clone Repository**
```bash
cd C:\Users\[YourUsername]
git clone https://github.com/arthainvest/arthainvest-crm.git
cd arthainvest-crm
```

#### **Step 2: Install Dependencies**
```bash
npm install
```

#### **Step 3: Start Backend Server**
```bash
node arthainvest-10-10-enhanced-server.js
```

#### **Step 4: Open in Browser**
Go to: **http://localhost:3001**

**Login Credentials:**
- 📧 Email: `admin@arthainvest.com`
- 🔐 Password: `admin123`

---

### **Option 2: Using Desktop Launcher (Windows)**

1. **Download the launcher files:**
   - 🎯 `ArthaInvest_Capital_CRM.lnk` (Shortcut)
   - 🎯 `🎯_ArthaInvest_Capital_CRM.bat` (Launcher script)

2. **Place on Desktop:**
   - Copy both files to your Desktop

3. **Double-click the shortcut:**
   - CRM will open automatically
   - Backend server starts in background

---

### **Option 3: Manual Setup**

1. **Install Node.js** (if not already installed)
   - Download: https://nodejs.org/ (v16 or higher)

2. **Clone the Repository**
   ```bash
   git clone https://github.com/arthainvest/arthainvest-crm.git
   cd arthainvest-crm
   ```

3. **Install npm packages**
   ```bash
   npm install
   ```

4. **Start the server**
   ```bash
   npm start
   # or
   node arthainvest-10-10-enhanced-server.js
   ```

5. **Access the CRM**
   - Open browser: http://localhost:3001
   - Login with credentials above

---

## 📱 MOBILE ACCESS

### **Web Browser Access (Recommended)**
- 📱 Access from any smartphone browser
- 📍 URL: `http://[YourComputerIP]:3001`
- ✅ Responsive design works on mobile

### **Find Your Computer's IP Address**

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

**Then on Mobile:**
- Open browser
- Enter: `http://192.168.1.100:3001`

### **Mobile-Optimized Apps (Coming Soon)**
- 📱 iOS App (App Store)
- 🤖 Android App (Google Play Store)

---

## 🔐 LOGIN CREDENTIALS

| Field | Value |
|-------|-------|
| **Email** | admin@arthainvest.com |
| **Password** | admin123 |
| **Role** | Administrator |
| **Access** | Full system access |

**⚠️ IMPORTANT:** Change password on first login!

---

## 📋 SYSTEM REQUIREMENTS

### **Laptop (Windows/Mac/Linux)**
- ✅ 4GB RAM minimum (8GB recommended)
- ✅ 500MB free disk space
- ✅ Node.js v16+ installed
- ✅ Modern web browser
- ✅ Internet connection (for initial setup)

### **Mobile (iOS/Android)**
- ✅ Modern smartphone (iOS 12+ or Android 6+)
- ✅ WiFi or mobile internet connection
- ✅ Modern web browser

---

## 🚀 FEATURES

✅ **Client Management** - 320+ active clients  
✅ **Sales Pipeline** - Deal tracking & probability scoring  
✅ **Commission Tracking** - Auto-calculated from closed deals  
✅ **Call Logging** - Phone & WhatsApp integration  
✅ **Documents** - Google Drive integration  
✅ **Reports** - Real-time analytics & dashboards  
✅ **Targets** - Performance tracking & goals  
✅ **Multi-user** - Role-based access control  

---

## 📊 BUSINESS MODULES

- 💼 **Pipelines** - Sales pipeline management
- 👥 **Contacts** - Client database (156+ contacts)
- 🏢 **Companies** - Company information
- 📦 **Products** - Product catalog
- 📞 **Activities** - Call logs & follow-ups
- 📈 **Dashboard** - Real-time KPIs
- 💾 **Data Hub** - Integrated data sources

---

## 🆘 TROUBLESHOOTING

### **Port Already in Use**
```bash
# If port 3001 is already in use:
netstat -ano | findstr :3001
taskkill /PID [PID_NUMBER] /F
```

### **Node.js Not Found**
- Install from: https://nodejs.org/
- Restart computer after installation
- Verify: `node --version`

### **Cannot Connect to Database**
- Ensure `arthainvest-10-10.db` exists in project folder
- Check file permissions
- Try restarting the server

### **Mobile Connection Issues**
- Ensure laptop and mobile are on same WiFi network
- Use computer IP address (not localhost)
- Check firewall settings

---

## 📞 SUPPORT & DOCUMENTATION

**Quick Start Guide:**
- 📄 `README_ARTHAINVEST_CRM.md`

**Complete Documentation:**
- 📄 `ARTHAINVEST_CRM_COMPLETE_GUIDE.txt`
- 📄 `PRODUCTION_RUNBOOK.txt`

**Video Tutorials:** (Coming Soon)
- 🎥 Getting Started
- 🎥 Client Management
- 🎥 Commission Tracking
- 🎥 Reports & Analytics

---

## 🔄 Updates & Maintenance

**Automatic Updates:**
```bash
# Pull latest changes from GitHub
git pull origin main

# Reinstall dependencies if needed
npm install

# Restart server
node arthainvest-10-10-enhanced-server.js
```

**Version Info:**
- Current Version: 10/10 (Production)
- Latest: https://github.com/arthainvest/arthainvest-crm/releases
- Changelog: See GitHub repository

---

## 🎓 GETTING STARTED CHECKLIST

- [ ] Clone repository
- [ ] Install Node.js
- [ ] Run `npm install`
- [ ] Start backend server
- [ ] Open http://localhost:3001
- [ ] Login with credentials
- [ ] Change password (first login)
- [ ] Explore dashboards
- [ ] Configure personal profile
- [ ] Contact admin for questions

---

## 📞 CONTACT INFORMATION

**Technical Support:**
- 📧 Email: support@arthainvest.com
- 📱 WhatsApp: [Your WhatsApp Number]
- 💼 Manager: [Manager Name]

**Documentation:**
- 📁 All docs: `/docs` folder in repository
- 🌐 Online: https://github.com/arthainvest/arthainvest-crm/wiki

---

## ✅ VERIFICATION CHECKLIST

After installation, verify:
- ✅ Backend server starts without errors
- ✅ Browser opens to http://localhost:3001
- ✅ Login page displays
- ✅ Can login with credentials
- ✅ Dashboard loads with data
- ✅ Navigation menu works
- ✅ Can access different modules

---

## 📱 MOBILE-SPECIFIC NOTES

**iOS:**
- Use Safari or Chrome
- Bookmark for quick access
- Add to home screen for app-like experience

**Android:**
- Use Chrome or Firefox
- Bookmark for quick access
- Use Chrome's "Add to Home Screen" feature

**Both Platforms:**
- Responsive design adapts to screen size
- Touch-friendly navigation
- Offline capability (partial)

---

## 🎉 YOU'RE ALL SET!

Your ArthaInvest Capital CRM is ready to use.

**Start here:** http://localhost:3001

Questions? Contact your manager or technical support.

**Happy selling!** 🚀

---

**Last Updated:** August 13, 2026  
**Version:** 10/10 Production  
**Status:** ✅ Live & Verified
