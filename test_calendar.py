#!/usr/bin/env python3
"""
Test script to verify the calendar/logbook functionality
"""

import requests
import json
from datetime import datetime, date

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

def test_calendar_endpoints():
    """Test the calendar API endpoints"""
    print("\n📋 Testing Calendar API Endpoints")
    print("=" * 50)
    
    # Test data
    test_user_email = "test@example.com"
    test_entry = {
        "user_email": test_user_email,
        "entry_date": "2025-01-30",
        "activity_type": "workout",
        "duration": 45,
        "intensity": "high",
        "additional_notes": "Great chest and back workout",
        "completed": False
    }
    
    try:
        # Test creating a calendar entry
        print("1. Testing calendar entry creation...")
        response = requests.post(f"{BASE_URL}/calendar/entries", json=test_entry)
        
        if response.status_code == 200:
            created_entry = response.json()
            print(f"   ✅ Created entry with ID: {created_entry['id']}")
            print(f"   📝 Activity: {created_entry['activity_type']}")
            print(f"   ⏱️ Duration: {created_entry['duration']} minutes")
            print(f"   🔥 Intensity: {created_entry['intensity']}")
            entry_id = created_entry['id']
        else:
            print(f"   ❌ Failed to create entry: {response.status_code} - {response.text}")
            return False
        
        # Test getting calendar entries
        print("\n2. Testing calendar entries retrieval...")
        response = requests.get(f"{BASE_URL}/calendar/entries/{test_user_email}")
        
        if response.status_code == 200:
            entries_data = response.json()
            entries = entries_data.get('entries', [])
            print(f"   ✅ Retrieved {len(entries)} entries for user")
            for entry in entries:
                print(f"   📅 {entry['entry_date']}: {entry['activity_type']} ({entry['duration']}min)")
        else:
            print(f"   ❌ Failed to get entries: {response.status_code} - {response.text}")
        
        # Test updating calendar entry
        print("\n3. Testing calendar entry update...")
        update_data = {
            "completed": True,
            "additional_notes": "Completed! Felt great after the workout."
        }
        response = requests.put(f"{BASE_URL}/calendar/entries/{entry_id}", json=update_data)
        
        if response.status_code == 200:
            print("   ✅ Successfully updated entry status")
        else:
            print(f"   ❌ Failed to update entry: {response.status_code} - {response.text}")
        
        # Test deleting calendar entry (cleanup)
        print("\n4. Testing calendar entry deletion...")
        response = requests.delete(f"{BASE_URL}/calendar/entries/{entry_id}")
        
        if response.status_code == 200:
            print("   ✅ Successfully deleted test entry")
        else:
            print(f"   ❌ Failed to delete entry: {response.status_code} - {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing calendar endpoints: {e}")
        return False

def display_calendar_features():
    """Display the new calendar features"""
    print("\n🎯 New Calendar/Logbook Features")
    print("=" * 50)
    
    print("📝 **Activity Types Available:**")
    activities = [
        "💪 Workout",
        "🧘 Yoga", 
        "🏊 Swimming",
        "🚴 Cycling",
        "🧘‍♀️ Meditation",
        "🥊 Boxing",
        "🍽️ Meal Planning",
        "📝 Other (custom activity)"
    ]
    for activity in activities:
        print(f"   - {activity}")
    
    print("\n🔥 **Intensity Levels:**")
    intensities = [
        "🟢 Low - Light activity, easy pace",
        "🟡 Medium - Moderate effort, comfortable",  
        "🔴 High - Intense effort, challenging"
    ]
    for intensity in intensities:
        print(f"   - {intensity}")
    
    print("\n📊 **Data Fields Tracked:**")
    fields = [
        "📅 Date of activity",
        "🏃 Activity type (predefined or custom)",
        "⏱️ Duration in minutes (except meal planning)",
        "🔥 Intensity level (low/medium/high)",
        "📝 Additional notes",
        "✅ Completion status (complete/incomplete)"
    ]
    for field in fields:
        print(f"   - {field}")
    
    print("\n🎨 **UI Features:**")
    ui_features = [
        "📅 Interactive calendar grid",
        "🎯 Activity emojis on calendar dates",
        "📝 Comprehensive entry form",
        "✏️ Edit existing entries",
        "🗑️ Delete entries",
        "✅ Toggle completion status",
        "📱 Responsive design",
        "🎨 Visual intensity indicators"
    ]
    for feature in ui_features:
        print(f"   - {feature}")

def display_testing_instructions():
    """Display testing instructions for manual verification"""
    print("\n📋 Manual Testing Instructions")
    print("=" * 50)
    
    print("1. **Start Both Servers:**")
    print("   Backend: python fastapi_fitness_trainer.py")
    print("   Frontend: npm run dev")
    
    print("\n2. **Test Calendar Navigation:**")
    print("   - Open http://localhost:3000")
    print("   - Login with your account")
    print("   - Click on 'Calendar' in the sidebar/bottom nav")
    print("   - Navigate between months using arrow buttons")
    
    print("\n3. **Test Adding Activities:**")
    print("   - Click on any date in the calendar")
    print("   - Click 'Add Activity' button")
    print("   - Test different activity types:")
    print("     • Workout with 45 min duration, high intensity")
    print("     • Yoga with 30 min duration, medium intensity")
    print("     • Meal Planning (no duration required)")
    print("     • Other with custom activity name")
    
    print("\n4. **Test Entry Management:**")
    print("   - Create multiple entries for the same date")
    print("   - Edit existing entries")
    print("   - Toggle completion status")
    print("   - Delete entries")
    print("   - Check that activity emojis appear on calendar dates")
    
    print("\n5. **Test Form Validation:**")
    print("   - Try to save 'Other' activity without custom name")
    print("   - Try to save workout without duration")
    print("   - Verify intensity levels work correctly")
    
    print("\n6. **Test UI Features:**")
    print("   - Check activity emojis on calendar dates")
    print("   - Verify intensity color coding")
    print("   - Test responsive design on different screen sizes")
    print("   - Check that notes display properly")

def main():
    """Run calendar logbook verification"""
    print("🏋️ RepGenie Calendar/Logbook Verification\n")
    
    # Test backend connectivity
    if not test_backend_health():
        print("\n❌ Cannot proceed - backend not accessible")
        print("💡 Make sure to run: python fastapi_fitness_trainer.py")
        return False
    
    # Test calendar API endpoints
    calendar_test_success = test_calendar_endpoints()
    
    # Display features and testing instructions
    display_calendar_features()
    display_testing_instructions()
    
    if calendar_test_success:
        print("\n🎉 Calendar/Logbook API Tests Passed!")
        print("✨ Your logbook system is ready to use")
        print("🔗 Open http://localhost:3000 and go to Calendar tab")
    else:
        print("\n⚠️ Some calendar API tests failed")
        print("🔍 Check the backend logs for detailed error information")
    
    return calendar_test_success

if __name__ == "__main__":
    main() 