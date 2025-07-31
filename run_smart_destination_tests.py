#!/usr/bin/env python3

import os
import sys
import asyncio

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.smart_destination_service import SmartDestinationService

async def run_basic_tests():
    """Run basic functionality tests without API calls."""
    
    print("🧪 Testing Smart Destination Service (Basic Tests)")
    print("=" * 60)
    
    # Set up service
    os.environ["RAPID_API_KEY"] = "test_key"
    service = SmartDestinationService()
    
    # Test 1: Trip Type Analysis
    print("\n1. Testing Trip Type Analysis:")
    test_cases = [
        ("Plan a trip to Yosemite National Park", "national_park", "yosemite"),
        ("Plan a trip from Dallas to Italy", "multi_city", "italy"),
        ("Visit Paris for a week", "single_destination", None),
        ("Yellowstone adventure", "national_park", "yellowstone"),
        ("France vacation", "multi_city", "france"),
        ("Rome Florence Venice trip", "multi_city", "italy")
    ]
    
    for user_input, expected_type, expected_destination in test_cases:
        result = await service.analyze_trip_type(user_input)
        status = "✅" if result["trip_type"] == expected_type else "❌"
        print(f"   {status} {user_input}")
        print(f"      Expected: {expected_type}, Got: {result['trip_type']}")
        if expected_destination:
            print(f"      Destination: {result.get('destination', 'None')}")
    
    # Test 2: Multi-City Route Suggestions
    print("\n2. Testing Multi-City Route Suggestions:")
    countries = ["italy", "france", "spain", "unknown_country"]
    
    for country in countries:
        result = service.get_multi_city_route_suggestion(country)
        if result:
            print(f"   ✅ {country.title()}: {result['cities']} ({result['route_type']})")
        else:
            print(f"   ❌ {country.title()}: No route found")
    
    # Test 3: Smart Itinerary Requests
    print("\n3. Testing Smart Itinerary Requests:")
    test_requests = [
        "Plan a trip to Yosemite National Park",
        "Plan a trip from Dallas to Italy",
        "Visit Paris for a week"
    ]
    
    for request in test_requests:
        result = await service.create_smart_itinerary_request(request)
        print(f"   ✅ {request}")
        print(f"      Type: {result['trip_type']}")
        if result.get('destination'):
            print(f"      Destination: {result['destination']}")
    
    print("\n✅ Basic tests completed successfully!")

async def run_api_tests():
    """Run tests with real API calls (requires valid API key)."""
    
    print("\n🌐 Testing with Real APIs...")
    print("=" * 60)
    
    service = SmartDestinationService()
    
    if not service.rapid_api_key or service.rapid_api_key == "test_key":
        print("❌ No valid RAPID_API_KEY found. Skipping API tests.")
        print("   Set RAPID_API_KEY environment variable to run API tests.")
        return
    
    # Test airport recommendations for national parks
    print("\n1. Testing Airport Recommendations:")
    destinations = ["Yosemite", "Yellowstone", "Grand Canyon"]
    
    for destination in destinations:
        print(f"\n   Testing: {destination}")
        result = await service.get_airports_near_destination(destination)
        
        if result:
            print(f"      ✅ Found {len(result['airports'])} airports")
            for airport in result['airports'][:3]:  # Show first 3
                print(f"         - {airport['name']} ({airport['code']}) - {airport['distance']:.1f}km")
        else:
            print(f"      ❌ No airports found")
    
    print("\n✅ API tests completed!")

def main():
    """Main test runner."""
    
    print("🚀 Smart Destination Service Test Suite")
    print("=" * 60)
    
    # Run basic tests
    asyncio.run(run_basic_tests())
    
    # Run API tests if requested
    if "--api" in sys.argv:
        asyncio.run(run_api_tests())
    
    print("\n🎉 All tests completed!")
    print("\nUsage:")
    print("   python3 run_smart_destination_tests.py          # Basic tests only")
    print("   python3 run_smart_destination_tests.py --api    # Include API tests")

if __name__ == "__main__":
    main() 