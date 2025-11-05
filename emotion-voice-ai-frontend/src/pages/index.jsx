import { useEffect, useRef, useState } from "react";

const ORCH_URL = process.env.NEXT_PUBLIC_ORCH_URL?.replace(/\/$/, "");

export default function Home() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [llmText, setLlmText] = useState("");
  const [recording, setRecording] = useState(false);
  const [recSupported, setRecSupported] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    setRecSupported(typeof window !== "undefined" && !!navigator.mediaDevices?.getUserMedia);
  }, []);

  
  useEffect(() => {
    if (!result?.llm_response?.message) return;
    let i = 0;
    const full = result.llm_response.message;
    setLlmText("");
    const id = setInterval(() => {
      i++;
      setLlmText(full.slice(0, i));
      if (i >= full.length) clearInterval(id);
    }, 18); 
    return () => clearInterval(id);
  }, [result?.llm_response?.message]);

  async function handleSubmitAudio(file) {
    if (!ORCH_URL) {
      setError("Frontend missing NEXT_PUBLIC_ORCH_URL. Add it to .env.local and restart.");
      return;
    }
    setBusy(true);
    setError("");
    setResult(null);
    setLlmText("");

    try {
      const form = new FormData();
      form.append("audio", file, file.name || "recording.wav");

      const res = await fetch(`${ORCH_URL}/e2e`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) throw new Error(`Orchestrator responded ${res.status}`);
      const json = await res.json();
      if (json.error) throw new Error(json.error);

      setResult(json);
    } catch (e) {
      setError(e.message || "Request failed");
    } finally {
      setBusy(false);
    }
  }

  
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        // Some backends prefer wav/ogg — orchestrator accepts file by content-type, so it's fine.
        const file = new File([blob], "recording.webm", { type: "audio/webm" });
        await handleSubmitAudio(file);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch (e) {
      setError("Mic not available: " + e.message);
    }
  }

  function stopRecording() {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }

  function onFileChange(e) {
    const f = e.target.files?.[0];
    if (f) handleSubmitAudio(f);
  }

  
  const emo = result?.audio_emotion?.emotion || result?.fusion?.unified_emotion;
  const dist = result?.audio_emotion?.distribution || {};
  const diar = result?.speakers?.segments || [];
  const transcript = result?.transcript?.text || "";
  const sentiment = result?.text_sentiment;

  return (
    <div className="wrap">
      <header className="hero">
        <h1>Emotion Voice AI</h1>
        <p className="sub">End-to-end VAD → Diarization → STT → Emotions → Fusion → LLM</p>
      </header>

      <section className="card">
        <h2>1) Give me audio</h2>
        <div className="ioRow">
          <label className={`btn ${busy ? "disabled" : ""}`}>
            <input type="file" accept="audio/*" onChange={onFileChange} disabled={busy} hidden />
            Upload audio
          </label>

          {recSupported ? (
            recording ? (
              <button className="btn danger pulse" onClick={stopRecording}>
                ⏺️ Recording… click to stop
              </button>
            ) : (
              <button className="btn" disabled={busy} onClick={startRecording}>
                🎙️ Record from mic
              </button>
            )
          ) : (
            <span className="hint">Mic not supported in this browser/OS</span>
          )}

          {busy && <div className="spinner" />}
        </div>

        {!!error && <div className="error">⚠️ {error}</div>}
      </section>

      {result && (
        <>
          <section className="grid">
            <div className="card">
              <h2>2) LLM response</h2>
              <div className="lyrics">
                <TypeCursor text={llmText} />
              </div>
              <div className="policy">Policy: <strong>{result?.fusion?.policy || "—"}</strong></div>
            </div>

            <div className="card">
              <h2>3) Emotions (audio)</h2>
              <div className="chips">
                <Chip label={emo || "unknown"} />
                {!!result?.audio_emotion?.confidence && (
                  <span className="small">conf: {result.audio_emotion.confidence}</span>
                )}
              </div>
              <BarChart data={dist} />
              <div className="triples">
                <Badge label="Valence" value={fmt(result?.audio_emotion?.valence)} />
                <Badge label="Arousal" value={fmt(result?.audio_emotion?.arousal)} />
                <Badge label="Dominance" value={fmt(result?.audio_emotion?.dominance)} />
              </div>
            </div>

            <div className="card">
              <h2>4) Text sentiment</h2>
              {sentiment ? (
                <>
                  <div className="chips"><Chip label={sentiment.label} /></div>
                  <div className="bar">
                    <span>Score</span>
                    <Progress value={(sentiment.score ?? 0) * 100} />
                  </div>
                  <div className="bar">
                    <span>Sarcasm</span>
                    <Progress value={(sentiment.sarcasm_probability ?? 0) * 100} />
                  </div>
                </>
              ) : (
                <div className="muted">No sentiment available</div>
              )}
            </div>

            <div className="card">
              <h2>5) Speakers</h2>
              {diar.length ? (
                <>
                  <Timeline segments={diar} />
                  <ul className="list">
                    {diar.map((s, i) => (
                      <li key={i}>
                        <b>{s.speaker}</b> — {s.start.toFixed(2)}s → {s.end.toFixed(2)}s
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <div className="muted">No diarization returned</div>
              )}
            </div>

            <div className="card wide">
              <h2>6) Transcript</h2>
              <p className="transcript">{transcript || "—"}</p>
            </div>
          </section>
        </>
      )}

      <style jsx>{`
        .wrap { max-width: 1100px; margin: 0 auto; padding: 24px; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial; color: #0f172a; }
        .hero { text-align: center; margin-bottom: 18px; }
        h1 { margin: 0 0 6px; font-size: 28px; letter-spacing: .2px; }
        .sub { margin: 0; color: #475569; font-size: 14px; }
        .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 16px; box-shadow: 0 1px 12px rgba(2,6,23,.04); }
        .grid { display: grid; gap: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-top: 16px; }
        .wide { grid-column: 1 / -1; }
        .ioRow { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
        .btn { appearance: none; border: 1px solid #334155; background: #0ea5e9; color: white; padding: 10px 14px; border-radius: 10px; cursor: pointer; font-weight: 600; }
        .btn.disabled { opacity: .6; cursor: not-allowed; }
        .btn.danger { background: #ef4444; border-color: #7f1d1d; }
        .pulse { animation: pulse 1.3s infinite; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.03); } 100% { transform: scale(1); } }
        .spinner { width: 18px; height: 18px; border-radius: 50%; border: 3px solid #bae6fd; border-top-color: #0284c7; animation: spin 0.9s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .error { margin-top: 12px; color: #b91c1c; background: #fee2e2; border: 1px solid #fecaca; padding: 10px; border-radius: 10px; }
        .lyrics { min-height: 96px; white-space: pre-wrap; line-height: 1.6; font-size: 16px; background: #f8fafc; border: 1px dashed #cbd5e1; padding: 12px; border-radius: 10px; }
        .policy { margin-top: 8px; font-size: 13px; color: #475569; }
        .chips { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
        .chip { background: #f1f5f9; border: 1px solid #e2e8f0; padding: 6px 10px; border-radius: 999px; font-weight: 600; font-size: 13px; }
        .small { font-size: 12px; color: #64748b; }
        .triples { display: flex; gap: 10px; margin-top: 8px; }
        .badge { display: inline-flex; flex-direction: column; gap: 2px; font-size: 12px; background: #f8fafc; padding: 8px 10px; border-radius: 10px; border: 1px solid #e2e8f0; }
        .badge b { font-size: 14px; }
        .bar { display: grid; grid-template-columns: 80px 1fr; gap: 12px; align-items: center; margin: 8px 0; }
        .progress { width: 100%; height: 10px; background: #e2e8f0; border-radius: 999px; overflow: hidden; border: 1px solid #cbd5e1; }
        .progress > span { display: block; height: 100%; background: linear-gradient(90deg, #22c55e, #84cc16); }
        .muted { color: #64748b; }
        .list { list-style: none; padding: 0; margin: 10px 0 0; max-height: 180px; overflow: auto; }
        .list li { padding: 6px 0; border-bottom: 1px dashed #e2e8f0; font-size: 14px; }
        .timeline { position: relative; height: 12px; background: #e5e7eb; border-radius: 999px; overflow: hidden; border: 1px solid #cbd5e1; margin-top: 6px; }
        .seg { position: absolute; top: 0; bottom: 0; border-radius: 999px; background: linear-gradient(90deg, #06b6d4, #3b82f6); opacity: .9; }
        .transcript { white-space: pre-wrap; background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px; border-radius: 10px; font-size: 15px; }
        .hint { font-size: 12px; color: #64748b; }
      `}</style>
    </div>
  );
}



