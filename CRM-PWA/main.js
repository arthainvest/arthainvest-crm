const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const sqlite3 = require('sqlite3').verbose();

let mainWindow;
let db;

// Create or connect to SQLite database
function initializeDatabase() {
  const dbPath = path.join(app.getPath('userData'), 'arthainvest-crm.db');
  db = new sqlite3.Database(dbPath, (err) => {
    if (err) console.error('Database connection error:', err);
    else console.log('Connected to SQLite database');
    initializeTables();
  });
}

function initializeTables() {
  const tables = [
    `CREATE TABLE IF NOT EXISTS contacts (
      id TEXT PRIMARY KEY,
      name TEXT,
      email TEXT UNIQUE,
      phone TEXT,
      company TEXT,
      status TEXT,
      createdAt DATETIME,
      syncedAt DATETIME
    )`,
    `CREATE TABLE IF NOT EXISTS pipeline (
      id TEXT PRIMARY KEY,
      client TEXT,
      amount REAL,
      status TEXT,
      login INTEGER,
      sanction INTEGER,
      disbursed INTEGER,
      createdAt DATETIME,
      syncedAt DATETIME
    )`,
    `CREATE TABLE IF NOT EXISTS calls (
      id TEXT PRIMARY KEY,
      clientId TEXT,
      phone TEXT,
      followUpStatus TEXT,
      timestamp DATETIME,
      syncedAt DATETIME
    )`,
    `CREATE TABLE IF NOT EXISTS team (
      id TEXT PRIMARY KEY,
      name TEXT,
      role TEXT,
      phone TEXT,
      email TEXT UNIQUE,
      leads INTEGER,
      closed INTEGER,
      revenue REAL,
      createdAt DATETIME,
      syncedAt DATETIME
    )`,
    `CREATE TABLE IF NOT EXISTS documents (
      id TEXT PRIMARY KEY,
      clientId TEXT,
      type TEXT,
      status TEXT,
      uploadedAt DATETIME,
      syncedAt DATETIME
    )`,
    `CREATE TABLE IF NOT EXISTS syncQueue (
      id TEXT PRIMARY KEY,
      storeName TEXT,
      operation TEXT,
      data TEXT,
      timestamp DATETIME,
      synced INTEGER DEFAULT 0,
      retries INTEGER DEFAULT 0
    )`,
    `CREATE TABLE IF NOT EXISTS credentials (
      key TEXT PRIMARY KEY,
      label TEXT,
      field TEXT,
      value TEXT
    )`,
    `CREATE TABLE IF NOT EXISTS userSettings (
      userId TEXT PRIMARY KEY,
      role TEXT,
      preferences TEXT
    )`
  ];

  tables.forEach(sql => {
    db.run(sql, (err) => {
      if (err) console.error('Table creation error:', err);
    });
  });
}

// Create application window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false
    },
    icon: path.join(__dirname, 'icon.png')
  });

  const startUrl = isDev
    ? 'http://localhost:3000'
    : `file://${path.join(__dirname, 'index.html')}`;

  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC handlers for database operations
ipcMain.handle('db:saveContact', async (event, contact) => {
  return new Promise((resolve, reject) => {
    db.run(
      `INSERT OR REPLACE INTO contacts (id, name, email, phone, company, status, createdAt, syncedAt)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [contact.id, contact.name, contact.email, contact.phone, contact.company, contact.status, new Date(), new Date()],
      (err) => {
        if (err) reject(err);
        else resolve(contact);
      }
    );
  });
});

ipcMain.handle('db:getContacts', async (event) => {
  return new Promise((resolve, reject) => {
    db.all('SELECT * FROM contacts', (err, rows) => {
      if (err) reject(err);
      else resolve(rows || []);
    });
  });
});

ipcMain.handle('db:deleteContact', async (event, id) => {
  return new Promise((resolve, reject) => {
    db.run('DELETE FROM contacts WHERE id = ?', [id], (err) => {
      if (err) reject(err);
      else resolve(id);
    });
  });
});

// Menu
function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Exit',
          accelerator: 'CmdOrCtrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' }
      ]
    },
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About ArthaInvest CRM',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About ArthaInvest CRM',
              message: 'ArthaInvest CRM Pro v1.0.0',
              detail: 'Enterprise Fintech Platform with Offline Support'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// App event handlers
app.on('ready', () => {
  initializeDatabase();
  createWindow();
  createMenu();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
  if (db) {
    db.close();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  dialog.showErrorBox('Error', 'An unexpected error occurred');
});
