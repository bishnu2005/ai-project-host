from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch
import torchaudio
import io
import tempfile
import os

app = FastAPI(title="Emotion Voice AI - VAD Service")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
(get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils


@app.post("/detect")
async def detect_voice(file: UploadFile = File(...)):
    """
    Detects human voice segments in an uploaded audio file.
    Returns timestamps for detected speech.
    """
    try:
        
        audio_bytes = await file.read()
        wav, sr = torchaudio.load(io.BytesIO(audio_bytes))

        
        if sr != 16000:
            wav = torchaudio.transforms.Resample(sr, 16000)(wav)
            sr = 16000

        
        if wav.shape[0] > 1:
            wav = torch.mean(wav, dim=0, keepdim=True)

        
        speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=sr)

        return {
            "status": "success",
            "num_segments": len(speech_timestamps),
            "segments": speech_timestamps
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@app.get("/")
def root():
    return {"message": "VAD Service is running "}
