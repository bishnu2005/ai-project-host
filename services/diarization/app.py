from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pyannote.audio import Pipeline
import torch
import tempfile
import os

app = FastAPI(title="Emotion Voice AI - Diarization Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_model():
    global diarization_pipeline
    HF_TOKEN = os.getenv("HF_TOKEN")
    diarization_pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1",
                                                    use_auth_token=HF_TOKEN)  
    print(" Diarization model loaded successfully.")


@app.post("/diarize")
async def diarize_audio(file: UploadFile = File(...)):
   
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        diarization = diarization_pipeline(tmp_path)

        results = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            results.append({
                "speaker": speaker,
                "start": round(turn.start, 2),
                "end": round(turn.end, 2)
            })

        os.remove(tmp_path)

        return {
            "status": "success",
            "num_speakers": len(set([r["speaker"] for r in results])),
            "segments": results
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.get("/")
def root():
    return {"message": "Diarization service is running "}
