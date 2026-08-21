# 📚 ArthaInvest CRM - Role-Based Training Manual

**Training Version:** 1.0  
**Date:** 2026-08-18  
**Audience:** Admin, Team Leader, Sales Employees

---

## 🎯 TRAINING OVERVIEW

This manual provides role-specific training for all ArthaInvest CRM users. Each section covers one role with step-by-step instructions, best practices, and practical exercises.

### Training Objectives
- ✅ Understand CRM features relevant to your role
- ✅ Master daily workflows and processes
- ✅ Use the system efficiently for maximum productivity
- ✅ Know when and how to escalate issues
- ✅ Support team members and customers effectively

### Training Modules
1. **Administrator Training** (Full System Control)
2. **Team Leader Training** (Team Supervision & Reporting)
3. **Sales Employee Training** (Daily Operations)

**Estimated Training Time:**
- Admin: 4-5 hours
- Team Leader: 3-4 hours
- Employee: 2-3 hours

---

# 👑 MODULE 1: ADMINISTRATOR TRAINING

## Role Overview

**Responsibilities:**
- System setup and configuration
- User management and permissions
- Data import/export operations
- Integration credentials management
- System monitoring and maintenance
- Reporting and analytics
- Backup and security

**Access Level:** Full System Access

---

## 1.1 SYSTEM ACCESS & LOGIN

### Step 1: Open the CRM Application

```
1. Double-click: ArthaInvest_CRM_COMPLETE.html
2. Browser opens automatically
3. Login page appears
```

### Step 2: Admin Login

**Credentials:**
- Email: `admin@arthainvest.com`
- Password: `admin123`
- Role: Administrator (select from dropdown)

**Result:** Full dashboard with all features enabled

---

## 1.2 ADMIN DASHBOARD OVERVIEW

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ ADMIN DASHBOARD                                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Sidebar Menu (Left):                                  │
│  ├── Dashboard                                         │
│  ├── Contacts                                          │
│  ├── Pipeline                                          │
│  ├── Calls & Follow-ups                                │
│  ├── Team                                              │
│  ├── Reports                                           │
│  ├── DigiLocker                                        │
│  ├── Marketing                                         │
│  └── Integrations (ADMIN ONLY)                         │
│                                                          │
│  Top Right:                                            │
│  ├── Theme Toggle (Light/Dark)                         │
│  └── Logout Button                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Admin Exclusive Features

1. **Contacts → Import Button**
   - Admin-only feature
   - Bulk upload customer data
   - CSV import support

2. **Integrations Page**
   - View all connected services
   - Edit credential information
   - Admin-only access

3. **Reports Page**
   - View all employee performance
   - Access detailed analytics
   - Export data (Admin-only)

---

## 1.3 USER MANAGEMENT

### Creating New User Accounts

**Current Users:**
```
Admin Account (You):
├── Email: admin@arthainvest.com
├── Password: admin123
└── Access Level: Full System

Team Leader:
├── Name: Rajesh Kumar
├── Email: rajesh@arthainvest.com
├── Role: Team Leader
└── Direct Reports: 4 Employees

Employees (4):
├── Arjun Sharma (arjun@arthainvest.com)
├── Priya Singh (priya@arthainvest.com)
├── Vikram Patel (vikram@arthainvest.com)
└── Neha Desai (neha@arthainvest.com)
```

**To Modify User Access:**
1. Go to **Integrations** page
2. Scroll to **Credential Management** section
3. Click **Edit** button next to user
4. Modify email/password (use strong passwords)
5. Click **Save Credentials**

**Best Practice:**
- Use strong passwords (12+ characters, mix of letters/numbers/symbols)
- Change default passwords immediately
- Don't share credentials
- Document password securely

---

## 1.4 DATA MANAGEMENT

### Importing Customer Data

**Step 1: Prepare Data**
```
Required CSV Format:
NAME, EMAIL, PHONE, COMPANY, STATUS

Example:
John Doe, john@example.com, +91 98765 43210, ABC Corp, Active
Jane Smith, jane@example.com, +91 87654 32109, XYZ Ltd, Active
```

**Step 2: Import Process**
1. Go to **Contacts** page
2. Click **Import** button (Admin-only)
3. Select CSV file from computer
4. Verify data preview
5. Click **Import** to complete

**Step 3: Verification**
- Check contact count increased
- Verify data accuracy
- Ensure no duplicates created

**Common Issues:**
```
Issue: "Invalid format" error
Solution: Ensure CSV headers match exactly:
          NAME, EMAIL, PHONE, COMPANY, STATUS

Issue: Duplicate entries created
Solution: Check for existing contacts before import
          Use unique identifiers (email/phone)

Issue: Missing data in some fields
Solution: Ensure all required fields populated
          Use placeholder values if needed
```

---

## 1.5 INTEGRATION CREDENTIALS MANAGEMENT

### Viewing Connected Integrations

**Location:** Integrations page (Admin-only)

