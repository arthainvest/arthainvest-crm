# 🧪 INSTALLER TEST GUIDE

**Installer File:** `arthainvest-crm-setup.exe`  
**Size:** 64.81 MB  
**Test Date:** August 7, 2026  
**Status:** Ready for Testing

---

## 🚀 INSTALLATION WIZARD WALKTHROUGH

### **Step 1: Welcome Screen**
```
┌────────────────────────────────────────────────────┐
│ ArthaInvest CRM Setup                              │
│                                                    │
│ Welcome to ArthaInvest CRM Setup Wizard           │
│                                                    │
│ This wizard will guide you through the            │
│ installation of ArthaInvest CRM v2.0.0            │
│                                                    │
│ [ < Back ]  [ Next >]  [ Cancel ]                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:** Click `[ Next >]`

---

### **Step 2: Installation Path**
```
┌────────────────────────────────────────────────────┐
│ Select Destination Directory                      │
│                                                    │
│ Where should ArthaInvest CRM be installed?        │
│                                                    │
│ [ C:\Program Files\ArthaInvest CRM    ]           │
│           [ Browse... ]                            │
│                                                    │
│ [ < Back ]  [ Next >]  [ Cancel ]                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:** 
- Default path is fine: `C:\Program Files\ArthaInvest CRM`
- Click `[ Next >]`

---

### **Step 3: Ready to Install**
```
┌────────────────────────────────────────────────────┐
│ Ready to Install                                   │
│                                                    │
│ ArthaInvest CRM will be installed to:             │
│ C:\Program Files\ArthaInvest CRM                  │
│                                                    │
│ Installation will take approximately 2-3 minutes │
│                                                    │
│ [ < Back ]  [ Install ]  [ Cancel ]               │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:** Click `[ Install ]`

---

### **Step 4: Installing (Progress Bar)**
```
┌────────────────────────────────────────────────────┐
│ Installing ArthaInvest CRM                         │
│                                                    │
│ Extracting files...  [████████░░░░░░░░░░] 40%    │
│                                                    │
│ Please wait...                                     │
│                                                    │
│                       [ Cancel ]                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:** Wait for completion (2-3 minutes)

---

### **Step 5: Installation Complete**
```
┌────────────────────────────────────────────────────┐
│ Installation Complete                              │
│                                                    │
│ ArthaInvest CRM has been successfully installed   │
│                                                    │
│ ☑ Launch application now                          │
│                                                    │
│ [ < Back ]  [ Finish ]                            │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:**
- Checkbox "Launch application now" should be CHECKED
- Click `[ Finish ]`

---

### **Step 6: CRM Launches!**

CRM window opens automatically with login screen:

```
┌────────────────────────────────────────────────────┐
│                                                    │
│          ArthaInvest CRM                          │
│      Enterprise Edition v2.0                      │
│                                                    │
│     ┌────────────────────────────────┐            │
│     │ Username: [____________]       │            │
│     │ Password: [____________]       │            │
│     │                                │            │
│     │    [ LOGIN ]                   │            │
│     │                                │            │
│     │ Demo Users:                    │            │
│     │ • artha / artha123 (Admin)     │            │
│     │ • ravi / ravi123 (Employee)    │            │
│     │ • priya / priya123 (Employee)  │            │
│     │                                │            │
│     └────────────────────────────────┘            │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Your Action:**
1. Type username: `artha`
2. Type password: `artha123`
3. Click `[ LOGIN ]`

---

## ✅ EXPECTED RESULTS

After login, you should see:

```
┌─────────────────────────────────────────────────────────────┐
│ [Logo] ArthaInvest CRM        [User] Artha Kumar  [Logout]  │
├──────────────────┬───────────────────────────────────────────┤
│ SIDEBAR          │ MAIN CONTENT                              │
│                  │                                           │
│ 📱 ArthaInvest   │ Dashboard                                │
│ Artha Kumar      │                                           │
│ Admin            │ Stats:                                    │
│                  │ • Total Leads: 0                          │
│ GENERAL          │ • New Leads: 0                            │
│ • Dashboard ✓    │ • Active: 0                               │
│ • All Leads      │ • Closed: 0                               │
│ • Team Members   │                                           │
│                  │ Recent Activity:                          │
│ ANALYTICS        │ (Empty - no data yet)                     │
│ • Reports        │                                           │
│                  │                                           │
│ ADMIN ONLY ✓     │                                           │
│ • Users          │                                           │
│ • Settings       │                                           │
│                  │                                           │
│ [Logout]         │                                           │
│                  │                                           │
└──────────────────┴───────────────────────────────────────────┘
```

