# ArthaInvest CRM Pro - Desktop & Mobile App

Enterprise Fintech CRM Platform with **Offline + Online** functionality across Web, Desktop (Windows/Mac), and Mobile (iOS/Android).

## 🚀 Quick Start

### **Option 1: Web App (PWA)** - Fastest to Deploy
```bash
# No setup needed! Open in browser:
# 1. Place files in a web server
# 2. Open https://yourdomain.com/
# 3. Click "Install" when prompted
# 4. Works offline automatically
```

**Features:**
- ✅ Works on any device (Windows, Mac, iPhone, Android)
- ✅ Installable from browser
- ✅ Full offline support
- ✅ Auto-sync when online
- ✅ No app store needed

---

### **Option 2: Desktop App (Electron)** - Professional Installation

#### **Requirements:**
- Windows 10+ / Mac 10.13+ / Linux
- Node.js 14+ installed

#### **Installation & Setup:**

```bash
# 1. Navigate to project directory
cd C:\Users\artha\OneDrive\Desktop\ArthaInvest\CRM-PWA

# 2. Install dependencies
npm install

# 3. Run app in development
npm start

# 4. Build installer (Windows)
npm run build:win

# 5. Build for Mac
npm run build:mac

# 6. Build for Linux
npm run build:linux

# 7. Build all platforms
npm run build:all
```

**Output:**
- Windows: `dist/ArthaInvest-CRM-Setup-1.0.0.exe` (Installer)
- Windows Portable: `dist/ArthaInvest-CRM-1.0.0.exe` (No installation)
- Mac: `dist/ArthaInvest-CRM-1.0.0.dmg`
- Linux: `dist/arthainvest-crm-1.0.0.AppImage` + `.deb`

#### **Desktop App Features:**
- ✅ Standalone installation
- ✅ SQLite local database
- ✅ Offline-first architecture
- ✅ Automatic updates (configurable)
- ✅ System tray integration
- ✅ Native notifications
- ✅ Background sync

---

### **Option 3: Mobile Apps (iOS/Android)** - Using Flutter

#### **Requirements:**
- Flutter SDK installed
- Xcode (Mac) for iOS
- Android Studio for Android

#### **Flutter Setup:**

```bash
# 1. Create Flutter project
flutter create arthainvest_crm_mobile --org=com.arthainvest

# 2. Replace lib/main.dart with code below
# See Flutter Setup section below

# 3. Run on Android
flutter run

# 4. Run on iOS
flutter run -d iphone

# 5. Build APK (Android)
flutter build apk --release

# 6. Build AAB (Google Play)
flutter build appbundle

# 7. Build iOS IPA
flutter build ios --release
```

#### **Flutter Mobile App Code** (`lib/main.dart`):

