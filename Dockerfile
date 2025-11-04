FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir supervisor

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir \
    fastapi uvicorn pydantic numpy requests \
    torch==2.2.2 torchaudio==2.2.2 \
    librosa==0.10.1 soundfile==0.12.1 tensorflow==2.15.0 \
    openai-whisper==20231117 ffmpeg-python==0.2.0 \
    transformers==4.42.0 \
    python-multipart \
    pyannote.audio==2.1.1

EXPOSE 8000

ENV VAD_URL=http://127.0.0.1:8001 \
    DIAR_URL=http://127.0.0.1:8002 \
    STT_URL=http://127.0.0.1:8003 \
    EMO_URL=http://127.0.0.1:8004 \
    TEXT_URL=http://127.0.0.1:8005 \
    FUSION_URL=http://127.0.0.1:8006 \
    LLM_URL=http://127.0.0.1:8007

ENV HF_TOKEN=""

COPY supervisord.conf /etc/supervisor/supervisord.conf

CMD ["supervisord","-c","/etc/supervisor/supervisord.conf"]
