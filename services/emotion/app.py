from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
import numpy as np, librosa, tempfile, os

app = FastAPI(title="Emotion Voice AI - Audio Emotion Recognition Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

EMOTIONS = ["neutral","calm","happy","sad","angry","fear","disgust","surprise"]

@app.on_event("startup")
def load_emotion_model():
    global model
    model_path = os.getenv("EMOTION_MODEL_PATH", "/models/emotion_model1.h5")
    model = load_model(model_path)

def extract_mfcc(file_path, n_mfcc=60, max_len=174):
    audio, sr = librosa.load(file_path, sr=22050)
    mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
    if mfcc.shape[1] < max_len:
        mfcc = np.pad(mfcc, ((0,0),(0,max_len - mfcc.shape[1])), mode="constant")
    elif mfcc.shape[1] > max_len:
        mfcc = mfcc[:, :max_len]
    return mfcc.reshape(1, n_mfcc, max_len, 1)

@app.post("/predict")
async def predict_emotion(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        feats = extract_mfcc(tmp_path)
        preds = model.predict(feats)[0]
        os.remove(tmp_path)
        idx = int(np.argmax(preds))
        return {
            "status": "success",
            "emotion": EMOTIONS[idx],
            "confidence": float(preds[idx]),
            "distribution": {EMOTIONS[i]: float(p) for i,p in enumerate(preds)},
            "valence": float(preds[idx]*2-1),
            "arousal": float(np.mean(preds)*2-1),
            "dominance": float(np.std(preds)*2-1)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/analyze")
async def analyze_alias(file: UploadFile = File(...)):
    return await predict_emotion(file)

@app.get("/")
def root():
    return {"message": "Emotion recognition service is running"}
