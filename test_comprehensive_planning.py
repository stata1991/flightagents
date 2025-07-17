#!/usr/bin/env python3
"""
Test Comprehensive Trip Planning Integration
Tests the complete flow: Itinerary → Flights → Hotels
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your_rapidapi_key_here"  # Replace with actual API key

def test_comprehensive_planning():
    """Test the comprehensive trip planning endpoint"""
    
    # Test data
    test_data = {
        "origin": "New York",
        "destination": "Paris",
        "start_date": "2024-07-15",
        "return_date": "2024-07-22",
        "travelers": 2,
        "budget_range": "moderate",
        "trip_type": "leisure",
        "interests": ["food", "art", "history"]
    }
    
    print("🧪 Testing Comprehensive Trip Planning")
    print("=" * 50)
    print(f"Test Data: {json.dumps(test_data, indent=2)}")
    print()
    
    try:
        # Test comprehensive planning endpoint
        print("📡 Calling comprehensive planning endpoint...")
        response = requests.post(
            f"{BASE_URL}/trip-planner/comprehensive-plan",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Comprehensive planning successful!")
            print()
            
            # Display trip summary
            if "trip_summary" in result:
                summary = result["trip_summary"]
                print("📋 Trip Summary:")
                print(f"  From: {summary.get('origin')} → To: {summary.get('destination')}")
                print(f"  Duration: {summary.get('duration_days')} days")
                print(f"  Travelers: {summary.get('travelers')}")
                print(f"  Budget: {summary.get('budget_range')}")
                print()
            
            # Display itinerary status
            if "itinerary" in result:
                itinerary = result["itinerary"]
                if "error" in itinerary:
                    print("❌ Itinerary Error:", itinerary["error"])
                else:
                    print("✅ Itinerary generated successfully")
                    if "itinerary" in itinerary and itinerary["itinerary"]:
                        print(f"  Days planned: {len(itinerary['itinerary'])}")
                print()
            
            # Display flights status
            if "flights" in result:
                flights = result["flights"]
                if "error" in flights:
                    print("❌ Flights Error:", flights["error"])
                else:
                    print("✅ Flights search completed")
                    print(f"  Cheapest: {len(flights.get('cheapest', []))} options")
                    print(f"  Fastest: {len(flights.get('fastest', []))} options")
                    print(f"  Best Value: {len(flights.get('best_value', []))} options")
                    print(f"  Total flights found: {flights.get('total_flights_found', 0)}")
                print()
            
            # Display hotels status
            if "hotels" in result:
                hotels = result["hotels"]
                if "error" in hotels:
                    print("❌ Hotels Error:", hotels["error"])
                else:
                    print("✅ Hotels search completed")
                    print(f"  Budget: {len(hotels.get('budget', []))} options")
                    print(f"  Mid-Range: {len(hotels.get('mid_range', []))} options")
                    print(f"  Luxury: {len(hotels.get('luxury', []))} options")
                    print(f"  Total hotels found: {hotels.get('total_hotels_found', 0)}")
                print()
            
            # Display budget breakdown
            if "budget_breakdown" in result:
                budget = result["budget_breakdown"]
                print("💰 Budget Breakdown:")
                print(f"  Flights: ${budget.get('flight_cost', 0):.2f}")
                print(f"  Hotels: ${budget.get('hotel_cost', 0):.2f}")
                print(f"  Activities: ${budget.get('activities_cost', 0):.2f}")
                print(f"  Total Estimated: ${budget.get('total_estimated_cost', 0):.2f}")
                print()
            
            # Save detailed results to file
            with open("comprehensive_plan_results.json", "w") as f:
                json.dump(result, f, indent=2)
            print("💾 Detailed results saved to comprehensive_plan_results.json")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the FastAPI server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_individual_components():
    """Test individual components separately"""
    
    print("\n🔧 Testing Individual Components")
    print("=" * 50)
    
    # Test itinerary generation
    print("\n📅 Testing Itinerary Generation...")
    itinerary_data = {
        "origin": "New York",
        "destination": "Paris",
        "duration_days": 7,
        "start_date": "2024-07-15",
        "end_date": "2024-07-22",
        "travelers": 2,
        "trip_type": "leisure",
        "budget_range": "moderate",
        "interests": ["food", "art", "history"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/trip-planner/start-natural",
            json={"query": "Plan a 7-day trip from New York to Paris for 2 people"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Itinerary endpoint working")
        else:
            print(f"❌ Itinerary endpoint error: {response.status_code}")
    except Exception as e:
        print(f"❌ Itinerary test error: {e}")
    
    # Test flight search
    print("\n✈️ Testing Flight Search...")
    try:
        response = requests.get(
            f"{BASE_URL}/flights/search",
            params={
                "from_location": "New York",
                "to_location": "Paris",
                "depart_date": "2024-07-15",
                "return_date": "2024-07-22",
                "adults": 2,
                "currency_code": "USD"
            }
        )
        if response.status_code == 200:
            print("✅ Flight search endpoint working")
            result = response.json()
            if "data" in result and "error" not in result["data"]:
                print("✅ Flight search returned valid data")
            else:
                print("⚠️ Flight search returned error or no data")
        else:
            print(f"❌ Flight search endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Flight test error: {e}")
    
    # Test hotel search with future dates
    print("\n🏨 Testing Hotel Search...")
    try:
        # Generate future dates for testing
        today = datetime.today()
        check_in = (today + timedelta(days=7)).strftime('%Y-%m-%d')  # 7 days from today
        check_out = (today + timedelta(days=14)).strftime('%Y-%m-%d')  # 14 days from today
        
        response = requests.get(
            f"{BASE_URL}/hotels/search",
            params={
                "location": "Paris",
                "check_in": check_in,
                "check_out": check_out,
                "adults": 2,
                "currency": "USD"
            }
        )
        if response.status_code == 200:
            print("✅ Hotel search endpoint working")
            result = response.json()
            if hasattr(result, 'total_results') and result.total_results > 0:
                print("✅ Hotel search returned valid data")
            else:
                print("⚠️ Hotel search returned no results")
        else:
            print(f"❌ Hotel search endpoint error: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Hotel test error: {e}")

def main():
    """Main test function"""
    print("🚀 Comprehensive Trip Planning Integration Test")
    print("=" * 60)
    print()
    
    # Test individual components first
    test_individual_components()
    
    # Test comprehensive planning
    test_comprehensive_planning()
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")

if __name__ == "__main__":
    main() 