import { useEffect, useState, useRef } from "react";
import "./command-center.css";

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [status, setStatus] = useState("IDLE");
  const [droneDet, setDroneDet] = useState(null);
  const [tankDet, setTankDet] = useState(null);
  const [videoDet, setVideoDet] = useState(null);
  const [videoStatus, setVideoStatus] = useState("IDLE");
  const [videoFile, setVideoFile] = useState(null);
  const [videoUploadState, setVideoUploadState] = useState("");
  const [logs, setLogs] = useState([]);
  const [finished, setFinished] = useState(false);
  const [page, setPage] = useState("dashboard");
  const [insects, setInsects] = useState([]);
  const [isLoadingInsects, setIsLoadingInsects] = useState(false);
  const socketRef = useRef(null);

  useEffect(() => {
    const connect = () => {
      const ws = new WebSocket("ws://127.0.0.1:8000/ws");

      ws.onopen = () => console.log("Connected to Backend");

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setStatus(data.status);
        setFinished(data.status === "FINISHED" || data.status === "VIDEO_FINISHED");

        if (data.last_detection) {
          const det = data.last_detection;

          // 1. Update Live View
          if (det.source === "drone") {
            setDroneDet(det);
          } else if (det.source === "tank") {
            setTankDet(det);
          } else if (det.source === "video") {
            setVideoDet(det);
            setVideoStatus(data.status);
            if (data.status === "VIDEO_PROCESSING") {
              setVideoUploadState("processing");
            } else if (data.status === "VIDEO_FINISHED") {
              setVideoUploadState("completed");
            } else if (data.status === "VIDEO_ERROR") {
              setVideoUploadState("error");
            }
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

  const handleShowInsects = async () => {
    setPage("insects");
    setIsLoadingInsects(true);

    try {
      const response = await fetch(`${API_BASE}/insects/list`);
      if (!response.ok) throw new Error("Failed to load insect library");
      const data = await response.json();
      setInsects(data);
    } catch (error) {
      console.error("Failed to load insect library", error);
      setInsects([]);
    } finally {
      setIsLoadingInsects(false);
    }
  };

  const handleBackToDashboard = () => {
    setPage("dashboard");
    setVideoFile(null);
    setVideoDet(null);
    setVideoUploadState("");
    setVideoStatus("IDLE");
  };

  const handleShowVideoPage = () => {
    setPage("video");
    setVideoDet(null);
    setVideoUploadState("");
    setVideoStatus("IDLE");
  };

  const handleVideoFileChange = (event) => {
    setVideoFile(event.target.files?.[0] ?? null);
  };

  const handleUploadVideo = async () => {
    if (!videoFile) return;

    setVideoUploadState("uploading");
    setVideoDet(null);
    setVideoStatus("VIDEO_PROCESSING");
    setLogs([]);

    const formData = new FormData();
    formData.append("file", videoFile);

    try {
      const response = await fetch(`${API_BASE}/upload_video`, {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (data.status === "started") {
        setVideoUploadState("processing");
      } else {
        setVideoUploadState("error");
        console.error("Video upload failed", data);
      }
    } catch (error) {
      setVideoUploadState("error");
      console.error("Video upload failed", error);
    }
  };

  const handleStopVideo = async () => {
    try {
      const response = await fetch(`${API_BASE}/stop_video`, { method: "POST" });
      const data = await response.json();
      if (data.status === "stopped") {
        setVideoUploadState("stopped");
        setVideoStatus("VIDEO_STOPPED");
      }
    } catch (error) {
      console.error("Failed to stop video", error);
    }
  };

  const isVideoProcessing =
    videoUploadState === "processing" || videoStatus === "VIDEO_PROCESSING";

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
            INSECTS-DETECTION <span className="text-green-500 italic">OMAN</span>
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
            onClick={page === "insects" ? handleBackToDashboard : handleShowInsects}
            className="glass px-6 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:bg-yellow-500/20 hover:text-yellow-400"
          >
            {page === "insects" ? "DASHBOARD" : "INSECTS"}
          </button>

          <button
            onClick={page === "video" ? handleBackToDashboard : handleShowVideoPage}
            className="glass px-6 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:bg-purple-500/20 hover:text-purple-400"
          >
            {page === "video" ? "DASHBOARD" : "VIDEO"}
          </button>

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

      {page === "insects" ? (
        <div className="glass p-6 rounded-2xl">
          <div className="flex flex-col gap-4 mb-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-2xl font-black">Insect Library</h2>
              <p className="text-slate-400 text-sm mt-1">
                Browse the insect images and names.
              </p>
            </div>
            <button
              onClick={handleBackToDashboard}
              className="glass px-5 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:bg-white/5"
            >
              BACK TO DASHBOARD
            </button>
          </div>

          {isLoadingInsects ? (
            <div className="text-slate-300">Loading insect library...</div>
          ) : insects.length === 0 ? (
            <div className="text-slate-400">No insects found. Please add images and metadata in the backend.</div>
          ) : (
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
  {insects.map((insect) => (
    <div key={insect.id} className="rounded-3xl overflow-hidden border border-slate-200 bg-white text-slate-900 shadow-sm">
      <div className="h-64 bg-white flex items-center justify-center overflow-hidden">
        {insect.image ? (
          <img
            src={`${API_BASE}${insect.image}`}
            alt={insect.name}
            loading="lazy"
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="text-slate-500 text-sm">No image available</div>
        )}
      </div>
      <div className="p-4">
        <h3 className="text-lg font-bold">{insect.name}</h3>
      </div>
    </div>
  ))}
</div>
          )}
        </div>
      ) : page === "video" ? (
        <div className="glass p-6 rounded-2xl">
          <div className="flex flex-col gap-4 mb-6 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-2xl font-black">Video Detection</h2>
              <p className="text-slate-400 text-sm mt-1">
                Upload a video and watch detections stream in real time.
              </p>
            </div>
            <button
              onClick={handleBackToDashboard}
              className="glass px-5 py-2 rounded-lg text-xs font-bold border border-slate-700 hover:bg-white/5"
            >
              BACK TO DASHBOARD
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="glass p-6 rounded-2xl border border-slate-700">
              <label className="block text-slate-400 text-xs uppercase tracking-widest mb-2">Select video file</label>
              <input
                type="file"
                accept="video/*"
                onChange={handleVideoFileChange}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 text-slate-100 p-3"
              />
              <div className="flex flex-col gap-3">
                <button
                  onClick={handleUploadVideo}
                  disabled={!videoFile || videoUploadState === "uploading" || videoUploadState === "processing"}
                  className="mt-4 glass px-5 py-3 rounded-lg text-xs font-bold border border-slate-700 hover:bg-green-500/20"
                >
                  {videoUploadState === "uploading" || videoUploadState === "processing"
                    ? "Uploading..."
                    : "Start Video Detection"}
                </button>
                <button
                  onClick={handleStopVideo}
                  disabled={!isVideoProcessing}
                  className="glass px-5 py-3 rounded-lg text-xs font-bold border border-slate-700 hover:bg-red-500/20"
                >
                  Stop Video
                </button>
              </div>
              {videoUploadState === "error" && (
                <p className="mt-3 text-sm text-red-400">Upload failed. Please try again.</p>
              )}
              {videoUploadState === "processing" && (
                <p className="mt-3 text-sm text-green-400">Video is processing. Watch the live feed below.</p>
              )}
              {videoUploadState === "stopped" && (
                <p className="mt-3 text-sm text-yellow-300">Video processing was stopped.</p>
              )}
            </div>

            <div className="glass p-6 rounded-2xl border border-slate-700 lg:col-span-2">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Video Detection Preview</h3>
                <span className="text-xs text-slate-400">Status: {videoStatus}</span>
              </div>
              <div className="live-feed h-[420px] relative overflow-hidden rounded-2xl bg-black/50 border border-white/10">
                {videoDet?.image ? (
                  <img
                    src={`data:image/jpeg;base64,${videoDet.image}`}
                    className="w-full h-full object-contain"
                    alt="Video Detection"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-500 font-mono text-sm text-center px-4 tracking-widest">
                    UPLOAD A VIDEO TO SEE FRAME DETECTIONS
                  </div>
                )}
              </div>
              <div className="mt-6 space-y-3">
                <div className="glass p-4 rounded-xl flex justify-between items-center border border-white/10">
                  <span className="text-xs text-slate-400 uppercase font-bold tracking-widest">Detected Insect</span>
                  <span className="text-xl font-black text-green-400">{videoDet?.class?.toUpperCase() || "---"}</span>
                </div>
                <div className="glass p-4 rounded-xl flex justify-between items-center border border-white/10">
                  <span className="text-xs text-slate-400 uppercase font-bold tracking-widest">Frame Progress</span>
                  <span className="text-xl font-black text-blue-400">{videoDet?.progress ? `${videoDet.progress}%` : "--"}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="glass p-6 rounded-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Video Detection Logs</h3>
            </div>
            <div className="max-h-[400px] overflow-y-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="text-slate-500 text-xs uppercase border-b border-slate-800 sticky top-0 bg-[#0a0a0a]">
                    <th className="pb-3 px-2">Timestamp</th>
                    <th className="pb-3 px-2">Source</th>
                    <th className="pb-3 px-2">Detection</th>
                    <th className="pb-3 px-2">Confidence</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {logs
                    .filter((l) => l.source === "video")
                    .map((l, i) => (
                      <tr
                        key={i}
                        className="border-b border-slate-800/50 hover:bg-white/5 transition-colors"
                      >
                        <td className="py-3 px-2 font-mono text-xs">
                          {new Date(l.timestamp).toLocaleTimeString()}
                        </td>
                        <td className="py-3 px-2">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-900 text-purple-200">
                            VIDEO
                          </span>
                        </td>
                        <td className="py-3 px-2 font-bold">{l.insect}</td>
                        <td className="py-3 px-2 text-green-400">
                          {l.confidence ? `${(l.confidence * 100).toFixed(1)}%` : "---"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <>
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
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            l.source === "drone"
                              ? "bg-blue-900 text-blue-200"
                              : l.source === "tank"
                              ? "bg-red-900 text-red-200"
                              : l.source === "video"
                              ? "bg-purple-900 text-purple-200"
                              : "bg-slate-700 text-slate-200"
                          }`}
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
        </>
      )}
    </div>
  );
}