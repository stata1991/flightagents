#!/usr/bin/env python3
"""
Test RapidAPI Key Configuration
Verifies that the API key is loaded and working
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_key():
    """Test if the RapidAPI key is loaded and working"""
    
    print("🔑 Testing RapidAPI Key Configuration")
    print("=" * 50)
    
    # Check if API key is loaded
    api_key = os.getenv('RAPID_API_KEY')
    if api_key:
        print(f"✅ RapidAPI key loaded: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ RapidAPI key not found in environment")
        return
    
    # Test a simple API call to verify the key works
    print("\n🌐 Testing API Key with Booking.com...")
    
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }
    
    params = {
        "query": "dallas"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            total_results = len(data.get('data', []))
            print(f"✅ API key working! Found {total_results} destinations for Dallas")
            
            # Show first destination if available
            if data.get('data') and len(data['data']) > 0:
                first_dest = data['data'][0]
                dest_name = first_dest.get('name', 'Unknown')
                dest_type = first_dest.get('dest_type', 'Unknown')
                print(f"   Sample destination: {dest_name} ({dest_type})")
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ API test error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 API Key Test Completed!")

if __name__ == "__main__":
    test_api_key() 