**Verify:**
- ✅ Dashboard is visible
- ✅ Sidebar shows all menu items
- ✅ Admin sections visible (because you're admin)
- ✅ No errors shown

---

## 🧪 FUNCTIONALITY TESTS

After installation and login, test these features:

### **Test 1: Navigation**
- [ ] Click "All Leads" → Page changes
- [ ] Click "Team Members" → Shows team
- [ ] Click "Reports" → Shows analytics
- [ ] Click "Manage Users" → Shows admin panel
- [ ] Click "Settings" → Shows settings
- Click "Dashboard" → Back to dashboard

### **Test 2: Add a Lead**
- [ ] Click "All Leads"
- [ ] Click "+ Add Lead"
- [ ] Fill in form:
  - Name: `Test Lead`
  - Phone: `9876543210`
  - Status: `New`
  - Budget: `Test`
- [ ] Click "Save Lead"
- [ ] Lead appears in list

### **Test 3: Dashboard Updates**
- [ ] Go to Dashboard
- [ ] Total Leads changed to: 1
- [ ] New Leads changed to: 1
- [ ] Recent Activity shows your lead

### **Test 4: Edit Lead**
- [ ] Go to All Leads
- [ ] Click the lead
- [ ] Change Status to: `Contacted`
- [ ] Click Save
- [ ] Status badge changes color
- [ ] Go to Dashboard
- [ ] Active Leads updated to: 1

### **Test 5: Data Persistence**
- [ ] Close the CRM completely
- [ ] Reopen from Start Menu or shortcut
- [ ] Login again: artha / artha123
- [ ] Go to All Leads
- [ ] Your lead is still there!

### **Test 6: Role-Based Access**
- [ ] Click "Manage Users"
- [ ] See list of users
- [ ] Verify you can see user management (admin feature)
- [ ] Logout
- [ ] Login as: ravi / ravi123
- [ ] Try to access "Manage Users"
- [ ] Should NOT be visible (employee restricted)

### **Test 7: Export Data**
- [ ] Login as: artha / artha123
- [ ] Look for Export button
- [ ] Click Export
- [ ] CSV file downloads
- [ ] Open file in Excel/Notepad
- [ ] Verify lead data is there

---

## 📋 INSTALLATION VERIFICATION CHECKLIST

### **Pre-Installation**
- [ ] Installer file exists: arthainvest-crm-setup.exe
- [ ] File size: ~64.8 MB
- [ ] File is readable

### **During Installation**
- [ ] Wizard opens correctly
- [ ] Welcome screen displays
- [ ] Path selection works
- [ ] Progress bar appears
- [ ] Installation completes without errors
- [ ] No Windows warnings/blocks

### **Post-Installation**
- [ ] CRM launches automatically
- [ ] Login screen appears
- [ ] Demo credentials work
- [ ] Dashboard loads
- [ ] All menu items visible

### **Functionality Tests**
- [ ] Add lead works
- [ ] Edit lead works
- [ ] Dashboard updates
- [ ] Data persists
- [ ] Export works
- [ ] No console errors

### **System Integration**
- [ ] Shortcut created on Desktop
- [ ] Start Menu entry created
- [ ] Can launch from Start Menu
- [ ] Can uninstall via Control Panel
- [ ] Uninstall cleans up properly

---

## 🔧 TROUBLESHOOTING

### **Issue: "Windows SmartScreen" Warning**
```
Windows Defender SmartScreen prevented an unrecognized app from starting.
Running this app might put your PC at risk.
```

**Solution:**
- Click: "More info"
- Click: "Run anyway"
- This is normal for new apps

### **Issue: Installation Hangs**
**Solution:**
- Wait 5 minutes (download may still be happening)
- Check Task Manager: Look for electron-builder process
- If stuck, click Cancel and retry

### **Issue: CRM Won't Start After Install**
**Solution:**
- Restart your computer
- Manually launch from Start Menu: "ArthaInvest CRM"
- Check if AppData folder was created: `%LOCALAPPDATA%\arthainvest-crm`

### **Issue: Login Fails**
**Solution:**
- Check username: `artha` (lowercase)
- Check password: `artha123`
- Verify no extra spaces
- Try logout/login again

### **Issue: Features Missing**
**Solution:**
- Refresh page: F5
- Restart application
- Check if you're logged in as admin (not employee)

---

## 🎯 PERFORMANCE CHECKS

During testing, verify:

| Metric | Expected | Your Result |
|--------|----------|-------------|
| Installer startup | <10 sec | _____ |
| Installation time | 2-3 min | _____ |
| App launch time | <2 sec | _____ |
| Login response | <1 sec | _____ |
| Add lead time | <1 sec | _____ |
| Data save time | <500ms | _____ |
| Dashboard update | <1 sec | _____ |

---

## 📊 TEST RESULTS SUMMARY

After completing all tests, rate:

| Aspect | Pass/Fail |
|--------|-----------|
| Installation | ☐ Pass ☐ Fail |
| Installer Wizard | ☐ Pass ☐ Fail |
| App Launch | ☐ Pass ☐ Fail |
| Login Screen | ☐ Pass ☐ Fail |
| Dashboard | ☐ Pass ☐ Fail |
| Add Leads | ☐ Pass ☐ Fail |
| Edit Leads | ☐ Pass ☐ Fail |
| Data Persistence | ☐ Pass ☐ Fail |
| Role-Based Access | ☐ Pass ☐ Fail |
| Export Function | ☐ Pass ☐ Fail |
| Uninstall | ☐ Pass ☐ Fail |

**Overall Result:**
- [ ] ✅ ALL TESTS PASSED - Ready for team deployment
- [ ] ⚠️ SOME ISSUES - Document below

**Issues Found (if any):**
```
1. _________________________________
2. _________________________________
3. _________________________________
```

---

## 🎉 NEXT STEPS IF TESTS PASS

1. ✅ Share installer with your team
2. ✅ Send installation instructions
3. ✅ Collect installation confirmations
4. ✅ Schedule team training
5. ✅ Start using in production!

---

## 📞 SUPPORT

**If something doesn't work:**

1. Check the Troubleshooting section above
2. Review the Installation Wizard steps
3. Try uninstalling and reinstalling
4. Check INSTALLER_READY.txt for more details
5. Report specific error messages

---

## ✨ SUCCESS CRITERIA

**The installer is working correctly if:**

✅ Installation wizard completes without errors  
✅ CRM launches after installation  
✅ Login with artha/artha123 works  
✅ Dashboard displays with stats  
✅ Can add and save leads  
✅ Data persists after closing  
✅ Export functionality works  
✅ Role-based access works (admin vs employee)  
✅ No error messages in console  

**If ALL of the above are true = Ready for production deployment!** 🚀

---

**Test Date:** _______________  
**Tested By:** _______________  
**Status:** ☐ PASSED ☐ FAILED

