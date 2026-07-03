"""
YT Downloader - Backend API
"""
import os
import re
import uuid
import json
import sys
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

# Electron passes the app root directory as an argument when spawning backend.exe
# This ensures Python looks in the correct folder for config.json
APP_ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
BASE_DIR = APP_ROOT

# Save downloads to AppData to avoid permission issues in Program Files
DOWNLOAD_DIR = os.path.join(os.environ.get('APPDATA', BASE_DIR), 'YTDownloader')
HISTORY_FILE = os.path.join(DOWNLOAD_DIR, 'history.json')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
JOBS = {}
JOBS_LOCK = threading.Lock()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DownloadCancelled(Exception): pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: return json.load(f)
            except: return []
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
            with JOBS_LOCK:
                if job_id in JOBS and JOBS[job_id]['status'] == 'cancelled':
                    raise DownloadCancelled("Cancelled by user")
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

        with yt_dlp.YoutubeDL(opts) as ydl: 
            info = ydl.extract_info(url, download=True)
        
        ext = '.mp3' if mode == 'audio' else '.mp4'
        final_file = next((os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR) if f.startswith(job_id) and f.endswith(ext)), None)
        if not final_file: raise Exception('File not found')

        update_job(job_id, status='completed', progress=100, file_path=final_file, filename=f"{''.join(c for c in info.get('title', 'video') if c.isalnum() or c in (' ', '-', '_')).strip()[:50]}{ext}", size=f"{os.path.getsize(final_file)/1048576:.1f} MB")

    except DownloadCancelled:
        update_job(job_id, status='cancelled', error='Cancelled by user')
        for f in os.listdir(DOWNLOAD_DIR):
            if f.startswith(job_id):
                try: os.remove(os.path.join(DOWNLOAD_DIR, f))
                except: pass
    except Exception as e:
        update_job(job_id, status='error', error=str(e))

@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    with JOBS_LOCK:
        if job_id in JOBS and JOBS[job_id]['status'] in ['downloading', 'queued', 'paused']:
            JOBS[job_id]['status'] = 'cancelled'
    return jsonify({'success': True})

@app.route('/api/clear_job/<job_id>', methods=['POST'])
def clear_job(job_id):
    with JOBS_LOCK:
        if job_id in JOBS: del JOBS[job_id]
    return jsonify({"status": "success"})

@app.route('/api/progress')
def get_progress():
    with JOBS_LOCK: return jsonify(list(JOBS.values()))

