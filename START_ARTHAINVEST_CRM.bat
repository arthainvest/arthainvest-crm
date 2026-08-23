@echo off
echo.
echo ╔════════════════════════════════════════════════════════════════════════════╗
echo ║                                                                            ║
echo ║                      ARTHAINVEST CRM - ENTERPRISE SYSTEM                  ║
echo ║                                                                            ║
echo ║              Multi-Role Platform with AI, Integrations & Analytics        ║
echo ║                                                                            ║
echo ╚════════════════════════════════════════════════════════════════════════════╝
echo.

REM Navigate to CRM directory
cd /d "C:\Users\artha\LaptopHub\CRM_APP"

REM Install dependencies if needed
echo 📦 Checking dependencies...
if not exist "node_modules" (
    echo Installing npm packages...
    call npm install express sqlite3 jwt-simple bcrypt multer cors csv-parser
)

REM Start Docker services
echo.
echo 🚀 Starting services...
call docker-compose up -d

REM Wait for services to start
timeout /t 5 /nobreak >nul

echo.
echo ════════════════════════════════════════════════════════════════════════════
echo ✅ SYSTEM STARTED SUCCESSFULLY!
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 🌐 LOGIN PAGE:     http://localhost:3000/arthainvest-login.html
echo.
echo 📊 ADMIN DASHBOARD: http://localhost:3000/admin-dashboard.html
echo 👔 TEAM LEADER:     http://localhost:3000/team-leader-dashboard.html
echo 📱 MARKETING:       http://localhost:3000/marketing-dashboard.html
echo 👥 FIELD TEAM APP:  http://localhost:3000/employee-app.html
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 🔐 LOGIN CREDENTIALS:
echo.
echo ADMIN:
echo   Username: admin
echo   Password: admin123
echo   Access: Full system, all modules, team management
echo.
echo TEAM LEADER:
echo   Username: team_leader
echo   Password: admin123
echo   Access: Assign leads, manage team, update status
echo.
echo MARKETING:
echo   Username: marketing_user
echo   Password: admin123
echo   Access: Campaigns, email/WhatsApp scheduler
echo.
echo FIELD TEAM (5 Employees):
echo   🧑‍💼 Rajesh Kumar     | rajesh / admin123     | Sales & Loans
echo   👩‍💼 Priya Sharma     | priya / admin123      | Insurance
echo   👨‍💼 Amit Singh       | amit / admin123       | Loans
echo   👩‍💼 Sneha Patel      | sneha / admin123      | Mutual Funds
echo   👨‍💼 Vikram Desai     | vikram / admin123     | Marketing
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 📋 SYSTEM FEATURES:
echo ✓ Role-based access control (Admin, Team Leader, Marketing, Employees)
echo ✓ Opportunities tracker with AI scoring
echo ✓ Campaign management & tracking
echo ✓ Call logging with voice notes
echo ✓ DigiLocker document management (scoped visibility)
echo ✓ Insurance, Loans & Mutual Funds trackers
echo ✓ Brokerage account management
echo ✓ Task & follow-up calendar with reminders
echo ✓ WhatsApp integration & scheduler
echo ✓ Email scheduler with templates
echo ✓ LinkedIn integration & scheduler
echo ✓ SMS integration
echo ✓ AI automations for email/WhatsApp
echo ✓ Performance metrics & analytics
echo ✓ Team status real-time tracking
echo ✓ Bulk data upload
echo ✓ Communication history
echo ✓ Policy Boss integration
echo ✓ MFU portal integration
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.
echo 🎯 NEXT STEPS:
echo 1. Open browser and go to: http://localhost:3000/arthainvest-login.html
echo 2. Click any demo account to auto-login
echo 3. Explore features based on your role
echo 4. Create opportunities, log calls, send messages
echo 5. Check admin dashboard for real-time analytics
echo.
echo ════════════════════════════════════════════════════════════════════════════
echo.

REM Open login page in browser
start http://localhost:3000/arthainvest-login.html

echo 🌐 Opening login page in browser...
echo.
echo ✅ ArthaInvest CRM is ready!
echo.
echo To stop the system, press Ctrl+C or close this window.
echo.

pause
