#!/usr/bin/env python3
"""
Script to download images for the blog post
Run this script to download all images locally
"""

import requests
import os
from pathlib import Path

def download_image(url, filename):
    """Download image from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to download {url}: {str(e)}")
        return False

def main():
    """Download all images"""
    images_to_download = [
    ]
    
    print(f"📥 Downloading {len(images_to_download)} images...")
    
    success_count = 0
    for img in images_to_download:
        if download_image(img["url"], img["filename"]):
            success_count += 1
    
    print(f"\n✅ Downloaded {success_count}/{len(images_to_download)} images successfully")

if __name__ == "__main__":
    main()
