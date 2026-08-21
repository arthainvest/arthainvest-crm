const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Database operations
  saveContact: (contact) => ipcRenderer.invoke('db:saveContact', contact),
  getContacts: () => ipcRenderer.invoke('db:getContacts'),
  deleteContact: (id) => ipcRenderer.invoke('db:deleteContact', id),

  // System operations
  getAppPath: () => ipcRenderer.invoke('app:getPath'),
  getVersion: () => ipcRenderer.invoke('app:getVersion'),

  // Listen for events
  onOnline: (callback) => ipcRenderer.on('app:online', callback),
  onOffline: (callback) => ipcRenderer.on('app:offline', callback),
  onSync: (callback) => ipcRenderer.on('app:sync', callback),

  // Platform info
  platform: process.platform,
  isElectron: true
});

// Log that preload is loaded
console.log('Preload script loaded');
