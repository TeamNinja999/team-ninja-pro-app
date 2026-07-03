const { app, BrowserWindow, ipcMain, shell, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let mainWindow;
let pyProc;

function createWindow(iconPath) {
  mainWindow = new BrowserWindow({
    width: 1200, height: 800, minWidth: 1000, minHeight: 700,
    frame: false, backgroundColor: '#1b2838',
    icon: iconPath, // Apply the icon instantly on creation
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
      autoplayPolicy: "no-user-gesture-required"
    }
  });
  mainWindow.loadURL('http://localhost:5173');
}

ipcMain.on('window:minimize', () => mainWindow.minimize());
ipcMain.on('window:maximize', () => {
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  else mainWindow.maximize();
});
ipcMain.on('window:close', () => {
  if (pyProc) pyProc.kill();
  app.quit();
});

ipcMain.on('file:openLocation', (event, filePath) => {
  if (filePath) shell.showItemInFolder(filePath);
});

ipcMain.handle('file:saveAs', async (event, filePath, fileName) => {
  const result = await dialog.showSaveDialog(mainWindow, { defaultPath: fileName });
  if (result.canceled || !result.filePath) return null;
  const destPath = result.filePath;
  try {
    fs.copyFileSync(filePath, destPath);
    fs.unlinkSync(filePath);
    return destPath;
  } catch (e) { return null; }
});

ipcMain.on('app:setIcon', (event, iconPath) => {
  if (iconPath && mainWindow) {
    try {
      mainWindow.setIcon(path.join(__dirname, iconPath));
    } catch (e) { console.error("Icon error:", e); }
  }
});

app.whenReady().then(() => {
  // Start Python Backend silently
  const pyPath = path.join(__dirname, 'backend', 'app.py');
  pyProc = spawn('python', [pyPath], { stdio: 'ignore' });
  
  // Read config.json to get the custom icon BEFORE creating the window
  let initialIcon = undefined;
  const configPath = path.join(__dirname, 'config.json');
  if (fs.existsSync(configPath)) {
    try {
      const configData = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      if (configData.appIcon) {
        const iconFullPath = path.join(__dirname, configData.appIcon);
        if (fs.existsSync(iconFullPath)) {
          initialIcon = iconFullPath;
        }
      }
    } catch (e) { console.error("Error reading config for icon:", e); }
  }
  
  // Create window with the correct icon from the start
  createWindow(initialIcon);
});

app.on('window-all-closed', () => {
  if (pyProc) pyProc.kill();
  app.quit();
});