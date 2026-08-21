/**
 * ARTHAINVEST CRM - PHASE C: LEAD SCORING ENGINE
 * Automatically calculates lead scores (0-100) and categorizes tiers
 *
 * SETUP INSTRUCTIONS:
 * 1. Open your Google Sheet
 * 2. Tools → Script Editor
 * 3. Copy-paste this entire code (REPLACE Phase B code)
 * 4. Save and authorize
 * 5. Run "setupLeadScoring()"
 */

// ============================================
// CONFIGURATION
// ============================================

const LEADS_SHEET = "Leads";
const SCORING_SHEET = "Lead Scoring";
const SCORING_LOGS_SHEET = "Scoring Logs";

// Scoring weights
const SCORING_WEIGHTS = {
  ENGAGEMENT: {
    emailOpens: 5,
    whatsappReplies: 10,
    calls: 8,
    meetings: 12,
    maxPoints: 30
  },
  FIRMOGRAPHY: {
    companySize: 15,
    industryFit: 15,
    maxPoints: 30
  },
  BEHAVIOR: {
    budgetConfirmed: 10,
    timeline: 10,
    proposalSent: 5,
    maxPoints: 25
  },
  CHARACTERISTICS: {
    qualificationStatus: 8,
    sourceQuality: 7,
    maxPoints: 15
  },
  DECAY: {
    noContact7Days: -2,
    noContact14Days: -5
  }
};

// Lead tier definitions
const LEAD_TIERS = [
  { name: "HOT", minScore: 80, color: "FF0000", action: "Call immediately" },
  { name: "WARM", minScore: 60, color: "FFA500", action: "Schedule meeting" },
  { name: "COOL", minScore: 40, color: "FFFF00", action: "Nurture sequence" },
  { name: "COLD", minScore: 20, color: "0000FF", action: "Email campaign" },
  { name: "VERY COLD", minScore: 0, color: "808080", action: "Re-engagement" }
];

// ============================================
// SETUP FUNCTIONS
// ============================================

function setupLeadScoring() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);

  if (!leadsSheet) {
    Logger.log("Error: Leads sheet not found");
    return;
  }

  // Add Lead Score column if doesn't exist
  const headers = leadsSheet.getRange(1, 1, 1, 15).getValues()[0];
  if (!headers.includes("Lead Score")) {
    leadsSheet.insertColumns(15);
    leadsSheet.getRange(1, 15).setValue("Lead Score");
    leadsSheet.getRange(1, 15).setFontWeight("bold").setBackground("#F79646");
  }

  if (!headers.includes("Lead Tier")) {
    leadsSheet.insertColumns(16);
    leadsSheet.getRange(1, 16).setValue("Lead Tier");
    leadsSheet.getRange(1, 16).setFontWeight("bold").setBackground("#F79646");
  }

  // Create Scoring Logs sheet
  if (!ss.getSheetByName(SCORING_LOGS_SHEET)) {
    const logsSheet = ss.insertSheet(SCORING_LOGS_SHEET);
    const headers = ["Lead Name", "Previous Score", "New Score", "Change", "New Tier",
                     "Scoring Date", "Engagement", "Firmography", "Behavior", "Characteristics", "Decay"];
    logsSheet.getRange("A1:K1").setValues([headers]);
    logsSheet.getRange("A1:K1")
      .setFontWeight("bold")
      .setBackground("#F79646")
      .setFontColor("white");
  }

  Logger.log("Lead Scoring system setup complete!");
}

// ============================================
// MAIN SCORING ENGINE
// ============================================

function calculateLeadScores() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);

  if (!leadsSheet) {
    Logger.log("Error: Leads sheet not found");
    return;
  }

  const lastRow = leadsSheet.getLastRow();
  if (lastRow < 2) {
    Logger.log("No leads to score");
    return;
  }

  // Get all lead data
  const leadsData = leadsSheet.getRange(2, 1, lastRow - 1, 20).getValues();

  leadsData.forEach((row, index) => {
    const leadName = row[1];
    const leadScore = calculateIndividualScore(row);
    const leadTier = getTierFromScore(leadScore.total);

    // Update in sheet
    const rowNum = index + 2;
    leadsSheet.getRange(rowNum, 15).setValue(leadScore.total);
    leadsSheet.getRange(rowNum, 16).setValue(leadTier.name);

    // Color code the tier
    leadsSheet.getRange(rowNum, 16).setBackground(leadTier.color).setFontWeight("bold");

    // Log the scoring
    logScoreCalculation(leadName, leadScore, leadTier);

    Logger.log("[SCORE] " + leadName + ": " + leadScore.total + " (" + leadTier.name + ")");
  });

  Logger.log("Lead scoring complete! " + (lastRow - 1) + " leads scored.");
}

