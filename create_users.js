const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');

const db = new sqlite3.Database('./arthainvest-10-10.db');

// Hash password
const hashPassword = (password) => bcrypt.hashSync(password, 10);

const users = [
  {
    username: 'admin',
    email: 'admin@arthainvest.com',
    password: 'admin123',
    name: 'Administrator',
    phone: '+91-9876543210',
    role: 'admin',
    department: 'Management',
    commission_rate: 0,
    monthly_target: 0,
    call_target: 0
  },
  {
    username: 'teamleader',
    email: 'teamleader@arthainvest.com',
    password: 'teamleader123',
    name: 'Team Leader',
    phone: '+91-9876543211',
    role: 'team_leader',
    department: 'Sales',
    commission_rate: 0,
    monthly_target: 50000,
    call_target: 100
  },
  {
    username: 'yogesh_khatri',
    email: 'yogesh.khatri@arthainvest.com',
    password: 'yogesh123',
    name: 'Yogesh Khatri',
    phone: '+91-9876543212',
    role: 'employee',
    department: 'Sales',
    commission_rate: 15,
    monthly_target: 50000,
    call_target: 80
  },
  {
    username: 'chirag_rathi',
    email: 'chirag.rathi@arthainvest.com',
    password: 'chirag123',
    name: 'Chirag Rathi',
    phone: '+91-9876543213',
    role: 'employee',
    department: 'Sales',
    commission_rate: 15,
    monthly_target: 50000,
    call_target: 80
  },
  {
    username: 'amol_kasat',
    email: 'amol.kasat@arthainvest.com',
    password: 'amol123',
    name: 'Amol Kasat',
    phone: '+91-9876543214',
    role: 'employee',
    department: 'Sales',
    commission_rate: 15,
    monthly_target: 50000,
    call_target: 80
  },
  {
    username: 'employee1',
    email: 'employee1@arthainvest.com',
    password: 'employee1123',
    name: 'Employee 1',
    phone: '+91-9876543215',
    role: 'employee',
    department: 'Sales',
    commission_rate: 15,
    monthly_target: 50000,
    call_target: 80
  },
  {
    username: 'employee2',
    email: 'employee2@arthainvest.com',
    password: 'employee2123',
    name: 'Employee 2',
    phone: '+91-9876543216',
    role: 'employee',
    department: 'Sales',
    commission_rate: 15,
    monthly_target: 50000,
    call_target: 80
  }
];

console.log('\n📝 Creating user accounts...\n');

db.serialize(() => {
  users.forEach((user, index) => {
    const hashedPassword = hashPassword(user.password);

    db.run(
      `INSERT OR REPLACE INTO users
       (username, email, password, name, phone, role, department, status, online_status,
        commission_rate, monthly_target, call_target, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`,
      [
        user.username,
        user.email,
        hashedPassword,
        user.name,
        user.phone,
        user.role,
        user.department,
        'active',
        'offline',
        user.commission_rate,
        user.monthly_target,
        user.call_target
      ],
      function(err) {
        if (err) {
          console.error(`❌ Error creating ${user.name}:`, err.message);
        } else {
          console.log(`✅ Created: ${user.name} (${user.email})`);
        }

        // If last user, show summary
        if (index === users.length - 1) {
          setTimeout(() => {
            console.log('\n✅ All users created successfully!\n');
            db.close();
            process.exit(0);
          }, 500);
        }
      }
    );
  });
});

process.on('error', (err) => {
  console.error('Error:', err);
  process.exit(1);
});
