import os
import json
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

CONFIG_FILE = 'config.json'

DEFAULT_CONFIG = {
    "appName": "YT Ninja", "appVersion": "Pro Edition v1.0", "titlebarText": "TEAM NINJA PRO", "appIcon": "",
    "texts": {
        "downloaderTitle": "Video Downloader", "fetchBtn": "Fetch", "downloadMp4Btn": "Download MP4",
        "downloadMp3Btn": "Download MP3", "downloadsTitle": "Active Downloads", "saveFileBtn": "SAVE FILE HERE",
        "cancelBtn": "Cancel", "libraryTitle": "Download History", "settingsTitle": "Settings",
        "versionLabel": "Application Version", "settingsVersionText": "YT Ninja v1.0.0 (Pre-Alpha)",
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

ICON_OPTIONS = [
    "bi-download", "bi-hourglass-split", "bi-folder", "bi-gear", "bi-arrow-repeat", "bi-film", 
    "bi-music-note-beamed", "bi-folder2-open", "bi-house", "bi-gear-wide", "bi-cloud-download",
    "bi-file-earmark-play", "bi-file-earmark-music", "bi-save", "bi-box-arrow-in-down", 
    "bi-collection-play", "bi-hdd", "bi-display", "bi-controller", "bi-android2"
]

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try:
                cfg = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(cfg)
                for k in ['texts', 'icons', 'fonts', 'colors', 'textures', 'animations', 'options']:
                    if k in DEFAULT_CONFIG and k in cfg:
                        merged[k] = {**DEFAULT_CONFIG[k], **cfg[k]}
                return merged
            except: pass
    return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=4)

HTML = '''
<!DOCTYPE html>
<html>
<head>
  <title>Ultimate App Customizer</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
  <style>
    body { background: #0f0f0f; color: #fff; font-family: 'Segoe UI', sans-serif; display: flex; height: 100vh; margin: 0; overflow: hidden; }
    .controls { width: 420px; overflow-y: auto; padding: 30px; background: #161618; border-right: 1px solid #222; }
    .preview { flex: 1; display: flex; align-items: center; justify-content: center; background: #0a0a0a; padding: 40px; position: relative; }
    .preview-mockup { width: 100%; max-width: 900px; height: 100%; max-height: 650px; border-radius: 12px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.8); display: flex; flex-direction: column; border: 1px solid #333; position: relative; }
    .prev-titlebar { height: 36px; display: flex; align-items: center; justify-content: space-between; padding: 0 15px; font-size: 12px; color: #fff; transition: background 0.3s; flex-shrink: 0; border-bottom: 1px solid rgba(0,0,0,0.2); }
    .prev-titlebar-controls { display: flex; gap: 15px; font-size: 12px; opacity: 0.7; }
    .prev-body { display: flex; flex: 1; overflow: hidden; }
    .prev-sidebar { padding: 20px; display: flex; flex-direction: column; gap: 10px; transition: background 0.3s, width 0.3s; }
    .prev-main { flex: 1; display: flex; flex-direction: column; overflow: hidden; transition: background 0.3s; position: relative; padding: 0; }
    
    /* Collapsible Details */
    details { background: #1a1a1d; margin-bottom: 15px; border-radius: 8px; border: 1px solid #333; overflow: hidden; }
    summary { padding: 15px; cursor: pointer; font-weight: bold; color: #cd9b1d; user-select: none; }
    summary::-webkit-details-marker { display: none; }
    summary::before { content: '▶ '; font-size: 10px; }
    details[open] summary::before { content: '▼ '; }
    .details-content { padding: 0 15px 15px 15px; }
    
    input[type="text"], select, textarea { width: 100%; padding: 10px; margin-bottom: 10px; background: #222; border: 1px solid #444; color: #fff; border-radius: 6px; box-sizing: border-box; font-family: inherit; }
    textarea { resize: vertical; min-height: 100px; }
    input[type="color"] { width: 100%; height: 35px; border: none; border-radius: 6px; cursor: pointer; background: #222; padding: 5px; margin-bottom: 10px; }
    input[type="range"] { width: 100%; margin-bottom: 10px; }
    input[type="file"] { padding: 10px; background: #222; border: 1px solid #444; color: #fff; border-radius: 6px; margin-bottom: 10px; width: 100%; box-sizing: border-box; }
    label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-top: 10px; display: block; }
    button.apply { width: 100%; padding: 15px; background: #cd9b1d; color: #000; border: none; font-weight: bold; font-size: 16px; border-radius: 6px; cursor: pointer; margin-top: 10px; }
    button.apply:hover { background: #e6b030; }
    h2 { margin-top: 0; color: #fff; }
    
    /* Preview Elements */
    .prev-btn { padding: 8px; border-radius: 6px; margin-bottom: 8px; font-size: 12px; background: rgba(255,255,255,0.05); color: #fff; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
    .prev-btn:hover { background: rgba(255,255,255,0.15); }
    .prev-btn.active { background: rgba(255,255,255,0.25); border-left: 3px solid #fff; }
    .prev-card { padding: 15px; border-radius: 8px; margin-bottom: 15px; transition: all 0.3s; }
    .prev-input { flex: 1; height: 35px; background: rgba(0,0,0,0.4); border-radius: 6px; }
    .prev-accent-btn { width: 70px; height: 35px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #000; font-size: 12px; cursor: pointer; }
    .prev-thumb { width: 120px; height: 70px; background: #444; border-radius: 4px; flex-shrink: 0; }
    .prev-line { height: 8px; background: rgba(255,255,255,0.2); border-radius: 4px; margin-bottom: 8px; }
    .prev-mp4 { color: #fff; padding: 8px; border-radius: 6px; text-align: center; font-size: 11px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 5px; }
    .prev-mp3 { color: #000; padding: 8px; border-radius: 6px; text-align: center; font-size: 11px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 5px; }
    .prev-progress-bg { width: 100%; border-radius: 4px; margin-top: 8px; background: rgba(0,0,0,0.4); }
    .prev-progress-bar { height: 100%; width: 60%; border-radius: 4px; }
    .prev-bitrate { padding: 5px; text-align: center; border-radius: 4px; font-size: 10px; cursor: pointer; border: 1px solid #444; }
    .prev-page { position: absolute; top: 0; left: 0; width: 100%; height: 100%; overflow-y: auto; padding: 20px; box-sizing: border-box; display: none; }
    .prev-page.active { display: block; }
    .prev-icon-box { width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
    .prev-settings-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; }
    .prev-open-loc { font-size:11px; padding:8px 15px; border-radius:6px; font-weight:bold; cursor:pointer; display:flex; align-items:center; gap:5px; color:#000; background:#cd9b1d; }
    
    /* Preview Loading Overlay */
    .prev-loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: none; flex-direction: column; align-items: center; justify-content: center; gap: 20px; z-index: 100; }
    .preview-loading-btn { position: absolute; bottom: 50px; right: 50px; background: #cd9b1d; color: #000; padding: 10px 20px; border-radius: 8px; font-weight: bold; cursor: pointer; border: none; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    .close-preview-btn { margin-top: 30px; background: rgba(255,255,255,0.1); color: #fff; padding: 8px 16px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2); cursor: pointer; }
    
    /* Preview Animations */
    @keyframes fade_slide { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes zoom { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
    @keyframes slide_left { from { opacity: 0; transform: translateX(50px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes slide_right { from { opacity: 0; transform: translateX(-50px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes flip_3d { from { opacity: 0; transform: perspective(1000px) rotateY(90deg); } to { opacity: 1; transform: perspective(1000px) rotateY(0deg); } }
    @keyframes flip_x { from { opacity: 0; transform: perspective(1000px) rotateX(90deg); } to { opacity: 1; transform: perspective(1000px) rotateX(0deg); } }
    @keyframes rotate_pop { from { opacity: 0; transform: rotate(-10deg) scale(0.9); } to { opacity: 1; transform: rotate(0deg) scale(1); } }
    @keyframes rotate_scale { from { opacity: 0; transform: rotate(-180deg) scale(0.5); } to { opacity: 1; transform: rotate(0deg) scale(1); } }
    @keyframes bounce_up { from { opacity: 0; transform: translateY(50px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes spin_in { from { opacity: 0; transform: rotate(180deg); } to { opacity: 1; transform: rotate(0deg); } }
    @keyframes skew_in { from { opacity: 0; transform: skew(20deg, 20deg); } to { opacity: 1; transform: skew(0deg, 0deg); } }
    
    /* Loading Animations */
    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1.0); } }
    @keyframes indeterminate { 0% { left: -40%; width: 40%; } 50% { left: 20%; width: 60%; } 100% { left: 100%; width: 40%; } }
    @keyframes ytPulse { 0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.4); } 50% { transform: scale(1.1); box-shadow: 0 0 0 15px rgba(255, 0, 0, 0); } 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); } }
  </style>
</head>
<body>
  <div class="controls">
    <h2>🎨 Ultimate App Customizer</h2>
    
    <details open>
      <summary>Loading Screen Customizer</summary>
      <div class="details-content">
        <label>Loading Text</label><input type="text" id="opt_loading_text" oninput="updatePreview()" placeholder="Loading..">
        <label>Loading Text Size</label>
        <select id="opt_loading_text_size" onchange="updatePreview()">
          <option value="16px">Small (16px)</option>
          <option value="20px">Medium (20px)</option>
          <option value="24px">Large (24px)</option>
          <option value="32px">Huge (32px)</option>
        </select>
        <label>Loading Text Weight</label>
        <select id="opt_loading_text_weight" onchange="updatePreview()">
          <option value="400">Normal (400)</option>
          <option value="600">Semi-Bold (600)</option>
          <option value="700">Bold (700)</option>
          <option value="800">Extra Bold (800)</option>
        </select>
        <label>Loading Background Color</label><input type="color" id="opt_loading_bg" oninput="updatePreview()">
        <label>Loading Background Texture</label>
        <select id="opt_loading_bg_texture" onchange="updatePreview()">
          <option value="none">None (Solid Color)</option><option value="tech_grid">Tech Grid</option>
          <option value="soft_dots">Soft Dots</option><option value="brushed_metal">Brushed Metal</option>
          <option value="carbon_fiber">Carbon Fiber</option><option value="camo">Camo</option>
          <option value="blueprint">Blueprint</option><option value="diagonal_stripes">Diagonal Stripes</option>
          <option value="hexagons">Hexagons</option><option value="circuit">Circuit Board</option>
        </select>
        <label>Loading Text Color</label><input type="color" id="opt_loading_text_color" oninput="updatePreview()">
        <label>Loading Spinner/Anim Color</label><input type="color" id="opt_loading_spinner_color" oninput="updatePreview()">
        <label>Loading Animation Size</label>
        <select id="opt_loading_spinner_size" onchange="updatePreview()">
          <option value="30px">Small (30px)</option>
          <option value="50px">Medium (50px)</option>
          <option value="70px">Large (70px)</option>
        </select>
        <label>Loading Animation Type</label>
        <select id="opt_loading_anim" onchange="updatePreview()">
          <option value="spinner">Spinner Circle</option>
          <option value="dots">Bouncing Dots</option>
          <option value="bar">Indeterminate Bar</option>
          <option value="yt_pulse">YT Pulse Logo</option>
        </select>
      </div>
    </details>

    <details open>
      <summary>Branding & Texts</summary>
      <div class="details-content">
        <label>App Name</label><input type="text" id="appName" oninput="updatePreview()">
        <label>App Version</label><input type="text" id="appVersion" oninput="updatePreview()">
        <label>Titlebar Text (Top Left Bar)</label><input type="text" id="titlebarText" oninput="updatePreview()">
        <label>Downloader Page Title</label><input type="text" id="txt_downloaderTitle" oninput="updatePreview()">
        <label>Fetch Button Text</label><input type="text" id="txt_fetchBtn" oninput="updatePreview()">
        <label>Download MP4 Button</label><input type="text" id="txt_downloadMp4Btn" oninput="updatePreview()">
        <label>Download MP3 Button</label><input type="text" id="txt_downloadMp3Btn" oninput="updatePreview()">
        <label>Downloads Page Title</label><input type="text" id="txt_downloadsTitle" oninput="updatePreview()">
        <label>Save File Button</label><input type="text" id="txt_saveFileBtn" oninput="updatePreview()">
        <label>Cancel Button</label><input type="text" id="txt_cancelBtn" oninput="updatePreview()">
        <label>Library Page Title</label><input type="text" id="txt_libraryTitle" oninput="updatePreview()">
        <label>Settings Page Title</label><input type="text" id="txt_settingsTitle" oninput="updatePreview()">
        <label>Settings: Version Label</label><input type="text" id="txt_versionLabel" oninput="updatePreview()">
        <label>Settings: Version Text</label><input type="text" id="txt_settingsVersionText" oninput="updatePreview()">
        <label>Settings: Close App Label</label><input type="text" id="txt_closeAppBtn" oninput="updatePreview()">
        <label>Updates Page Title</label><input type="text" id="txt_updatesTitle" oninput="updatePreview()">
        <label>Updates Log / Patch Notes</label>
        <textarea id="txt_updatesLog" oninput="updatePreview()" placeholder="Type your update logs here..."></textarea>
      </div>
    </details>

    <details open>
      <summary>App Icon & Assets</summary>
      <div class="details-content">
        <label>Upload Desktop App Icon (PNG/ICO)</label>
        <input type="file" id="icon_upload" accept="image/png, image/x-icon, image/jpeg">
        <p style="font-size: 10px; color: #888; margin-bottom: 10px;">Upload an image. It will instantly change the Desktop App taskbar icon!</p>
      </div>
    </details>

    <details open>
      <summary>Fonts & Typography</summary>
      <div class="details-content">
        <label>Font Family</label>
        <select id="font_family" onchange="updatePreview()">
          <option value="Segoe UI, sans-serif">Segoe UI (Default Windows)</option>
          <option value="Arial, sans-serif">Arial</option>
          <option value="'Courier New', monospace">Courier New (Monospace)</option>
          <option value="Georgia, serif">Georgia (Serif)</option>
          <option value="'Trebuchet MS', sans-serif">Trebuchet MS</option>
          <option value="Verdana, sans-serif">Verdana</option>
        </select>
        <label>Global Font Size</label>
        <select id="opt_font_size" onchange="updatePreview()">
          <option value="14px">Small (14px)</option>
          <option value="16px">Normal (16px)</option>
          <option value="18px">Large (18px)</option>
          <option value="20px">Huge (20px)</option>
        </select>
        <label>Global Text Alignment</label>
        <select id="opt_text_align" onchange="updatePreview()">
          <option value="left">Left</option>
          <option value="center">Center</option>
          <option value="right">Right</option>
        </select>
        <label>Font Weight (Thickness)</label>
        <select id="font_weight" onchange="updatePreview()">
          <option value="400">Normal (400)</option><option value="500">Medium (500)</option>
          <option value="600">Semi-Bold (600)</option><option value="700">Bold (700)</option><option value="800">Extra Bold (800)</option>
        </select>
        <label>Text Stroke (Outline) Color</label>
        <input type="color" id="font_stroke_color" value="#000000" oninput="updatePreview()">
        <label>Text Stroke Width</label>
        <select id="font_stroke_width" onchange="updatePreview()">
          <option value="0px">None (0px)</option><option value="0.5px">Thin (0.5px)</option>
          <option value="1px">Medium (1px)</option><option value="2px">Thick (2px)</option>
          <option value="3px">Very Thick (3px)</option>
        </select>
      </div>
    </details>

    <details open>
      <summary>Icon Customizer</summary>
      <div class="details-content">
        <label>Downloader Icon</label><select id="icon_downloader" onchange="updatePreview()"></select>
        <label>Active Downloads Icon</label><select id="icon_downloads" onchange="updatePreview()"></select>
        <label>Library Icon</label><select id="icon_library" onchange="updatePreview()"></select>
        <label>Settings Icon</label><select id="icon_settings" onchange="updatePreview()"></select>
        <label>Updates Icon</label><select id="icon_updates" onchange="updatePreview()"></select>
        <label>MP4 (Video) Icon</label><select id="icon_mp4" onchange="updatePreview()"></select>
        <label>MP3 (Audio) Icon</label><select id="icon_mp3" onchange="updatePreview()"></select>
        <label>Save File Icon</label><select id="icon_save" onchange="updatePreview()"></select>
        <label>Open Location Icon</label><select id="icon_openLocation" onchange="updatePreview()"></select>
      </div>
    </details>

    <details open>
      <summary>Colors & Highlights</summary>
      <div class="details-content">
        <label>Titlebar Color</label><input type="color" id="titlebar" oninput="updatePreview()">
        <label>Sidebar Color</label><input type="color" id="sidebar" oninput="updatePreview()">
        <label>Background Color</label><input type="color" id="bg" oninput="updatePreview()">
        <label>Card Color</label><input type="color" id="card" oninput="updatePreview()">
        <label>Accent / MP3 Button Color</label><input type="color" id="accent" oninput="updatePreview()">
        <label>Success / MP4 Button Color</label><input type="color" id="success" oninput="updatePreview()">
        <label>Danger / Cancel Button Color</label><input type="color" id="danger" oninput="updatePreview()">
        <label>Hover / Highlight Color</label><input type="color" id="hover" oninput="updatePreview()">
        <label>UI Outline Color</label><input type="color" id="opt_outline_color" value="#000000" oninput="updatePreview()">
        <label>UI Outline Width</label>
        <select id="opt_outline_width" onchange="updatePreview()">
          <option value="0px">None (0px)</option><option value="1px">Thin (1px)</option>
          <option value="2px">Medium (2px)</option><option value="3px">Thick (3px)</option>
        </select>
      </div>
    </details>

    <details>
      <summary>Textures & Backgrounds</summary>
      <div class="details-content">
        <label>Main Background Texture</label>
        <select id="texture_bg" onchange="updatePreview()">
          <option value="none">None (Solid Color)</option><option value="tech_grid">Tech Grid</option>
          <option value="soft_dots">Soft Dots</option><option value="brushed_metal">Brushed Metal</option>
          <option value="carbon_fiber">Carbon Fiber</option><option value="camo">Camo</option>
          <option value="blueprint">Blueprint</option><option value="diagonal_stripes">Diagonal Stripes</option>
          <option value="hexagons">Hexagons</option><option value="circuit">Circuit Board</option>
        </select>
        <label>Sidebar Texture</label>
        <select id="texture_sidebar" onchange="updatePreview()">
          <option value="none">None (Solid Color)</option><option value="tech_grid">Tech Grid</option>
          <option value="soft_dots">Soft Dots</option><option value="brushed_metal">Brushed Metal</option>
          <option value="carbon_fiber">Carbon Fiber</option><option value="camo">Camo</option>
          <option value="blueprint">Blueprint</option><option value="diagonal_stripes">Diagonal Stripes</option>
          <option value="hexagons">Hexagons</option><option value="circuit">Circuit Board</option>
        </select>
      </div>
    </details>

    <details>
      <summary>Layout & Glassmorphism</summary>
      <div class="details-content">
        <label>Border Radius (Roundness)</label>
        <select id="opt_radius" onchange="updatePreview()">
          <option value="0px">Sharp (0px)</option><option value="8px">Slightly Round (8px)</option>
          <option value="12px">Round (12px)</option><option value="20px">Very Round (20px)</option>
        </select>
        <label>Card Shadow Depth</label>
        <select id="opt_shadow" onchange="updatePreview()">
          <option value="none">None</option><option value="0 4px 6px rgba(0,0,0,0.2)">Subtle</option>
          <option value="0 10px 20px rgba(0,0,0,0.4)">Medium</option><option value="0 15px 35px rgba(0,0,0,0.6)">Heavy</option>
        </select>
        <label>Sidebar Width</label>
        <select id="opt_sidebar_width" onchange="updatePreview()">
          <option value="220px">Small (220px)</option><option value="260px">Medium (260px)</option>
          <option value="300px">Large (300px)</option>
        </select>
        <label>Content Padding (Spacing)</label>
        <select id="opt_padding" onchange="updatePreview()">
          <option value="16px">Compact (16px)</option><option value="24px">Normal (24px)</option>
          <option value="32px">Spacious (32px)</option><option value="48px">Very Spacious (48px)</option>
        </select>
        <label>Progress Bar Height</label>
        <select id="opt_progress_height" onchange="updatePreview()">
          <option value="6px">Thin (6px)</option><option value="12px">Normal (12px)</option>
          <option value="18px">Thick (18px)</option>
        </select>
        <label>Card Opacity (Glass Effect) - <span id="opacity_val">100%</span></label>
        <input type="range" id="opt_card_opacity" min="0.2" max="1.0" step="0.1" value="1.0" oninput="updatePreview()">
        <label>Titlebar Opacity - <span id="tb_opacity_val">100%</span></label>
        <input type="range" id="opt_titlebar_opacity" min="0.2" max="1.0" step="0.1" value="1.0" oninput="updatePreview()">
        <label>Show Version in Sidebar</label>
        <select id="opt_show_version" onchange="updatePreview()">
          <option value="true">Yes</option><option value="false">No</option>
        </select>
      </div>
    </details>

    <details>
      <summary>Animations</summary>
      <div class="details-content">
        <label>Page Transition Effect</label>
        <select id="anim_page" onchange="updatePreview()">
          <option value="fade_slide">Fade & Slide Up</option><option value="zoom">Zoom In</option>
          <option value="slide_left">Slide Left</option><option value="slide_right">Slide Right</option>
          <option value="flip_3d">3D Flip Y</option><option value="flip_x">3D Flip X</option>
          <option value="rotate_pop">Rotate Pop</option><option value="rotate_scale">Rotate & Scale</option>
          <option value="bounce_up">Bounce Up</option><option value="spin_in">Spin In</option>
          <option value="skew_in">Skew In</option>
        </select>
      </div>
    </details>

    <button class="apply" onclick="applyConfig()">Apply to Desktop App</button>
  </div>

  <div class="preview">
    <div class="preview-mockup" id="mockup">
      <div class="prev-titlebar" id="prev_titlebar_container">
        <div style="display: flex; align-items: center; gap: 8px;">
          <img id="prev_app_icon" src="" style="width: 16px; height: 16px; display: none;">
          <span id="prev_titlebar_text">TEAM NINJA PRO</span>
        </div>
        <div class="prev-titlebar-controls"><span>—</span><span>▢</span><span>✕</span></div>
      </div>
      <div class="prev-body">
        <div class="prev-sidebar" id="prev_sidebar">
          <div style="font-size: 9px; letter-spacing: 2px; opacity: 0.8;" id="prev_titlebar_dup">TEAM NINJA PRO</div>
          <h3 style="margin:0; border:none; color:#fff; font-size: 20px;" id="prev_appName">YT Ninja</h3>
          <p style="margin:0; font-size: 10px; opacity: 0.7;" id="prev_appVersion">Pro Edition v1.0</p>
          <div style="margin-top: 20px;">
            <div class="prev-btn active" onclick="switchPrevPage('downloader')" id="nav_downloader"><i class="bi bi-download"></i> Downloader</div>
            <div class="prev-btn" onclick="switchPrevPage('downloads')" id="nav_downloads"><i class="bi bi-hourglass-split"></i> Active Downloads</div>
            <div class="prev-btn" onclick="switchPrevPage('library')" id="nav_library"><i class="bi bi-folder"></i> Library</div>
            <div class="prev-btn" onclick="switchPrevPage('settings')" id="nav_settings"><i class="bi bi-gear"></i> Settings</div>
            <div class="prev-btn" onclick="switchPrevPage('updates')" id="nav_updates"><i class="bi bi-arrow-repeat"></i> Updates</div>
          </div>
        </div>
        <div class="prev-main" id="prev_main"></div>
      </div>
      <div class="prev-loading-overlay" id="prev_loading_overlay">
        <div id="prev_loading_anim"></div>
        <h2 id="prev_loading_text" style="margin: 0;">Loading..</h2>
        <button class="close-preview-btn" onclick="hideLoadingPreview()">Close Preview</button>
      </div>
    </div>
    <button class="preview-loading-btn" onclick="showLoadingPreview()">Preview Loading Screen</button>
  </div>

<script>
  let currentConfig = {};
  let prevPage = 'downloader';
  const iconOptions = {{ icon_options_json | safe }};

  function hexToRgba(hex, alpha) {
    if(!hex) return `rgba(34,34,38,${alpha})`;
    const r = parseInt(hex.slice(1,3), 16), g = parseInt(hex.slice(3,5), 16), b = parseInt(hex.slice(5,7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  function populateIcons() {
    const keys = ['downloader', 'downloads', 'library', 'settings', 'updates', 'mp4', 'mp3', 'save', 'openLocation'];
    keys.forEach(k => {
      const sel = document.getElementById('icon_' + k);
      if(sel) sel.innerHTML = iconOptions.map(i => `<option value="${i}">${i.replace('bi-', '')}</option>`).join('');
    });
  }

  function getTextures(type) {
    const t = {
      tech_grid: 'linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)',
      soft_dots: 'radial-gradient(rgba(255,255,255,0.1) 1px, transparent 1px)',
      brushed_metal: 'linear-gradient(45deg, rgba(255,255,255,0.03) 25%, transparent 25%, transparent 75%, rgba(255,255,255,0.03) 75%, rgba(255,255,255,0.03))',
      carbon_fiber: 'linear-gradient(27deg, #151515 5px, transparent 5px) 0 5px, linear-gradient(207deg, #151515 5px, transparent 5px) 10px 0px, linear-gradient(27deg, #222 5px, transparent 5px) 0px 10px, linear-gradient(207deg, #222 5px, transparent 5px) 10px 5px, linear-gradient(90deg, #1b1b1b 10px, transparent 10px), linear-gradient(#1d1d1d 25%, #1b1b1b 25%, #1b1b1b 50%, transparent 50%, transparent 75%, #1d1d1d 75%, #1d1d1d)',
      camo: 'radial-gradient(circle at 20% 20%, #2a2a2a 10%, transparent 10%), radial-gradient(circle at 80% 30%, #1a1a1a 15%, transparent 15%), radial-gradient(circle at 50% 80%, #333 10%, transparent 10%)',
      blueprint: 'linear-gradient(rgba(0, 100, 255, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 100, 255, 0.1) 1px, transparent 1px)',
      diagonal_stripes: 'repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 10px, transparent 10px, transparent 20px)',
      hexagons: 'linear-gradient(30deg, #0001 12%, transparent 12.5%, transparent 87%, #0001 87.5%, #0001), linear-gradient(150deg, #0001 12%, transparent 12.5%, transparent 87%, #0001 87.5%, #0001), linear-gradient(30deg, #0001 12%, transparent 12.5%, transparent 87%, #0001 87.5%, #0001), linear-gradient(150deg, #0001 12%, transparent 12.5%, transparent 87%, #0001 87.5%, #0001), linear-gradient(60deg, #7777 25%, transparent 25.5%, transparent 75%, #7777 75%, #7777), linear-gradient(60deg, #7777 25%, transparent 25.5%, transparent 75%, #7777 75%, #7777)',
      circuit: 'radial-gradient(circle at 50% 50%, transparent 20%, #000 20%, #000 21%, transparent 21%), linear-gradient(transparent 49%, #000 49%, #000 51%, transparent 51%)'
    };
    return t[type] || 'none';
  }
  function getTextureSize(type) {
    const s = { tech_grid: '20px 20px', soft_dots: '15px 15px', brushed_metal: '4px 4px', carbon_fiber: '20px 20px', camo: '100px 100px', blueprint: '40px 40px', diagonal_stripes: 'auto', hexagons: '80px 140px', circuit: '50px 50px' };
    return s[type] || 'auto';
  }

  function getPageHTML(page) {
    if(page === 'downloader') {
      return `
        <h2 style="margin:0 0 15px 0; font-size: 18px; color:#fff;" id="prev_txt_downloaderTitle">Video Downloader</h2>
        <div style="display:flex; gap:10px; align-items:center; margin-bottom:15px;">
          <div class="prev-input"></div>
          <div class="prev-accent-btn" id="prev_accent_btn" onclick="alert('Fetch simulated!')">Fetch</div>
        </div>
        <div class="prev-card" id="prev_card" style="display:flex; gap:10px;">
          <div class="prev-thumb"></div>
          <div style="flex:1;">
            <div class="prev-line" style="width: 80%; background: #fff;"></div>
            <div class="prev-line" style="width: 40%;"></div>
          </div>
        </div>
        <div style="display:flex; gap:10px;">
          <div class="prev-card" id="prev_card2" style="flex:1;">
            <div class="prev-line" style="width: 50%; background: #fff; margin-bottom: 15px;"></div>
            <div class="prev-input" style="height: 25px; margin-bottom: 10px;"></div>
            <div class="prev-mp4" id="prev_txt_mp4"><i class="bi bi-film"></i> Download MP4</div>
          </div>
          <div class="prev-card" id="prev_card3" style="flex:1;">
            <div class="prev-line" style="width: 50%; background: #fff; margin-bottom: 15px;"></div>
            <div style="display:flex; gap:5px; margin-bottom: 10px;">
                <div class="prev-bitrate" id="prev_br1" onclick="selectPrevBitrate('128')" style="flex:1;">128</div>
                <div class="prev-bitrate" id="prev_br2" onclick="selectPrevBitrate('320')" style="flex:1;">320</div>
            </div>
            <div class="prev-mp3" id="prev_txt_mp3"><i class="bi bi-music-note-beamed"></i> Download MP3</div>
          </div>
        </div>`;
    }
    if(page === 'downloads') {
      return `
        <h2 style="margin:0 0 15px 0; font-size: 18px; color:#fff;" id="prev_txt_downloadsTitle">Active Downloads</h2>
        <div class="prev-card" id="prev_card4">
          <div style="display:flex; justify-content:space-between; font-size: 12px; margin-bottom: 5px;">
            <span>Video Title Here</span>
            <span style="display:flex; align-items:center; gap:3px;" id="prev_txt_saveFile"><i class="bi bi-folder2-open"></i> SAVE FILE HERE</span>
          </div>
          <div class="prev-progress-bg" id="prev_prog_bg"><div class="prev-progress-bar" id="prev_progress"></div></div>
          <div style="display:flex; justify-content:space-between; margin-top:10px;">
              <span style="font-size:10px; opacity:0.7;">2.5 MB/s | ETA: 10s</span>
              <span style="font-size:10px; padding:2px 8px; border-radius:4px;" id="prev_txt_cancel">Cancel</span>
          </div>
        </div>`;
    }
    if(page === 'library') {
      return `
        <h2 style="margin:0 0 15px 0; font-size: 18px; color:#fff;" id="prev_txt_libraryTitle">Download History</h2>
        <div class="prev-card" style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:15px;">
            <div class="prev-icon-box" id="prev_lib_icon_mp4"><i class="bi bi-film" id="prev_lib_i_mp4"></i></div>
            <div><div style="font-weight:bold; font-size:14px;">MP4 Video Title</div><div style="font-size:11px; opacity:0.6;">MP4 | 45.2 MB | 2024-07-03</div></div>
          </div>
          <div class="prev-open-loc" id="prev_open_loc_mp4"><i class="bi bi-folder2-open"></i> Open Location</div>
        </div>
        <div class="prev-card" style="display:flex; justify-content:space-between; align-items:center;">
          <div style="display:flex; align-items:center; gap:15px;">
            <div class="prev-icon-box" id="prev_lib_icon_mp3"><i class="bi bi-music-note-beamed" id="prev_lib_i_mp3"></i></div>
            <div><div style="font-weight:bold; font-size:14px;">MP3 Audio Title</div><div style="font-size:11px; opacity:0.6;">MP3 | 8.5 MB | 2024-07-03</div></div>
          </div>
          <div class="prev-open-loc" id="prev_open_loc_mp3"><i class="bi bi-folder2-open"></i> Open Location</div>
        </div>`;
    }
    if(page === 'settings') {
      return `
        <div class="prev-settings-container">
          <div class="prev-card" id="prev_card5" style="width:320px; text-align:center; padding: 30px;">
            <h2 style="margin:0 0 30px 0; font-size: 20px; color:#fff; text-align:center;" id="prev_txt_settingsTitle">Settings</h2>
            <div style="margin-bottom:30px;">
              <h3 style="margin:0 0 5px 0; border:none; font-size:14px; color:#fff;" id="prev_txt_versionLabel">Application Version</h3>
              <p style="margin:0; font-size:11px; opacity:0.7;" id="prev_txt_settingsVersionText">YT Ninja v1.0.0 (Pre-Alpha)</p>
            </div>
            <div style="border-top:1px solid rgba(255,255,255,0.2); padding-top:20px;">
              <h3 style="margin:0 0 5px 0; border:none; font-size:14px; color:#fff;" id="prev_txt_closeApp">Close Application</h3>
              <p style="margin:0 0 20px 0; font-size:10px; opacity:0.7;">Force quit the application and stop all background processes.</p>
              <div style="padding:10px; border-radius:6px; font-size:13px; font-weight:bold; color:#fff; cursor:pointer;" id="prev_close_btn">Close App</div>
            </div>
          </div>
        </div>`;
    }
    if(page === 'updates') {
      return `
        <h2 style="margin:0 0 15px 0; font-size: 18px; color:#fff;" id="prev_txt_updatesTitle">Updates</h2>
        <div class="prev-card" id="prev_card6" style="white-space: pre-wrap; height: 100%; overflow-y: auto;"><div id="prev_txt_updatesLog">v1.0.0:\n- Initial Release</div></div>`;
    }
    return '';
  }

  async function loadConfig() {
    populateIcons();
    const res = await fetch('/api/config');
    currentConfig = await res.json();
    
    document.getElementById('appName').value = currentConfig.appName;
    document.getElementById('appVersion').value = currentConfig.appVersion;
    document.getElementById('titlebarText').value = currentConfig.titlebarText;
    document.getElementById('font_family').value = currentConfig.fonts.family;
    document.getElementById('font_weight').value = currentConfig.fonts.fontWeight;
    document.getElementById('font_stroke_color').value = currentConfig.fonts.strokeColor;
    document.getElementById('font_stroke_width').value = currentConfig.fonts.strokeWidth;
    
    Object.keys(currentConfig.texts).forEach(k => {
      const el = document.getElementById('txt_' + k);
      if(el) el.value = currentConfig.texts[k];
    });

    Object.keys(currentConfig.icons).forEach(k => {
      const el = document.getElementById('icon_' + k);
      if(el) el.value = currentConfig.icons[k];
    });

    document.getElementById('titlebar').value = currentConfig.colors.titlebar || '#000000';
    document.getElementById('sidebar').value = currentConfig.colors.sidebar;
    document.getElementById('bg').value = currentConfig.colors.bg;
    document.getElementById('card').value = currentConfig.colors.card;
    document.getElementById('accent').value = currentConfig.colors.accent;
    document.getElementById('success').value = currentConfig.colors.success || '#28a745';
    document.getElementById('danger').value = currentConfig.colors.danger || '#dc3545';
    document.getElementById('hover').value = currentConfig.colors.hover || '#a40000';
    document.getElementById('opt_outline_color').value = currentConfig.options.outlineColor || '#000000';
    document.getElementById('opt_outline_width').value = currentConfig.options.outlineWidth || '0px';
    document.getElementById('texture_bg').value = currentConfig.textures.background;
    document.getElementById('texture_sidebar').value = currentConfig.textures.sidebar || 'none';
    document.getElementById('anim_page').value = currentConfig.animations.pageTransition;
    document.getElementById('opt_radius').value = currentConfig.options.borderRadius;
    document.getElementById('opt_shadow').value = currentConfig.options.cardShadow;
    document.getElementById('opt_sidebar_width').value = currentConfig.options.sidebarWidth || '260px';
    document.getElementById('opt_padding').value = currentConfig.options.contentPadding || '32px';
    document.getElementById('opt_progress_height').value = currentConfig.options.progressBarHeight || '12px';
    document.getElementById('opt_card_opacity').value = currentConfig.options.cardOpacity || '1.0';
    document.getElementById('opt_titlebar_opacity').value = currentConfig.options.titlebarOpacity || '1.0';
    document.getElementById('opt_show_version').value = currentConfig.options.showVersion || 'true';
    document.getElementById('opt_font_size').value = currentConfig.options.fontSize || '16px';
    document.getElementById('opt_text_align').value = currentConfig.options.textAlign || 'left';
    
    document.getElementById('opt_loading_text').value = currentConfig.options.loadingText || 'Loading..';
    document.getElementById('opt_loading_text_size').value = currentConfig.options.loadingTextSize || '24px';
    document.getElementById('opt_loading_text_weight').value = currentConfig.options.loadingTextWeight || '700';
    document.getElementById('opt_loading_bg').value = currentConfig.options.loadingBgColor || '#1a1a1d';
    document.getElementById('opt_loading_bg_texture').value = currentConfig.options.loadingBgTexture || 'none';
    document.getElementById('opt_loading_text_color').value = currentConfig.options.loadingTextColor || '#cd9b1d';
    document.getElementById('opt_loading_spinner_color').value = currentConfig.options.loadingSpinnerColor || '#cd9b1d';
    document.getElementById('opt_loading_spinner_size').value = currentConfig.options.loadingSpinnerSize || '50px';
    document.getElementById('opt_loading_anim').value = currentConfig.options.loadingAnimation || 'spinner';
    
    if(currentConfig.appIcon) {
      document.getElementById('prev_app_icon').src = currentConfig.appIcon + '?t=' + new Date().getTime();
      document.getElementById('prev_app_icon').style.display = 'block';
    } else {
      document.getElementById('prev_app_icon').style.display = 'none';
    }

    updatePreview();
  }

  async function uploadIcon() {
    const fileInput = document.getElementById('icon_upload');
    if (fileInput.files.length === 0) return alert("Please select an image file first.");
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    const res = await fetch('/api/upload_icon', { method: 'POST', body: formData });
    const data = await res.json();
    if(data.success) {
      alert('Icon uploaded and applied!');
      currentConfig.appIcon = data.icon;
      document.getElementById('prev_app_icon').src = data.icon + '?t=' + new Date().getTime();
      document.getElementById('prev_app_icon').style.display = 'block';
      applyConfig();
    } else {
      alert('Upload failed: ' + data.error);
    }
  }

  function updatePreview() {
    currentConfig.appName = document.getElementById('appName').value;
    currentConfig.appVersion = document.getElementById('appVersion').value;
    currentConfig.titlebarText = document.getElementById('titlebarText').value;
    currentConfig.fonts.family = document.getElementById('font_family').value;
    currentConfig.fonts.fontWeight = document.getElementById('font_weight').value;
    currentConfig.fonts.strokeColor = document.getElementById('font_stroke_color').value;
    currentConfig.fonts.strokeWidth = document.getElementById('font_stroke_width').value;
    
    Object.keys(currentConfig.texts).forEach(k => {
      const el = document.getElementById('txt_' + k);
      if(el) currentConfig.texts[k] = el.value;
    });

    Object.keys(currentConfig.icons).forEach(k => {
      const el = document.getElementById('icon_' + k);
      if(el) currentConfig.icons[k] = el.value;
    });

    currentConfig.colors.titlebar = document.getElementById('titlebar').value;
    currentConfig.colors.sidebar = document.getElementById('sidebar').value;
    currentConfig.colors.bg = document.getElementById('bg').value;
    currentConfig.colors.card = document.getElementById('card').value;
    currentConfig.colors.accent = document.getElementById('accent').value;
    currentConfig.colors.success = document.getElementById('success').value;
    currentConfig.colors.danger = document.getElementById('danger').value;
    currentConfig.colors.hover = document.getElementById('hover').value;
    currentConfig.options.outlineColor = document.getElementById('opt_outline_color').value;
    currentConfig.options.outlineWidth = document.getElementById('opt_outline_width').value;
    currentConfig.textures.background = document.getElementById('texture_bg').value;
    currentConfig.textures.sidebar = document.getElementById('texture_sidebar').value;
    currentConfig.animations.pageTransition = document.getElementById('anim_page').value;
    currentConfig.options.borderRadius = document.getElementById('opt_radius').value;
    currentConfig.options.cardShadow = document.getElementById('opt_shadow').value;
    currentConfig.options.sidebarWidth = document.getElementById('opt_sidebar_width').value;
    currentConfig.options.contentPadding = document.getElementById('opt_padding').value;
    currentConfig.options.progressBarHeight = document.getElementById('opt_progress_height').value;
    currentConfig.options.cardOpacity = document.getElementById('opt_card_opacity').value;
    currentConfig.options.titlebarOpacity = document.getElementById('opt_titlebar_opacity').value;
    currentConfig.options.showVersion = document.getElementById('opt_show_version').value;
    currentConfig.options.fontSize = document.getElementById('opt_font_size').value;
    currentConfig.options.textAlign = document.getElementById('opt_text_align').value;

    currentConfig.options.loadingText = document.getElementById('opt_loading_text').value;
    currentConfig.options.loadingTextSize = document.getElementById('opt_loading_text_size').value;
    currentConfig.options.loadingTextWeight = document.getElementById('opt_loading_text_weight').value;
    currentConfig.options.loadingBgColor = document.getElementById('opt_loading_bg').value;
    currentConfig.options.loadingBgTexture = document.getElementById('opt_loading_bg_texture').value;
    currentConfig.options.loadingTextColor = document.getElementById('opt_loading_text_color').value;
    currentConfig.options.loadingSpinnerColor = document.getElementById('opt_loading_spinner_color').value;
    currentConfig.options.loadingSpinnerSize = document.getElementById('opt_loading_spinner_size').value;
    currentConfig.options.loadingAnimation = document.getElementById('opt_loading_anim').value;

    document.getElementById('opacity_val').innerText = Math.round(currentConfig.options.cardOpacity * 100) + '%';
    document.getElementById('tb_opacity_val').innerText = Math.round(currentConfig.options.titlebarOpacity * 100) + '%';

    const mockup = document.getElementById('mockup');
    mockup.style.fontFamily = currentConfig.fonts.family;
    mockup.style.fontWeight = currentConfig.fonts.fontWeight;
    mockup.style.fontSize = currentConfig.options.fontSize;
    mockup.style.WebkitTextStroke = `${currentConfig.fonts.strokeWidth} ${currentConfig.fonts.strokeColor}`;

    const tbBg = hexToRgba(currentConfig.colors.titlebar, parseFloat(currentConfig.options.titlebarOpacity));
    const tbContainer = document.getElementById('prev_titlebar_container');
    if(tbContainer) tbContainer.style.backgroundColor = tbBg;
    document.getElementById('prev_titlebar_text').innerText = currentConfig.titlebarText;
    document.getElementById('prev_titlebar_dup').innerText = currentConfig.titlebarText;
    document.getElementById('prev_appName').innerText = currentConfig.appName;
    
    const versionEl = document.getElementById('prev_appVersion');
    if(currentConfig.options.showVersion === 'true') {
      versionEl.style.display = 'block';
      versionEl.innerText = currentConfig.appVersion;
    } else {
      versionEl.style.display = 'none';
    }
    
    const sideBar = document.getElementById('prev_sidebar');
    sideBar.style.width = currentConfig.options.sidebarWidth;
    sideBar.style.backgroundColor = currentConfig.colors.sidebar;
    sideBar.style.backgroundImage = getTextures(currentConfig.textures.sidebar);
    sideBar.style.backgroundSize = getTextureSize(currentConfig.textures.sidebar);
    
    const navMap = { nav_downloader: 'downloader', nav_downloads: 'downloads', nav_library: 'library', nav_settings: 'settings', nav_updates: 'updates' };
    Object.keys(navMap).forEach(id => {
      const el = document.getElementById(id);
      if(el) {
        const icon = el.querySelector('i');
        if(icon) icon.className = `bi ${currentConfig.icons[navMap[id]]}`;
      }
    });

    const mainBg = document.getElementById('prev_main');
    mainBg.style.backgroundColor = currentConfig.colors.bg;
    mainBg.style.backgroundImage = getTextures(currentConfig.textures.background);
    mainBg.style.backgroundSize = getTextureSize(currentConfig.textures.background);
    mainBg.style.textAlign = currentConfig.options.textAlign;

    // Update Loading Screen Preview Colors/Text live
    const loadingText = document.getElementById('prev_loading_text');
    loadingText.innerText = currentConfig.options.loadingText;
    loadingText.style.color = currentConfig.options.loadingTextColor;
    loadingText.style.fontSize = currentConfig.options.loadingTextSize;
    loadingText.style.fontWeight = currentConfig.options.loadingTextWeight;
    
    const loadingOverlay = document.getElementById('prev_loading_overlay');
    loadingOverlay.style.backgroundColor = currentConfig.options.loadingBgColor;
    loadingOverlay.style.backgroundImage = getTextures(currentConfig.options.loadingBgTexture);
    loadingOverlay.style.backgroundSize = getTextureSize(currentConfig.options.loadingBgTexture);

    // If the preview is currently open, update the animation live
    if (loadingOverlay.style.display === 'flex') {
      showLoadingPreview();
    }

    switchPrevPage(prevPage, true);
  }

  function showLoadingPreview() {
    const overlay = document.getElementById('prev_loading_overlay');
    const animContainer = document.getElementById('prev_loading_anim');
    const animType = currentConfig.options.loadingAnimation;
    const color = currentConfig.options.loadingSpinnerColor;
    const size = currentConfig.options.loadingSpinnerSize;

    if (animType === 'spinner') {
      animContainer.innerHTML = `<div style="width: ${size}; height: ${size}; border: 5px solid rgba(255,255,255,0.2); border-top-color: ${color}; border-radius: 50%; animation: spin 1s linear infinite;"></div>`;
    } else if (animType === 'dots') {
      const dotSize = parseInt(size) / 3 + 'px';
      animContainer.innerHTML = `<div style="display: flex; gap: 10px;"><div style="width: ${dotSize}; height: ${dotSize}; background: ${color}; border-radius: 50%; animation: bounce 1s infinite;"></div><div style="width: ${dotSize}; height: ${dotSize}; background: ${color}; border-radius: 50%; animation: bounce 1s infinite 0.2s;"></div><div style="width: ${dotSize}; height: ${dotSize}; background: ${color}; border-radius: 50%; animation: bounce 1s infinite 0.4s;"></div></div>`;
    } else if (animType === 'bar') {
      animContainer.innerHTML = `<div style="width: ${parseInt(size)*3}px; height: 8px; background: rgba(255,255,255,0.2); border-radius: 4px; overflow: hidden; position: relative;"><div style="position: absolute; height: 100%; background: ${color}; border-radius: 4px; animation: indeterminate 1.5s infinite ease-in-out;"></div></div>`;
    } else if (animType === 'yt_pulse') {
      const sz = parseInt(size);
      animContainer.innerHTML = `
        <div style="position: relative; width: ${sz}px; height: ${sz * 0.7}px; display: flex; align-items: center; justify-content: center; animation: ytPulse 1.5s infinite ease-in-out;">
          <div style="width: 100%; height: 100%; background: ${color}; border-radius: 30%;"></div>
          <div style="position: absolute; width: 0; height: 0; border-top: ${sz/4}px solid transparent; border-bottom: ${sz/4}px solid transparent; border-left: ${sz/3}px solid #fff; margin-left: ${sz/12}px;"></div>
        </div>
      `;
    }

    overlay.style.display = 'flex';
  }

  function hideLoadingPreview() {
    document.getElementById('prev_loading_overlay').style.display = 'none';
  }

  function switchPrevPage(page, isUpdate = false) {
    prevPage = page;
    const main = document.getElementById('prev_main');
    
    const animClass = isUpdate ? '' : `style="animation: ${currentConfig.animations.pageTransition} 0.3s forwards;"`;
    main.innerHTML = `<div class="prev-page active" ${animClass}>${getPageHTML(page)}</div>`;
    
    const cardOpacity = parseFloat(currentConfig.options.cardOpacity || 1.0);
    const cardBg = hexToRgba(currentConfig.colors.card, cardOpacity);
    
    document.querySelectorAll('.prev-card').forEach(el => {
      el.style.backgroundColor = cardBg;
      el.style.borderRadius = currentConfig.options.borderRadius;
      el.style.boxShadow = currentConfig.options.cardShadow;
      el.style.outline = `${currentConfig.options.outlineWidth} solid ${currentConfig.options.outlineColor}`;
    });

    const accentBtn = document.getElementById('prev_accent_btn');
    if(accentBtn) {
      accentBtn.style.backgroundColor = currentConfig.colors.accent;
      accentBtn.style.borderRadius = currentConfig.options.borderRadius;
      accentBtn.style.outline = `${currentConfig.options.outlineWidth} solid ${currentConfig.options.outlineColor}`;
      accentBtn.innerText = currentConfig.texts.fetchBtn;
    }
    
    const mp4Btn = document.getElementById('prev_txt_mp4');
    if(mp4Btn) {
      mp4Btn.style.backgroundColor = currentConfig.colors.success;
      mp4Btn.style.borderRadius = currentConfig.options.borderRadius;
      mp4Btn.innerHTML = `<i class="bi ${currentConfig.icons.mp4}"></i> ${currentConfig.texts.downloadMp4Btn}`;
    }
    
    const mp3Btn = document.getElementById('prev_txt_mp3');
    if(mp3Btn) {
      mp3Btn.style.backgroundColor = currentConfig.colors.accent;
      mp3Btn.style.borderRadius = currentConfig.options.borderRadius;
      mp3Btn.innerHTML = `<i class="bi ${currentConfig.icons.mp3}"></i> ${currentConfig.texts.downloadMp3Btn}`;
    }
    
    const cancelBtn = document.getElementById('prev_txt_cancel');
    if(cancelBtn) {
      cancelBtn.style.backgroundColor = currentConfig.colors.danger;
      cancelBtn.innerText = currentConfig.texts.cancelBtn;
    }
    
    const saveBtn = document.getElementById('prev_txt_saveFile');
    if(saveBtn) {
      saveBtn.style.color = currentConfig.colors.success;
      saveBtn.innerHTML = `<i class="bi ${currentConfig.icons.save}"></i> ${currentConfig.texts.saveFileBtn}`;
    }
    
    const progBg = document.getElementById('prev_prog_bg');
    if(progBg) {
      progBg.style.height = currentConfig.options.progressBarHeight;
    }
    
    const progBar = document.getElementById('prev_progress');
    if(progBar) {
      progBar.style.background = currentConfig.colors.accent;
    }
    
    const libIconMp4 = document.getElementById('prev_lib_icon_mp4');
    if(libIconMp4) {
      libIconMp4.style.backgroundColor = currentConfig.colors.accent + '20';
      libIconMp4.style.borderRadius = currentConfig.options.borderRadius;
      document.getElementById('prev_lib_i_mp4').className = `bi ${currentConfig.icons.mp4}`;
      document.getElementById('prev_lib_i_mp4').style.color = currentConfig.colors.accent;
    }
    
    const libIconMp3 = document.getElementById('prev_lib_icon_mp3');
    if(libIconMp3) {
      libIconMp3.style.backgroundColor = currentConfig.colors.accent + '20';
      libIconMp3.style.borderRadius = currentConfig.options.borderRadius;
      document.getElementById('prev_lib_i_mp3').className = `bi ${currentConfig.icons.mp3}`;
      document.getElementById('prev_lib_i_mp3').style.color = currentConfig.colors.accent;
    }
    
    document.querySelectorAll('.prev-open-loc').forEach(loc => {
      loc.style.backgroundColor = currentConfig.colors.accent;
      loc.style.color = '#000';
      loc.style.borderRadius = currentConfig.options.borderRadius;
      loc.innerHTML = `<i class="bi ${currentConfig.icons.openLocation}"></i> Open Location`;
    });
    
    const closeBtn = document.getElementById('prev_close_btn');
    if(closeBtn) {
      closeBtn.style.background = `linear-gradient(to bottom, ${currentConfig.colors.danger}, #8b0000)`;
      closeBtn.style.borderRadius = currentConfig.options.borderRadius;
      closeBtn.innerText = currentConfig.texts.closeAppBtn;
    }

    const textMap = {
      prev_txt_downloaderTitle: 'downloaderTitle', 
      prev_txt_downloadsTitle: 'downloadsTitle', 
      prev_txt_libraryTitle: 'libraryTitle', 
      prev_txt_settingsTitle: 'settingsTitle', 
      prev_txt_versionLabel: 'versionLabel', 
      prev_txt_settingsVersionText: 'settingsVersionText', 
      prev_txt_updatesTitle: 'updatesTitle',
      prev_txt_updatesLog: 'updatesLog'
    };
    Object.keys(textMap).forEach(id => {
      const el = document.getElementById(id);
      if(el) el.innerText = currentConfig.texts[textMap[id]];
    });

    document.querySelectorAll('.prev-sidebar .prev-btn').forEach(b => b.classList.remove('active'));
    const navEl = document.getElementById('nav_' + page);
    if(navEl) navEl.classList.add('active');
  }

  function selectPrevBitrate(bitrate) {
    const br1 = document.getElementById('prev_br1');
    const br2 = document.getElementById('prev_br2');
    if(!br1 || !br2) return;
    if(bitrate === '128') {
      br1.style.background = currentConfig.colors.accent; br1.style.color = '#000'; br1.style.borderColor = currentConfig.colors.accent;
      br2.style.background = 'transparent'; br2.style.color = '#fff'; br2.style.borderColor = '#444';
    } else {
      br2.style.background = currentConfig.colors.accent; br2.style.color = '#000'; br2.style.borderColor = currentConfig.colors.accent;
      br1.style.background = 'transparent'; br1.style.color = '#fff'; br1.style.borderColor = '#444';
    }
  }

  async function applyConfig() {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(currentConfig)
    });
    if(res.ok) alert('Applied! Check your Desktop App.');
  }

  document.getElementById('icon_upload').addEventListener('change', uploadIcon);

  loadConfig();
</script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML, icon_options_json=json.dumps(ICON_OPTIONS))

@app.route('/api/config', methods=['GET'])
def get_config_api():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def apply_config_api():
    save_config(request.json)
    return jsonify({"status": "success"})

@app.route('/api/upload_icon', methods=['POST'])
def upload_icon():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'custom_icon.png')
    file.save(save_path)
    
    cfg = load_config()
    cfg['appIcon'] = 'custom_icon.png'
    save_config(cfg)
    
    return jsonify({"success": True, "icon": "custom_icon.png"})

if __name__ == '__main__':
    app.run(port=4000)