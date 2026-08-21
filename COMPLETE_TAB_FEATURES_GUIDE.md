# 📱 ARTHAINVEST CRM - COMPLETE TAB FEATURES GUIDE

**Document Version**: Phase 1 Complete  
**Total Tabs**: 9  
**Last Updated**: August 21, 2026

---

# 🎯 QUICK NAVIGATION

1. [📊 Dashboard](#1--dashboard)
2. [👥 Contacts](#2--contacts)
3. [📋 Leads](#3--leads)
4. [💼 Pipeline](#4--pipeline)
5. [☎️ Calls](#5--calls)
6. [📢 Marketing](#6--marketing)
7. [📈 Reports](#7--reports)
8. [⚙️ Integrations](#8--integrations)
9. [⚡ Settings](#9--settings)

---

# 1️⃣ **📊 DASHBOARD**

**URL**: `/dashboard`  
**Status**: ✅ Active  
**Purpose**: View all KPIs and business metrics at a glance

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Dashboard                                   │
│ Welcome back! Here's your sales overview.   │
│ Friday, Aug 21                              │
└─────────────────────────────────────────────┘
```
- **Title**: "Dashboard"
- **Subtitle**: "Welcome back! Here's your sales overview."
- **Date Display**: Current date (auto-updates)

---

### **B) KPI Cards Section** (4 Cards - Horizontal Row)

#### **Card 1: Total Leads**
- **Icon**: 📊
- **Label**: "Total Leads"
- **Value**: Displays count (currently: 1)
- **Trend**: Shows percentage change (e.g., +12%)
- **Color Accent**: Blue (#3498db)
- **Border**: 4px left border (blue)
- **Hover Effect**: Lift animation (-4px), enhanced shadow
- **Click Action**: Drill down to leads detail
- **Responsive**: 4 columns desktop, 2 columns tablet, 1 column mobile

#### **Card 2: Qualified Leads**
- **Icon**: ✓
- **Label**: "Qualified Leads"
- **Value**: Count of qualified leads (currently: 0)
- **Trend**: Conversion rate percentage (e.g., 0% conv.)
- **Color Accent**: Green (#2ecc71)
- **Border**: 4px left border (green)
- **Calculation**: Leads with status = "qualified"
- **Hover Effect**: Lift animation, color intensification

#### **Card 3: Active Deals**
- **Icon**: 💼
- **Label**: "Active Deals"
- **Value**: Count of active deals (currently: 4)
- **Trend**: Pipeline value in rupees (e.g., ₹34.5L)
- **Color Accent**: Orange (#f39c12)
- **Border**: 4px left border (orange)
- **Calculation**: Deals where stage ≠ 'closed'
- **Format**: Currency display (₹)

#### **Card 4: Closed Deals**
- **Icon**: 🎯
- **Label**: "Closed Deals"
- **Value**: Count of closed deals (currently: 0)
- **Trend**: Growth percentage (e.g., +8%)
- **Color Accent**: Red (#e74c3c)
- **Border**: 4px left border (red)
- **Calculation**: Deals where stage = 'closed'

**Card Styling**:
- **Height**: 140px
- **Width**: Responsive (4 equal columns)
- **Background**: White (#ffffff)
- **Shadow**: 0 4px 12px rgba(0,0,0,0.1)
- **Padding**: 20px
- **Transition**: 0.3s ease

---

### **C) Pipeline Performance Section**

**Title**: "Pipeline Performance"

#### **Metric 1: Total Pipeline Value**
- **Label**: "Total Pipeline Value"
- **Value**: ₹34.50L (Lakhs format)
- **Icon**: 💰
- **Border**: 3px top border (#667eea)
- **Calculation**: SUM of all active deal values
- **Format**: Currency (Indian Rupees)

#### **Metric 2: Average Deal Value**
- **Label**: "Average Deal Value"
- **Value**: ₹86.3K (Thousands format)
- **Icon**: 📊
- **Border**: 3px top border (#667eea)
- **Calculation**: Total Value ÷ Number of Active Deals
- **Example**: ₹345K ÷ 4 deals = ₹86.25K

#### **Metric 3: Conversion Rate**
- **Label**: "Conversion Rate"
- **Value**: 0% (Percentage)
- **Icon**: 📈
- **Border**: 3px top border (#667eea)
- **Calculation**: (Qualified Leads ÷ Total Leads) × 100
- **Benchmark**: Typically 30-50% target
- **Current**: 0 qualified ÷ 1 total = 0%

#### **Metric 4: Active Opportunities**
- **Label**: "Active Opportunities"
- **Value**: 4 (Count)
- **Icon**: 🎯
- **Border**: 3px top border (#667eea)
- **Calculation**: Sum of deals in pipeline (non-closed)
- **Shows**: Total active deals in progress

**Metric Box Styling**:
- **Layout**: 4 boxes per row (responsive)
- **Height**: 120px
- **Background**: White (#ffffff)
- **Padding**: 16px
- **Gap**: 15px between boxes
- **Hover**: Lift effect, enhanced shadow, color change

---

### **D) Recent Leads Table**

**Title**: "Recent Leads"

**Table Structure**: 5 Columns × 5 Rows

#### **Column 1: Name**
- **Content**: Lead name (clickable)
- **Font**: Bold, 14px
- **Color**: Dark (#2c3e50)
- **Function**: Click to view lead detail
- **Examples**:
  - Neha Singh
  - Vikram Reddy
  - Anjali Desai
  - Amit Patel
  - Priya Kapoor

#### **Column 2: Company**
- **Content**: Company name
- **Font**: Regular, 14px
- **Color**: Gray (#7f8c8d)
- **Examples**:
  - StartUp Fund
  - Tech Park
  - Retail Chain
  - Manufacturing
  - Digital Ventures

#### **Column 3: Status**
- **Content**: Lead status badge (color-coded)
- **Font**: 12px, bold
- **Options**:
  - **New** → Blue (#3498db)
  - **Qualified** → Green (#2ecc71)
  - **Proposal** → Orange (#f39c12)
  - **Negotiation** → Red (#e74c3c)
  - **Closed** → Purple (#9b59b6)
- **Background**: Semi-transparent color
- **Border Radius**: 4px

#### **Column 4: Tier**
- **Content**: AI-assigned tier (HOT/WARM/COOL/COLD)
- **Font**: Bold, 13px
- **Color**: Primary blue (#667eea)
- **Current State**: Shows "-" (no tier assigned yet)
- **Calculation**: Based on AI scoring algorithm

#### **Column 5: Score**
- **Content**: Lead score (0-100)
- **Font**: Bold, 13px
- **Color**: Primary blue (#667eea)
- **Current State**: Shows "-" (pending)
- **Updates**: Auto-calculates based on engagement
- **Algorithm**: Multi-factor scoring system

**Table Styling**:
- **Background**: White
- **Header**: Light gray (#f8f9fa)
- **Rows**: Alternating white/slight gray
- **Hover**: Light blue highlight (#f0f1f5)
- **Border**: 0.5px #e0e0e0
- **Padding**: 12px per cell
- **Row Height**: 50px
- **Font Size**: 14px body, 12px labels

**Table Features**:
- ✅ Sortable columns (click header)
- ✅ Clickable rows (view detail)
- ✅ Responsive design (scrollable on mobile)
- ✅ Pagination (5 rows per page)
- ✅ Search integration

---

### **E) Real-Time Updates**
- ✅ Auto-refresh every 30 seconds
- ✅ Live data from API
- ✅ Smooth animations
- ✅ No manual refresh needed

---

### **F) Responsive Breakpoints**

**Desktop (1280px+)**:
- 4-column KPI layout
- 2-row metrics layout
- Full-width table
- All elements visible

**Tablet (768px-1024px)**:
- 2-column KPI layout (2 rows)
- 2-column metrics (2 rows)
- Scrollable table
- Reduced padding

**Mobile (<768px)**:
- 1-column KPI layout (4 rows)
- 1-column metrics (4 rows)
- Horizontal scroll table
- Hamburger menu sidebar
- Full-width content

---

---

# 2️⃣ **👥 CONTACTS**

**URL**: `/contacts`  
**Status**: ✅ Active  
**Purpose**: Manage and organize contact database

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Contacts                                    │
│ Manage your sales contacts and leads        │
└─────────────────────────────────────────────┘
```

### **B) Toolbar Section**

#### **Search Box**
- **Placeholder**: "Search contacts..."
- **Scope**: Searches by:
  - Name
  - Email
  - Phone
  - Company
- **Real-time**: Live filtering as you type
- **Clear Button**: ✅ Yes (X button to clear)

#### **Status Filter Dropdown**
- **Label**: "All Status"
- **Default**: Shows "All Status"
- **Options Available**:
  - ✅ All Status (Show all)
  - ✅ New (New contacts)
  - ✅ Active (Active contacts)
  - ✅ Interested (Interested in products)
  - ✅ Negotiating (In negotiation)
  - ✅ Customer (Existing customers)
- **Type**: Multi-select dropdown
- **Count Display**: "Showing X of Y"

#### **Sort Dropdown**
- **Label**: "Sort by Name"
- **Options Available**:
  - ✅ Name (A-Z)
  - ✅ Score (High to Low)
  - ✅ Company (A-Z)
  - ✅ Recent (Newest first)
  - ✅ Oldest first
- **Default**: Sort by Name
- **Direction**: Ascending/Descending toggle

#### **Add Contact Button**
- **Label**: "+ Add Contact"
- **Style**: Blue button (#667eea)
- **Action**: Opens "Create New Contact" modal
- **Keyboard Shortcut**: None (click only)

### **C) Contact Grid/List**

**Grid Layout**: Card-based, responsive grid (320px min-width per card)

#### **Contact Card Structure**

Each card displays:

**Card Header**:
- Contact name (bold, 16px)
- Company name (gray, 14px)

**Card Body**:
- **Email**: Email address (clickable)
- **Phone**: Phone number (clickable - dial)
- **Status**: Badge (color-coded)
- **Tier**: HOT/WARM/COOL/COLD (if assigned)
- **Score**: 0-100 (if assigned)

**Card Footer**:
- **Hover Buttons**:
  - 📧 Email (opens email client)
  - 📞 Call (opens dialer)
  - ✏️ Edit (opens edit modal)
  - 🗑️ Delete (with confirmation)
  - 👁️ View (shows full details)

**Card Styling**:
- **Width**: 320px (responsive)
- **Height**: Auto
- **Background**: White
- **Border**: 0.5px #e0e0e0
- **Shadow**: 0 2px 8px rgba(0,0,0,0.1)
- **Padding**: 16px
- **Hover**: Lift effect (-4px), enhanced shadow

**Grid Properties**:
- **Desktop**: 3-4 columns
- **Tablet**: 2-3 columns
- **Mobile**: 1 column
- **Gap**: 16px between cards

---

### **D) Empty State**
When no contacts exist:
```
┌─────────────────────────────────────┐
│  No contacts found                  │
│  [+ Add your first contact]         │
└─────────────────────────────────────┘
```

---

### **E) Create/Edit Contact Modal**

**Modal Title**: "Add New Contact" or "Edit Contact"

**Form Fields** (16 fields):

1. **Full Name** (Required)
   - Type: Text input
   - Placeholder: "Enter full name"
   - Validation: Required field

2. **Email** (Required)
   - Type: Email input
   - Placeholder: "Enter email address"
   - Validation: Valid email format

3. **Phone** (Required)
   - Type: Phone input
   - Placeholder: "Enter phone number"
   - Format: Supports +91 country code

4. **Company** (Optional)
   - Type: Text input
   - Placeholder: "Enter company name"
   - Autocomplete: Yes (from existing companies)

5. **Job Title** (Optional)
   - Type: Text input
   - Placeholder: "e.g., CEO, Sales Manager"

6. **Industry** (Optional)
   - Type: Dropdown
   - Options: Insurance, Finance, Technology, Retail, Manufacturing, etc.

7. **Company Size** (Optional)
   - Type: Dropdown
   - Options: 1-10, 11-50, 51-200, 201-1000, 1000+

8. **Annual Revenue** (Optional)
   - Type: Text input
   - Format: Currency (₹)

9. **Website** (Optional)
   - Type: URL input
   - Placeholder: "https://company.com"

10. **LinkedIn URL** (Optional)
    - Type: URL input
    - Placeholder: "linkedin.com/in/..."

11. **Source** (Required)
    - Type: Dropdown
    - Options:
      - Website
      - Referral
      - LinkedIn
      - Cold Call
      - Email Campaign
      - Other

12. **Status** (Required)
    - Type: Dropdown
    - Options:
      - New
      - Active
      - Interested
      - Negotiating
      - Customer

13. **Notes** (Optional)
    - Type: Textarea
    - Placeholder: "Add any notes about this contact..."
    - Max length: 500 characters

14. **Tags** (Optional)
    - Type: Multi-select
    - Existing tags: VIP, Hot Lead, Prospect, Partner, etc.
    - Ability to create new tags

15. **Preferred Contact Method** (Optional)
    - Type: Dropdown
    - Options: Email, Phone, WhatsApp, LinkedIn

16. **Best Time to Contact** (Optional)
    - Type: Time range
    - Options: Morning (9-12), Afternoon (12-5), Evening (5-8)

**Form Buttons**:
- **Save** (Blue button) - Saves and closes
- **Cancel** (Gray button) - Closes without saving
- **Delete** (Red button) - Only on edit modal

**Form Styling**:
- **Layout**: 2-column grid
- **Modal Width**: 600px
- **Padding**: 24px
- **Field Spacing**: 16px between fields

---

### **F) CRUD Operations**

✅ **Create**: [+ Add Contact] button → Modal form → Save  
✅ **Read**: Click contact card → View details  
✅ **Update**: Click Edit (pencil icon) → Modal form → Save  
✅ **Delete**: Click Delete (trash icon) → Confirmation → Remove  

---

### **G) Advanced Features**

- ✅ Bulk selection (checkboxes)
- ✅ Bulk actions (delete, export, email)
- ✅ Export to CSV
- ✅ Import from CSV
- ✅ Duplicate contact detection
- ✅ Activity timeline per contact
- ✅ Contact history

---

---

# 3️⃣ **📋 LEADS**

**URL**: `/leads`  
**Status**: ✅ Active  
**Purpose**: Track inbound leads and scoring

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Leads                                       │
│ Track and manage inbound leads              │
└─────────────────────────────────────────────┘
```

### **B) Toolbar Section**

#### **Search Box**
- **Placeholder**: "Search leads..."
- **Scope**: Searches by:
  - Lead name
  - Company
  - Email
  - Phone

#### **Status Filter Dropdown**
- **Label**: "All Status"
- **Options**:
  - ✅ All Status
  - ✅ New
  - ✅ Qualified
  - ✅ Proposal
  - ✅ Negotiation
  - ✅ Closed
- **Multi-select**: Yes

#### **Tier Filter Dropdown**
- **Label**: "All Tiers"
- **Options**:
  - ✅ All Tiers
  - ✅ HOT (Highest priority)
  - ✅ WARM (Medium priority)
  - ✅ COOL (Lower priority)
  - ✅ COLD (Lowest priority)
- **Multi-select**: Yes

#### **Source Filter Dropdown**
- **Label**: "All Sources"
- **Options**: Website, Referral, LinkedIn, Cold Call, Email, Other
- **Multi-select**: Yes

#### **Sort Dropdown**
- **Label**: "Sort by"
- **Options**:
  - ✅ Score (High to Low)
  - ✅ Name (A-Z)
  - ✅ Recent (Newest first)
  - ✅ Engagement (Most active)

#### **Date Range Selector**
- **Label**: "All Time" (default)
- **Options**:
  - Today
  - Last 7 Days
  - Last 30 Days
  - This Month
  - Last Quarter
  - Custom Range (date picker)

#### **Add Lead Button**
- **Label**: "+ New Lead"
- **Action**: Opens "Create Lead" modal

### **C) Leads Table/Grid**

**Layout**: Table format (can toggle to card view)

#### **Columns** (8 columns):

| Column | Content | Sortable | Type |
|--------|---------|----------|------|
| **Name** | Lead name | ✅ Yes | Text (Clickable) |
| **Company** | Company name | ✅ Yes | Text |
| **Email** | Email address | ❌ No | Email (Clickable) |
| **Phone** | Phone number | ❌ No | Phone (Clickable) |
| **Status** | Badge (New/Qual/Prop/Neg/Closed) | ✅ Yes | Status Badge |
| **Tier** | HOT/WARM/COOL/COLD | ✅ Yes | Tier Badge |
| **Score** | 0-100 score | ✅ Yes | Number |
| **Added Date** | When lead was added | ✅ Yes | Date |

**Table Actions** (per row):
- **View** (👁️) - Opens lead detail
- **Edit** (✏️) - Opens edit modal
- **Delete** (🗑️) - Removes with confirmation
- **Convert to Deal** (💼) - Creates associated deal
- **Email** (📧) - Opens email template

**Pagination**:
- **Rows per page**: 10, 25, 50, 100
- **Navigation**: Previous, Next, Go to page
- **Count display**: "Showing X-Y of Z results"

---

### **D) Lead Detail View**

When clicking on a lead name:

**Information Sections**:

1. **Lead Overview**
   - Name (editable)
   - Company (editable)
   - Email (editable, clickable)
   - Phone (editable, clickable)

2. **Lead Scoring Section**
   - Current Score (0-100)
   - Score breakdown:
     - Engagement score
     - Company fit score
     - Urgency score
     - Recency score
   - Tier assignment (HOT/WARM/COOL/COLD)
   - Score history (chart)

3. **Activity Timeline**
   - All interactions logged:
     - Email opens
     - Link clicks
     - Form submissions
     - Phone calls
     - Meetings scheduled
   - Timestamps
   - User who performed action

4. **Associated Deals**
   - List of deals linked to this lead
   - Deal value
   - Deal stage
   - Expected close date

5. **Notes**
   - Internal notes about the lead
   - Add new notes (textarea)
   - Note history with timestamps

6. **Files**
   - Attachments uploaded
   - Document history
   - Upload new files

---

### **E) Create/Edit Lead Modal**

**Form Fields** (12 fields):

1. **Lead Name** (Required)
2. **Email** (Required)
3. **Phone** (Required)
4. **Company** (Optional)
5. **Product Interest** (Optional) - Dropdown
6. **Source** (Required) - Dropdown
7. **Status** (Required) - Dropdown
8. **Budget Range** (Optional) - Dropdown
9. **Decision Timeline** (Optional) - Dropdown
10. **Number of Employees** (Optional) - Number
11. **Industry** (Optional) - Dropdown
12. **Additional Notes** (Optional) - Textarea

**Form Buttons**:
- Save Lead (Blue)
- Cancel (Gray)
- Delete (Red - edit only)

---

### **F) Lead Scoring Algorithm**

**Automated Scoring** (0-100):

- **Engagement Signals** (30 points)
  - Email opens
  - Link clicks
  - Website visits
  - Page time spent

- **Company Fit** (25 points)
  - Industry match
  - Company size fit
  - Revenue fit
  - Location

- **Urgency** (25 points)
  - Budget approved
  - Timeline mentioned
  - Competitor mention
  - "ASAP" language

- **Recency** (20 points)
  - Last activity < 24 hours
  - Recent engagement
  - Active communication

**Tier Assignment**:
- **HOT** (Score 80-100) - Priority
- **WARM** (Score 60-79) - Good prospect
- **COOL** (Score 40-59) - Maybe
- **COLD** (Score <40) - Follow up later

---

---

# 4️⃣ **💼 PIPELINE**

**URL**: `/pipeline`  
**Status**: ✅ Active  
**Purpose**: Kanban board for deal management

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Pipeline                                    │
│ Manage your deals across stages             │
└─────────────────────────────────────────────┘
```

### **B) Toolbar**

#### **New Deal Button**
- **Label**: "+ New Deal"
- **Action**: Opens deal creation modal

#### **View Toggle**
- **Options**: 
  - Kanban View (default - cards)
  - List View (table format)
  - Chart View (pipeline value chart)

#### **Filter Options**
- **Owner Filter**: Show deals by team member
- **Stage Filter**: Show specific stages
- **Value Range**: Filter by deal value

#### **Sort Options**
- By Value (High to Low)
- By Probability (High to Low)
- By Close Date (Soonest first)
- By Created Date (Newest first)

---

### **C) Kanban Board Layout**

**5-Column Layout** (Drag-and-drop enabled):

#### **Column 1: NEW**
- **Header**: "New [0]" (count in brackets)
- **Color**: Blue accent
- **Meaning**: New opportunities not yet qualified
- **Auto-actions**: None

#### **Column 2: QUALIFIED**
- **Header**: "Qualified [0]"
- **Color**: Green accent
- **Meaning**: Qualified leads with identified needs
- **Auto-actions**: None

#### **Column 3: PROPOSAL**
- **Header**: "Proposal [0]"
- **Color**: Orange accent
- **Meaning**: Proposal sent, awaiting response
- **Auto-actions**: Auto-reminder after 5 days

#### **Column 4: NEGOTIATION**
- **Header**: "Negotiation [0]"
- **Color**: Red accent
- **Meaning**: Actively negotiating terms
- **Auto-actions**: Auto-reminder every 3 days

#### **Column 5: CLOSED**
- **Header**: "Closed [0]"
- **Color**: Purple accent
- **Meaning**: Completed deals (won)
- **Auto-actions**: Archive old deals

---

### **D) Deal Card Structure**

**Information Displayed on Card**:

```
┌─────────────────────────┐
│ Lead Name               │
│ Company Name            │
├─────────────────────────┤
│ ₹Deal Value             │
│ Probability: X%         │
├─────────────────────────┤
│ Tier: HOT/WARM/COOL... │
│ Expected Close: MM/DD   │
├─────────────────────────┤
│ [Edit] [Delete] [View]  │
└─────────────────────────┘
```

**Card Details**:

1. **Deal ID/Name**
   - Display: "Deal with [Company]"
   - Format: Bold, 14px

2. **Company Name**
   - Display: Associated company
   - Format: Gray, 12px

3. **Deal Value**
   - Display: ₹ Amount
   - Format: Currency (Indian Rupees)
   - Example: ₹50,000

4. **Probability**
   - Display: 0-100%
   - Calculation: Automatic based on stage
   - Visual: Progress bar

5. **Tier**
   - Display: HOT/WARM/COOL/COLD
   - Color: Matching badge color
   - Source: AI-assigned

6. **Expected Close Date**
   - Display: MM/DD/YY format
   - Overdue indicator: Red if past date
   - Days remaining: Shows countdown

7. **Owner/Assigned To**
   - Display: Team member name
   - Avatar: Small profile pic
   - Clickable: Filter by owner

**Card Actions** (on click):
- **View**: Opens deal detail page
- **Edit**: Opens edit modal
- **Delete**: Removes with confirmation

**Card Hover Effects**:
- Shadow lift
- Color enhancement
- Show full action buttons

---

### **E) Drag-and-Drop Functionality**

**Enabled**: ✅ Yes

**Actions**:
- **Drag deal card** from one column to another
- **Drop** to change stage
- **Auto-save**: Immediately saves new stage
- **Undo**: Yes (last action)
- **Validation**: Prevents invalid transitions

**Drag Behavior**:
- Card lifts on drag
- Column highlights on hover
- Smooth drop animation
- Toast notification: "Deal moved to [Stage]"

---

### **F) Create Deal Modal**

**Form Fields** (8 fields):

1. **Select Contact/Lead** (Required)
   - Dropdown of existing contacts
   - Can create new contact inline

2. **Deal Value** (Required)
   - Number input
   - Currency: INR (₹)
   - Example: 50000

3. **Initial Stage** (Required)
   - Dropdown: New, Qualified, Proposal, Negotiation, Closed
   - Default: New

4. **Probability** (Optional)
   - Slider: 0-100%
   - Auto-based on stage if empty

5. **Expected Close Date** (Required)
   - Date picker
   - Format: MM/DD/YYYY

6. **Deal Description** (Optional)
   - Textarea
   - Notes about the deal

7. **Owner/Assigned To** (Optional)
   - Dropdown of team members
   - Default: Current user

8. **Associated Files** (Optional)
   - File upload
   - Proposal documents, contracts, etc.

**Buttons**:
- Create Deal (Blue)
- Cancel (Gray)

---

### **G) Deal Detail View**

When clicking "View" on a deal:

**Sections**:

1. **Deal Overview**
   - Deal name/ID
   - Company
   - Value
   - Stage
   - Owner
   - Created date
   - Last updated

2. **Deal Timeline**
   - Stage change history
   - Dates for each transition
   - Who made changes

3. **Activity Log**
   - All interactions
   - Notes added
   - Files attached
   - Tasks completed

4. **Related Contacts**
   - Decision makers involved
   - Contact information
   - Interaction history

5. **Documents**
   - Uploaded files
   - Proposals
   - Contracts
   - Email threads

6. **Probability Breakdown**
   - Stage-based percentage
   - Weighted factors
   - Historical data

---

### **H) Advanced Features**

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

✅ **Deal Health**: Indicators for:
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

# 5️⃣ **☎️ CALLS**

**URL**: `/calls`  
**Status**: ✅ Active  
**Purpose**: Track and log sales calls

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Calls                                       │
│ Track and log your sales calls              │
└─────────────────────────────────────────────┘
```

### **B) Toolbar Section**

#### **Log Call Button**
- **Label**: "+ Log Call"
- **Action**: Opens call logging form

#### **Search Box**
- **Placeholder**: "Search by name or phone..."
- **Scope**: Name, phone number, company

#### **Call Type Filter**
- **Label**: "All Types"
- **Options**:
  - ✅ All Types
  - ✅ Inbound (incoming)
  - ✅ Outbound (made by us)
  - ✅ Conference (multi-party)

#### **Outcome Filter**
- **Label**: "All Outcomes"
- **Options**:
  - ✅ All Outcomes
  - ✅ Positive (Interested)
  - ✅ Neutral (No decision)
  - ✅ Negative (Not interested)
  - ✅ No Answer

#### **Date Range Selector**
- **Label**: "This Month"
- **Options**: Today, This Week, This Month, Last Month, Custom

---

### **C) Statistics Cards (4 Cards)**

#### **Card 1: Total Calls**
- **Label**: "Total Calls"
- **Value**: Count (e.g., 4)
- **Icon**: ☎️
- **Color**: Blue

#### **Card 2: Inbound Calls**
- **Label**: "Inbound"
- **Value**: Count (e.g., 1)
- **Icon**: 📥
- **Color**: Green

#### **Card 3: Outbound Calls**
- **Label**: "Outbound"
- **Value**: Count (e.g., 3)
- **Icon**: 📤
- **Color**: Orange

#### **Card 4: Average Duration**
- **Label**: "Avg Duration"
- **Value**: Time (e.g., 4m 21s)
- **Icon**: ⏱️
- **Color**: Purple

**Card Styling**: Same as dashboard KPI cards

---

### **D) Call Log Table**

**Columns** (8 columns):

| Column | Content | Type |
|--------|---------|------|
| **Contact Name** | Name with icon (📥/📤) | Clickable |
| **Phone** | Phone number | Clickable (dial) |
| **Date** | When call occurred | Date |
| **Duration** | Call length | Time |
| **Type** | Inbound/Outbound | Badge |
| **Outcome** | Positive/Neutral/Negative | Badge |
| **Notes** | Brief description | Text |
| **Actions** | View/Edit/Delete | Buttons |

**Table Features**:
- Sortable columns
- Filterable by type/outcome
- Searchable by name/phone
- Pagination (10 per page)
- Responsive design

---

### **E) Call Record Details**

Each call log entry shows:

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

**Information**:

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

### **F) Log Call Modal**

**Form Fields** (10 fields):

1. **Select Contact** (Required)
   - Dropdown of contacts
   - Searchable

2. **Phone Number** (Required)
   - Auto-populated from contact
   - Can override
   - Format: +91-XXXXXXXXXX

3. **Call Type** (Required)
   - Dropdown: Inbound, Outbound, Conference
   - Radio buttons

4. **Start Time** (Required)
   - Date & time picker
   - Default: Now

5. **End Time** (Required)
   - Date & time picker
   - Auto-calculates duration

6. **Duration** (Auto-calculated)
   - Displays calculated time
   - Format: Xm XXs

7. **Call Outcome** (Required)
   - Dropdown: Positive, Neutral, Negative, No Answer
   - Color indicators

8. **Reason for Call** (Optional)
   - Dropdown:
     - Follow-up
     - Sales pitch
     - Problem resolution
     - Information gathering
     - Objection handling

9. **Call Notes** (Required)
   - Textarea
   - What was discussed
   - Action items
   - Next steps
   - Min 10 characters

10. **Schedule Follow-up** (Optional)
    - Checkbox to enable
    - Follow-up date
    - Follow-up time
    - Task description

**Form Buttons**:
- Log Call (Blue)
- Cancel (Gray)

---

### **G) Call Features**

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
- All calls with same contact listed
- Chronological order
- Clickable to view previous calls

✅ **Call Analytics**
- Total calls by team member
- Average duration by type
- Conversion rate from calls
- Peak call times

---

---

# 6️⃣ **📢 MARKETING**

**URL**: `/marketing`  
**Status**: ✅ Active  
**Purpose**: Campaign management and tracking

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Marketing                                   │
│ Manage campaigns and track performance      │
└─────────────────────────────────────────────┘
```

### **B) Toolbar Section**

#### **New Campaign Button**
- **Label**: "+ New Campaign"
- **Action**: Opens campaign creation form

#### **Status Filter**
- **Label**: "All Status"
- **Options**:
  - ✅ All Status
  - ✅ Draft (Not started)
  - ✅ Active (Running)
  - ✅ Scheduled (Upcoming)
  - ✅ Completed (Finished)
  - ✅ Paused

#### **Channel Filter**
- **Label**: "All Channels"
- **Options**:
  - ✅ Email
  - ✅ SMS
  - ✅ WhatsApp
  - ✅ LinkedIn
  - ✅ Facebook
  - ✅ Instagram
  - ✅ Paid Ads
  - ✅ Landing Page

#### **Sort Options**
- By Engagement (High to Low)
- By Recipients (Most to Least)
- By Date Created (Newest first)
- By Performance (Best to Worst)

---

### **C) Statistics Cards (4 Cards)**

#### **Card 1: Total Campaigns**
- **Label**: "Total Campaigns"
- **Value**: 3 (count)
- **Icon**: 📊
- **Color**: Blue

#### **Card 2: Active Campaigns**
- **Label**: "Active"
- **Value**: 1 (count)
- **Icon**: ▶️
- **Color**: Green

#### **Card 3: Total Recipients**
- **Label**: "Total Recipients"
- **Value**: 6,700 (count)
- **Icon**: 👥
- **Color**: Orange

#### **Card 4: Avg Engagement**
- **Label**: "Avg Engagement"
- **Value**: 38% (percentage)
- **Icon**: 📈
- **Color**: Purple

---

### **D) Campaign Cards Grid**

**Layout**: Card-based grid (responsive)

#### **Campaign Card Structure**:

```
┌────────────────────────────────────┐
│ 📧 Campaign Name                   │
│ Campaign Type (Insurance Awareness) │
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

**Card Information**:

1. **Campaign Name**
   - Display: Bold, 16px
   - Icon matching channel (📧📱💬🔗)

2. **Campaign Type**
   - Display: Description (Insurance Awareness)
   - Gray text

3. **Status Badge**
   - Active (Green)
   - Draft (Blue)
   - Scheduled (Yellow)
   - Completed (Gray)
   - Paused (Orange)

4. **Channel**
   - Email, SMS, WhatsApp, LinkedIn, etc.
   - Icon + text

5. **Recipient Count**
   - Total people reached
   - Format: 2,500 (showing thousands)

6. **Engagement Metrics**
   - **Opens**: Number and percentage
   - **Clicks**: Number and click-through rate (CTR)
   - **Conversions**: Lead count
   - **ROI**: Return on investment %

7. **Progress Bar**
   - Visual bar showing completion %
   - Colored based on campaign status
   - Shows: X% Complete

8. **Duration**
   - Start date
   - End date
   - Days remaining (if active)

9. **Card Actions**
   - View Campaign (eye icon)
   - Edit Campaign (pencil icon)
   - Pause/Resume (pause/play icon)
   - Delete Campaign (trash icon)

---

### **E) Campaign Detail View**

When clicking "View" on a campaign:

**Sections**:

1. **Campaign Overview**
   - Name, type, channel
   - Status, owner
   - Start/end dates
   - Description

2. **Campaign Stats**
   - Recipients sent
   - Open rate (%)
   - Click rate (%)
   - Conversion rate (%)
   - Revenue generated
   - ROI (%)

3. **Performance Charts**
   - Opens over time (line chart)
   - Clicks over time
   - Conversion funnel
   - Revenue by day

4. **Recipient Segments**
   - List of target segments
   - Segment criteria
   - Recipient count per segment
   - Performance per segment

5. **Email Content** (if email campaign)
   - Subject line
   - Preview text
   - Full email body (rendered)
   - Send time

6. **Performance by Link**
   - Links in campaign
   - Click count per link
   - Click-through rate
   - Conversion rate

7. **Subscriber Actions**
   - List of who opened
   - List of who clicked
   - List of converters
   - Export lists

8. **Campaign History**
   - Created date/by
   - Last edited
   - Modifications made
   - Performance timeline

---

### **F) Create Campaign Modal**

**Form Fields** (15 fields):

1. **Campaign Name** (Required)
   - Text input
   - Example: "Insurance Awareness Q3"

2. **Campaign Type** (Required)
   - Dropdown:
     - Awareness
     - Lead Generation
     - Nurture
     - Re-engagement
     - Promotion
     - Educational

3. **Select Channel** (Required)
   - Dropdown: Email, SMS, WhatsApp, LinkedIn, Facebook, Instagram, Paid Ads

4. **Target Audience** (Required)
   - Select from saved segments
   - Build new segment:
     - Filter by industry
     - Filter by company size
     - Filter by location
     - Filter by product interest
     - Filter by past engagement

5. **Budget** (Optional)
   - Number input
   - Currency: INR (₹)

6. **Campaign Duration** (Required)
   - Start date (date picker)
   - End date (date picker)

7. **Frequency** (Optional)
   - One-time
   - Daily
   - Weekly
   - Monthly

8. **Campaign Subject** (Optional)
   - For email: Email subject line
   - For SMS: Message preview
   - Character limit display

9. **Campaign Content** (Optional)
   - Textarea for message
   - Rich text editor
   - Template selector
   - Preview option

10. **Call-to-Action** (Optional)
    - Text for CTA button
    - Link/destination
    - Button color

11. **Tracking Options** (Optional)
    - Enable link tracking (checkboxes)
    - UTM parameters
    - Conversion tracking

12. **Sender Info** (Required for email)
    - From name
    - From email address
    - Reply-to email

13. **Schedule Send** (Optional)
    - Date to send
    - Time to send
    - Or: Send immediately

14. **Automation** (Optional)
    - Auto-follow-up (checkbox)
    - Resend to unopened (checkbox)
    - Days to wait for resend

15. **Tags** (Optional)
    - Add campaign tags
    - For organization/filtering

**Form Buttons**:
- Create Campaign (Blue)
- Save as Draft (Gray)
- Cancel (Gray)

---

### **G) Campaign Features**

✅ **Email Templates**
- Pre-built templates
- Drag-and-drop builder
- Custom branding

✅ **A/B Testing**
- Test different subject lines
- Test different content
- Test different send times
- Automatically pick winner

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

# 7️⃣ **📈 REPORTS**

**URL**: `/reports`  
**Status**: ✅ Active  
**Purpose**: Multi-dimensional business analytics

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Reports                                     │
│ Analyze your business metrics               │
└─────────────────────────────────────────────┘
```

### **B) Tab Navigation (3 Tabs)**

#### **Tab 1: Sales Reports**
- Click to view sales analytics
- Default active tab

#### **Tab 2: Contacts Reports**
- Click to view contact analytics
- Shows contact health metrics

#### **Tab 3: Calls Reports**
- Click to view call analytics
- Shows call performance data

---

### **C) Toolbar (Common to all tabs)**

#### **Date Range Selector**
- **Label**: "This Month"
- **Options**:
  - This Month (default)
  - Last Month
  - Last Quarter
  - This Year
  - Last Year
  - Custom Range (date picker)

#### **Export Button**
- **Label**: "📥 Export"
- **Formats**:
  - PDF report
  - Excel spreadsheet
  - CSV file
  - Email report

---

### **D) Sales Reports Tab**

#### **Statistics Cards (4 Cards)**

1. **Total Revenue**
   - Value: ₹5,25,000
   - Trend: +12%
   - Icon: 💰
   - Color: Green

2. **Deals Closed**
   - Value: 8
   - Trend: +2
   - Icon: ✓
   - Color: Blue

3. **Win Rate**
   - Value: 68%
   - Trend: +5%
   - Icon: 🎯
   - Color: Orange

4. **Avg Deal Size**
   - Value: ₹65,625
   - Trend: -3%
   - Icon: 📊
   - Color: Purple

---

#### **Charts and Graphs**

1. **Revenue Trend Chart**
   - **Type**: Line chart
   - **X-axis**: Months (Jan-Dec)
   - **Y-axis**: Revenue amount
   - **Display**: Blue line showing revenue progression
   - **Hover**: Shows exact amount

2. **Sales by Stage**
   - **Type**: Horizontal bar chart
   - **Stages**: New, Qualified, Proposal, Negotiation, Closed
   - **Display**: Deal count or value per stage
   - **Color**: Each stage different color

3. **Top Deals**
   - **Type**: Table/cards
   - **Columns**: Deal name, Value, Stage, Expected close
   - **Sort**: By value (highest first)
   - **Count**: Top 10 deals

---

#### **Data Table: Sales Performance**

**Columns** (7 columns):

| Column | Content | Type |
|--------|---------|------|
| **Deal Name** | Deal identifier | Text |
| **Company** | Company name | Text |
| **Value** | ₹ Amount | Currency |
| **Stage** | Current stage | Badge |
| **Probability** | 0-100% | Number |
| **Expected Close** | MM/DD/YYYY | Date |
| **Owner** | Sales person | Text |

**Features**:
- Sortable columns
- Filterable by stage
- Searchable
- Pagination (10 per page)
- Export to Excel

---

### **E) Contacts Reports Tab**

#### **Statistics Cards (4 Cards)**

1. **Total Contacts**
   - Value: 150
   - Trend: +8
   - Icon: 👥
   - Color: Blue

2. **Active Contacts**
   - Value: 95
   - Trend: +5
   - Icon: ✓
   - Color: Green

3. **Conversion Rate**
   - Value: 42%
   - Trend: +3%
   - Icon: 📈
   - Color: Orange

4. **Avg Contact Score**
   - Value: 65
   - Trend: +8
   - Icon: ⭐
   - Color: Purple

---

#### **Charts**

1. **Contact Status Distribution**
   - **Type**: Pie chart
   - **Segments**: New, Active, Interested, Customer
   - **Display**: Percentage and count
   - **Color**: Each status different color

2. **Contacts by Industry**
   - **Type**: Horizontal bar chart
   - **Display**: Top 10 industries
   - **Count**: Number of contacts per industry

3. **Contact Engagement Timeline**
   - **Type**: Area chart
   - **X-axis**: Days/Weeks/Months
   - **Y-axis**: Engagement level
   - **Display**: Trends over time

---

#### **Data Table: Contact Details**

**Columns** (6 columns):

| Column | Content | Type |
|--------|---------|------|
| **Name** | Contact name | Clickable |
| **Company** | Company name | Text |
| **Status** | Contact status | Badge |
| **Last Contact** | Date | Date |
| **Engagement** | Score | Number |
| **Owner** | Assigned to | Text |

---

### **F) Calls Reports Tab**

#### **Statistics Cards (4 Cards)**

1. **Total Calls**
   - Value: 250
   - Trend: +45
   - Icon: ☎️
   - Color: Blue

2. **Avg Call Duration**
   - Value: 4m 30s
   - Trend: +30s
   - Icon: ⏱️
   - Color: Green

3. **Conversion from Calls**
   - Value: 38%
   - Trend: +5%
   - Icon: 🎯
   - Color: Orange

4. **Calls by Team**
   - Value: 8 (avg per person)
   - Trend: +2
   - Icon: 👥
   - Color: Purple

---

#### **Charts**

1. **Call Volume Trend**
   - **Type**: Column chart
   - **X-axis**: Weeks/Months
   - **Y-axis**: Call count
   - **Display**: Inbound vs Outbound (stacked)

2. **Call Outcomes**
   - **Type**: Pie chart
   - **Segments**: Positive, Neutral, Negative, No Answer
   - **Display**: Percentage and count

3. **Call Duration by Type**
   - **Type**: Bar chart
   - **Categories**: Inbound, Outbound, Conference
   - **Display**: Average duration

---

#### **Data Table: Call Summary**

**Columns** (6 columns):

| Column | Content | Type |
|--------|---------|------|
| **Date** | Date & time | Date |
| **Contact** | Contact name | Text |
| **Type** | Inbound/Outbound | Badge |
| **Duration** | Time | Time |
| **Outcome** | Result | Badge |
| **Owner** | Who made call | Text |

---

### **G) Report Features**

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

# 8️⃣ **⚙️ INTEGRATIONS**

**URL**: `/integrations`  
**Status**: ✅ Active  
**Purpose**: Connect third-party apps and services

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Integrations                                │
│ Connect and manage third-party services     │
└─────────────────────────────────────────────┘
```

### **B) Connected Integrations (5 Active)**

#### **Integration 1: Gmail**
```
┌────────────────────────────────┐
│ 📧 Gmail                       │
├────────────────────────────────┤
│ Status: ✓ Connected (Green)    │
│ Connected: 2 hours ago         │
│ Account: user@gmail.com        │
│                                │
│ Features:                      │
│ ✓ Email sync                   │
│ ✓ Contact sync                 │
│ ✓ Email tracking               │
│                                │
│ Last synced: Now               │
│                                │
│ [Settings] [Disconnect]        │
└────────────────────────────────┘
```

**Details**:
- Connected email account
- Sync frequency: Real-time
- Features: Read, compose, track emails
- Data synced: Emails, attachments, contacts

#### **Integration 2: Google Calendar**
```
┌────────────────────────────────┐
│ 📅 Google Calendar             │
├────────────────────────────────┤
│ Status: ✓ Connected (Green)    │
│ Connected: 1 hour ago          │
│                                │
│ Features:                      │
│ ✓ Meeting scheduling           │
│ ✓ Event sync                   │
│ ✓ Conflict detection           │
│                                │
│ Calendars synced: 2            │
│                                │
│ [Settings] [Disconnect]        │
└────────────────────────────────┘
```

**Details**:
- Sync calendars (primary + work)
- Auto-create events from deals
- Send meeting invites
- Block time for calls

#### **Integration 3: Zapier**
```
┌────────────────────────────────┐
│ ⚡ Zapier                      │
├────────────────────────────────┤
│ Status: ✓ Connected (Green)    │
│ Connected: 30 minutes ago      │
│                                │
│ Active Zaps: 8                 │
│                                │
│ Sample Zaps:                   │
│ • New contact → Slack          │
│ • New deal → Gmail reminder    │
│ • Call logged → Task creation  │
│ • Email opened → DB update     │
│                                │
│ [Manage Zaps] [Disconnect]     │
└────────────────────────────────┘
```

**Details**:
- 8 active automation workflows
- Connects to 50+ apps
- Real-time triggers
- Conditional actions

#### **Integration 4: Slack**
```
┌────────────────────────────────┐
│ 💬 Slack                       │
├────────────────────────────────┤
│ Status: ○ Disconnected (Gray)  │
│ Last connected: Never          │
│                                │
│ Features Available:            │
│ • Deal notifications           │
│ • Lead alerts                  │
│ • Team collaboration           │
│ • Daily reports                │
│                                │
│ [Connect Now]                  │
└────────────────────────────────┘
```

**Details**:
- Not yet connected
- Click to authorize
- Select channel for notifications
- Configure alert types

#### **Integration 5: HubSpot**
```
┌────────────────────────────────┐
│ 🎯 HubSpot                     │
├────────────────────────────────┤
│ Status: ✓ Connected (Green)    │
│ Connected: 5 minutes ago       │
│ Account: company@domain.com    │
│                                │
│ Features:                      │
│ ✓ Contact sync                 │
│ ✓ Deal sync                    │
│ ✓ Email tracking               │
│ ✓ Pipeline management          │
│                                │
│ [Settings] [Disconnect]        │
└────────────────────────────────┘
```

**Details**:
- Bidirectional sync
- Auto-update contacts/deals
- Email tracking enabled
- Pipeline sync every 15 min

---

### **C) Available Integrations (Not Yet Connected)**

#### **Coming Soon**
```
┌────────────────────────────────┐
│ 👥 Microsoft Teams             │
│ Status: Coming Soon            │
│ [Notify Me]                    │
└────────────────────────────────┘

┌────────────────────────────────┐
│ 💬 WhatsApp Business           │
│ Status: Coming Soon            │
│ [Notify Me]                    │
└────────────────────────────────┘

┌────────────────────────────────┐
│ 📱 Twilio (SMS)                │
│ Status: Coming Soon            │
│ [Notify Me]                    │
└────────────────────────────────┘
```

---

### **D) Integration Connection Modal**

When clicking "Connect" on an available integration:

**Modal Structure**:

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

### **E) Integration Settings**

When clicking "Settings" on a connected integration:

**Options**:

1. **Sync Frequency**
   - Real-time (default)
   - Every 15 minutes
   - Every hour
   - Every day
   - Manual only

2. **Data to Sync**
   - Checkboxes for:
     - Contacts
     - Deals
     - Emails
     - Calendar events
     - Tasks
     - Files
     - Custom fields

3. **Notification Settings**
   - Alert on new contact
   - Alert on new deal
   - Alert on missed email
   - Alert on integration error

4. **Auto-Actions**
   - Create task on deal stage change
   - Add note on email open
   - Update contact on interaction
   - Sync custom fields

5. **Data Mapping** (advanced)
   - Map CRM fields to service fields
   - Custom field mapping
   - Transformation rules

6. **Test Connection**
   - Button to verify integration
   - Test data sync
   - Show last sync timestamp
   - Show error logs

---

### **F) Integration Status & Monitoring**

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

### **G) Integration Features**

✅ **Bidirectional Sync**
- Changes in CRM update service
- Changes in service update CRM
- Conflict resolution (last update wins)

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

# 9️⃣ **⚡ SETTINGS**

**URL**: `/settings`  
**Status**: ✅ Active  
**Purpose**: User preferences and account management

## **SECTIONS AVAILABLE**

### **A) Header Area**
```
┌─────────────────────────────────────────────┐
│ Settings                                    │
│ Manage your account and preferences         │
└─────────────────────────────────────────────┘
```

### **B) Settings Tabs (4 Tabs)**

#### **Tab 1: Profile**
- Personal information
- Default: Active

#### **Tab 2: Preferences**
- App behavior & defaults
- Click to switch

#### **Tab 3: Security**
- Password & authentication
- Click to switch

#### **Tab 4: Integrations**
- Connected apps
- Click to switch

---

### **C) Profile Settings Tab**

**Section 1: Personal Information**

**Form Fields**:

1. **Full Name**
   - Input: Text
   - Current: Your name
   - Editable: ✅ Yes
   - Required: Yes

2. **Email Address**
   - Input: Email
   - Current: user@example.com
   - Editable: ✅ Yes
   - Verified: ✅ Yes (blue checkmark)

3. **Phone Number**
   - Input: Phone
   - Current: +91-XXXXXXXXXX
   - Editable: ✅ Yes
   - Format: +91 country code

4. **Job Title**
   - Input: Text
   - Current: Sales Manager
   - Editable: ✅ Yes
   - Examples: CEO, Sales Executive, etc.

5. **Department**
   - Input: Dropdown
   - Options: Sales, Marketing, Management, Support, Other
   - Editable: ✅ Yes

6. **Company Name**
   - Input: Text
   - Display: Read-only (gray)
   - Current: ArthaInvest

**Section 2: Profile Picture**

- **Upload Area**: Drag-and-drop or click to upload
- **Current**: Avatar/profile pic
- **Accepted Formats**: JPG, PNG, GIF
- **Max Size**: 5MB
- **Dimensions**: 200x200px
- **Actions**: [Change] [Remove]

**Save Button**:
- **Label**: "Save Changes"
- **Color**: Blue
- **Confirmation**: "Changes saved successfully"

---

### **D) Preferences Settings Tab**

**Section 1: Notification Settings**

**Email Notifications** (Toggle switches):

1. **New Lead Notification**
   - Toggle: ✅ On/Off
   - Frequency: Real-time / Daily digest / Weekly digest
   - Description: "Notify when new lead added"

2. **Deal Movement Alert**
   - Toggle: ✅ On/Off
   - Frequency: Real-time / Daily / Off
   - Description: "Notify when deal changes stage"

3. **Upcoming Meeting Reminder**
   - Toggle: ✅ On/Off
   - Frequency: 1 hour before / 30 min before / 15 min before
   - Description: "Remind about scheduled meetings"

4. **Daily Sales Summary**
   - Toggle: ✅ On/Off
   - Time: Dropdown (9 AM, 5 PM, etc.)
   - Description: "Daily KPI summary email"

5. **Weekly Performance Report**
   - Toggle: ✅ On/Off
   - Day: Dropdown (Friday, Monday, etc.)
   - Time: Dropdown
   - Description: "Weekly analytics report"

6. **Team Updates**
   - Toggle: ✅ On/Off
   - Frequency: Daily / Weekly
   - Description: "Activity from team members"

7. **System Notifications**
   - Toggle: ✅ On/Off
   - Description: "Important system updates"

---

**Section 2: App Preferences**

**Display Settings**:

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

**Section 3: Behavior Settings**

1. **Auto-Save**
   - Toggle: ✅ On/Off
   - Description: "Auto-save form changes"

2. **Keyboard Shortcuts**
   - Toggle: ✅ On/Off
   - Link: "View all shortcuts"
   - Description: "Enable keyboard shortcuts"

3. **Compact View**
   - Toggle: ✅ On/Off
   - Description: "Reduce spacing in lists"

4. **Default Page on Login**
   - Dropdown: Dashboard / Pipeline / Reports / etc.
   - Current: Dashboard

5. **Page Load Animation**
   - Toggle: ✅ On/Off
   - Description: "Show transitions between pages"

6. **Pagination Size**
   - Dropdown: 10 / 25 / 50 / 100 records per page
   - Current: 10

---

### **E) Security Settings Tab**

**Section 1: Password & Authentication**

**Change Password**:

1. **Current Password**
   - Input: Password (masked)
   - Placeholder: "Enter current password"
   - Required: Yes

2. **New Password**
   - Input: Password (masked)
   - Placeholder: "Enter new password"
   - Requirements:
     - Minimum 8 characters
     - At least 1 uppercase letter
     - At least 1 number
     - At least 1 special character
   - Strength indicator: Weak/Medium/Strong

3. **Confirm Password**
   - Input: Password (masked)
   - Placeholder: "Re-enter new password"
   - Validation: Must match

4. **[Change Password] Button**
   - Color: Blue
   - Confirmation: "Password changed successfully"

---

**Section 2: Two-Factor Authentication (2FA)**

1. **Status**
   - Display: "Not enabled" (red)
   - Description: "Add an extra layer of security"

2. **Enable 2FA Button**
   - Label: "Enable Two-Factor Authentication"
   - Color: Blue
   - Opens: Setup modal

3. **2FA Setup Modal**
   - Step 1: Download authenticator app (Google Authenticator, Microsoft Authenticator)
   - Step 2: Scan QR code with app
   - Step 3: Enter 6-digit code from app
   - Backup codes: Display and allow download

**After Enabled**:
- Status shows: "Enabled" (green)
- Options: [Disable] [Download Backup Codes] [Regenerate]

---

**Section 3: Active Sessions**

**Your Active Sessions**:

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

**Section 4: Login History**

**Table Structure**:

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

### **F) Integrations Settings Tab**

**Connected Integrations List**:

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

### **G) Danger Zone Section**

**At bottom of all tabs**:

```
┌────────────────────────────────────┐
│ ⚠️ Danger Zone                     │
├────────────────────────────────────┤
│                                    │
│ Delete Account                     │
│ Permanently delete your account    │
│ and all associated data            │
│ [Delete Account] (Red button)      │
│                                    │
│ Download Data                      │
│ Export all your data as JSON       │
│ [Download] (Gray button)           │
│                                    │
└────────────────────────────────────┘
```

**Delete Account**:
- Requires password confirmation
- Shows warning message
- 30-day recovery period
- [Yes, Delete] confirmation

**Download Data**:
- Exports: Contacts, Leads, Deals, Calls, etc.
- Format: JSON file
- Download starts immediately
- Email copy also sent

---

### **H) Settings Features**

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

# 📊 **COMPLETE FEATURE SUMMARY**

## **Total Features Across All 9 Tabs**:

| Tab | Key Features | Count |
|-----|--------------|-------|
| 📊 Dashboard | KPI cards, Metrics, Recent leads table | 8 |
| 👥 Contacts | Search, Filter, CRUD, Modal form | 16 |
| 📋 Leads | Scoring, Tier assignment, Activity log | 12 |
| 💼 Pipeline | Kanban board, Drag-drop, Deal cards | 18 |
| ☎️ Calls | Call log, Timer, Statistics, Follow-ups | 10 |
| 📢 Marketing | Campaign management, A/B testing, Analytics | 15 |
| 📈 Reports | Multi-tab analytics, Charts, Export | 12 |
| ⚙️ Integrations | 5+ connected apps, Settings, Sync control | 8 |
| ⚡ Settings | Profile, Preferences, Security, 2FA | 18 |

**TOTAL: 117+ Features Implemented**

---

## **Key Dropdowns Available**

| Dropdown | Location | Options |
|----------|----------|---------|
| Status Filter | Contacts, Leads, Reports | 5-6 options |
| Tier Filter | Leads, Dashboard | HOT/WARM/COOL/COLD |
| Channel Filter | Marketing, Integrations | Email/SMS/WhatsApp/LinkedIn/etc |
| Date Range | Reports, Calls, Dashboard | Today/Week/Month/Quarter/Custom |
| Sort Options | Contacts, Leads, Pipeline | Name/Score/Date/Value |
| Theme | Settings | Light/Dark/Auto |
| Notification Frequency | Settings | Real-time/Daily/Weekly/Off |

---

**✅ Complete CRM system with 9 fully functional tabs!**

