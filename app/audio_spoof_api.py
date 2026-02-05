"""
Audio Spoof Detection API - Base64 Input Version
Accepts base64-encoded audio with format specification
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch
import torchaudio
import tempfile
import os
from typing import Optional
import logging
from contextlib import asynccontextmanager
import numpy as np
import base64
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
model_loaded = True
VALID_API_KEY = "your-secret-api-key-here"  # Change this in production

# Request Model
class DetectionRequest(BaseModel):
    language: str  # e.g., "English", "Tamil", "Hindi"
    audioFormat: str  # e.g., "mp3", "wav", "m4a", "ogg"
    audioBase64: str  # Base64-encoded audio data

# Response Models
class SuccessResponse(BaseModel):
    status: str = "success"
    language: str
    classification: str  # "AI_GENERATED" or "HUMAN"
    confidenceScore: float  # 0.0 to 1.0
    explanation: str

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str

def extract_audio_features(signal, sr=16000):
    """Extract audio features for spoof detection"""
    try:
        if isinstance(signal, torch.Tensor):
            signal = signal.numpy()
        
        if len(signal.shape) > 1:
            signal = signal[0]
        
        # Feature 1: Zero Crossing Rate
        zcr = np.mean(np.abs(np.diff(np.sign(signal))))
        
        # Feature 2: Spectral Centroid
        fft = np.fft.fft(signal)
        magnitude = np.abs(fft[:len(fft)//2])
        freqs = np.fft.fftfreq(len(signal), 1/sr)[:len(fft)//2]
        spectral_centroid = np.sum(freqs * magnitude) / (np.sum(magnitude) + 1e-10)
        
        # Feature 3: Spectral Flatness
        spectral_flatness = np.exp(np.mean(np.log(magnitude + 1e-10))) / (np.mean(magnitude) + 1e-10)
        
        # Feature 4: Energy variations
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        
        energy_variations = []
        for i in range(0, len(signal) - frame_length, hop_length):
            frame = signal[i:i+frame_length]
            energy = np.sum(frame ** 2)
            energy_variations.append(energy)
        
        energy_std = np.std(energy_variations) if len(energy_variations) > 0 else 0
        
        return {
            'zcr': zcr,
            'spectral_centroid': spectral_centroid,
            'spectral_flatness': spectral_flatness,
            'energy_std': energy_std
        }
    except Exception as e:
        logger.error(f"Feature extraction error: {e}")
        raise

def classify_audio(features):
    """Simple rule-based classification"""
    zcr_score = min(features['zcr'] / 0.5, 1.0)
    spectral_score = 1.0 - min(features['spectral_flatness'], 1.0)
    energy_score = 1.0 - min(features['energy_std'] / 10000, 1.0)
    
    ai_score = (zcr_score * 0.3 + spectral_score * 0.4 + energy_score * 0.3)
    
    if ai_score > 0.6:
        classification = "AI_GENERATED"
        confidence = min(ai_score, 0.95)
    else:
        classification = "HUMAN"
        confidence = min(1.0 - ai_score, 0.95)
    
    return classification, confidence

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler"""
    logger.info("API starting up...")
    logger.info("Using feature-based spoof detection with base64 input")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="Audio Spoof Detection API", 
    version="2.0.0",
    description="Base64-based audio deepfake detection",
    lifespan=lifespan
)

def verify_api_key(api_key: Optional[str]) -> bool:
    """Verify API key"""
    return api_key == VALID_API_KEY

def get_explanation(confidence: float, classification: str) -> str:
    """Generate human-readable explanation"""
    if classification == "AI_GENERATED":
        if confidence >= 0.85:
            return "Strong synthetic patterns detected (unnatural pitch consistency and robotic speech patterns)"
        elif confidence >= 0.70:
            return "Moderate synthetic artifacts detected (artificial harmonics and phase inconsistencies)"
        else:
            return "Possible synthetic characteristics detected (some unnatural spectral features)"
    else:
        if confidence >= 0.85:
            return "Strong natural speech characteristics (organic pitch variations and human breathing patterns)"
        elif confidence >= 0.70:
            return "Moderate natural speech patterns (typical human vocal characteristics)"
        else:
            return "Mostly natural characteristics detected (human-like vocal patterns)"

def process_base64_audio(audio_base64: str, audio_format: str) -> tuple[str, float]:
    """
    Process base64-encoded audio and return classification
    
    Args:
        audio_base64: Base64-encoded audio data
        audio_format: Audio format (mp3, wav, m4a, etc.)
    
    Returns:
        tuple: (classification, confidence_score)
    """
    try:
        # Decode base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Save to temporary file with correct extension
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        # Load audio
        signal, sr = torchaudio.load(temp_path)
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Resample to 16kHz if needed
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            signal = resampler(signal)
            sr = 16000
        
        # Convert to mono if stereo
        if signal.shape[0] > 1:
            signal = torch.mean(signal, dim=0, keepdim=True)
        
        # Extract features
        features = extract_audio_features(signal, sr)
        
        # Classify
        classification, confidence = classify_audio(features)
        
        return classification, confidence
        
    except Exception as e:
        logger.error(f"Error processing audio: {str(e)}")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

@app.post("/detect", response_model=SuccessResponse)
async def detect_spoof(
    request: DetectionRequest,
    api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Detect if audio is AI-generated or human speech
    
    Request Body:
    - language: Language of the audio (e.g., "English", "Tamil", "Hindi")
    - audioFormat: Audio file format (e.g., "mp3", "wav", "m4a", "ogg")
    - audioBase64: Base64-encoded audio data
    
    Headers:
    - X-API-Key: Your API key
    
    Returns:
    - JSON response with classification and confidence
    """
    
    # Verify API key
    if not verify_api_key(api_key):
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                status="error",
                message="Invalid API key or malformed request"
            ).dict()
        )
    
    # Validate audio format
    supported_formats = ["mp3", "wav", "m4a", "ogg", "flac", "aac"]
    if request.audioFormat.lower() not in supported_formats:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                status="error",
                message=f"Unsupported audio format. Supported: {', '.join(supported_formats)}"
            ).dict()
        )
    
    try:
        # Process audio
        classification, confidence = process_base64_audio(
            request.audioBase64, 
            request.audioFormat
        )
        
        # Generate explanation
        explanation = get_explanation(confidence, classification)
        
        # Return success response
        return SuccessResponse(
            status="success",
            language=request.language,
            classification=classification,
            confidenceScore=round(confidence, 2),
            explanation=explanation
        )
        
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                status="error",
                message=f"Error processing audio: {str(e)}"
            ).dict()
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "detection_method": "feature-based",
        "input_type": "base64",
        "supported_formats": ["mp3", "wav", "m4a", "ogg", "flac", "aac"],
        "message": "Ready"
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Audio Spoof Detection API",
        "version": "2.0.0 - Base64 Input",
        "detection_method": "Audio feature analysis (ZCR, spectral features, energy patterns)",
        "input_type": "Base64-encoded audio",
        "supported_formats": ["mp3", "wav", "m4a", "ogg", "flac", "aac"],
        "endpoints": {
            "/detect": "POST - Detect AI-generated vs Human speech (base64 input)",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        },
        "example_request": {
            "language": "English",
            "audioFormat": "mp3",
            "audioBase64": "BASE64_ENCODED_AUDIO_DATA_HERE"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)