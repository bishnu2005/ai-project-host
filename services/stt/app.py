from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import whisper
import tempfile
import os

app = FastAPI(title="Emotion Voice AI - STT Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_model():
    global model
    model_size = os.getenv("STT_MODEL_SIZE", "small")  
    print(f"🎙️ Loading Whisper model: {model_size}")
    try:
        model = whisper.load_model(model_size)
        print("✅ Whisper model loaded successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Whisper model: {str(e)}")

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio (.wav) to text.
    Returns JSON with text and timestamps.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        result = model.transcribe(tmp_path)

        os.remove(tmp_path)

        return {
            "status": "success",
            "text": result.get("text", "").strip(),
            "segments": result.get("segments", []),
            "language": result.get("language", "unknown")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@app.get("/")
def root():
    return {"message": "STT service is running "}
