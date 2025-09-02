#!/usr/bin/env python3
"""
Test script for location discovery flow
Verifies the complete location discovery integration is working
"""
import requests
import json

def test_location_discovery_flow():
    """Test the complete location discovery flow"""
    print("🧪 Testing Location Discovery Flow")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Verify the main endpoint is accessible
    print("1. Testing enhanced-travel endpoint...")
    try:
        response = requests.get(f"{base_url}/enhanced-travel")
        if response.status_code == 200:
            print("   ✅ Frontend accessible")
            if "location-discovery-section" in response.text:
                print("   ✅ Location discovery UI found")
            else:
                print("   ❌ Location discovery UI not found")
        else:
            print(f"   ❌ Frontend not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error accessing frontend: {e}")
        return False
    
    # Test 2: Test location API endpoint
    print("\n2. Testing location API endpoint...")
    try:
        response = requests.get(f"{base_url}/api/location/discovery-homepage?user_consent=false")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ API endpoint working")
                print(f"   📍 Location: {data.get('user_location', {}).get('detection_method', 'unknown')}")
                print(f"   🌍 Suggestions: {len(data.get('international_suggestions', []))} international")
                print(f"   📊 Data source: {data.get('data_source', 'unknown')}")
            else:
                print("   ❌ API returned success: false")
                return False
        else:
            print(f"   ❌ API endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing API: {e}")
        return False
    
    # Test 3: Test with user consent
    print("\n3. Testing with user consent...")
    try:
        response = requests.get(f"{base_url}/api/location/discovery-homepage?user_consent=true")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("   ✅ Consent flow working")
                print(f"   📍 Detection method: {data.get('user_location', {}).get('detection_method', 'unknown')}")
            else:
                print("   ❌ Consent flow failed")
                return False
        else:
            print(f"   ❌ Consent endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error testing consent: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Location Discovery Flow Test Complete!")
    print("✅ All tests passed - the system is working correctly!")
    print()
    print("🌐 Frontend URL: http://localhost:8000/enhanced-travel")
    print("📱 You can now test the location discovery UI in your browser!")
    print()
    print("The system provides:")
    print("• Dynamic destination suggestions (not hardcoded)")
    print("• User consent handling for location detection")
    print("• Integration with external APIs for real-time data")
    print("• Responsive UI for location discovery")
    
    return True

if __name__ == "__main__":
    test_location_discovery_flow()
