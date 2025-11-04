# Data Schemas

## VAD POST /infer (multipart)
- form field `file`: WAV/PCM audio (16 kHz preferred)

Response:
{
  "sample_rate": 16000,
  "segments": [{"start": 0.12, "end": 1.95, "confidence": 0.98}, ...]
}

## Diarization POST /infer (multipart)
- form `file`: WAV audio
- form `segments_json`: JSON string of VAD segments

Response:
{
  "speakers":[{"speaker":"S0","start":0.12,"end":1.95,"conf":0.88},...],
  "rttm":"SPEAKER file 1 0.12 1.83 <NA> <NA> S0 <NA> <NA>\n..."
}

## STT POST /transcribe (multipart)
- form `file`: WAV audio

Response:
{
  "text":"hello world",
  "language":"en",
  "segments":[{"start":0.1,"end":0.9,"text":"hello","avg_logprob":-0.1,"no_speech_prob":0.01}],
  "confidence":0.85
}

## Emotion (Audio) POST /infer (multipart)
- form `file`: WAV audio

Response:
{
  "discrete":{"angry":0.05,"sad":0.12,"happy":0.62,"neutral":0.21},
  "vad":{"valence":0.40,"arousal":0.15,"dominance":-0.05},
  "features":{"rms":0.018,"pitch_mean":196.2}
}

## Text Sentiment POST /infer (json)
Request:
{"text":"I am not happy about this."}

Response:
{
  "sentiment":{"label":"NEGATIVE","score":0.91},
  "sarcasm_prob":0.33,"toxicity_prob":0.04
}

## Fusion POST /infer (json)
Request:
{
  "audio_emotion": {...},
  "text_sentiment": {...},
  "speakers":[{"speaker":"S0","start":0,"end":2.3}],
  "transcript":{"text":"...", "segments":[...]}
}

Response:
{
  "emotion_embedding":[0.11,-0.03,0.55],
  "summary":{"overall":"happy","speaker_map":{"S0":1.2}},
  "policy":"calm_response"
}

## LLM POST /respond (json)
Request:
{ "context": { "transcript":"...", "emotion":{...}, "policy":"empathy" } }

Response:
{ "action":"reply", "message":"...", "priority":"normal" }

## Orchestrator POST /e2e (multipart)
- form `file`: WAV audio
Response: aggregated JSON including all stages + final LLM message.
