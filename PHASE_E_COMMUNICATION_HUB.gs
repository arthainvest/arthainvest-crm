/**
 * ARTHAINVEST CRM - PHASE E: COMMUNICATION HUB
 * Unified tracking of all customer communications
 *
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Copy-paste this entire code (REPLACE Phase D code)
 * 4. Save and authorize
 * 5. Run "setupCommunicationHub()"
 */

// ============================================
// CONFIGURATION
// ============================================

const LEADS_SHEET = "Leads";
const CLIENTS_SHEET = "Clients";
const CONTACTS_SHEET = "Contacts";
const COMMUNICATIONS_SHEET = "Communications";
const COMM_HUB_SHEET = "Communication Hub";
const COMM_PREFERENCES_SHEET = "Communication Preferences";
const INTERACTION_HISTORY_SHEET = "Interaction History";

// Communication channels
const CHANNELS = ["WhatsApp", "Email", "Phone Call", "In-person", "Video Call", "SMS", "LinkedIn"];

// Communication types
const COMM_TYPES = ["Inquiry", "Follow-up", "Proposal", "Negotiation", "Feedback", "Support"];

// ============================================
// SETUP FUNCTIONS
// ============================================

function setupCommunicationHub() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Create Communication Hub sheet
  if (!ss.getSheetByName(COMM_HUB_SHEET)) {
    const hubSheet = ss.insertSheet(COMM_HUB_SHEET);

    const headers = ["Lead/Client Name", "Email Opens", "Email Clicks", "WhatsApp Sent",
                     "WhatsApp Delivered", "WhatsApp Read", "Calls Made", "Call Duration (min)",
                     "Meetings Scheduled", "Meetings Completed", "Last Activity",
                     "Last Activity Type", "Next Touchpoint", "Days Since Contact",
                     "Communication Preference", "Status"];
    hubSheet.getRange("A1:P1").setValues([headers]);
    hubSheet.getRange("A1:P1")
      .setFontWeight("bold")
      .setBackground("#203864")
      .setFontColor("white");

    const widths = [150, 100, 100, 100, 150, 100, 80, 120, 150, 150, 150, 150, 150, 130, 150, 100];
    for (let i = 0; i < widths.length; i++) {
      hubSheet.setColumnWidth(i + 1, widths[i]);
    }
  }

  // Create Communication Preferences sheet
  if (!ss.getSheetByName(COMM_PREFERENCES_SHEET)) {
    const prefSheet = ss.insertSheet(COMM_PREFERENCES_SHEET);

    const headers = ["Contact Name", "Preferred Channel", "Preferred Time", "Do Not Disturb",
                     "Opt-in Email", "Opt-in WhatsApp", "Opt-in SMS", "Opted Out",
                     "Reason for Opt-out", "Last Updated"];
    prefSheet.getRange("A1:J1").setValues([headers]);
    prefSheet.getRange("A1:J1")
      .setFontWeight("bold")
      .setBackground("#203864")
      .setFontColor("white");

    const widths = [150, 150, 120, 150, 120, 150, 120, 100, 200, 100];
    for (let i = 0; i < widths.length; i++) {
      prefSheet.setColumnWidth(i + 1, widths[i]);
    }
  }

  // Create Interaction History sheet
  if (!ss.getSheetByName(INTERACTION_HISTORY_SHEET)) {
    const historySheet = ss.insertSheet(INTERACTION_HISTORY_SHEET);

    const headers = ["Interaction ID", "Contact Name", "Date & Time", "Channel", "Type",
                     "Message/Subject", "Duration (min)", "Outcome", "Notes", "Logged By"];
    historySheet.getRange("A1:J1").setValues([headers]);
    historySheet.getRange("A1:J1")
      .setFontWeight("bold")
      .setBackground("#203864")
      .setFontColor("white");

    const widths = [100, 150, 150, 120, 120, 250, 120, 150, 200, 100];
    for (let i = 0; i < widths.length; i++) {
      historySheet.setColumnWidth(i + 1, widths[i]);
    }
  }

  Logger.log("Communication Hub system setup complete!");
}

// ============================================
// COMMUNICATION TRACKING
// ============================================

function logCommunication(contactName, channel, commType, subject, duration, outcome, notes) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const historySheet = ss.getSheetByName(INTERACTION_HISTORY_SHEET);

  if (!historySheet) {
    Logger.log("Error: Interaction History sheet not found");
    return;
  }

  const logData = [
    "INT-" + new Date().getTime(),
    contactName,
    new Date(),
    channel,
    commType,
    subject,
    duration || "",
    outcome || "",
    notes || "",
    "System"
  ];

  historySheet.appendRow(logData);
  updateCommunicationHub(contactName);
}

function recordEmailOpen(contactName) {
  logCommunication(contactName, "Email", "Follow-up", "Email opened", "", "Opened", "");
}

