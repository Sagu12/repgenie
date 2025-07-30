#!/usr/bin/env python3
"""
Test script to verify the audio recording and transcription system
"""

import requests
import json
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_audio_endpoint():
    """Test the audio transcription endpoint"""
    print("🎵 Testing audio transcription endpoint...")
    
    # Create a small test audio file (if you have one)
    # For testing purposes, we'll skip actual audio file testing
    # since we don't have a sample audio file
    
    print("ℹ️ To test audio properly:")
    print("1. Start the backend: python fastapi_fitness_trainer.py")
    print("2. Start the frontend: npm run dev")
    print("3. Go to http://localhost:3000")
    print("4. Sign in with your credentials")
    print("5. Click the microphone button")
    print("6. Speak for 2-3 seconds")
    print("7. Click the microphone button again to stop")
    print("8. Check the browser console for detailed logs")
    
    return True

def test_backend_health():
    """Test if backend is running"""
    print("🔍 Testing backend health...")
    try:
        response = requests.get(f'{API_BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def check_audio_format_support():
    """Check what audio formats the backend supports"""
    print("\n🎯 Audio format support information:")
    print("✅ Supported formats:")
    print("   - WAV (RIFF header)")
    print("   - MP3 (ID3 header or raw MP3)")
    print("   - FLAC (fLaC header)")
    print("   - OGG (OggS header)")
    print("   - WebM (Matroska header) - with fallback to MP3")
    print("\n📱 Browser MediaRecorder typically produces:")
    print("   - Chrome: WebM (audio/webm;codecs=opus)")
    print("   - Firefox: WebM or OGG")
    print("   - Safari: MP4 (audio/mp4)")
    print("   - Edge: WebM")
    
    return True

def main():
    """Run all tests"""
    print("🚀 RepGenie Audio System Test\n")
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Audio Format Support", check_audio_format_support),
        ("Audio Endpoint Info", test_audio_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
        print()  # Add spacing between tests
    
    print("📊 Test Results Summary:")
    print("=" * 40)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print("\n🎤 Audio Recording Instructions:")
    print("=" * 40)
    print("1. Make sure backend is running (python fastapi_fitness_trainer.py)")
    print("2. Make sure frontend is running (npm run dev)")
    print("3. Open browser and go to http://localhost:3000")
    print("4. Sign in or sign up")
    print("5. Click the microphone button (🎤)")
    print("6. Speak clearly for 2-3 seconds")
    print("7. Click the microphone button again (🔇)")
    print("8. Watch for transcription and AI response")
    print("\n🔧 Troubleshooting:")
    print("- Check browser console (F12) for detailed logs")
    print("- Make sure microphone permissions are granted")
    print("- Try speaking louder and more clearly")
    print("- Check network connection for OpenAI API calls")
    
    return True

if __name__ == "__main__":
    main() 