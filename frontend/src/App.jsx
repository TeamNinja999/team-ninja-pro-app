import React, { useState, useEffect } from 'react'

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