**Connected Services:**
```
┌─────────────────────────────────────────────────┐
│ INTEGRATION CREDENTIALS                          │
├─────────────────────────────────────────────────┤
│                                                  │
│ WhatsApp Business API                           │
│ ├── Phone: +91-98765-43210                      │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
│ Twilio Click-to-Call                            │
│ ├── Phone: +91-87654-32109                      │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
│ Email Service                                   │
│ ├── Email: support@arthainvest.com              │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
│ LinkedIn Campaign Manager                       │
│ ├── Email: artha@arthainvest.com                │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
│ Razorpay Payments                               │
│ ├── Email: payments@arthainvest.com             │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
│ DigiLocker Documents                            │
│ ├── Email: documents@arthainvest.com            │
│ ├── Status: Connected ✓                         │
│ ├── Last Active: 2026-08-18                     │
│ └── Edit Button                                 │
│                                                  │
└─────────────────────────────────────────────────┘
```

### Editing Integration Credentials

**Step 1: Click Edit Button**
- Modal dialog opens
- Shows current credential values

**Step 2: Update Information**
- Modify credential value
- Ensure accuracy (copy from integration provider)

**Step 3: Save Changes**
- Click "Save Credential"
- System confirms update
- Change effective immediately

**Example: Update WhatsApp Phone Number**
```
Old: +91-98765-43210
New: +91-98765-11111

Steps:
1. Click Edit next to "WhatsApp Business API"
2. Clear current value
3. Enter new phone number
4. Click "Save Credential"
5. Verify change saved (shows new number)
```

**Security Note:**
- Only Admin can view/edit credentials
- Credentials are securely stored
- Regular credential updates recommended
- Never share credentials via email/chat

---

## 1.6 REPORTS & ANALYTICS

### Accessing Admin Reports

**Location:** Reports page (Admin-only view)

**Available Reports:**
```
1. EMPLOYEE PERFORMANCE REPORT
   ├── Name, Role, Phone, Email
   ├── Total Leads Assigned
   ├── Deals Closed This Month
   ├── Revenue Generated
   ├── Performance Trends
   └── Commission Calculation

2. PIPELINE HEALTH REPORT
   ├── Stage-wise deal count
   ├── Revenue by stage
   ├── Average deal size
   ├── Bottleneck identification
   └── Conversion rates

3. REVENUE REPORT
   ├── Monthly revenue
   ├── Revenue by employee
   ├── Revenue by deal stage
   ├── Forecast accuracy
   └── Growth trends

4. FOLLOW-UP REPORT
   ├── Follow-up completion rate
   ├── FWP status distribution
   ├── Response time metrics
   └── Team efficiency
```

### Running Custom Reports

**Step 1: Select Report Type**
- Choose from available report templates

**Step 2: Set Date Range**
- Pick start date (e.g., 2026-08-01)
- Pick end date (e.g., 2026-08-18)

**Step 3: Generate Report**
- Click "Generate Report" button
- Data compiled and displayed

**Step 4: Export Data (Admin-only)**
- Click "Export to CSV" button
- File downloads to computer
- Use for external analysis/sharing

---

## 1.7 SYSTEM MONITORING

### Daily Admin Tasks

**Morning Checklist:**
```
Before 9:00 AM:
□ Check system status
□ Review overnight activity
□ Verify all integrations connected
□ Check for error logs
□ Preview reports for team
```

**Weekly Tasks:**
```
Every Monday:
□ Review past week's metrics
□ Check team performance trends
□ Verify data integrity
□ Backup data (manual trigger)
□ Update credentials if needed
```

**Monthly Tasks:**
```
Every 1st of Month:
□ Generate full monthly reports
□ Review employee performance
□ Plan optimization actions
□ Audit user access
□ Update training materials
□ Plan for next month
```

### Monitoring Performance Metrics

**Key Metrics to Watch:**
```
System Health:
├── Page load time: Should be < 2 seconds
├── Data save time: Should be < 1 second
├── No error messages: Check console
└── All features responsive

Data Integrity:
├── No duplicate entries
├── All required fields populated
├── Consistent data format
└── No missing customer records

Integration Status:
├── All services showing "Connected"
├── Credentials valid and active
├── No failed API calls
└── Data syncing properly
```

---

## 1.8 BACKUP & DATA SECURITY

### Data Backup

**Browser Local Storage:**
- CRM data stored locally in browser
- Automatic save on every change
- Persists across browser sessions

**Manual Backup Recommendation:**
```
1. Go to Dashboard
2. Take screenshot of KPI cards
3. Go to Contacts → Export contacts (if feature available)
4. Go to Pipeline → Note all deals
5. Go to Reports → Download all reports
6. Store files in cloud backup (Google Drive, OneDrive)
```

**Backup Frequency:**
- Daily: Screenshot dashboard metrics
- Weekly: Export full reports
- Monthly: Full system backup

### Data Security Best Practices

```
Password Management:
✓ Use strong passwords (12+ characters)
✓ Change passwords every 90 days
✓ Don't share passwords
✓ Use password manager (LastPass, 1Password)
✗ Don't store passwords in email/chat
✗ Don't share via unsecured channels

Access Control:
✓ Audit user access quarterly
✓ Remove access immediately for departing staff
✓ Limit credentials to those who need them
✓ Use role-based access (already configured)
✗ Don't give admin access to non-admins

Data Privacy:
✓ Limit data visibility per role
✓ Don't share customer data externally
✓ Follow compliance requirements
✓ Document data access
✗ Don't export sensitive data insecurely
✗ Don't discuss customer data in public
```

