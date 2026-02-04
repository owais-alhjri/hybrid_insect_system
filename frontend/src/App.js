import { useEffect, useState } from "react";
import "./command-center.css";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [status, setStatus] = useState("IDLE");
  const [droneDet, setDroneDet] = useState(null);
  const [tankDet, setTankDet] = useState(null);
  const [logs, setLogs] = useState([]);
  const [finished, setFinished] = useState(false);

  useEffect(() => {
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  async function update() {
    try {
      const res = await fetch(`${API_BASE}/live_status`);
      if (!res.ok) return;
      const data = await res.json();

      setStatus(data.status);
      
      // Explicitly toggle finished based on backend status
      setFinished(data.status === "FINISHED");

      if (data.last_detection) {
        if (data.status.startsWith("AERIAL")) {
          setDroneDet(data.last_detection);
        } else if (data.status.startsWith("GROUND")) {
          setTankDet(data.last_detection);
        }
      }

      const logRes = await fetch(`${API_BASE}/detections`);
      if (logRes.ok) {
        const logData = await logRes.json();
        setLogs(logData.slice(0, 8));
      }
    } catch (e) { 
      console.log("Waiting for backend connection..."); 
    }
  }

const handleReboot = async () => {
  try {
    // 1. Tell the backend to clear "FINISHED" status
    const response = await fetch(`${API_BASE}/reset`, { method: 'POST' });
    
    if (response.ok) {
      // 2. Clear local state
      setDroneDet(null);
      setTankDet(null);
      setFinished(false);
      setStatus("IDLE");
      
      // 3. Refresh page to clear the log table and images
      window.location.reload(); 
    }
  } catch (e) {
    console.error("Backend is offline. Cannot reset.");
    // Force a reload anyway to try and clear the UI
    window.location.reload();
  }
};

  const renderUnit = (type) => {
    const active = status?.startsWith(type === "drone" ? "AERIAL" : "GROUND");
    const det = type === "drone" ? droneDet : tankDet;
    // FIXED: Added 'scanning' definition here
    const scanning = status?.includes("SCANNING") && active;

    return (
      <div
        className={`glass p-6 rounded-2xl transition-all duration-700 ${active ? "ring-2 ring-green-500/50" : "opacity-60 scale-95"}`}
      >
        <h2 className="text-xl font-bold flex items-center gap-2 mb-4">
          {type === "drone" ? "🚁 AERIAL UNIT" : "🚜 GROUND UNIT"}
        </h2>

        <div className="live-feed h-[300px]">
          {scanning && <div className="scan-line block" />}
          {det?.image ? (
            <img
              src={`data:image/jpeg;base64,${det.image}`}
              className="w-full h-full object-cover rounded-lg"
              alt="Feed"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-700 font-mono text-xs text-center px-4">
              {type === "drone" ? "WAITING FOR UPLINK..." : "AWAITING COORDINATES..."}
            </div>
          )}
        </div>

        <div className="mt-4 space-y-2">
          <div className="glass p-3 rounded-xl flex justify-between items-center">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Target</span>
            <span className="font-bold text-green-400">
              {det?.class?.toUpperCase() || "---"}
            </span>
          </div>
          <div className="glass p-3 rounded-xl flex justify-between items-center">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Confidence</span>
            <span className="font-bold text-blue-400">
              {det?.confidence ? `${(det.confidence * 100).toFixed(1)}%` : "0%"}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="flex justify-between items-end mb-8 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tighter text-white">
            AGRI-TECH <span className="text-green-500 italic">OMAN</span>
          </h1>
          <p className="text-slate-400 font-mono text-sm tracking-widest uppercase">
            Hybrid Autonomous Inspection Network
          </p>
        </div>

        <div className="flex gap-4">
          {finished ? (
            <div className="bg-green-500/20 border border-green-500 px-4 py-2 rounded-lg text-center min-w-[140px]">
              <p className="text-[10px] text-green-500 font-bold uppercase">Mission Status</p>
              <p className="text-white font-black">COMPLETE</p>
            </div>
          ) : (
            <div className="bg-blue-500/20 border border-blue-500 px-4 py-2 rounded-lg text-center min-w-[140px]">
              <p className="text-[10px] text-blue-500 font-bold uppercase">Mission Status</p>
              <p className="text-white font-black animate-pulse">OPERATIONAL</p>
            </div>
          )}
          <button
            onClick={handleReboot}
            className="glass px-6 py-2 rounded-lg text-xs font-bold hover:bg-red-500/20 hover:text-red-500 transition-all border border-slate-700"
          >
            REBOOT SYSTEM
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {renderUnit("drone")}
        {renderUnit("tank")}
      </div>

      <div className="glass p-6 rounded-2xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Centralized Mission Logs</h3>
          {finished && (
            <span className="text-green-500 font-bold text-xs animate-bounce">
              ✓ ALL SECTORS VERIFIED
            </span>
          )}
        </div>
        <table className="w-full text-left">
          <thead>
            <tr className="text-slate-500 text-xs uppercase border-b border-slate-800">
              <th className="pb-3 px-2">Timestamp</th>
              <th className="pb-3 px-2">Unit</th>
              <th className="pb-3 px-2">Detection</th>
              <th className="pb-3 px-2">Confidence</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {logs.map((l, i) => (
              <tr key={i} className="border-b border-slate-800/50">
                <td className="py-3 px-2 font-mono text-xs">{new Date(l.timestamp).toLocaleTimeString()}</td>
                <td className="py-3 px-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] ${l.source === "drone" ? "bg-blue-900 text-blue-200" : "bg-red-900 text-red-200"}`}>
                    {l.source.toUpperCase()}
                  </span>
                </td>
                <td className="py-3 px-2 font-bold">{l.insect}</td>
                <td className="py-3 px-2 text-green-400">{(l.confidence * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}