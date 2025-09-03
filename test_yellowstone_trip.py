#!/usr/bin/env python3
"""
Test Complete Trip Planning Flow
Dallas → Yellowstone National Park
2 people, 5 days, $3500 budget, hiking + relaxation
"""

import asyncio
import sys
import os
import json

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.maps_weather_service import MapsWeatherService
from services.smart_destination_service import SmartDestinationService
from services.budget_allocation_service import BudgetAllocationService

async def test_yellowstone_trip():
    """Test the complete trip planning flow for Dallas to Yellowstone."""
    
    print("🏔️ Testing Complete Trip Planning Flow")
    print("=" * 60)
    print("📍 Trip Request:")
    print("   From: Dallas, TX")
    print("   To: Yellowstone National Park")
    print("   Travelers: 2 people")
    print("   Dates: 2025-09-25 for 5 days")
    print("   Budget: $3,500")
    print("   Interests: Hiking, Relaxation, Casual Getaway")
    print("=" * 60)
    
    # Initialize services
    maps_service = MapsWeatherService()
    smart_service = SmartDestinationService()
    budget_service = BudgetAllocationService()
    
    # Step 1: Get destination coordinates
    print("\n1️⃣ Getting Yellowstone Coordinates...")
    print("-" * 40)
    
    yellowstone_coords = await maps_service.get_destination_coordinates("Yellowstone National Park")
    if yellowstone_coords:
        print(f"✅ Coordinates: {yellowstone_coords['lat']:.4f}, {yellowstone_coords['lng']:.4f}")
        print(f"   Address: {yellowstone_coords['formatted_address']}")
        print(f"   Source: {yellowstone_coords['source']}")
    else:
        print("❌ Could not get coordinates")
        return
    
    # Step 2: Find nearby airports
    print("\n2️⃣ Finding Nearby Airports...")
    print("-" * 40)
    
    airports = await maps_service.find_nearby_airports(
        yellowstone_coords['lat'], 
        yellowstone_coords['lng'],
        radius_km=300  # Larger radius for Yellowstone
    )
    
    if airports:
        print(f"✅ Found {len(airports)} airports within 300km:")
        for i, airport in enumerate(airports[:5]):  # Show top 5
            print(f"   {i+1}. {airport['name']} ({airport['code']})")
            print(f"      Distance: {airport['distance']:.1f} km")
            print(f"      City: {airport['city']}, {airport['country']}")
            print(f"      Source: {airport['source']}")
            print()
    else:
        print("❌ Could not find nearby airports")
    
    # Step 3: Analyze trip type
    print("\n3️⃣ Analyzing Trip Type...")
    print("-" * 40)
    
    user_input = "plan a trip from Dallas to Yellowstone National Park for 2 people, 5 days, starting 2025-09-25 with $3500 budget for hiking and relaxation"
    
    trip_analysis = await smart_service.analyze_trip_type(user_input)
    print(f"✅ Trip Analysis: {trip_analysis}")
    
    # Step 4: Get smart airport recommendation
    print("\n4️⃣ Getting Smart Airport Recommendation...")
    print("-" * 40)
    
    if trip_analysis["trip_type"] == "national_park":
        airport_rec = await smart_service.get_smart_airport_recommendation(
            trip_analysis["destination"], 
            trip_analysis["trip_type"]
        )
        
        if airport_rec:
            print("✅ Smart Airport Recommendation:")
            print(f"   Primary Airport: {airport_rec.get('airport_name', 'N/A')}")
            print(f"   Airport Code: {airport_rec.get('airport_code', 'N/A')}")
            print(f"   Type: {airport_rec.get('airport_type', 'N/A')}")
            print(f"   Distance: {airport_rec.get('distance_to_destination', 'N/A')}")
            print(f"   Reasoning: {airport_rec.get('reasoning', 'N/A')}")
            
            if airport_rec.get('transportation_options'):
                print(f"   Transportation: {', '.join(airport_rec['transportation_options'])}")
            
            if airport_rec.get('minimum_days'):
                print(f"   Minimum Days: {airport_rec['minimum_days']}")
        else:
            print("❌ Could not generate airport recommendation")
    
    # Step 5: Budget Allocation
    print("\n5️⃣ Budget Allocation Analysis...")
    print("-" * 40)
    
    total_budget = 3500
    travelers = 2
    duration_days = 5
    
    budget_breakdown = budget_service.calculate_budget_allocation(
        total_budget=total_budget,
        trip_duration=duration_days,
        travelers=travelers
    )
    
    if budget_breakdown:
        print("✅ Budget Breakdown:")
        print(f"   Total Budget: ${total_budget:,}")
        print(f"   Per Person: ${total_budget/travelers:,}")
        print(f"   Per Day: ${total_budget/duration_days:,}")
        print()
        
        # Display budget breakdown
        breakdown = budget_breakdown.get("budget_breakdown", {})
        percentages = budget_breakdown.get("budget_percentages", {})
        
        for category, amount in breakdown.items():
            percentage = percentages.get(category, "N/A")
            print(f"   {category.title()}: {amount} ({percentage})")
        
        print()
        
        # Display hotel recommendations
        hotel_info = budget_breakdown.get("hotel_budget_allocation", {})
        if hotel_info:
            print("🏨 Hotel Budget Details:")
            print(f"   Per Night: {hotel_info.get('per_night', 'N/A')}")
            print(f"   Per Person/Night: {hotel_info.get('per_person_per_night', 'N/A')}")
            print(f"   Recommendation: {hotel_info.get('recommendation', 'N/A')}")
    else:
        print("❌ Could not allocate budget")
    
    # Step 6: Transportation Planning
    print("\n6️⃣ Transportation Planning...")
    print("-" * 40)
    
    if airports:
        primary_airport = airports[0]  # Closest airport
        print(f"✅ Primary Airport: {primary_airport['name']} ({primary_airport['code']})")
        print(f"   Distance from Yellowstone: {primary_airport['distance']:.1f} km")
        print(f"   Location: {primary_airport['city']}, {primary_airport['country']}")
        print()
        
        print("🚗 Transportation Options:")
        print("   • Rental Car: Highly recommended for Yellowstone access")
        print("   • Shuttle Service: Available from major airports")
        print("   • Private Tour: Guided transportation included")
        print("   • Public Transport: Limited availability in national parks")
    
    # Step 7: Trip Summary
    print("\n7️⃣ Complete Trip Summary...")
    print("-" * 40)
    
    print("🎯 TRIP SUMMARY:")
    print(f"   Origin: Dallas, TX")
    print(f"   Destination: Yellowstone National Park")
    print(f"   Dates: 2025-09-25 to 2025-09-30 (5 days)")
    print(f"   Travelers: 2 people")
    print(f"   Budget: $3,500")
    print(f"   Interests: Hiking, Relaxation, Casual Getaway")
    print()
    
    if airports:
        print("✈️ FLIGHT RECOMMENDATIONS:")
        print(f"   Primary: {airports[0]['name']} ({airports[0]['code']}) - {airports[0]['distance']:.1f} km")
        if len(airports) > 1:
            print(f"   Alternative: {airports[1]['name']} ({airports[1]['code']}) - {airports[1]['distance']:.1f} km")
        print()
    
    print("🏞️ ACTIVITY RECOMMENDATIONS:")
    print("   • Hiking: Old Faithful Geyser Basin, Grand Canyon of Yellowstone")
    print("   • Relaxation: Hot Springs, Wildlife Viewing, Scenic Drives")
    print("   • Casual Getaway: Photography, Nature Walks, Ranger Programs")
    print()
    
    print("💰 BUDGET ALLOCATION:")
    if budget_breakdown:
        breakdown = budget_breakdown.get("budget_breakdown", {})
        for category, amount in breakdown.items():
            print(f"   • {category.title()}: {amount}")
    
    print("\n" + "=" * 60)
    print("🎯 Yellowstone Trip Planning Complete!")

if __name__ == "__main__":
    asyncio.run(test_yellowstone_trip())