---

## 1.9 TROUBLESHOOTING & SUPPORT

### Common Admin Issues

**Issue 1: User Can't Login**
```
Symptoms: "Invalid credentials" error
Solution:
1. Verify email is correct (case-sensitive)
2. Reset password to default (admin123)
3. Have user change password on first login
4. Check browser cache (clear if needed)
5. Try different browser
```

**Issue 2: Data Import Failed**
```
Symptoms: "Invalid format" or "Import error"
Solution:
1. Verify CSV format matches template
2. Check for special characters in data
3. Ensure no blank rows in CSV
4. Try importing in smaller batches
5. Check file encoding (UTF-8)
```

**Issue 3: Integrations Showing Disconnected**
```
Symptoms: "Status: Not Connected" appears
Solution:
1. Verify credentials are correct
2. Re-enter credential values
3. Check internet connection
4. Clear browser cache
5. Try in different browser
6. Contact integration provider
```

**Issue 4: Data Not Saving**
```
Symptoms: Changes disappear on refresh
Solution:
1. Check browser allows localStorage
2. Verify sufficient storage space
3. Try in incognito/private mode
4. Check for JavaScript errors (F12 console)
5. Clear browser cache and cookies
```

### Admin Support Contacts

**Internal Support:**
- Email: support@arthainvest.com
- Phone: +91-98765-11111
- Hours: Monday-Friday, 9 AM - 6 PM IST

**Integration Support:**
- WhatsApp: +91-98765-43210
- Twilio: +91-87654-32109
- Email: support@arthainvest.com

---

## 📋 ADMIN TRAINING CHECKLIST

- [ ] Completed login with admin credentials
- [ ] Explored all 9 CRM pages
- [ ] Understood admin-only features (Import, Integrations, Reports)
- [ ] Practiced importing sample data
- [ ] Reviewed all integration credentials
- [ ] Generated at least one report
- [ ] Understood backup procedures
- [ ] Learned troubleshooting steps
- [ ] Know escalation contacts
- [ ] Tested dark/light theme toggle

**Training Sign-off:** _________________ Date: _______

---

---

# 👔 MODULE 2: TEAM LEADER TRAINING

## Role Overview

**Responsibilities:**
- Team supervision and guidance
- Lead assignment to employees
- Team performance tracking
- Quality assurance and coaching
- Daily operations oversight
- Supporting employee success
- Escalating blockers

**Access Level:** Team/Report View (Limited Admin Features)

---

## 2.1 TEAM LEADER LOGIN

### Credentials

```
Email: rajesh@arthainvest.com
Password: (Set by Admin)
Role: Team Leader (select from dropdown)
```

### Dashboard View (Team Leader)

```
┌─────────────────────────────────────────────────────────┐
│ TEAM LEADER DASHBOARD                                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Sidebar Menu (Limited):                                │
│ ├── Dashboard (View all KPIs)                          │
│ ├── Contacts (Import only, no export)                  │
│ ├── Pipeline (Full view for assignment)                │
│ ├── Calls & Follow-ups (Full view)                     │
│ ├── Team (View all employees + profiles)               │
│ ├── Reports (View employee performance)                │
│ ├── DigiLocker (View assigned folders)                 │
│ ├── Marketing (View campaigns)                         │
│ └── Integrations (VIEW ONLY - no edit)                 │
│                                                          │
│ Key Differences from Admin:                             │
│ - Cannot edit integration credentials                  │
│ - Cannot export data                                   │
│ - Cannot modify user accounts                          │
│ - Full visibility into team performance               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 2.2 DAILY TEAM LEADER WORKFLOW

### Morning (9:00-10:00 AM)

**Step 1: Review Dashboard Metrics** (5-10 min)
```
Open: Dashboard page
Check:
├── Total Deals Closed This Month: Is it on track?
├── In Progress Deals: Any stuck deals?
├── Rejected Deals: Any concerns?
├── On Hold Deals: Need follow-up?
├── Pipeline Value: Are we hitting target?
└── KPI Trends: Going up or down?

Action:
If metrics down:
- Plan team meeting to discuss challenges
- Identify blockers and obstacles
- Allocate additional support
- Adjust strategy if needed
```

**Step 2: Check Team Status** (10-15 min)
```
Open: Team page
Review:
├── Arjun Sharma: Leads assigned? On track?
├── Priya Singh: Leads assigned? On track?
├── Vikram Patel: Leads assigned? On track?
└── Neha Desai: Leads assigned? On track?

Click on each employee card to view:
├── Total leads assigned
├── Deals closed
├── Revenue generated
├── Performance trend
└── Personal metrics
```

**Step 3: Assign Leads** (15-20 min)
```
Open: Pipeline page
Review:
├── "New Leads" stage: Which leads are unassigned?
├── Consider: Who should get this lead?
├── Factors:
│   ├── Employee workload (leads assigned)
│   ├── Lead complexity (match with skill)
│   ├── Geographic preference
│   └── Customer industry fit

