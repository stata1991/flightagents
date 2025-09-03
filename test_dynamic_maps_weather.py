#!/usr/bin/env python3
"""
Test Dynamic Maps and Weather Integration
Tests the new service without hardcoded data
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.maps_weather_service import MapsWeatherService
from services.smart_destination_service import SmartDestinationService

async def test_maps_weather_service():
    """Test the maps and weather service."""
    
    print("🧪 Testing Dynamic Maps and Weather Integration")
    print("=" * 60)
    
    # Test Maps and Weather Service
    print("\n1️⃣ Testing Maps and Weather Service:")
    print("-" * 40)
    
    service = MapsWeatherService()
    
    # Test destination coordinates
    print("📍 Testing destination coordinates...")
    coords = await service.get_destination_coordinates("Yosemite National Park")
    if coords:
        print(f"✅ Coordinates: {coords['lat']:.4f}, {coords['lng']:.4f}")
        print(f"   Address: {coords['formatted_address']}")
    else:
        print("❌ Could not get coordinates (likely missing GOOGLE_MAPS_API_KEY)")
    
    # Test nearby airports
    if coords:
        print("\n✈️ Testing nearby airports...")
        airports = await service.find_nearby_airports(coords['lat'], coords['lng'])
        if airports:
            print(f"✅ Found {len(airports)} airports:")
            for i, airport in enumerate(airports[:3]):  # Show first 3
                print(f"   {i+1}. {airport['name']} ({airport['code']}) - {airport['distance']:.1f} km")
        else:
            print("❌ Could not find nearby airports")
    
    # Test weather forecast
    if coords:
        print("\n🌤️ Testing weather forecast...")
        weather = await service.get_weather_forecast(coords['lat'], coords['lng'])
        if weather:
            print(f"✅ Weather for {weather['destination']}, {weather['country']}:")
            for forecast in weather['forecasts'][:3]:  # Show first 3 days
                print(f"   {forecast['date']}: {forecast['temp_min']}°C - {forecast['temp_max']}°C, {forecast['description']}")
        else:
            print("❌ Could not get weather forecast (likely missing OPENWEATHER_API_KEY)")
    
    # Test comprehensive destination analysis
    print("\n🔍 Testing comprehensive destination analysis...")
    analysis = await service.analyze_destination_for_travel("Yosemite National Park")
    if analysis and "error" not in analysis:
        print("✅ Comprehensive analysis successful:")
        print(f"   Destination: {analysis['destination']}")
        print(f"   Coordinates: {analysis['coordinates']['lat']:.4f}, {analysis['coordinates']['lng']:.4f}")
        
        airports = analysis.get('airports', {})
        if airports.get('primary'):
            primary = airports['primary']
            print(f"   Primary Airport: {primary['name']} ({primary['code']})")
            print(f"   Distance: {primary['distance']:.1f} km")
            print(f"   Recommendation: {airports['reasoning']}")
        
        if analysis.get('weather'):
            print(f"   Weather: Available for {len(analysis['weather']['forecasts'])} days")
        
        if analysis.get('transportation'):
            print(f"   Transportation: {', '.join(analysis['transportation'][:3])}")
    else:
        print("❌ Comprehensive analysis failed")
        if analysis:
            print(f"   Error: {analysis.get('error', 'Unknown error')}")

async def test_enhanced_smart_destination():
    """Test the enhanced smart destination service."""
    
    print("\n2️⃣ Testing Enhanced Smart Destination Service:")
    print("-" * 40)
    
    service = SmartDestinationService()
    
    # Test Yosemite National Park
    print("🏞️ Testing Yosemite National Park:")
    user_input = "plan a trip to Yosemite National Park for 2 people, 5 days, starting next month"
    
    # Analyze trip type
    trip_analysis = await service.analyze_trip_type(user_input)
    print(f"   Trip Analysis: {trip_analysis}")
    
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
            print(f"   Distance: {airport_rec.get('distance_to_destination', 'N/A')}")
            
            if airport_rec.get('weather_forecast'):
                print("   Weather: Available for trip planning")
            
            if airport_rec.get('maps_integration'):
                print("   Maps: Integrated with coordinates and analysis")
            
            if airport_rec.get('transportation_options'):
                print(f"   Transportation: {', '.join(airport_rec['transportation_options'][:3])}")
        else:
            print("❌ Failed to generate airport recommendation")
    
    print("\n" + "=" * 60)
    print("🎯 Dynamic Maps and Weather Integration Test Complete!")

async def main():
    """Run all tests."""
    await test_maps_weather_service()
    await test_enhanced_smart_destination()

if __name__ == "__main__":
    asyncio.run(main())
