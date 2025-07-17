#!/usr/bin/env python3
"""
Test API Endpoints
Tests the flight and hotel search endpoints to ensure they work correctly
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"

def test_flight_search_endpoint():
    """Test the flight search endpoint"""
    print("🧪 Testing Flight Search Endpoint")
    print("=" * 50)
    
    # Test parameters
    params = {
        "from_location": "New York",
        "to_location": "Paris",
        "depart_date": "2024-07-15",
        "return_date": "2024-07-22",
        "adults": 2,
        "currency_code": "USD"
    }
    
    print(f"Test Parameters: {json.dumps(params, indent=2)}")
    print()
    
    try:
        response = requests.get(f"{BASE_URL}/flights/search", params=params)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Flight search endpoint working")
            
            if "data" in result:
                if "error" in result["data"]:
                    print(f"❌ API returned error: {result['data']['error']}")
                else:
                    print("✅ Flight search returned valid data")
                    print(f"Data keys: {list(result['data'].keys())}")
            else:
                print("⚠️ Response format unexpected")
                print(f"Response: {result}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_hotel_search_endpoint():
    """Test the hotel search endpoint"""
    print("\n🏨 Testing Hotel Search Endpoint")
    print("=" * 50)
    
    # Generate future dates for testing
    today = datetime.today()
    check_in = (today + timedelta(days=7)).strftime('%Y-%m-%d')  # 7 days from today
    check_out = (today + timedelta(days=14)).strftime('%Y-%m-%d')  # 14 days from today
    
    # Test parameters
    params = {
        "location": "Paris",
        "check_in": check_in,
        "check_out": check_out,
        "adults": 2,
        "currency": "USD"
    }
    
    print(f"Test Parameters: {json.dumps(params, indent=2)}")
    print(f"Using future dates: check_in={check_in}, check_out={check_out}")
    print()
    
    try:
        response = requests.get(f"{BASE_URL}/hotels/search", params=params)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Hotel search endpoint working")
            
            if hasattr(result, 'total_results'):
                if result.total_results > 0:
                    print(f"✅ Hotel search returned {result.total_results} results")
                else:
                    print("⚠️ Hotel search returned no results")
            else:
                print("⚠️ Response format unexpected")
                print(f"Response: {result}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_destination_search():
    """Test the destination search endpoint"""
    print("\n📍 Testing Destination Search Endpoint")
    print("=" * 50)
    
    test_queries = ["New York", "Paris", "London"]
    
    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        
        try:
            response = requests.get(f"{BASE_URL}/search-destination", params={"query": query})
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                if "data" in result and "destinations" in result["data"]:
                    destinations = result["data"]["destinations"]
                    print(f"✅ Found {len(destinations)} destinations")
                    
                    for i, dest in enumerate(destinations[:3]):  # Show first 3
                        print(f"  {i+1}. {dest.get('name', 'N/A')} ({dest.get('type', 'N/A')}) - ID: {dest.get('id', 'N/A')}")
                else:
                    print("⚠️ No destinations found or unexpected response format")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")

def main():
    """Main test function"""
    print("🚀 API Endpoints Test")
    print("=" * 60)
    print()
    
    # Test destination search first
    test_destination_search()
    
    # Test flight search
    test_flight_search_endpoint()
    
    # Test hotel search
    test_hotel_search_endpoint()
    
    print("\n" + "=" * 60)
    print("🏁 API endpoints test completed!")

if __name__ == "__main__":
    main() 