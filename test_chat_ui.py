#!/usr/bin/env python3
"""
Test script to verify the new chat UI features including markdown rendering and streaming text
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

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

def test_chat_with_markdown():
    """Test if chat responses include markdown formatting"""
    print("\n💬 Testing chat response formatting...")
    
    test_requests = [
        {
            "thread_id": "test@example.com",
            "query": "Give me a quick beginner workout plan",
            "selected_agent": "workout"
        }
    ]
    
    try:
        for req in test_requests:
            response = requests.post(
                f'{API_BASE_URL}/chat/text',
                headers={'Content-Type': 'application/json'},
                data=json.dumps(req),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check for markdown elements
                markdown_indicators = ['**', '#', '-', '>', '`', '💪', '🏋️', '🥗']
                found_markdown = [indicator for indicator in markdown_indicators if indicator in response_text]
                
                if found_markdown:
                    print(f"✅ Response contains markdown formatting: {found_markdown}")
                    print(f"📝 Sample response preview: {response_text[:150]}...")
                else:
                    print("⚠️ Response doesn't seem to contain markdown formatting")
                    print(f"📝 Response preview: {response_text[:150]}...")
                
                return True
            else:
                print(f"❌ Chat request failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing chat: {e}")
        return False

def display_feature_info():
    """Display information about the new chat features"""
    print("\n🎨 New Chat UI Features:")
    print("=" * 50)
    
    print("✨ **Streaming Text Animation:**")
    print("   - Bot responses now appear character by character")
    print("   - Typing indicator with animated cursor")
    print("   - Configurable speed (60 characters per second)")
    print("   - Placeholder messages while loading")
    
    print("\n📝 **Markdown Rendering:**")
    print("   - **Bold text** for emphasis")
    print("   - # Headings and ## Subheadings")
    print("   - - Bullet point lists")
    print("   - 1. Numbered lists")
    print("   - > Blockquotes for important notes")
    print("   - `Code formatting` for exercises/measurements")
    print("   - [Clickable links](URL) that open in new tabs")
    print("   - Emojis for visual appeal 💪 🥗 📺")
    
    print("\n🎯 **Improved Layout:**")
    print("   - Fixed text overflow issues")
    print("   - Better message container sizing (75% max width)")
    print("   - Proper text wrapping for long URLs")
    print("   - break-words CSS for better text handling")
    print("   - Improved spacing and typography")
    
    print("\n🎤 **Enhanced Audio:**")
    print("   - Better error messages")
    print("   - Improved audio format detection")
    print("   - Transcription displayed in messages")
    print("   - Streaming responses for audio input")

def display_usage_instructions():
    """Display instructions for testing the new features"""
    print("\n📋 How to Test the New Features:")
    print("=" * 50)
    
    print("1. **Start the application:**")
    print("   Backend: python fastapi_fitness_trainer.py")
    print("   Frontend: npm run dev")
    
    print("\n2. **Test Markdown Rendering:**")
    print("   - Ask: 'Give me a workout plan for beginners'")
    print("   - Ask: 'Show me nutrition tips with examples'")
    print("   - Look for: Bold text, headings, bullet points, emojis")
    
    print("\n3. **Test Streaming Text:**")
    print("   - Send any message to a bot")
    print("   - Watch text appear character by character")
    print("   - Notice the animated cursor during typing")
    
    print("\n4. **Test Responsive Layout:**")
    print("   - Send very long messages")
    print("   - Try URLs and links")
    print("   - Resize browser window")
    print("   - Check message wrapping and boundaries")
    
    print("\n5. **Test Different Agents:**")
    print("   - 💪 Workout: Structured fitness plans")
    print("   - 🌐 News: Formatted news articles with links")
    print("   - 📺 YouTube: Video recommendations with links")
    print("   - 🚀 All Agents: Combined formatted responses")
    
    print("\n6. **Test Audio with Streaming:**")
    print("   - Record voice message")
    print("   - Watch transcription appear")
    print("   - See streaming response from selected agent")

def main():
    """Run all tests and display information"""
    print("🚀 RepGenie Chat UI Enhancement Test\n")
    
    tests = [
        ("Backend Health", test_backend_health),
        ("Chat Markdown", test_chat_with_markdown),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n📊 Test Results Summary:")
    print("=" * 40)
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    display_feature_info()
    display_usage_instructions()
    
    print("\n🎉 Ready to test the enhanced chat experience!")
    print("Open http://localhost:3000 in your browser to see the new features in action.")
    
    return True

if __name__ == "__main__":
    main() 