function recordEmailClick(contactName) {
  logCommunication(contactName, "Email", "Follow-up", "Email link clicked", "", "Clicked", "");
}

function recordWhatsAppMessage(contactName, messageText) {
  logCommunication(contactName, "WhatsApp", "Inquiry", messageText, "", "Sent", "");
}

function recordPhoneCall(contactName, duration, notes) {
  logCommunication(contactName, "Phone Call", "Follow-up", "Call", duration, "Completed", notes);
}

function recordMeeting(contactName, meetingTitle, duration) {
  logCommunication(contactName, "In-person", "Negotiation", meetingTitle, duration, "Completed", "");
}

// ============================================
// COMMUNICATION HUB UPDATE
// ============================================

function updateCommunicationHub(contactName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hubSheet = ss.getSheetByName(COMM_HUB_SHEET);
  const historySheet = ss.getSheetByName(INTERACTION_HISTORY_SHEET);

  if (!hubSheet || !historySheet) return;

  // Get interaction history for this contact
  const historyData = historySheet.getDataRange().getValues();
  const contactInteractions = historyData.filter(row => row[1] === contactName);

  if (contactInteractions.length === 0) return;

  // Calculate statistics
  let stats = {
    emailOpens: 0,
    emailClicks: 0,
    whatsappSent: 0,
    whatsappDelivered: 0,
    whatsappRead: 0,
    callsMade: 0,
    totalCallDuration: 0,
    meetingsScheduled: 0,
    meetingsCompleted: 0,
    lastActivity: null,
    lastActivityType: null,
    nextTouchpoint: null
  };

  contactInteractions.forEach(row => {
    const channel = row[3];
    const type = row[4];
    const outcome = row[7];
    const date = new Date(row[2]);

    if (channel === "Email") {
      stats.whatsappSent++;
      if (outcome === "Opened") stats.emailOpens++;
      if (outcome === "Clicked") stats.emailClicks++;
    } else if (channel === "WhatsApp") {
      stats.whatsappSent++;
      if (outcome === "Delivered") stats.whatsappDelivered++;
      if (outcome === "Read") stats.whatsappRead++;
    } else if (channel === "Phone Call") {
      stats.callsMade++;
      stats.totalCallDuration += (row[6] || 0);
    } else if (channel === "In-person") {
      stats.meetingsCompleted++;
    }

    if (!stats.lastActivity || date > stats.lastActivity) {
      stats.lastActivity = date;
      stats.lastActivityType = channel;
    }
  });

  // Calculate days since contact
  const daysSinceContact = stats.lastActivity ?
    Math.floor((new Date() - stats.lastActivity) / (1000 * 60 * 60 * 24)) : 999;

  // Determine next touchpoint (example: 7 days after last contact)
  if (stats.lastActivity) {
    stats.nextTouchpoint = new Date(stats.lastActivity.getTime() + 7 * 24 * 60 * 60 * 1000);
  }

  // Find or create row in hub
  const hubData = hubSheet.getDataRange().getValues();
  let hubRowIndex = -1;
  for (let i = 1; i < hubData.length; i++) {
    if (hubData[i][0] === contactName) {
      hubRowIndex = i + 1;
      break;
    }
  }

  if (hubRowIndex === -1) {
    // Create new row
    hubSheet.appendRow([
      contactName,
      stats.emailOpens,
      stats.emailClicks,
      stats.whatsappSent,
      stats.whatsappDelivered,
      stats.whatsappRead,
      stats.callsMade,
      stats.totalCallDuration,
      stats.meetingsScheduled,
      stats.meetingsCompleted,
      stats.lastActivity || "",
      stats.lastActivityType || "",
      stats.nextTouchpoint || "",
      daysSinceContact,
      "", // Communication preference
      daysSinceContact > 30 ? "Dormant" : "Active"
    ]);
  } else {
    // Update existing row
    hubSheet.getRange(hubRowIndex, 1, 1, 16).setValues([[
      contactName,
      stats.emailOpens,
      stats.emailClicks,
      stats.whatsappSent,
      stats.whatsappDelivered,
      stats.whatsappRead,
      stats.callsMade,
      stats.totalCallDuration,
      stats.meetingsScheduled,
      stats.meetingsCompleted,
      stats.lastActivity || "",
      stats.lastActivityType || "",
      stats.nextTouchpoint || "",
      daysSinceContact,
      "", // Communication preference
      daysSinceContact > 30 ? "Dormant" : "Active"
    ]]);
  }
}

// ============================================
// COMMUNICATION PREFERENCES
// ============================================

function setCommunicationPreference(contactName, preferredChannel, preferredTime, dnd) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const prefSheet = ss.getSheetByName(COMM_PREFERENCES_SHEET);

  if (!prefSheet) return;

  const prefData = [
    contactName,
    preferredChannel,
    preferredTime,
    dnd || "None",
    "Yes",
    "Yes",
    "No",
    "No",
    "",
    new Date()
  ];

  prefSheet.appendRow(prefData);
}

