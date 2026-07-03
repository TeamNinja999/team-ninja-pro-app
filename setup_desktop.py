import os
import subprocess
import sys

print("Setting up the Team Ninja Desktop App (Electron + React)...")

# Create folder structure
folders = [
    "backend",
    "frontend/src/components",
    "frontend/public",
    "build/assets"
]
for f in folders:
    os.makedirs(f, exist_ok=True)

files = {
    # --- ROOT ELECTRON CONFIG ---
    "package.json": r'''{
  "name": "team-ninja-desktop",
  "version": "1.0.0",
  "description": "Professional YouTube Downloader",
  "main": "main.js",
  "scripts": {
    "dev": "concurrently \"npm run react:dev\" \"npm run electron:dev\"",
    "react:dev": "vite",
    "electron:dev": "wait-on http://localhost:5173 && cross-env NODE_ENV=development electron .",
    "build": "vite build && electron-builder",
    "build:win": "vite build && electron-builder --win"
  },
  "build": {
    "appId": "com.teamninja.ytdownloader",
    "productName": "Team Ninja Pro",
    "files": ["main.js", "preload.js", "build/**/*", "backend/**/*"],
    "extraResources": [],
    "win": {
      "target": "nsis",
      "icon": "icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  },
  "devDependencies": {
    "electron": "^31.0.0",
    "electron-builder": "^24.13.3",
    "vite": "^5.3.1",
    "@vitejs/plugin-react": "^4.3.1",
    "tailwindcss": "^3.4.4",
    "postcss": "^8.4.38",
    "autoprefixer": "^10.4.19",
    "concurrently": "^8.2.2",
    "wait-on": "^7.2.0",
    "cross-env": "^7.0.3"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  }
}
''',

    # Electron Main Process (Creates the window, hides console)
    "main.js": r'''const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pyProc;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1000,
    minHeight: 700,
    frame: false, // Removes default Windows border (Steam style)
    backgroundColor: '#1b2838',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // Load React dev server or production build
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, 'build', 'index.html'));
  }
}

// Window Controls (Minimize, Maximize, Close)
ipcMain.on('window:minimize', () => mainWindow.minimize());
ipcMain.on('window:maximize', () => {
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  else mainWindow.maximize();
});
ipcMain.on('window:close', () => {
  if (pyProc) pyProc.kill();
  app.quit();
});

app.whenReady().then(() => {
  // Start Python Backend silently
  const pyPath = path.join(__dirname, 'backend', 'app.py');
  pyProc = spawn('python', [pyPath], { stdio: 'ignore' });
  
  createWindow();
});

app.on('window-all-closed', () => {
  if (pyProc) pyProc.kill();
  app.quit();
});
''',

    # Preload (Allows React to talk to Electron for window controls)
    "preload.js": r'''const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close')
});
''',

    # --- BACKEND (PYTHON) ---
    "backend/app.py": r'''"""
Team Ninja Pro - Backend API
"""
import os
import re
import uuid
import json
import threading
import time
import logging
import shutil
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
import yt_dlp
import imageio_ffmpeg

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# In production, downloads go to user's temp folder. For dev, local folder.
DOWNLOAD_DIR = os.path.join(os.environ.get('TEMP', BASE_DIR), 'TeamNinjaDownloads')
HISTORY_FILE = os.path.join(DOWNLOAD_DIR, 'history.json')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
JOBS = {}
JOBS_LOCK = threading.Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=4)

YOUTUBE_URL_RE = re.compile(r'^(https?://)?(www\.|m\.)?(youtube\.com/(watch\?v=|shorts/|embed/)|youtu\.be/)', re.IGNORECASE)
HEIGHT_LABELS = {144: '144p', 240: '240p', 360: '360p', 480: '480p', 720: '720p (HD)', 1080: '1080p (Full HD)', 1440: '1440p (2K)', 2160: '2160p (4K)'}

def is_valid_youtube_url(url): return bool(YOUTUBE_URL_RE.match(url))
def update_job(job_id, **kwargs):
    with JOBS_LOCK:
        if job_id in JOBS: JOBS[job_id].update(kwargs)

@app.route('/api/info', methods=['POST'])
def get_info():
    data = request.get_json(silent=True) or {}
    url = (data.get('url') or '').strip()
    if not url or not is_valid_youtube_url(url): return jsonify({'error': 'Invalid URL'}), 400
    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True, 'skip_download': True, 'ffmpeg_location': FFMPEG_PATH}) as ydl:
            info = ydl.extract_info(url, download=False)
        formats_dict = {}
        for f in info.get('formats', []):
            if f.get('vcodec') and f.get('vcodec') != 'none' and f.get('height'):
                h, fps = f['height'], (f.get('fps') or 0)
                formats_dict[(h, 60 if fps > 50 else 30)] = True
        qualities = [{'value': f"{h}_{'60' if fps==60 else '30'}", 'label': f"{h}p60" if fps==60 and h>=720 else HEIGHT_LABELS.get(h, f'{h}p')} for (h, fps) in sorted(formats_dict.keys(), key=lambda x: (x[0], x[1]), reverse=True)]
        thumb = info.get('thumbnail')
        for t in info.get('thumbnails', []):
            if t.get('preference', 0) >= 10: thumb = t.get('url'); break
        return jsonify({'title': info.get('title', 'Unknown'), 'thumbnail': thumb, 'duration': info.get('duration'), 'uploader': info.get('uploader', 'Unknown'), 'qualities': qualities})
    except Exception as e: return jsonify({'error': str(e)}), 400

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.get_json(silent=True) or {}
    job_id = uuid.uuid4().hex[:12]
    with JOBS_LOCK:
        JOBS[job_id] = {'job_id': job_id, 'status': 'queued', 'progress': 0, 'speed': '-', 'eta': '-', 'title': data.get('title', 'Video'), 'mode': data.get('mode')}
    threading.Thread(target=run_download, args=(job_id, data), daemon=True).start()
    return jsonify({'job_id': job_id})

def run_download(job_id, data):
    try:
        url, mode = data.get('url'), data.get('mode')
        update_job(job_id, status='downloading', progress=0)
        out_template = os.path.join(DOWNLOAD_DIR, f'{job_id}.%(ext)s')
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                got = d.get('downloaded_bytes', 0)
                pct = (got / total * 100) if total > 0 else 0
                speed = d.get('speed')
                eta = d.get('eta')
                update_job(job_id, progress=round(pct, 1), speed=f'{speed/1048576:.2f} MB/s' if speed else '-', eta=f"{eta//60}m {eta%60}s" if eta else '-')
            elif d['status'] == 'finished':
                update_job(job_id, progress=99)

        if mode == 'video':
            parts = str(data.get('height')).split('_')
            h = int(parts[0]); fps = int(parts[1]) if len(parts)>1 else 30
            fmt = f'bestvideo[height<={h}]{"[fps>=50]" if fps==60 else ""}[ext=mp4]+bestaudio[ext=m4a]/best[height<={h}]/best'
            opts = {'format': fmt, 'outtmpl': out_template, 'merge_output_format': 'mp4', 'ffmpeg_location': FFMPEG_PATH, 'progress_hooks': [progress_hook], 'quiet': True}
        else:
            opts = {'format': 'bestaudio/best', 'outtmpl': out_template, 'ffmpeg_location': FFMPEG_PATH, 'progress_hooks': [progress_hook], 'quiet': True, 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': data.get('bitrate', '320')}]}

        with yt_dlp.YoutubeDL(opts) as ydl: info = ydl.extract_info(url, download=True)
        
        ext = '.mp3' if mode == 'audio' else '.mp4'
        final_file = next((os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if f.startswith(job_id) and f.endswith(ext)), None)
        if not final_file: raise Exception('File not found')

        update_job(job_id, status='completed', progress=100, file_path=final_file, filename=f"{''.join(c for c in info.get('title', 'video') if c.isalnum() or c in (' ', '-', '_')).strip()[:50]}{ext}")
        
        hist = load_history()
        hist.insert(0, {'id': job_id, 'title': info.get('title', 'Unknown'), 'date': time.strftime('%Y-%m-%d %H:%M'), 'size': f"{os.path.getsize(final_file)/1048576:.1f} MB"})
        save_history(hist)

    except Exception as e:
        update_job(job_id, status='error', error=str(e))

@app.route('/api/progress')
def get_progress():
    with JOBS_LOCK: return jsonify(list(JOBS.values()))

@app.route('/api/history')
def get_history(): return jsonify(load_history())

@app.route('/api/file/<job_id>')
def get_file(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job or job['status'] != 'completed': abort(404)
        file_path = job['file_path']
    if not os.path.exists(file_path): abort(404)
    return send_file(file_path, as_attachment=True, download_name=job.get('filename', 'download'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
''',

    "backend/requirements.txt": r'''flask>=3.0.0
yt-dlp>=2024.8.6
imageio-ffmpeg>=0.4.9
flask-cors>=4.0.0
''',

    # --- FRONTEND (REACT + TAILWIND) ---
    "frontend/vite.config.js": r'''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { '/api': 'http://127.0.0.1:5000' }
  },
  build: {
    outDir: '../build',
    emptyOutDir: true
  }
})
''',

    "frontend/tailwind.config.js": r'''/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        steam: {
          dark: '#171a21',
          bg: '#1b2838',
          card: '#2a475e',
          hover: '#316282',
          accent: '#66c0f4',
          success: '#5ba32b',
          danger: '#d94126'
        }
      }
    },
  },
  plugins: [],
}
''',

    "frontend/postcss.config.js": r'''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',

    "frontend/index.html": r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Team Ninja Pro</title>
</head>
<body class="bg-steam-dark">
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
''',

    "frontend/src/main.jsx": r'''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',

    "frontend/src/index.css": r'''@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  font-family: 'Inter', sans-serif;
  user-select: none;
  cursor: default;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #1b2838; }
::-webkit-scrollbar-thumb { background: #2a475e; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #316282; }

.drag-region { -webkit-app-region: drag; }
.no-drag { -webkit-app-region: no-drag; }
''',

    # THE STEAM-STYLE UI COMPONENT
    "frontend/src/App.jsx": r'''import React, { useState, useEffect } from 'react'

export default function App() {
  const [url, setUrl] = useState('');
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloads, setDownloads] = useState([]);

  // Fetch active downloads every second
  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const res = await fetch('/api/progress');
        const data = await res.json();
        setDownloads(data.filter(d => d.status !== 'cancelled'));
      } catch (e) {}
    };
    const interval = setInterval(fetchProgress, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchInfo = async () => {
    if(!url) return;
    setLoading(true);
    setError('');
    setInfo(null);
    try {
      const res = await fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);
      setInfo(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startDownload = async (mode) => {
    if(!info) return;
    const height = document.getElementById('qualitySelect')?.value;
    const payload = { url, mode, title: info.title, height };
    
    await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  };

  return (
    <div className="flex h-screen bg-steam-dark text-white overflow-hidden">
      
      {/* Custom Titlebar */}
      <div className="drag-region fixed top-0 left-0 right-0 h-9 bg-steam-dark z-50 flex items-center justify-between px-2 text-xs text-gray-400 font-bold">
        <div className="flex items-center gap-2 ml-2">
          <span className="text-steam-accent">TEAM NINJA PRO</span>
        </div>
        <div className="no-drag flex items-center">
          <button onClick={() => window.electronAPI.minimize()} className="p-2 hover:bg-steam-hover w-12 text-center">—</button>
          <button onClick={() => window.electronAPI.maximize()} className="p-2 hover:bg-steam-hover w-12 text-center">▢</button>
          <button onClick={() => window.electronAPI.close()} className="p-2 hover:bg-steam-danger w-12 text-center">✕</button>
        </div>
      </div>

      {/* Sidebar */}
      <aside className="w-60 bg-steam-dark mt-9 flex flex-col justify-between border-r border-black/50">
        <div className="p-4">
          <h1 className="text-xl font-bold text-steam-accent mb-8">YT Downloader</h1>
          <nav className="flex flex-col gap-1">
            <button className="text-left p-2 rounded bg-steam-hover font-semibold text-white">Downloader</button>
            <button className="text-left p-2 rounded hover:bg-steam-hover text-gray-400">Library</button>
            <button className="text-left p-2 rounded hover:bg-steam-hover text-gray-400">Settings</button>
          </nav>
        </div>
        <div className="p-4 border-t border-black/50">
          <p className="text-xs text-gray-500">v1.0.0</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 mt-9 overflow-y-auto bg-steam-bg p-8">
        
        <div className="mb-8">
          <h2 className="text-2xl font-bold mb-4">Download a Video</h2>
          <div className="flex gap-2">
            <input 
              type="text" 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube URL here..."
              className="flex-1 bg-steam-card border border-black/30 p-3 rounded outline-none focus:ring-2 focus:ring-steam-accent text-white"
            />
            <button 
              onClick={fetchInfo}
              disabled={loading}
              className="bg-steam-accent hover:bg-blue-400 text-steam-dark px-6 py-3 rounded font-bold transition"
            >
              {loading ? 'Fetching...' : 'Fetch'}
            </button>
          </div>
          {error && <div className="bg-steam-danger/20 text-red-300 p-3 rounded mt-4">{error}</div>}
        </div>

        {/* Video Info & Download Options */}
        {info && (
          <div className="bg-steam-card p-6 rounded-lg flex gap-6 mb-8 shadow-lg">
            <img src={info.thumbnail} className="w-80 rounded shadow-md" alt="Thumbnail" />
            <div className="flex-1 flex flex-col">
              <h3 className="text-xl font-bold mb-2">{info.title}</h3>
              <p className="text-gray-400 mb-6">{info.uploader} | {info.duration}s</p>
              
              <div className="mt-auto">
                <select id="qualitySelect" className="bg-steam-dark border border-black/30 p-3 rounded w-full mb-4 outline-none">
                  {info.qualities.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                </select>
                <div className="flex gap-4">
                  <button onClick={() => startDownload('video')} className="flex-1 bg-steam-success hover:bg-green-600 text-white py-3 rounded font-bold transition">
                    Download MP4
                  </button>
                  <button onClick={() => startDownload('audio')} className="flex-1 bg-steam-hover hover:bg-blue-800 text-white py-3 rounded font-bold transition">
                    Download MP3
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Active Downloads (Steam Style) */}
        <h2 className="text-2xl font-bold mb-4">Active Downloads</h2>
        <div className="space-y-4">
          {downloads.length === 0 && <p className="text-gray-500">No active downloads.</p>}
          {downloads.map(job => (
            <div key={job.job_id} className="bg-steam-card p-4 rounded-lg shadow-md">
              <div className="flex justify-between mb-2">
                <span className="font-bold truncate">{job.title}</span>
                <span className={`text-sm font-bold ${job.status === 'error' ? 'text-red-400' : 'text-steam-accent'}`}>
                  {job.status === 'completed' ? 'Ready to Save' : job.status.toUpperCase()}
                </span>
              </div>
              <div className="w-full h-2 bg-steam-dark rounded-full overflow-hidden">
                <div 
                  className="h-full bg-steam-accent transition-all duration-300" 
                  style={{width: `${job.progress}%`}}
                ></div>
              </div>
              <div className="flex justify-between mt-2 text-xs text-gray-400">
                <span>{job.speed || '-'} | ETA: {job.eta || '-'}</span>
                {job.status === 'completed' ? (
                  <a href={`/api/file/${job.job_id}`} className="text-steam-success font-bold hover:underline">SAVE FILE</a>
                ) : (
                  <span>{Math.round(job.progress)}%</span>
                )}
              </div>
            </div>
          ))}
        </div>

      </main>
    </div>
  );
}
'''
}

# Write files
for filename, content in files.items():
    dir_name = os.path.dirname(filename)
    if dir_name: os.makedirs(dir_name, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f: f.write(content)
    print(f"Created {filename}")

print("\n⬇️  Installing Node Modules (Electron, React, Tailwind)...")
subprocess.run(["npm", "install"])

print("\n⬇️  Installing Python Backend Packages...")
os.chdir("backend")
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
os.chdir("..")

print("\n✅ Setup Complete!")
print("To run the app in dev mode: npm run dev")