Action:
1. Click on unassigned lead
2. Note customer details
3. Assign to most suitable employee
4. Add note: "Assigned - customer ready"
5. Set follow-up reminder
```

---

### Midday (12:00-1:00 PM)

**Step 1: Support Struggling Employees** (15-20 min)
```
Review Reports page:
├── Identify: Who's below target?
├── Analyze: What's the issue?
│   ├── Too few leads assigned?
│   ├── Long follow-up time?
│   ├── Low conversion rate?
│   └── Skill gap?

Take Action:
├── One-on-one coaching session
├── Review recent calls/interactions
├── Provide feedback and guidance
├── Assign additional training if needed
└── Set performance improvement goal
```

**Step 2: Celebrate Wins** (5 min)
```
Review Reports page:
├── Identify: Who's exceeding target?
├── Recognize: Send appreciation message
├── Learn: What are they doing right?
└── Share: Best practices with team
```

**Step 3: Check Pipeline Health** (10-15 min)
```
Open: Pipeline page
Identify "stuck" deals:
├── Deals unchanged for 5+ days
├── Status in "On Hold" for long time
├── Proposal sent but no response

For each stuck deal:
1. Review full deal history
2. Identify blocking issue
3. Add comment: "Following up today"
4. Reach out to customer personally
5. Escalate if needed
```

---

### Afternoon (4:00-5:00 PM)

**Step 1: Review Daily Activity** (10-15 min)
```
Open: Calls & Follow-ups page
Check:
├── How many calls made today?
├── Follow-up status updated?
├── All clients have contact attempt?
├── FWP status clearly set?

Verify:
├── "Interested" leads → Scheduled follow-up
├── "In Process" leads → Timeline set
├── "Not Interested" leads → Archived
└── "No Response" leads → Escalated
```

**Step 2: Plan Next Day** (10-15 min)
```
Prepare for tomorrow:
├── Preview new leads coming in
├── Plan lead assignments
├── Identify potential bottlenecks
├── Schedule team touchpoints
└── Note any special customer needs

Send team message:
"Tomorrow's plan: Focus on ABC Corp proposal follow-up.
 New leads assigned: 4 leads to Arjun, 3 to Priya.
 Morning call at 9:30 AM to align."
```

---

## 2.3 TEAM PERFORMANCE TRACKING

### Weekly Performance Review

**Every Friday Afternoon:**

**Step 1: Generate Weekly Reports**
```
Open: Reports page
Generate:
├── Weekly employee performance
├── Revenue by employee
├── Deals closed by employee
├── Average deal size
└── Conversion rate

Note: Week-over-week trends
```

**Step 2: Individual Employee Review**

**For Each Employee:**
```
Name: Arjun Sharma

Weekly Metrics:
├── Leads Assigned: 8
├── Contacts Made: 7 (88%)
├── Deals Closed: 2
├── Revenue: ₹8,50,000
├── Conversion Rate: 25%
├── Avg Deal Size: ₹42.5L
└── Avg Days to Close: 15 days

Performance vs Target:
├── Target Revenue: ₹10L
├── Actual: ₹8.5L
├── Gap: -13% (slightly below)
└── Trend: ↑ Improving (up from ₹7L last week)

Coaching Points:
├── Strength: Fast closing (15 days avg)
├── Growth: Increase proposal conversion
├── Action: Role-play proposal techniques
└── Support: Shadowing with top performer
```

---

## 2.4 LEAD ASSIGNMENT STRATEGY

### Best Practices for Lead Distribution

**Consider These Factors:**

1. **Workload Balance**
   ```
   Current Leads Assigned:
   ├── Arjun: 28 leads
   ├── Priya: 32 leads
   ├── Vikram: 25 leads
   └── Neha: 30 leads
   
   Next new lead assignment:
   → Give to Vikram (lowest count)
   → Ensure no one overwhelmed
   → Rotate distribution
   ```

2. **Lead Complexity vs Skill**
   ```
   Lead: ABC Corp (large enterprise, complex)
   → Assign to: Priya Singh (highest conversion)
   
   Lead: Small retail store (simple)
   → Assign to: Arjun (good at speed)
   
   Lead: New industry segment
   → Assign to: Rajesh (Team Leader expertise)
   ```

3. **Customer Geographic/Industry Fit**
   ```
   Lead: Tech startup in Bangalore
   → Assign to: Employee with tech experience
   
   Lead: Manufacturing in Delhi
   → Assign to: Employee familiar with manufacturing
   
   Lead: Financial services in Mumbai
   → Assign to: Top performer (high value)
   ```

4. **Development Opportunity**
   ```
   Employee: Vikram (needs proposal skills)
   Lead: Good for learning (mid-size, clear need)
   → Assign with: Coaching plan and support
   ```

---

## 2.5 COACHING & DEVELOPMENT

### Performance Coaching Framework

**Situation: Employee Below Target**

```
Step 1: Diagnose the Issue
├── Review their recent activity
├── Check call quality notes
├── Look at customer feedback
├── Identify specific problem area
└── Example: "Proposals taking too long"

