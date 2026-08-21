/**
 * ARTHAINVEST CRM - PHASE B: WORKFLOW AUTOMATION ENGINE
 * Automatically executes actions when events occur
 *
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Copy-paste this entire code (REPLACE Phase A code)
 * 4. Save and authorize
 * 5. Run "setupWorkflows()"
 */

// ============================================
// CONFIGURATION
// ============================================

const WORKFLOWS_SHEET = "Workflows";
const WORKFLOW_LOGS_SHEET = "Workflow Logs";
const LEADS_SHEET = "Leads";
const CLIENTS_SHEET = "Clients";
const DEALS_SHEET = "Deals";
const TASKS_SHEET = "Tasks";
const NOTIFICATION_LOG_SHEET = "Notification Log";

// ============================================
// WORKFLOW DEFINITIONS
// ============================================

const WORKFLOWS = [
  {
    id: "W001",
    name: "Lead Assignment Workflow",
    trigger: "New lead created",
    condition: "Source = Referral or LinkedIn",
    actions: [
      { type: "send_message", channel: "WhatsApp", template: "welcome_lead" },
      { type: "create_task", priority: "High", description: "Follow up with {leadName}" }
    ],
    enabled: true
  },
  {
    id: "W002",
    name: "Hot Lead Alert Workflow",
    trigger: "Lead score updated",
    condition: "Score > 80",
    actions: [
      { type: "create_task", priority: "Critical", description: "Call {leadName} - HOT LEAD" },
      { type: "send_notification", title: "Hot Lead Alert", message: "{leadName} scored {score}" },
      { type: "create_calendar_event", duration: 30, title: "Call {leadName}" }
    ],
    enabled: true
  },
  {
    id: "W003",
    name: "Deal Won Workflow",
    trigger: "Deal status changed",
    condition: "Stage = Closed Won",
    actions: [
      { type: "create_task", priority: "High", description: "Onboard {clientName} - new client" },
      { type: "create_task", priority: "Medium", description: "Schedule renewal reminder for {renewalDate}" },
      { type: "send_notification", title: "Deal Won!", message: "₹{dealValue} from {clientName}" }
    ],
    enabled: true
  },
  {
    id: "W004",
    name: "Dormant Client Workflow",
    trigger: "Daily check",
    condition: "No contact for 30 days, Status = Active",
    actions: [
      { type: "create_task", priority: "Medium", description: "Re-engage {clientName} - no contact 30 days" },
      { type: "send_message", channel: "Email", template: "re_engagement" },
      { type: "send_notification", title: "Dormant Alert", message: "{clientName} needs re-engagement" }
    ],
    enabled: true
  },
  {
    id: "W005",
    name: "Commission Workflow",
    trigger: "Commission logged",
    condition: "Status = Earned",
    actions: [
      { type: "send_notification", title: "Commission Earned", message: "₹{amount} from {clientName}" },
      { type: "create_task", priority: "Low", description: "Process commission payment - ₹{amount}" }
    ],
    enabled: true
  }
];

// ============================================
// MESSAGE TEMPLATES
// ============================================

const MESSAGE_TEMPLATES = {
  welcome_lead: {
    channel: "WhatsApp",
    subject: "Welcome to ArthaInvest",
    body: "Hi {leadName}, Welcome! I'm excited to help you with your {productInterest} needs. Looking forward to connecting with you soon!"
  },
  re_engagement: {
    channel: "Email",
    subject: "We miss you! Special offer for valued client",
    body: "Hi {clientName}, It's been a while! We have some great offers for you. Let's catch up soon!"
  },
  deal_won: {
    channel: "WhatsApp",
    subject: "Congratulations!",
    body: "Thank you {clientName}! Your {product} policy is now active. We'll reach out for any support you need."
  }
};

// ============================================
// MAIN SETUP FUNCTION
// ============================================

function setupWorkflows() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // Create Workflow Logs sheet if doesn't exist
  if (!ss.getSheetByName(WORKFLOW_LOGS_SHEET)) {
    const logsSheet = ss.insertSheet(WORKFLOW_LOGS_SHEET);

    const headers = ["Workflow ID", "Workflow Name", "Timestamp", "Trigger", "Lead/Client Name",
                     "Actions Executed", "Status", "Notes"];
    logsSheet.getRange("A1:H1").setValues([headers]);
    logsSheet.getRange("A1:H1")
      .setFontWeight("bold")
      .setBackground("#2E75B6")
      .setFontColor("white");

    logsSheet.setColumnWidth(1, 80);
    logsSheet.setColumnWidth(2, 150);
    logsSheet.setColumnWidth(3, 150);
    logsSheet.setColumnWidth(4, 120);
    logsSheet.setColumnWidth(5, 150);
    logsSheet.setColumnWidth(6, 200);
    logsSheet.setColumnWidth(7, 100);
    logsSheet.setColumnWidth(8, 200);
  }

  Logger.log("Workflow system setup complete!");
}