@app.route('/api/get_filepath/<job_id>', methods=['GET'])
def get_filepath(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job or job['status'] != 'completed': return jsonify({'error': 'Not ready'}), 400
        return jsonify({
            'file_path': job['file_path'], 
            'filename': job['filename'], 
            'size': job.get('size', '0 MB'), 
            'mode': job.get('mode', 'video')
        })

@app.route('/api/history/add', methods=['POST'])
def add_to_history():
    data = request.get_json(silent=True) or {}
    hist = load_history()
    if not any(h.get('id') == data.get('id') for h in hist):
        hist.insert(0, data)
        save_history(hist)
    return jsonify({"status": "success"})

@app.route('/api/history')
def get_history():
    hist = load_history()
    valid_hist = [h for h in hist if 'file_path' in h and os.path.exists(h['file_path'])]
    if len(valid_hist) != len(hist):
        save_history(valid_hist)
    return jsonify(valid_hist)

@app.route('/api/file/<job_id>')
def get_file(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job or job['status'] != 'completed': abort(404)
        file_path = job['file_path']
    if not os.path.exists(file_path): abort(404)
    return send_file(file_path, as_attachment=True, download_name=job.get('filename', 'download'))

# --- CONFIG CONTROLLER ENDPOINT ---
@app.route('/api/config')
def get_config():
    # Look for config.json in the APP_ROOT passed by Electron
    config_file = os.path.join(BASE_DIR, 'config.json')
    
    default_cfg = {
        "appName": "YT Downloader", "appVersion": "Pro Edition v1.0", "titlebarText": "YT DOWNLOADER", "appIcon": "",
        "texts": {
            "downloaderTitle": "Video Downloader", "fetchBtn": "Fetch", "downloadMp4Btn": "Download MP4",
            "downloadMp3Btn": "Download MP3", "downloadsTitle": "Active Downloads", "saveFileBtn": "SAVE FILE HERE",
            "cancelBtn": "Cancel", "libraryTitle": "Download History", "settingsTitle": "Settings",
            "versionLabel": "Application Version", "settingsVersionText": "YT Downloader v1.0.0 (Pre-Alpha)",
            "closeAppBtn": "Close App", "closeAppDesc": "Force quit the application and stop all background processes.",
            "updatesTitle": "Updates", "updatesLog": "v1.0.0 - Initial Release\n- Added Customizer\n- Added Download Manager"
        },
        "icons": {
            "downloader": "bi-download", "downloads": "bi-hourglass-split", "library": "bi-folder", 
            "settings": "bi-gear", "updates": "bi-arrow-repeat", "mp4": "bi-film", 
            "mp3": "bi-music-note-beamed", "save": "bi-folder2-open", "openLocation": "bi-folder2-open"
        },
        "fonts": { "family": "Segoe UI, sans-serif", "fontWeight": "600", "strokeColor": "transparent", "strokeWidth": "0px" },
        "colors": {"sidebar": "#8b0000", "bg": "#1a1a1d", "card": "#222226", "accent": "#cd9b1d", "hover": "#a40000", "success": "#28a745", "danger": "#dc3545", "titlebar": "#000000"},
        "textures": {"background": "brushed_metal", "sidebar": "none"},
        "animations": {"pageTransition": "fade_slide"},
        "options": {"borderRadius": "12px", "cardShadow": "0 10px 20px rgba(0,0,0,0.4)", "outlineColor": "transparent", "outlineWidth": "0px", "sidebarWidth": "260px", "progressBarHeight": "12px", "showVersion": "true", "cardOpacity": "1.0", "contentPadding": "32px", "fontSize": "16px", "textAlign": "left", "titlebarOpacity": "1.0", "loadingText": "Loading..", "loadingBgColor": "#1a1a1d", "loadingTextColor": "#cd9b1d", "loadingSpinnerColor": "#cd9b1d", "loadingAnimation": "spinner", "loadingBgTexture": "none", "loadingTextSize": "24px", "loadingTextWeight": "700", "loadingSpinnerSize": "50px"}
    }
    
    if os.path.exists(config_file):
        print(f"[Config] Found config.json at: {config_file}")
        with open(config_file, 'r') as f:
            try:
                cfg = json.load(f)
                print(f"[Config] Successfully read appName: {cfg.get('appName')}")
                for key in default_cfg:
                    if key not in cfg: cfg[key] = default_cfg[key]
                    elif isinstance(default_cfg[key], dict):
                        for subkey in default_cfg[key]:
                            if subkey not in cfg[key]: cfg[key][subkey] = default_cfg[key][subkey]
                return jsonify(cfg)
            except Exception as e:
                print(f"[Config] ERROR reading JSON: {e}")
    else:
        print("[Config] WARNING: config.json not found! Using defaults.")

    return jsonify(default_cfg)

# --- ICON UPLOAD ENDPOINT ---
@app.route('/api/upload_icon', methods=['POST'])
def upload_icon():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save the uploaded icon to the APP_ROOT
    save_path = os.path.join(BASE_DIR, 'custom_icon.png')
    file.save(save_path)
    
    cfg = load_config()
    cfg['appIcon'] = 'custom_icon.png'
    save_config(cfg)
    
    return jsonify({"success": True, "icon": "custom_icon.png"})

def load_config():
    config_file = os.path.join(BASE_DIR, 'config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(cfg):
    config_file = os.path.join(BASE_DIR, 'config.json')
    with open(config_file, 'w') as f:
        json.dump(cfg, f, indent=4)

if __name__ == '__main__':
    print("Server starting on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)