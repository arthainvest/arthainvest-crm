# ArthaInvest CRM - Build & Distribution Instructions

## For Administrators / IT Department

This guide explains how to build installers and distribute the CRM app to your team.

---

## Prerequisites

Before building, you'll need:

1. **Node.js & npm** (download from nodejs.org)
   ```bash
   # Verify installation
   node --version  # Should show v12 or higher
   npm --version
   ```

2. **Git** (optional, for cloning if needed)

3. **Windows Build Tools** (for Windows installer)
   - Visual Studio Build Tools or
   - Python 3.x + Microsoft C++ Build Tools

---

## Step 1: Set Up Development Environment

### Windows

```bash
# 1. Open Command Prompt or PowerShell

# 2. Navigate to CRM_APP folder
cd "C:\Users\artha\LaptopHub\CRM_APP"

# 3. Install dependencies
npm install

# This will install:
# - electron (desktop framework)
# - electron-builder (for creating installers)
```

### Mac/Linux

```bash
# Same commands as Windows
cd /path/to/CRM_APP
npm install
```

---

## Step 2: Test the App Before Building

```bash
# Start the app to test it works
npm start

# Test features:
# - Add a lead
# - Edit lead
# - Delete lead
# - Export data
# - All tabs working

# Close the app when done (Ctrl+C in terminal)
```

---

## Step 3: Build Windows Installer

```bash
# Build the installer
npm run build-win

# This creates:
# - arthainvest-crm-setup.exe (installer)
# - arthainvest-crm.exe (portable)
```

**Output location:** `CRM_APP/dist/`

### Installer Features:
- Install to Program Files
- Create Start Menu shortcuts
- Create Desktop shortcut
- Add/Remove Programs support

---

## Step 4: Build Mac Installer (Requires Mac)

```bash
npm run build

# Creates:
# - arthainvest-crm.dmg (disk image for Mac)
```

---

## Step 5: Distribution

### Option 1: USB Drive / Network Share

1. Copy `arthainvest-crm-setup.exe` to shared folder
2. Share link or USB with team
3. Each employee downloads and runs

### Option 2: Email Distribution

```
Subject: ArthaInvest CRM - New Desktop App

Hi Team,

New CRM app is ready for download!

Download here: [link to shared folder]
File: arthainvest-crm-setup.exe
Size: ~150MB

Installation is automatic - just run the .exe file.

Instructions: See README.md in the CRM_APP folder
Contact: [your email]
```

### Option 3: OneDrive / Google Drive Share

1. Upload `arthainvest-crm-setup.exe` to shared drive
2. Share link with team
3. Anyone can download and install

---

## Step 6: Employee Installation

### For Each Team Member:

1. **Download:** Get `arthainvest-crm-setup.exe`
2. **Run:** Double-click the file
3. **Install:** Follow wizard
4. **Open:** App launches automatically
5. **Add Team Member:** Contact admin with their name
6. **Start Using:** Add leads and track calls

---

## Updates & New Versions

### When Making Updates:

1. Edit files as needed
2. Update version in `package.json`:
   ```json
   "version": "1.0.1"
   ```
3. Rebuild:
   ```bash
   npm run build-win
   ```
4. Redistribute new `.exe` file

**Note:** Auto-update feature can be added later.

---

## File Structure

```
CRM_APP/
├── package.json        (Dependencies & version)
├── main.js            (Electron main process)
├── preload.js         (Secure IPC)
├── index.html         (UI)
├── app.js             (Application logic)
├── README.md          (User guide)
├── SETUP_INSTRUCTIONS.md (This file)
└── dist/              (Built installers - created after npm run build-win)
    ├── arthainvest-crm-setup.exe
    └── arthainvest-crm.exe
```

---

## Customization Options

### Change App Icon

1. Replace `icon.png` with your logo (256x256 px)
2. Rebuild installer
3. Icon will appear in taskbar and shortcuts

### Change Company Name

1. Edit `package.json`:
   ```json
   "productName": "Your Company CRM"
   ```
2. Rebuild

### Add Company Logo

1. Create 256x256 PNG logo
2. Save as `icon.png` in CRM_APP folder
3. Rebuild

---

## Troubleshooting Build Issues

### "npm not found"
- Node.js not installed properly
- Reinstall from nodejs.org

### "Build failed"
- Delete `node_modules` folder
- Run `npm install` again
- Retry build

### "Port 3000 already in use"
- Another app is using the port
- Restart computer or run: `npm start` with different port

### Large File Size
- Normal for Electron apps
- ~150MB is typical
- Includes entire Chromium browser

---

## Security Considerations

✅ **Good Practices:**
- Keep version updated
- Don't share unencrypted data backups
- Ensure Windows Defender isn't blocking app
- Test on a clean machine before distribution

⚠️ **Important:**
- Advise employees NOT to share CRM data files
- All employee data is local to their machine
- Set clear data privacy policies
- Regular backups recommended

---

## Support & Maintenance

### For IT/Admin:

1. **Track installations:** Keep record of who has the app
2. **Version control:** Note which version each person has
3. **Update rollout:** Plan updates quarterly
4. **Backup data:** Periodically collect CSV exports

### For Users:

1. **Report issues:** Clear bug reports help improvement
2. **Suggest features:** Track user requests
3. **Regular exports:** Weekly backups recommended
4. **Follow best practices:** See README.md

---

## Next Steps

### Immediate (This Week):
1. ✅ Test the app locally
2. ✅ Build Windows installer
3. ✅ Test installer on clean machine
4. ✅ Create distribution share/link

### Week 1:
1. ✅ Distribute to first employee
2. ✅ Get feedback
3. ✅ Make any quick fixes
4. ✅ Roll out to full team

### Week 2+:
1. ✅ Monitor usage
2. ✅ Collect feedback
3. ✅ Plan version 1.1
4. ✅ Schedule quarterly updates

---

## Version History

**v1.0.0** (Current)
- Initial release
- Lead management
- Call tracking
- Team collaboration
- CSV export

**Future Releases:**
- v1.1: Cloud sync option
- v1.2: Mobile app companion
- v1.3: API for integrations
- v2.0: Advanced analytics

---

## Questions?

For technical issues:
- Check README.md first
- Review this setup guide
- Test locally before distributing
- Contact: [admin email]

For user support:
- Share README with employees
- Point to Quick Start section
- Collect feedback for improvements

---

## Building is Complete! ✅

Your CRM app is ready to distribute.

**Next:** Share the installer with your team and get feedback!

Good luck! 🚀