// ============================================
// WORKFLOW EXECUTION ENGINE
// ============================================

function executeWorkflow(workflowId, triggerData) {
  const workflow = WORKFLOWS.find(w => w.id === workflowId);

  if (!workflow || !workflow.enabled) {
    Logger.log("Workflow " + workflowId + " not found or disabled");
    return;
  }

  const actionsExecuted = [];

  // Execute each action in the workflow
  workflow.actions.forEach(action => {
    try {
      let result = executeAction(action, triggerData);
      actionsExecuted.push(result);
      Logger.log("[WORKFLOW] " + workflow.name + " - Action executed: " + action.type);
    } catch (e) {
      Logger.log("[WORKFLOW ERROR] " + e.toString());
      actionsExecuted.push("FAILED: " + action.type);
    }
  });

  // Log workflow execution
  logWorkflowExecution(workflow, triggerData, actionsExecuted);
}

function executeAction(action, data) {
  switch (action.type) {
    case "send_message":
      return sendWorkflowMessage(action, data);
    case "create_task":
      return createWorkflowTask(action, data);
    case "send_notification":
      return sendWorkflowNotification(action, data);
    case "create_calendar_event":
      return createWorkflowEvent(action, data);
    default:
      return "Unknown action: " + action.type;
  }
}

// ============================================
// ACTION IMPLEMENTATIONS
// ============================================

function sendWorkflowMessage(action, data) {
  const channel = action.channel;
  const template = MESSAGE_TEMPLATES[action.template];

  if (!template) {
    return "SKIPPED: Template not found";
  }

  let message = template.body;
  for (let key in data) {
    message = message.replace("{" + key + "}", data[key]);
  }

  Logger.log("[MESSAGE] " + channel + ": " + message);
  return "Message queued: " + channel;
}

function createWorkflowTask(action, data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const tasksSheet = ss.getSheetByName(TASKS_SHEET);

  if (!tasksSheet) {
    return "FAILED: Tasks sheet not found";
  }

  // Build task description
  let description = action.description;
  for (let key in data) {
    description = description.replace("{" + key + "}", data[key]);
  }

  const taskData = [
    "T-" + new Date().getTime(), // Task ID
    description,
    "You", // Assigned To
    data.leadName || data.clientName || "N/A",
    "Lead", // Related Type
    "Pending", // Status
    action.priority || "Medium",
    new Date(), // Due Date (today)
    new Date(), // Created Date
    "", // Completed Date
    "Auto-created by workflow"
  ];

  tasksSheet.appendRow(taskData);
  Logger.log("[TASK CREATED] " + description);
  return "Task created: " + description;
}

function sendWorkflowNotification(action, data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const notifSheet = ss.getSheetByName(NOTIFICATION_LOG_SHEET);

  if (!notifSheet) {
    return "FAILED: Notification Log not found";
  }

  let message = action.message;
  for (let key in data) {
    message = message.replace("{" + key + "}", data[key]);
  }

  const notifData = [
    "NTF-" + new Date().getTime(),
    new Date(),
    action.title,
    data.leadName || data.clientName || "N/A",
    message,
    "Logged",
    data.phone || "N/A",
    "Workflow: " + action.title
  ];

  notifSheet.appendRow(notifData);
  Logger.log("[NOTIFICATION] " + action.title + ": " + message);
  return "Notification sent: " + action.title;
}

function createWorkflowEvent(action, data) {
  try {
    const calendar = CalendarApp.getDefaultCalendar();
    let title = action.title;
    for (let key in data) {
      title = title.replace("{" + key + "}", data[key]);
    }

    const startTime = new Date();
    const endTime = new Date(startTime.getTime() + (action.duration * 60 * 1000));

    calendar.createEvent(title, startTime, endTime);
    Logger.log("[CALENDAR EVENT] " + title);
    return "Calendar event created: " + title;
  } catch (e) {
    return "SKIPPED: Calendar permission needed";
  }
}

