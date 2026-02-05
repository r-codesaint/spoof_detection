"""
Example client for Audio Spoof Detection API
"""

import requests
import json

# API configuration
API_URL = "http://localhost:8000/detect"
API_KEY = "your-secret-api-key-here"  # Must match the server

def detect_spoof(audio_file_path: str, language: str):
    """
    Send audio file to spoof detection API
    
    Args:
        audio_file_path: Path to audio file
        language: Language of the audio (e.g., "Tamil", "English")
    
    Returns:
        dict: API response
    """
    
    # Prepare headers with API key
    headers = {
        "X-API-Key": API_KEY
    }
    
    # Prepare files and data
    with open(audio_file_path, 'rb') as audio_file:
        files = {
            'audio': (audio_file_path, audio_file, 'audio/wav')
        }
        data = {
            'language': language
        }
        
        # Make request
        response = requests.post(API_URL, headers=headers, files=files, data=data)
    
    return response.json()

# Example usage
if __name__ == "__main__":
    # Example 1: Tamil audio
    print("=" * 50)
    print("Example 1: Detecting Tamil audio")
    print("=" * 50)
    
    try:
        result = detect_spoof("sample_tamil.wav", "Tamil")
        print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print("sample_tamil.wav not found. Please provide a valid audio file.")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 50)
    print("Example 2: Detecting English audio")
    print("=" * 50)
    
    try:
        result = detect_spoof("sample_english.wav", "English")
        print(json.dumps(result, indent=2))
    except FileNotFoundError:
        print("sample_english.wav not found. Please provide a valid audio file.")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example with error (invalid API key)
    print("\n" + "=" * 50)
    print("Example 3: Invalid API key")
    print("=" * 50)
    
    old_key = API_KEY
    API_KEY = "wrong-key"
    
    try:
        result = detect_spoof("sample_tamil.wav", "Tamil")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        API_KEY = old_key