import os
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Emotion Voice AI - Orchestrator", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

VAD_URL  = os.getenv("VAD_URL",  "http://127.0.0.1:8001")
DIAR_URL = os.getenv("DIAR_URL", "http://127.0.0.1:8002")
STT_URL  = os.getenv("STT_URL",  "http://127.0.0.1:8003")
EMO_URL  = os.getenv("EMO_URL",  "http://127.0.0.1:8004")
TEXT_URL = os.getenv("TEXT_URL", "http://127.0.0.1:8005")
FUSION_URL = os.getenv("FUSION_URL", "http://127.0.0.1:8006")
LLM_URL    = os.getenv("LLM_URL",    "http://127.0.0.1:8007")

@app.get("/")
def root():
    return {"service": "orchestrator", "status": "ready"}

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.post("/e2e")
async def full_pipeline(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        files = {"file": (audio.filename or "audio.wav", audio_bytes, audio.content_type or "audio/wav")}

        try:
            vad_resp = requests.post(f"{VAD_URL}/detect", files=files, timeout=60).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"VAD Service failed: {e}")

        try:
            diar_resp = requests.post(f"{DIAR_URL}/diarize", files=files, timeout=120).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Diarization Service failed: {e}")

        try:
            stt_resp = requests.post(f"{STT_URL}/transcribe", files=files, timeout=300).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"STT Service failed: {e}")

        text_full = " ".join(seg.get("text", "") for seg in stt_resp.get("segments", [])) or stt_resp.get("text", "")

        # EMOTION: the endpoint is /predict (not /analyze)
        try:
            emo_resp = requests.post(f"{EMO_URL}/predict", files=files, timeout=120).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Emotion Service failed: {e}")

        try:
            text_payload = {"text": text_full}
            text_resp = requests.post(f"{TEXT_URL}/analyze", json=text_payload, timeout=60).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Text Sentiment Service failed: {e}")

        try:
            fusion_payload = {
                "audio_emotion": emo_resp.get("emotion", "neutral"),
                "audio_valence": float(emo_resp.get("valence", 0.0)),
                "audio_arousal": float(emo_resp.get("arousal", 0.0)),
                "text_emotion": text_resp.get("label", "neutral"),
                "text_score": float(text_resp.get("score", 0.0)),
            }
            fusion_resp = requests.post(f"{FUSION_URL}/fuse", json=fusion_payload, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"Fusion Service failed: {e}")

        try:
            llm_payload = {
                "context": text_full,
                "emotion": fusion_resp.get("unified_emotion", "neutral"),
                "policy": fusion_resp.get("policy", "calm_response"),
            }
            llm_resp = requests.post(f"{LLM_URL}/generate", json=llm_payload, timeout=60).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=502, detail=f"LLM Service failed: {e}")

        return {
            "speech_segments": vad_resp,
            "speakers": diar_resp,
            "transcript": stt_resp,
            "audio_emotion": emo_resp,
            "text_sentiment": text_resp,
            "fusion": fusion_resp,
            "llm_response": llm_resp,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator failed: {e}")
