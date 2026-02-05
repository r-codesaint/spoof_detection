"""
Advanced client examples for Audio Spoof Detection API
Includes base64 encoding, batch processing, and error handling
"""

import requests
import json
import base64
from pathlib import Path
from typing import Dict, List
import time

API_URL = "http://localhost:8000/detect"
API_KEY = "your-secret-api-key-here"

class SpoofDetectionClient:
    """Client wrapper for the Audio Spoof Detection API"""
    
    def __init__(self, api_url: str = API_URL, api_key: str = API_KEY):
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {"X-API-Key": self.api_key}
    
    def detect_from_file(self, audio_path: str, language: str) -> Dict:
        """
        Detect spoof from audio file
        
        Args:
            audio_path: Path to audio file
            language: Language of the audio
            
        Returns:
            API response dict
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': (audio_path, audio_file, 'audio/wav')}
                data = {'language': language}
                
                response = requests.post(
                    self.api_url,
                    headers=self.headers,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"File not found: {audio_path}"
            }
    
    def detect_from_bytes(self, audio_bytes: bytes, language: str, filename: str = "audio.wav") -> Dict:
        """
        Detect spoof from audio bytes
        
        Args:
            audio_bytes: Audio file as bytes
            language: Language of the audio
            filename: Filename to use (for content type detection)
            
        Returns:
            API response dict
        """
        try:
            files = {'audio': (filename, audio_bytes, 'audio/wav')}
            data = {'language': language}
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def detect_from_base64(self, audio_base64: str, language: str) -> Dict:
        """
        Detect spoof from base64-encoded audio
        
        Args:
            audio_base64: Base64-encoded audio data
            language: Language of the audio
            
        Returns:
            API response dict
        """
        try:
            audio_bytes = base64.b64decode(audio_base64)
            return self.detect_from_bytes(audio_bytes, language)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Base64 decode failed: {str(e)}"
            }
    
    def batch_detect(self, audio_files: List[tuple], delay: float = 0.5) -> List[Dict]:
        """
        Batch process multiple audio files
        
        Args:
            audio_files: List of tuples (audio_path, language)
            delay: Delay between requests in seconds
            
        Returns:
            List of API responses
        """
        results = []
        
        for audio_path, language in audio_files:
            print(f"Processing: {audio_path} ({language})")
            result = self.detect_from_file(audio_path, language)
            results.append({
                "file": audio_path,
                "result": result
            })
            
            # Avoid rate limiting
            if delay > 0:
                time.sleep(delay)
        
        return results
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = requests.get(
                self.api_url.replace("/detect", "/health"),
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


def print_result(result: Dict, title: str = "Result"):
    """Pretty print API result"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)
    print(json.dumps(result, indent=2))
    print('=' * 60)


# Example usage
if __name__ == "__main__":
    client = SpoofDetectionClient()
    
    # Check API health
    print("Checking API health...")
    if client.health_check():
        print("✅ API is healthy")
    else:
        print("❌ API is not responding")
        exit(1)
    
    # Example 1: Detect from file
    print("\n📁 Example 1: Detect from file")
    result = client.detect_from_file("sample_tamil.wav", "Tamil")
    print_result(result, "Tamil Audio Detection")
    
    # Example 2: Detect from base64
    print("\n🔢 Example 2: Detect from base64")
    try:
        with open("sample_english.wav", "rb") as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
        
        result = client.detect_from_base64(audio_base64, "English")
        print_result(result, "English Audio Detection (Base64)")
    except FileNotFoundError:
        print("sample_english.wav not found")
    
    # Example 3: Batch processing
    print("\n📦 Example 3: Batch processing")
    audio_files = [
        ("sample_tamil.wav", "Tamil"),
        ("sample_english.wav", "English"),
        ("sample_hindi.wav", "Hindi"),
    ]
    
    results = client.batch_detect(audio_files, delay=0.5)
    
    print("\n" + "=" * 60)
    print("Batch Processing Summary")
    print("=" * 60)
    for item in results:
        status = item["result"].get("status", "unknown")
        classification = item["result"].get("classification", "N/A")
        confidence = item["result"].get("confidenceScore", 0)
        
        print(f"\n{item['file']}:")
        print(f"  Status: {status}")
        if status == "success":
            print(f"  Classification: {classification}")
            print(f"  Confidence: {confidence}")
        else:
            print(f"  Error: {item['result'].get('message', 'Unknown error')}")
    
    # Example 4: Error handling
    print("\n\n⚠️  Example 4: Error handling")
    
    # Invalid file
    result = client.detect_from_file("nonexistent.wav", "English")
    print_result(result, "Invalid File Test")
    
    # Invalid API key
    print("\n🔑 Testing with invalid API key...")
    bad_client = SpoofDetectionClient(api_key="wrong-key")
    result = bad_client.detect_from_file("sample_tamil.wav", "Tamil")
    print_result(result, "Invalid API Key Test")
    
    # Example 5: Interpretation helper
    print("\n\n📊 Example 5: Result interpretation")
    result = client.detect_from_file("sample_tamil.wav", "Tamil")
    
    if result.get("status") == "success":
        classification = result.get("classification")
        confidence = result.get("confidenceScore")
        
        print(f"\nAudio Classification: {classification}")
        print(f"Confidence Score: {confidence}")
        
        if classification == "AI_GENERATED":
            if confidence >= 0.85:
                print("⚠️  High confidence: This is very likely AI-generated speech")
            elif confidence >= 0.70:
                print("⚠️  Moderate confidence: This is probably AI-generated speech")
            else:
                print("⚠️  Low confidence: This might be AI-generated speech")
        else:
            if confidence >= 0.85:
                print("✅ High confidence: This is very likely human speech")
            elif confidence >= 0.70:
                print("✅ Moderate confidence: This is probably human speech")
            else:
                print("✅ Low confidence: This might be human speech")
        
        print(f"\nExplanation: {result.get('explanation')}")