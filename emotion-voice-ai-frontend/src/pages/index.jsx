import { useEffect, useRef, useState } from "react";

// ✅ Updated: hard-set your backend URL for deployment
const ORCH_URL = "https://ai-project-host-5.onrender.com".replace(/\/$/, "");

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
      setError("Frontend missing backend URL.");
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
      {/* ——— rest of your JSX unchanged ——— */}
    </div>
  );
}

/* keep all your helper components (TypeCursor, Chip, etc.) below unchanged */