Step 2: Have Coaching Conversation
├── "I noticed your proposals take 5 days."
├── "What's making the process slow?"
├── "What support do you need?"
├── "Let's work on this together."
└── Active listening

Step 3: Create Improvement Plan
├── Specific goal: "Reduce to 2 days"
├── Action steps: "Use templates, get feedback faster"
├── Timeline: "Achieve by August 30"
├── Support: "I'll review first 3 proposals"
└── Accountability: "Check-in Friday"

Step 4: Support & Follow-up
├── Daily: Answer questions, remove blockers
├── Weekly: Review progress, celebrate wins
├── Monitor: Track improvements
└── Adjust: Modify plan if not working

Step 5: Recognize Improvement
├── "Great work cutting proposal time!"
├── "This approach is working - keep it up"
├── "You're now on pace to hit target"
└── Share success with team
```

---

## 2.6 ESCALATION PROCEDURES

### When to Escalate to Admin

**Escalate These Situations:**

```
1. SYSTEM ISSUES
   ├── CRM page not loading
   ├── Data not saving
   ├── Features not working
   └── Action: Email support@arthainvest.com

2. DATA PROBLEMS
   ├── Duplicate customer entries
   ├── Data corruption
   ├── Missing records
   └── Action: Contact Admin immediately

3. INTEGRATION ISSUES
   ├── WhatsApp not connecting
   ├── Calls not working
   ├── Email not sending
   └── Action: Admin needs to re-verify credentials

4. ACCESS ISSUES
   ├── Employee can't login
   ├── Feature access denied
   ├── Permission problems
   └── Action: Admin needs to check user settings

5. COMPLIANCE ISSUES
   ├── Data security concern
   ├── Privacy violation
   ├── Audit requirement
   └── Action: Escalate to Admin immediately
```

---

## 📋 TEAM LEADER TRAINING CHECKLIST

- [ ] Logged in with Team Leader credentials
- [ ] Reviewed all team member performance
- [ ] Practiced assigning leads
- [ ] Generated performance reports
- [ ] Understood role limitations vs Admin
- [ ] Learned daily/weekly workflow
- [ ] Practiced coaching conversation
- [ ] Know escalation procedures
- [ ] Reviewed team metrics
- [ ] Can access all allowed features

**Training Sign-off:** _________________ Date: _______

---

---

# 👨 MODULE 3: SALES EMPLOYEE TRAINING

## Role Overview

**Responsibilities:**
- Convert assigned leads into customers
- Follow up with prospects systematically
- Update customer status in CRM
- Document all interactions
- Achieve monthly targets
- Support team members
- Maintain customer satisfaction

**Access Level:** Own Data + Assigned Leads (Limited View)

---

## 3.1 EMPLOYEE LOGIN

### Credentials

```
Example (Arjun Sharma):
Email: arjun@arthainvest.com
Password: (Set by Admin)
Role: Employee (select from dropdown)
```

### Dashboard View (Employee)

```
┌─────────────────────────────────────────────────────────┐
│ SALES EMPLOYEE DASHBOARD                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Sidebar Menu (Limited):                                │
│ ├── Dashboard (My KPIs only)                           │
│ ├── Contacts (Import only)                             │
│ ├── Pipeline (My assigned leads)                       │
│ ├── Calls & Follow-ups (My activities)                 │
│ ├── Team (View profiles, no data)                      │
│ ├── Reports (My performance)                           │
│ ├── DigiLocker (My assigned folders)                   │
│ ├── Marketing (View campaigns)                         │
│ └── Integrations (BLOCKED - no access)                 │
│                                                          │
│ Key Features Available:                                 │
│ - See only my assigned leads and customers            │
│ - Track my personal performance                        │
│ - Use communication tools                              │
│ - Access my documents                                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 3.2 YOUR DAILY WORKFLOW

### Morning (9:00-10:00 AM)

**Step 1: Check Your Dashboard** (5 min)
```
Open: Dashboard page
Review YOUR metrics:
├── My Target This Month: ₹?
├── My Revenue So Far: ₹?
├── My Deals Closed This Month: ?
├── My Current Pipeline: ₹?
└── Am I on track?

Think:
"Do I need to close X more deals to hit target?"
"How many days left in month?"
"What do I need to do?"
```

**Step 2: View Your Assigned Leads** (10-15 min)
```
Open: Pipeline page
You see ONLY your assigned leads

Review each lead:
├── Customer Name & Company
├── Deal Amount
├── Current Stage (Contacted, Interested, Proposal, etc.)
├── Days at current stage
├── Last interaction date
└── Next action required

Example:
Customer: ABC Corp
Amount: ₹25L
Stage: "Interested" (3 days)
Last Contact: 2 days ago (email)
Next Action: Call today to discuss proposal

Action:
"ABC Corp needs follow-up today"
→ Add to today's call list
```

