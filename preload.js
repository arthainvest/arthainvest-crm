const { contextBridge, ipcRenderer, shell } = require('electron');

contextBridge.exposeInMainWorld('leadTracker', {
  saveData: (data) => ipcRenderer.invoke('save-data', data),
  loadData: () => ipcRenderer.invoke('load-data')
});

contextBridge.exposeInMainWorld('electronAPI', {
  openPath: (filePath) => ipcRenderer.invoke('open-path', filePath),
  importBusinessData: () => ipcRenderer.invoke('import-business-data')
});
