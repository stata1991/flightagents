#!/usr/bin/env python3
"""
Test Smart Airport Logic for National Parks
Tests the Yosemite → SFO/SJC logic
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.smart_destination_service import SmartDestinationService

async def test_smart_airport_logic():
    """Test the smart airport logic for national parks."""
    
    print("🧪 Testing Smart Airport Logic for National Parks")
    print("=" * 60)
    
    service = SmartDestinationService()
    
    # Test 1: Yosemite National Park
    print("\n1️⃣ Testing Yosemite National Park:")
    print("-" * 40)
    
    user_input = "plan a trip to Yosemite National Park for 2 people, 5 days, starting next month"
    
    # Analyze trip type
    trip_analysis = await service.analyze_trip_type(user_input)
    print(f"Trip Analysis: {trip_analysis}")
    
    if trip_analysis["trip_type"] == "national_park":
        print("✅ Correctly identified as national park trip")
        
        # Get smart airport recommendation
        airport_rec = await service.get_smart_airport_recommendation(
            trip_analysis["destination"], 
            trip_analysis["trip_type"]
        )
        
        if airport_rec:
            print("✅ Smart airport recommendation generated:")
            print(f"   Primary Airport: {airport_rec.get('airport_name', 'N/A')}")
            print(f"   Airport Code: {airport_rec.get('airport_code', 'N/A')}")
            print(f"   Type: {airport_rec.get('airport_type', 'N/A')}")
            print(f"   Reasoning: {airport_rec.get('reasoning', 'N/A')}")
            print(f"   Transportation: {airport_rec.get('transportation_options', [])}")
            print(f"   Minimum Days: {airport_rec.get('minimum_days', 'N/A')}")
            
            if airport_rec.get('cost_considerations'):
                print("   Cost Considerations:")
                for key, value in airport_rec['cost_considerations'].items():
                    print(f"     {key}: {value}")
        else:
            print("❌ Failed to generate airport recommendation")
    
    # Test 2: Yellowstone National Park
    print("\n2️⃣ Testing Yellowstone National Park:")
    print("-" * 40)
    
    user_input2 = "I want to visit Yellowstone National Park for a week"
    
    trip_analysis2 = await service.analyze_trip_type(user_input2)
    print(f"Trip Analysis: {trip_analysis2}")
    
    if trip_analysis2["trip_type"] == "national_park":
        airport_rec2 = await service.get_smart_airport_recommendation(
            trip_analysis2["destination"], 
            trip_analysis2["trip_type"]
        )
        
        if airport_rec2:
            print("✅ Smart airport recommendation generated:")
            print(f"   Primary Airport: {airport_rec2.get('airport_name', 'N/A')}")
            print(f"   Airport Code: {airport_rec2.get('airport_code', 'N/A')}")
    
    # Test 3: Multi-city trip
    print("\n3️⃣ Testing Multi-City Trip (Italy):")
    print("-" * 40)
    
    user_input3 = "plan a trip to Rome, Florence, and Venice for 12 days"
    
    trip_analysis3 = await service.analyze_trip_type(user_input3)
    print(f"Trip Analysis: {trip_analysis3}")
    
    if trip_analysis3["trip_type"] == "multi_city":
        print("✅ Correctly identified as multi-city trip")
        
        route_suggestion = service.get_multi_city_route_suggestion(trip_analysis3["destination"])
        
        if route_suggestion:
            print("✅ Route suggestion generated:")
            print(f"   Cities: {', '.join(route_suggestion.get('cities', []))}")
            print(f"   Route Type: {route_suggestion.get('route_type', 'N/A')}")
            print(f"   Minimum Days: {route_suggestion.get('minimum_days', 'N/A')}")
            
            if route_suggestion.get('transportation'):
                print("   Transportation:")
                for route, details in route_suggestion['transportation'].items():
                    print(f"     {route}: {details['method']} - {details['duration']} - {details['cost']}")
    
    print("\n" + "=" * 60)
    print("🎯 Smart Airport Logic Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_smart_airport_logic())
