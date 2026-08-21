/**
 * ARTHAINVEST CRM - PHASE D: EMAIL SEQUENCES ENGINE
 * Automated drip campaigns for lead nurturing
 *
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Copy-paste this entire code (REPLACE Phase C code)
 * 4. Save and authorize
 * 5. Run "setupEmailSequences()"
 */

// ============================================
// CONFIGURATION
// ============================================

const LEADS_SHEET = "Leads";
const CLIENTS_SHEET = "Clients";
const SEQUENCES_SHEET = "Email Sequences";
const SEQUENCE_LOGS_SHEET = "Sequence Logs";

// Email Sequence Templates
const EMAIL_SEQUENCES = [
  {
    id: "SEQ001",
    name: "Nurture Sequence",
    targetTier: "COLD",
    targetScore: { min: 0, max: 39 },
    emails: [
      { day: 0, subject: "Welcome to ArthaInvest - Let's Get Started", delay: 0 },
      { day: 3, subject: "Why Insurance Matters for Your Business", delay: 3 },
      { day: 7, subject: "Success Story: How We Helped Companies Like Yours", delay: 7 },
      { day: 14, subject: "Special Offer - Limited Time Only", delay: 14 },
      { day: 21, subject: "Your Next Steps to Peace of Mind", delay: 21 },
      { day: 28, subject: "Last Chance - Don't Miss This Opportunity", delay: 28 },
      { day: 35, subject: "Final Reminder - Act Now", delay: 35 }
    ],
    enrolledLeads: 0,
    active: true
  },
  {
    id: "SEQ002",
    name: "Onboarding Sequence",
    targetTier: "CLIENT",
    targetScore: { min: 0, max: 100 },
    emails: [
      { day: 0, subject: "Welcome Aboard! Your Policy is Now Active", delay: 0 },
      { day: 3, subject: "Here's What's Next - Getting Started Guide", delay: 3 },
      { day: 7, subject: "Your Resources & Support Hub", delay: 7 },
      { day: 14, subject: "First Month Success Tips & Best Practices", delay: 14 },
      { day: 21, subject: "How to Maximize Your Coverage Benefits", delay: 21 },
      { day: 28, subject: "Meet Your Dedicated Support Team", delay: 28 },
      { day: 35, subject: "Your 30-Day Check-In - How Are You Doing?", delay: 35 },
      { day: 42, subject: "Exclusive Resources for Our Valued Clients", delay: 42 }
    ],
    enrolledLeads: 0,
    active: true
  },
  {
    id: "SEQ003",
    name: "Re-engagement Sequence",
    targetTier: "DORMANT",
    targetScore: { min: 0, max: 100 },
    emails: [
      { day: 0, subject: "We Miss You! Special Offer Inside", delay: 0 },
      { day: 3, subject: "What's New - Updates You Should Know", delay: 3 },
      { day: 7, subject: "Exclusive Offer for Valued Customers", delay: 7 },
      { day: 14, subject: "How Others Are Maximizing Their Coverage", delay: 14 },
      { day: 21, subject: "Let's Reconnect - Schedule Your Review Today", delay: 21 },
      { day: 28, subject: "Final Invitation - We Value You", delay: 28 }
    ],
    enrolledLeads: 0,
    active: true
  },
  {
    id: "SEQ004",
    name: "Sales Sequence",
    targetTier: "WARM",
    targetScore: { min: 60, max: 79 },
    emails: [
      { day: 0, subject: "Perfect Timing - The Solution You Need", delay: 0 },
      { day: 2, subject: "3 Reasons Why [Product] is Right for You", delay: 2 },
      { day: 5, subject: "Real Client Success: [Company Name] Story", delay: 5 },
      { day: 10, subject: "Special Pricing Available This Week Only", delay: 10 },
      { day: 15, subject: "See How Easy the Setup Process Is", delay: 15 },
      { day: 20, subject: "Your Personalized Proposal is Ready", delay: 20 },
      { day: 25, subject: "Let's Schedule Your Implementation Call", delay: 25 }
    ],
    enrolledLeads: 0,
    active: true
  }
];

