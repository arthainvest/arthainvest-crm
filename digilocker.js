// ArthaInvest CRM - DigiLocker System
// Secure client data storage with role-based access control

const digiLockerStorage = {
  documents: [
    {
      id: 1,
      clientName: 'Rajesh Kumar',
      clientId: 'CLI-001',
      documentType: 'KYC',
      fileName: 'Rajesh_Kumar_KYC_2026.pdf',
      fileSize: '245 KB',
      uploadedBy: 'rajesh',
      uploadedDate: '2026-08-10',
      expiryDate: '2027-08-10',
      status: 'Active',
      tags: ['kyc', 'verified'],
      visibility: 'admin_rajesh'
    },
    {
      id: 2,
      clientName: 'Rajesh Kumar',
      clientId: 'CLI-001',
      documentType: 'Bank Statements',
      fileName: 'ICICI_BankStatement_Jul2026.pdf',
      fileSize: '512 KB',
      uploadedBy: 'rajesh',
      uploadedDate: '2026-08-09',
      expiryDate: null,
      status: 'Active',
      tags: ['bank', 'statement'],
      visibility: 'admin_rajesh'
    },
    {
      id: 3,
      clientName: 'Priya Sharma',
      clientId: 'CLI-002',
      documentType: 'Insurance Policy',
      fileName: 'TATA_PolicyDoc_InsuranceID12345.pdf',
      fileSize: '1.2 MB',
      uploadedBy: 'priya',
      uploadedDate: '2026-08-08',
      expiryDate: '2027-08-08',
      status: 'Active',
      tags: ['insurance', 'policy', 'tata'],
      visibility: 'admin_priya'
    },
    {
      id: 4,
      clientName: 'Amit Patel',
      clientId: 'CLI-003',
      documentType: 'Loan Agreement',
      fileName: 'HDFC_LoanAgreement_LoanID54321.pdf',
      fileSize: '890 KB',
      uploadedBy: 'amit',
      uploadedDate: '2026-08-07',
      expiryDate: null,
      status: 'Active',
      tags: ['loan', 'hdfc', 'dsa'],
      visibility: 'admin_amit'
    }
  ]
};

// Document Categories
const documentCategories = {
  'KYC': { icon: '🆔', description: 'Know Your Customer documents' },
  'Bank Statements': { icon: '🏦', description: 'Bank account statements' },
  'Insurance Policy': { icon: '🛡️', description: 'Insurance policy documents' },
  'Loan Agreement': { icon: '📜', description: 'Loan agreement documents' },
  'Investment Proof': { icon: '📈', description: 'Investment proofs' },
  'Income Certificate': { icon: '📄', description: 'Income certificates' },
  'PAN Card': { icon: '🆔', description: 'PAN card details' },
  'Aadhar Card': { icon: '🆔', description: 'Aadhar identification' },
  'Address Proof': { icon: '🏠', description: 'Address proof documents' },
  'Other Documents': { icon: '📋', description: 'Other important documents' }
};

// Upload document to DigiLocker
function uploadDocumentToDigiLocker(documentData) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return { success: false, message: 'Not logged in' };
  }

  const newDocument = {
    id: digiLockerStorage.documents.length + 1,
    ...documentData,
    uploadedBy: currentUser.username,
    uploadedDate: new Date().toISOString().split('T')[0],
    status: 'Active',
    visibility: `admin_${currentUser.username}`
  };

  digiLockerStorage.documents.push(newDocument);

  return {
    success: true,
    message: `Document "${documentData.fileName}" uploaded to DigiLocker`,
    document: newDocument
  };
}

// Get documents (with access control)
function getClientDocuments(clientId) {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return [];
  }

  // Admin can see all documents
  if (currentUser.role === 'admin') {
    return digiLockerStorage.documents.filter(doc => doc.clientId === clientId);
  }

  // Employees can only see their own documents
  return digiLockerStorage.documents.filter(
    doc => doc.clientId === clientId && doc.visibility.includes(currentUser.username)
  );
}

// Get all documents for current user
function getMyDocuments() {
  const currentUser = getCurrentUser();

  if (!currentUser) {
    return [];
  }

  if (currentUser.role === 'admin') {
    return digiLockerStorage.documents;
  }

  return digiLockerStorage.documents.filter(
    doc => doc.visibility.includes(currentUser.username)
  );
}

