# ArthaInvest CRM v2.0 - Setup & Testing Guide

## What's New in v2.0

✅ **New Clients Tab** - Manage your 27 existing clients  
✅ **Role-Based Access Control** - Employees can't see client PAN or AUM  
✅ **Audit Logging** - Every action tracked (view, edit, export)  
✅ **CSV Import** - Bulk import clients from Google Sheets  
✅ **Cross-Sell Tracking** - MF, Health, Life insurance coverage status  
✅ **Commission Trail Support** - Renewal dates, review tracking  

---

## Quick Start - Test Now (No Installation)

### Option 1: Test in Browser (Right Now!)

1. **Navigate to CRM_APP folder:**
   ```
   C:\Users\artha\LaptopHub\CRM_APP\
   ```

2. **Open `index.html` in your browser:**
   - Double-click the file, OR
   - Right-click → Open with → Chrome/Edge/Firefox

3. **You should see:**
   - ArthaInvest CRM dashboard
   - Tabs: Dashboard, Leads, **Clients** (NEW), Pipeline, Team, Reports
   - "Add Client" and "Import CSV" buttons

4. **Test Features:**
   - Click "Add Client" → Fill form → Save
   - Notice: PAN & AUM fields show "🔒 Admin Only - Hidden from employees"
   - All data auto-saves to browser storage

---

## Full Setup - Build for Team Distribution

### Prerequisites

**Install Node.js (if not already installed):**

1. Go to https://nodejs.org/
2. Download LTS version (v20 or later)
3. Run installer, click "Next" through all steps
4. Restart your computer
5. Verify installation:
   ```powershell
   node --version
   npm --version
   ```

---

### Installation Steps

1. **Open PowerShell/Command Prompt**

2. **Navigate to CRM_APP:**
   ```powershell
   cd C:\Users\artha\LaptopHub\CRM_APP
   ```

3. **Install dependencies:**
   ```powershell
   npm install
   ```
   (This takes 5-10 minutes first time)

4. **Test locally:**
   ```powershell
   npm start
   ```
   - App should open in a window
   - Test all features
   - Press Ctrl+C to close

5. **Build installer for team:**
   ```powershell
   npm run build-win
   ```
   - Creates: `C:\Users\artha\LaptopHub\CRM_APP\dist\arthainvest-crm-setup.exe`

---

## Preparing Clients Data for Import

### Step 1: Export from Google Sheets

1. Open your Google Sheets Clients tab
2. Select all data (including headers)
3. Copy (Ctrl+C)
4. Paste into a text editor
5. Save as: `clients.csv`

### Step 2: Format Requirements

**Minimum columns needed:**
- Name
- Phone
- Email
- Product (MF / Insurance / Loan / Multiple)
- Folio / Policy No.

**Optional columns:**
- PAN (admin only field)
- AUM (admin only field)
- Start Date
- SIP Amount
- Frequency
- Renewal Date
- MF (Yes/No/Review Due)
- Health Insurance
- Life Insurance
- Last Review
- Notes

### Step 3: Import in CRM

1. Open ArthaInvest CRM → Clients tab
2. Click "📥 Import CSV"
3. Select your `clients.csv` file
4. Done! Clients loaded with audit log entry

---

## Role-Based Access - How It Works

### Admin (You)
**Visible fields:**
- ✅ All client data
- ✅ PAN number
- ✅ AUM (Assets Under Management)
- ✅ Commission Trail
- ✅ All reports (with financial data)
- ✅ Audit logs
- ✅ Export full data

### Employee
**Visible fields:**
- ✅ Client name, phone, email
- ✅ Product type (MF, Insurance, Loan)
- ✅ Folio/Policy number
- ✅ Next action & follow-up date
- ✅ Notes
- ❌ PAN (hidden)
- ❌ AUM (hidden)
- ❌ Commission info (hidden)
- ❌ Audit logs

**How to test:**
1. In app, press F12 (open developer console)
2. Run: `currentUser = 'employee'; location.reload();`
3. Notice: PAN & AUM fields disappear
4. Return: `currentUser = 'artha'; location.reload();`

---

## Data Security - DPDP Compliance

### Audit Logs Location
- **Windows Electron:** `C:\Users\[USERNAME]\AppData\Roaming\arthainvest-crm\audit_logs.json`
- **Browser:** localStorage (IndexedDB not used)

