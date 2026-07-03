import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// --- Smart API Router ---
// If running inside the compiled .exe, use absolute URL. Otherwise use proxy.
const API_BASE = window.location.protocol === 'file:' ? 'http://127.0.0.1:5000' : '';

// --- Smart Sound Engine ---
const playNotification = (type) => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    if (type === 'found') {
      osc.type = 'sine'; osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start(); osc.stop(ctx.currentTime + 0.3);
    } else if (type === 'finished') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(660, ctx.currentTime);
      osc.frequency.setValueAtTime(990, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start(); osc.stop(ctx.currentTime + 0.4);
    }
  } catch(e) {}
};

// --- Helpers ---
const hexToRgba = (hex, alpha) => {
  if(!hex) return `rgba(34,34,38,${alpha})`;
  const r = parseInt(hex.slice(1,3), 16), g = parseInt(hex.slice(3,5), 16), b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
};

const getTexture = (type) => {
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
};
const getTextureSize = (type) => {
  const s = { tech_grid: '20px 20px', soft_dots: '15px 15px', brushed_metal: '4px 4px', carbon_fiber: '20px 20px', camo: '100px 100px', blueprint: '40px 40px', diagonal_stripes: 'auto', hexagons: '80px 140px', circuit: '50px 50px' };
  return s[type] || 'auto';
};

