# ArthaInvest CRM - Desktop Application

**A complete Customer Relationship Management (CRM) system built for ArthaInvest Capital**

## Features

✅ **Lead Management**
- Add, edit, and track all leads
- Capture phone, email, budget, and requirements
- Store detailed notes and conversation history

✅ **Call Tracking & Reminders**
- Set preferred call times for each lead
- Auto-schedule follow-up reminders
- Track call history and interactions
- Daily call schedule view

✅ **Pipeline Management**
- Track leads through stages: New → Contacted → Interested → Meeting → Proposal → Closed
- My Pipeline view for personal tracking
- Team-wide pipeline visibility

✅ **Team Collaboration**
- Assign leads to team members
- Team member management
- Track individual performance metrics

✅ **Reporting & Analytics**
- Dashboard with key metrics
- Conversion rate tracking
- Export reports as CSV
- Performance analytics

✅ **Data Sync & Backup**
- Auto-save all data locally
- Easy CSV export/import
- Backup functionality
- Works offline

---

## System Requirements

- **OS:** Windows 7 or later, macOS 10.10+, Linux
- **RAM:** 2GB minimum
- **Storage:** 100MB free space
- **Internet:** Optional (works offline)

---

## Installation

### Option 1: Using the Installer (Recommended)

1. Download the installer: `arthainvest-crm-setup.exe`
2. Double-click to run
3. Follow the installation wizard
4. Click "Finish" - app opens automatically

### Option 2: Portable Version (No Installation)

1. Download: `arthainvest-crm-portable.exe`
2. Double-click to run directly (no installation needed)
3. App launches immediately

### Option 3: Developer Setup (Windows/Mac/Linux)

**Prerequisites:**
- Node.js 12+ (download from nodejs.org)
- npm (comes with Node.js)

**Steps:**

```bash
# 1. Extract the CRM_APP folder to your desktop

# 2. Open terminal/command prompt in CRM_APP folder

# 3. Install dependencies
npm install

# 4. Start the app
npm start

# 5. To build an installer
npm run build-win  # Windows
# For Mac: npm run build  (requires macOS)
```

---

## Quick Start

### First Launch

1. App opens with Dashboard view
2. Click **"+ Add Lead"** to add your first lead
3. Fill in lead details:
   - Name (required)
   - Phone number
   - Email address
   - Status
   - Budget/Value
   - Assigned to (your name or team member)

### Adding Call Reminders

1. When adding a lead, set:
   - **What time to call:** 10:00 AM, 2:30 PM, etc.
   - **Call reminder:** Date when you want to follow up

2. App will remind you on the set date

### Daily Workflow

1. **Morning:**
   - Check "Call Schedule" tab for today's reminders
   - Click "✓ Called" when you contact someone

2. **Throughout Day:**
   - Click leads to add notes
   - Update status as you progress (Contacted → Interested → Meeting, etc.)
   - Set next action and due date

3. **End of Day:**
   - Review "My Pipeline" for next steps
   - Export data if needed

---

## Using Each Tab

### 📊 Dashboard
- See your key metrics at a glance
- View recent activity
- Quick stats: Total leads, Pipeline, Calls, Follow-ups

### 👥 All Leads
- View all leads in card format
- Search by name or details
- Click to edit or delete
- Add new leads with "+ Add Lead" button

### 📈 My Pipeline
- Table view of your assigned leads
- See status, next action, and due dates
- Quick action buttons
- Filter by date or status

### 📞 Call Schedule
- See leads to call today
- Shows preferred call times
- Click "✓ Called" to mark completed

### 👨‍💼 Team
- Manage team members
- See leads assigned to each person
- Add new team members
- View team performance

### 📋 Reports
- Conversion rate tracking
- Success metrics
- Export data as CSV
- Performance analytics

---

## Data Format

### Lead Fields