```dart
import 'package:flutter/material.dart';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:intl/intl.dart';

void main() {
  runApp(const ArthaInvestCRMApp());
}

class ArthaInvestCRMApp extends StatelessWidget {
  const ArthaInvestCRMApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ArthaInvest CRM',
      theme: ThemeData(
        primaryColor: const Color(0xFF1e3a8a),
        useMaterial3: true,
      ),
      home: const LoginScreen(),
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _selectedRole = 'admin';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF1e3a8a), Color(0xFF3b82f6)],
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(20.0),
              child: Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(30.0),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        '🏢',
                        style: TextStyle(fontSize: 48),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        'ArthaInvest',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1e3a8a),
                        ),
                      ),
                      const Text(
                        'Enterprise Fintech CRM',
                        style: TextStyle(
                          fontSize: 14,
                          color: Color(0xFF6b7280),
                        ),
                      ),
                      const SizedBox(height: 30),
                      TextField(
                        controller: _emailController,
                        decoration: InputDecoration(
                          labelText: 'Email Address',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _passwordController,
                        obscureText: true,
                        decoration: InputDecoration(
                          labelText: 'Password',
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButton<String>(
                        value: _selectedRole,
                        isExpanded: true,
                        items: ['admin', 'leader', 'employee']
                            .map((role) => DropdownMenuItem(
                                  value: role,
                                  child: Text(role.toUpperCase()),
                                ))
                            .toList(),
                        onChanged: (value) {
                          setState(() => _selectedRole = value!);
                        },
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: () {
                          Navigator.of(context).pushReplacement(
                            MaterialPageRoute(
                              builder: (_) => const DashboardScreen(),
                            ),
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1e3a8a),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 50,
                            vertical: 14,
                          ),
                        ),
                        child: const Text(
                          'Sign In',
                          style: TextStyle(fontSize: 16),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        backgroundColor: const Color(0xFF1e3a8a),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Dashboard',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 20),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 16,
              crossAxisSpacing: 16,
              children: [
                _buildKPICard('Deals Closed', '18', '₹45,00,000'),
                _buildKPICard('In Progress', '12', '₹32,00,000'),
                _buildKPICard('Rejected', '5', '₹8,50,000'),
                _buildKPICard('On Hold', '7', '₹15,50,000'),
              ],
            ),
          ],
        ),
      ),
      bottomNavigationBar: BottomNavigationBar(
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.people), label: 'Contacts'),
          BottomNavigationBarItem(icon: Icon(Icons.trending_up), label: 'Pipeline'),
          BottomNavigationBarItem(icon: Icon(Icons.phone), label: 'Calls'),
          BottomNavigationBarItem(icon: Icon(Icons.menu), label: 'More'),
        ],
      ),
    );
  }

  Widget _buildKPICard(String label, String value, String change) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Text(label, style: const TextStyle(fontSize: 12, color: Color(0xFF6b7280))),
            Text(value, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            Text(change, style: const TextStyle(fontSize: 12, color: Color(0xFF10b981))),
          ],
        ),
      ),
    );
  }
}
```

#### **Flutter pubspec.yaml Dependencies:**
```yaml
dependencies:
  flutter:
    sdk: flutter
  sqflite: ^2.2.8
  path: ^1.8.2
  intl: ^0.18.1
  http: ^1.1.0
  connectivity_plus: ^4.0.1
  shared_preferences: ^2.1.1
```

---

## 📱 Offline/Online Sync Architecture

### **Data Flow:**
```
User Action (Online/Offline)
    ↓
IndexedDB (Browser) / SQLite (Desktop/Mobile)
    ↓
Service Worker/Electron caches
    ↓
Sync Queue (when online)
    ↓
Server API (POST /api/sync)
    ↓
Cloud Database
```

### **Sync Queue Features:**
- ✅ Automatic sync when online
- ✅ Retry logic (up to 3 retries)
- ✅ Conflict resolution
- ✅ Real-time updates
- ✅ Background sync (Electron)

---

## 🔐 Security Features

- **Context Isolation** (Electron)
- **Encrypted Credentials** (local storage)
- **Role-Based Access Control** (Admin/Leader/Employee)
- **HTTPS Only** (PWA)
- **Credential Validation** (Forms)

---

## 📊 Database Schema

### **Tables:**
- `contacts` - Client information
- `pipeline` - Deal tracking
- `calls` - Call logs & follow-ups
- `team` - Team member profiles
- `documents` - Document management
- `syncQueue` - Pending changes
- `credentials` - API keys & integration details
- `userSettings` - User preferences

---

## 🚀 Deployment

### **Web (PWA):**
```bash
# Host on any web server
# Examples: Netlify, Vercel, GitHub Pages, AWS S3, Heroku
```

### **Desktop (Electron):**
```bash
npm run build:all
# Distribute via website, email, or app store
```

### **Mobile (Flutter):**
```bash
# Android: Upload APK/AAB to Google Play
# iOS: Upload IPA to Apple App Store via TestFlight
```

---

## 🔄 Enable Auto-Updates (Electron)

Update `main.js`:
```javascript
const { autoUpdater } = require('electron-updater');

function createWindow() {
  // ... existing code ...
  
  // Check for updates
  autoUpdater.checkForUpdatesAndNotify();
}
```

---

## 📞 Support

For issues or questions:
- Email: support@arthainvest.com
- Dashboard: Access built-in support chat

---

## 📝 License

MIT License - Open for personal and commercial use