### Backup Your Data
```powershell
# Weekly backup to OneDrive
Copy-Item "C:\Users\[USERNAME]\AppData\Roaming\arthainvest-crm\crm_data.json" `
  -Destination "C:\Users\artha\OneDrive\Backups\crm_backup_$(Get-Date -Format 'yyyy-MM-dd').json"
```

---

## Testing Checklist

- [ ] Open CRM in browser → Dashboard loads
- [ ] Navigate all tabs (Dashboard, Leads, **Clients**, Pipeline, Team, Reports)
- [ ] **Clients tab:**
  - [ ] "Add Client" button works
  - [ ] Form opens with all fields
  - [ ] PAN & AUM labeled "🔒 Admin Only"
  - [ ] Save client → renders on list
  - [ ] Click client card → opens edit modal
  - [ ] Search clients by name/phone
  - [ ] "Import CSV" button (test with sample CSV)
  
- [ ] **Cross-sell tracking:**
  - [ ] Add client with MF = "Yes"
  - [ ] Set Health = "Review Due"
  - [ ] Product badges appear on client card
  
- [ ] **Admin only fields:**
  - [ ] Admin can see & edit PAN, AUM
  - [ ] Employee (currentUser='employee') cannot see PAN/AUM
  
- [ ] **Audit logging:**
  - [ ] View a client → logged as "view"
  - [ ] Edit & save → logged as "save"
  - [ ] Export → logged as "export"
  - [ ] Logs appear in: `C:\Users\[USERNAME]\AppData\Roaming\arthainvest-crm\audit_logs.json`
  
- [ ] **Data persistence:**
  - [ ] Add client
  - [ ] Close & reopen app
  - [ ] Client data still there
  
- [ ] **Export:**
  - [ ] Click Export button
  - [ ] CSV downloads with Leads + Clients data
  - [ ] Open in Excel → data formats correctly

---

## Distributing to Team

### For Employee #1:
1. Build installer: `npm run build-win`
2. Share file: `arthainvest-crm-setup.exe`
3. They install & launch
4. They add their name in "Team Members" tab
5. Data stays local on their laptop (no sync yet)

### Weekly Sync Process:
1. **Employee exports:** Click Export button → send CSV to you
2. **You review:** Check for duplicates
3. **You import:** In CRM, click "Import CSV" → select their data
4. **Central backup:** Save master CSV each week

---

## Troubleshooting

### "npm not found"
→ Node.js not installed or PATH not refreshed
→ Restart PowerShell or computer after installing Node.js

### "Module not found: better-sqlite3"
→ Run: `npm install`
→ Some modules build from source, may take 2-3 minutes

### Data not persisting
→ In browser: check if localStorage is enabled (Settings → Cookies/Storage → ON)
→ In Electron: data should auto-save to AppData\Roaming

### Audit logs not appearing
→ Make sure window.crm is available (Electron only)
→ Browser version stores logs in localStorage under key: 'crmAuditLogs'

---

## Features Summary

| Feature | Leads | Clients | Role-Based | Audit Logged |
|---------|-------|---------|-----------|--------------|
| Add/Edit | ✅ | ✅ | - | ✅ |
| View | ✅ | ✅ | ✅ (Clients) | ✅ |
| Delete | ✅ | ✅ | - | ✅ |
| Search/Filter | ✅ | ✅ | - | - |
| Import CSV | - | ✅ | - | ✅ |
| Export | ✅ | ✅ | ✅ (admin sees all) | ✅ |
| Cross-sell tracking | - | ✅ | - | - |
| Renewal dates | - | ✅ | - | - |

---

## Next Steps

1. **Today:** Test in browser (5 mins)
2. **This week:** 
   - Install Node.js
   - Run `npm install`
   - Test locally with `npm start`
   - Import your 27 clients from CSV
3. **Next week:**
   - Build installer: `npm run build-win`
   - Share with first employee
   - Get feedback

---

## Support

**For setup issues:** Check node.js installation first  
**For feature requests:** All features are built-in  
**For data recovery:** Find `crm_data.json` in AppData\Roaming\arthainvest-crm

**Version:** ArthaInvest CRM v2.0.0  
**Built:** August 7, 2026  
**ARN-267891 | POSP | DSA**