| Field | Type | Purpose |
|-------|------|---------|
| Name | Text | Lead's full name (required) |
| Phone | Tel | Contact number |
| Email | Email | Email address |
| Status | Dropdown | Conversation stage |
| Budget | Text | Estimated value (e.g., ₹50L - 1Cr) |
| What Time to Call | Time | Preferred calling hours |
| Call Reminder | Date | When to follow up |
| Assigned To | Dropdown | Which team member |
| Next Action | Text | What to do next |
| Next Action Date | Date | When to do it |
| Notes | Text | Conversation details |

### Status Values
- **New:** Not contacted yet
- **Contacted:** Initial contact made
- **Interested:** Lead showed interest
- **Meeting:** Meeting scheduled
- **Proposal:** Sent proposal/quote
- **Closed:** Deal closed or lost

---

## Export & Backup

### Export as CSV

1. Click **"⬇️ Export"** button in header
2. Choose save location
3. File saved with today's date
4. Share with team or import elsewhere

### Import Data

For team members who need to sync data:
1. Share the CSV export file
2. They can review in Excel or reimport

### Manual Backup

CSV files can be opened in Excel and backed up easily.

---

## Troubleshooting

### App Won't Start
- **Solution:** Restart the app or reinstall
- **Windows:** Uninstall from Control Panel > Reinstall

### Data Not Saving
- **Solution:** Check disk space (need 100MB free)
- **Solution:** Try exporting data to backup

### Missing Team Members
- **Solution:** Use Team tab to re-add them
- All data is stored locally on your machine

### Export Not Working
- **Solution:** Ensure you have write permissions in Documents
- **Solution:** Try exporting to Desktop instead

---

## Sharing Data Between Employees

### Option 1: Cloud Sync (Recommended)
1. Export data from app (⬇️ Export button)
2. Save to shared folder or Google Drive
3. Team members can download and import

### Option 2: Email
1. Export as CSV
2. Email file to team members
3. They import locally

### Option 3: USB Drive
1. Export data
2. Copy CSV file to USB
3. Share with team member

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `ESC` | Close modal/dialog |
| `Ctrl+S` | Save data (auto-saves) |
| `Ctrl+E` | Export data |

---

## Tips & Best Practices

✅ **Set Reminders Early**
- Add call reminders when adding leads
- Set preferred call times in lead details

✅ **Update Status Regularly**
- Mark as "Contacted" after calling
- Move to "Interested" when there's positive response
- Track progress through pipeline

✅ **Add Detailed Notes**
- Record conversation summary
- Note objections and budget confirmed
- Track next steps discussed

✅ **Assign Leads**
- Assign to yourself or team member
- Use "My Pipeline" to see your leads
- Don't leave leads unassigned

✅ **Export Regularly**
- Weekly backup to shared folder
- Before important meetings
- For reporting to management

---

## Multi-Employee Setup

### For Team Leads / Managers

1. Install CRM on your machine
2. Add team members in "Team" tab
3. Add leads and assign to team
4. Export data and share CSV weekly
5. Each employee gets their own installation

### For Each Team Member

1. Install CRM on their laptop
2. When manager adds them to Team, they see themselves
3. View leads assigned to them in "My Pipeline"
4. Update statuses and add notes
5. Export weekly for manager review

---

## Contact & Support

**Issues or Feature Requests:**
- Report problems to: support@arthainvest.com
- Include version number (see About menu)

**Data Privacy:**
- All data stays on your computer
- No cloud storage by default
- You control all exports and sharing

---

## Version

**ArthaInvest CRM v1.0.0**

AMFI ARN-267891 | IRDAI POSP | DSA

---

## Legal

This software is provided as-is for ArthaInvest Capital employees.
Ensure compliance with all applicable regulations when managing client data.

---

## Getting Help

### First Time Setup?
1. Read this README
2. Try the Quick Start section
3. Watch the in-app tooltips

### Having Issues?
1. Check Troubleshooting section
2. Try restarting the app
3. Export data to backup before reinstalling

### Ready to Use?
Start adding leads and tracking calls! 🚀
