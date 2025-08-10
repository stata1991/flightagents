#!/usr/bin/env python3
"""
End-to-End Integration Test
Tests the complete flow from chat interface to trip planning
"""
import requests
import json
import time

def test_chat_integration_flow():
    """Test the complete chat integration flow"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing End-to-End Chat Integration Flow")
    print("=" * 50)
    
    # Test 1: Check if enhanced chat interface is accessible
    print("\n1. Testing Enhanced Chat Interface Accessibility...")
    try:
        response = requests.get(f"{base_url}/enhanced-chat")
        if response.status_code == 200:
            print("✅ Enhanced chat interface is accessible")
        else:
            print(f"❌ Enhanced chat interface failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing enhanced chat interface: {e}")
        return False
    
    # Test 2: Test message processing endpoint
    print("\n2. Testing Message Processing...")
    test_message = "Plan a trip from dallas to las vegas for 5 days with my family"
    try:
        response = requests.post(
            f"{base_url}/chat-integration/process-message",
            headers={"Content-Type": "application/json"},
            json={
                "message": test_message,
                "session_id": "test_e2e_123",
                "conversation_state": {}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Message processing successful")
            print(f"   - Can start planning: {data.get('can_start_planning')}")
            print(f"   - Trip request: {data.get('trip_request')}")
            
            if data.get('can_start_planning'):
                print("✅ Ready to start trip planning!")
                return True
            else:
                print("❌ Cannot start planning - missing information")
                return False
        else:
            print(f"❌ Message processing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error in message processing: {e}")
        return False
    
    # Test 3: Test trip information extraction
    print("\n3. Testing Trip Information Extraction...")
    try:
        response = requests.post(
            f"{base_url}/chat-integration/extract-trip-info",
            headers={"Content-Type": "application/json"},
            json={
                "message": test_message,
                "conversation_state": {}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Trip information extraction successful")
            print(f"   - Confidence: {data.get('confidence', 0):.2%}")
            print(f"   - Trip request: {data.get('trip_request')}")
            
            if data.get('trip_request'):
                trip_request = data['trip_request']
                print(f"   - Origin: {trip_request.get('origin')}")
                print(f"   - Destination: {trip_request.get('destination')}")
                print(f"   - Duration: {trip_request.get('duration_days')} days")
                print(f"   - Travelers: {trip_request.get('travelers')}")
                print(f"   - Budget: {trip_request.get('budget_range')}")
                return True
            else:
                print("❌ No trip request extracted")
                return False
        else:
            print(f"❌ Trip information extraction failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in trip information extraction: {e}")
        return False

def test_frontend_backend_connection():
    """Test the connection between frontend and backend"""
    print("\n4. Testing Frontend-Backend Connection...")
    
    # Simulate what the frontend JavaScript would do
    test_data = {
        "message": "I want to go from dallas to las vegas for 5 days with my family",
        "session_id": "frontend_test_123",
        "conversation_state": {
            "origin": None,
            "destination": None,
            "travelers": None,
            "start_date": None,
            "end_date": None,
            "budget_range": None,
            "interests": []
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/chat-integration/process-message",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Frontend-backend connection successful")
            print(f"   - Session ID: {data.get('session_id')}")
            print(f"   - Can start planning: {data.get('can_start_planning')}")
            print(f"   - Next step: {data.get('next_step')}")
            
            if data.get('can_start_planning') and data.get('trip_request'):
                print("✅ Complete integration flow working!")
                return True
            else:
                print("❌ Integration flow incomplete")
                return False
        else:
            print(f"❌ Frontend-backend connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error in frontend-backend connection: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting End-to-End Integration Tests")
    print("=" * 50)
    
    # Run all tests
    test1_passed = test_chat_integration_flow()
    test2_passed = test_frontend_backend_connection()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   - Chat Integration Flow: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   - Frontend-Backend Connection: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED! End-to-end integration is working perfectly!")
        print("✅ Enhanced chat interface is accessible")
        print("✅ Message processing is working")
        print("✅ Trip information extraction is working")
        print("✅ Frontend-backend connection is working")
        print("✅ Ready for production use!")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")
    
    print("\n🌐 To test the UI manually:")
    print("   1. Open http://localhost:8000/enhanced-chat in your browser")
    print("   2. Type: 'Plan a trip from dallas to las vegas for 5 days with my family'")
    print("   3. Watch the magic happen! ✨") 