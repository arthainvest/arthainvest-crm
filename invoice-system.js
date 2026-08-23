// ArthaInvest CRM - Invoice Generation System
// GST-ready invoice creation and management

const invoiceConfig = {
  company: {
    name: 'ArthaInvest Financial Services',
    address: 'Mumbai, Maharashtra, India',
    gst: 'GST/PAN Pending', // Will be updated when registered
    phone: '9876543200',
    email: 'billing@arthainvest.com'
  },
  invoicePrefix: 'ARTH',
  currentInvoiceNumber: 1001
};

const invoices = [
  {
    invoiceId: 'ARTH-1001',
    invoiceDate: '2026-08-10',
    clientName: 'Rajesh Kumar',
    clientId: 'CLI-001',
    clientEmail: 'rajesh.kumar@email.com',
    clientPhone: '9876543210',
    description: 'Insurance Policy Commission',
    amount: 4500,
    gstRate: 18,
    gstAmount: 810,
    totalAmount: 5310,
    status: 'Paid',
    paymentMethod: 'Bank Transfer',
    dueDate: '2026-08-20',
    paidDate: '2026-08-10',
    invoicedBy: 'rajesh',
    notes: 'TATA AIA Term Insurance - Policy Commission'
  },
  {
    invoiceId: 'ARTH-1002',
    invoiceDate: '2026-08-09',
    clientName: 'Priya Sharma',
    clientId: 'CLI-002',
    clientEmail: 'priya.sharma@email.com',
    clientPhone: '9876543211',
    description: 'Mutual Fund Investment',
    amount: 25000,
    gstRate: 18,
    gstAmount: 4500,
    totalAmount: 29500,
    status: 'Pending',
    paymentMethod: 'UPI',
    dueDate: '2026-08-23',
    invoicedBy: 'sneha',
    notes: 'SIP Investment in Equity Growth Fund'
  }
];

// Payment Methods
const paymentMethods = ['Bank Transfer', 'UPI', 'Credit Card', 'Debit Card', 'Cheque', 'Cash'];

// GST Rates
const gstRates = {
  'Insurance Services': 18,
  'Financial Advisory': 18,
  'Investment Services': 18,
  'Loan Processing': 18,
  'Other Services': 18
};

// Generate new invoice
function generateInvoice(invoiceData) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return { success: false, message: 'Not logged in' };
  }

  // Calculate GST
  const gstRate = gstRates[invoiceData.serviceType] || 18;
  const gstAmount = (invoiceData.amount * gstRate) / 100;
  const totalAmount = invoiceData.amount + gstAmount;

  const newInvoice = {
    invoiceId: `${invoiceConfig.invoicePrefix}-${invoiceConfig.currentInvoiceNumber}`,
    invoiceDate: new Date().toISOString().split('T')[0],
    ...invoiceData,
    gstRate: gstRate,
    gstAmount: gstAmount,
    totalAmount: totalAmount,
    status: 'Draft',
    invoicedBy: currentUser.username,
    dueDate: addDays(new Date(), 14).toISOString().split('T')[0]
  };

  invoiceConfig.currentInvoiceNumber++;
  invoices.push(newInvoice);

  return {
    success: true,
    message: `Invoice ${newInvoice.invoiceId} created successfully`,
    invoice: newInvoice
  };
}

// Get invoice
function getInvoice(invoiceId) {
  const invoice = invoices.find(inv => inv.invoiceId === invoiceId);

  if (!invoice) {
    return null;
  }

  return invoice;
}

// Get all invoices (with access control)
function getAllInvoices() {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return [];
  }

  // Admin can see all invoices
  if (currentUser.role === 'admin') {
    return invoices;
  }

  // Employees see only their invoices
  return invoices.filter(inv => inv.invoicedBy === currentUser.username);
}