function calculateIndividualScore(leadRow) {
  let scores = {
    engagement: 0,
    firmography: 0,
    behavior: 0,
    characteristics: 0,
    decay: 0,
    total: 0
  };

  // Extract lead data from row
  const leadName = leadRow[1];
  const qualification = leadRow[8]; // Column I
  const source = leadRow[6]; // Column G
  const budget = leadRow[10]; // Column J
  const timeline = leadRow[11]; // Column K
  const lastContact = leadRow[13]; // Column M

  // ============ ENGAGEMENT SCORING ============
  // Simplified for now - can integrate with Communications sheet
  scores.engagement = 15; // Placeholder - update based on actual engagement data

  // ============ FIRMOGRAPHY SCORING ============
  // Company size and industry fit
  if (source === "LinkedIn" || source === "Referral") {
    scores.firmography = 25; // High quality source
  } else {
    scores.firmography = 15;
  }

  // ============ BEHAVIOR SCORING ============
  if (budget && budget !== "") {
    scores.behavior += 10; // Budget confirmed
  }

  if (timeline && timeline < 3) {
    scores.behavior += 10; // Timeline < 3 months
  }

  // ============ CHARACTERISTICS SCORING ============
  if (qualification === "Qualified") {
    scores.characteristics += 8;
  } else if (qualification === "Warm") {
    scores.characteristics += 4;
  }

  if (source === "Referral" || source === "LinkedIn") {
    scores.characteristics += 7; // Quality source
  }

  // ============ DECAY SCORING ============
  if (lastContact) {
    const lastContactDate = new Date(lastContact);
    const today = new Date();
    const daysNoContact = Math.floor((today - lastContactDate) / (1000 * 60 * 60 * 24));

    if (daysNoContact > 14) {
      scores.decay = -5;
    } else if (daysNoContact > 7) {
      scores.decay = -2;
    }
  }

  // ============ CALCULATE TOTAL ============
  scores.total = Math.min(100, Math.max(0,
    Math.min(scores.engagement, SCORING_WEIGHTS.ENGAGEMENT.maxPoints) +
    Math.min(scores.firmography, SCORING_WEIGHTS.FIRMOGRAPHY.maxPoints) +
    Math.min(scores.behavior, SCORING_WEIGHTS.BEHAVIOR.maxPoints) +
    Math.min(scores.characteristics, SCORING_WEIGHTS.CHARACTERISTICS.maxPoints) +
    scores.decay
  ));

  return scores;
}

function getTierFromScore(score) {
  for (let tier of LEAD_TIERS) {
    if (score >= tier.minScore) {
      return tier;
    }
  }
  return LEAD_TIERS[LEAD_TIERS.length - 1];
}

// ============================================
// LOGGING
// ============================================

function logScoreCalculation(leadName, scores, tier) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const logsSheet = ss.getSheetByName(SCORING_LOGS_SHEET);

  if (!logsSheet) return;

  const logData = [
    leadName,
    "", // Previous score - can be enhanced
    scores.total,
    "", // Change - can be calculated
    tier.name,
    new Date(),
    scores.engagement,
    scores.firmography,
    scores.behavior,
    scores.characteristics,
    scores.decay
  ];

  logsSheet.appendRow(logData);
}

// ============================================
// ANALYSIS FUNCTIONS
// ============================================

function getScoringAnalytics() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const leadsSheet = ss.getSheetByName(LEADS_SHEET);

  if (!leadsSheet) {
    Logger.log("Error: Leads sheet not found");
    return;
  }

  const lastRow = leadsSheet.getLastRow();
  if (lastRow < 2) return;

  const leadsData = leadsSheet.getRange(2, 1, lastRow - 1, 20).getValues();
  const scoreColumn = 14; // Column O (0-indexed = 14)

  let analytics = {
    totalLeads: leadsData.length,
    hotLeads: 0,
    warmLeads: 0,
    coolLeads: 0,
    coldLeads: 0,
    veryColLeads: 0,
    averageScore: 0,
    totalScore: 0
  };

  leadsData.forEach((row) => {
    const score = row[scoreColumn] || 0;
    analytics.totalScore += score;

    if (score >= 80) analytics.hotLeads++;
    else if (score >= 60) analytics.warmLeads++;
    else if (score >= 40) analytics.coolLeads++;
    else if (score >= 20) analytics.coldLeads++;
    else analytics.veryColLeads++;
  });

  analytics.averageScore = Math.round(analytics.totalScore / analytics.totalLeads);

  return analytics;
}

function displayScoringAnalytics() {
  const analytics = getScoringAnalytics();

  Logger.log("\n=== LEAD SCORING ANALYTICS ===");
  Logger.log("Total Leads: " + analytics.totalLeads);
  Logger.log("Average Score: " + analytics.averageScore);
  Logger.log("\nTier Distribution:");
  Logger.log("HOT (80-100): " + analytics.hotLeads);
  Logger.log("WARM (60-79): " + analytics.warmLeads);
  Logger.log("COOL (40-59): " + analytics.coolLeads);
  Logger.log("COLD (20-39): " + analytics.coldLeads);
  Logger.log("VERY COLD (0-19): " + analytics.veryColLeads);
}

// ============================================
// TEST FUNCTION
// ============================================

function testLeadScoring() {
  Logger.log("Testing Lead Scoring System...");

  setupLeadScoring();

  // Add sample lead scores
  calculateLeadScores();

  // Display analytics
  displayScoringAnalytics();

  Logger.log("\nLead scoring complete! Check 'Leads' sheet for scores and 'Scoring Logs' for history.");
}

// ============================================
// SCHEDULED DAILY RECALCULATION
// ============================================

function dailyLeadScoringRecalculation() {
  Logger.log("Running daily lead score recalculation...");
  calculateLeadScores();
  displayScoringAnalytics();
}

// ============================================
// MENU SETUP
// ============================================

function onOpen() {
  const ui = SpreadsheetApp.getUi();

  ui.createMenu("Lead Scoring")
    .addItem("Setup Scoring System", "setupLeadScoring")
    .addItem("Calculate Lead Scores", "calculateLeadScores")
    .addItem("Test Lead Scoring", "testLeadScoring")
    .addItem("View Analytics", "displayScoringAnalytics")
    .addItem("Daily Recalculation", "dailyLeadScoringRecalculation")
    .addToUi();

  Logger.log("Lead Scoring menu ready.");
}
