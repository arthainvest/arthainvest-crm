# 🎯 ARTHAINVEST CRM - ALL TABS COMPLETE DETAILS

**Every single detail, dropdown, field, and feature in each tab**

---

# 📊 TAB 1: DASHBOARD

## **URL**: `/dashboard`

## **HEADER SECTION**
```
Title: "Dashboard"
Subtitle: "Welcome back! Here's your sales overview."
Date Display: Current date (auto-updates)
```

---

## **SECTION 1: KPI CARDS (4 Cards)**

### **Card 1: Total Leads**
- **Icon**: 📊
- **Title**: "Total Leads"
- **Value**: Count (e.g., 1)
- **Trend**: Percentage (e.g., +12%)
- **Trend Color**: Green (positive)
- **Left Border**: 4px blue (#3498db)
- **Width**: ~25% (responsive)
- **Height**: 140px
- **Background**: White
- **Hover**: Lift 4px up, shadow intensifies
- **Clickable**: Yes → Drill to Leads page
- **Animation**: 0.3s ease transition

### **Card 2: Qualified Leads**
- **Icon**: ✓
- **Title**: "Qualified Leads"
- **Value**: Count (e.g., 0)
- **Trend**: Conversion % (e.g., 0% conv.)
- **Trend Color**: Gray (neutral)
- **Left Border**: 4px green (#2ecc71)
- **Width**: ~25%
- **Height**: 140px
- **Calculation**: COUNT WHERE status='qualified'
- **Hover**: Lift effect, green accent
- **Clickable**: Yes → Filter contacts by qualified

### **Card 3: Active Deals**
- **Icon**: 💼
- **Title**: "Active Deals"
- **Value**: Count (e.g., 4)
- **Trend**: Pipeline value (e.g., ₹34.5L)
- **Trend Color**: Orange
- **Left Border**: 4px orange (#f39c12)
- **Width**: ~25%
- **Height**: 140px
- **Calculation**: COUNT WHERE stage!='closed'
- **Format**: Currency display (₹)
- **Hover**: Orange intensification

### **Card 4: Closed Deals**
- **Icon**: 🎯
- **Title**: "Closed Deals"
- **Value**: Count (e.g., 0)
- **Trend**: Growth % (e.g., +8%)
- **Trend Color**: Red
- **Left Border**: 4px red (#e74c3c)
- **Width**: ~25%
- **Height**: 140px
- **Calculation**: COUNT WHERE stage='closed'
- **Hover**: Red accent

---

## **SECTION 2: Pipeline Performance (4 Metrics)**

### **Metric 1: Total Pipeline Value**
- **Label**: "Total Pipeline Value"
- **Value**: ₹34.50L
- **Icon**: 💰
- **Border-top**: 3px #667eea (blue)
- **Calculation**: SUM(deal_values) where stage!='closed'
- **Format**: Indian currency (₹) with Lakh format
- **Box Size**: 25% width, 120px height
- **Hover**: Blue highlight

### **Metric 2: Average Deal Value**
- **Label**: "Average Deal Value"
- **Value**: ₹86.3K
- **Icon**: 📊
- **Border-top**: 3px #667eea
- **Calculation**: Total Pipeline Value ÷ Number of Active Deals
- **Format**: Thousands (K) format
- **Example**: ₹345K ÷ 4 = ₹86.25K
- **Box Size**: 25% width, 120px height

### **Metric 3: Conversion Rate**
- **Label**: "Conversion Rate"
- **Value**: 0%
- **Icon**: 📈
- **Border-top**: 3px #667eea
- **Calculation**: (Qualified Leads ÷ Total Leads) × 100
- **Current**: (0 ÷ 1) × 100 = 0%
- **Benchmark**: 30-50% is healthy
- **Box Size**: 25% width, 120px height

### **Metric 4: Active Opportunities**
- **Label**: "Active Opportunities"
- **Value**: 4
- **Icon**: 🎯
- **Border-top**: 3px #667eea
- **Calculation**: COUNT(deals) where stage!='closed'
- **Meaning**: Total active deals in pipeline
- **Box Size**: 25% width, 120px height

---

## **SECTION 3: Recent Leads Table**

### **Table Header**
```
Title: "Recent Leads"
Rows Displayed: 5 (most recent)
Total Columns: 5
```

### **Column 1: Name**
- **Width**: 20%
- **Font**: Bold, 14px
- **Color**: Dark gray (#2c3e50)
- **Action**: Clickable → View lead detail
- **Content**: Full name of lead
- **Examples**: 
  - Neha Singh
  - Vikram Reddy
  - Anjali Desai
  - Amit Patel
  - Priya Kapoor

### **Column 2: Company**
- **Width**: 25%
- **Font**: Regular, 14px
- **Color**: Medium gray (#7f8c8d)
- **Action**: Clickable → Filter by company
- **Content**: Company name
- **Examples**:
  - StartUp Fund
  - Tech Park
  - Retail Chain
  - Manufacturing
  - Digital Ventures

### **Column 3: Status**
- **Width**: 15%
- **Font**: 12px, bold
- **Display**: Color-coded badge
- **Options**: New (blue), Qualified (green), Proposal (orange), Negotiation (red), Closed (purple)
- **Current**: All showing "new"
- **Background**: Semi-transparent matching color
- **Border-radius**: 4px

### **Column 4: Tier**
- **Width**: 15%
- **Font**: Bold, 13px
- **Color**: Primary blue (#667eea)
- **Display**: HOT/WARM/COOL/COLD or "-"
- **Current**: All showing "-" (not assigned)
- **Source**: AI-calculated

### **Column 5: Score**
- **Width**: 15%
- **Font**: Bold, 13px
- **Color**: Primary blue (#667eea)
- **Range**: 0-100
- **Current**: All showing "-" (pending)
- **Calculation**: Automated AI scoring
- **Updates**: Real-time based on engagement

### **Table Styling**
- **Background**: White
- **Header BG**: Light gray (#f8f9fa)
- **Row Spacing**: 50px height per row
- **Row Hover**: Light blue (#f0f1f5)
- **Border**: 0.5px #e0e0e0
- **Padding**: 12px per cell
- **Responsive**: Scrollable on mobile

### **Table Actions**
- Click row → View lead detail
- Hover row → Show edit/delete buttons
- Sort by column → Click header

---

## **RESPONSIVE BREAKPOINTS**

### **Desktop (1280px+)**
- KPI Cards: 4 columns (full width)
- Metrics: 4 columns
- Table: Full width, all columns visible
- Sidebar: 220px fixed
- Main content: Responsive

### **Tablet (768px-1024px)**
- KPI Cards: 2 columns (2 rows)
- Metrics: 2 columns (2 rows)
- Table: Horizontally scrollable
- Sidebar: Reduced width (160px)
- Font sizes: Slightly smaller

### **Mobile (<768px)**
- KPI Cards: 1 column (4 rows stacked)
- Metrics: 1 column (4 rows stacked)
- Table: Horizontal scroll
- Sidebar: Hamburger menu (icons only)
- Full width content

---

## **REAL-TIME FEATURES**
- ✅ Auto-refresh every 30 seconds
- ✅ Live data from API
- ✅ Smooth animations on updates
- ✅ No manual refresh needed
- ✅ WebSocket ready (future)

---

---

# 👥 TAB 2: CONTACTS

## **URL**: `/contacts`

## **HEADER SECTION**
```
Title: "Contacts"
Subtitle: "Manage your sales contacts and leads"
```

---

## **TOOLBAR SECTION**

### **Search Box**
- **Placeholder**: "Search contacts..."
- **Search Scope**: 
  - Name
  - Email
  - Phone
  - Company
- **Real-time**: Yes (filters as you type)
- **Clear Button**: Yes (X icon)
- **Position**: Left side

### **Status Filter Dropdown**
- **Label**: "All Status"
- **Type**: Select dropdown
- **Default**: "All Status"
- **Options Available**:
  1. All Status (show all)
  2. New (brand new)
  3. Active (currently engaged)
  4. Interested (showed interest)
  5. Negotiating (in negotiation)
  6. Customer (became customer)
- **Multi-select**: No (single select)
- **Position**: Next to search

### **Sort Dropdown**
- **Label**: "Sort by Name"
- **Default**: Name (A-Z)
- **Options Available**:
  1. Name (A-Z)
  2. Score (High to Low)
  3. Company (A-Z)
  4. Recent (Newest first)
  5. Oldest first
- **Direction**: Ascending/Descending
- **Position**: Right of search

### **Add Contact Button**
- **Label**: "+ Add Contact"
- **Color**: Blue (#667eea)
- **Style**: Primary button
- **Position**: Right side
- **Action**: Opens modal → Create new contact form
- **Icon**: Plus sign

### **Display Counter**
- **Format**: "Showing X of Y"
- **Updates**: Real-time as you filter
- **Position**: Below toolbar

---

## **CONTACT GRID (Card-based)**

### **Card Layout**
- **Grid Columns**: 
  - Desktop: 3-4 columns
  - Tablet: 2-3 columns
  - Mobile: 1 column
- **Min Width**: 320px per card
- **Gap**: 16px between cards
- **Responsive**: Auto-reflow

### **Contact Card Structure**

#### **Card Header**
- **Name**: Bold, 16px, clickable
- **Company**: Gray, 14px
- **Status Badge**: Small, color-coded

#### **Card Body**
- **Email**: Email address, clickable (opens email)
- **Phone**: Phone number, clickable (opens dialer)
- **Location**: City, State (if available)
- **Score**: 0-100 (if assigned)
- **Tier**: HOT/WARM/COOL/COLD (if assigned)

#### **Card Footer**
- **Action Buttons** (on hover):
  1. 📧 Email (send email)
  2. 📞 Call (dial phone)
  3. ✏️ Edit (open edit modal)
  4. 🗑️ Delete (delete with confirmation)
  5. 👁️ View (show full details)

### **Card Styling**
- **Background**: White
- **Border**: 0.5px #e0e0e0
- **Shadow**: 0 2px 8px rgba(0,0,0,0.1)
- **Padding**: 16px
- **Border-radius**: 4px
- **Hover**: Lift effect (-4px), shadow intensifies

---

## **EMPTY STATE**
```
┌─────────────────────────────┐
│  No contacts found          │
│  [+ Add your first contact] │
└─────────────────────────────┘
```

---

## **CREATE/EDIT CONTACT MODAL**

### **Modal Title**
- Create: "Add New Contact"
- Edit: "Edit Contact"

### **Form Fields (16 fields)**

1. **Full Name** (Required)
   - Type: Text input
   - Placeholder: "Enter full name"
   - Validation: Required
   - Max length: 100

2. **Email** (Required)
   - Type: Email input
   - Placeholder: "Enter email address"
   - Validation: Valid email format
   - Max length: 100

3. **Phone** (Required)
   - Type: Phone input
   - Placeholder: "Enter phone number"
   - Format: Supports +91 country code
   - Validation: Valid phone

4. **Company** (Optional)
   - Type: Text input + autocomplete
   - Placeholder: "Enter company name"
   - Autocomplete: From existing companies
   - Max length: 100

5. **Job Title** (Optional)
   - Type: Text input
   - Placeholder: "e.g., CEO, Sales Manager"
   - Max length: 50

6. **Industry** (Optional)
   - Type: Dropdown
   - Options: Insurance, Finance, Technology, Retail, Manufacturing, Healthcare, Other
   - Searchable: Yes

7. **Company Size** (Optional)
   - Type: Dropdown
   - Options: 1-10, 11-50, 51-200, 201-1000, 1000+

8. **Annual Revenue** (Optional)
   - Type: Text input
   - Format: Currency (₹)
   - Max length: 20

9. **Website** (Optional)
   - Type: URL input
   - Placeholder: "https://company.com"
   - Validation: Valid URL

10. **LinkedIn URL** (Optional)
    - Type: URL input
    - Placeholder: "linkedin.com/in/..."
    - Validation: Valid LinkedIn URL

11. **Source** (Required)
    - Type: Dropdown
    - Options: Website, Referral, LinkedIn, Cold Call, Email Campaign, Event, Other
    - Default: Website

12. **Status** (Required)
    - Type: Dropdown
    - Options: New, Active, Interested, Negotiating, Customer
    - Default: New

13. **Notes** (Optional)
    - Type: Textarea
    - Placeholder: "Add any notes about this contact..."
    - Max length: 500 characters
    - Show char count: Yes

14. **Tags** (Optional)
    - Type: Multi-select
    - Existing tags: VIP, Hot Lead, Prospect, Partner
    - Add new tags: Yes

15. **Preferred Contact Method** (Optional)
    - Type: Dropdown
    - Options: Email, Phone, WhatsApp, LinkedIn, No contact
    - Default: Email

16. **Best Time to Contact** (Optional)
    - Type: Dropdown
    - Options: Morning (9-12), Afternoon (12-5), Evening (5-8), Any time

### **Form Layout**
- **Layout**: 2-column grid on desktop, 1-column on mobile
- **Field Spacing**: 16px between fields
- **Modal Width**: 600px
- **Padding**: 24px
- **Font Size**: 14px labels, 14px inputs

### **Form Buttons**
- **Save** (Primary Blue) - Saves and closes modal
- **Cancel** (Secondary Gray) - Closes without saving
- **Delete** (Danger Red) - Only on edit modal, shows confirmation

---

## **CRUD OPERATIONS SUMMARY**

| Operation | Action | Modal | Result |
|-----------|--------|-------|--------|
| **Create** | [+ Add Contact] | Opens form | New contact added |
| **Read** | Click card | Shows detail page | View all info |
| **Update** | Click Edit | Opens form | Contact updated |
| **Delete** | Click Delete | Confirmation | Contact removed |

---

## **ADVANCED FEATURES**
- ✅ Bulk selection (checkboxes)
- ✅ Bulk delete
- ✅ Bulk export to CSV
- ✅ CSV import
- ✅ Duplicate detection
- ✅ Activity timeline
- ✅ Contact history
- ✅ Email integration
- ✅ Phone integration

---

---

# 📋 TAB 3: LEADS

## **URL**: `/leads`

## **HEADER SECTION**
```
Title: "Leads"
Subtitle: "Track and manage inbound leads"
```

---

## **TOOLBAR SECTION**

### **Search Box**
- **Placeholder**: "Search leads..."
- **Search By**: Name, Company, Email, Phone
- **Real-time**: Yes

### **Status Filter Dropdown**
- **Label**: "All Status"
- **Options**: All, New, Qualified, Proposal, Negotiation, Closed
- **Multi-select**: Yes
- **Color-coded badges**: Yes

### **Tier Filter Dropdown**
- **Label**: "All Tiers"
- **Options**: All, HOT, WARM, COOL, COLD
- **Multi-select**: Yes
- **Color indicators**: Yes

### **Source Filter Dropdown**
- **Label**: "All Sources"
- **Options**: All, Website, Referral, LinkedIn, Cold Call, Email, Other
- **Multi-select**: Yes

### **Sort Dropdown**
- **Label**: "Sort by"
- **Options**: Score (High to Low), Name (A-Z), Recent, Engagement
- **Default**: Score

### **Date Range Selector**
- **Label**: "All Time"
- **Options**: Today, Last 7 Days, Last 30 Days, This Month, Last Quarter, Custom
- **Custom**: Date picker

---

## **LEADS TABLE**

### **Columns (8 columns)**

| # | Column | Type | Sortable | Actions |
|---|--------|------|----------|---------|
| 1 | **Name** | Text | ✅ Yes | Clickable → detail |
| 2 | **Company** | Text | ✅ Yes | - |
| 3 | **Email** | Email | ❌ No | Clickable → email |
| 4 | **Phone** | Phone | ❌ No | Clickable → call |
| 5 | **Status** | Badge | ✅ Yes | Color-coded |
| 6 | **Tier** | Badge | ✅ Yes | HOT/WARM/COOL/COLD |
| 7 | **Score** | Number | ✅ Yes | 0-100 |
| 8 | **Added Date** | Date | ✅ Yes | MM/DD/YY |

### **Row Actions**
- [👁️ View] - Opens detail page
- [✏️ Edit] - Opens edit modal
- [🗑️ Delete] - Deletes with confirmation
- [💼 Convert to Deal] - Creates associated deal
- [📧 Email] - Email template

### **Pagination**
- **Rows per page**: 10, 25, 50, 100 (dropdown)
- **Navigation**: Previous, Next, Go to page
- **Display**: "Showing X-Y of Z results"

---

## **LEAD DETAIL VIEW (Clicking on name)**

### **Section 1: Lead Overview**
- **Name**: Editable text
- **Company**: Editable text
- **Email**: Editable, clickable
- **Phone**: Editable, clickable
- **Source**: Display
- **Created Date**: Display

### **Section 2: Lead Scoring**
- **Current Score**: 0-100
- **Score Breakdown**:
  - Engagement score (%)
  - Company fit score (%)
  - Urgency score (%)
  - Recency score (%)
- **Tier Assignment**: HOT/WARM/COOL/COLD
- **Score History**: Chart showing trend

### **Section 3: Activity Timeline**
- **Email opens**: Timestamp, user
- **Link clicks**: Timestamp, link, user
- **Form submissions**: Timestamp, form, user
- **Phone calls**: Timestamp, duration, outcome
- **Meetings**: Timestamp, attendees
- **Notes**: Timestamp, content
- **Chronological**: Newest first

### **Section 4: Associated Deals**
- **List of deals** linked to lead
- **Columns**: Deal name, Value, Stage, Expected close
- **Actions**: View deal, Create new deal

### **Section 5: Notes**
- **Internal notes** about lead
- **Add new note**: Textarea
- **Note history**: All past notes with timestamps

### **Section 6: Files**
- **Attachments**: Documents uploaded
- **File name**: Clickable to download
- **Upload date**: Timestamp
- **Uploaded by**: User name
- **Upload new**: Drag-and-drop or click

---

## **CREATE/EDIT LEAD MODAL**

### **Form Fields (12 fields)**

1. **Lead Name** (Required) - Text input
2. **Email** (Required) - Email input
3. **Phone** (Required) - Phone input
4. **Company** (Optional) - Text + autocomplete
5. **Product Interest** (Optional) - Dropdown (Insurance, Investment, Loan, etc.)
6. **Source** (Required) - Dropdown (Website, Referral, LinkedIn, Cold Call, Email, Other)
7. **Status** (Required) - Dropdown (New, Qualified, Proposal, Negotiation, Closed)
8. **Budget Range** (Optional) - Dropdown (0-1L, 1L-5L, 5L-10L, 10L+)
9. **Decision Timeline** (Optional) - Dropdown (Immediate, This month, This quarter, Next quarter, Undecided)
10. **Number of Employees** (Optional) - Number input
11. **Industry** (Optional) - Dropdown
12. **Additional Notes** (Optional) - Textarea

### **Form Buttons**
- [Save Lead] (Blue)
- [Cancel] (Gray)
- [Delete] (Red - edit only)

---

## **LEAD SCORING ALGORITHM**

### **Automated Scoring (0-100)**

**Engagement Signals (30 points)**
- Email opens (1 point each)
- Link clicks (2 points each)
- Website visits (1 point each)
- Page time spent (1 point per min)

**Company Fit (25 points)**
- Industry match (5-10 points)
- Company size fit (5-10 points)
- Revenue fit (5-10 points)
- Location match (5 points)

**Urgency (25 points)**
- Budget approved (10 points)
- Timeline mentioned (10 points)
- Competitor mention (3 points)
- "ASAP" language (2 points)

**Recency (20 points)**
- Last activity < 24 hours (20 points)
- Last activity < 7 days (10 points)
- Last activity < 30 days (5 points)
- No activity (0 points)

### **Tier Assignment**
- **HOT** (80-100) - Priority, contact immediately
- **WARM** (60-79) - Good prospect, follow up soon
- **COOL** (40-59) - Maybe, needs more nurturing
- **COLD** (<40) - Follow up later

---

---

# 💼 TAB 4: PIPELINE

## **URL**: `/pipeline`

## **HEADER SECTION**
```
Title: "Pipeline"
Subtitle: "Manage your deals across stages"
```

---

## **TOOLBAR SECTION**

### **New Deal Button**
- **Label**: "+ New Deal"
- **Color**: Blue (#667eea)
- **Action**: Opens deal creation modal

### **View Toggle**
- **Options**: 
  1. Kanban View (cards) - Default
  2. List View (table format)
  3. Chart View (pipeline value chart)
- **Selected**: Highlighted
- **Icons**: Different icon per view

### **Filter Options**
- **Owner Filter**: Dropdown - By team member
- **Stage Filter**: Dropdown - Show specific stages
- **Value Range**: Dropdown - Filter by deal value (0-1L, 1L-5L, etc.)

### **Sort Options**
- By Value (High to Low)
- By Probability (High to Low)
- By Close Date (Soonest first)
- By Created Date (Newest first)

---

## **KANBAN BOARD (5 Columns)**

### **Column 1: NEW**
- **Header**: "New [0]" (count in brackets)
- **Color Accent**: Blue
- **Meaning**: New opportunities, not yet qualified
- **Auto-actions**: None
- **Drag-to**: Yes (can move to other columns)

### **Column 2: QUALIFIED**
- **Header**: "Qualified [0]"
- **Color Accent**: Green
- **Meaning**: Qualified leads with identified needs
- **Auto-actions**: None
- **Drag-to**: Yes

### **Column 3: PROPOSAL**
- **Header**: "Proposal [0]"
- **Color Accent**: Orange
- **Meaning**: Proposal sent, awaiting response
- **Auto-actions**: Auto-reminder after 5 days
- **Drag-to**: Yes

### **Column 4: NEGOTIATION**
- **Header**: "Negotiation [0]"
- **Color Accent**: Red
- **Meaning**: Actively negotiating terms
- **Auto-actions**: Auto-reminder every 3 days
- **Drag-to**: Yes

### **Column 5: CLOSED**
- **Header**: "Closed [0]"
- **Color Accent**: Purple
- **Meaning**: Completed deals (won/lost)
- **Auto-actions**: Archive old deals
- **Drag-to**: Yes

---

## **DEAL CARD STRUCTURE**

```
┌─────────────────────────────┐
│ Lead/Company Name           │
│ Company Name                │
├─────────────────────────────┤
│ ₹Deal Value                 │
│ Probability: X%             │
├─────────────────────────────┤
│ Tier: HOT/WARM/COOL/COLD   │
│ Expected Close: MM/DD       │
├─────────────────────────────┤
│ [✏️ Edit] [🗑️ Delete]       │
└─────────────────────────────┘
```

### **Card Information**

1. **Deal Name/ID**
   - Format: "Deal with [Company]"
   - Font: Bold, 14px
   - Clickable: Yes

2. **Company Name**
   - Font: Gray, 12px
   - Associated company

3. **Deal Value**
   - Display: ₹ Amount
   - Format: Currency (₹)
   - Example: ₹50,000

4. **Probability**
   - Display: 0-100%
   - Visual: Progress bar
   - Auto-based: On stage

5. **Tier**
   - Display: HOT/WARM/COOL/COLD
   - Source: AI-assigned
   - Color: Matching badge

6. **Expected Close Date**
   - Format: MM/DD/YY
   - Overdue: Red if past date
   - Countdown: Days remaining

7. **Owner**
   - Display: Team member name
   - Avatar: Small profile pic
   - Clickable: Filter by owner

### **Card Actions**
- **View** (👁️) - Opens detail page
- **Edit** (✏️) - Opens edit modal
- **Delete** (🗑️) - Deletes with confirmation

### **Card Styling**
- **Width**: Variable (column width ÷ max cards)
- **Height**: Auto-adjusting
- **Background**: White
- **Border**: 0.5px #e0e0e0
- **Shadow**: 0 2px 8px rgba(0,0,0,0.1)
- **Hover**: Lift, shadow intensifies
- **Animation**: 0.3s ease

---

## **DRAG-AND-DROP FUNCTIONALITY**

### **Enabled**: ✅ Yes

### **Actions**
- **Drag deal card** from one column to another
- **Drop** to change stage
- **Auto-save**: Immediately saves new stage
- **Undo**: Yes (last action)
- **Validation**: Prevents invalid transitions

### **Visual Feedback**
- Card lifts on drag
- Column highlights on hover
- Smooth drop animation
- Toast notification: "Deal moved to [Stage]"

---

## **CREATE DEAL MODAL**

### **Form Fields (8 fields)**

1. **Select Contact/Lead** (Required)
   - Type: Dropdown
   - Searchable: Yes
   - Create inline: Yes (add new contact)

2. **Deal Value** (Required)
   - Type: Number input
   - Currency: INR (₹)
   - Example: 50000

3. **Initial Stage** (Required)
   - Type: Dropdown
   - Options: New, Qualified, Proposal, Negotiation, Closed
   - Default: New

4. **Probability** (Optional)
   - Type: Slider
   - Range: 0-100%
   - Auto-calculate: If empty

5. **Expected Close Date** (Required)
   - Type: Date picker
   - Format: MM/DD/YYYY

6. **Deal Description** (Optional)
   - Type: Textarea
   - Notes: About the deal

7. **Owner/Assigned To** (Optional)
   - Type: Dropdown
   - Options: Team members
   - Default: Current user

8. **Associated Files** (Optional)
   - Type: File upload
   - Documents: Proposal, contracts, etc.

### **Form Buttons**
- [Create Deal] (Blue)
- [Cancel] (Gray)

---

## **DEAL DETAIL VIEW**

### **Section 1: Deal Overview**
- Deal name/ID
- Company
- Value
- Stage
- Owner
- Created date
- Last updated

### **Section 2: Deal Timeline**
- Stage change history
- Dates for each transition
- Who made changes

### **Section 3: Activity Log**
- All interactions
- Notes added
- Files attached
- Tasks completed

### **Section 4: Related Contacts**
- Decision makers involved
- Contact information
- Interaction history

### **Section 5: Documents**
- Uploaded files
- Proposals
- Contracts
- Email threads

### **Section 6: Probability Breakdown**
- Stage-based percentage
- Weighted factors
- Historical data

---

## **ADVANCED FEATURES**

✅ **Bulk Actions**: Select multiple deals for:
- Change stage
- Delete
- Export
- Email owner

✅ **Forecasting**: Pipeline value by:
- Month
- Quarter
- Custom period
- Chart visualization

✅ **Deal Health**:
- Stalled deals (no activity >7 days)
- At-risk deals (probability declining)
- Closing soon (within 7 days)
- Won deals

✅ **Probability Rules**: Auto-update based on:
- Stage progress
- Activity level
- Time in stage
- Historical success rate

---

---

# ☎️ TAB 5: CALLS

## **URL**: `/calls`

## **HEADER SECTION**
```
Title: "Calls"
Subtitle: "Track and log your sales calls"
```

---

## **STATISTICS CARDS (4 Cards)**

### **Card 1: Total Calls**
- **Label**: "Total Calls"
- **Value**: Count (e.g., 4)
- **Icon**: ☎️
- **Color**: Blue
- **Trend**: Optional

### **Card 2: Inbound Calls**
- **Label**: "Inbound"
- **Value**: Count (e.g., 1)
- **Icon**: 📥
- **Color**: Green

### **Card 3: Outbound Calls**
- **Label**: "Outbound"
- **Value**: Count (e.g., 3)
- **Icon**: 📤
- **Color**: Orange

### **Card 4: Avg Duration**
- **Label**: "Avg Duration"
- **Value**: Time (e.g., 4m 21s)
- **Icon**: ⏱️
- **Color**: Purple

---

## **TOOLBAR SECTION**

### **Log Call Button**
- **Label**: "+ Log Call"
- **Color**: Blue
- **Action**: Opens call logging form

### **Search Box**
- **Placeholder**: "Search by name or phone..."
- **Search By**: Name, Phone number, Company

### **Call Type Filter**
- **Label**: "All Types"
- **Options**: All, Inbound (📥), Outbound (📤), Conference
- **Default**: All

### **Outcome Filter**
- **Label**: "All Outcomes"
- **Options**: All, Positive, Neutral, Negative, No Answer
- **Default**: All

### **Date Range Selector**
- **Label**: "This Month"
- **Options**: Today, This Week, This Month, Last Month, Custom

---

## **CALL LOG TABLE**

### **Columns (8 columns)**

| Column | Content | Type |
|--------|---------|------|
| **Icon** | 📥 or 📤 | Icon |
| **Contact Name** | Name | Text (Clickable) |
| **Phone** | Phone number | Phone (Clickable) |
| **Date** | When call occurred | Date |
| **Duration** | Call length | Time |
| **Type** | Inbound/Outbound | Badge |
| **Outcome** | Positive/Neutral/Negative | Badge |
| **Actions** | View/Edit/Delete | Buttons |

### **Row Actions**
- [View] - Opens call detail
- [Edit] - Opens edit modal
- [Delete] - Deletes with confirmation

---

## **CALL RECORD DETAILS**

```
┌─────────────────────────────────┐
│ 📤 Contact Name                 │
│ Phone: +91-XXXXXXXXXX          │
│ Date: Aug 21, 2026              │
│ Time: 2:30 PM - 2:37 PM        │
│ Duration: 7m 30s                │
├─────────────────────────────────┤
│ Type: Outbound                  │
│ Outcome: ✓ Positive             │
│ Notes: Discussed proposal...     │
│ Next Follow-up: Aug 25           │
├─────────────────────────────────┤
│ [Edit] [Delete] [Schedule FU]   │
└─────────────────────────────────┘
```

### **Information Displayed**

1. **Contact Info**
   - Name (bold)
   - Phone (clickable)
   - Company (gray)

2. **Call Details**
   - Date & time
   - Duration (auto-calculated)
   - Call type (icon + label)
   - Outcome (color-coded)

3. **Call Recording** (if available)
   - Play button
   - Transcript link
   - Duration

4. **Notes**
   - What was discussed
   - Objections raised
   - Next steps
   - Follow-up date

5. **Linked Records**
   - Associated lead/contact
   - Related deal
   - Associated tasks

---

## **LOG CALL MODAL**

### **Form Fields (10 fields)**

1. **Select Contact** (Required)
   - Type: Dropdown
   - Searchable: Yes

2. **Phone Number** (Required)
   - Auto-populated: From contact
   - Override-able: Yes
   - Format: +91-XXXXXXXXXX

3. **Call Type** (Required)
   - Type: Dropdown
   - Options: Inbound, Outbound, Conference

4. **Start Time** (Required)
   - Type: Date & time picker
   - Default: Now

5. **End Time** (Required)
   - Type: Date & time picker
   - Auto-calculates: Duration

6. **Duration** (Auto-calculated)
   - Display: Calculated time
   - Format: Xm XXs
   - Editable: No

7. **Call Outcome** (Required)
   - Type: Dropdown
   - Options: Positive, Neutral, Negative, No Answer
   - Color indicators: Yes

8. **Reason for Call** (Optional)
   - Type: Dropdown
   - Options: Follow-up, Sales pitch, Problem resolution, Information gathering, Objection handling

9. **Call Notes** (Required)
   - Type: Textarea
   - Placeholder: "What was discussed?"
   - Min 10 characters
   - Max 500 characters
   - Char count: Yes

10. **Schedule Follow-up** (Optional)
    - Type: Checkbox to enable
    - Follow-up date: Date picker
    - Follow-up time: Time picker
    - Task description: Text input

### **Form Buttons**
- [Log Call] (Blue)
- [Cancel] (Gray)

---

## **CALL FEATURES**

✅ **Call Timer**
- Displays during active call logging
- Start/Stop/Pause buttons
- Real-time duration tracking
- Auto-stops on form submission

✅ **Call Transcription**
- Records call notes
- Voice-to-text (if available)
- Auto-summary generation

✅ **Follow-up Reminders**
- Auto-create task from call
- Notify on follow-up date
- Link to original call

✅ **Call History**
- All calls with same contact
- Chronological order
- Clickable to view previous calls

✅ **Call Analytics**
- Total calls by team member
- Average duration by type
- Conversion rate from calls
- Peak call times

---

---

# 📢 TAB 6: MARKETING

## **URL**: `/marketing`

## **HEADER SECTION**
```
Title: "Marketing"
Subtitle: "Manage campaigns and track performance"
```

---

## **STATISTICS CARDS (4 Cards)**

### **Card 1: Total Campaigns**
- **Label**: "Total Campaigns"
- **Value**: 3 (count)
- **Icon**: 📊
- **Color**: Blue
- **Clickable**: Yes → View all campaigns

### **Card 2: Active Campaigns**
- **Label**: "Active"
- **Value**: 1 (count)
- **Icon**: ▶️
- **Color**: Green
- **Description**: Currently running

### **Card 3: Total Recipients**
- **Label**: "Total Recipients"
- **Value**: 6,700 (count)
- **Icon**: 👥
- **Color**: Orange
- **Description**: Total people reached

### **Card 4: Avg Engagement**
- **Label**: "Avg Engagement"
- **Value**: 38% (percentage)
- **Icon**: 📈
- **Color**: Purple
- **Description**: Average across all campaigns

---

## **TOOLBAR SECTION**

### **New Campaign Button**
- **Label**: "+ New Campaign"
- **Color**: Blue
- **Action**: Opens campaign creation form

### **Status Filter**
- **Label**: "All Status"
- **Options**: All, Draft, Active, Scheduled, Completed, Paused
- **Multi-select**: Yes

### **Channel Filter**
- **Label**: "All Channels"
- **Options**: Email, SMS, WhatsApp, LinkedIn, Facebook, Instagram, Paid Ads, Landing Page
- **Multi-select**: Yes

### **Sort Options**
- By Engagement (High to Low)
- By Recipients (Most to Least)
- By Date Created (Newest first)
- By Performance (Best to Worst)

---

## **CAMPAIGN CARDS GRID**

### **Card Layout**
- **Grid**: Responsive (2-4 columns)
- **Card Width**: 320px min
- **Card Height**: Auto
- **Gap**: 16px
- **Mobile**: 1 column

### **Campaign Card Structure**

```
┌────────────────────────────────────┐
│ 📧 Campaign Name                   │
│ Campaign Type (Insurance...)       │
├────────────────────────────────────┤
│ Status: ACTIVE (Green badge)       │
│ Channel: Email                     │
│ Recipients: 2,500                  │
├────────────────────────────────────┤
│ Opens: 890 (36%)                   │
│ Clicks: 975 (39% CTR)              │
│ Conversions: 47                    │
│ ROI: 340%                          │
├────────────────────────────────────┤
│ Progress: ▮▮▮░░░░░░ 40%           │
│ Start: Aug 15  |  End: Aug 30      │
├────────────────────────────────────┤
│ [View] [Edit] [Pause] [Delete]     │
└────────────────────────────────────┘
```

### **Card Information**

1. **Campaign Name**
   - Display: Bold, 16px
   - Icon: Matching channel (📧📱💬🔗)

2. **Campaign Type**
   - Display: Description
   - Font: Gray, 12px

3. **Status Badge**
   - Active (Green)
   - Draft (Blue)
   - Scheduled (Yellow)
   - Completed (Gray)
   - Paused (Orange)

4. **Channel**
   - Display: Email, SMS, WhatsApp, etc.
   - Icon + text

5. **Recipient Count**
   - Display: Total reached
   - Format: 2,500 (thousands)

6. **Engagement Metrics**
   - **Opens**: Number + %
   - **Clicks**: Number + CTR %
   - **Conversions**: Lead count
   - **ROI**: Return %

7. **Progress Bar**
   - Visual: Filled/unfilled
   - Display: X% Complete
   - Color: Based on status

8. **Duration**
   - Start date
   - End date
   - Days remaining (if active)

9. **Card Actions**
   - [View] - Opens campaign detail
   - [Edit] - Opens edit form
   - [Pause/Resume] - Toggle status
   - [Delete] - Deletes campaign

---

## **CAMPAIGN DETAIL VIEW**

### **Section 1: Campaign Overview**
- Name, type, channel
- Status, owner
- Start/end dates
- Description
- Budget

### **Section 2: Campaign Stats**
- Recipients sent
- Open rate (%)
- Click rate (%)
- Conversion rate (%)
- Revenue generated
- ROI (%)

### **Section 3: Performance Charts**
- Opens over time (line chart)
- Clicks over time (line chart)
- Conversion funnel (chart)
- Revenue by day (bar chart)

### **Section 4: Recipient Segments**
- List of target segments
- Segment criteria
- Recipient count per segment
- Performance per segment

### **Section 5: Email Content**
- Subject line
- Preview text
- Full email body (rendered)
- Send time

### **Section 6: Performance by Link**
- Links in campaign
- Click count per link
- Click-through rate
- Conversion rate

### **Section 7: Subscriber Actions**
- List of who opened
- List of who clicked
- List of converters
- Export lists

### **Section 8: Campaign History**
- Created date/by
- Last edited
- Modifications made
- Performance timeline

---

## **CREATE CAMPAIGN MODAL**

### **Form Fields (15 fields)**

1. **Campaign Name** (Required)
   - Type: Text input
   - Example: "Insurance Awareness Q3"
   - Max length: 100

2. **Campaign Type** (Required)
   - Type: Dropdown
   - Options: Awareness, Lead Generation, Nurture, Re-engagement, Promotion, Educational

3. **Select Channel** (Required)
   - Type: Dropdown
   - Options: Email, SMS, WhatsApp, LinkedIn, Facebook, Instagram, Paid Ads

4. **Target Audience** (Required)
   - Type: Select segments
   - Build new: Yes
   - Filters:
     - Industry
     - Company size
     - Location
     - Product interest
     - Past engagement

5. **Budget** (Optional)
   - Type: Number input
   - Currency: INR (₹)

6. **Campaign Duration** (Required)
   - Start date: Date picker
   - End date: Date picker

7. **Frequency** (Optional)
   - Type: Dropdown
   - Options: One-time, Daily, Weekly, Monthly

8. **Campaign Subject** (Optional)
   - Type: Text input
   - For email: Email subject line
   - For SMS: Message preview
   - Char limit: 100

9. **Campaign Content** (Optional)
   - Type: Textarea
   - Rich text editor: Yes
   - Template selector: Yes
   - Preview option: Yes

10. **Call-to-Action** (Optional)
    - Text for CTA button
    - Link/destination
    - Button color

11. **Tracking Options** (Optional)
    - Enable link tracking (checkbox)
    - UTM parameters
    - Conversion tracking

12. **Sender Info** (Required for email)
    - From name
    - From email address
    - Reply-to email

13. **Schedule Send** (Optional)
    - Send immediately: Checkbox
    - Date to send: Date picker
    - Time to send: Time picker

14. **Automation** (Optional)
    - Auto-follow-up (checkbox)
    - Resend to unopened (checkbox)
    - Days to wait for resend

15. **Tags** (Optional)
    - Add campaign tags
    - For organization/filtering

### **Form Buttons**
- [Create Campaign] (Blue)
- [Save as Draft] (Gray)
- [Cancel] (Gray)

---

## **CAMPAIGN FEATURES**

✅ **Email Templates**
- Pre-built templates
- Drag-and-drop builder
- Custom branding

✅ **A/B Testing**
- Test subject lines
- Test content
- Test send times
- Auto-pick winner

✅ **Automation Rules**
- Auto-follow-up based on action
- Auto-segment based on engagement
- Trigger-based campaigns

✅ **Recipient Management**
- View sent list
- View opened list
- View clicked list
- Unsubscribe management
- Bounce handling

✅ **Performance Reporting**
- Real-time statistics
- Comparison to past campaigns
- Benchmarking
- Custom report builder

---

---

# 📈 TAB 7: REPORTS

## **URL**: `/reports`

## **HEADER SECTION**
```
Title: "Reports"
Subtitle: "Analyze your business metrics"
```

---

## **TAB NAVIGATION (3 Tabs)**

### **Tab 1: Sales Reports**
- Label: "💰 Sales"
- Default: Active
- Content: Sales analytics

### **Tab 2: Contacts Reports**
- Label: "👥 Contacts"
- Content: Contact analytics

### **Tab 3: Calls Reports**
- Label: "☎️ Calls"
- Content: Call analytics

---

## **TOOLBAR (Common to all tabs)**

### **Date Range Selector**
- **Label**: "This Month"
- **Options**:
  - This Month (default)
  - Last Month
  - Last Quarter
  - This Year
  - Last Year
  - Custom Range (date picker)

### **Export Button**
- **Label**: "📥 Export"
- **Formats**: PDF, Excel, CSV, Email report

---

## **SALES REPORTS TAB**

### **Statistics Cards (4 Cards)**

#### **Card 1: Total Revenue**
- **Value**: ₹5,25,000
- **Trend**: +12%
- **Icon**: 💰
- **Color**: Green

#### **Card 2: Deals Closed**
- **Value**: 8
- **Trend**: +2
- **Icon**: ✓
- **Color**: Blue

#### **Card 3: Win Rate**
- **Value**: 68%
- **Trend**: +5%
- **Icon**: 🎯
- **Color**: Orange

#### **Card 4: Avg Deal Size**
- **Value**: ₹65,625
- **Trend**: -3%
- **Icon**: 📊
- **Color**: Purple

### **Charts**

#### **Chart 1: Revenue Trend**
- **Type**: Line chart
- **X-axis**: Months (Jan-Dec)
- **Y-axis**: Revenue amount
- **Display**: Blue line
- **Hover**: Shows exact amount

#### **Chart 2: Sales by Stage**
- **Type**: Horizontal bar chart
- **Stages**: New, Qualified, Proposal, Negotiation, Closed
- **Display**: Deal count or value per stage
- **Color**: Each stage different

#### **Chart 3: Top Deals**
- **Type**: Table/cards
- **Columns**: Deal name, Value, Stage, Expected close
- **Sort**: By value (highest first)
- **Count**: Top 10 deals

### **Data Table: Sales Performance**

| Column | Content | Type | Sortable |
|--------|---------|------|----------|
| **Deal Name** | Deal identifier | Text | ✅ Yes |
| **Company** | Company name | Text | ✅ Yes |
| **Value** | ₹ Amount | Currency | ✅ Yes |
| **Stage** | Current stage | Badge | ✅ Yes |
| **Probability** | 0-100% | Number | ✅ Yes |
| **Expected Close** | MM/DD/YYYY | Date | ✅ Yes |
| **Owner** | Sales person | Text | ✅ Yes |

### **Table Features**
- Sortable columns
- Filterable by stage
- Searchable
- Pagination (10 per page)
- Export to Excel

---

## **CONTACTS REPORTS TAB**

### **Statistics Cards (4 Cards)**

#### **Card 1: Total Contacts**
- **Value**: 150
- **Trend**: +8
- **Icon**: 👥
- **Color**: Blue

#### **Card 2: Active Contacts**
- **Value**: 95
- **Trend**: +5
- **Icon**: ✓
- **Color**: Green

#### **Card 3: Conversion Rate**
- **Value**: 42%
- **Trend**: +3%
- **Icon**: 📈
- **Color**: Orange

#### **Card 4: Avg Contact Score**
- **Value**: 65
- **Trend**: +8
- **Icon**: ⭐
- **Color**: Purple

### **Charts**

#### **Chart 1: Contact Status Distribution**
- **Type**: Pie chart
- **Segments**: New, Active, Interested, Customer
- **Display**: % and count
- **Color**: Each status different

#### **Chart 2: Contacts by Industry**
- **Type**: Horizontal bar chart
- **Display**: Top 10 industries
- **Count**: Contacts per industry

#### **Chart 3: Engagement Timeline**
- **Type**: Area chart
- **X-axis**: Days/Weeks/Months
- **Y-axis**: Engagement level
- **Display**: Trends over time

### **Data Table: Contact Details**

| Column | Content | Type |
|--------|---------|------|
| **Name** | Contact name | Clickable |
| **Company** | Company name | Text |
| **Status** | Contact status | Badge |
| **Last Contact** | Date | Date |
| **Engagement** | Score | Number |
| **Owner** | Assigned to | Text |

---

## **CALLS REPORTS TAB**

### **Statistics Cards (4 Cards)**

#### **Card 1: Total Calls**
- **Value**: 250
- **Trend**: +45
- **Icon**: ☎️
- **Color**: Blue

#### **Card 2: Avg Call Duration**
- **Value**: 4m 30s
- **Trend**: +30s
- **Icon**: ⏱️
- **Color**: Green

#### **Card 3: Conversion from Calls**
- **Value**: 38%
- **Trend**: +5%
- **Icon**: 🎯
- **Color**: Orange

#### **Card 4: Calls by Team**
- **Value**: 8 (avg per person)
- **Trend**: +2
- **Icon**: 👥
- **Color**: Purple

### **Charts**

#### **Chart 1: Call Volume Trend**
- **Type**: Column chart
- **X-axis**: Weeks/Months
- **Y-axis**: Call count
- **Display**: Inbound vs Outbound (stacked)

#### **Chart 2: Call Outcomes**
- **Type**: Pie chart
- **Segments**: Positive, Neutral, Negative, No Answer
- **Display**: % and count

#### **Chart 3: Call Duration by Type**
- **Type**: Bar chart
- **Categories**: Inbound, Outbound, Conference
- **Display**: Average duration

### **Data Table: Call Summary**

| Column | Content | Type |
|--------|---------|------|
| **Date** | Date & time | Date |
| **Contact** | Contact name | Text |
| **Type** | Inbound/Outbound | Badge |
| **Duration** | Time | Time |
| **Outcome** | Result | Badge |
| **Owner** | Who made call | Text |

---

## **REPORT FEATURES**

✅ **Export Functionality**
- PDF reports with branding
- Excel spreadsheets
- CSV for data import
- Email reports automatically

✅ **Scheduled Reports**
- Set reports to run weekly/monthly
- Auto-email results
- Alert on threshold changes

✅ **Custom Reports**
- Select metrics to display
- Drag-and-drop builder
- Save custom report templates
- Share with team

✅ **Drill-Down Capability**
- Click on chart data
- View underlying records
- Filter and refine
- Export subset

✅ **Comparison Reports**
- Compare periods (YoY, MoM)
- Compare segments
- Benchmark against targets
- Identify trends

---

---

# ⚙️ TAB 8: INTEGRATIONS

## **URL**: `/integrations`

## **HEADER SECTION**
```
Title: "Integrations"
Subtitle: "Connect and manage third-party services"
```

---

## **CONNECTED INTEGRATIONS (5 Active)**

### **Integration 1: Gmail**
```
📧 Gmail
────────────────────────
Status: ✓ Connected (Green)
Connected: 2 hours ago
Account: user@gmail.com

Features:
✓ Email sync
✓ Contact sync
✓ Email tracking

Last synced: Now

[Settings] [Disconnect]
```

**Details**:
- Connected email account
- Sync frequency: Real-time
- Features: Read, compose, track emails
- Data synced: Emails, attachments, contacts

### **Integration 2: Google Calendar**
```
📅 Google Calendar
────────────────────────
Status: ✓ Connected (Green)
Connected: 1 hour ago

Features:
✓ Meeting scheduling
✓ Event sync
✓ Conflict detection

Calendars synced: 2

[Settings] [Disconnect]
```

**Details**:
- Sync calendars (primary + work)
- Auto-create events from deals
- Send meeting invites
- Block time for calls

### **Integration 3: Zapier**
```
⚡ Zapier
────────────────────────
Status: ✓ Connected (Green)
Connected: 30 minutes ago

Active Zaps: 8

Sample Zaps:
• New contact → Slack
• New deal → Gmail reminder
• Call logged → Task creation
• Email opened → DB update

[Manage Zaps] [Disconnect]
```

**Details**:
- 8 active automation workflows
- Connects to 50+ apps
- Real-time triggers
- Conditional actions

### **Integration 4: Slack**
```
💬 Slack
────────────────────────
Status: ○ Disconnected (Gray)
Last connected: Never

Features Available:
• Deal notifications
• Lead alerts
• Team collaboration
• Daily reports

[Connect Now]
```

**Details**:
- Not yet connected
- Click to authorize
- Select channel for notifications
- Configure alert types

### **Integration 5: HubSpot**
```
🎯 HubSpot
────────────────────────
Status: ✓ Connected (Green)
Connected: 5 minutes ago
Account: company@domain.com

Features:
✓ Contact sync
✓ Deal sync
✓ Email tracking
✓ Pipeline management

[Settings] [Disconnect]
```

**Details**:
- Bidirectional sync
- Auto-update contacts/deals
- Email tracking enabled
- Pipeline sync every 15 min

---

## **AVAILABLE INTEGRATIONS (Coming Soon)**

```
👥 Microsoft Teams
Status: Coming Soon
[Notify Me]

💬 WhatsApp Business
Status: Coming Soon
[Notify Me]

📱 Twilio (SMS)
Status: Coming Soon
[Notify Me]
```

---

## **INTEGRATION CONNECTION MODAL**

### **Modal Structure**

1. **Integration Name & Logo**
   - Icon display
   - Full integration name
   - Description

2. **Features List**
   - Bullet list of what it does
   - What data it accesses
   - Frequency of sync

3. **Connection Instructions**
   - Step-by-step guide
   - "Authorize with [Service]" button
   - Redirects to service login
   - Auto-returns after auth

4. **Permissions Required**
   - Read emails
   - Write calendar events
   - Access contacts
   - Create tasks, etc.

5. **Configuration Options**
   - Sync frequency
   - Which data to sync
   - Notification preferences
   - Auto-action settings

6. **Connect Button**
   - "Authorize [Service]" (primary)
   - "Cancel" (secondary)

---

## **INTEGRATION SETTINGS**

### **Sync Frequency**
- Real-time (default)
- Every 15 minutes
- Every hour
- Every day
- Manual only

### **Data to Sync**
- ☑️ Contacts
- ☑️ Deals
- ☑️ Emails
- ☑️ Calendar events
- ☑️ Tasks
- ☑️ Files
- ☑️ Custom fields

### **Notification Settings**
- Alert on new contact
- Alert on new deal
- Alert on missed email
- Alert on integration error

### **Auto-Actions**
- Create task on deal stage change
- Add note on email open
- Update contact on interaction
- Sync custom fields

### **Data Mapping** (advanced)
- Map CRM fields to service fields
- Custom field mapping
- Transformation rules

### **Test Connection**
- Button to verify integration
- Test data sync
- Show last sync timestamp
- Show error logs

---

## **INTEGRATION STATUS & MONITORING**

**For each connected integration**:

- **Connection Status**
  - Green (Connected)
  - Yellow (Warning - sync delayed)
  - Red (Error - disconnected)

- **Last Sync**
  - "Synced just now"
  - "Synced 2 hours ago"
  - Show timestamp

- **Sync Health**
  - Records synced today
  - Sync errors (if any)
  - Failed records

- **Activity Log**
  - Click to view:
     - When sync occurred
     - Records changed
     - Errors encountered
     - User actions

---

## **INTEGRATION FEATURES**

✅ **Bidirectional Sync**
- Changes in CRM update service
- Changes in service update CRM
- Conflict resolution

✅ **Field Mapping**
- Map CRM fields to service fields
- Support for custom fields
- Data transformation

✅ **Error Handling**
- Automatic retry on failure
- Error logging and alerts
- Manual sync option

✅ **Security**
- OAuth authentication
- No passwords stored
- Encrypted data transmission
- Audit logs

✅ **Automation**
- Workflow triggers
- Conditional actions
- Scheduled syncs
- Bulk operations

---

---

# ⚡ TAB 9: SETTINGS

## **URL**: `/settings`

## **HEADER SECTION**
```
Title: "Settings"
Subtitle: "Manage your account and preferences"
```

---

## **TAB NAVIGATION (4 Tabs)**

### **Tab 1: Profile**
- Label: "👤 Profile"
- Default: Active
- Content: Personal information

### **Tab 2: Preferences**
- Label: "⚙️ Preferences"
- Content: App behavior & defaults

### **Tab 3: Security**
- Label: "🔒 Security"
- Content: Password & authentication

### **Tab 4: Integrations**
- Label: "🔗 Integrations"
- Content: Connected apps

---

## **PROFILE SETTINGS TAB**

### **Section 1: Personal Information**

#### **Form Fields**

1. **Full Name**
   - Type: Text input
   - Editable: ✅ Yes
   - Required: Yes
   - Max length: 100

2. **Email Address**
   - Type: Email input
   - Editable: ✅ Yes
   - Verified: ✅ Yes (blue checkmark)
   - Unique: Yes

3. **Phone Number**
   - Type: Phone input
   - Editable: ✅ Yes
   - Format: +91-XXXXXXXXXX

4. **Job Title**
   - Type: Text input
   - Editable: ✅ Yes
   - Examples: CEO, Sales Manager
   - Max length: 50

5. **Department**
   - Type: Dropdown
   - Options: Sales, Marketing, Management, Support, Other
   - Editable: ✅ Yes

6. **Company Name**
   - Type: Text (display only)
   - Editable: ❌ No
   - Current: ArthaInvest

### **Section 2: Profile Picture**

- **Upload Area**: Drag-and-drop or click
- **Current**: Avatar/profile pic
- **Formats**: JPG, PNG, GIF
- **Max Size**: 5MB
- **Dimensions**: 200x200px
- **Actions**: [Change] [Remove]

### **Save Button**
- **Label**: "Save Changes"
- **Color**: Blue
- **Confirmation**: "Changes saved successfully"

---

## **PREFERENCES SETTINGS TAB**

### **Section 1: Notification Settings**

#### **Email Notifications** (Toggle switches)

1. **New Lead Notification**
   - Toggle: ✅ On/Off
   - Frequency: Real-time / Daily digest / Weekly digest

2. **Deal Movement Alert**
   - Toggle: ✅ On/Off
   - Frequency: Real-time / Daily / Off

3. **Upcoming Meeting Reminder**
   - Toggle: ✅ On/Off
   - Frequency: 1 hour before / 30 min before / 15 min before

4. **Daily Sales Summary**
   - Toggle: ✅ On/Off
   - Time: Dropdown (9 AM, 5 PM, etc.)

5. **Weekly Performance Report**
   - Toggle: ✅ On/Off
   - Day: Dropdown (Friday, Monday, etc.)
   - Time: Dropdown

6. **Team Updates**
   - Toggle: ✅ On/Off
   - Frequency: Daily / Weekly

7. **System Notifications**
   - Toggle: ✅ On/Off

---

### **Section 2: App Preferences**

#### **Display Settings**

1. **Theme**
   - Dropdown: Light / Dark / Auto (system default)
   - Current: Light
   - Preview: Shows theme sample

2. **Date Format**
   - Dropdown: MM/DD/YYYY / DD/MM/YYYY / YYYY-MM-DD
   - Current: MM/DD/YYYY

3. **Time Format**
   - Dropdown: 12-hour (AM/PM) / 24-hour
   - Current: 12-hour

4. **Currency**
   - Dropdown: INR (₹) / USD ($) / EUR (€) / etc.
   - Current: INR (₹)

5. **Timezone**
   - Dropdown: IST (Asia/Kolkata), PST, EST, etc.
   - Current: IST

6. **Language**
   - Dropdown: English, Hindi, Spanish, etc.
   - Current: English

---

### **Section 3: Behavior Settings**

1. **Auto-Save**
   - Toggle: ✅ On/Off

2. **Keyboard Shortcuts**
   - Toggle: ✅ On/Off
   - Link: "View all shortcuts"

3. **Compact View**
   - Toggle: ✅ On/Off

4. **Default Page on Login**
   - Dropdown: Dashboard / Pipeline / Reports / etc.
   - Current: Dashboard

5. **Page Load Animation**
   - Toggle: ✅ On/Off

6. **Pagination Size**
   - Dropdown: 10 / 25 / 50 / 100
   - Current: 10

---

## **SECURITY SETTINGS TAB**

### **Section 1: Password & Authentication**

#### **Change Password**

1. **Current Password**
   - Type: Password (masked)
   - Required: Yes

2. **New Password**
   - Type: Password (masked)
   - Requirements:
     - Min 8 characters
     - 1 uppercase letter
     - 1 number
     - 1 special character
   - Strength indicator: Weak/Medium/Strong

3. **Confirm Password**
   - Type: Password (masked)
   - Validation: Must match

4. **[Change Password] Button**
   - Color: Blue
   - Confirmation: "Password changed successfully"

---

### **Section 2: Two-Factor Authentication (2FA)**

1. **Status**
   - Display: "Not enabled" (red)

2. **Enable 2FA Button**
   - Label: "Enable Two-Factor Authentication"
   - Color: Blue
   - Opens: Setup modal

3. **2FA Setup Modal**
   - Step 1: Download authenticator app
   - Step 2: Scan QR code
   - Step 3: Enter 6-digit code
   - Backup codes: Display & download

**After Enabled**:
- Status: "Enabled" (green)
- Options: [Disable] [Download Backup Codes] [Regenerate]

---

### **Section 3: Active Sessions**

```
┌────────────────────────────────────────┐
│ Device: Windows - Chrome               │
│ IP Address: 192.168.1.100              │
│ Location: Delhi, India                 │
│ Last Active: Now                       │
│ [Sign Out] [This Device]               │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│ Device: Mac - Safari                   │
│ IP Address: 192.168.1.105              │
│ Location: Mumbai, India                │
│ Last Active: 2 hours ago               │
│ [Sign Out]                             │
└────────────────────────────────────────┘
```

**Features**:
- View all active sessions
- Device info (OS, browser)
- IP address and location
- Last activity time
- Sign out other devices
- Sign out all except current

---

### **Section 4: Login History**

| Column | Content |
|--------|---------|
| **Date & Time** | When login occurred |
| **Device** | OS and browser |
| **IP Address** | Login source |
| **Location** | Geo-location |
| **Status** | Successful/Failed |

**Features**:
- View last 30 logins
- Identify suspicious activity
- [Report Suspicious Activity] link

---

## **INTEGRATIONS SETTINGS TAB**

### **Connected Integrations List**

1. Gmail - Connected ✓ - [Settings] [Disconnect]
2. Google Calendar - Connected ✓ - [Settings] [Disconnect]
3. Zapier - Connected ✓ - [Settings] [Disconnect]
4. HubSpot - Connected ✓ - [Settings] [Disconnect]
5. Slack - Not Connected - [Connect]

**Features**:
- Toggle integrations on/off
- Modify settings
- Disconnect apps
- View last sync time
- Check connection status

---

## **DANGER ZONE SECTION**

```
┌────────────────────────────────┐
│ ⚠️ Danger Zone                 │
├────────────────────────────────┤
│                                │
│ Delete Account                 │
│ Permanently delete your        │
│ account and all associated data│
│ [Delete Account] (Red)         │
│                                │
│ Download Data                  │
│ Export all your data as JSON   │
│ [Download] (Gray)              │
│                                │
└────────────────────────────────┘
```

### **Delete Account**
- Requires password confirmation
- Shows warning message
- 30-day recovery period
- [Yes, Delete] confirmation

### **Download Data**
- Exports: Contacts, Leads, Deals, Calls, etc.
- Format: JSON file
- Download starts immediately
- Email copy also sent

---

## **SETTINGS FEATURES**

✅ **Profile Management**
- Update personal info
- Change profile picture
- Add bio/about
- Manage preferences

✅ **Privacy Controls**
- Who can see profile
- Visibility settings
- Data sharing preferences

✅ **Security**
- Change password
- Enable 2FA
- View active sessions
- Login history
- Suspicious activity alerts

✅ **Communication**
- Notification preferences
- Email digest options
- Alert frequencies
- Channel preferences

✅ **Account Management**
- Download data export
- Delete account
- Manage API keys
- Webhook settings

✅ **Help & Support**
- [Contact Support] link
- [Read FAQ] link
- [View Documentation] link
- [Report Bug] link

---

---

# 📊 COMPLETE FEATURE SUMMARY

## **Total Features Across All 9 Tabs**: **117+**

| Tab | Key Features | Count |
|-----|--------------|-------|
| 📊 Dashboard | KPI cards, Metrics, Recent leads table | 8 |
| 👥 Contacts | Search, Filter, CRUD, Modal form, Advanced CRUD | 16 |
| 📋 Leads | Scoring, Tier assignment, Activity log, Detail view | 12 |
| 💼 Pipeline | Kanban board, Drag-drop, Deal cards, Forecasting | 18 |
| ☎️ Calls | Call log, Timer, Statistics, Follow-ups, Analytics | 10 |
| 📢 Marketing | Campaign management, A/B testing, Analytics, Automation | 15 |
| 📈 Reports | Multi-tab analytics, Charts, Export, Comparison | 12 |
| ⚙️ Integrations | 5+ connected apps, Settings, Sync control, Bidirectional | 8 |
| ⚡ Settings | Profile, Preferences, Security, 2FA, Sessions | 18 |

---

## **Key Dropdowns**: **25+ Dropdown Menus**
## **Form Fields**: **80+ Input Fields**
## **Buttons & Actions**: **150+ Interactive Elements**
## **Data Visualizations**: **15+ Charts & Tables**
## **Filter Options**: **40+ Filter Combinations**

---

**✅ COMPLETE CRM SYSTEM - FULLY DOCUMENTED!**

