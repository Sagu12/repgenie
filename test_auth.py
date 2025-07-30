#!/usr/bin/env python3
"""
Test script to verify the authentication system is working properly
"""

import sqlite3
import requests
import json

def test_database():
    """Test if database tables are created"""
    print("🗄️ Testing database setup...")
    try:
        conn = sqlite3.connect('conversations.db')
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Database tables found: {[table[0] for table in tables]}")
        
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        users_columns = cursor.fetchall()
        print(f"✅ Users table columns: {[col[1] for col in users_columns]}")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_backend_health():
    """Test if backend is running"""
    print("\n🔍 Testing backend health...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def test_signup():
    """Test user registration"""
    print("\n📝 Testing user registration...")
    test_user = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "confirm_password": "TestPassword123"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/auth/signup',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(test_user),
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Signup successful: {user_data}")
            return True
        else:
            error = response.json()
            if "Email already registered" in error.get('detail', ''):
                print("⚠️ User already exists (this is expected if running multiple times)")
                return True
            else:
                print(f"❌ Signup failed: {error}")
                return False
    except Exception as e:
        print(f"❌ Signup error: {e}")
        return False

def test_login():
    """Test user login"""
    print("\n🔐 Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "TestPassword123"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/auth/login',
            headers={'Content-Type': 'application/json'},
            data=json.dumps(login_data),
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Login successful: {user_data}")
            return True
        else:
            error = response.json()
            print(f"❌ Login failed: {error}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 RepGenie Authentication System Test\n")
    
    tests = [
        ("Database Setup", test_database),
        ("Backend Health", test_backend_health),
        ("User Registration", test_signup),
        ("User Login", test_login)
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
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests passed! Authentication system is working properly.")
    else:
        print("\n⚠️ Some tests failed. Please check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    main() 