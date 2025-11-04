from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
import numpy as np
import librosa
import tempfile
import os

app = FastAPI(title="Emotion Voice AI - Audio Emotion Recognition Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMOTIONS = ["neutral", "calm", "happy", "sad", "angry", "fear", "disgust", "surprise"]

@app.on_event("startup")
def load_emotion_model():
    global model
    model_path = os.getenv("EMOTION_MODEL_PATH", "/models/emotion_model1.h5")
    print(f"🎧 Loading emotion model from: {model_path}")
    model = load_model(model_path)
    print("✅ Emotion model loaded successfully.")


def extract_mfcc(file_path, n_mfcc=60, max_len=174):
    """Extract MFCC features for emotion recognition."""
    try:
        audio, sr = librosa.load(file_path, sr=22050)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
        if mfcc.shape[1] < max_len:
            pad_width = max_len - mfcc.shape[1]
            mfcc = np.pad(mfcc, ((0, 0), (0, pad_width)), mode="constant")
        elif mfcc.shape[1] > max_len:
            mfcc = mfcc[:, :max_len]
        mfcc = mfcc.reshape(1, n_mfcc, max_len, 1)
        return mfcc
    except Exception as e:
        raise RuntimeError(f"MFCC extraction failed: {e}")


@app.post("/predict")
async def predict_emotion(file: UploadFile = File(...)):
    """Predict emotion from uploaded audio file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        features = extract_mfcc(tmp_path)

        preds = model.predict(features)[0]
        top_idx = int(np.argmax(preds))
        top_emotion = EMOTIONS[top_idx]

        valence = round(float(preds[top_idx] * 2 - 1), 3)
        arousal = round(float(np.mean(preds) * 2 - 1), 3)
        dominance = round(float(np.std(preds) * 2 - 1), 3)

        os.remove(tmp_path)

        return {
            "status": "success",
            "emotion": top_emotion,
            "confidence": round(float(preds[top_idx]), 3),
            "distribution": {EMOTIONS[i]: round(float(p), 3) for i, p in enumerate(preds)},
            "valence": valence,
            "arousal": arousal,
            "dominance": dominance
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def root():
    return {"message": "Emotion recognition service is running "}
