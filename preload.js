const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
  openLocation: (filePath) => ipcRenderer.send('file:openLocation', filePath),
  saveAs: (filePath, fileName) => ipcRenderer.invoke('file:saveAs', filePath, fileName),
  setIcon: (iconPath) => ipcRenderer.send('app:setIcon', iconPath)
});