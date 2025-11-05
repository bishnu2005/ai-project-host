FROM python:3.10-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

# Upgrade build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Torch (CPU wheels)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
    torch==2.2.2 torchaudio==2.2.2

# Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Ports are managed by supervisord/services; keep default exposed
EXPOSE 8000

# Env (override in Render)
ENV VAD_URL=http://127.0.0.1:8001 \
    DIAR_URL=http://127.0.0.1:8002 \
    STT_URL=http://127.0.0.1:8003 \
    EMO_URL=http://127.0.0.1:8004 \
    TEXT_URL=http://127.0.0.1:8005 \
    FUSION_URL=http://127.0.0.1:8006 \
    LLM_URL=http://127.0.0.1:8007 \
    HF_TOKEN=""

# Supervisord to run all services
RUN pip install --no-cache-dir supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf

CMD ["supervisord","-c","/etc/supervisor/supervisord.conf"]
