# 📁 DIGILOCKER DOCUMENTS FEATURE TEST GUIDE

**Test Date:** August 7, 2026  
**Feature:** DigiLocker-Type Document Management  
**Status:** Ready for Testing

---

## 🎯 FEATURE OVERVIEW

The Documents feature allows you to organize and store client documents by folder structure:
- **Organization:** One folder per client
- **Document Types:** PAN, Aadhaar, Insurance, Bank Statement, Agreement, Invoice, Other
- **Access Control:** Employees see only their assigned clients' documents
- **Metadata:** Each document tracks upload timestamp and uploader name

---

## 📋 PRE-TEST CHECKLIST

Before starting tests, verify:

- [ ] CRM is installed: `C:\Program Files\ArthaInvest CRM\`
- [ ] CRM executable exists: `ArthaInvest CRM.exe`
- [ ] Installer files built: 
  - [ ] `arthainvest-crm-setup.exe` (64.81 MB)
  - [ ] `arthainvest-crm-portable.exe` (64.60 MB)

---

## 🚀 LAUNCHING THE CRM FOR DOCUMENTS TESTING

### **Step 1: Start the Application**
```
Double-click: C:\Program Files\ArthaInvest CRM\ArthaInvest CRM.exe
Wait: 2-3 seconds for window to open
```

### **Step 2: Login**
```
Username: artha
Password: artha123
```

**Expected Result:**
- ✅ Dashboard appears with login successful
- ✅ Sidebar shows all menu items including "Documents"

---

## ✅ TEST 1: VERIFY DOCUMENTS MENU ITEM

**Purpose:** Confirm Documents navigation item is visible

**Steps:**
1. After login, look at left sidebar
2. Find "📁 Documents" menu item
3. Click "📁 Documents"

**Expected Results:**
- ✅ Page title changes to: "Client Documents"
- ✅ Main content area shows document management interface
- ✅ No errors in console (F12 → Console tab)

**Verify in Sidebar:**
```
GENERAL
  • Dashboard
  • All Leads
  • Team Members

ANALYTICS
  • Reports
  • 📁 Documents  ← NEW

ADMIN (Admin Only)
  • Manage Users
  • Settings
```

---

## ✅ TEST 2: ADD SAMPLE LEAD (PREREQUISITE)

Before testing document upload, create a sample client/lead:

**Steps:**
1. Click "All Leads"
2. Click "+ Add Lead"
3. Fill form with:
   - **Name:** Test Client
   - **Phone:** 9876543210
   - **Email:** client@test.com
   - **Status:** New
   - **Budget:** Test Budget
4. Click "Save Lead"

**Expected Result:**
- ✅ Lead appears in list
- ✅ Dashboard shows "Total Leads: 1"

---

## ✅ TEST 3: OPEN DOCUMENTS SECTION

**Purpose:** Verify Documents section displays and is interactive

**Steps:**
1. Click "📁 Documents" in sidebar
2. Observe the Documents area

**Expected Result:**
```
📁 Client Documents
Organize and store client documents by category

[Empty state message or client list]
```

**What You Should See:**
- ✅ Header: "📁 Client Documents"
- ✅ Subheader: "Organize and store client documents by category"
- ✅ Either empty state OR list of clients with document counts

---

## ✅ TEST 4: UPLOAD A DOCUMENT (MAIN TEST)

**Purpose:** Test document upload functionality

**Prerequisites:**
- At least one lead/client created (Test Client)
- Documents section open

**Steps:**

### **Finding the Upload Button**
1. In Documents section, find "Test Client" entry
2. Look for an upload button (usually "+ Add Document" or upload icon)
3. Click to open upload modal

### **Filling the Upload Form**
```
Modal Title: "Add Document"

Field 1: Document Name
Input: "PAN Card - Test Client"

Field 2: Document Type
Select: "PAN" from dropdown

Field 3: Document Upload
Input: (In current version, document metadata only)
```

### **Submitting**
1. Click "Upload Document" button
2. Wait for response

**Expected Results:**
- ✅ Modal closes after submission
- ✅ Alert shows: "✅ Document uploaded successfully!"
- ✅ Document appears in client's folder
- ✅ Shows upload timestamp
- ✅ Shows uploader: "ArthaInvest Admin"

---

## ✅ TEST 5: VIEW UPLOADED DOCUMENTS

**Purpose:** Verify documents are stored and displayed

**Steps:**
1. In Documents section, click on "Test Client"
2. Expand client's document folder
3. Look for your uploaded document

**Expected Display:**
```
Test Client
  📄 PAN Card - Test Client
     Type: PAN
     Uploaded: [Timestamp]
     By: ArthaInvest Admin
     [Delete button]
