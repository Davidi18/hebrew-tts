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

# Global variables for model and cache
model = None
tokenizer = None
_audio_cache = {}

@app.on_event("startup")
async def load_model():
    """Load the TTS model on startup"""
    global model, tokenizer
    try:
        print(f"Loading model: {MODEL_NAME}")
        model = VitsModel.from_pretrained(MODEL_NAME).to(device)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        torch.manual_seed(0)  # For deterministic output
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Model load failed: {e}")
        raise RuntimeError(f"Model load failed: {e}")

@app.get("/")
def root():
    """Root endpoint with service info"""
    return {
        "service": "Hebrew TTS Service",
        "model": MODEL_NAME,
        "endpoints": {
            "health": "/health",
            "speak": "/speak?text=YOUR_TEXT",
            "stats": "/stats"
        },
        "example": "curl 'https://your-domain.com/speak?text=שלום עולם' -o hello.mp3"
    }

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok" if model is not None else "loading",
        "model": MODEL_NAME,
        "cache_size": len(_audio_cache),
        "device": str(device)
    }

@app.get("/stats")
def stats():
    """Statistics endpoint"""
    return {
        "total_cached_texts": len(_audio_cache),
        "model_loaded": model is not None,
        "device": str(device),
        "recent_texts": list(_audio_cache.keys())[-5:] if _audio_cache else []
    }

@app.get("/speak")
def speak(text: str):
    """
    Convert Hebrew text to MP3 audio
    
    Args:
        text: Hebrew text to convert to speech
        
    Returns:
        MP3 audio file
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    # Check cache first
    if text in _audio_cache:
        print(f"Cache hit for: {text[:50]}...")
        mp3_bytes = _audio_cache[text]
    else:
        print(f"Generating speech for: {text[:50]}...")
        
        try:
            # Tokenize and generate
            inputs = tokenizer(text, return_tensors="pt").to(device)
            with torch.no_grad():
                wav = model(**inputs).waveform.squeeze().cpu().numpy()

            # Convert to MP3
            from scipy.io import wavfile
            wav_path = "/tmp/out.wav"
            mp3_path = "/tmp/out.mp3"
            
            wavfile.write(wav_path, rate=model.config.sampling_rate, data=wav)
            
            # Use ffmpeg to convert to MP3
            result = os.system(f"ffmpeg -y -loglevel error -i {wav_path} {mp3_path}")
            if result != 0:
                raise HTTPException(status_code=500, detail="Audio conversion failed")

            # Read MP3 file
            with open(mp3_path, "rb") as f:
                mp3_bytes = f.read()

            # Cleanup
            if os.path.exists(wav_path):
                os.remove(wav_path)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
            
            # Cache the result
            _audio_cache[text] = mp3_bytes
            print(f"Speech generated and cached. Cache size: {len(_audio_cache)}")
            
        except Exception as e:
            print(f"Error generating speech: {e}")
            raise HTTPException(status_code=500, detail=f"Speech generation failed: {str(e)}")

    # Return MP3 file
    headers = {
        "Content-Disposition": 'attachment; filename="speech.mp3"',
        "Content-Type": "audio/mpeg"
    }
    return Response(content=mp3_bytes, media_type="audio/mpeg", headers=headers)

@app.get("/clear-cache")
def clear_cache():
    """Clear the audio cache"""
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