// Update invoice status
function updateInvoiceStatus(invoiceId, newStatus) {
  const currentUser = getCurrentUser();
  const invoice = invoices.find(inv => inv.invoiceId === invoiceId);

  if (!invoice) {
    return { success: false, message: 'Invoice not found' };
  }

  // Check access
  if (currentUser.role !== 'admin' && invoice.invoicedBy !== currentUser.username) {
    return { success: false, message: 'Access denied' };
  }

  const oldStatus = invoice.status;
  invoice.status = newStatus;

  if (newStatus === 'Paid') {
    invoice.paidDate = new Date().toISOString().split('T')[0];
  }

  return {
    success: true,
    message: `Invoice status updated from ${oldStatus} to ${newStatus}`,
    invoice: invoice
  };
}

// Send invoice by email
function sendInvoiceByEmail(invoiceId) {
  const invoice = getInvoice(invoiceId);

  if (!invoice) {
    return { success: false, message: 'Invoice not found' };
  }

  return {
    success: true,
    message: `Invoice ${invoiceId} sent to ${invoice.clientEmail}`,
    emailSent: true,
    recipient: invoice.clientEmail,
    sentTime: new Date().toISOString()
  };
}

// Generate PDF (simulated)
function downloadInvoiceAsPDF(invoiceId) {
  const invoice = getInvoice(invoiceId);

  if (!invoice) {
    return { success: false, message: 'Invoice not found' };
  }

  return {
    success: true,
    message: `Invoice PDF generated: ${invoiceId}.pdf`,
    fileName: `${invoiceId}.pdf`,
    url: `/invoices/download/${invoiceId}`,
    fileSize: '245 KB'
  };
}

// Get invoice statistics
function getInvoiceStats() {
  const currentUser = getCurrentUser();
  let stats = {
    totalInvoices: 0,
    totalAmount: 0,
    paidAmount: 0,
    pendingAmount: 0,
    averageInvoiceValue: 0
  };

  const userInvoices = currentUser.role === 'admin'
    ? invoices
    : invoices.filter(inv => inv.invoicedBy === currentUser.username);

  stats.totalInvoices = userInvoices.length;
  stats.totalAmount = userInvoices.reduce((sum, inv) => sum + inv.totalAmount, 0);
  stats.paidAmount = userInvoices
    .filter(inv => inv.status === 'Paid')
    .reduce((sum, inv) => sum + inv.totalAmount, 0);
  stats.pendingAmount = stats.totalAmount - stats.paidAmount;
  stats.averageInvoiceValue = stats.totalInvoices > 0 ? (stats.totalAmount / stats.totalInvoices).toFixed(2) : 0;

  return stats;
}

// Get invoice breakdown by status
function getInvoiceBreakdown() {
  const breakdown = {
    draft: 0,
    sent: 0,
    pending: 0,
    paid: 0
  };

  invoices.forEach(inv => {
    const status = inv.status.toLowerCase();
    if (breakdown[status] !== undefined) {
      breakdown[status]++;
    }
  });

  return breakdown;
}

// Helper function to add days
function addDays(date, days) {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

// Duplicate invoice
function duplicateInvoice(invoiceId) {
  const original = getInvoice(invoiceId);

  if (!original) {
    return { success: false, message: 'Invoice not found' };
  }

  const duplicated = {
    ...original,
    invoiceId: `${invoiceConfig.invoicePrefix}-${invoiceConfig.currentInvoiceNumber}`,
    invoiceDate: new Date().toISOString().split('T')[0],
    status: 'Draft'
  };

  invoiceConfig.currentInvoiceNumber++;
  invoices.push(duplicated);

  return {
    success: true,
    message: `Invoice duplicated as ${duplicated.invoiceId}`,
    invoice: duplicated
  };
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    generateInvoice,
    getInvoice,
    getAllInvoices,
    updateInvoiceStatus,
    sendInvoiceByEmail,
    downloadInvoiceAsPDF,
    getInvoiceStats,
    getInvoiceBreakdown,
    duplicateInvoice,
    gstRates,
    paymentMethods
  };
}