**Step 3: Plan Today's Activities** (10-15 min)
```
Create your daily action list:

Morning (9-12):
├── Call ABC Corp (follow-up)
├── Send proposal to XYZ Ltd
├── Email Tech Solutions (questions)
└── WhatsApp: Follow-up on proposal

Afternoon (12-5):
├── Meet with Team Leader (coaching)
├── Calls to 5 new leads
├── Email follow-ups
└── Document all interactions

Evening (5-6):
├── Update all statuses in CRM
├── Add notes on calls
├── Set follow-up reminders
└── Close day with Win/Loss analysis
```

---

### During Day: Making Calls & Following Up

**Step 1: Click-to-Call Feature**

```
Open: Calls & Follow-ups page
Click: ☎️ Call button next to customer

What happens:
├── Your phone app opens
├── Customer number auto-dialed
├── Call connects
├── You have conversation
└── Interaction logged in CRM

After call:
├── Note what customer said
├── Set FWP status (Interested/In Process/etc)
├── Schedule next follow-up
└── Add any required action
```

**Step 2: Send WhatsApp Message**

```
Open: Calls & Follow-ups page
Click: 💬 WhatsApp button

What happens:
├── WhatsApp chat opens
├── Customer number pre-filled
├── Send your message
├── Message documented

Example Message:
"Hi ABC Corp team,
 Following up on proposal sent yesterday.
 Do you have any questions?
 Would tomorrow 2 PM work for discussion?
 - Arjun"
```

**Step 3: Send Email**

```
Open: Calls & Follow-ups page
Click: ✉️ Email button

What happens:
├── Email modal opens
├── Customer email pre-filled
├── Compose your message
├── Email sent and logged

Email Template:
Subject: "Following Up - Your Proposal"

Dear [Customer Name],

I hope this message finds you well.

I wanted to follow up on the proposal 
we sent on [date]. 

Do you have any questions or concerns?
Would you like to discuss further?

Best regards,
[Your Name]
[Your Phone]
```

---

### Documenting Interactions

**Step 1: Update Customer Status**

```
After every interaction, update FWP status:

Open: Calls & Follow-ups page
Select: Customer from list
Change: Status dropdown

Options:
├── "Interested" 
│   ✓ Customer showed clear interest
│   → Next: Send proposal/details
│
├── "Not Interested"
│   ✓ Customer declined
│   → Next: Ask why, store feedback
│
├── "In Process"
│   ✓ Customer considering
│   → Next: Follow-up in 2-3 days
│
└── "No Response"
    ✓ Customer not reachable
    → Next: Try different time/method

Save status change
```

**Step 2: Add Notes**

```
After call/message, click "Add Note"

Example Notes:
"2026-08-18 | Call | Customer (Rajesh) interested in 
 product. Has budget approval. Need to send technical 
 specs by tomorrow. Will follow-up Friday morning."

Include in notes:
├── What customer said (key points)
├── Any concerns/objections mentioned
├── Next action and timeline
├── Person who made the call
└── Any special requirements
```

**Step 3: Set Follow-up Reminder**

```
For each customer, set next action:

Example:
Customer: ABC Corp
Last action: Call today (Interested)
Next action: Send proposal
Timeline: By end of day today
Reminder: Set for tomorrow morning

System will remind you tomorrow:
"Send proposal to ABC Corp"
```

---

## 3.3 CONVERTING LEADS TO CUSTOMERS

### The Sales Process

```
┌─────────────────────────────┐
│ STAGE 1: CONTACTED          │
│ Customer answered your call │
└──────────────┬──────────────┘
               │
         Listened to needs?
               │
    ┌──────────┴──────────┐
    ↓                     ↓
  YES                    NO
    │                    │
    └────────┬───────────┘
             ↓
    ┌──────────────────────┐
    │ STAGE 2: INTERESTED  │
    │ Customer wants more  │
    └──────────┬───────────┘
               │
        Send proposal?
               │
               ↓
    ┌──────────────────────┐
    │ STAGE 3: PROPOSAL    │
    │ Details sent         │
    └──────────┬───────────┘
               │
        Customer ready?
               │
    ┌──────────┴──────────┐
    ↓                     ↓
  YES                    NO
    │              (Follow-up needed)
    │                    │
    └────────┬───────────┘
             ↓
    ┌──────────────────────┐
    │ STAGE 4: SANCTION    │
    │ Approval in process  │
    └──────────┬───────────┘
               │
        Approved?
               │
    ┌──────────┴──────────┐
    ↓                     ↓
  YES                    NO
    │              (Re-approach)
    │                    │
    └────────┬───────────┘
             ↓
    ┌──────────────────────┐
    │ STAGE 5: DISBURSED   │
    │ Funds sent           │
    └──────────┬───────────┘
               │
        ✓ CUSTOMER WON! ✓
               │
    ┌──────────────────────┐
    │ STAGE 6: ONBOARDING  │
    │ Customer activated   │
    └──────────────────────┘
```

### Your Conversion Toolkit

**Template 1: Initial Interest Conversation**
```
Opening:
"Hi [Name], I hope you're doing well!
 I noticed your company [Company].
 Do you have 5 minutes to chat about a solution 
 that could help with [Specific Problem]?"

Listen:
- Ask about their current situation
- Identify pain points
- Understand their needs
- Ask qualifying questions

Closing:
"Based on what you shared, I think we have a solution 
 that could really help. Would you like me to send 
 over some details?"
```

