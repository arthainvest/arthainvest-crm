# ArthaInvest CRM v3.0 - Team Training Guide

## Welcome to the New Production System! 🚀

This training guide covers everything your team needs to know to use the new ArthaInvest CRM system effectively.

---

## 📚 Table of Contents

1. [System Overview](#system-overview)
2. [Logging In](#logging-in)
3. [Dashboard Features](#dashboard-features)
4. [Auto-Lead Routing](#auto-lead-routing)
5. [Predictive Analytics](#predictive-analytics)
6. [Daily Workflows](#daily-workflows)
7. [Frequently Asked Questions](#frequently-asked-questions)
8. [Support & Troubleshooting](#support--troubleshooting)

---

## 🌐 System Overview

### **What's New?**

The new ArthaInvest CRM v3.0 includes:

✅ **Auto-Lead Routing** - Intelligent lead assignment  
✅ **Predictive Analytics** - AI-powered insights  
✅ **Performance Dashboards** - Real-time metrics  
✅ **Churn Risk Alerts** - Proactive retention  
✅ **Product Recommendations** - Smart suggestions  
✅ **Best Call Times** - Optimal contact windows  

### **System Architecture**

```
┌─────────────────────────────────────┐
│     Your Browser                    │
│  https://arthainvestcapital.com     │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│     Nginx Reverse Proxy             │
│   (SSL/TLS, Security, Routing)      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   Express.js Application Server     │
│  (CRM Logic, APIs, Dashboards)      │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│   PostgreSQL Database               │
│   (All Your Business Data)          │
└─────────────────────────────────────┘
```

### **Key Features by Role**

**Sales Representatives:**
- View assigned leads automatically
- See lead scores and quality ratings
- Get best call time recommendations
- Track deal closure predictions
- Receive churn risk alerts

**Sales Managers:**
- Monitor team performance
- View routing analytics
- Track conversion rates
- Analyze rep capacity
- Access team dashboards

**Administrators:**
- Manage user accounts
- Configure routing rules
- Monitor system health
- Access backup/recovery
- View audit logs

---

## 🔑 Logging In

### **First Time Login**

1. **Open Browser**
   - Navigate to: https://arthainvestcapital.com
   - Accept SSL warning (if first time)

2. **Enter Credentials**
   - Username: (provided by admin)
   - Password: (provided by admin)

3. **Change Password (Recommended)**
   - Click "Settings" (top-right)
   - Select "Change Password"
   - Enter old and new password
   - Click "Update"

### **Forgot Password?**

1. Click "Forgot Password" on login page
2. Enter your email
3. Check email for reset link
4. Follow link and create new password

### **2FA Setup (Optional Security)**

1. Go to Settings → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes in safe location

---

## 📊 Dashboard Features

### **Main Dashboard Components**

#### **1. KPI Cards (Top Section)**

Shows key metrics at a glance:

```
┌─────────────────────────────────────┐
│ 📊 Average Lead Score: 72/100       │
│ 34 high-quality leads (>70)         │
│ +8% improvement vs last month       │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ 🎯 Avg Deal Closure Rate: 28.5%     │
│ 12 deals closed this month          │
│ Avg deal value: ₹2.5L              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ ⚠️ Churn Alerts: 5 clients          │
│ 2 critical, 3 high risk             │
│ Immediate action recommended        │
└─────────────────────────────────────┘
```

**How to Use:**
- Monitor performance trends
- Identify problem areas
- Set personal targets
- Compare with team average

#### **2. Auto-Lead Routing Table**

Shows which leads are assigned to whom and why:

| Lead Name | Score | Quality | Assigned To | Routing Score | Product |
|-----------|-------|---------|-------------|----------------|---------|
| Acme Corp CEO | 95 | Excellent | Yogesh Khatri | 92/100 | Business Loan |
| Tech Startup | 88 | Excellent | Chirag Rathi | 85/100 | Term Insurance |

**How to Use:**
- Click a row to view full lead details
- See why lead was assigned to you
- View alternative assignments
- Contact manager if routing seems wrong

#### **3. Deal Closure Predictions**

Shows probability of deals closing:

```
Deal-001: Acme Corp
Status: Proposal
Value: ₹50L
Closure Probability: 92% [████████░]

Deal-002: Tech Startup
Status: Negotiation
Value: ₹20L
Closure Probability: 78% [███████░░]

Deal-003: Finance Manager
Status: Qualified
Value: ₹15L
Closure Probability: 55% [█████░░░░]
```

**How to Use:**
- Prioritize high-probability deals
- Focus effort on deals with >70% probability
- Review low-probability deals for issues
- Use recommendations for next steps

#### **4. Churn Risk Alerts**

Identifies at-risk clients:

```
🔴 CRITICAL
ABC Company - 85% Churn Risk
No contact in 95 days
Action: Assign relationship manager

🟠 HIGH
XYZ Ltd - 72% Churn Risk
Last interaction 65 days ago
Action: Schedule executive call
```

**How to Use:**
- Address critical clients immediately
- Schedule calls for high-risk clients
- Implement retention strategies
- Report improvements to manager

#### **5. Product Recommendations**

AI-powered suggestions for cross-selling:

```
Lead: Acme Corp CEO
Recommended: Business Loan
Match: 90% (High earner, decision maker)
Estimated Value: ₹50L+

Lead: Tech Startup Founder
Recommended: Term Insurance
Match: 85% (Risk coverage need)
Estimated Value: ₹20L
```

**How to Use:**
- Follow recommendations for cross-sells
- High match scores = higher close probability
- Use conversation starters from recommendations
- Track cross-sell success rate

#### **6. Best Call Times**

Optimal times to contact leads by industry:

```
IT Industry Leads: Tue-Wed, 10:00-11:30
Finance/Banking: Mon-Wed, 14:00-15:30
Insurance Sector: Thu-Fri, 15:00-16:30
Pharma Industry: Mon-Wed, 11:00-12:30
```

**How to Use:**
- Schedule calls during recommended times
- Increase answer rates by 15-20%
- Avoid calling during low-response windows
- Adjust follow-up schedules accordingly

---

## 🤖 Auto-Lead Routing

### **How Leads Are Assigned**

The system automatically routes leads based on:

1. **Product Type (30%)**
   - Insurance, Loans, or Mutual Funds
   - Routed to specialists

2. **Rep Specialization (20%)**
   - Your certified products/skills
   - TATA, Niva Bupa, HDFC, etc.

3. **Current Capacity (20%)**
   - How many active leads you have
   - Even workload distribution

4. **Geographic Proximity (15%)**
   - Prefer same location/region
   - Reduce travel time

5. **Recent Performance (15%)**
   - Your closure rate (past 30 days)
   - High performers get premium leads

### **What You'll See**

When a lead is assigned:

✅ Notification (email/SMS)  
✅ Appears in "My Leads" section  
✅ Lead score and recommendations  
✅ Best call time for that lead  
✅ Suggested product recommendations  

### **Taking Action**

```
Step 1: Review Lead Score
- 90-100: Premium (prioritize)
- 70-89: Good (follow up within 24h)
- 50-69: Medium (follow up within 48h)
- <50: Low (monitor, low priority)

Step 2: Follow Best Call Time
- Use recommended times for first contact
- Increases answer rate significantly

Step 3: Use Product Recommendations
- Lead recommended Business Loan?
- Lead it into conversation naturally
- Mention during qualification call

Step 4: Log Interaction
- Call, Email, WhatsApp, Meeting
- System tracks all interactions
- Improves future AI recommendations

Step 5: Update Deal Status
- Qualified, Proposal, Negotiation, Closing
- System will predict closure probability
- Alerts trigger for issues
```

---

## 📈 Predictive Analytics

### **Lead Scoring (0-100)**

**What It Measures:**
- Profile completeness
- Engagement history
- Company profile
- Job designation
- Historical similarity to past conversions

**How to Improve:**
- Complete all profile fields
- Respond promptly to contacts
- Log all interactions
- Keep notes updated

**What It Means:**

| Score Range | Quality | Action |
|-------------|---------|--------|
| 90-100 | Excellent | Prioritize |
| 70-89 | Good | Follow up soon |
| 50-69 | Medium | Regular follow-up |
| 30-49 | Low | Monitor |
| <30 | Very Low | Consider nurture |

### **Deal Closure Prediction**

**Factors Considered:**
- Deal value
- Pipeline stage progression
- Rep historical close rate
- Lead quality score
- Time spent in current stage

**Confidence Levels:**
- 🟢 High (>70%): Allocate resources
- 🟡 Medium (40-70%): Monitor closely
- 🔴 Low (<40%): Review for issues

**What to Do:**
- 🟢 High deals: Close the deal, move to next
- 🟡 Medium deals: Remove obstacles, add value
- 🔴 Low deals: Requalify or move to nurture

### **Churn Risk Prediction**

**Warning Signs:**
- No contact for 30+ days
- Single product only
- Low lifetime value
- Declining engagement

**Prevention Actions:**
- Schedule regular check-ins
- Cross-sell additional products
- Offer upgrades/improvements
- Escalate to manager if critical

---

## 💼 Daily Workflows

### **Morning Routine (9:00 AM)**

```
1. Check Dashboard (5 min)
   - Review new leads assigned
   - Check churn alerts
   - Note any critical deals

2. Prioritize Your Tasks (5 min)
   - High-score leads: call first
   - Churn alerts: schedule immediate follow-up
   - Deals >70% closure: push to close

3. Plan Calls (10 min)
   - Use "Best Call Times" for planning
   - Schedule calls in optimal windows
   - Note product recommendations
```

### **During Day (All Day)**

```
✅ Follow Lead Routing
   - Call assigned leads
   - Use provided recommendations
   - Log all interactions

✅ Track Interactions
   - Update status after each contact
   - Add notes and next steps
   - Log call duration

✅ Monitor Churn Alerts
   - Act on critical alerts same day
   - Schedule follow-ups for high-risk

✅ Update Deal Status
   - Move deals through pipeline
   - Track actual vs. predicted
   - Highlight obstacles
```

### **Evening Routine (5:00 PM)**

```
1. Review Day's Activity (5 min)
   - Calls made vs. planned
   - Deals advanced
   - Issues encountered

2. Update Next Actions (10 min)
   - Schedule follow-ups
   - Set reminders
   - Plan tomorrow's priorities

3. Check Alerts (5 min)
   - Review any new churn alerts
   - Acknowledge warnings
   - Plan corrective actions
```

### **Weekly Review (Friday 4:00 PM)**

```
1. Performance Metrics
   - Total leads worked
   - Closure rate
   - Average deal value
   - Lead quality average

2. Routing Accuracy
   - Were leads well-suited?
   - Any mismatches?
   - Feedback for managers

3. Predictions vs. Reality
   - Compare closure predictions vs. actual
   - Review churn prevention success
   - Identify patterns

4. Upcoming Week
   - Plan key activities
   - Identify at-risk deals
   - Prepare for critical calls
```

---

## ❓ Frequently Asked Questions

### **Q: What if a lead doesn't match my specialization?**

**A:** The system tries to match, but flexibility is key. If you receive a lead outside your area:
1. Accept it anyway (helps system learn)
2. Log the mismatch with manager
3. Can request transfer if uncomfortable
4. System will adjust future routing

### **Q: How accurate is the closure prediction?**

**A:** Currently **78% accuracy**. It's a guide, not gospel:
- Use it to prioritize efforts
- High predictions need less time
- Low predictions need investigation
- Accuracy improves with more data

### **Q: Can I change my specializations?**

**A:** Yes! Contact your manager to:
1. Add new product certification
2. Remove product you're leaving
3. Update your location/territory
4. Adjust your capacity limits

### **Q: What if I disagree with a product recommendation?**

**A:** Recommendations are suggestions, not rules:
- Use your judgment
- If wrong, note it in interaction log
- System learns from your choices
- Share feedback with manager

### **Q: How do I improve my lead score average?**

**A:**
1. Complete all profile fields on every lead
2. Log all interactions (calls, emails, meetings)
3. Respond to leads quickly (same day)
4. Keep detailed notes
5. Track all outcomes

### **Q: What does "Best Call Time" mean?**

**A:** Times when leads in that industry are most likely to answer:
- IT: Tue-Wed 10-11:30 (post-morning standup)
- Finance: Mon-Wed 14-15:30 (post-lunch)
- Insurance: Thu-Fri 15-16:30 (pre-weekend)
- Pharma: Mon-Wed 11-12:30 (mid-morning)

### **Q: Can I request specific leads?**

**A:** No, but you can:
1. Set specialization preferences
2. Adjust territory/location
3. Request capacity increase
4. Provide feedback on routing
5. Discuss with manager

### **Q: How is my performance measured?**

**A:** Multiple metrics tracked:
- Leads worked vs. assigned
- Closure rate
- Average deal value
- Response time
- Churn prevention
- Product mix
- Customer satisfaction

---

## 🆘 Support & Troubleshooting

### **Common Issues & Solutions**

**Issue: Can't log in**
- Solution: Check CAPS LOCK, try forgot password, contact admin

**Issue: Lead doesn't appear in my list**
- Solution: Refresh page (F5), check filters, contact manager

**Issue: Prediction seems wrong**
- Solution: It's a guide not gospel, review actual factors, provide feedback

**Issue: Best call time not working**
- Solution: Use as a guide, customer preferences vary, track your success rate

**Issue: Can't see churn alert**
- Solution: Might be assigned to manager, scroll down, check filters

### **Getting Help**

**For System Issues:**
- Contact: Tech Support
- Email: support@arthainvestcapital.com
- Phone: +91-XXX-XXXX-XXXX (IT Helpdesk)
- Chat: In-system chat with support

**For Business/Process Questions:**
- Contact: Your Sales Manager
- Email: manager@arthainvestcapital.com
- Office Hours: Daily 2-3 PM

**For Product/Feature Questions:**
- Consult: This training guide
- Ask: Senior team member
- Schedule: One-on-one coaching

### **Reporting Bugs**

Found an issue? Report it:

1. **Document the problem**
   - What were you doing?
   - What went wrong?
   - Screenshots helpful?

2. **Report to support**
   - Email: bugs@arthainvestcapital.com
   - Include: Date, time, browser, details

3. **Follow up**
   - Support confirms receipt
   - Regular updates on progress
   - Notified when fixed

---

## 📞 Contact Information

**System Admin:**
- Name: [Admin Name]
- Email: admin@arthainvestcapital.com
- Phone: +91-XXX-XXXX-XXXX

**Sales Manager:**
- Name: [Manager Name]
- Email: manager@arthainvestcapital.com
- Phone: +91-XXX-XXXX-XXXX

**Technical Support:**
- Email: support@arthainvestcapital.com
- Phone: +91-XXX-XXXX-XXXX
- Hours: 9 AM - 6 PM IST

**Emergency (After Hours):**
- On-call: [On-call Number]
- Email: emergency@arthainvestcapital.com

---

## 🎓 Additional Training Resources

**Video Tutorials:**
- Coming soon at: learning.arthainvestcapital.com

**Documentation:**
- Full API docs: docs.arthainvestcapital.com
- User manual: [Intranet link]
- FAQ: [Intranet link]

**Live Training Sessions:**
- Mondays 10 AM: New features overview
- Wednesdays 2 PM: Advanced tips & tricks
- Fridays 4 PM: Q&A with product team

---

## ✅ Training Checklist

Complete these by end of week:

- [ ] Log in successfully
- [ ] Change password
- [ ] View dashboard
- [ ] Understand lead routing
- [ ] Review your assigned leads
- [ ] Make first call (use best call time)
- [ ] Log interaction
- [ ] Update deal status
- [ ] Check churn alerts
- [ ] Ask questions/feedback

---

## 🚀 You're Ready!

Congratulations! You now understand the new ArthaInvest CRM system.

**Key Takeaways:**
1. System routes high-quality leads automatically
2. Use AI insights to prioritize efforts
3. Follow best call times for better results
4. Log all interactions (system learns)
5. Act on churn alerts proactively
6. Track closure predictions vs. actual

**Remember:**
- The system is here to help you succeed
- AI insights are guides, not gospel
- Your judgment & effort still matter most
- More data = better predictions
- Team feedback improves everyone

---

**Questions? Contact your Sales Manager or Support Team!**

**Welcome to the future of selling! 🎉**