// ============================================
// SETUP FUNCTIONS
// ============================================

function setupEmailSequences() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Create Sequence Logs sheet
  if (!ss.getSheetByName(SEQUENCE_LOGS_SHEET)) {
    const logsSheet = ss.insertSheet(SEQUENCE_LOGS_SHEET);

    const headers = ["Log ID", "Lead/Client Name", "Sequence Name", "Email #", "Subject",
                     "Scheduled Date", "Sent Date", "Open Status", "Click Status",
                     "Conversion", "Notes"];
    logsSheet.getRange("A1:K1").setValues([headers]);
    logsSheet.getRange("A1:K1")
      .setFontWeight("bold")
      .setBackground("#A6A6A6")
      .setFontColor("white");

    logsSheet.setColumnWidth(1, 80);
    logsSheet.setColumnWidth(2, 150);
    logsSheet.setColumnWidth(3, 150);
    logsSheet.setColumnWidth(4, 80);
    logsSheet.setColumnWidth(5, 250);
    logsSheet.setColumnWidth(6, 120);
    logsSheet.setColumnWidth(7, 120);
    logsSheet.setColumnWidth(8, 100);
    logsSheet.setColumnWidth(9, 100);
    logsSheet.setColumnWidth(10, 100);
    logsSheet.setColumnWidth(11, 200);
  }

  Logger.log("Email Sequences system setup complete!");
}

// ============================================
// SEQUENCE ENROLLMENT
// ============================================

function enrollLeadsInSequences() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);

  if (!leadsSheet) {
    Logger.log("Error: Leads sheet not found");
    return;
  }

  const lastRow = leadsSheet.getLastRow();
  if (lastRow < 2) {
    Logger.log("No leads to enroll");
    return;
  }

  const leadsData = leadsSheet.getRange(2, 1, lastRow - 1, 20).getValues();
  let enrollmentCount = 0;

  leadsData.forEach((row, index) => {
    const leadName = row[1];
    const score = row[14] || 0; // Lead Score column
    const tier = row[15] || "UNKNOWN"; // Lead Tier column

    // Determine which sequence to enroll in
    let sequenceId = null;

    if (tier === "COLD" || tier === "VERY COLD") {
      sequenceId = "SEQ001"; // Nurture
    } else if (tier === "WARM") {
      sequenceId = "SEQ004"; // Sales
    } else if (tier === "HOT") {
      // Don't auto-enroll HOT leads - they need direct contact
      sequenceId = null;
    }

    if (sequenceId) {
      enrollLeadInSequence(leadName, sequenceId, row);
      enrollmentCount++;
      Logger.log("[ENROLLED] " + leadName + " in " + sequenceId);
    }
  });

  Logger.log(enrollmentCount + " leads enrolled in sequences");
}

function enrollLeadInSequence(leadName, sequenceId, leadData) {
  const sequence = EMAIL_SEQUENCES.find(s => s.id === sequenceId);
  if (!sequence) return;

  // Schedule all emails in the sequence
  sequence.emails.forEach((email, index) => {
    scheduleSequenceEmail(leadName, sequenceId, email, index + 1);
  });

  sequence.enrolledLeads++;
}

function scheduleSequenceEmail(leadName, sequenceId, emailConfig, emailNumber) {
  const sequence = EMAIL_SEQUENCES.find(s => s.id === sequenceId);
  if (!sequence) return;

  const scheduledDate = new Date();
  scheduledDate.setDate(scheduledDate.getDate() + emailConfig.delay);

  // Log the scheduled email
  logScheduledEmail(leadName, sequence.name, emailNumber, emailConfig.subject, scheduledDate);
}

// ============================================
// EMAIL TRACKING
// ============================================

function trackEmailOpens(leadName, sequenceId, emailNumber) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(SEQUENCE_LOGS_SHEET);

  if (!logsSheet) return;

  // Find and update the email log
  const data = logsSheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][1] === leadName && data[i][3] === emailNumber) {
      logsSheet.getRange(i + 1, 8).setValue("Opened"); // Open Status column
      break;
    }
  }
}

