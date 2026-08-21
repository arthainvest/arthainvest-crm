# ArthaInvest CRM - Complete Setup Guide

## 🎯 What You Get

| Platform | Installation | Offline | Sync | Release |
|----------|--------------|---------|------|---------|
| **Web (PWA)** | Install from browser | ✅ Yes | ✅ Auto | Ready Now |
| **Windows Desktop** | Standalone .exe | ✅ Yes | ✅ Auto | `npm run build:win` |
| **Mac Desktop** | DMG installer | ✅ Yes | ✅ Auto | `npm run build:mac` |
| **Linux Desktop** | AppImage / .deb | ✅ Yes | ✅ Auto | `npm run build:linux` |
| **iOS App** | App Store | ✅ Yes | ✅ Auto | Flutter build |
| **Android App** | Google Play | ✅ Yes | ✅ Auto | Flutter build |

---

## 📋 Files Overview

```
CRM-PWA/
├── index.html           ← Main app (PWA + Electron)
├── manifest.json        ← PWA config
├── sw.js               ← Service Worker (offline)
├── db.js               ← IndexedDB local storage
├── main.js             ← Electron main process
├── preload.js          ← Electron security
├── package.json        ← Dependencies & build config
├── README.md           ← Full documentation
└── SETUP_GUIDE.md      ← This file
```

---

## 🌐 Option 1: Web App (PWA) - Instant Deploy

### **No Installation Required!**

#### **Method A: GitHub Pages (Free)**
```bash
# 1. Create GitHub repo
# 2. Upload files to /docs folder
# 3. Enable GitHub Pages in settings
# 4. URL: https://yourusername.github.io/arthainvest-crm
```

#### **Method B: Netlify (Free + Easy)**
```bash
# 1. Drag & drop folder to Netlify
# 2. Auto deploys
# 3. Custom domain support
```

#### **Method C: Self-Hosted Server**
```bash
# Copy all files to /var/www/html/crm or equivalent
# Configure HTTPS (required for PWA)
# Access at https://yourdomain.com/crm
```

#### **Use in Browser:**
```
1. Open https://yourdomain.com/
2. Click "Install ArthaInvest CRM"
3. Works offline automatically
4. Auto-syncs when online
```

#### **Offline Features:**
- ✅ Open app without internet
- ✅ Make changes (saved locally)
- ✅ Auto-sync when online
- ✅ View all data offline
- ✅ Full CRM functionality

---

## 💻 Option 2: Windows Desktop App

### **Step 1: Install Node.js**
- Download: https://nodejs.org/ (LTS version)
- Install with defaults

### **Step 2: Setup Project**
```bash
# Open Command Prompt or PowerShell
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\CRM-PWA

# Install dependencies (first time only)
npm install
```

### **Step 3: Run & Test**
```bash
# Run in development mode
npm start
```
- App opens automatically
- Change code → Auto-refresh
- Press F12 for Developer Tools

### **Step 4: Build Installer**
```bash
# Create Windows installer (.exe)
npm run build:win
```

**Output Files:**
- `dist/ArthaInvest-CRM-Setup-1.0.0.exe` ← Share this!
- Portable version also available

### **Step 5: Distribute**
- Share `.exe` file via email, USB, or website
- Users click to install
- Shortcut added to Desktop/Start Menu
- Fully offline capable

---

## 🍎 Option 3: Mac Desktop App

### **Requirements:**
- macOS 10.13+
- Node.js installed

### **Build:**
```bash
cd /path/to/CRM-PWA
npm install
npm run build:mac
```

**Output:**
- `dist/ArthaInvest-CRM-1.0.0.dmg`
- Users: Drag app to Applications folder

---

## 🐧 Option 4: Linux Desktop App

### **Build:**
```bash
cd /path/to/CRM-PWA
npm install
npm run build:linux
```

**Outputs:**
- AppImage (single file, no installation)
- .deb package (for Ubuntu/Debian)

---

## 📱 Option 5: iOS/Android Mobile Apps

### **Prerequisites:**
- Flutter SDK: https://flutter.dev/docs/get-started/install
- Android Studio (for Android)
- Xcode (for iOS - macOS only)

### **Quick Start:**
```bash
# Create new Flutter project
flutter create arthainvest_crm_mobile --org=com.arthainvest
cd arthainvest_crm_mobile

# Replace lib/main.dart with Flutter code from README.md
# Copy pubspec.yaml dependencies

# Test on emulator/device
flutter run

# Build for release
flutter build apk --release      # Android
flutter build ios --release      # iOS
```