// Download document (admin can download all, employees only their own)
function downloadDocument(documentId) {
  const currentUser = getCurrentUser();
  const document = digiLockerStorage.documents.find(doc => doc.id === documentId);

  if (!document) {
    return { success: false, message: 'Document not found' };
  }

  // Check access
  if (currentUser.role !== 'admin' && !document.visibility.includes(currentUser.username)) {
    return { success: false, message: 'Access denied' };
  }

  return {
    success: true,
    message: `Downloaded: ${document.fileName}`,
    document: document,
    downloadUrl: `/digilocker/download/${document.id}`
  };
}

// Delete document (only admin)
function deleteDocument(documentId) {
  const currentUser = getCurrentUser();

  if (currentUser.role !== 'admin') {
    return { success: false, message: 'Only admin can delete documents' };
  }

  const index = digiLockerStorage.documents.findIndex(doc => doc.id === documentId);

  if (index === -1) {
    return { success: false, message: 'Document not found' };
  }

  const deleted = digiLockerStorage.documents.splice(index, 1);
  return {
    success: true,
    message: `Document "${deleted[0].fileName}" deleted from DigiLocker`,
    document: deleted[0]
  };
}

// Share document (employee to admin approval)
function shareDocumentForApproval(documentId, message) {
  const currentUser = getCurrentUser();
  const document = digiLockerStorage.documents.find(doc => doc.id === documentId);

  if (!document) {
    return { success: false, message: 'Document not found' };
  }

  if (currentUser.role !== 'employee' && !document.visibility.includes(currentUser.username)) {
    return { success: false, message: 'Access denied' };
  }

  return {
    success: true,
    message: `Document "${document.fileName}" shared for admin approval`,
    notificationSent: true,
    adminNotification: {
      type: 'document_approval',
      employee: currentUser.name,
      document: document.fileName,
      message: message,
      timestamp: new Date().toISOString()
    }
  };
}

// Get document statistics (admin only)
function getDigiLockerStats() {
  const currentUser = getCurrentUser();

  if (currentUser.role !== 'admin') {
    return null;
  }

  return {
    totalDocuments: digiLockerStorage.documents.length,
    totalSize: `${(digiLockerStorage.documents.length * 0.8).toFixed(2)} MB`,
    documentsByType: getDocumentsByType(),
    documentsByEmployee: getDocumentsByEmployee(),
    recentUploads: getRecentDocuments(5)
  };
}

// Get documents grouped by type
function getDocumentsByType() {
  const byType = {};

  digiLockerStorage.documents.forEach(doc => {
    byType[doc.documentType] = (byType[doc.documentType] || 0) + 1;
  });

  return byType;
}

// Get documents by employee
function getDocumentsByEmployee() {
  const byEmployee = {};

  digiLockerStorage.documents.forEach(doc => {
    byEmployee[doc.uploadedBy] = (byEmployee[doc.uploadedBy] || 0) + 1;
  });

  return byEmployee;
}

// Get recent documents
function getRecentDocuments(limit = 5) {
  return digiLockerStorage.documents
    .sort((a, b) => new Date(b.uploadedDate) - new Date(a.uploadedDate))
    .slice(0, limit);
}

// Search documents
function searchDigiLocker(query) {
  const currentUser = getCurrentUser();
  const lowerQuery = query.toLowerCase();

  let results = digiLockerStorage.documents.filter(doc => {
    return (
      doc.clientName.toLowerCase().includes(lowerQuery) ||
      doc.fileName.toLowerCase().includes(lowerQuery) ||
      doc.documentType.toLowerCase().includes(lowerQuery)
    );
  });

  // Filter by access
  if (currentUser.role !== 'admin') {
    results = results.filter(doc => doc.visibility.includes(currentUser.username));
  }

  return results;
}

// Get DigiLocker summary
function getDigiLockerSummary() {
  const currentUser = getCurrentUser();
  const documents = currentUser.role === 'admin'
    ? digiLockerStorage.documents
    : getMyDocuments();

  return {
    totalDocuments: documents.length,
    activeDocuments: documents.filter(d => d.status === 'Active').length,
    expiredDocuments: documents.filter(d => d.expiryDate && new Date(d.expiryDate) < new Date()).length,
    pendingDocuments: documents.filter(d => d.status === 'Pending').length
  };
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    uploadDocumentToDigiLocker,
    getClientDocuments,
    getMyDocuments,
    downloadDocument,
    deleteDocument,
    shareDocumentForApproval,
    getDigiLockerStats,
    getDigiLockerSummary,
    searchDigiLocker,
    documentCategories
  };
}
