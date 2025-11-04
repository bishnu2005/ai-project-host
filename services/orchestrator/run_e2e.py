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

VAD_URL = os.getenv("VAD_URL", "http://vad:8000")
DIAR_URL = os.getenv("DIAR_URL", "http://diarization:8000")
STT_URL = os.getenv("STT_URL", "http://stt:8000")
EMO_URL = os.getenv("EMO_URL", "http://emotion:8000")
TEXT_URL = os.getenv("TEXT_URL", "http://text_sentiment:8000")
FUSION_URL = os.getenv("FUSION_URL", "http://fusion:8000")
LLM_URL = os.getenv("LLM_URL", "http://llm:8000")

@app.post("/e2e")
async def full_pipeline(audio: UploadFile = File(...)):
    try:
        audio_bytes = await audio.read()
        files = {"file": (audio.filename, audio_bytes, audio.content_type)}

       
        try:
            vad_resp = requests.post(f"{VAD_URL}/detect", files=files, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"VAD Service failed: {e}")

        
        try:
            diar_resp = requests.post(f"{DIAR_URL}/diarize", files=files, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Diarization Service failed: {e}")

        
        try:
            stt_resp = requests.post(f"{STT_URL}/transcribe", files=files, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"STT Service failed: {e}")

        text_full = " ".join(seg["text"] for seg in stt_resp.get("segments", []))

        
        try:
            emo_resp = requests.post(f"{EMO_URL}/analyze", files=files, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Emotion Service failed: {e}")

        
        try:
            text_payload = {"text": text_full}
            text_resp = requests.post(f"{TEXT_URL}/analyze", json=text_payload, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Text Sentiment Service failed: {e}")

        
        try:
            fusion_payload = {
                "audio_emotion": emo_resp["emotion"],
                "audio_valence": emo_resp["valence"],
                "audio_arousal": emo_resp["arousal"],
                "text_emotion": text_resp["label"],
                "text_score": text_resp["score"]
            }
            fusion_resp = requests.post(f"{FUSION_URL}/fuse", json=fusion_payload, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Fusion Service failed: {e}")

        
        try:
            llm_payload = {
                "context": text_full,
                "emotion": fusion_resp["unified_emotion"],
                "policy": fusion_resp["policy"]
            }
            llm_resp = requests.post(f"{LLM_URL}/generate", json=llm_payload, timeout=30).json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"LLM Service failed: {e}")

        return {
            "speech_segments": vad_resp,
            "speakers": diar_resp,
            "transcript": stt_resp,
            "audio_emotion": emo_resp,
            "text_sentiment": text_resp,
            "fusion": fusion_resp,
            "llm_response": llm_resp
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Orchestrator failed: {str(e)}")

@app.get("/")
def root():
    return {"service": "orchestrator", "status": "ready"}
