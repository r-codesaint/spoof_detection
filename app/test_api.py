"""
Test suite for Audio Spoof Detection API
Run with: pytest test_api.py -v
"""

import pytest
import requests
from io import BytesIO
import wave
import struct
import math

# Test configuration
API_URL = "http://127.0.0.1:8000"
VALID_API_KEY = "your-secret-api-key-here"
INVALID_API_KEY = "wrong-key"

def generate_test_audio(duration=1.0, sample_rate=16000, frequency=440):
    """
    Generate a simple sine wave audio file for testing
    
    Args:
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
        frequency: Frequency of sine wave in Hz
    
    Returns:
        BytesIO object containing WAV file
    """
    num_samples = int(duration * sample_rate)
    
    # Generate sine wave
    samples = []
    for i in range(num_samples):
        sample = math.sin(2 * math.pi * frequency * i / sample_rate)
        samples.append(int(sample * 32767))
    
    # Create WAV file in memory
    buffer = BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write samples
        for sample in samples:
            wav_file.writeframes(struct.pack('h', sample))
    
    buffer.seek(0)
    return buffer

class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test that health endpoint responds"""
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_model_loaded(self):
        """Test that model is loaded"""
        response = requests.get(f"{API_URL}/health")
        data = response.json()
        assert "model_loaded" in data
        # May be True or False depending on if model loaded successfully

class TestRootEndpoint:
    """Test root endpoint"""
    
    def test_root_endpoint(self):
        """Test that root endpoint returns API info"""
        response = requests.get(f"{API_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data

class TestDetectEndpoint:
    """Test detection endpoint"""
    
    def test_detect_with_valid_audio(self):
        """Test detection with valid audio and API key"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check response structure
        assert result["status"] == "success"
        assert result["language"] == "English"
        assert result["classification"] in ["AI_GENERATED", "HUMAN"]
        assert 0.0 <= result["confidenceScore"] <= 1.0
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0
    
    def test_detect_without_api_key(self):
        """Test that missing API key is rejected"""
        audio = generate_test_audio()
        
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            files=files,
            data=data
        )
        
        assert response.status_code == 401
        result = response.json()
        assert result["status"] == "error"
        assert "Invalid API key" in result["message"]
    
    def test_detect_with_invalid_api_key(self):
        """Test that invalid API key is rejected"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": INVALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 401
        result = response.json()
        assert result["status"] == "error"
    
    def test_detect_with_different_languages(self):
        """Test detection with different languages"""
        languages = ["Tamil", "English", "Hindi", "Malayalam", "Telugu"]
        
        for language in languages:
            audio = generate_test_audio()
            
            headers = {"X-API-Key": VALID_API_KEY}
            files = {"audio": ("test.wav", audio, "audio/wav")}
            data = {"language": language}
            
            response = requests.post(
                f"{API_URL}/detect",
                headers=headers,
                files=files,
                data=data
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["language"] == language
            assert result["status"] == "success"
    
    def test_detect_without_audio_file(self):
        """Test that missing audio file is rejected"""
        headers = {"X-API-Key": VALID_API_KEY}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            data=data
        )
        
        # FastAPI will return 422 for missing required field
        assert response.status_code == 422
    
    def test_detect_without_language(self):
        """Test that missing language parameter is rejected"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files
        )
        
        # FastAPI will return 422 for missing required field
        assert response.status_code == 422
    
    def test_detect_with_invalid_file_type(self):
        """Test that non-audio files are rejected"""
        # Create a fake text file
        fake_file = BytesIO(b"This is not an audio file")
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.txt", fake_file, "text/plain")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result["status"] == "error"
        assert "Invalid file type" in result["message"]

class TestResponseFormat:
    """Test response format compliance"""
    
    def test_success_response_format(self):
        """Test that success response has all required fields"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "Tamil"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        result = response.json()
        
        # Required fields
        required_fields = ["status", "language", "classification", "confidenceScore", "explanation"]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Field types
        assert isinstance(result["status"], str)
        assert isinstance(result["language"], str)
        assert isinstance(result["classification"], str)
        assert isinstance(result["confidenceScore"], (int, float))
        assert isinstance(result["explanation"], str)
    
    def test_error_response_format(self):
        """Test that error response has correct format"""
        headers = {"X-API-Key": INVALID_API_KEY}
        files = {"audio": ("test.wav", generate_test_audio(), "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        result = response.json()
        
        # Required fields for error
        assert "status" in result
        assert "message" in result
        assert result["status"] == "error"
        assert isinstance(result["message"], str)
    
    def test_confidence_score_range(self):
        """Test that confidence score is between 0 and 1"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        result = response.json()
        confidence = result["confidenceScore"]
        
        assert 0.0 <= confidence <= 1.0, f"Confidence score {confidence} out of range"
    
    def test_classification_values(self):
        """Test that classification is one of the expected values"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        result = response.json()
        classification = result["classification"]
        
        assert classification in ["AI_GENERATED", "HUMAN"], \
            f"Invalid classification: {classification}"

class TestEdgeCases:
    """Test edge cases and potential issues"""
    
    def test_very_short_audio(self):
        """Test with very short audio (0.1 seconds)"""
        audio = generate_test_audio(duration=0.1)
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        # Should still work, even if accuracy may be lower
        assert response.status_code in [200, 500]  # May succeed or fail
    
    def test_long_audio(self):
        """Test with longer audio (5 seconds)"""
        audio = generate_test_audio(duration=5.0)
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "English"}
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        assert response.status_code == 200
    
    def test_special_characters_in_language(self):
        """Test with special characters in language field"""
        audio = generate_test_audio()
        
        headers = {"X-API-Key": VALID_API_KEY}
        files = {"audio": ("test.wav", audio, "audio/wav")}
        data = {"language": "தமிழ் (Tamil)"}  # Tamil script
        
        response = requests.post(
            f"{API_URL}/detect",
            headers=headers,
            files=files,
            data=data
        )
        
        # Should accept any string for language
        assert response.status_code == 200
        result = response.json()
        assert result["language"] == "தமிழ் (Tamil)"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])