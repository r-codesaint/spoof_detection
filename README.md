# Audio Spoof Detection API

FastAPI-based API for detecting AI-generated vs Human speech using SpeechBrain's anti-spoofing model.

## Features

- ✅ Detects AI-generated (synthetic) vs Human speech
- ✅ Returns confidence scores (0.0 to 1.0)
- ✅ Supports multiple languages (Tamil, English, Hindi, Malayalam, Telugu, etc.)
- ✅ API key authentication
- ✅ Clear error handling
- ✅ Automatic audio preprocessing (resampling, mono conversion)

## Response Format

### Success Response
```json
{
  "status": "success",
  "language": "Tamil",
  "classification": "AI_GENERATED",
  "confidenceScore": 0.91,
  "explanation": "Unnatural pitch consistency and robotic speech patterns detected"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Invalid API key or malformed request"
}
```

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure API key:**
Edit `audio_spoof_api.py` and change:
```python
VALID_API_KEY = "your-secret-api-key-here"
```

## Running the Server

```bash
python audio_spoof_api.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### 1. POST /detect
Detect if audio is AI-generated or human

**Headers:**
- `X-API-Key`: Your API key

**Form Data:**
- `audio`: Audio file (wav, mp3, etc.)
- `language`: Language name (e.g., "Tamil", "English")

**Example with cURL:**
```bash
curl -X POST "http://localhost:8000/detect" \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "audio=@sample_audio.wav" \
  -F "language=Tamil"
```

**Example with Python:**
```python
import requests

headers = {"X-API-Key": "your-secret-api-key-here"}
files = {"audio": open("sample_audio.wav", "rb")}
data = {"language": "Tamil"}

response = requests.post(
    "http://localhost:8000/detect",
    headers=headers,
    files=files,
    data=data
)

print(response.json())
```

### 2. GET /health
Check API health status

```bash
curl http://localhost:8000/health
```

### 3. GET /docs
Interactive API documentation (Swagger UI)

Visit: `http://localhost:8000/docs`

## Classification Logic

The model outputs two labels:
- `bonafide` → Mapped to `HUMAN`
- `spoof` → Mapped to `AI_GENERATED`

## Confidence Score Interpretation

| Confidence | Meaning |
|------------|---------|
| 0.85 - 1.0 | Strong confidence in classification |
| 0.70 - 0.84 | Moderate confidence |
| 0.0 - 0.69 | Low confidence (uncertain) |

## Explanation Messages

The API provides context-aware explanations:

**AI_GENERATED (High Confidence):**
- "Strong synthetic patterns detected (unnatural pitch consistency and robotic speech patterns)"

**AI_GENERATED (Moderate Confidence):**
- "Moderate synthetic artifacts detected (artificial harmonics and phase inconsistencies)"

**HUMAN (High Confidence):**
- "Strong natural speech characteristics (organic pitch variations and human breathing patterns)"

## Supported Audio Formats

- WAV (recommended)
- MP3
- FLAC
- OGG
- Any format supported by torchaudio

The API automatically:
- Resamples to 16kHz (required by the model)
- Converts stereo to mono
- Normalizes audio levels

## Language Support

The `language` parameter is **metadata only** and doesn't affect detection accuracy. The spoof detection model works on acoustic features, not linguistic content.

Supported languages include:
- Tamil
- English
- Hindi
- Malayalam
- Telugu
- Any other language

## Model Information

This API uses **SpeechBrain's ASVspoof ECAPA-TDNN** model:
- Model: `speechbrain/asvspoof-ecapa-tdnn`
- Trained on: ASVspoof 2019 dataset
- Architecture: ECAPA-TDNN (Emphasized Channel Attention, Propagation and Aggregation in TDNN)
- Purpose: Anti-spoofing / Deepfake detection

## Error Handling

The API returns appropriate HTTP status codes:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid file type) |
| 401 | Unauthorized (invalid API key) |
| 500 | Internal server error |
| 503 | Service unavailable (model not loaded) |

## Production Deployment

For production use:

1. **Use environment variables for API key:**
```python
import os
VALID_API_KEY = os.getenv("API_KEY", "default-key")
```

2. **Use a production ASGI server:**
```bash
# Install gunicorn
pip install gunicorn

# Run with multiple workers
gunicorn audio_spoof_api:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

3. **Add rate limiting:**
```bash
pip install slowapi
```

4. **Use HTTPS:**
Deploy behind a reverse proxy (nginx) with SSL certificates

## Testing

Use the provided `client_example.py`:

```bash
python client_example.py
```

## Performance Considerations

- **First request may be slow** (model loading)
- Subsequent requests are fast (~100-500ms per audio file)
- For high-traffic scenarios, consider:
  - Multiple worker processes
  - GPU acceleration (if available)
  - Request queuing

## Limitations

1. The model is trained primarily on English speech
2. Performance may vary for very short clips (<2 seconds)
3. Background noise can affect accuracy
4. Some modern AI voices (2024+) may be harder to detect

## Troubleshooting

**Model fails to load:**
- Ensure you have internet connection (first run downloads model)
- Check disk space (~500MB needed)

**Low accuracy:**
- Ensure audio quality is good (no heavy compression)
- Try resampling to 16kHz before sending
- Remove background noise if possible

**Slow responses:**
- Use a GPU if available
- Reduce audio file size
- Increase worker count

## License

This API uses SpeechBrain models which are licensed under Apache 2.0.

## Support

For issues or questions:
1. Check the `/docs` endpoint for API documentation
2. Review error messages in the API response
3. Check server logs for detailed error information