### **Distribution:**
- **Android:** Upload AAB to Google Play Console
- **iOS:** Upload via App Store Connect (TestFlight)

---

## ⚙️ Configuration

### **Change App Name**
`package.json`:
```json
"productName": "Your App Name",
"name": "your-app-name"
```

### **Change Theme Colors**
`index.html` (CSS `:root`):
```css
--primary: #1e3a8a;          /* Main blue */
--primary-light: #3b82f6;
--secondary: #0f766e;        /* Teal */
--accent: #f59e0b;           /* Amber */
```

### **Add Company Logo**
Replace emoji in:
- `index.html` line 475: `<div class="login-logo">🏢</div>`
- Use `<img src="logo.png" />` instead

---

## 🔐 Security Setup

### **Change Default Credentials**
`index.html` (around line 482):
```html
<input type="email" value="your-email@company.com">
<input type="password" value="secure-password">
```

### **Enable HTTPS for PWA**
- **Required** for production
- Use Let's Encrypt (free) or buy certificate
- Redirect http → https

---

## 📊 Database & Data Sync

### **How Sync Works:**

**Online:**
1. User makes change
2. Saved to local IndexedDB/SQLite + sent to server
3. Server confirms → data synced

**Offline:**
1. User makes change
2. Saved to local IndexedDB/SQLite
3. Queued in sync-queue
4. When online → auto-uploads
5. Server confirms → cleared from queue

### **Server Integration:**
Create API endpoint `/api/sync` that accepts:
```json
{
  "storeName": "contacts",
  "operation": "add",
  "data": { "id": "123", "name": "John Doe", ... }
}
```

---

## 🚀 Performance Tips

### **Minimize App Size:**
```bash
npm run build:win --publish=never
```

### **Faster Syncs:**
- Batch operations
- Use indexes
- Compress data

### **Offline-First Performance:**
- Cache 90 days of data
- Index by date for quick queries
- Auto-cleanup old records

---

## 🐛 Troubleshooting

### **Issue: npm command not found**
**Solution:** Reinstall Node.js, close terminal, reopen

### **Issue: Port 3000 already in use**
**Solution:** 
```bash
npm start -- --port 3001
```

### **Issue: Service Worker not caching**
**Solution:**
- Ensure HTTPS (PWA requires)
- Check browser console for errors
- Clear cache: DevTools → Storage → Clear

### **Issue: Database sync not working**
**Solution:**
- Check network tab in DevTools
- Verify `/api/sync` endpoint exists
- Check sync-queue table in IndexedDB

### **Issue: Electron build fails**
**Solution:**
```bash
# Clean and rebuild
rm -r node_modules dist
npm install
npm run build:win
```

---

## 📦 Delivery Checklist

- [ ] Test all 3 offline scenarios
- [ ] Change default login credentials
- [ ] Add company logo
- [ ] Test on target OS/devices
- [ ] Create user guide
- [ ] Setup server sync endpoint
- [ ] Enable HTTPS (if web)
- [ ] Test data sync
- [ ] Prepare installer/documentation
- [ ] Create backup restore procedure

---

## 📞 Next Steps

1. **Choose your platform** (Web/Desktop/Mobile or all 3)
2. **Configure** app name, theme, credentials
3. **Build** using appropriate command
4. **Test** offline functionality
5. **Deploy** to users
6. **Monitor** sync and data integrity

---

## 💡 Pro Tips

- **Dev Mode:** Keep terminal open, auto-reloads on file change
- **Multiple Platforms:** Build all at once: `npm run build:all`
- **Mobile First:** Test on actual devices before release
- **Backup:** Users' local data stored in IndexedDB/SQLite, not lost
- **Updates:** Update app → data preserved automatically

---

## 📖 For Employees/Users

### **Web App:**
1. Visit: `https://yourcompany.com/crm`
2. Click "Install"
3. Works offline automatically

### **Desktop App:**
1. Run `.exe` installer
2. Click through setup
3. Desktop shortcut appears
4. Launch anytime

### **Mobile App:**
1. Download from App Store / Google Play
2. Tap "Install"
3. Works offline immediately

---

**Ready to deploy? Start with Option 1 (Web) - it's the fastest!** 🚀