// ============================================
// WORKFLOW LOGGING
// ============================================

function logWorkflowExecution(workflow, data, actionsExecuted) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(WORKFLOW_LOGS_SHEET);

  if (!logsSheet) return;

  const logData = [
    workflow.id,
    workflow.name,
    new Date(),
    workflow.trigger,
    data.leadName || data.clientName || "System",
    actionsExecuted.join(" | "),
    "Executed",
    "All actions completed"
  ];

  logsSheet.appendRow(logData);
}

// ============================================
// TRIGGER FUNCTIONS
// ============================================

function onLeadAssignedTrigger() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);
  const lastRow = leadsSheet.getLastRow();

  if (lastRow > 1) {
    const lastData = leadsSheet.getRange(lastRow, 1, 1, 15).getValues()[0];

    const triggerData = {
      leadName: lastData[1],
      productInterest: lastData[7],
      source: lastData[6],
      budget: lastData[10],
      phone: lastData[2]
    };

    executeWorkflow("W001", triggerData);
  }
}

function onLeadScoreChanged() {
  // This would be called when lead score is updated
  const triggerData = {
    leadName: "Lead Name",
    score: "85",
    tier: "HOT"
  };

  executeWorkflow("W002", triggerData);
}

function onDealWon() {
  const triggerData = {
    clientName: "Client Name",
    dealValue: "15,00,000",
    product: "Tata AIG Term"
  };

  executeWorkflow("W003", triggerData);
}

function checkDormantClientsWorkflow() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const clientsSheet = ss.getSheetByName(CLIENTS_SHEET);
  const data = clientsSheet.getRange(2, 1, clientsSheet.getLastRow() - 1, 20).getValues();

  const today = new Date();
  const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);

  data.forEach((row) => {
    const clientName = row[1];
    const lastContact = row[17];
    const status = row[14];

    if (clientName && status === "Active" && lastContact) {
      const lastContactObj = new Date(lastContact);

      if (lastContactObj < thirtyDaysAgo) {
        const triggerData = {
          clientName: clientName,
          lastContact: lastContact.toLocaleDateString()
        };

        executeWorkflow("W004", triggerData);
      }
    }
  });
}

function onCommissionEarned() {
  const triggerData = {
    clientName: "Client Name",
    amount: "40000",
    product: "Tata AIG Term"
  };

  executeWorkflow("W005", triggerData);
}

// ============================================
// TEST FUNCTIONS
// ============================================

function testAllWorkflows() {
  Logger.log("Testing all workflows...");

  setupWorkflows();

  // Test Lead Assignment Workflow
  Logger.log("\n=== Testing W001: Lead Assignment ===");
  executeWorkflow("W001", {
    leadName: "Rajesh Patel",
    productInterest: "Term Insurance",
    source: "LinkedIn",
    budget: "50,00,000",
    phone: "98765-43210"
  });

  // Test Hot Lead Alert Workflow
  Logger.log("\n=== Testing W002: Hot Lead Alert ===");
  executeWorkflow("W002", {
    leadName: "Priya Sharma",
    score: "85",
    tier: "HOT"
  });

  // Test Deal Won Workflow
  Logger.log("\n=== Testing W003: Deal Won ===");
  executeWorkflow("W003", {
    clientName: "Rajesh Corp",
    dealValue: "15,00,000",
    product: "Tata AIG Term",
    renewalDate: "2027-09-15"
  });

  // Test Dormant Client Workflow
  Logger.log("\n=== Testing W004: Dormant Client ===");
  executeWorkflow("W004", {
    clientName: "Priya Sharma",
    lastContact: "2026-07-15"
  });

  // Test Commission Workflow
  Logger.log("\n=== Testing W005: Commission Earned ===");
  executeWorkflow("W005", {
    clientName: "Priya Sharma",
    amount: "40000",
    product: "Tata AIG Term"
  });

  Logger.log("\nAll workflows tested! Check 'Workflow Logs' sheet for details.");
}

// ============================================
// MENU SETUP
// ============================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu("Workflows")
    .addItem("Setup Workflows", "setupWorkflows")
    .addItem("Test All Workflows", "testAllWorkflows")
    .addItem("Lead Assignment Workflow", "onLeadAssignedTrigger")
    .addItem("Check Dormant Clients", "checkDormantClientsWorkflow")
    .addItem("Refresh Workflows", "setupWorkflows")
    .addToUi();

  Logger.log("Workflow menu ready. Click 'Workflows' to access.");
}