**Template 2: Proposal Follow-up**
```
"Hi [Name],

I hope you received the proposal we sent.

I'd love to get your thoughts on it.
Do you have any questions about the approach?

Are you interested in moving forward?

Would tomorrow at 2 PM work for a quick discussion?"
```

**Template 3: Handling Objections**
```
Objection: "Your price is too high"
Response: "I understand budget is important. 
           However, our solution saves you X hours/week,
           which is worth ₹Y per month. 
           Can we discuss how the ROI works?"

Objection: "I need to think about it"
Response: "That's great! When would be a good time 
           to follow up? (e.g., Thursday)
           I'll send you some additional info in the meantime."

Objection: "We're already using a competitor"
Response: "I understand. Many of our best customers 
           switched from competitor. Would you be open 
           to a quick comparison to see if we can do better?"
```

---

## 3.4 DAILY/WEEKLY TARGETS

### Your Personal Targets

```
MONTHLY TARGET: ₹?L (Example: ₹50L)

Breakdown:
├── Minimum Deals: ? (Example: 10-12)
├── Minimum Contacts: ? (Example: 40+)
├── Minimum Follow-ups: ? (Example: 50+)
└── Target Conversion Rate: ?% (Example: 25-30%)

Weekly Target: ₹?L ÷ 4 weeks
Example: ₹50L ÷ 4 = ₹12.5L per week

Daily Target: ₹?L ÷ 20 working days
Example: ₹50L ÷ 20 = ₹2.5L per day

Action:
"I need to close about ₹2.5L daily to hit ₹50L monthly"
```

### Weekly Review

**Every Friday:**
```
Open: Reports page
Check YOUR performance:

├── Deals Closed This Week: ?
├── Revenue This Week: ₹?
├── Am I on pace? (Compare to weekly target)
├── Where can I improve next week?
└── Do I need help/support?

Examples:
✓ On track: "Great! Keeping this pace will hit target"
↓ Below track: "Need 2 more deals to hit target"
↑ Above track: "Excellent! Ahead of pace, can relax or over-deliver"
```

---

## 3.5 USING DIGILOCKER FOR DOCUMENTS

### Document Management

**What is DigiLocker?**
```
Central place to store/access customer documents:
├── Customer KYC (Know Your Customer)
├── Financial statements
├── Bank details
├── Proof of income
├── Loan agreements
├── Disbursement documents
└── Other supporting files
```

**Accessing Your Folders:**

```
Open: DigiLocker page
View: Folders assigned to you

Your section shows:
├── Customer 1
│   ├── Document 1 (Status)
│   ├── Document 2 (Status)
│   └── "Open Folder" button
│
├── Customer 2
│   ├── Document 1 (Status)
│   └── "Open Folder" button
│
└── Customer 3
    ├── Documents as listed
    └── "Open Folder" button
```

**Document Status:**
```
✓ RECEIVED - Document uploaded and verified
⏳ PENDING - Waiting for customer to provide
🔄 REVIEW - Currently being reviewed
✗ REJECTED - Need to resubmit (check notes)
```

**How to Use:**
1. Click "Open Folder" for customer
2. Review documents provided
3. Check status of pending documents
4. Follow up with customer for missing docs
5. Once all received → Mark stage complete

---

## 3.6 DIGILOCKER WORKFLOW EXAMPLE

**Scenario: ABC Corp (Customer)**

```
Timeline:
┌─────────────────────────────────────┐
│ Day 1: Customer Interested          │
│ You: Send list of required docs     │
│ Customer: Receives email            │
│ System: Updates DigiLocker status   │
├─────────────────────────────────────┤
│ Day 2-3: Customer Uploads Documents │
│ Customer: Uploads via DigiLocker    │
│ You: Get alert when docs received   │
│ System: Shows ✓ Received status     │
├─────────────────────────────────────┤
│ Day 4: You Review Documents         │
│ You: Check completeness             │
│ You: Verify all required docs there │
│ You: Mark "Ready for next stage"    │
├─────────────────────────────────────┤
│ Day 5: Escalate to Approver         │
│ You: Message Team Leader            │
│ You: "ABC Corp docs complete"       │
│ Team Leader: Forwards to approval   │
├─────────────────────────────────────┤
│ Day 6-10: Approval Process          │
│ Approver: Reviews and approves      │
│ System: Updates status (APPROVED)   │
│ You: Notified of approval           │
├─────────────────────────────────────┤
│ Day 11: Disbursement                │
│ Finance: Processes payment          │
│ System: Updates status (DISBURSED)  │
│ You: Close deal, celebrate win! 🎉  │
└─────────────────────────────────────┘
```

---

## 3.7 PERFORMANCE & COMPENSATION

### Understanding Your Performance Metrics

**Available in Reports:**
```
My Performance This Month:
├── Total Leads Assigned: 28
├── Contacts Made: 24
├── Contact Rate: 86%
├── Deals Closed: 12
├── Conversion Rate: 43%
├── Total Revenue: ₹52L
├── Average Deal Size: ₹43.3L
└── Days to Close (Avg): 18 days

Comparison:
├── Team Average: 30% conversion
├── Your Rate: 43% (↑ Above average!)
├── Target: 25%
├── Status: ✓ Exceeding target
```

