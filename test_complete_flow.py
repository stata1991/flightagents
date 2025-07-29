#!/usr/bin/env python3
"""
Test script to verify the complete trip planning flow
"""

import requests
import json
import time

def test_complete_flow():
    """Test the complete trip planning flow"""
    
    base_url = "http://localhost:8000"
    
    print("🚀 Testing Complete Trip Planning Flow")
    print("=" * 50)
    
    # Test 1: Incomplete query (should trigger requirements modal)
    print("\n📋 Test 1: Incomplete query (missing travelers)")
    print("-" * 40)
    
    query1 = "I want to visit Disney World from New York for 5 days starting August 10th"
    print(f"Query: {query1}")
    
    response1 = requests.post(
        f"{base_url}/trip-planner/plan-trip-natural",
        json={"query": query1},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response1.status_code}")
    result1 = response1.json()
    print(f"Response: {json.dumps(result1, indent=2)}")
    
    # Verify it returns validation error for missing travelers
    if (result1.get("success") == False and 
        "number of travelers" in result1.get("missing_fields", [])):
        print("✅ Correctly identified missing travelers")
    else:
        print("❌ Failed to identify missing travelers")
    
    # Test 2: Complete query with travelers
    print("\n📋 Test 2: Complete query with travelers")
    print("-" * 40)
    
    query2 = "I want to visit Disney World from New York for 5 days starting August 10th for 2 adults and 1 child"
    print(f"Query: {query2}")
    
    response2 = requests.post(
        f"{base_url}/trip-planner/plan-trip-natural",
        json={"query": query2},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response2.status_code}")
    result2 = response2.json()
    
    if result2.get("success"):
        print("✅ Successfully planned trip")
        trip_plan = result2.get("trip_plan", {})
        summary = trip_plan.get("summary", {})
        print(f"Origin: {summary.get('origin')}")
        print(f"Destination: {summary.get('destination')}")
        print(f"Duration: {summary.get('duration')} days")
        print(f"Travelers: {summary.get('travelers')}")
        
        # Check if hotels and flights are found
        hotels = trip_plan.get("hotels", {})
        flights = trip_plan.get("flights", {})
        itinerary = trip_plan.get("itinerary", [])
        
        print(f"Hotels found: {bool(hotels.get('moderate') or hotels.get('budget') or hotels.get('luxury'))}")
        print(f"Flights found: {bool(flights.get('cheapest') or flights.get('fastest') or flights.get('best_value'))}")
        print(f"Itinerary days: {len(itinerary)}")
        
        if itinerary:
            print("Sample activities:")
            for day in itinerary[:2]:  # Show first 2 days
                activities = day.get("activities", [])
                print(f"  Day {day.get('day')}: {activities[:2]}")  # Show first 2 activities
    else:
        print(f"❌ Failed to plan trip: {result2.get('error')}")
    
    # Test 3: Requirements gathering simulation
    print("\n📋 Test 3: Requirements gathering simulation")
    print("-" * 40)
    
    # Simulate what happens when user fills the requirements modal
    enhanced_query = "I want to visit Disney World from New York for 5 days starting August 10th for 2 adults with theme_parks interests on a moderate budget"
    print(f"Enhanced Query: {enhanced_query}")
    
    response3 = requests.post(
        f"{base_url}/trip-planner/plan-trip-natural",
        json={"query": enhanced_query},
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status Code: {response3.status_code}")
    result3 = response3.json()
    
    if result3.get("success"):
        print("✅ Successfully planned trip with requirements")
        trip_plan = result3.get("trip_plan", {})
        summary = trip_plan.get("summary", {})
        print(f"Budget: {summary.get('budget_preference')}")
        print(f"Travelers: {summary.get('travelers')}")
        
        # Check if activities are generated
        itinerary = trip_plan.get("itinerary", [])
        if itinerary:
            print("Activities generated:")
            for day in itinerary[:2]:
                activities = day.get("activities", [])
                print(f"  Day {day.get('day')}: {activities}")
    else:
        print(f"❌ Failed to plan trip with requirements: {result3.get('error')}")
    
    print("\n" + "=" * 50)
    print("🎉 Complete flow test finished!")

if __name__ == "__main__":
    # Wait a moment for server to start
    print("Waiting for server to start...")
    time.sleep(2)
    
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}") 