function TypeCursor({ text }) {
  return (
    <span className="type">
      {text}
      <span className="cursor">|</span>
      <style jsx>{`
        .cursor { display: inline-block; width: 1px; background: #0f172a; margin-left: 2px; animation: blink 1s steps(1) infinite; height: 1.1em; vertical-align: text-bottom; }
        @keyframes blink { 0%, 50% { opacity: 1 } 50.01%, 100% { opacity: 0 } }
      `}</style>
    </span>
  );
}

function Chip({ label }) {
  if (!label) return null;
  return <span className="chip">{label}</span>;
}

function Badge({ label, value }) {
  return (
    <div className="badge">
      <span>{label}</span>
      <b>{value ?? "—"}</b>
    </div>
  );
}

function Progress({ value = 0 }) {
  const v = Math.max(0, Math.min(100, Number.isFinite(value) ? value : 0));
  return (
    <div className="progress">
      <span style={{ width: `${v}%` }} />
    </div>
  );
}

function fmt(x) {
  if (x === undefined || x === null) return "—";
  const n = Number(x);
  if (!Number.isFinite(n)) return "—";
  return n.toFixed(3);
}

function Timeline({ segments }) {
  const total = Math.max(...segments.map((s) => s.end), 1);
  return (
    <>
      <div className="timeline">
        {segments.map((s, i) => {
          const left = (s.start / total) * 100;
          const width = Math.max(1, ((s.end - s.start) / total) * 100);
          return <div key={i} className="seg" style={{ left: `${left}%`, width: `${width}%` }} title={`${s.speaker}: ${s.start.toFixed(2)}–${s.end.toFixed(2)}s`} />;
        })}
      </div>
      <div className="small" style={{ marginTop: 6 }}>duration ≈ {total.toFixed(1)}s</div>
    </>
  );
}

function BarChart({ data }) {
  const entries = Object.entries(data || {});
  if (!entries.length) return <div className="muted">No distribution</div>;
  const max = Math.max(...entries.map(([, v]) => v || 0), 1);
  return (
    <div>
      {entries.map(([k, v]) => {
        const pct = Math.round(((v || 0) / max) * 100);
        return (
          <div key={k} style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 10, alignItems: "center", margin: "4px 0" }}>
            <span style={{ fontSize: 13 }}>{k}</span>
            <div className="progress"><span style={{ width: `${pct}%`, background: "linear-gradient(90deg,#6366f1,#22d3ee)" }} /></div>
          </div>
        );
      })}
    </div>
  );
}
