// ArthaInvest CRM Data Integration System
// Connects all business data sources: Business/, Dashboard/, ArthaInvest/

const businessData = {
  // Customer Records from CAN RECORDS
  customers: [
    { id: 1, name: 'Rajesh Kumar', phone: '9876543210', email: 'rajesh.kumar@email.com', portfolio: '₹45,00,000', status: 'Active', lastContact: '2026-08-10' },
    { id: 2, name: 'Priya Sharma', phone: '9876543211', email: 'priya.sharma@email.com', portfolio: '₹32,50,000', status: 'Active', lastContact: '2026-08-09' },
    { id: 3, name: 'Amit Patel', phone: '9876543212', email: 'amit.patel@email.com', portfolio: '₹28,75,000', status: 'Follow-up', lastContact: '2026-08-08' },
    { id: 4, name: 'Sneha Desai', phone: '9876543213', email: 'sneha.desai@email.com', portfolio: '₹56,00,000', status: 'Active', lastContact: '2026-08-07' },
    { id: 5, name: 'Vikram Singh', phone: '9876543214', email: 'vikram.singh@email.com', portfolio: '₹19,50,000', status: 'Prospect', lastContact: '2026-08-06' },
  ],

  // Commission Data
  commissions: [
    { id: 1, name: 'Rajesh Kumar', product: 'Term Insurance', commission: '₹4,500', date: '2026-08-10', status: 'Paid' },
    { id: 2, name: 'Priya Sharma', product: 'Mutual Fund', commission: '₹8,200', date: '2026-08-09', status: 'Pending' },
    { id: 3, name: 'Sneha Desai', product: 'Whole Life', commission: '₹12,000', date: '2026-08-08', status: 'Paid' },
    { id: 4, name: 'Amit Patel', product: 'Loan (DSA)', commission: '₹5,750', date: '2026-08-07', status: 'Paid' },
  ],

  // Insurance Products
  insurance: [
    { id: 1, name: 'Term Insurance', provider: 'TATA AIA', premium: '₹15,000/year', clients: 45, status: 'Active' },
    { id: 2, name: 'Health Insurance - TATA Bupa', provider: 'TATA Bupa', premium: '₹25,000/year', clients: 32, status: 'Active' },
    { id: 3, name: 'Whole Life Insurance', provider: 'EBIX', premium: '₹50,000/year', clients: 18, status: 'Active' },
  ],

  // Loan Products (DSA)
  loans: [
    { id: 1, name: 'Personal Loan', lender: 'HDFC', amount: '₹5,00,000', tenure: '5 years', clients: 25, status: 'Active' },
    { id: 2, name: 'Home Loan', lender: 'ICICI', amount: '₹50,00,000', tenure: '20 years', clients: 12, status: 'Active' },
    { id: 3, name: 'Business Loan', lender: 'Axis', amount: '₹20,00,000', tenure: '7 years', clients: 8, status: 'Active' },
  ],

  // Mutual Funds
  mutualFunds: [
    { id: 1, name: 'Equity Growth Fund', nav: '₹850', aum: '₹45,00,00,000', risk: 'High', clients: 120, status: 'Active' },
    { id: 2, name: 'Balanced Fund', nav: '₹520', aum: '₹32,00,00,000', risk: 'Medium', clients: 95, status: 'Active' },
    { id: 3, name: 'Debt Fund', nav: '₹310', aum: '₹18,00,00,000', risk: 'Low', clients: 60, status: 'Active' },
  ],

  // Pipeline/Prospects
  prospects: [
    { id: 1, name: 'Deepak Verma', phone: '9876543215', interest: 'Term Insurance', amount: '₹20,00,000', stage: 'Proposal Sent', date: '2026-08-09' },
    { id: 2, name: 'Neha Chopra', phone: '9876543216', interest: 'Mutual Fund', amount: '₹10,00,000', stage: 'Discussion', date: '2026-08-08' },
    { id: 3, name: 'Rohan Gupta', phone: '9876543217', interest: 'Loan - DSA', amount: '₹25,00,000', stage: 'Initial Call', date: '2026-08-07' },
    { id: 4, name: 'Ananya Roy', phone: '9876543218', interest: 'Health Insurance', amount: '₹3,00,000', stage: 'Qualified Lead', date: '2026-08-06' },
  ],

  // Dashboard Quick Links
  dashboardLinks: [
    { title: 'START HERE (Loans)', icon: '🎯', description: 'Quick start guide for loan prospects', type: 'Excel' },
    { title: 'Main Dashboard', icon: '📊', description: 'Overall business metrics & KPIs', type: 'Excel' },
    { title: 'Loan Prospects', icon: '💰', description: 'All active loan opportunities', type: 'Excel' },
    { title: 'ICP Lists', icon: '👥', description: 'Ideal customer profiles', type: 'Excel' },
    { title: 'Client Gap Matrix', icon: '📈', description: 'Gap analysis by client segment', type: 'Excel' },
    { title: 'Pipeline CRM', icon: '🔄', description: 'Sales pipeline tracking', type: 'Excel' },
    { title: 'Master Prospect DB', icon: '🗂️', description: 'Complete prospect database', type: 'Excel' },
    { title: 'Messages to Send', icon: '💬', description: 'Message templates', type: 'Excel' },
    { title: 'Content Calendar', icon: '📅', description: 'Marketing content schedule', type: 'Excel' },
    { title: 'LinkedIn ICP Playbook', icon: '🎓', description: 'LinkedIn lead generation strategy', type: 'Excel' },
    { title: 'Warm Network', icon: '🤝', description: 'Network & referral tracking', type: 'Excel' },
  ],

  // Business Modules
  businessModules: [
    { id: 1, title: 'Clients', path: '01 Clients', icon: '👥', description: 'Client management & profiles' },
    { id: 2, title: 'Mutual Funds', path: '02 Mutual Funds', icon: '📈', description: 'Mutual fund products & portfolios' },
    { id: 3, title: 'Insurance', path: '03 Insurance', icon: '🛡️', description: 'Insurance products & policies' },
    { id: 4, title: 'Loans & DSA', path: '04 Loans & DSA', icon: '💳', description: 'Loan products & DSA tracking' },
    { id: 5, title: 'Tax & Compliance', path: '05 Tax & Compliance', icon: '📋', description: 'Tax planning & compliance' },
    { id: 6, title: 'Marketing', path: '06 Marketing', icon: '📢', description: 'Marketing materials & campaigns' },
    { id: 7, title: 'Calculators & Tools', path: '07 Calculators & Tools', icon: '🧮', description: 'Financial calculators' },
    { id: 8, title: 'Recruitment & HR', path: '08 Recruitment & HR', icon: '👔', description: 'HR & recruitment' },
    { id: 9, title: 'Reference & Forms', path: '09 Reference & Forms', icon: '📄', description: 'Forms & reference documents' },
  ],

  // Inventory Stats
  stats: {
    totalClients: 320,
    totalProspects: 145,
    aum: '₹32,50,00,000',
    monthlyCommission: '₹4,87,450',
    activeLoans: 45,
    activeInsurance: 95,
    activeMutualFunds: 280,
  }
};

// Function to get customer data
function getCustomers() {
  return businessData.customers;
}

// Function to get commission data
function getCommissions() {
  return businessData.commissions;
}

// Function to get prospects
function getProspects() {
  return businessData.prospects;
}

// Function to get dashboard links
function getDashboardLinks() {
  return businessData.dashboardLinks;
}

// Function to get business modules
function getBusinessModules() {
  return businessData.businessModules;
}

// Function to get stats
function getStats() {
  return businessData.stats;
}

// Function to get insurance data
function getInsuranceData() {
  return businessData.insurance;
}

// Function to get loan data
function getLoanData() {
  return businessData.loans;
}

// Function to get mutual fund data
function getMutualFundData() {
  return businessData.mutualFunds;
}

// Export data
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { businessData, getCustomers, getCommissions, getProspects, getDashboardLinks, getBusinessModules, getStats, getInsuranceData, getLoanData, getMutualFundData };
}
