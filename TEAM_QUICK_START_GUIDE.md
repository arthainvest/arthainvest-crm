# 🚀 ArthaInvest CRM - Team Quick Start Guide

**Last Updated:** 2026-08-20  
**System:** Complete Kylas-Level CRM with 5 Automation Phases  
**Team:** All users

---

## 📋 TABLE OF CONTENTS

1. [Getting Started](#getting-started)
2. [Daily Workflow](#daily-workflow)
3. [Sheet Guide](#sheet-guide)
4. [Key Features](#key-features)
5. [Common Tasks](#common-tasks)
6. [Troubleshooting](#troubleshooting)
7. [Tips & Tricks](#tips--tricks)

---

## 🎯 GETTING STARTED

### **Access Your CRM**
1. Open Google Sheets
2. Search for: "ArthaInvest CRM ADVANCED"
3. Bookmark it (you'll use it daily)
4. Share the link: `https://docs.google.com/spreadsheets/d/[YOUR-ID]`

### **What You'll See**
- **15 sheets** at the bottom (tabs)
- **Menus** at top right: Notifications | Workflows | Lead Scoring | Email Sequences | Communication Hub
- **Color-coded sheets** for easy navigation

### **Your Role**
- **Add data** to Leads, Clients, Deals, Tasks
- **Monitor** dashboards and notifications
- **Act on** tasks and follow-ups
- **Track** communications

---

## 📅 DAILY WORKFLOW

### **MORNING (5 minutes)**

1. **Open Dashboard sheet**
   - Check KPIs: Total clients, active prospects, open deals
   - Review pending tasks
   - Check upcoming renewals

2. **Check Notification Log sheet**
   - See what happened overnight
   - Alerts about hot leads, renewals, dormant clients

3. **Review Lead Scoring sheet**
   - Filter by "HOT" (score 80-100)
   - These need immediate calls

### **DURING DAY (ongoing)**

1. **Add New Leads**
   - Go to **Leads sheet**
   - Add: Name, Phone, Email, Company, Source, Product Interest
   - System auto-calculates score
   - Auto-creates notification (if high priority)

2. **Log Communications**
   - Go to **Communications sheet** or **Communication Hub**
   - Record: Who, when, channel (Email/WhatsApp/Call), outcome
   - Auto-updates timeline

3. **Track Deals**
   - Go to **Deals sheet**
   - Update stage as you move forward
   - System auto-sends notifications

4. **Manage Tasks**
   - Go to **Tasks sheet**
   - Add: Description, priority, due date, related lead
   - System sends reminders

### **END OF DAY (5 minutes)**

1. **Update Last Contact**
   - Mark in Leads/Clients: Today's date in "Last Contact" column
   - System updates in Communication Hub

2. **Check Tomorrow's Tasks**
   - Filter Tasks sheet by tomorrow's date
   - Prepare for next day

---

## 📊 SHEET GUIDE

### **CORE SHEETS (Read/Write)**

#### **1. Dashboard**
**What:** Executive overview of your CRM
**Use:** Start your day here
**Key Fields:** KPIs, business profile, quick stats
**Action:** View only (for monitoring)

#### **2. Leads**
**What:** All prospects/new opportunities
**Use:** Add new leads, track qualification
**Key Fields:** Name, Phone, Email, Score, Tier, Qualification Status
**Action:** Add new leads, update status, monitor scores

**Example:**
```
Rajesh Patel | 98765-43210 | rajesh@email | LinkedIn | Term Insurance | 
Qualified | 85 (HOT) | ₹50L | 2 months
```

#### **3. Contacts**
**What:** Master directory of all people
**Use:** Manage all relationships
**Key Fields:** Name, Phone, Email, Relationship Type, Preference
**Action:** Add contacts, set preferences, track relationships

#### **4. Clients**
**What:** Active customers/paying clients
**Use:** Manage renewals, track commission
**Key Fields:** Name, Product, Premium, Renewal Date, Status
**Action:** Track renewals (30 days before alert), monitor commission

**Auto-Alert:** If renewal is within 7 days, you get notified

#### **5. Deals**
**What:** Sales pipeline opportunities
**Use:** Track revenue-generating opportunities
**Key Fields:** Deal Name, Value, Stage, Close Date, Probability
**Action:** Update stage as deal progresses (7 stages: Prospecting → Won/Lost)

**Auto-Action:** When stage = Won, system creates renewal task

#### **6. Tasks**
**What:** All follow-ups and action items
**Use:** Stay organized, never miss a follow-up
**Key Fields:** Description, Priority, Due Date, Status, Related Lead
**Action:** Create tasks, mark as pending/in-progress/completed

**Auto-Create:** System creates tasks from workflows (doesn't require manual entry)

#### **7. Communications**
**What:** Log of all customer interactions
**Use:** Track every conversation
**Key Fields:** Date, Contact, Channel (Email/WhatsApp/Call), Subject, Status
**Action:** Log calls, messages, meetings

#### **8. Products**
**What:** Your insurance products
**Use:** Reference (don't edit - already setup)
**Pre-loaded:** Tata AIG (8%), Niva Bupa (12%), POSP (5%), DSA (6%)

---

### **AUTOMATION SHEETS (Monitor Only)**

#### **9. Lead Scoring**
**What:** Auto-calculated scores (0-100)
**View:** See tier assignments
**Don't Edit:** System updates automatically

**Tier Reference:**
- 🔴 HOT (80-100): Call today
- 🟠 WARM (60-79): Schedule meeting
- 🟡 COOL (40-59): Email nurture
- 🔵 COLD (20-39): Sequence email
- ⚪ VERY COLD (0-19): Re-engage

#### **10. Workflows**
**What:** Automation rules that execute actions
**View:** See which workflows are enabled
**Don't Edit:** Pre-configured

**5 Active Workflows:**
1. Lead Assignment → Send welcome message
2. Hot Lead Alert → Create urgent task
3. Deal Won → Create renewal reminder
4. Dormant Client → Start re-engagement
5. Commission → Log & alert

#### **11. Email Sequences**
**What:** Automated email campaigns running
**View:** See who's enrolled, email subjects
**Don't Edit:** System manages automatically

**4 Sequences Running:**
- Nurture (Cold leads: 7 emails)
- Onboarding (New clients: 8 emails)
- Re-engagement (Inactive: 6 emails)
- Sales (Warm leads: 7 emails)

#### **12. Communication Hub**
**What:** Unified view of all interactions
**View:** Last activity, next touchpoint, status for each lead/client
**Use:** Track relationship health

#### **13. Notification Log**
**What:** History of all system alerts
**View:** See what triggered, when, who
**Use:** Stay informed of important events

#### **14. Workflow Logs**
**What:** Record of all automated actions executed
**View:** See tasks created, messages sent automatically
**Use:** Verify automation is working

#### **15. Sequence Logs**
**What:** Email send history and engagement
**View:** Opens, clicks, deliverability
**Use:** Track email effectiveness

---

## 🔥 KEY FEATURES

### **FEATURE 1: Auto Lead Scoring**
**What it does:** Every lead gets a score (0-100) automatically

**How to use:**
1. Add a new lead to Leads sheet
2. Fill in basic info (name, company, source, budget, timeline)
3. System auto-calculates score within seconds
4. Check "Lead Tier" column for tier (HOT/WARM/COLD)

**Action:** Focus on HOT leads first

---

### **FEATURE 2: WhatsApp Notifications**
**What it does:** Get instant WhatsApp alerts for important events

**You'll get alerts for:**
- ✅ New lead assigned
- ✅ Lead score changed
- ✅ Deal created
- ✅ Renewal due (7 days before)
- ✅ Commission earned
- ✅ Client dormant (30+ days)

**Check:** Notification Log sheet to see all alerts

---

### **FEATURE 3: Automatic Task Creation**
**What it does:** System creates tasks automatically (no manual entry needed)

**Examples:**
- New lead assigned → Welcome task created
- Lead score becomes HOT → Call task created
- Deal won → Onboarding task created
- Client dormant → Re-engagement task created

**Check:** Tasks sheet to see auto-created tasks

**Action:** Complete tasks as they appear

---

### **FEATURE 4: Email Sequences**
**What it does:** Sends automated email series to nurture leads

**What happens:**
1. Lead added → System evaluates tier
2. If COLD: Enrolled in Nurture Sequence (7 emails over 14 days)
3. If WARM: Enrolled in Sales Sequence (7 emails over 21 days)
4. System tracks opens, clicks, conversions

**Check:** Sequence Logs sheet for engagement metrics

**Result:** 24/7 automated email outreach

---

### **FEATURE 5: Communication Hub**
**What it does:** Unified view of ALL interactions with each contact

**See for each lead/client:**
- Email opens/clicks count
- WhatsApp sent/delivered/read count
- Call history
- Meeting history
- Last activity date
- Next touchpoint date

**Use:** Know exactly where you stand with each person

---

## ✅ COMMON TASKS

### **TASK 1: Add a New Lead**

**Steps:**
1. Open **Leads sheet**
2. Add new row with:
   - Name: "Rajesh Patel"
   - Phone: "98765-43210"
   - Email: "rajesh@company.com"
   - Company: "Tech Corp"
   - Source: "LinkedIn"
   - Product Interest: "Term Insurance"
   - Timeline: "2" (months)
   - Budget: "50,00,000"

3. System automatically:
   - Calculates lead score
   - Assigns tier (HOT/WARM/COOL/COLD)
   - Creates notification
   - Schedules email if applicable

**Result:** Lead is now in system, scoring active

---

### **TASK 2: Log a Phone Call**

**Steps:**
1. Open **Communications sheet**
2. Add new row with:
   - Date: Today
   - Contact Name: "Rajesh Patel"
   - Channel: "Phone Call"
   - Type: "Follow-up"
   - Subject: "Discussed budget & timeline"
   - Duration: "15" (minutes)
   - Outcome: "Very interested"

3. System automatically:
   - Updates Communication Hub
   - Updates last contact date
   - Adjusts lead score (recent activity = higher score)

**Result:** Interaction logged, communication history updated

---

### **TASK 3: Update Deal Stage**

**Steps:**
1. Open **Deals sheet**
2. Find the deal: "Rajesh Corp Insurance"
3. Update "Stage" column: Change from "Proposal" to "Negotiation"

4. System automatically:
   - Creates notification
   - Updates pipeline value calculation

**Tip:** When you move to "Closed Won", system auto-creates:
- Renewal reminder task
- Onboarding email sequence

---

### **TASK 4: Create Follow-up Task**

**Steps:**
1. Open **Tasks sheet**
2. Add new row with:
   - Description: "Call Rajesh Patel to discuss quotation"
   - Related To: "Rajesh Patel"
   - Priority: "High"
   - Due Date: "2026-08-25"
   - Status: "Pending"

3. System automatically:
   - Sends reminder on due date
   - Links to lead/client profile

**Result:** You have a reminder, won't miss follow-up

---

### **TASK 5: Check Your Daily Priorities**

**Steps:**
1. Open **Leads sheet**
2. Filter "Lead Tier" column by "HOT" (use filter icon)
3. Now you see only HIGH priority leads

4. Alternative: Open **Dashboard** sheet
   - See "Hot Leads" count at top
   - Click on leads with score > 80

**Result:** Know exactly who to call today

---

### **TASK 6: Monitor Client Renewals**

**Steps:**
1. Open **Clients sheet**
2. Look at "Renewal Date" column
3. Any date in next 7 days = URGENT

4. System automatically:
   - Sends notification 7 days before
   - Creates renewal task
   - Logs in workflow logs

**Action:** Reach out to renew before date passes

---

### **TASK 7: Track Commission**

**Steps:**
1. Open **Commissions sheet**
2. See all commissions earned (auto-logged from policies)
3. Check status: Earned / Pending / Paid

4. System automatically:
   - Sends notification when commission earned
   - Creates payment task

**Result:** Know exactly how much you've earned

---

## 🆘 TROUBLESHOOTING

### **Problem: Lead Score Not Updating**
**Solution:** Wait 5-10 seconds, refresh page (Ctrl+R)
- Scores calculate automatically
- Check Score column appeared in Leads sheet

---

### **Problem: Notification Not Received**
**Check:**
1. Notification Log sheet - Is it there?
2. WhatsApp connected? (Automatic for now)
3. Try "Notifications" menu → "Test Notifications"

---

### **Problem: Task Not Created Automatically**
**Check:**
1. Open Tasks sheet - Is it there?
2. Workflows sheet - Is workflow enabled?
3. Try "Workflows" menu → "Run Workflows"

---

### **Problem: Email Not Sent**
**Check:**
1. Sequence Logs sheet - Is email listed?
2. Lead tier? (COLD/WARM to get enrolled)
3. Try "Email Sequences" menu → "Test Sequences"

---

### **Problem: Score Seems Wrong**
**Check:**
1. Lead Scoring sheet - See calculation breakdown
2. Check last contact date (affects score)
3. Try "Lead Scoring" menu → "Calculate Lead Scores"

---

## 💡 TIPS & TRICKS

### **TIP 1: Use Filters**
- Click column header → Filter icon
- Filter by Tier (HOT), Status (Pending), Priority (High)
- Saves time finding what matters

### **TIP 2: Use Search (Ctrl+F)**
- Search for lead name across all sheets
- Find all interactions with one person

### **TIP 3: Sort by Last Contact**
- Oldest contacts first = who needs re-engagement
- Newest contacts first = recent activity

### **TIP 4: Check Dashboards Daily**
- Dashboard sheet (KPIs)
- Communication Hub (relationship health)
- Notification Log (what happened)

### **TIP 5: Use Preferred Channel**
- Check Communication Preferences sheet
- Some prefer WhatsApp, some email
- Respect preferences = higher response rates

### **TIP 6: Batch Similar Tasks**
- Group calls by location
- Group emails by sequence
- More efficient than switching between

### **TIP 7: Update "Last Contact" Column**
- System uses this for scoring & alerts
- Update after every interaction
- Keeps dormant detection accurate

### **TIP 8: Set Realistic Follow-up Dates**
- Don't create too many tasks (overwhelm)
- Focus on HIGH priority only
- MEDIUM/LOW can use email sequences

### **TIP 9: Review Sequence Performance**
- Open Sequence Logs weekly
- Check open rates (target: 25%+)
- Check click rates (target: 5%+)
- Adjust if needed

### **TIP 10: Trust the Automation**
- Workflows run 24/7
- Sequences send automatically
- Scores update automatically
- Your job: Add data, take action on alerts

---

## 🎯 YOUR DAILY CHECKLIST

**Every Morning:**
- [ ] Open Dashboard → Check KPIs
- [ ] Check Notification Log → See overnight alerts
- [ ] Filter Leads by "HOT" tier → Call these today
- [ ] Review today's Tasks → Prioritize

**Throughout Day:**
- [ ] Add new leads → System scores them
- [ ] Log communications → Keep history updated
- [ ] Update deal stages → System auto-acts
- [ ] Create follow-up tasks → Don't forget

**End of Day:**
- [ ] Check tomorrow's tasks → Prepare
- [ ] Update last contact dates → Keep scoring accurate
- [ ] Review communication hub → See relationship status

---

## 📞 GETTING HELP

**For questions about:**
- **Data entry** → Check Sheet Guide section
- **Features** → Check Key Features section
- **How to do something** → Check Common Tasks section
- **Something not working** → Check Troubleshooting section

**Contact:** [Your contact info]

---

## 🚀 YOU'RE READY!

**You now have:**
- ✅ Complete CRM with 15 sheets
- ✅ 5 automation phases working
- ✅ 27 clients pre-loaded
- ✅ 12 prospects ready to score
- ✅ Automatic notifications
- ✅ Automatic tasks
- ✅ Email sequences running
- ✅ Communication tracking

**Start using it today. Success comes from consistent data entry and action on alerts.**

---

**Happy selling!** 🎉

*Last updated: 2026-08-20*  
*Next review: Monthly*
