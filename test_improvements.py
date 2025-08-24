#!/usr/bin/env python3

import requests
import json
import time

def test_trip_planning():
    """Test the improved trip planning with more flights, hotels, and practical info"""
    
    url = "http://localhost:8000/api/hybrid/plan"
    
    # Test data
    trip_request = {
        "origin": "New York",
        "destination": "Paris",
        "start_date": "2024-06-15",
        "duration_days": 5,
        "travelers": 2,
        "budget_range": "moderate",
        "interests": ["culture", "food", "history"],
        "trip_type": "leisure"
    }
    
    print("🚀 Testing improved trip planning...")
    print(f"Request: {json.dumps(trip_request, indent=2)}")
    
    try:
        response = requests.post(url, json=trip_request, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                itinerary = result.get("itinerary", {})
                
                print("\n✅ Trip planning successful!")
                
                # Check flights
                transportation = itinerary.get("transportation", {})
                total_flights = 0
                for category in ["fastest", "cheapest", "optimal"]:
                    flights = transportation.get(category, [])
                    total_flights += len(flights)
                    print(f"  ✈️ {category.capitalize()} flights: {len(flights)}")
                
                print(f"  📊 Total flights: {total_flights}")
                
                # Check hotels
                accommodation = itinerary.get("accommodation", {})
                total_hotels = 0
                for category in ["budget", "moderate", "luxury"]:
                    hotels = accommodation.get(category, [])
                    total_hotels += len(hotels)
                    print(f"  🏨 {category.capitalize()} hotels: {len(hotels)}")
                
                print(f"  📊 Total hotels: {total_hotels}")
                
                # Check practical info
                practical_info = itinerary.get("practical_info", {})
                cultural_insights = itinerary.get("cultural_insights", {})
                
                print(f"  💰 Currency: {practical_info.get('currency', 'N/A')}")
                print(f"  🌍 Language: {practical_info.get('language', 'N/A')}")
                print(f"  🚨 Emergency numbers: {practical_info.get('emergency_numbers', 'N/A')}")
                print(f"  🎒 Packing suggestions: {len(practical_info.get('packing_suggestions', []))} items")
                print(f"  🌍 Cultural customs: {len(cultural_insights.get('local_customs', []))} tips")
                
                # Check trip summary
                trip_summary = itinerary.get("trip_summary", {})
                print(f"  📋 Trip title: {trip_summary.get('title', 'N/A')}")
                print(f"  📅 Duration: {trip_summary.get('duration', 'N/A')} days")
                
                # Check other new fields
                print(f"  🍽️ Restaurants: {len(itinerary.get('restaurants', []))}")
                print(f"  🏛️ Key attractions: {len(itinerary.get('key_attractions', []))}")
                print(f"  📝 Insider tips: {len(itinerary.get('insider_tips', []))}")
                print(f"  📋 Booking priorities: {len(itinerary.get('booking_priorities', []))}")
                
                # Verify we have the expected number of options
                if total_flights >= 6:  # Should have at least 6 flights (2 outbound + 2 return in each category)
                    print("  ✅ Flight options: SUCCESS (6+ flights)")
                else:
                    print(f"  ❌ Flight options: FAILED (only {total_flights} flights)")
                
                if total_hotels >= 6:  # Should have at least 6 hotels (2 in each category)
                    print("  ✅ Hotel options: SUCCESS (6+ hotels)")
                else:
                    print(f"  ❌ Hotel options: FAILED (only {total_hotels} hotels)")
                
                # Check if practical info has content
                practical_fields = [
                    practical_info.get('currency'),
                    practical_info.get('language'),
                    practical_info.get('emergency_numbers'),
                    practical_info.get('packing_suggestions'),
                    cultural_insights.get('local_customs')
                ]
                
                filled_fields = sum(1 for field in practical_fields if field and (isinstance(field, list) and len(field) > 0 or isinstance(field, str) and field.strip()))
                
                if filled_fields >= 3:
                    print("  ✅ Practical info: SUCCESS (3+ fields filled)")
                else:
                    print(f"  ❌ Practical info: FAILED (only {filled_fields} fields filled)")
                
            else:
                print(f"❌ Trip planning failed: {result.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (120 seconds)")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_trip_planning()
