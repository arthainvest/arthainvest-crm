// ArthaInvest CRM - User Authentication & Role Management System
// Support for Admin + 5 Employees with role-based access control

const users = {
  // Admin User
  'admin': {
    password: 'admin123',
    name: 'Artha Admin',
    email: 'admin@arthainvest.com',
    role: 'admin',
    phone: '9876543200',
    joinDate: '2026-01-01',
    permissions: ['all']
  },

  // Employee 1 - Sales
  'rajesh': {
    password: 'rajesh123',
    name: 'Rajesh Kumar',
    email: 'rajesh@arthainvest.com',
    role: 'employee',
    department: 'Sales',
    phone: '9876543201',
    joinDate: '2026-02-15',
    permissions: ['view_clients', 'edit_own_clients', 'view_pipeline', 'view_dashboard', 'marketing']
  },

  // Employee 2 - Insurance Specialist
  'priya': {
    password: 'priya123',
    name: 'Priya Sharma',
    email: 'priya@arthainvest.com',
    role: 'employee',
    department: 'Insurance',
    phone: '9876543202',
    joinDate: '2026-02-20',
    permissions: ['view_clients', 'edit_own_clients', 'view_insurance', 'view_dashboard', 'marketing']
  },

  // Employee 3 - Loan Specialist
  'amit': {
    password: 'amit123',
    name: 'Amit Patel',
    email: 'amit@arthainvest.com',
    role: 'employee',
    department: 'Loans & DSA',
    phone: '9876543203',
    joinDate: '2026-03-01',
    permissions: ['view_clients', 'edit_own_clients', 'view_loans', 'view_dashboard', 'marketing']
  },

  // Employee 4 - Mutual Funds Specialist
  'sneha': {
    password: 'sneha123',
    name: 'Sneha Desai',
    email: 'sneha@arthainvest.com',
    role: 'employee',
    department: 'Mutual Funds',
    phone: '9876543204',
    joinDate: '2026-03-10',
    permissions: ['view_clients', 'edit_own_clients', 'view_funds', 'view_dashboard', 'marketing']
  },

  // Employee 5 - Marketing & Business Development
  'vikram': {
    password: 'vikram123',
    name: 'Vikram Singh',
    email: 'vikram@arthainvest.com',
    role: 'employee',
    department: 'Marketing',
    phone: '9876543205',
    joinDate: '2026-03-20',
    permissions: ['view_clients', 'view_pipeline', 'view_dashboard', 'marketing', 'design', 'content']
  }
};

// Authenticate user
function authenticateUser(username, password) {
  const user = users[username.toLowerCase()];

  if (!user) {
    return { success: false, message: 'User not found' };
  }

  if (user.password !== password) {
    return { success: false, message: 'Invalid password' };
  }

  // Store user session
  const session = {
    username: username.toLowerCase(),
    name: user.name,
    email: user.email,
    role: user.role,
    department: user.department,
    permissions: user.permissions,
    loginTime: new Date().toISOString()
  };

  sessionStorage.setItem('arthaCRMSession', JSON.stringify(session));
  return { success: true, user: session };
}

// Get current user session
function getCurrentUser() {
  const session = sessionStorage.getItem('arthaCRMSession');
  return session ? JSON.parse(session) : null;
}

// Check if user has permission
function hasPermission(permission) {
  const user = getCurrentUser();
  if (!user) return false;
  if (user.role === 'admin') return true;
  return user.permissions.includes(permission) || user.permissions.includes('all');
}

// Logout user
function logoutUser() {
  sessionStorage.removeItem('arthaCRMSession');
  window.location.reload();
}

// Get all employees (admin only)
function getEmployees() {
  const employeeList = [];
  for (const [username, user] of Object.entries(users)) {
    if (user.role === 'employee') {
      employeeList.push({
        username,
        name: user.name,
        email: user.email,
        department: user.department,
        phone: user.phone,
        status: 'Active'
      });
    }
  }
  return employeeList;
}

// Check if logged in
function isLoggedIn() {
  return getCurrentUser() !== null;
}

// Export functions
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    authenticateUser,
    getCurrentUser,
    hasPermission,
    logoutUser,
    getEmployees,
    isLoggedIn,
    users
  };
}
