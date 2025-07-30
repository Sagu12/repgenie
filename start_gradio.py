#!/usr/bin/env python3
"""
RepGenie Gradio App Launcher
"""

import subprocess
import sys
import time
import threading
import os

def install_requirements():
    """Install required packages"""
    print("🔧 Installing Gradio app requirements...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_gradio.txt"])

def start_fastapi():
    """Start FastAPI backend in background"""
    print("🚀 Starting FastAPI backend...")
    subprocess.Popen([sys.executable, "fastapi_fitness_trainer.py"])
    time.sleep(3)  # Give FastAPI time to start

def start_gradio():
    """Start Gradio frontend"""
    print("🚀 Starting Gradio frontend...")
    subprocess.run([sys.executable, "gradio_app.py"])

def main():
    print("=" * 50)
    print("🏋️  RepGenie - AI Fitness Trainer")
    print("   Gradio Web Application")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n⚠️  Creating .env file...")
        with open(".env", "w") as f:
            f.write("openai_api_key=your_openai_api_key_here\n")
        print("📝 Please add your OpenAI API key to the .env file")
        print("   Edit .env and replace 'your_openai_api_key_here' with your actual key")
        input("\nPress Enter when you've added your API key...")
    
    try:
        # Install requirements
        install_requirements()
        
        # Start FastAPI in background
        fastapi_thread = threading.Thread(target=start_fastapi)
        fastapi_thread.daemon = True
        fastapi_thread.start()
        
        print("\n" + "=" * 50)
        print("✅ Starting RepGenie Application")
        print("📱 Gradio UI: http://localhost:7860")
        print("🔗 FastAPI Backend: http://localhost:8000")
        print("📖 API Docs: http://localhost:8000/docs")
        print("=" * 50)
        
        # Start Gradio (this will block)
        start_gradio()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down RepGenie...")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 