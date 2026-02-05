FROM python:3.10-slim

# Keep stdout/stderr unbuffered
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies from the app folder
COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./

EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "audio_spoof_api:app", "--host", "0.0.0.0", "--port", "8000"]
