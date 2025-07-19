# Hebrew TTS Service Dockerfile
FROM python:3.10-slim

LABEL maintainer="strudel.marketing"
LABEL description="Hebrew Text-to-Speech service using Facebook MMS-TTS"
LABEL version="1.0.0"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        curl \
        && \
    rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU version (smaller and faster for CPU-only inference)
RUN pip install --no-cache-dir \
        torch==2.0.1+cpu \
        torchvision==0.15.2+cpu \
        torchaudio==2.0.2+cpu \
        -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other Python dependencies
RUN pip install --no-cache-dir \
        transformers>=4.33 \
        accelerate \
        scipy \
        fastapi \
        uvicorn[standard]

# Create app directory
WORKDIR /app

# Copy application code
COPY app.py .

# Create temp directory for audio processing
RUN mkdir -p /tmp

# Set environment variables
ENV PORT=80
ENV PYTHONUNBUFFERED=1
ENV TRANSFORMERS_CACHE=/app/.cache

# Create cache directory
RUN mkdir -p /app/.cache

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1"]