```

**Verify:**
- ✅ Document name appears
- ✅ Document type shown
- ✅ Upload timestamp visible
- ✅ Uploader name shows "ArthaInvest Admin"
- ✅ Delete button present

---

## ✅ TEST 6: UPLOAD MULTIPLE DOCUMENTS

**Purpose:** Test multiple uploads for same client

**Steps:**
1. Open Documents section
2. Upload 3 documents for "Test Client":
   - **Doc 1:** "Aadhaar Card" (Type: Aadhaar)
   - **Doc 2:** "Bank Statement" (Type: Bank)
   - **Doc 3:** "Insurance Policy" (Type: Insurance)

**Expected Results:**
- ✅ All 3 uploads succeed
- ✅ All appear under "Test Client" folder
- ✅ Each shows correct type badge

**Display Should Show:**
```
Test Client
  📄 PAN Card - Test Client [PAN] [Delete]
  📄 Aadhaar Card [Aadhaar] [Delete]
  📄 Bank Statement [Bank] [Delete]
  📄 Insurance Policy [Insurance] [Delete]
```

---

## ✅ TEST 7: DELETE A DOCUMENT

**Purpose:** Test document deletion

**Steps:**
1. In Documents section, find "Aadhaar Card" document
2. Click [Delete] button
3. Confirm deletion if prompted

**Expected Results:**
- ✅ Deletion prompt appears
- ✅ Document removed from list
- ✅ Remaining documents still visible
- ✅ No error messages

**After Deletion - Should Show 3 Documents:**
```
Test Client
  📄 PAN Card - Test Client [PAN] [Delete]
  📄 Bank Statement [Bank] [Delete]
  📄 Insurance Policy [Insurance] [Delete]
```

---

## ✅ TEST 8: ROLE-BASED ACCESS (ADMIN vs EMPLOYEE)

**Purpose:** Verify employees can't see admin-only documents

**Steps:**

### **As Admin (artha/artha123):**
1. Currently logged in as Admin
2. Go to Documents
3. Verify documents visible

### **Switch to Employee:**
1. Click Logout
2. Login as: **ravi / ravi123**
3. Go to Documents section
4. Check visibility

**Expected Results:**
- ✅ Admin sees all client documents
- ✅ Employee sees only assigned leads' documents
- ✅ Documents section available to both roles

**Employee View Should Show:**
```
Documents assigned to you:
[Only clients assigned to Ravi visible]
```

---

## ✅ TEST 9: DATA PERSISTENCE

**Purpose:** Verify documents persist after app restart

**Steps:**
1. With documents uploaded, close the CRM
2. Wait 2 seconds
3. Reopen: `C:\Program Files\ArthaInvest CRM\ArthaInvest CRM.exe`
4. Login again: artha / artha123
5. Go to Documents

**Expected Results:**
- ✅ CRM opens normally
- ✅ All documents still visible
- ✅ No data loss
- ✅ Metadata (timestamps, types) preserved

---

## ✅ TEST 10: ADD LEAD AND DOCUMENTS FOR MULTIPLE CLIENTS

**Purpose:** Test multi-client document management

**Steps:**

### **Add Second Client:**
1. Go to "All Leads"
2. Click "+ Add Lead"
3. Add: **Name:** Client Two, **Phone:** 8765432109
4. Save

### **Add Documents for Client Two:**
1. Go to Documents
2. Upload to "Client Two":
   - "GST Certificate" (Type: Other)
   - "Identity Proof" (Type: Aadhaar)

### **Verify:**
```
Test Client
  📄 PAN Card - Test Client [PAN]
  📄 Bank Statement [Bank]
  📄 Insurance Policy [Insurance]

Client Two
  📄 GST Certificate [Other]
  📄 Identity Proof [Aadhaar]
