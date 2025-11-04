from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np

app = FastAPI(title="Emotion Voice AI - Fusion Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class EmotionInput(BaseModel):
    audio_emotion: str
    audio_valence: float
    audio_arousal: float
    text_emotion: str
    text_score: float

class FusionOutput(BaseModel):
    unified_emotion: str
    emotion_embedding: list
    policy: str

@app.post("/fuse", response_model=FusionOutput)
async def fuse_emotions(data: EmotionInput):
    try:
        weights = np.array([
            data.audio_valence,
            data.audio_arousal,
            data.text_score
        ])
        weights = np.clip(weights, -1, 1)
        unified_value = float(np.mean(weights))
        unified_emotion = (
            data.text_emotion if abs(data.text_score) > abs(data.audio_valence)
            else data.audio_emotion
        )

        policy = "calm_response"
        if unified_emotion.lower() in ["angry", "fear", "disgust"]:
            policy = "empathy_response"
        elif unified_emotion.lower() in ["sad"]:
            policy = "reassurance_response"
        elif unified_emotion.lower() in ["happy"]:
            policy = "supportive_response"

        embedding = weights.tolist()
        return FusionOutput(
            unified_emotion=unified_emotion,
            emotion_embedding=embedding,
            policy=policy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fusion failed: {e}")

@app.get("/")
def root():
    return {"service": "fusion", "status": "ready"}
