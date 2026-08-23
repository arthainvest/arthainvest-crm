# 🔧 ArthaInvest CRM - Debug & Troubleshooting Guide

## ⚠️ IF YOU SEE ZEROS ON DASHBOARD

### Step 1: Open Browser Console
1. Launch the app
2. Press **F12** 
3. Click "Console" tab
4. Look for RED error messages

### Step 2: Check Demo Data Test File
1. Open: `test-dashboard.html` in a browser
2. If it shows "3 leads, 2 calls, 1 campaign" → UI works!
3. If it's blank → File issue, not data issue

### Step 3: Verify localStorage
In Console (F12), run:
```javascript
console.log(JSON.parse(localStorage.getItem('crmData')).leads)
```

**Expected Output:**
```
{
  lead_001: {name: "Rajesh Kumar", ...},
  lead_002: {name: "Priya Singh", ...},
  lead_003: {name: "Amit Patel", ...}
}
```

If empty `{}` → Data loading failed

### Step 4: Clear Cache & Retry
1. Press **Ctrl+Shift+Delete**
2. Click "Clear all"
3. Close app completely
4. Reopen app
5. Login again

---

## 🔍 COMMON ISSUES & FIXES

### Issue 1: Dashboard shows all zeros

**Cause:** Demo data not initializing

**Fix 1 - Try this in Console:**
```javascript
// Initialize demo data manually
crmData.leads = {
  lead_001: {id: 'lead_001', name: 'Rajesh Kumar', phone: '+919876543210', status: 'interested', budget: 500000, assignedTo: 'artha', createdAt: new Date().toISOString()},
  lead_002: {id: 'lead_002', name: 'Priya Singh', phone: '+919876543211', status: 'contacted', budget: 300000, assignedTo: 'ravi', createdAt: new Date().toISOString()},
  lead_003: {id: 'lead_003', name: 'Amit Patel', phone: '+919876543212', status: 'new', budget: 750000, assignedTo: 'priya', createdAt: new Date().toISOString()}
};

// Render dashboard
renderDashboard();
```

**Result:** Dashboard should update to show 3 leads

### Issue 2: "Cannot read property 'role' of undefined"

**Cause:** currentUser not set properly

**Fix:**
```javascript
currentUser = 'artha';
renderDashboard();
```

### Issue 3: Table shows "No leads yet" even after adding

**Cause:** Lead not being saved to localStorage

**Fix - Check in Console:**
```javascript
// Save data to localStorage
saveData();

// Reload dashboard
renderDashboard();
```

### Issue 4: App won't open at all

**Fix:**
1. Try portable exe: `arthainvest-crm-portable.exe`
2. Wait 10 seconds (slow start first time)
3. Check task manager for running process
4. Close and try again

---

## 📊 CONSOLE DIAGNOSTICS

Run these in F12 Console to debug:

**Check all data:**
```javascript
console.log('CRM Data:', crmData)
```

**Check leads:**
```javascript
console.log('Leads:', crmData.leads)
console.log('Lead count:', Object.keys(crmData.leads).length)
```

**Check current user:**
```javascript
console.log('Current user:', currentUser)
console.log('User role:', crmData.users[currentUser])
```

**Force render:**
```javascript
renderDashboard()
```

**Save and reload:**
```javascript
saveData()
location.reload()
```

---

## 🧪 MANUAL TEST IN CONSOLE

**Add a test lead manually:**
```javascript
crmData.leads.test_lead = {
  id: 'test_lead',
  name: 'Console Test Lead',
  phone: '+911234567890',
  email: 'test@example.com',
  status: 'interested',
  budget: 100000,
  assignedTo: 'artha',
  createdAt: new Date().toISOString()
};

saveData();
renderDashboard();
```

**Expected:** New lead appears in table + stats update

---

## ✅ VERIFICATION CHECKLIST

After each fix, verify:

- [ ] Console has no RED errors
- [ ] Dashboard shows numbers > 0
- [ ] Table shows at least 1 lead
- [ ] Statistics match: 3 leads, 2 calls, 1 campaign
- [ ] Can navigate to other sections
- [ ] Can add new lead

---

## 📞 ERROR REFERENCE

| Error | Meaning | Fix |
|-------|---------|-----|
| "Cannot read property 'leads' of undefined" | crmData not initialized | Refresh page |
| "getElementById is null" | HTML element missing | Check element IDs match |
| "currentUser is null" | Not logged in | Login first |
| "localStorage is undefined" | Browser issue | Use private/incognito mode |
| "renderDashboard is not a function" | Script not loaded | Check browser console |

---

## 🎯 IF ALL ELSE FAILS

1. **Completely close the app**
   - Force close: Ctrl+Alt+Delete → Task Manager → Close

2. **Clear everything:**
   ```javascript
   localStorage.clear()
   sessionStorage.clear()
   ```

3. **Delete localStorage file manually:**
   - Windows: `%APPDATA%\electron\cache`
   - Delete everything in that folder

4. **Reopen app fresh**
   - Click portable exe
   - Login: artha / artha123
   - Demo data should load

5. **If still broken:**
   - Uninstall completely
   - Delete: C:\Users\artha\LaptopHub\CRM_APP\dist\
   - Rebuild fresh

---

## 💡 TIPS

**Speed up testing:**
- Use Console to initialize data instead of rebuilding
- Use `localStorage.getItem('crmData')` to check what's saved
- Use `renderDashboard()` to force refresh

**Monitor app health:**
- Keep F12 Console open while testing
- Watch for errors as you interact
- Test each feature systematically

**Save time:**
- Don't reinstall if localStorage is issue
- Clear cache first (Ctrl+Shift+Delete)
- Then try login again

---

**Questions?** Check the console output first! 🔍
