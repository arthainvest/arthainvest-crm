/**
 * ArthaInvest Complete CRM - Auto Builder Script
 * Run this once to create your entire production-ready CRM
 *
 * INSTRUCTIONS:
 * 1. Create a new Google Sheet at sheets.google.com
 * 2. Go to Tools → Script Editor
 * 3. Copy-paste this entire script
 * 4. Click Run → Authorize → Select your account
 * 5. Done! Your CRM will be created automatically
 */

function createCompleteCRM() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  ss.setName("ArthaInvest CRM - Complete");

  // Remove default Sheet
  try {
    ss.deleteSheet(ss.getSheetByName("Sheet1"));
  } catch(e) {}

  // CREATE ALL SHEETS
  createDashboard(ss);
  createLeads(ss);
  createContacts(ss);
  createClients(ss);
  createDeals(ss);
  createProducts(ss);
  createTasks(ss);
  createCommunications(ss);
  createDocuments(ss);
  createCommissions(ss);
  createReports(ss);
  createSettings(ss);

  SpreadsheetApp.flush();
  Logger.log("✅ Complete CRM Created Successfully!");
  Logger.log("📊 All 12 modules are ready to use");
}

// ============================================
// SHEET 1: DASHBOARD
// ============================================
function createDashboard(ss) {
  const sheet = ss.insertSheet("Dashboard", 0);

  // Title
  sheet.getRange("A1:E1").merge().setValue("ArthaInvest CRM Dashboard").setFontSize(16).setFontWeight("bold");
  sheet.getRange("A1:E1").setBackground("#1f497d").setFontColor("white");

  // KPIs
  sheet.getRange("A3").setValue("📊 KEY METRICS");
  sheet.getRange("A4").setValue("Total Clients").setFontWeight("bold");
  sheet.getRange("B4").setFormula("=COUNTA(Clients!A2:A)");

  sheet.getRange("A5").setValue("Active Prospects").setFontWeight("bold");
  sheet.getRange("B5").setFormula("=COUNTA(Leads!A2:A)");

  sheet.getRange("A6").setValue("Open Deals").setFontWeight("bold");
  sheet.getRange("B6").setFormula("=COUNTIF(Deals!G2:G,\"Open\")");

  sheet.getRange("A7").setValue("Total Pipeline Value").setFontWeight("bold");
  sheet.getRange("B7").setFormula("=SUM(Deals!H2:H)");
  sheet.getRange("B7").setNumberFormat("₹#,##0");

  sheet.getRange("A8").setValue("Pending Tasks").setFontWeight("bold");
  sheet.getRange("B8").setFormula("=COUNTIF(Tasks!F2:F,\"Pending\")");

  sheet.getRange("A9").setValue("Renewals This Month").setFontWeight("bold");
  sheet.getRange("B9").setFormula("=COUNTIFS(Clients!J2:J,\">=\"&TODAY(),Clients!J2:J,\"<=\"&DATE(YEAR(TODAY()),MONTH(TODAY())+1,0))");

  // Upcoming Tasks
  sheet.getRange("D3").setValue("⏰ UPCOMING TASKS (Next 5 Days)");
  sheet.getRange("D4:F6").setBorder(true, true, true, true, true, true);
  sheet.getRange("D4").setValue("Task").setFontWeight("bold").setBackground("#E8E8E8");
  sheet.getRange("E4").setValue("Lead").setFontWeight("bold").setBackground("#E8E8E8");
  sheet.getRange("F4").setValue("Due Date").setFontWeight("bold").setBackground("#E8E8E8");

  // Set column widths
  sheet.setColumnWidth(1, 150);
  sheet.setColumnWidth(2, 100);
  sheet.setColumnWidth(4, 200);
}

