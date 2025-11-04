from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline

app = FastAPI(title="Emotion Voice AI - Text Sentiment", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

try:
    sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    print(" Sentiment analysis model loaded successfully.")
except Exception as e:
    raise RuntimeError(f"Failed to load text sentiment model: {e}")

class TextInput(BaseModel):
    text: str

class SentimentOutput(BaseModel):
    label: str
    score: float
    sarcasm_probability: float

@app.post("/analyze", response_model=SentimentOutput)
async def analyze(input_data: TextInput):
    text = input_data.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text provided")

    try:
        result = sentiment_analyzer(text)[0]
        label = result["label"]
        score = float(result["score"])

        sarcasm_prob = round(abs(score - 0.5) * 2 * 0.1, 3)  

        return SentimentOutput(label=label, score=score, sarcasm_probability=sarcasm_prob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in sentiment analysis: {e}")

@app.get("/")
def root():
    return {"service": "text_sentiment", "status": "ready", "model": "distilbert-sst2"}
