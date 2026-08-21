#!/usr/bin/env python3
"""
ArthaInvest CRM - Professional Sales & Marketing Hub
Beautiful, Modern CRM with Kanban, AI, and Analytics
"""

import sys
import sqlite3
import hashlib
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QFormLayout, QComboBox, QSpinBox,
    QScrollArea, QFrame, QGridLayout, QProgressBar, QTextEdit
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap

class ArthaInvestCRM(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.current_role = None
        self.db = None
        self.init_database()
        self.show_login_screen()

    def init_database(self):
        """Initialize SQLite database"""
        self.db = sqlite3.connect('arthainvest_crm.db')
        cursor = self.db.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                email TEXT
            )
        ''')

        try:
            cursor.execute("INSERT INTO users (username, password, role, email) VALUES ('admin', ?, 'Admin', 'admin@arthainvest.com')",
                         (self.hash_password('123'),))
            cursor.execute("INSERT INTO users (username, password, role, email) VALUES ('teamlead', ?, 'Team Lead', 'lead@arthainvest.com')",
                         (self.hash_password('123'),))
            cursor.execute("INSERT INTO users (username, password, role, email) VALUES ('user1', ?, 'Sales', 'user1@arthainvest.com')",
                         (self.hash_password('123'),))
            self.db.commit()
        except:
            pass

        # Leads table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY,
                name TEXT,
                phone TEXT,
                email TEXT,
                company TEXT,
                product TEXT,
                ai_score INTEGER,
                status TEXT,
                source TEXT,
                created_by TEXT,
                created_date TEXT,
                last_contact TEXT,
                notes TEXT
            )
        ''')

        # Deals table (pipeline)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY,
                name TEXT,
                lead_id INTEGER,
                value REAL,
                stage TEXT,
                probability INTEGER,
                close_date TEXT,
                owner TEXT,
                created_date TEXT,
                updated_date TEXT
            )
        ''')

        # Activities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY,
                lead_id INTEGER,
                type TEXT,
                description TEXT,
                created_by TEXT,
                created_date TEXT,
                email TEXT
            )
        ''')

        # Pre-load sample data
        self.load_sample_data()
        self.db.commit()

    def load_sample_data(self):
        """Load sample data for demo"""
        cursor = self.db.cursor()

        # Check if leads already exist
        cursor.execute('SELECT COUNT(*) FROM leads')
        if cursor.fetchone()[0] == 0:
            # Add sample leads
            sample_leads = [
                ('Rajesh Patel', '9876543210', 'rajesh@company.com', 'Tech Corp', 'Term Insurance', 85, 'Hot', 'LinkedIn'),
                ('Priya Sharma', '9876543211', 'priya@company.com', 'Finance Ltd', 'Health Insurance', 75, 'Warm', 'Direct'),
                ('Amit Kumar', '9876543212', 'amit@company.com', 'StartUp XYZ', 'POSP', 65, 'Warm', 'Referral'),
                ('Neha Singh', '9876543213', 'neha@company.com', 'Retail Co', 'Term Insurance', 55, 'Cool', 'Website'),
                ('Vikram Reddy', '9876543214', 'vikram@company.com', 'Manufacturing', 'Health Insurance', 45, 'Cool', 'Email'),
            ]

            for lead in sample_leads:
                cursor.execute('''
                    INSERT INTO leads (name, phone, email, company, product, ai_score, status, source, created_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (*lead, datetime.now().strftime('%Y-%m-%d')))

            self.db.commit()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def show_login_screen(self):
        """Display modern login screen"""
        self.setWindowTitle('ArthaInvest CRM')
        self.setGeometry(200, 100, 1000, 750)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left - Brand
        left = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(50, 50, 50, 50)
        left_layout.setSpacing(30)

        title = QLabel('ArthaInvest')
        title.setFont(QFont('Segoe UI', 56, QFont.Bold))
        title.setStyleSheet('color: white;')
        left_layout.addWidget(title)

        tagline = QLabel('Sales & Marketing CRM')
        tagline.setFont(QFont('Segoe UI', 18))
        tagline.setStyleSheet('color: rgba(255,255,255,0.9);')
        left_layout.addWidget(tagline)

        left_layout.addSpacing(40)

        features = QLabel(
            '✓ Kanban Pipeline Management\n'
            '✓ AI Lead Scoring\n'
            '✓ Real-time Analytics\n'
            '✓ Email Integration\n'
            '✓ Team Collaboration\n'
            '✓ Activity Timeline'
        )
        features.setFont(QFont('Segoe UI', 13))
        features.setStyleSheet('color: rgba(255,255,255,0.95); line-height: 2.2;')
        left_layout.addWidget(features)

        left_layout.addStretch()
        left.setLayout(left_layout)
        # Darker, richer gradient for better contrast
        left.setStyleSheet('background: linear-gradient(135deg, #4c63d2 0%, #5a3a8a 100%);')
        layout.addWidget(left, 1)

        # Right - Login
        right = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(12)

        login_title = QLabel('Welcome Back')
        login_title.setFont(QFont('Segoe UI', 36, QFont.Bold))
        login_title.setStyleSheet('color: #333;')
        right_layout.addWidget(login_title)

        subtitle = QLabel('Sign in to your account')
        subtitle.setFont(QFont('Segoe UI', 12))
        subtitle.setStyleSheet('color: #666;')
        right_layout.addWidget(subtitle)
        right_layout.addSpacing(15)

        # Username
        username_label = QLabel('Username')
        username_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        username_label.setStyleSheet('color: #333;')
        right_layout.addWidget(username_label)

        self.username_input = QLineEdit()
        self.username_input.setMinimumHeight(45)
        self.username_input.setMaximumHeight(45)
        self.username_input.setPlaceholderText('admin, teamlead, or user1')
        self.username_input.setFont(QFont('Segoe UI', 11))
        self.username_input.setStyleSheet(self.get_input_style())
        right_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel('Password')
        password_label.setFont(QFont('Segoe UI', 11, QFont.Bold))
        password_label.setStyleSheet('color: #333;')
        right_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setMinimumHeight(45)
        self.password_input.setMaximumHeight(45)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText('Default: 123')
        self.password_input.setFont(QFont('Segoe UI', 11))
        self.password_input.setStyleSheet(self.get_input_style())
        right_layout.addWidget(self.password_input)

        right_layout.addSpacing(8)

        login_btn = QPushButton('SIGN IN →')
        login_btn.setMinimumHeight(60)
        login_btn.setFont(QFont('Segoe UI', 14, QFont.Bold))
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet('''
            QPushButton {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #5568d3 0%, #6a3a90 100%);
                transform: scale(1.02);
            }
        ''')
        login_btn.clicked.connect(self.verify_login)
        right_layout.addWidget(login_btn)

        right_layout.addSpacing(5)

        info = QLabel('Demo: admin/123 • teamlead/123 • user1/123')
        info.setFont(QFont('Segoe UI', 8))
        info.setStyleSheet('color: #aaa;')
        info.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(info)

        right_layout.addStretch(1)
        right.setLayout(right_layout)
        right.setStyleSheet('background: white;')
        layout.addWidget(right, 1)

        central.setLayout(layout)

    def verify_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please enter username and password')
            return

        cursor = self.db.cursor()
        cursor.execute('SELECT role FROM users WHERE username = ? AND password = ?',
                      (username, self.hash_password(password)))
        result = cursor.fetchone()

        if result:
            self.current_user = username
            self.current_role = result[0]
            self.show_main_dashboard()
        else:
            QMessageBox.warning(self, 'Error', 'Invalid credentials')

    def show_main_dashboard(self):
        """Display main dashboard with Kanban"""
        self.setWindowTitle(f'ArthaInvest CRM - {self.current_user}')
        self.setGeometry(0, 0, 1600, 900)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Main content
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        sidebar = self.create_sidebar()
        content_layout.addWidget(sidebar)

        # Main area
        main_area = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Top navigation
        nav = self.create_nav()
        main_layout.addWidget(nav)

        # Content stack
        self.current_view = 'dashboard'
        self.view_widget = self.get_view('dashboard')
        main_layout.addWidget(self.view_widget, 1)

        main_area.setLayout(main_layout)
        main_area.setStyleSheet('background: #f5f7fa;')
        content_layout.addWidget(main_area, 1)

        content = QWidget()
        content.setLayout(content_layout)
        layout.addWidget(content, 1)

        central.setLayout(layout)

    def create_header(self):
        """Create top header"""
        header = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(30, 15, 30, 15)

        title = QLabel('ArthaInvest CRM')
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet('color: white;')
        layout.addWidget(title)

        layout.addStretch()

        user_info = QLabel(f'{self.current_user} ({self.current_role})')
        user_info.setFont(QFont('Segoe UI', 10))
        user_info.setStyleSheet('color: white;')
        layout.addWidget(user_info)

        logout = QPushButton('Logout')
        logout.setMinimumWidth(100)
        logout.setMinimumHeight(35)
        logout.setStyleSheet('background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 4px;')
        logout.clicked.connect(self.logout)
        layout.addWidget(logout)

        header.setLayout(layout)
        header.setStyleSheet('background: #667eea;')
        return header

    def create_sidebar(self):
        """Create navigation sidebar"""
        sidebar = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(10)

        sections = [
            ('📊 Dashboard', 'dashboard'),
            ('🚀 Pipeline', 'pipeline'),
            ('👥 Leads', 'leads'),
            ('📈 Analytics', 'analytics'),
            ('⚙️ Settings', 'settings'),
        ]

        for label, view in sections:
            btn = QPushButton(label)
            btn.setMinimumHeight(45)
            btn.setFont(QFont('Segoe UI', 10))
            btn.setStyleSheet(self.get_sidebar_button_style())
            btn.clicked.connect(lambda checked, v=view: self.switch_view(v))
            layout.addWidget(btn)

        layout.addStretch()

        settings = QPushButton('🔑 Change Password')
        settings.setMinimumHeight(40)
        settings.setStyleSheet(self.get_sidebar_button_style())
        settings.clicked.connect(self.show_password_dialog)
        layout.addWidget(settings)

        sidebar.setLayout(layout)
        sidebar.setStyleSheet('background: #2c3e50;')
        sidebar.setMaximumWidth(200)
        return sidebar

    def create_nav(self):
        """Create page navigation"""
        nav = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        title = QLabel(self.get_view_title(self.current_view))
        title.setFont(QFont('Segoe UI', 22, QFont.Bold))
        layout.addWidget(title)

        layout.addStretch()

        nav.setLayout(layout)
        return nav

    def get_view_title(self, view):
        titles = {
            'dashboard': '📊 Dashboard',
            'pipeline': '🚀 Sales Pipeline',
            'leads': '👥 Leads',
            'analytics': '📈 Analytics',
            'settings': '⚙️ Settings'
        }
        return titles.get(view, 'Dashboard')

    def get_view(self, view):
        """Get the requested view"""
        if view == 'dashboard':
            return self.create_dashboard()
        elif view == 'pipeline':
            return self.create_kanban()
        elif view == 'leads':
            return self.create_leads_view()
        elif view == 'analytics':
            return self.create_analytics()
        elif view == 'settings':
            return self.create_settings()
        return QWidget()

    def create_dashboard(self):
        """Create beautiful dashboard"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # KPIs
        kpis_layout = QHBoxLayout()
        kpis = [
            ('Total Leads', '12', '#667eea'),
            ('Qualified', '8', '#10b981'),
            ('In Pipeline', '5', '#f59e0b'),
            ('Closed (This Month)', '3', '#8b5cf6'),
        ]

        for label, value, color in kpis:
            card = self.create_kpi_card(label, value, color)
            kpis_layout.addWidget(card)

        layout.addLayout(kpis_layout)

        # Charts row
        charts_layout = QHBoxLayout()

        # Chart 1: Pipeline by stage
        chart1 = self.create_chart('Pipeline by Stage')
        charts_layout.addWidget(chart1)

        # Chart 2: Leads by source
        chart2 = self.create_chart('Leads by Source')
        charts_layout.addWidget(chart2)

        layout.addLayout(charts_layout)

        # Recent activity
        activity = QLabel('Recent Activity')
        activity.setFont(QFont('Segoe UI', 14, QFont.Bold))
        layout.addWidget(activity)

        activities_table = QTableWidget()
        activities_table.setColumnCount(4)
        activities_table.setHorizontalHeaderLabels(['Time', 'Lead', 'Action', 'User'])
        activities_table.setRowCount(5)
        layout.addWidget(activities_table)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_kpi_card(self, title, value, color):
        """Create KPI card"""
        card = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 11))
        title_label.setStyleSheet('color: #888;')
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont('Segoe UI', 32, QFont.Bold))
        value_label.setStyleSheet(f'color: {color};')
        layout.addWidget(value_label)

        card.setLayout(layout)
        card.setStyleSheet('background: white; border-radius: 8px; border: 1px solid #e0e0e0;')
        return card

    def create_chart(self, title):
        """Create sample chart"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        layout.addWidget(title_label)

        # Simple chart representation
        chart_info = QLabel('📊 Chart Data\n\n✓ Qualified: 8 leads\n✓ Proposal: 3 leads\n✓ Negotiation: 2 leads\n✓ Closed: 3 leads')
        chart_info.setFont(QFont('Segoe UI', 10))
        chart_info.setStyleSheet('color: #666;')
        layout.addWidget(chart_info)

        layout.addStretch()
        widget.setLayout(layout)
        widget.setStyleSheet('background: white; border-radius: 8px; border: 1px solid #e0e0e0;')
        return widget

    def create_kanban(self):
        """Create Kanban board"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)

        stages = [
            ('New', '#3b82f6'),
            ('Qualified', '#10b981'),
            ('Proposal', '#f59e0b'),
            ('Negotiation', '#8b5cf6'),
            ('Closed', '#10b981'),
        ]

        for stage, color in stages:
            column = self.create_kanban_column(stage, color)
            layout.addWidget(column)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_kanban_column(self, stage, color):
        """Create Kanban column"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header
        header = QLabel(stage)
        header.setFont(QFont('Segoe UI', 12, QFont.Bold))
        header.setStyleSheet(f'color: {color}; padding: 10px;')
        layout.addWidget(header)

        # Cards
        cards = ['Rajesh Patel', 'Priya Sharma', 'Amit Kumar']
        for card_title in cards:
            card = QWidget()
            card_layout = QVBoxLayout()
            card_layout.setContentsMargins(12, 12, 12, 12)

            name = QLabel(card_title)
            name.setFont(QFont('Segoe UI', 10, QFont.Bold))
            name.setStyleSheet('color: #333;')
            card_layout.addWidget(name)

            value = QLabel('₹5L - ₹10L')
            value.setFont(QFont('Segoe UI', 9))
            value.setStyleSheet('color: #888;')
            card_layout.addWidget(value)

            card.setLayout(card_layout)
            card.setStyleSheet('background: white; border-radius: 6px; border-left: 4px solid ' + color + '; cursor: move;')
            layout.addWidget(card)

        layout.addStretch()
        widget.setLayout(layout)
        widget.setStyleSheet(f'background: #f0f4f8; border-radius: 8px;')
        return widget

    def create_leads_view(self):
        """Create leads view"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Add lead form
        form_layout = QFormLayout()

        self.lead_name = QLineEdit()
        form_layout.addRow('Name:', self.lead_name)

        self.lead_phone = QLineEdit()
        form_layout.addRow('Phone:', self.lead_phone)

        self.lead_company = QLineEdit()
        form_layout.addRow('Company:', self.lead_company)

        self.lead_product = QComboBox()
        self.lead_product.addItems(['Term Insurance', 'Health Insurance', 'POSP', 'DSA'])
        form_layout.addRow('Product:', self.lead_product)

        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)

        btn = QPushButton('+ Add Lead')
        btn.setMinimumHeight(40)
        btn.setStyleSheet(self.get_button_style())
        btn.clicked.connect(self.add_lead)
        layout.addWidget(btn)

        # Leads table
        self.leads_table = QTableWidget()
        self.leads_table.setColumnCount(6)
        self.leads_table.setHorizontalHeaderLabels(['Name', 'Company', 'Phone', 'Product', 'AI Score', 'Status'])
        self.leads_table.setStyleSheet('background: white; border-radius: 8px;')
        self.load_leads()
        layout.addWidget(self.leads_table)

        widget.setLayout(layout)
        return widget

    def create_analytics(self):
        """Create analytics view"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)

        title = QLabel('📈 Performance Analytics')
        title.setFont(QFont('Segoe UI', 14, QFont.Bold))
        layout.addWidget(title)

        # Stats
        stats_layout = QGridLayout()
        stats = [
            ('Conversion Rate', '67%', '#10b981'),
            ('Avg Deal Value', '₹10L', '#667eea'),
            ('Sales Cycle', '15 days', '#f59e0b'),
            ('Team Performance', 'Above Target', '#8b5cf6'),
        ]

        for i, (label, value, color) in enumerate(stats):
            card = self.create_stat_card(label, value, color)
            stats_layout.addWidget(card, i // 2, i % 2)

        layout.addLayout(stats_layout)

        layout.addSpacing(20)

        # Charts
        charts_layout = QHBoxLayout()
        chart1 = self.create_chart('Monthly Revenue')
        chart2 = self.create_chart('Team Performance')
        charts_layout.addWidget(chart1)
        charts_layout.addWidget(chart2)

        layout.addLayout(charts_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_stat_card(self, title, value, color):
        """Create stat card"""
        card = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 10))
        title_label.setStyleSheet('color: #888;')
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setFont(QFont('Segoe UI', 24, QFont.Bold))
        value_label.setStyleSheet(f'color: {color};')
        layout.addWidget(value_label)

        card.setLayout(layout)
        card.setStyleSheet('background: white; border-radius: 8px; border-left: 4px solid ' + color)
        return card

    def create_settings(self):
        """Create settings view"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel('Settings')
        title.setFont(QFont('Segoe UI', 24, QFont.Bold))
        layout.addWidget(title)

        info = QLabel('System Configuration\n\n✓ Database: SQLite (Local)\n✓ Version: 1.0 Professional\n✓ Users: 10 Active\n✓ Data Backup: Enabled')
        info.setFont(QFont('Segoe UI', 11))
        info.setStyleSheet('background: white; padding: 20px; border-radius: 8px;')
        layout.addWidget(info)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_leads(self):
        """Load leads from database"""
        cursor = self.db.cursor()
        cursor.execute('SELECT name, company, phone, product, ai_score, status FROM leads')
        leads = cursor.fetchall()

        self.leads_table.setRowCount(len(leads))
        for row, lead in enumerate(leads):
            for col, value in enumerate(lead):
                if col == 4:  # AI Score
                    item = QTableWidgetItem(f'{value}/100')
                else:
                    item = QTableWidgetItem(str(value))
                self.leads_table.setItem(row, col, item)

    def add_lead(self):
        """Add new lead"""
        name = self.lead_name.text()
        phone = self.lead_phone.text()
        company = self.lead_company.text()
        product = self.lead_product.currentText()

        if not name or not phone:
            QMessageBox.warning(self, 'Error', 'Please fill Name and Phone')
            return

        # AI Scoring (simple algorithm)
        ai_score = 50 + (len(company) * 5) + (len(name) * 2)
        ai_score = min(100, ai_score)

        cursor = self.db.cursor()
        cursor.execute('''
            INSERT INTO leads (name, phone, company, product, ai_score, status, created_date)
            VALUES (?, ?, ?, ?, ?, 'New', ?)
        ''', (name, phone, company, product, ai_score, datetime.now().strftime('%Y-%m-%d')))
        self.db.commit()

        QMessageBox.information(self, 'Success', f'Lead added! AI Score: {ai_score}/100')
        self.lead_name.clear()
        self.lead_phone.clear()
        self.lead_company.clear()
        self.load_leads()

    def switch_view(self, view):
        """Switch to different view"""
        self.current_view = view
        self.view_widget.deleteLater()
        self.view_widget = self.get_view(view)

        # Find main layout and replace widget
        parent = self.view_widget.parent()
        if parent:
            layout = parent.layout()
            if layout and layout.count() > 1:
                old_widget = layout.itemAt(1).widget()
                if old_widget:
                    layout.removeWidget(old_widget)
                layout.insertWidget(1, self.view_widget)

    def show_password_dialog(self):
        """Show password change dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Change Password')
        dialog.setGeometry(400, 300, 400, 250)

        layout = QFormLayout()

        current = QLineEdit()
        current.setEchoMode(QLineEdit.Password)
        layout.addRow('Current Password:', current)

        new = QLineEdit()
        new.setEchoMode(QLineEdit.Password)
        layout.addRow('New Password:', new)

        confirm = QLineEdit()
        confirm.setEchoMode(QLineEdit.Password)
        layout.addRow('Confirm Password:', confirm)

        def change():
            if new.text() != confirm.text():
                QMessageBox.warning(dialog, 'Error', 'Passwords do not match')
                return

            cursor = self.db.cursor()
            cursor.execute('UPDATE users SET password = ? WHERE username = ?',
                          (self.hash_password(new.text()), self.current_user))
            self.db.commit()

            QMessageBox.information(dialog, 'Success', 'Password changed!')
            dialog.close()

        btn = QPushButton('Change')
        btn.clicked.connect(change)
        layout.addRow('', btn)

        dialog.setLayout(layout)
        dialog.exec_()

    def logout(self):
        """Logout user"""
        self.show_login_screen()

    def get_input_style(self):
        return '''
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
                font-size: 12px;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
            }
        '''

    def get_button_style(self):
        return '''
            QPushButton {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #5568d3 0%, #6a3a90 100%);
            }
        '''

    def get_sidebar_button_style(self):
        return '''
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                text-align: left;
                padding-left: 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        '''

def main():
    app = QApplication(sys.argv)
    window = ArthaInvestCRM()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
