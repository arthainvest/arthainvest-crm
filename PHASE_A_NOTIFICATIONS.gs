/**
 * ARTHAINVEST CRM - PHASE A: NOTIFICATION SYSTEM
 * Sends WhatsApp alerts for important events
 *
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Copy-paste this entire code
 * 4. Save and authorize
 * 5. Run "setupNotifications()"
 */

// ============================================
// CONFIGURATION
// ============================================

// WhatsApp notification log sheet
const NOTIFICATION_SHEET_NAME = "Notification Log";
const LEADS_SHEET = "Leads";
const CLIENTS_SHEET = "Clients";
const DEALS_SHEET = "Deals";

// WhatsApp message templates
const NOTIFICATION_TEMPLATES = {
  LEAD_ASSIGNED: {
    title: "Lead Assigned",
    template: "New lead assigned: {leadName} from {source}. Budget: {budget}. Timeline: {timeline} months. Contact: {phone}"
  },
  DEAL_CREATED: {
    title: "Deal Created",
    template: "New deal created: {dealName}. Expected value: ₹{dealValue}. Close date: {closeDate}. Stage: {stage}"
  },
  LEAD_SCORE_CHANGED: {
    title: "Lead Score Update",
    template: "{leadName} score updated to {score}. Tier: {tier}. Action: {action}"
  },
  RENEWAL_DUE: {
    title: "Renewal Due",
    template: "{clientName}'s {product} renewal is due on {renewalDate}. Premium: ₹{premium}. Action needed!"
  },
  COMMISSION_EARNED: {
    title: "Commission Earned",
    template: "Commission earned: ₹{amount} from {clientName} ({product}). Total month: ₹{monthlyTotal}"
  },
  CLIENT_DORMANT: {
    title: "Client Dormant Alert",
    template: "{clientName} has been inactive for 30 days. Last contact: {lastContact}. Re-engagement needed!"
  }
};

// ============================================
// MAIN FUNCTIONS
// ============================================

function setupNotifications() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Create Notification Log sheet if doesn't exist
  if (!ss.getSheetByName(NOTIFICATION_SHEET_NAME)) {
    const notificationSheet = ss.insertSheet(NOTIFICATION_SHEET_NAME);

    // Add headers
    const headers = ["Notification ID", "Date & Time", "Event Type", "Lead/Client Name",
                     "Message", "WhatsApp Status", "Recipient Phone", "Notes"];
    notificationSheet.getRange("A1:H1").setValues([headers]);

    // Format header
    notificationSheet.getRange("A1:H1")
      .setFontWeight("bold")
      .setBackground("#1F4788")
      .setFontColor("white");

    // Set column widths
    notificationSheet.setColumnWidths([80, 150, 120, 150, 300, 120, 120, 200]);
  }

  Logger.log("Notification system setup complete!");
}

function sendNotification(eventType, data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const notificationSheet = ss.getSheetByName(NOTIFICATION_SHEET_NAME);

  if (!notificationSheet) {
    Logger.log("Error: Notification Log sheet not found");
    return;
  }

  const template = NOTIFICATION_TEMPLATES[eventType];
  if (!template) {
    Logger.log("Error: Template not found for " + eventType);
    return;
  }

  // Build message
  let message = template.template;
  for (let key in data) {
    message = message.replace("{" + key + "}", data[key]);
  }

  // Add to log
  const notificationId = "NTF-" + new Date().getTime();
  const newRow = [
    notificationId,
    new Date(),
    eventType,
    data.leadName || data.clientName || data.dealName || "N/A",
    message,
    "Logged",
    data.phone || "N/A",
    "Phase A notification"
  ];

  notificationSheet.appendRow(newRow);

  // Log to console
  Logger.log("[NOTIFICATION] " + eventType + ": " + message);

  // TODO: Integrate with WhatsApp API when ready
  // sendToWhatsApp(data.phone, message);
}

// ============================================
// EVENT TRIGGERS
// ============================================

function onLeadAssigned() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);
  const lastRow = leadsSheet.getLastRow();

  if (lastRow > 1) {
    const lastData = leadsSheet.getRange(lastRow, 1, 1, 15).getValues()[0];

    sendNotification("LEAD_ASSIGNED", {
      leadName: lastData[1] || "Unknown",
      source: lastData[6] || "Unknown",
      budget: lastData[10] || "N/A",
      timeline: lastData[11] || "N/A",
      phone: lastData[2] || "N/A"
    });
  }
}

