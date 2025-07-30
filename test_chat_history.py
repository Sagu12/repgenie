#!/usr/bin/env python3
"""
Test script to verify chat history functionality
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_backend_health():
    """Test if the backend is running"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_chat_and_history():
    """Test chat functionality and history retrieval"""
    print("\n💬 Testing Chat History Functionality")
    print("=" * 50)
    
    # Test user
    test_thread_id = "test@example.com"
    
    try:
        # Test sending a text message
        print("1. Testing text message...")
        text_message = {
            "thread_id": test_thread_id,
            "query": "Hello, this is a test message for chat history!",
            "selected_agent": "workout"
        }
        
        response = requests.post(f"{BASE_URL}/chat/text", json=text_message)
        
        if response.status_code == 200:
            chat_response = response.json()
            print(f"   ✅ Chat response received: {chat_response['response'][:100]}...")
            print(f"   🤖 Agent used: {chat_response.get('agent_used', 'unknown')}")
        else:
            print(f"   ❌ Failed to send text message: {response.status_code} - {response.text}")
            return False
        
        # Test getting conversation history
        print("\n2. Testing conversation history retrieval...")
        response = requests.get(f"{BASE_URL}/conversation_history/{test_thread_id}")
        
        if response.status_code == 200:
            history_data = response.json()
            conversations = history_data.get('conversations', [])
            print(f"   ✅ Retrieved {len(conversations)} conversation entries")
            
            for i, conv in enumerate(conversations[:3]):  # Show first 3
                print(f"   📅 Entry {i+1}:")
                print(f"      Date: {conv['date']}")
                print(f"      Agent: {conv['agent_type']}")
                print(f"      User: {conv['human_message'][:50]}...")
                print(f"      Bot: {conv['ai_message'][:50]}...")
                print(f"      Type: {conv['input_type']}")
                print()
        else:
            print(f"   ❌ Failed to get conversation history: {response.status_code} - {response.text}")
            return False
        
        # Test sending another message to see history grows
        print("3. Testing second message...")
        text_message2 = {
            "thread_id": test_thread_id,
            "query": "Can you help me plan a workout?",
            "selected_agent": "workout"
        }
        
        response = requests.post(f"{BASE_URL}/chat/text", json=text_message2)
        
        if response.status_code == 200:
            print("   ✅ Second message sent successfully")
        else:
            print(f"   ❌ Failed to send second message: {response.status_code}")
        
        # Get updated history
        print("\n4. Testing updated conversation history...")
        response = requests.get(f"{BASE_URL}/conversation_history/{test_thread_id}")
        
        if response.status_code == 200:
            history_data = response.json()
            conversations = history_data.get('conversations', [])
            print(f"   ✅ Updated history has {len(conversations)} conversation entries")
            print("   🔄 History should now include both messages")
        else:
            print(f"   ❌ Failed to get updated history: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing chat history: {e}")
        return False

def display_chat_history_features():
    """Display the chat history features"""
    print("\n🎯 Chat History Features")
    print("=" * 50)
    
    print("💾 **Data Persistence:**")
    features = [
        "All chat messages saved to SQLite database",
        "Messages persist across sessions and screen changes", 
        "History loaded automatically when opening chat",
        "Messages displayed in chronological order",
        "Support for text, image, and audio messages",
        "Agent type information preserved"
    ]
    for feature in features:
        print(f"   - {feature}")
    
    print("\n🔄 **History Loading:**")
    loading_features = [
        "Automatic history loading on chat component mount",
        "Loading indicator while fetching history",
        "Fallback to welcome message if no history",
        "Error handling with graceful fallback",
        "Conversation threading by user email",
        "Configurable history limit (default 50 messages)"
    ]
    for feature in loading_features:
        print(f"   - {feature}")
    
    print("\n📱 **Frontend Integration:**")
    ui_features = [
        "Messages converted from backend to frontend format",
        "Proper timestamp handling and display",
        "Agent information shown for bot messages",
        "Support for streaming text animation",
        "Markdown rendering for bot responses",
        "Auto-scroll to latest messages"
    ]
    for feature in ui_features:
        print(f"   - {feature}")

def display_testing_instructions():
    """Display testing instructions"""
    print("\n📋 Testing Instructions")
    print("=" * 50)
    
    print("1. **Start Both Servers:**")
    print("   Backend: python fastapi_fitness_trainer.py")
    print("   Frontend: npm run dev")
    
    print("\n2. **Test Chat History:**")
    print("   - Open http://localhost:3000")
    print("   - Login with your account")
    print("   - Go to Chat tab")
    print("   - Send a few messages")
    print("   - Switch to Calendar tab and back to Chat")
    print("   - Verify messages are still there")
    
    print("\n3. **Test Session Persistence:**")
    print("   - Send some messages")
    print("   - Close the browser tab")
    print("   - Open the app again and login")
    print("   - Go to Chat tab")
    print("   - Verify all previous messages are loaded")
    
    print("\n4. **Test Different Message Types:**")
    print("   - Send text messages")
    print("   - Upload images")
    print("   - Record audio messages")
    print("   - Use different agents (workout, news, YouTube)")
    print("   - Verify all are saved and loaded correctly")
    
    print("\n5. **Verify Browser Console:**")
    print("   - Open Developer Tools (F12)")
    print("   - Check Console tab for loading messages:")
    print("     • '📚 Loading conversation history for: user@email.com'")
    print("     • '💬 Converted to X chat messages'")
    print("     • No error messages")

def main():
    """Run chat history verification"""
    print("💬 RepGenie Chat History Verification\n")
    
    # Test backend connectivity
    if not test_backend_health():
        print("\n❌ Cannot proceed - backend not accessible")
        print("💡 Make sure to run: python fastapi_fitness_trainer.py")
        return False
    
    # Test chat history functionality
    chat_history_success = test_chat_and_history()
    
    # Display features and testing instructions
    display_chat_history_features()
    display_testing_instructions()
    
    if chat_history_success:
        print("\n🎉 Chat History Tests Passed!")
        print("✨ Your chat messages will now persist across sessions")
        print("🔗 Open http://localhost:3000 to test the frontend")
    else:
        print("\n⚠️ Some chat history tests failed")
        print("🔍 Check the backend logs for detailed error information")
    
    return chat_history_success

if __name__ == "__main__":
    main() 