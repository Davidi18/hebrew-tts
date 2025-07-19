FROM python:3.10-slim

LABEL maintainer="strudel.marketing"
LABEL description="Hebrew Text-to-Speech service using Facebook MMS-TTS"
LABEL version="1.0.1"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        curl \
        && \
    rm -rf /var/lib/apt/lists/*

# Install compatible NumPy first (fixes the compatibility issue)
RUN pip install --no-cache-dir "numpy<2.0"

# Install newer PyTorch that's compatible (>= 2.1)
RUN pip install --no-cache-dir \
        torch==2.1.0+cpu \
        torchvision==0.16.0+cpu \
        torchaudio==2.1.0+cpu \
        -f https://download.pytorch.org/whl/cpu/torch_stable.html

# Install other dependencies with compatible versions
RUN pip install --no-cache-dir \
        transformers>=4.33 \
        accelerate \
        "scipy<1.13" \
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
ENV HF_HOME=/app/.cache

# Create cache directory
RUN mkdir -p /app/.cache

# Expose port
EXPOSE 80

# Health check (more forgiving for model loading)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:80/health || exit 1

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1"]