function onDealCreated() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dealsSheet = ss.getSheetByName(DEALS_SHEET);
  const lastRow = dealsSheet.getLastRow();

  if (lastRow > 1) {
    const lastData = dealsSheet.getRange(lastRow, 1, 1, 14).getValues()[0];

    sendNotification("DEAL_CREATED", {
      dealName: lastData[1] || "Unknown",
      dealValue: lastData[4] || "N/A",
      closeDate: lastData[6] || "N/A",
      stage: lastData[7] || "N/A"
    });
  }
}

function checkRenewals() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const clientsSheet = ss.getSheetByName(CLIENTS_SHEET);
  const data = clientsSheet.getRange(2, 1, clientsSheet.getLastRow() - 1, 20).getValues();

  const today = new Date();
  const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

  data.forEach((row, index) => {
    const clientName = row[1];
    const renewalDate = row[10];
    const product = row[4];
    const premium = row[8];
    const phone = row[2];

    if (renewalDate && clientName) {
      const renewalDateObj = new Date(renewalDate);

      // Check if renewal is in next 7 days
      if (renewalDateObj >= today && renewalDateObj <= nextWeek) {
        sendNotification("RENEWAL_DUE", {
          clientName: clientName,
          product: product || "N/A",
          renewalDate: renewalDate.toLocaleDateString(),
          premium: premium || "N/A",
          phone: phone || "N/A"
        });
      }
    }
  });
}

function checkDormantClients() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const clientsSheet = ss.getSheetByName(CLIENTS_SHEET);
  const data = clientsSheet.getRange(2, 1, clientsSheet.getLastRow() - 1, 20).getValues();

  const today = new Date();
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

  data.forEach((row) => {
    const clientName = row[1];
    const lastContact = row[17]; // Adjust column if needed
    const status = row[14];
    const phone = row[2];

    if (clientName && status === "Active" && lastContact) {
      const lastContactObj = new Date(lastContact);

      if (lastContactObj < thirtyDaysAgo) {
        sendNotification("CLIENT_DORMANT", {
          clientName: clientName,
          lastContact: lastContact.toLocaleDateString(),
          phone: phone || "N/A"
        });
      }
    }
  });
}

// ============================================
// MANUAL TRIGGER FUNCTIONS
// ============================================

function testNotificationSystem() {
  Logger.log("Testing Notification System...");

  // Setup notification log
  setupNotifications();

  // Send test notifications
  sendNotification("LEAD_ASSIGNED", {
    leadName: "Rajesh Patel",
    source: "LinkedIn",
    budget: "50,00,000",
    timeline: "2",
    phone: "98765-43210"
  });

  sendNotification("DEAL_CREATED", {
    dealName: "Rajesh Corp Insurance",
    dealValue: "15,00,000",
    closeDate: "2026-09-15",
    stage: "Proposal"
  });

  sendNotification("RENEWAL_DUE", {
    clientName: "Priya Sharma",
    product: "Tata AIG Term",
    renewalDate: "2026-09-15",
    premium: "5000",
    phone: "98765-43211"
  });

  sendNotification("COMMISSION_EARNED", {
    clientName: "Priya Sharma",
    amount: "40000",
    product: "Tata AIG Term",
    monthlyTotal: "136000",
    phone: "98765-43211"
  });

  Logger.log("Test notifications sent! Check 'Notification Log' sheet");
}

// ============================================
// SCHEDULED TRIGGERS (Set up in Google Sheets)
// ============================================

function dailyNotificationCheck() {
  checkRenewals();
  checkDormantClients();
}

// ============================================
// WHATSAPP INTEGRATION (Ready for API)
// ============================================

function sendToWhatsApp(phoneNumber, message) {
  // This function is ready to integrate with WhatsApp Business API
  // Currently logs to console - ready for API setup

  const payload = {
    to: phoneNumber,
    message: message,
    timestamp: new Date()
  };

  Logger.log("[WhatsApp API Ready] Message to " + phoneNumber + ": " + message);

  // TODO: Replace with actual WhatsApp API call
  // Example:
  // const url = "https://api.whatsapp.com/send";
  // const options = {
  //   method: 'post',
  //   payload: JSON.stringify(payload),
  //   headers: { 'Content-Type': 'application/json' }
  // };
  // UrlFetchApp.fetch(url, options);
}

// ============================================
// MENU SETUP
// ============================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu("Notifications")
    .addItem("Setup Notification System", "setupNotifications")
    .addItem("Test Notifications", "testNotificationSystem")
    .addItem("Check Renewals Now", "checkRenewals")
    .addItem("Check Dormant Clients", "checkDormantClients")
    .addItem("Run Daily Check", "dailyNotificationCheck")
    .addToUi();

  Logger.log("Notification menu added. Click 'Notifications' in menu bar to use.");
}