function trackEmailClicks(leadName, sequenceId, emailNumber) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(SEQUENCE_LOGS_SHEET);

  if (!logsSheet) return;

  const data = logsSheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][1] === leadName && data[i][3] === emailNumber) {
      logsSheet.getRange(i + 1, 9).setValue("Clicked"); // Click Status column
      break;
    }
  }
}

// ============================================
// LOGGING
// ============================================

function logScheduledEmail(leadName, sequenceName, emailNumber, subject, scheduledDate) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(SEQUENCE_LOGS_SHEET);

  if (!logsSheet) return;

  const logData = [
    "LOG-" + new Date().getTime(),
    leadName,
    sequenceName,
    emailNumber,
    subject,
    scheduledDate,
    "", // Sent Date
    "Scheduled", // Open Status
    "", // Click Status
    "", // Conversion
    "Auto-enrolled from sequence"
  ];

  logsSheet.appendRow(logData);
}

// ============================================
// ANALYTICS
// ============================================

function getSequenceAnalytics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(SEQUENCE_LOGS_SHEET);

  if (!logsSheet) return null;

  const data = logsSheet.getDataRange().getValues();
  const analytics = {
    totalEmailsScheduled: data.length - 1,
    totalOpens: 0,
    totalClicks: 0,
    openRate: 0,
    clickRate: 0,
    sequences: {}
  };

  data.forEach((row, index) => {
    if (index === 0) return; // Skip header

    const sequence = row[2];
    if (!analytics.sequences[sequence]) {
      analytics.sequences[sequence] = { sent: 0, opens: 0, clicks: 0 };
    }

    analytics.sequences[sequence].sent++;
    if (row[7] === "Opened") {
      analytics.totalOpens++;
      analytics.sequences[sequence].opens++;
    }
    if (row[8] === "Clicked") {
      analytics.totalClicks++;
      analytics.sequences[sequence].clicks++;
    }
  });

  if (analytics.totalEmailsScheduled > 0) {
    analytics.openRate = Math.round((analytics.totalOpens / analytics.totalEmailsScheduled) * 100);
    analytics.clickRate = Math.round((analytics.totalClicks / analytics.totalEmailsScheduled) * 100);
  }

  return analytics;
}

function displaySequenceAnalytics() {
  const analytics = getSequenceAnalytics();

  if (!analytics) {
    Logger.log("No sequence data available");
    return;
  }

  Logger.log("\n=== EMAIL SEQUENCE ANALYTICS ===");
  Logger.log("Total Emails Scheduled: " + analytics.totalEmailsScheduled);
  Logger.log("Total Opens: " + analytics.totalOpens + " (" + analytics.openRate + "%)");
  Logger.log("Total Clicks: " + analytics.totalClicks + " (" + analytics.clickRate + "%)");

  Logger.log("\nBy Sequence:");
  for (let seq in analytics.sequences) {
    const s = analytics.sequences[seq];
    const openRate = s.sent > 0 ? Math.round((s.opens / s.sent) * 100) : 0;
    const clickRate = s.sent > 0 ? Math.round((s.clicks / s.sent) * 100) : 0;
    Logger.log("  " + seq + ": " + s.sent + " sent, " + s.opens + " opens (" + openRate + "%), " + s.clicks + " clicks (" + clickRate + "%)");
  }
}

// ============================================
// TEST FUNCTIONS
// ============================================

function testEmailSequences() {
  Logger.log("Testing Email Sequences System...");

  setupEmailSequences();

  // Test enrollment
  Logger.log("\nEnrolling leads in sequences...");
  enrollLeadsInSequences();

  // Display analytics
  displaySequenceAnalytics();

  Logger.log("\nEmail sequences setup complete! Check 'Sequence Logs' sheet for details.");
}

// ============================================
// MENU SETUP
// ============================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu("Email Sequences")
    .addItem("Setup Email Sequences", "setupEmailSequences")
    .addItem("Enroll Leads in Sequences", "enrollLeadsInSequences")
    .addItem("Test Email Sequences", "testEmailSequences")
    .addItem("View Sequence Analytics", "displaySequenceAnalytics")
    .addToUi();

  Logger.log("Email Sequences menu ready.");
}
