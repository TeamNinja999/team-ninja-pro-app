const { app, BrowserWindow, ipcMain, shell, dialog, Menu } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { autoUpdater } = require('electron-updater');

let mainWindow;
let pyProc;

function createWindow(iconPath) {
  mainWindow = new BrowserWindow({
    title: 'YTDownloader',
    width: 1200, height: 800, minWidth: 1000, minHeight: 700,
    frame: false, backgroundColor: '#1b2838',
    icon: iconPath,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true, nodeIntegration: false,
      autoplayPolicy: "no-user-gesture-required"
    }
  });
  
  Menu.setApplicationMenu(null);

  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'));
  }
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
  const isDev = !app.isPackaged;
  
  // Determine the correct paths for production vs development
  const pyPath = isDev ? path.join(__dirname, 'backend', 'app.py') : path.join(process.resourcesPath, 'backend.exe');
  const appRoot = isDev ? __dirname : path.join(process.resourcesPath, 'app.asar.unpacked');
  
  // Open a log file to capture Python errors in production
  const logFile = fs.openSync(path.join(app.getPath('userData'), 'backend.log'), 'w');
  
  // Spawn Python, passing appRoot as an argument so it finds config.json
  pyProc = isDev ? spawn('python', [pyPath, appRoot]) : spawn(pyPath, [appRoot], { stdio: ['ignore', logFile, logFile] });
  
  let initialIcon = undefined;
  const configPath = path.join(appRoot, 'config.json');
  if (fs.existsSync(configPath)) {
    try {
      const configData = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      if (configData.appIcon) {
        const iconFullPath = path.join(appRoot, configData.appIcon);
        if (fs.existsSync(iconFullPath)) {
          initialIcon = iconFullPath;
        }
      }
    } catch (e) { console.error("Error reading config for icon:", e); }
  }
  
  createWindow(initialIcon);

  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  if (pyProc) pyProc.kill();
  app.quit();
});