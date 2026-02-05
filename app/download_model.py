"""
Manual Model Downloader for SpeechBrain ASVspoof Model
Use this if automatic download fails due to network/auth issues
"""

import os
import requests
from pathlib import Path
from tqdm import tqdm

# Model files to download
MODEL_FILES = {
    "hyperparams.yaml": "https://huggingface.co/speechbrain/asvspoof-ecapa-tdnn/resolve/main/hyperparams.yaml",
    "embedding_model.ckpt": "https://huggingface.co/speechbrain/asvspoof-ecapa-tdnn/resolve/main/embedding_model.ckpt",
    "label_encoder.txt": "https://huggingface.co/speechbrain/asvspoof-ecapa-tdnn/resolve/main/label_encoder.txt",
    "classifier.ckpt": "https://huggingface.co/speechbrain/asvspoof-ecapa-tdnn/resolve/main/classifier.ckpt",
}

SAVE_DIR = "pretrained_models/asvspoof-ecapa-tdnn"

def download_file(url: str, dest_path: str):
    """Download a file with progress bar"""
    print(f"Downloading: {os.path.basename(dest_path)}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(dest_path, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        print(f"✓ Downloaded: {os.path.basename(dest_path)}")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download {os.path.basename(dest_path)}: {e}")
        return False

def main():
    """Download all model files"""
    print("="*60)
    print("SpeechBrain ASVspoof Model - Manual Downloader")
    print("="*60)
    
    # Create directory
    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"\nSaving to: {os.path.abspath(SAVE_DIR)}\n")
    
    success_count = 0
    for filename, url in MODEL_FILES.items():
        dest_path = os.path.join(SAVE_DIR, filename)
        
        # Skip if already exists
        if os.path.exists(dest_path):
            print(f"⊙ Already exists: {filename}")
            success_count += 1
            continue
        
        # Download
        if download_file(url, dest_path):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"Download Complete: {success_count}/{len(MODEL_FILES)} files")
    print("="*60)
    
    if success_count == len(MODEL_FILES):
        print("✓ All files downloaded successfully!")
        print("\nYou can now run: python audio_spoof_api.py")
    else:
        print("⚠ Some files failed to download.")
        print("\nAlternative method:")
        print("1. Go to: https://huggingface.co/speechbrain/asvspoof-ecapa-tdnn")
        print("2. Click 'Files and versions'")
        print(f"3. Manually download the files to: {os.path.abspath(SAVE_DIR)}")
        print("\nRequired files:")
        for filename in MODEL_FILES.keys():
            status = "✓" if os.path.exists(os.path.join(SAVE_DIR, filename)) else "✗"
            print(f"  {status} {filename}")

if __name__ == "__main__":
    main()