### Commission Calculation

**Example (Hypothetical):**
```
Your compensation:

Base Monthly: ₹? (Fixed)

Commission Structure:
├── 5% of revenue for 0-₹40L
├── 7% of revenue for ₹40L-₹60L
├── 10% of revenue above ₹60L

Your Month:
└── Revenue: ₹52L
    └── Commission Calculation:
        ├── First ₹40L × 5% = ₹2L
        ├── Next ₹12L × 7% = ₹84,000
        └── Total Commission: ₹2.84L

Final Compensation:
├── Base: ₹? (varies)
├── Commission: ₹2.84L
└── Total: ₹? (Base + 2.84L)
```

**Bonus Opportunities:**
```
Performance Incentives:
├── Hit 100% of target → ₹?
├── Exceed target by 20% → ₹?
├── Highest performer this month → ₹?
├── Customer satisfaction 5-star reviews → ₹?
└── Refer customer who signs → ₹?
```

---

## 3.8 BEST PRACTICES & TIPS

### Sales Excellence Tips

**Tip 1: Build Rapport**
```
During calls:
├── Use customer's first name
├── Reference previous conversation
├── Show genuine interest in their needs
├── Listen more than you talk
└── Find common ground

Example:
"Rajesh, I remember you mentioned concerns about 
 processing time. We actually have a way to cut that 
 by 50%. Interested to hear more?"
```

**Tip 2: Ask the Right Questions**
```
Open-ended questions work better:
✓ "Tell me about your current situation"
✓ "What challenges are you facing?"
✓ "How do you approach this currently?"
✗ "Do you like our product?" (Too narrow)
✗ "Do you want to buy?" (Too aggressive)
```

**Tip 3: Create Urgency (Ethically)**
```
Gentle urgency:
├── "This offer expires end of month"
├── "We have limited availability for onboarding"
├── "Other customers in your industry moved quickly"
├── "The sooner we start, the sooner you see ROI"

NOT manipulation - just reality
```

**Tip 4: Document Everything**
```
Why document?
├── Helps you remember details
├── Helps team member if you're out
├── Provides legal proof of communication
├── Improves follow-up effectiveness
├── Supports dispute resolution

What to document:
├── Date and time of interaction
├── Who you talked to
├── What was discussed
├── Next steps and timeline
└── Any promises/commitments
```

**Tip 5: Follow up Religiously**
```
Follow-up Timeline:
├── Same day: Send proposal/info
├── Day 2: Email with additional info
├── Day 3: Phone call check-in
├── Day 5: "Checking in" message
├── Day 7: Final follow-up before archiving
└── Day 10: "We're here when you're ready"

80% of sales close after 5+ follow-ups
Most reps stop after 1-2 attempts
Persistence = success
```

---

## 📋 EMPLOYEE TRAINING CHECKLIST

- [ ] Logged in with Employee credentials
- [ ] Viewed your personal dashboard
- [ ] Reviewed your assigned leads
- [ ] Practiced Click-to-Call button
- [ ] Sent a test WhatsApp message
- [ ] Sent a test email
- [ ] Updated customer FWP status
- [ ] Added notes to a customer
- [ ] Viewed your performance report
- [ ] Accessed your DigiLocker folder
- [ ] Understood target and commission
- [ ] Know escalation procedure

**Training Sign-off:** _________________ Date: _______

---

---

## 🎓 ROLE COMPARISON CHART

| Feature | Admin | Team Leader | Employee |
|---------|-------|------------|----------|
| Dashboard | Full System | Team Only | Personal Only |
| Contacts | Import/Export | Import Only | Import Only |
| Pipeline | All Deals | All Deals | Assigned Deals |
| Calls | All Data | All Data | Personal Only |
| Team | Manage | View/Coach | View Only |
| Reports | Full System | Team Reports | Personal Report |
| DigiLocker | All Folders | Assigned Folders | Assigned Folders |
| Marketing | Full Access | View | View |
| Integrations | Edit Access | View Only | No Access |
| User Management | Yes | No | No |
| Data Export | Yes | No | No |
| Credential Edit | Yes | No | No |

---

## 📞 SUPPORT & ESCALATION

### Getting Help

**For Any Role:**
```
Step 1: Check Training Manual
- Look in relevant section for answer
- Most common issues covered here

Step 2: Ask Team Leader
- Rajesh Kumar (rajesh@arthainvest.com)
- 9 AM - 6 PM on business days
- Usually responds within 1 hour

Step 3: Contact Admin Support
- Email: support@arthainvest.com
- Phone: +91-98765-11111
- For system issues / technical problems
- Emergency support 24/7

Step 4: Try Troubleshooting
- Clear browser cache
- Try different browser
- Restart computer
- Check internet connection
```

---

**ArthaInvest CRM Training Complete!**

*All roles trained and ready for production use.*

---

*Training Manual v1.0 | Date: 2026-08-18*
