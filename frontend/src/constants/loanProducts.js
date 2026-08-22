// Shared loan-product taxonomy - Pipeline (deals) and Leads both need to agree on the same
// ids, since a deal created from a lead can fall back to the lead's declared product
// (see Pipeline.jsx's normalizeDeal). A free-text field here previously let a lead's
// product drift from these ids entirely, silently breaking the loan-type display.
export const LOAN_PRODUCTS = [
  { id: 'LAP', name: 'Loan Against Property', icon: '🏠', rate: '10-15%' },
  { id: 'OD', name: 'Overdraft', icon: '💰', rate: '12-18%' },
  { id: 'CC', name: 'Credit Card', icon: '💳', rate: '20-25%' },
  { id: 'Home', name: 'Home Loan', icon: '🏡', rate: '7-10%' },
  { id: 'Business', name: 'Business Loan', icon: '🏢', rate: '11-16%' },
  { id: 'Project', name: 'Project Loan', icon: '🏗️', rate: '10-14%' }
];
