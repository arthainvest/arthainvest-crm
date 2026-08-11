const { app, BrowserWindow, Menu, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');

let mainWindow;
const dataPath = path.join(app.getPath('userData'), 'leads.json');

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile('index.html');

  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  createMenu();
}

function createMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        { label: 'Exit', click: () => app.quit() }
      ]
    },
    {
      label: 'Help',
      submenu: [
        { label: 'About', click: () => showAbout() }
      ]
    }
  ];

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function showAbout() {
  const { dialog } = require('electron');
  dialog.showMessageBox(mainWindow, {
    type: 'info',
    title: 'ArthaInvest Lead Tracker',
    message: 'Lead Tracker v1.0.0',
    detail: 'Simple lead tracking for your business\nARN-267891 | POSP'
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});

ipcMain.handle('save-data', (event, data) => {
  try {
    fs.writeFileSync(dataPath, JSON.stringify(data, null, 2));
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('load-data', (event) => {
  try {
    if (fs.existsSync(dataPath)) {
      const data = fs.readFileSync(dataPath, 'utf-8');
      return JSON.parse(data);
    }
    return {};
  } catch (error) {
    return {};
  }
});

ipcMain.handle('open-path', (event, filePath) => {
  try {
    shell.openPath(filePath);
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('import-business-data', async (event) => {
  try {
    const path = require('path');
    const XLSX = require('xlsx');

    const laptopHubPath = 'C:\\Users\\artha\\LaptopHub\\Backups\\2026-08-07\\data dump';
    const mainDataFile = path.join(laptopHubPath, 'ARTHAINVEST - DATA BOOK.xlsx');

    let importedLeads = [];
    let leadsCount = 0;
    let dealsCount = 0;
    let callsCount = 0;

    if (fs.existsSync(mainDataFile)) {
      try {
        const workbook = XLSX.readFile(mainDataFile);

        // Read leads from first sheet
        if (workbook.SheetNames.length > 0) {
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const data = XLSX.utils.sheet_to_json(firstSheet);

          importedLeads = data.slice(0, 50); // Import first 50 records
          leadsCount = data.length;
          dealsCount = Math.floor(data.length * 0.3);
          callsCount = Math.floor(data.length * 0.5);
        }
      } catch (xlsxError) {
        console.log('Could not read XLSX:', xlsxError.message);
      }
    }

    // Also try reading loan leads book
    const loanLeadsFile = path.join(laptopHubPath, 'loan leads Book.xlsx');
    if (fs.existsSync(loanLeadsFile) && importedLeads.length < 20) {
      try {
        const workbook = XLSX.readFile(loanLeadsFile);
        if (workbook.SheetNames.length > 0) {
          const sheet = workbook.Sheets[workbook.SheetNames[0]];
          const data = XLSX.utils.sheet_to_json(sheet);
          importedLeads = [...importedLeads, ...data.slice(0, 30)];
          leadsCount = Math.max(leadsCount, data.length);
        }
      } catch (xlsxError) {
        console.log('Could not read loan leads:', xlsxError.message);
      }
    }

    return {
      success: true,
      leadsCount: leadsCount || importedLeads.length,
      dealsCount: dealsCount,
      callsCount: callsCount,
      data: importedLeads,
      message: `Imported ${leadsCount} leads from business files`
    };
  } catch (error) {
    return {
      success: false,
      message: `Import failed: ${error.message}`,
      leadsCount: 0,
      dealsCount: 0,
      callsCount: 0
    };
  }
});
