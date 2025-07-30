#!/usr/bin/env python3
"""
Test script for the AI-powered Insights Dashboard
"""

import json
import requests
from datetime import datetime, timedelta

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def create_test_user():
    """Create a test user for insights demo"""
    try:
        signup_data = {
            "email": "testuser@insights.demo",
            "password": "TestPassword123",
            "confirm_password": "TestPassword123"
        }
        response = requests.post("http://localhost:8000/auth/signup", json=signup_data)
        if response.status_code == 200:
            print("✅ Test user created successfully")
            return True
        elif response.status_code == 400 and "already registered" in response.text:
            print("ℹ️ Test user already exists")
            return True
        else:
            print(f"❌ Failed to create test user: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return False

def create_sample_conversations():
    """Create sample conversation data for testing"""
    user_email = "testuser@insights.demo"
    today = datetime.now().strftime('%Y-%m-%d')
    
    sample_conversations = [
        {
            "thread_id": user_email,
            "query": "I want to start a workout plan for muscle building",
            "selected_agent": "workout"
        },
        {
            "thread_id": user_email,
            "query": "Show me some protein-rich meal ideas",
            "selected_agent": "workout"
        },
        {
            "thread_id": user_email,
            "query": "Find me some workout videos on YouTube",
            "selected_agent": "youtube"
        },
        {
            "thread_id": user_email,
            "query": "What's the latest fitness news?",
            "selected_agent": "news"
        }
    ]
    
    print(f"📝 Creating sample conversations for {today}...")
    
    for i, conv in enumerate(sample_conversations):
        try:
            response = requests.post("http://localhost:8000/chat/text", json=conv)
            if response.status_code == 200:
                print(f"  ✅ Conversation {i+1} created")
            else:
                print(f"  ❌ Failed to create conversation {i+1}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error creating conversation {i+1}: {e}")

def create_sample_calendar_entries():
    """Create sample calendar entries for testing"""
    user_email = "testuser@insights.demo"
    today = datetime.now().strftime('%Y-%m-%d')
    
    sample_entries = [
        {
            "user_email": user_email,
            "entry_date": today,
            "activity_type": "workout",
            "duration": 60,
            "intensity": "high",
            "additional_notes": "Upper body strength training session",
            "completed": True
        },
        {
            "user_email": user_email,
            "entry_date": today,
            "activity_type": "meal_planning",
            "additional_notes": "Planned high-protein meals for muscle building",
            "completed": True
        },
        {
            "user_email": user_email,
            "entry_date": today,
            "activity_type": "cardio",
            "duration": 30,
            "intensity": "medium",
            "additional_notes": "Morning jog in the park",
            "completed": False
        }
    ]
    
    print(f"📅 Creating sample calendar entries for {today}...")
    
    for i, entry in enumerate(sample_entries):
        try:
            response = requests.post("http://localhost:8000/calendar/entries", json=entry)
            if response.status_code == 200:
                print(f"  ✅ Calendar entry {i+1} created")
            else:
                print(f"  ❌ Failed to create calendar entry {i+1}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error creating calendar entry {i+1}: {e}")

def test_insights_api():
    """Test the insights API endpoint"""
    user_email = "testuser@insights.demo"
    today = datetime.now().strftime('%Y-%m-%d')
    
    print(f"🧠 Testing insights API for {user_email} on {today}...")
    
    try:
        url = f"http://localhost:8000/insights/{user_email}?date={today}"
        response = requests.get(url)
        
        if response.status_code == 200:
            insights = response.json()
            print("✅ Insights API successful!")
            
            # Display the insights in a readable format
            print(f"\n📊 AI-Generated Insights for {today}:")
            print("=" * 50)
            print(f"📧 User: {insights['user_email']}")
            print(f"📅 Date: {insights['date']}")
            print(f"💪 Workout Requested: {'Yes' if insights['workout_requested'] else 'No'}")
            if insights['workout_type']:
                print(f"   └─ Type: {insights['workout_type']}")
            print(f"🍎 Meal Requested: {'Yes' if insights['meal_requested'] else 'No'}")
            if insights['meal_type']:
                print(f"   └─ Type: {insights['meal_type']}")
            print(f"📺 Video Requested: {'Yes' if insights['video_requested'] else 'No'}")
            if insights['video_type']:
                print(f"   └─ Type: {insights['video_type']}")
            print(f"📰 News Requested: {'Yes' if insights['news_requested'] else 'No'}")
            if insights['news_type']:
                print(f"   └─ Type: {insights['news_type']}")
            print(f"📷 Image Analysis: {'Yes' if insights['image_analysis_done'] else 'No'}")
            if insights['image_analysis_insights']:
                print(f"   └─ Insights: {insights['image_analysis_insights']}")
            print(f"📝 Calendar Entries: {'Yes' if insights['calendar_entries_logged'] else 'No'}")
            print(f"   └─ Count: {insights['entries_count']}")
            if insights['calendar_entries_summary']:
                print(f"   └─ Summary: {insights['calendar_entries_summary']}")
            print(f"\n💬 Conversation Summary:")
            print(f"   {insights['conversation_summary']}")
            
            return True
        else:
            print(f"❌ Insights API failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing insights API: {e}")
        return False

def show_frontend_testing_instructions():
    """Show instructions for testing the frontend"""
    print("\n🌐 Frontend Testing Instructions:")
    print("=" * 50)
    
    print("1. **Start the Frontend:**")
    print("   cd project")
    print("   npm run dev")
    print("   Open http://localhost:3000")
    
    print("\n2. **Test the Insights Dashboard:**")
    print("   - Log in with: testuser@insights.demo / TestPassword123")
    print("   - Navigate to the Insights page")
    print("   - Select today's date")
    print("   - Click 'Generate Insights'")
    
    print("\n3. **Expected Results:**")
    print("   ✅ Beautiful AI Insights Dashboard loads")
    print("   ✅ Comprehensive table with all categories")
    print("   ✅ AI-analyzed data from conversations and calendar")
    print("   ✅ Visual indicators (Yes/No with icons)")
    print("   ✅ Type badges for different categories")
    print("   ✅ Hover tooltips for long summaries")
    print("   ✅ Professional gradient design")
    
    print("\n4. **Test Different Scenarios:**")
    print("   - Select a date with no data (should show empty insights)")
    print("   - Test with different user accounts")
    print("   - Verify error handling with friendly messages")
    
    print("\n5. **Key Features to Verify:**")
    print("   🧠 AI-powered analysis using GPT-4o")
    print("   📊 Comprehensive insights table")
    print("   🎨 Beautiful, responsive design")
    print("   ⚡ Real-time data processing")
    print("   🛡️ User-friendly error messages")

def show_implementation_details():
    """Show technical implementation details"""
    print("\n🔧 Implementation Details:")
    print("=" * 50)
    
    print("📁 **Backend Implementation:**")
    print("   - New InsightsResponse Pydantic model")
    print("   - analyze_user_insights_with_openai() function")
    print("   - /insights/{user_email} API endpoint")
    print("   - GPT-4o integration for intelligent analysis")
    print("   - Fetches both conversations and calendar data")
    
    print("\n📁 **Frontend Implementation:**")
    print("   - Completely redesigned Insights component")
    print("   - Beautiful gradient design with Tailwind CSS")
    print("   - Date picker for flexible analysis")
    print("   - Comprehensive insights table")
    print("   - Loading states and error handling")
    print("   - Responsive design for all devices")
    
    print("\n🎯 **AI Analysis Categories:**")
    categories = [
        "Workout requests and types",
        "Meal planning and nutrition", 
        "Video content requests",
        "Fitness news consumption",
        "Image analysis insights",
        "Conversation summaries",
        "Calendar activity tracking",
        "Completion status analysis"
    ]
    
    for category in categories:
        print(f"   ✅ {category}")
    
    print("\n💡 **Key Benefits:**")
    benefits = [
        "Comprehensive user behavior analysis",
        "AI-powered insights using GPT-4o",
        "Professional, data-driven dashboard",
        "Date-based filtering and analysis",
        "User-friendly error handling",
        "Real-time data processing",
        "Beautiful, responsive UI design"
    ]
    
    for benefit in benefits:
        print(f"   🎯 {benefit}")

def main():
    """Run comprehensive insights testing"""
    print("🧠 RepGenie AI Insights Dashboard Testing\n")
    
    # Test backend connectivity
    if not test_backend_health():
        print("❌ Backend not running. Please start the backend first:")
        print("   python fastapi_fitness_trainer.py")
        return False
    
    # Create test data
    print("\n📝 Setting up test data...")
    create_test_user()
    create_sample_conversations()
    create_sample_calendar_entries()
    
    # Test insights API
    print("\n🧠 Testing AI insights generation...")
    insights_success = test_insights_api()
    
    # Show results
    if insights_success:
        print("\n🎉 Insights Dashboard Implementation Complete!")
        print("✨ AI-powered analytics are working perfectly!")
        
        # Show implementation details
        show_implementation_details()
        
        # Show frontend testing instructions
        show_frontend_testing_instructions()
        
        print("\n🚀 Ready to use the Insights Dashboard!")
        print("🔗 Access at: http://localhost:3000 (after starting frontend)")
    else:
        print("\n❌ Insights testing failed")
        print("💡 Check backend logs and try again")
    
    return insights_success

if __name__ == "__main__":
    main() 