// ============================================
// SHEET 2: LEADS
// ============================================
function createLeads(ss) {
  const sheet = ss.insertSheet("Leads");

  const headers = [
    "Lead ID", "Name", "Phone", "Email", "Company", "Position",
    "Source", "Product Interest", "Qualification Status", "Budget",
    "Timeline", "Created Date", "Last Contact", "Next Follow-up", "Notes"
  ];

  sheet.getRange("A1:O1").setValues([headers]).setFontWeight("bold").setBackground("#4472C4").setFontColor("white");

  // Set column widths
  sheet.setColumnWidths([60, 120, 100, 150, 120, 100, 100, 120, 120, 80, 100, 100, 100, 100, 200]);

  // Add data validation
  const sourceRange = sheet.getRange("G2:G1000");
  const sourceValues = ["Direct", "Referral", "LinkedIn", "WhatsApp", "Email Campaign", "Website", "Other"];
  const sourceValidation = SpreadsheetApp.newDataValidation().requireValueInList(sourceValues).build();
  sourceRange.setDataValidation(sourceValidation);

  const statusRange = sheet.getRange("I2:I1000");
  const statusValues = ["Warm", "Qualified", "Not Qualified", "On Hold"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Format currency column
  sheet.getRange("J2:J1000").setNumberFormat("₹#,##0");

  // Format date columns
  sheet.getRange("L2:N1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 3: CONTACTS
// ============================================
function createContacts(ss) {
  const sheet = ss.insertSheet("Contacts");

  const headers = [
    "Contact ID", "Name", "Phone", "Email", "Company", "Position",
    "Relationship Type", "Related To", "Address", "City", "State",
    "Preferred Contact Method", "Preferred Time", "Birthday", "Last Contact",
    "Created Date", "Notes"
  ];

  sheet.getRange("A1:Q1").setValues([headers]).setFontWeight("bold").setBackground("#70AD47").setFontColor("white");
  sheet.setColumnWidths([60, 120, 100, 150, 120, 100, 120, 120, 150, 100, 80, 120, 100, 100, 100, 100, 200]);

  // Data validation
  const relationshipRange = sheet.getRange("G2:G1000");
  const relationshipValues = ["Client", "Prospect", "Referrer", "Influencer", "Partner"];
  const relationshipValidation = SpreadsheetApp.newDataValidation().requireValueInList(relationshipValues).build();
  relationshipRange.setDataValidation(relationshipValidation);

  const methodRange = sheet.getRange("L2:L1000");
  const methodValues = ["WhatsApp", "Email", "Phone", "SMS", "In-person"];
  const methodValidation = SpreadsheetApp.newDataValidation().requireValueInList(methodValues).build();
  methodRange.setDataValidation(methodValidation);

  // Format dates
  sheet.getRange("O2:P1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 4: CLIENTS
// ============================================
function createClients(ss) {
  const sheet = ss.insertSheet("Clients");

  const headers = [
    "Client ID", "Name", "Phone", "Email", "Product", "Folio/Policy No.",
    "Start Date", "SIP/Premium Amount", "Frequency", "Renewal/Review Date",
    "Commission Trail", "Last Review", "Status", "Annual Value", "Created Date",
    "Client Score", "Notes"
  ];

  sheet.getRange("A1:Q1").setValues([headers]).setFontWeight("bold").setBackground("#FFC000").setFontColor("black");
  sheet.setColumnWidths([60, 120, 100, 150, 100, 120, 100, 120, 100, 120, 100, 100, 100, 100, 100, 100, 200]);

  // Data validation
  const statusRange = sheet.getRange("M2:M1000");
  const statusValues = ["Active", "Inactive", "Dormant", "Churned"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Format currency and dates
  sheet.getRange("H2:H1000").setNumberFormat("₹#,##0");
  sheet.getRange("N2:N1000").setNumberFormat("₹#,##0");
  sheet.getRange("G2:G1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("J2:J1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("L2:L1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("O2:O1000").setNumberFormat("yyyy-mm-dd");

  // Frequency validation
  const frequencyRange = sheet.getRange("I2:I1000");
  const frequencyValues = ["Monthly", "Quarterly", "Half-yearly", "Annual", "One-time"];
  const frequencyValidation = SpreadsheetApp.newDataValidation().requireValueInList(frequencyValues).build();
  frequencyRange.setDataValidation(frequencyValidation);
}

// ============================================
// SHEET 5: DEALS
// ============================================
function createDeals(ss) {
  const sheet = ss.insertSheet("Deals");

  const headers = [
    "Deal ID", "Deal Name", "Client/Lead Name", "Product", "Expected Value",
    "Probability %", "Expected Close Date", "Stage", "Owner", "Created Date",
    "Last Activity", "Key Decision Maker", "Competition", "Notes"
  ];

  sheet.getRange("A1:N1").setValues([headers]).setFontWeight("bold").setBackground("#C5504E").setFontColor("white");
  sheet.setColumnWidths([60, 120, 120, 100, 120, 80, 120, 120, 100, 100, 100, 120, 100, 200]);

  // Stage validation
  const stageRange = sheet.getRange("H2:H1000");
  const stageValues = ["Prospecting", "Qualification", "Needs Analysis", "Proposal", "Negotiation", "Closed Won", "Closed Lost"];
  const stageValidation = SpreadsheetApp.newDataValidation().requireValueInList(stageValues).build();
  stageRange.setDataValidation(stageValidation);

  // Format currency and percentage
  sheet.getRange("E2:E1000").setNumberFormat("₹#,##0");
  sheet.getRange("F2:F1000").setNumberFormat("0\"%\"");
  sheet.getRange("G2:G1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("J2:J1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("K2:K1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 6: PRODUCTS
// ============================================
function createProducts(ss) {
  const sheet = ss.insertSheet("Products");

  const headers = [
    "Product ID", "Product Name", "Category", "Provider", "Commission %",
    "Min Premium", "Max Premium", "Description", "Key Features", "Active", "Created Date"
  ];

  sheet.getRange("A1:K1").setValues([headers]).setFontWeight("bold").setBackground("#5B9BD5").setFontColor("white");
  sheet.setColumnWidths([80, 150, 120, 120, 100, 100, 100, 200, 200, 80, 100]);

  // Sample products
  const products = [
    ["P001", "Tata AIG Term Plan", "Life Insurance", "Tata AIG", "8%", "50000", "10000000", "Term life insurance plan", "High coverage, low premium", "Yes", new Date()],
    ["P002", "Niva Bupa Health Insurance", "Health Insurance", "Niva Bupa", "12%", "10000", "500000", "Comprehensive health coverage", "Cashless treatment, wide network", "Yes", new Date()],
    ["P003", "POSP Pension Plan", "Pension", "Government", "5%", "100000", "5000000", "Pension scheme", "Tax benefits, retirement planning", "Yes", new Date()],
    ["P004", "DSA Investment Plan", "Investment", "Various", "6%", "50000", "2000000", "Direct Selling Agent commission", "Flexible, good returns", "Yes", new Date()],
  ];

  sheet.getRange("A2:K5").setValues(products);
  sheet.getRange("E2:E5").setNumberFormat("0\"%\"");
  sheet.getRange("F2:G5").setNumberFormat("₹#,##0");
  sheet.getRange("K2:K5").setNumberFormat("yyyy-mm-dd");

  // Active validation
  const activeRange = sheet.getRange("J2:J1000");
  const activeValidation = SpreadsheetApp.newDataValidation().requireValueInList(["Yes", "No"]).build();
  activeRange.setDataValidation(activeValidation);
}

// ============================================
// SHEET 7: TASKS
// ============================================
function createTasks(ss) {
  const sheet = ss.insertSheet("Tasks");

  const headers = [
    "Task ID", "Task Description", "Assigned To", "Related To", "Related Type",
    "Status", "Priority", "Due Date", "Created Date", "Completed Date", "Notes"
  ];

  sheet.getRange("A1:K1").setValues([headers]).setFontWeight("bold").setBackground("#92D050").setFontColor("black");
  sheet.setColumnWidths([60, 200, 100, 120, 100, 100, 100, 100, 100, 100, 200]);

  // Status validation
  const statusRange = sheet.getRange("F2:F1000");
  const statusValues = ["Pending", "In Progress", "Completed", "On Hold"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Priority validation
  const priorityRange = sheet.getRange("G2:G1000");
  const priorityValues = ["High", "Medium", "Low"];
  const priorityValidation = SpreadsheetApp.newDataValidation().requireValueInList(priorityValues).build();
  priorityRange.setDataValidation(priorityValidation);

  // Type validation
  const typeRange = sheet.getRange("E2:E1000");
  const typeValues = ["Lead", "Client", "Deal", "Other"];
  const typeValidation = SpreadsheetApp.newDataValidation().requireValueInList(typeValues).build();
  typeRange.setDataValidation(typeValidation);

  // Format dates
  sheet.getRange("H2:J1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 8: COMMUNICATIONS
// ============================================
function createCommunications(ss) {
  const sheet = ss.insertSheet("Communications");

  const headers = [
    "Communication ID", "Date", "Contact Name", "Channel", "Type", "Message Subject",
    "Status", "Outcome", "Next Follow-up", "Duration (min)", "Notes"
  ];

  sheet.getRange("A1:K1").setValues([headers]).setFontWeight("bold").setBackground("#FF6B6B").setFontColor("white");
  sheet.setColumnWidths([80, 100, 120, 100, 100, 200, 100, 150, 100, 100, 200]);

  // Channel validation
  const channelRange = sheet.getRange("D2:D1000");
  const channelValues = ["WhatsApp", "Email", "Phone Call", "In-person Meeting", "Video Call", "SMS"];
  const channelValidation = SpreadsheetApp.newDataValidation().requireValueInList(channelValues).build();
  channelRange.setDataValidation(channelValidation);

  // Type validation
  const typeRange = sheet.getRange("E2:E1000");
  const typeValues = ["Inquiry", "Follow-up", "Proposal", "Negotiation", "Feedback", "Support"];
  const typeValidation = SpreadsheetApp.newDataValidation().requireValueInList(typeValues).build();
  typeRange.setDataValidation(typeValidation);

  // Status validation
  const statusRange = sheet.getRange("G2:G1000");
  const statusValues = ["Sent", "Delivered", "Opened", "Replied", "Scheduled", "Failed"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Format dates
  sheet.getRange("B2:B1000").setNumberFormat("yyyy-mm-dd hh:mm:ss");
  sheet.getRange("I2:I1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 9: DOCUMENTS
// ============================================
function createDocuments(ss) {
  const sheet = ss.insertSheet("Documents");

  const headers = [
    "Document ID", "Document Name", "Type", "Related To", "Client/Lead Name",
    "Upload Date", "Status", "Expiry Date", "File Link", "Notes"
  ];

  sheet.getRange("A1:J1").setValues([headers]).setFontWeight("bold").setBackground("#7030A0").setFontColor("white");
  sheet.setColumnWidths([80, 150, 120, 120, 120, 100, 100, 100, 300, 200]);

  // Type validation
  const typeRange = sheet.getRange("C2:C1000");
  const typeValues = ["Policy Document", "KYC Form", "Quotation", "Proposal", "Invoice", "Agreement", "Medical Report", "Other"];
  const typeValidation = SpreadsheetApp.newDataValidation().requireValueInList(typeValues).build();
  typeRange.setDataValidation(typeValidation);

  // Status validation
  const statusRange = sheet.getRange("G2:G1000");
  const statusValues = ["Uploaded", "Pending", "Expired", "Archived"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Format dates
  sheet.getRange("F2:F1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("H2:H1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 10: COMMISSIONS
// ============================================
function createCommissions(ss) {
  const sheet = ss.insertSheet("Commissions");

  const headers = [
    "Commission ID", "Date", "Agent/DSA", "Policy/Deal No.", "Client Name", "Product",
    "Commission Amount", "Commission %", "Commission Type", "Status", "Payment Date", "Notes"
  ];

  sheet.getRange("A1:L1").setValues([headers]).setFontWeight("bold").setBackground("#1F4E78").setFontColor("white");
  sheet.setColumnWidths([80, 100, 120, 120, 120, 120, 120, 100, 120, 100, 100, 200]);

  // Type validation
  const typeRange = sheet.getRange("I2:I1000");
  const typeValues = ["Initial", "Trail", "Bonus", "Incentive"];
  const typeValidation = SpreadsheetApp.newDataValidation().requireValueInList(typeValues).build();
  typeRange.setDataValidation(typeValidation);

  // Status validation
  const statusRange = sheet.getRange("J2:J1000");
  const statusValues = ["Earned", "Pending", "Paid", "Disputed"];
  const statusValidation = SpreadsheetApp.newDataValidation().requireValueInList(statusValues).build();
  statusRange.setDataValidation(statusValidation);

  // Format currency and dates
  sheet.getRange("G2:G1000").setNumberFormat("₹#,##0.00");
  sheet.getRange("H2:H1000").setNumberFormat("0.00\"%\"");
  sheet.getRange("A2:A1000").setNumberFormat("yyyy-mm-dd");
  sheet.getRange("K2:K1000").setNumberFormat("yyyy-mm-dd");
}

// ============================================
// SHEET 11: REPORTS
// ============================================
function createReports(ss) {
  const sheet = ss.insertSheet("Reports");

  sheet.getRange("A1:D1").merge().setValue("ArthaInvest CRM Reports").setFontSize(14).setFontWeight("bold").setBackground("#44546A").setFontColor("white");

  // Summary Section
  sheet.getRange("A3").setValue("MONTHLY SUMMARY").setFontWeight("bold").setFontSize(12);

  const summaryHeaders = ["Metric", "This Month", "Last Month", "Growth %"];
  sheet.getRange("A4:D4").setValues([summaryHeaders]).setBackground("#E8E8E8").setFontWeight("bold");

  sheet.getRange("A5:D11").setValues([
    ["New Clients", 0, 0, ""],
    ["New Leads", 0, 0, ""],
    ["Deals Closed", 0, 0, ""],
    ["Total Commission", 0, 0, ""],
    ["Tasks Completed", 0, 0, ""],
    ["Follow-ups Made", 0, 0, ""],
    ["Client Retention Rate %", 0, 0, ""]
  ]);

  sheet.setColumnWidths([150, 100, 100, 100]);
}

// ============================================
// SHEET 12: SETTINGS
// ============================================
function createSettings(ss) {
  const sheet = ss.insertSheet("Settings");

  sheet.getRange("A1:B1").merge().setValue("CRM SETTINGS").setFontSize(14).setFontWeight("bold").setBackground("#203864").setFontColor("white");

  // Team Settings
  sheet.getRange("A3").setValue("TEAM MEMBERS").setFontWeight("bold").setFontSize(12);
  sheet.getRange("A4:D4").setValues([["Name", "Role", "Email", "Phone"]]).setBackground("#E8E8E8").setFontWeight("bold");

  // Add sample team member
  sheet.getRange("A5:D5").setValues([["You", "Owner/Agent", "neemailbox555@gmail.com", ""]]);

  // Products Setup
  sheet.getRange("A8").setValue("COMMISSION RATES (%)").setFontWeight("bold").setFontSize(12);
  sheet.getRange("A9:B14").setValues([
    ["Tata AIG Term", "8%"],
    ["Niva Bupa Health", "12%"],
    ["POSP Pension", "5%"],
    ["DSA Investment", "6%"],
    ["Other Products", "5%"],
    ["Referral Bonus", "3%"]
  ]);

  sheet.setColumnWidths([150, 150, 150, 150]);
}

// Run function
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("CRM")
    .addItem("Create Complete CRM", "createCompleteCRM")
    .addSeparator()
    .addItem("Setup Instructions", "showInstructions")
    .addToUi();
}

function showInstructions() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    "ArthaInvest CRM Setup\n\n" +
    "1. Click 'CRM' → 'Create Complete CRM'\n" +
    "2. Authorize the script\n" +
    "3. Wait for it to complete (1-2 minutes)\n" +
    "4. Refresh the page\n" +
    "5. Your complete CRM is ready!\n\n" +
    "All 12 modules will be created:\n" +
    "✓ Dashboard\n✓ Leads\n✓ Contacts\n✓ Clients\n" +
    "✓ Deals\n✓ Products\n✓ Tasks\n✓ Communications\n" +
    "✓ Documents\n✓ Commissions\n✓ Reports\n✓ Settings"
  );
}