```

**Expected Results:**
- ✅ Both clients appear
- ✅ Each has separate folder
- ✅ No cross-contamination of documents
- ✅ All documents properly organized

---

## 🧪 BRANDING VERIFICATION

**Purpose:** Confirm rebranding to "ArthaInvest Admin"

**Steps:**
1. After login, check top-right user info
2. Look for admin name display

**Expected:**
- ✅ Shows "ArthaInvest Admin" (NOT "Artha Kumar")
- ✅ Dashboard shows correct branding
- ✅ Document uploader field shows "ArthaInvest Admin"

---

## 📊 COMPREHENSIVE TEST CHECKLIST

### **Navigation & UI**
- [ ] Documents menu item visible in sidebar
- [ ] Clicking Documents navigates to section
- [ ] Page title updates to "Client Documents"
- [ ] No console errors (F12)

### **Document Upload**
- [ ] Upload modal opens
- [ ] Form fields visible (Name, Type)
- [ ] Document type dropdown has all options
- [ ] Upload button submits form
- [ ] Success message appears

### **Document Display**
- [ ] Documents appear under correct client
- [ ] Upload timestamp displays
- [ ] Document type shown correctly
- [ ] Uploader name shows "ArthaInvest Admin"
- [ ] Multiple documents organize properly

### **Document Deletion**
- [ ] Delete button visible
- [ ] Delete confirmation works
- [ ] Document removed from list
- [ ] Other documents remain intact

### **Role-Based Access**
- [ ] Admins see all client documents
- [ ] Employees see assigned clients only
- [ ] No unauthorized access

### **Data Persistence**
- [ ] Documents survive app restart
- [ ] All metadata preserved
- [ ] No data corruption

### **Branding**
- [ ] Admin name shows "ArthaInvest Admin"
- [ ] Uploader shows "ArthaInvest Admin"
- [ ] All branding updated correctly

### **Performance**
- [ ] Upload completes in <1 second
- [ ] Delete completes in <1 second
- [ ] No lag during navigation
- [ ] App remains responsive

---

## 📋 TEST RESULTS SUMMARY

After completing all tests, rate each:

| Test | Result | Notes |
|------|--------|-------|
| Documents Menu | ☐ Pass ☐ Fail | |
| Upload Document | ☐ Pass ☐ Fail | |
| View Documents | ☐ Pass ☐ Fail | |
| Delete Document | ☐ Pass ☐ Fail | |
| Multiple Documents | ☐ Pass ☐ Fail | |
| Role-Based Access | ☐ Pass ☐ Fail | |
| Data Persistence | ☐ Pass ☐ Fail | |
| Multi-Client Docs | ☐ Pass ☐ Fail | |
| Branding Check | ☐ Pass ☐ Fail | |
| Performance | ☐ Pass ☐ Fail | |

**Overall Status:**
- [ ] ✅ ALL TESTS PASSED - Ready for team deployment
- [ ] ⚠️ SOME ISSUES FOUND - See details below

---

## ⚠️ ISSUES FOUND (If Any)

```
Issue 1: _________________________________
Description: ____________________________
Severity: High / Medium / Low
Fix: _____________________________________

Issue 2: _________________________________
Description: ____________________________
Severity: High / Medium / Low
Fix: _____________________________________
```

---

## 🎯 SUCCESS CRITERIA

**The Documents feature is working correctly if:**

✅ Documents menu item visible in sidebar  
✅ Can upload documents with name and type  
✅ Documents organized by client folder  
✅ Upload timestamp and metadata preserved  
✅ Delete functionality works  
✅ Role-based access enforced  
✅ Documents persist after app restart  
✅ Branding shows "ArthaInvest Admin"  
✅ No console errors  
✅ Performance is responsive  

**If ALL criteria met = Ready for Production!** 🚀

---

## 📞 TROUBLESHOOTING

### **Issue: Documents menu doesn't appear**
**Solution:**
- Refresh page (F5)
- Restart CRM application
- Verify latest build: `npm run build-win`

### **Issue: Upload fails silently**
**Solution:**
- Check console (F12) for errors
- Verify lead/client exists first
- Try uploading with simple name (no special chars)

### **Issue: Uploaded documents don't appear**
**Solution:**
- Refresh page (F5)
- Close and reopen Documents section
- Check if correct client selected
- Restart app

### **Issue: Documents disappear after restart**
**Solution:**
- Check AppData folder: `%LOCALAPPDATA%\arthainvest-crm\`
- Verify data file exists: `crm_data.json`
- Reinstall if data corrupted

### **Issue: Role-based access not working**
**Solution:**
- Logout and login as employee account
- Employee must have leads assigned
- Check console for access control errors

---

## 🚀 NEXT STEPS

If all tests pass:

1. ✅ Documents feature fully tested
2. ✅ Ready to share installer with team
3. ✅ Team can start using on their laptops
4. ✅ Document management workflow ready

If issues found:

1. ⚠️ Document issues found
2. ⚠️ Fix in app.js or index.html
3. ⚠️ Rebuild: `npm run build-win`
4. ⚠️ Retest with new build

---

## 📝 TEST LOG

**Tester Name:** ___________________  
**Test Date:** ___________________  
**Test Time:** ___________________  
**Build Version:** 2.0.0  
**Overall Result:** ☐ PASSED ☐ FAILED  

**Notes:**
```
_____________________________________________
_____________________________________________
_____________________________________________
```

---

**ArthaInvest CRM v2.0.0 - Documents Feature Test**  
**Status: READY FOR TESTING** ✅

---

Good luck with your testing! The Documents feature should provide your team with a complete DigiLocker-type solution for client document management. 🎉