export default function App() {
  const [configLoaded, setConfigLoaded] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const [page, setPage] = useState('downloader');
  const [url, setUrl] = useState('');
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [downloads, setDownloads] = useState([]);
  const [history, setHistory] = useState([]);
  const [mp3Bitrate, setMp3Bitrate] = useState('320');
  const playedSounds = useRef([]);
  const appliedIcon = useRef(null);
  
  const [config, setConfig] = useState({
    appName: "YT Downloader", appVersion: "Pro Edition v1.0", titlebarText: "YT DOWNLOADER", appIcon: "",
    texts: { downloaderTitle: "Video Downloader", fetchBtn: "Fetch", downloadMp4Btn: "Download MP4", downloadMp3Btn: "Download MP3", downloadsTitle: "Active Downloads", saveFileBtn: "SAVE FILE HERE", cancelBtn: "Cancel", libraryTitle: "Download History", settingsTitle: "Settings", versionLabel: "Application Version", settingsVersionText: "YT Downloader v1.0.0 (Pre-Alpha)", closeAppBtn: "Close App", closeAppDesc: "Force quit the application and stop all background processes.", updatesTitle: "Updates", updatesLog: "v1.0.0 - Initial Release" },
    icons: { downloader: "bi-download", downloads: "bi-hourglass-split", library: "bi-folder", settings: "bi-gear", updates: "bi-arrow-repeat", mp4: "bi-film", mp3: "bi-music-note-beamed", save: "bi-folder2-open", openLocation: "bi-folder2-open" },
    fonts: { family: "Segoe UI, sans-serif", fontWeight: "600", strokeColor: "transparent", strokeWidth: "0px" },
    colors: { sidebar: "#8b0000", bg: "#1a1a1d", card: "#222226", accent: "#cd9b1d", hover: "#a40000", success: "#28a745", danger: "#dc3545", titlebar: "#000000" },
    textures: { background: "brushed_metal", sidebar: "none" },
    animations: { pageTransition: "fade_slide" },
    options: { borderRadius: "12px", cardShadow: "0 10px 20px rgba(0,0,0,0.4)", outlineColor: "transparent", outlineWidth: "0px", sidebarWidth: "260px", progressBarHeight: "12px", showVersion: "true", cardOpacity: "1.0", contentPadding: "32px", fontSize: "16px", textAlign: "left", titlebarOpacity: "1.0", loadingText: "Loading..", loadingBgColor: "#1a1a1d", loadingTextColor: "#cd9b1d", loadingSpinnerColor: "#cd9b1d", loadingAnimation: "spinner", loadingBgTexture: "none", loadingTextSize: "24px", loadingTextWeight: "700", loadingSpinnerSize: "50px" }
  });

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/progress?t=${Date.now()}`);
        const data = await res.json();
        data.forEach(job => {
          if (job.status === 'completed' && !playedSounds.current.includes(job.job_id)) {
            playNotification('finished');
            playedSounds.current.push(job.job_id);
          }
        });
        setDownloads(data.filter(d => d.status !== 'cancelled'));
      } catch (e) {}
    };
    const interval = setInterval(fetchProgress, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/config?t=${Date.now()}`);
      console.log("Fetching config from:", `${API_BASE}/api/config?t=${Date.now()}`);
      console.log("Response status:", res.status);
      const data = await res.json();
      console.log("Data received from Python:", data.appName);
      
      setConfig(data);
      
      if (data.appIcon && data.appIcon !== appliedIcon.current && window.electronAPI?.setIcon) {
        window.electronAPI.setIcon(data.appIcon);
        appliedIcon.current = data.appIcon;
      }

      if (!configLoaded) {
        setConfigLoaded(true);
        setTimeout(() => setIsLoaded(true), 1500);
      }
    } catch (e) {
      console.error("Fetch Config Failed:", e);
      if (!configLoaded) setTimeout(fetchConfig, 1000);
    }
  };  useEffect(() => {
    fetchConfig();
    const interval = setInterval(fetchConfig, 1500);
    return () => clearInterval(interval);
  }, [configLoaded]);

  useEffect(() => {
    if (page === 'library') fetchHistory();
  }, [page]);

  const fetchHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/history?t=${Date.now()}`);
      const data = await res.json();
      setHistory(data);
    } catch (e) {}
  };

  const fetchInfo = async () => {
    if(!url) return;
    setLoading(true); setError(''); setInfo(null);
    try {
      const res = await fetch(`${API_BASE}/api/info`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ url }) });
      const data = await res.json();
      if(!res.ok) throw new Error(data.error);
      setInfo(data); playNotification('found');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startDownload = async (mode) => {
    if(!info) return;
    const height = document.getElementById('qualitySelect')?.value;
    const payload = { url, mode, title: info.title, height, bitrate: mp3Bitrate };
    const res = await fetch(`${API_BASE}/api/download`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (res.ok) setPage('downloads');
  };

  const cancelDownload = async (jobId) => {
    await fetch(`${API_BASE}/api/cancel/${jobId}`, { method: 'POST' });
  };

  const saveFile = async (job) => {
    try {
      const res = await fetch(`${API_BASE}/api/get_filepath/${job.job_id}`);
      const data = await res.json();
      if(data.error) return alert(data.error);
      
      const savedPath = await window.electronAPI.saveAs(data.file_path, data.filename);
      
      if(savedPath) {
        await fetch(`${API_BASE}/api/history/add`, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            id: job.job_id, title: job.title, date: new Date().toLocaleString(),
            size: data.size, file_path: savedPath, type: data.mode === 'video' ? 'MP4' : 'MP3'
          })
        });
        await fetch(`${API_BASE}/api/clear_job/${job.job_id}`, { method: 'POST' });
        setDownloads(prev => prev.filter(j => j.job_id !== job.job_id));
      }
    } catch(e) { alert('Save failed: ' + e.message); }
  };

  const pageVariants = {
    fade_slide: { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 } },
    zoom: { initial: { opacity: 0, scale: 0.95 }, animate: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 0.95 } },
    slide_left: { initial: { opacity: 0, x: 50 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -50 } },
    slide_right: { initial: { opacity: 0, x: -50 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: 50 } },
    flip_3d: { initial: { opacity: 0, rotateY: 90 }, animate: { opacity: 1, rotateY: 0 }, exit: { opacity: 0, rotateY: -90 } },
    flip_x: { initial: { opacity: 0, rotateX: 90 }, animate: { opacity: 1, rotateX: 0 }, exit: { opacity: 0, rotateX: -90 } },
    rotate_pop: { initial: { opacity: 0, rotate: -10, scale: 0.9 }, animate: { opacity: 1, rotate: 0, scale: 1 }, exit: { opacity: 0, rotate: 10, scale: 0.9 } },
    rotate_scale: { initial: { opacity: 0, rotate: -180, scale: 0.5 }, animate: { opacity: 1, rotate: 0, scale: 1 }, exit: { opacity: 0, rotate: 180, scale: 0.5 } },
    bounce_up: { initial: { opacity: 0, y: 50 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 50 } },
    spin_in: { initial: { opacity: 0, rotate: 180 }, animate: { opacity: 1, rotate: 0 }, exit: { opacity: 0, rotate: -180 } },
    skew_in: { initial: { opacity: 0, skewX: 20, skewY: 20 }, animate: { opacity: 1, skewX: 0, skewY: 0 }, exit: { opacity: 0, skewX: -20, skewY: -20 } }
  };
  
  if (!configLoaded) {
    return <div style={{ width: '100vw', height: '100vh', backgroundColor: '#1a1a1d' }}></div>;
  }

  const currentAnim = pageVariants[config.animations.pageTransition] || pageVariants.fade_slide;
  const radius = config.options.borderRadius;
  const shadow = config.options.cardShadow;
  const outline = `${config.options.outlineWidth} solid ${config.options.outlineColor}`;
  const textStyle = { fontFamily: config.fonts.family, fontWeight: config.fonts.fontWeight, WebkitTextStroke: `${config.fonts.strokeWidth} ${config.fonts.strokeColor}`, fontSize: config.options.fontSize };
  const cardBg = hexToRgba(config.colors.card, parseFloat(config.options.cardOpacity || 1.0));
  const titlebarBg = hexToRgba(config.colors.titlebar || '#000000', parseFloat(config.options.titlebarOpacity || 1.0));

  const navItem = (id, iconKey, label) => (
    <button 
      onClick={() => setPage(id)}
      className={`flex items-center gap-3 px-4 py-3 w-full transition-all duration-100 ${page === id ? 'bg-black/30 text-white shadow-lg border-l-4 border-white/50' : 'text-white/80 hover:text-white'}`}
      style={{ borderRadius: radius, outline: outline }}
      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = config.colors.hover}
      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
    >
      <i className={`bi ${config.icons[iconKey]} text-xl`}></i>
      <span className="font-medium">{label}</span>
    </button>
  );

  if (!isLoaded) {
    let animHTML = null;
    const spinSize = config.options.loadingSpinnerSize || '50px';
    if (config.options.loadingAnimation === 'spinner') {
      animHTML = <div style={{ width: spinSize, height: spinSize, border: `5px solid rgba(255,255,255,0.2)`, borderTopColor: config.options.loadingSpinnerColor, borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>;
    } else if (config.options.loadingAnimation === 'dots') {
      const dotSize = parseInt(spinSize) / 3 + 'px';
      animHTML = (
        <div style={{ display: 'flex', gap: '10px' }}>
          <div style={{ width: dotSize, height: dotSize, backgroundColor: config.options.loadingSpinnerColor, borderRadius: '50%', animation: 'bounce 1s infinite' }}></div>
          <div style={{ width: dotSize, height: dotSize, backgroundColor: config.options.loadingSpinnerColor, borderRadius: '50%', animation: 'bounce 1s infinite 0.2s' }}></div>
          <div style={{ width: dotSize, height: dotSize, backgroundColor: config.options.loadingSpinnerColor, borderRadius: '50%', animation: 'bounce 1s infinite 0.4s' }}></div>
        </div>
      );
    } else if (config.options.loadingAnimation === 'bar') {
      animHTML = (
        <div style={{ width: parseInt(spinSize)*3 + 'px', height: '8px', backgroundColor: 'rgba(255,255,255,0.2)', borderRadius: '4px', overflow: 'hidden', position: 'relative' }}>
          <div style={{ position: 'absolute', height: '100%', backgroundColor: config.options.loadingSpinnerColor, borderRadius: '4px', animation: 'indeterminate 1.5s infinite ease-in-out' }}></div>
        </div>
      );
    } else if (config.options.loadingAnimation === 'yt_pulse') {
      const sz = parseInt(spinSize);
      animHTML = (
        <div style={{ position: 'relative', width: sz, height: sz * 0.7, display: 'flex', alignItems: 'center', justifyContent: 'center', animation: 'ytPulse 1.5s infinite ease-in-out' }}>
          <div style={{ width: '100%', height: '100%', backgroundColor: config.options.loadingSpinnerColor, borderRadius: '30%' }}></div>
          <div style={{ position: 'absolute', width: 0, height: 0, borderTop: `${sz/4}px solid transparent`, borderBottom: `${sz/4}px solid transparent`, borderLeft: `${sz/3}px solid #fff`, marginLeft: `${sz/12}px` }}></div>
        </div>
      );
    }

    return (
      <div style={{ 
        width: '100vw', height: '100vh', 
        backgroundColor: config.options.loadingBgColor, 
        backgroundImage: getTexture(config.options.loadingBgTexture), 
        backgroundSize: getTextureSize(config.options.loadingBgTexture), 
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px' 
      }}>
        {animHTML}
        <h2 style={{ color: config.options.loadingTextColor, margin: 0, fontFamily: config.fonts.family, fontWeight: config.options.loadingTextWeight, fontSize: config.options.loadingTextSize }}>{config.options.loadingText}</h2>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      transition={{ duration: 0.5 }}
      className="flex h-screen text-white overflow-hidden" 
      style={{ backgroundColor: config.colors.bg, ...textStyle }}
    >
      <div className="fixed top-0 left-0 right-0 h-10 z-50 flex items-center justify-between px-3 text-xs text-gray-400 font-bold drag-region" style={{ backgroundColor: titlebarBg, borderBottom: '1px solid rgba(0,0,0,0.5)', WebkitBackdropFilter: 'blur(4px)' }}>
        <div className="flex items-center gap-2 ml-2">
          <span className="text-white">{config.titlebarText}</span>
        </div>
        <div className="flex items-center no-drag">
          <button onClick={() => window.electronAPI.minimize()} className="p-2 hover:bg-white/10 w-10 text-center">—</button>
          <button onClick={() => window.electronAPI.maximize()} className="p-2 hover:bg-white/10 w-10 text-center">▢</button>
          <button onClick={() => window.electronAPI.close()} className="p-2 hover:bg-red-600 w-10 text-center">✕</button>
        </div>
      </div>

      <aside 
        className="mt-10 flex flex-col justify-between border-r border-black/50 shadow-xl" 
        style={{ width: config.options.sidebarWidth, backgroundColor: config.colors.sidebar, backgroundImage: getTexture(config.textures.sidebar), backgroundSize: getTextureSize(config.textures.sidebar) }}
      >
        <div className="p-4 space-y-2">
          <div className="px-2 py-4 mb-4 border-b border-white/20">
            <p className="text-[10px] tracking-widest text-white/80 mb-1">{config.titlebarText}</p>
            <h1 className="text-2xl font-bold text-white">{config.appName}</h1>
            {config.options.showVersion === "true" && <p className="text-xs text-white/70 mt-1">{config.appVersion}</p>}
          </div>
          {navItem('downloader', 'downloader', 'Downloader')}
          {navItem('downloads', 'downloads', 'Active Downloads')}
          {navItem('library', 'library', 'Library')}
          {navItem('settings', 'settings', 'Settings')}
          {navItem('updates', 'updates', 'Updates')}
        </div>
      </aside>

      <main 
        className="flex-1 mt-10 overflow-y-auto" 
        style={{ backgroundColor: config.colors.bg, backgroundImage: getTexture(config.textures.background), backgroundSize: getTextureSize(config.textures.background), padding: config.options.contentPadding, textAlign: config.options.textAlign }}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={page}
            initial={currentAnim.initial}
            animate={currentAnim.animate}
            exit={currentAnim.exit}
            transition={{ duration: 0.3 }}
            className="max-w-4xl mx-auto h-full"
          >
            {page === 'downloader' && (
              <div>
                <h2 className="text-3xl font-bold mb-6">{config.texts.downloaderTitle}</h2>
                <div className="flex gap-2 mb-8">
                  <input 
                    type="text" value={url} onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://www.youtube.com/watch?v=..."
                    className="flex-1 bg-black/40 border border-white/10 p-4 outline-none focus:ring-2 text-white"
                    style={{ borderRadius: radius, outline: outline, '--tw-ring-color': config.colors.accent }}
                  />
                  <button 
                    onClick={fetchInfo} disabled={loading}
                    className="text-black px-8 py-4 font-bold transition shadow-lg"
                    style={{ backgroundColor: config.colors.accent, borderRadius: radius, outline: outline }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = config.colors.hover}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = config.colors.accent}
                  >
                    {loading ? 'Fetching...' : config.texts.fetchBtn}
                  </button>
                </div>
                {error && <div className="bg-red-500/20 text-red-300 p-4 mb-8 border border-red-500/50" style={{ borderRadius: radius }}>{error}</div>}

                {info && (
                  <div className="space-y-6">
                    <motion.div 
                      initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
                      className="p-6 flex gap-6"
                      style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}
                    >
                      <img src={info.thumbnail} className="w-72 shadow-md object-cover" style={{ borderRadius: radius }} alt="Thumbnail" />
                      <div className="flex-1 flex flex-col justify-center">
                        <h3 className="text-xl font-bold mb-2">{info.title}</h3>
                        <p className="text-gray-400 mb-1">By {info.uploader}</p>
                        <p className="text-gray-500 text-sm">Duration: {info.duration}s</p>
                      </div>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="p-6" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}>
                        <h4 className="text-lg font-bold mb-4" style={{ color: config.colors.accent }}>Video Format</h4>
                        <div className="space-y-4">
                          <select id="qualitySelect" className="w-full bg-black/40 border border-white/10 p-3 outline-none text-white" style={{ borderRadius: radius }}>
                            {info.qualities.map(q => <option key={q.value} value={q.value}>{q.label}</option>)}
                          </select>
                          <button 
                            onClick={() => startDownload('video')} 
                            className="w-full text-white py-3 font-bold transition shadow flex items-center justify-center gap-2" 
                            style={{ backgroundColor: config.colors.success, borderRadius: radius, outline: outline }}
                          >
                            <i className={`bi ${config.icons.mp4}`}></i> {config.texts.downloadMp4Btn}
                          </button>
                        </div>
                      </div>

                      <div className="p-6" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}>
                        <h4 className="text-lg font-bold mb-4" style={{ color: config.colors.accent }}>Audio Format</h4>
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <button 
                              onClick={() => setMp3Bitrate('128')} 
                              className={`py-3 font-medium transition border ${mp3Bitrate === '128' ? 'text-black border-white' : 'bg-black/40 text-white border-white/10'}`}
                              style={mp3Bitrate === '128' ? { backgroundColor: config.colors.accent, borderColor: config.colors.accent, borderRadius: radius, outline: outline } : { borderRadius: radius, outline: outline }}
                            >128 kbps</button>
                            <button 
                              onClick={() => setMp3Bitrate('320')} 
                              className={`py-3 font-medium transition border ${mp3Bitrate === '320' ? 'text-black border-white' : 'bg-black/40 text-white border-white/10'}`}
                              style={mp3Bitrate === '320' ? { backgroundColor: config.colors.accent, borderColor: config.colors.accent, borderRadius: radius, outline: outline } : { borderRadius: radius, outline: outline }}
                            >320 kbps</button>
                          </div>
                          <button 
                            onClick={() => startDownload('audio')} 
                            className="w-full text-black py-3 font-bold transition shadow flex items-center justify-center gap-2"
                            style={{ backgroundColor: config.colors.accent, borderRadius: radius, outline: outline }}
                          >
                            <i className={`bi ${config.icons.mp3}`}></i> {config.texts.downloadMp3Btn}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {page === 'downloads' && (
              <div>
                <h2 className="text-3xl font-bold mb-6">{config.texts.downloadsTitle}</h2>
                <div className="space-y-4">
                  {downloads.length === 0 && <p className="text-gray-500 text-lg">No active downloads. Start one from the Downloader tab!</p>}
                  {downloads.map(job => (
                    <div key={job.job_id} className="p-5" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}>
                      <div className="flex justify-between mb-3">
                        <span className="font-bold truncate text-lg">{job.title}</span>
                        <span className={`text-sm font-bold ${job.status === 'error' ? 'text-red-400' : ''}`} style={{ color: job.status === 'error' ? '#f87171' : config.colors.accent }}>
                          {job.status === 'completed' ? 'Ready to Save' : job.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="w-full bg-black/40 overflow-hidden" style={{ height: config.options.progressBarHeight, borderRadius: radius }}>
                        <motion.div 
                          className="h-full"
                          style={{ background: `linear-gradient(to right, ${config.colors.accent}, ${config.colors.sidebar})`, borderRadius: radius }}
                          initial={{ width: 0 }} animate={{ width: `${job.progress}%` }} transition={{ ease: "easeOut", duration: 0.5 }}
                        ></motion.div>
                      </div>
                      <div className="flex justify-between items-center mt-3 text-sm text-gray-400">
                        <span>{job.speed || '-'} | ETA: {job.eta || '-'}</span>
                        {job.status === 'completed' ? (
                          <button onClick={() => saveFile(job)} className="text-green-400 font-bold hover:underline flex items-center gap-1">
                            <i className={`bi ${config.icons.save}`}></i> {config.texts.saveFileBtn}
                          </button>
                        ) : job.status === 'error' ? (
                          <span className="text-red-400">Failed</span>
                        ) : (
                          <button onClick={() => cancelDownload(job.job_id)} className="text-white px-4 py-1 font-medium transition" style={{ backgroundColor: config.colors.danger, borderRadius: radius }}>{config.texts.cancelBtn}</button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {page === 'library' && (
              <div>
                <h2 className="text-3xl font-bold mb-6">{config.texts.libraryTitle}</h2>
                {history.length === 0 ? (
                  <p className="text-gray-500 text-lg">You haven't downloaded anything yet.</p>
                ) : (
                  <div className="space-y-3">
                    {history.map(h => (
                      <div key={h.id} className="p-4 flex justify-between items-center" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}>
                        <div className="flex items-center gap-4">
                          <div style={{ backgroundColor: config.colors.accent + '20', width: '48px', height: '48px', borderRadius: radius, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <i className={`bi ${h.type === 'MP3' ? config.icons.mp3 : config.icons.mp4} text-2xl`} style={{ color: config.colors.accent }}></i>
                          </div>
                          <div>
                            <h4 className="font-bold text-lg">{h.title}</h4>
                            <p className="text-sm text-gray-400">{h.type} | {h.size} | {h.date}</p>
                          </div>
                        </div>
                        <button 
                          onClick={() => window.electronAPI.openLocation(h.file_path)} 
                          className="text-black px-4 py-2 font-medium transition flex items-center gap-2"
                          style={{ backgroundColor: config.colors.accent, borderRadius: radius }}
                        >
                          <i className={`bi ${config.icons.openLocation}`}></i> Open Location
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {page === 'settings' && (
              <div className="flex flex-col items-center justify-center h-full">
                <div className="p-8 w-full max-w-md text-center" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline }}>
                  <h2 className="text-2xl font-bold mb-8 text-white">{config.texts.settingsTitle}</h2>
                  <div className="mb-8">
                    <h3 className="font-bold text-lg mb-1 text-white">{config.texts.versionLabel}</h3>
                    <p className="text-gray-400">{config.texts.settingsVersionText}</p>
                  </div>
                  <div className="border-t border-white/20 pt-6">
                    <h3 className="font-bold text-lg mb-2 text-white">{config.texts.closeAppBtn}</h3>
                    <p className="text-gray-400 text-sm mb-6">{config.texts.closeAppDesc}</p>
                    <button onClick={() => window.electronAPI.close()} className="text-white px-8 py-3 font-bold transition w-full shadow-lg" style={{ background: `linear-gradient(to bottom, ${config.colors.danger}, #8b0000)`, border: `1px solid #8b0000`, borderRadius: radius }}>{config.texts.closeAppBtn}</button>
                  </div>
                </div>
              </div>
            )}

            {page === 'updates' && (
              <div>
                <h2 className="text-3xl font-bold mb-6">{config.texts.updatesTitle}</h2>
                <div className="p-6" style={{ backgroundColor: cardBg, borderRadius: radius, boxShadow: shadow, outline: outline, whiteSpace: 'pre-wrap' }}>
                  {config.texts.updatesLog}
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </main>
    </motion.div>
  );
}