function canSendToContact(contactName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const prefSheet = ss.getSheetByName(COMM_PREFERENCES_SHEET);

  if (!prefSheet) return true;

  const prefData = prefSheet.getDataRange().getValues();
  const contact = prefData.find(row => row[0] === contactName);

  if (!contact) return true;

  return contact[7] !== "Yes"; // Check OptedOut column
}

// ============================================
// INTERACTION TIMELINE
// ============================================

function getInteractionTimeline(contactName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const historySheet = ss.getSheetByName(INTERACTION_HISTORY_SHEET);

  if (!historySheet) return [];

  const historyData = historySheet.getDataRange().getValues();
  const timeline = historyData
    .filter(row => row[1] === contactName && row[0] !== "Interaction ID")
    .sort((a, b) => new Date(b[2]) - new Date(a[2]));

  return timeline;
}

function displayInteractionTimeline(contactName) {
  const timeline = getInteractionTimeline(contactName);

  Logger.log("\n=== INTERACTION TIMELINE: " + contactName + " ===");
  timeline.forEach((row, index) => {
    const date = new Date(row[2]).toLocaleDateString();
    const time = new Date(row[2]).toLocaleTimeString();
    const channel = row[3];
    const type = row[4];
    const subject = row[5];

    Logger.log((index + 1) + ". [" + date + " " + time + "] " + channel + " (" + type + "): " + subject);
  });
}

// ============================================
// COMMUNICATION ANALYTICS
// ============================================

function getCommunicationAnalytics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const historySheet = ss.getSheetByName(INTERACTION_HISTORY_SHEET);

  if (!historySheet) return null;

  const data = historySheet.getDataRange().getValues();
  const analytics = {
    totalInteractions: data.length - 1,
    byChannel: {},
    byType: {},
    averageResponseTime: 0
  };

  data.forEach((row, index) => {
    if (index === 0) return; // Skip header

    const channel = row[3];
    const type = row[4];

    if (!analytics.byChannel[channel]) analytics.byChannel[channel] = 0;
    if (!analytics.byType[type]) analytics.byType[type] = 0;

    analytics.byChannel[channel]++;
    analytics.byType[type]++;
  });

  return analytics;
}

function displayCommunicationAnalytics() {
  const analytics = getCommunicationAnalytics();

  if (!analytics) {
    Logger.log("No communication data available");
    return;
  }

  Logger.log("\n=== COMMUNICATION ANALYTICS ===");
  Logger.log("Total Interactions: " + analytics.totalInteractions);

  Logger.log("\nBy Channel:");
  for (let channel in analytics.byChannel) {
    Logger.log("  " + channel + ": " + analytics.byChannel[channel]);
  }

  Logger.log("\nBy Type:");
  for (let type in analytics.byType) {
    Logger.log("  " + type + ": " + analytics.byType[type]);
  }
}

// ============================================
// TEST FUNCTIONS
// ============================================

function testCommunicationHub() {
  Logger.log("Testing Communication Hub...");

  setupCommunicationHub();

  // Log sample communications
  Logger.log("\nLogging sample communications...");

  logCommunication("Rajesh Patel", "Email", "Follow-up", "Proposal email sent", "", "Sent", "");
  logCommunication("Rajesh Patel", "Email", "Follow-up", "Email opened", "", "Opened", "");
  logCommunication("Rajesh Patel", "WhatsApp", "Inquiry", "Sent follow-up message", "", "Delivered", "");
  logCommunication("Rajesh Patel", "Phone Call", "Negotiation", "Call with Rajesh", "15", "Completed", "Discussed budget and timeline");

  logCommunication("Priya Sharma", "Email", "Follow-up", "Welcome email", "", "Sent", "");
  logCommunication("Priya Sharma", "WhatsApp", "Support", "Client support message", "", "Read", "");
  logCommunication("Priya Sharma", "In-person", "Negotiation", "Office meeting", "60", "Completed", "Signed agreement");

  // Display analytics
  displayCommunicationAnalytics();

  // Display timelines
  displayInteractionTimeline("Rajesh Patel");
  displayInteractionTimeline("Priya Sharma");

  Logger.log("\nCommunication Hub test complete! Check sheets for details.");
}

// ============================================
// MENU SETUP
// ============================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu("Communication Hub")
    .addItem("Setup Communication Hub", "setupCommunicationHub")
    .addItem("Test Communication Hub", "testCommunicationHub")
    .addItem("View Analytics", "displayCommunicationAnalytics")
    .addItem("Update Hub", "updateCommunicationHub")
    .addToUi();

  Logger.log("Communication Hub menu ready.");
}
