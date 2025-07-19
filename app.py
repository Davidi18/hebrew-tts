import os
import torch
from transformers import VitsModel, AutoTokenizer
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

app = FastAPI(
    title="Hebrew TTS Service",
    description="Text-to-Speech service for Hebrew using Facebook MMS-TTS model",
    version="1.0.0"
)

MODEL_NAME = "facebook/mms-tts-heb"
device = torch.device("cpu")

model = None
tokenizer = None
_audio_cache = {}

@app.on_event("startup")
async def load_model():
    global model, tokenizer
    try:
        print(f"Loading model: {MODEL_NAME}")
        print(f"PyTorch version: {torch.__version__}")
        print(f"Device: {device}")
        
        model = VitsModel.from_pretrained(MODEL_NAME).to(device)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        torch.manual_seed(0)
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Model load failed: {e}")
        # Don't raise - let the service start but mark as not ready
        print("Service starting without model - will retry on first request")

@app.get("/")
def root():
    return {
        "service": "Hebrew TTS Service",
        "model": MODEL_NAME,
        "model_loaded": model is not None,
        "pytorch_version": torch.__version__,
        "endpoints": {
            "health": "/health",
            "speak": "/speak?text=YOUR_TEXT",
            "stats": "/stats"
        },
        "example": "curl 'https://your-domain.com/speak?text=שלום עולם' -o hello.mp3"
    }

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model": MODEL_NAME,
        "cache_size": len(_audio_cache),
        "device": str(device),
        "pytorch_version": torch.__version__
    }

@app.get("/stats")
def stats():
    return {
        "total_cached_texts": len(_audio_cache),
        "model_loaded": model is not None,
        "device": str(device),
        "pytorch_version": torch.__version__,
        "recent_texts": list(_audio_cache.keys())[-5:] if _audio_cache else []
    }

@app.get("/speak")
def speak(text: str):
    global model, tokenizer
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    # Try to load model if not loaded
    if model is None:
        try:
            print("Attempting to load model on demand...")
            model = VitsModel.from_pretrained(MODEL_NAME).to(device)
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            torch.manual_seed(0)
            print("Model loaded successfully on demand!")
        except Exception as e:
            print(f"On-demand model load failed: {e}")
            raise HTTPException(status_code=503, detail=f"Model not available: {str(e)}")

    if text in _audio_cache:
        print(f"Cache hit for: {text[:50]}...")
        mp3_bytes = _audio_cache[text]
    else:
        print(f"Generating speech for: {text[:50]}...")
        
        try:
            inputs = tokenizer(text, return_tensors="pt").to(device)
            with torch.no_grad():
                wav = model(**inputs).waveform.squeeze().cpu().numpy()

            from scipy.io import wavfile
            wav_path = "/tmp/out.wav"
            mp3_path = "/tmp/out.mp3"
            
            wavfile.write(wav_path, rate=model.config.sampling_rate, data=wav)
            
            result = os.system(f"ffmpeg -y -loglevel error -i {wav_path} {mp3_path}")
            if result != 0:
                raise HTTPException(status_code=500, detail="Audio conversion failed")

            with open(mp3_path, "rb") as f:
                mp3_bytes = f.read()

            if os.path.exists(wav_path):
                os.remove(wav_path)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            
            _audio_cache[text] = mp3_bytes
            print(f"Speech generated and cached. Cache size: {len(_audio_cache)}")
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

    headers = {
        "Content-Disposition": 'attachment; filename="speech.mp3"',
        "Content-Type": "audio/mpeg"
    }
    return Response(content=mp3_bytes, media_type="audio/mpeg", headers=headers)

@app.get("/clear-cache")
def clear_cache():
    global _audio_cache
    cache_size = len(_audio_cache)
    _audio_cache = {}
    return {
        "message": f"Cache cleared. Removed {cache_size} items.",
        "cache_size": 0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
