import { useEffect, useState, useRef } from "react";
import "./command-center.css";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [status, setStatus] = useState("IDLE");
  const [droneDet, setDroneDet] = useState(null);
  const [tankDet, setTankDet] = useState(null);
  const [logs, setLogs] = useState([]);
  const [finished, setFinished] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws");

      ws.onopen = () => console.log("Connected to Backend");

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStatus(data.status);
        setFinished(data.status === "FINISHED");

        if (data.last_detection) {
          const det = data.last_detection;

          // 1. Update Live View
          if (det.source === "drone") {
            setDroneDet(det);
          } else if (det.source === "tank") {
            setTankDet(det);
          }

          // 2. Update Logs (With Filters)
          setLogs((prevLogs) => {
            // FILTER: Don't log "Scanning..."
            if (det.class === "Scanning...") return prevLogs;

            const newTimestamp = det.timestamp || new Date().toISOString();

            // FILTER: Prevent duplicates
            if (prevLogs.length > 0) {
              const last = prevLogs[0];
              if (
                last.id === det.id ||
                (last.timestamp === newTimestamp && last.insect === det.class)
              ) {
                return prevLogs;
              }
            }

            const newEntry = {
              ...det,
              insect: det.class || "Unknown",
              timestamp: newTimestamp,
            };

            return [newEntry, ...prevLogs].slice(0, 50);
          });
        }
      };

      ws.onclose = () => setTimeout(connect, 2000);
      socketRef.current = ws;
    };

    connect();

    return () => {
      if (socketRef.current) socketRef.current.close();
    };
  }, []);

  useEffect(() => {
    if (!finished) return;
    fetch(`${API_BASE}/detections`)
      .then((r) => r.json())
      .then((data) => {
        const formattedLogs = data.map((d) => ({
          ...d,
          insect: d.insect || d.class || "Unknown",
        }));
        setLogs(formattedLogs);
      });
  }, [finished]);

  const handleStartMission = async () => {
    try {
      const res = await fetch(`${API_BASE}/start_mission`, { method: "POST" });
      const data = await res.json();
      if (data.status === "started") {
        setFinished(false);
        setStatus("OPERATIONAL");
        setLogs([]);
        setDroneDet(null);
        setTankDet(null);
      }
    } catch (e) {
      console.error("Failed to start mission");
    }
  };

  const handleStopMission = async () => {
    try {
      await fetch(`${API_BASE}/stop_mission`, { method: "POST" });
    } catch (e) {}
  };

  const handleReboot = async () => {
    try {
      await fetch(`${API_BASE}/reset`, { method: "POST" });
      window.location.reload();
    } catch (e) {
      window.location.reload();
    }
  };

  useEffect(() => {
    if (status === "STOPPED" || status === "IDLE") {
      setDroneDet(null);
      setTankDet(null);
    }
  }, [status]);

  const isRunning =
    status !== "IDLE" && status !== "FINISHED" && status !== "STOPPED";
  const canStart =
    status === "IDLE" || status === "STOPPED" || status === "FINISHED";

  const renderUnit = (type) => {
    const isDrone = type === "drone";
    const active = status?.startsWith(isDrone ? "AERIAL" : "GROUND");
    const det = isDrone ? droneDet : tankDet;
    const scanning = status?.includes("SCANNING") && active;

    return (
      <div
        // 1. CHANGED: p-6 -> p-10 (More padding)
        // 2. CHANGED: removed "scale-95" so it doesn't shrink
        // 3. CHANGED: ring-2 -> ring-4 (Thicker border when active)
        className={`glass p-3 rounded-3xl transition-all duration-700 ${
          active
            ? "ring-4 ring-green-500/50 shadow-2xl scale-100"
            : "opacity-70 scale-100"
        }`}
      >
        <h2 className="text-3xl font-bold flex items-center gap-3 mb-6">
          {isDrone ? "🚁 AERIAL UNIT" : "🚜 GROUND UNIT"}
        </h2>

        {/* 4. CHANGED: h-[300px] -> h-[500px] (Much taller image area) */}
        <div className="live-feed h-[700px] relative overflow-hidden rounded-2xl bg-black/50 border border-white/10">
          {scanning && <div className="scan-line" />}

          {det?.image ? (
            <img
              src={`data:image/jpeg;base64,${det.image}`}
              className="w-full h-full object-contain"
              alt="Live Feed"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 font-mono text-sm text-center px-4 tracking-widest">
              {isDrone ? "WAITING FOR IMAGE..." : "WAITING FOR IMAGE..."}
            </div>
          )}
        </div>

        <div className="mt-6 space-y-3">
          <div className="glass p-4 rounded-xl flex justify-between items-center border border-white/5">
            <span className="text-xs text-slate-400 uppercase font-bold tracking-widest">
              Insect Name
            </span>
            <span className="text-xl font-black text-green-400">
              {det?.class?.toUpperCase() || "---"}
            </span>
          </div>
          <div className="glass p-4 rounded-xl flex justify-between items-center border border-white/5">
            <span className="text-xs text-slate-400 uppercase font-bold tracking-widest">
              Confidence Level
            </span>
            <span className="text-xl font-black text-blue-400">
              {det?.confidence ? `${(det.confidence * 100).toFixed(1)}%` : "0%"}
            </span>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto text-white">
      <header className="flex justify-between items-end mb-8 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-black tracking-tighter">
            AGRI-TECH <span className="text-green-500 italic">OMAN</span>
          </h1>
          <p className="text-slate-400 font-mono text-sm tracking-widest uppercase">
            Hybrid Autonomous Detection 
          </p>
        </div>

        <div className="flex gap-4">
          <div
            className={`px-4 py-2 rounded-lg text-center min-w-[140px] border ${finished ? "bg-green-500/20 border-green-500" : "bg-blue-500/20 border-blue-500"}`}
          >
            <p
              className={`text-[10px] font-bold uppercase ${finished ? "text-green-500" : "text-blue-500"}`}
            >
              Mission Status
            </p>
            <p
              className={`font-black ${!finished && isRunning ? "animate-pulse" : ""}`}
            >
              {finished ? "COMPLETE" : status}
            </p>
          </div>

          <button
            onClick={handleReboot}
            disabled={isRunning}
            className={`glass px-6 py-2 rounded-lg text-xs font-bold border border-slate-700 ${isRunning ? "opacity-40 cursor-not-allowed" : "hover:bg-red-500/20 hover:text-red-500"}`}
          >
            REBOOT
          </button>

          <button
            onClick={handleStartMission}
            disabled={!canStart}
            className={`glass px-6 py-2 rounded-lg text-xs font-bold border border-slate-700 ${canStart ? "hover:bg-green-500/20 hover:text-green-400" : "opacity-40 cursor-not-allowed"}`}
          >
            START MISSION
          </button>

          {isRunning && (
            <button
              onClick={handleStopMission}
              className="glass px-6 py-2 rounded-lg text-xs font-bold hover:bg-red-500/20 hover:text-red-400 border border-slate-700"
            >
              STOP
            </button>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {renderUnit("drone")}
        {renderUnit("tank")}
      </div>

      <div className="glass p-6 rounded-2xl">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
            Centralized Mission Logs
          </h3>
          {finished && (
            <span className="text-green-500 font-bold text-xs animate-bounce">
              ✓ ALL SECTORS VERIFIED
            </span>
          )}
        </div>
        <div className="max-h-[400px] overflow-y-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-slate-500 text-xs uppercase border-b border-slate-800 sticky top-0 bg-[#0a0a0a]">
                <th className="pb-3 px-2">Timestamp</th>
                <th className="pb-3 px-2">Unit</th>
                <th className="pb-3 px-2">Detection</th>
                <th className="pb-3 px-2">Confidence</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {logs.map((l, i) => (
                <tr
                  key={i}
                  className="border-b border-slate-800/50 hover:bg-white/5 transition-colors"
                >
                  <td className="py-3 px-2 font-mono text-xs">
                    {new Date(l.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${l.source === "drone" ? "bg-blue-900 text-blue-200" : "bg-red-900 text-red-200"}`}
                    >
                      {l.source?.toUpperCase() ?? "UNKNOWN"}
                    </span>
                  </td>
                  <td className="py-3 px-2 font-bold">{l.insect}</td>
                  <td className="py-3 px-2 text-green-400">
                    {l.confidence
                      ? `${(l.confidence * 100).toFixed(1)}%`
                      : "---"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
