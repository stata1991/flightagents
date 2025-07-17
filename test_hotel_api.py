#!/usr/bin/env python3
"""
Test script for Hotel API integration
"""

import asyncio
import sys
import os

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.hotel_client import HotelClient
from api.models import HotelSearchRequest

async def test_hotel_search():
    """Test hotel search functionality"""
    print("Testing Hotel API Integration...")
    
    # Initialize hotel client
    hotel_client = HotelClient()
    
    # Test destination search first
    print("\n1. Testing destination search...")
    try:
        dest_result = hotel_client.search_destination("Los Angeles")
        print(f"Destination search completed. Found {len(dest_result.get('destinations', []))} destinations.")
        
        if dest_result.get("destinations"):
            dest = dest_result["destinations"][0]
            print(f"First destination: {dest['name']} (ID: {dest['dest_id']})")
            print(f"Type: {dest['search_type']}")
            print(f"Hotels available: {dest['hotels']}")
        
    except Exception as e:
        print(f"Error testing destination search: {e}")
    
    # Test hotel search
    print("\n2. Testing hotel search...")
    try:
        request = HotelSearchRequest(
            location="Los Angeles",
            check_in="2025-08-18",
            check_out="2025-08-22",
            adults=1,
            children=[],
            rooms=1,
            currency="AED",
            language="en-us",
            page_number=1
        )
        
        result = hotel_client.search_hotels(request)
        
        print(f"Search completed. Found {result.total_results} hotels.")
        print(f"Location: {result.location}")
        print(f"Check-in: {result.check_in}")
        print(f"Check-out: {result.check_out}")
        
        if result.hotels:
            print(f"\nTop {len(result.hotels)} hotels found:")
            for i, hotel_result in enumerate(result.hotels[:3], 1):
                hotel = hotel_result.hotel
                print(f"\n{i}. {hotel.name}")
                print(f"   Hotel ID: {hotel.hotel_id}")
                print(f"   Rating: {hotel.rating}")
                print(f"   Review Score: {hotel.review_score}")
                print(f"   Review Count: {hotel.review_count}")
                print(f"   Star Rating: {hotel.star_rating}")
                print(f"   Price: {hotel_result.average_price_per_night} {hotel_result.currency}")
                print(f"   Photos: {len(hotel.photos)} available")
        else:
            print("No hotels found.")
            
    except Exception as e:
        print(f"Error testing hotel search: {e}")
    
    # Test hotel details
    print("\n3. Testing hotel details...")
    try:
        # Use a hotel ID from the search results
        if result.hotels:
            hotel_id = result.hotels[0].hotel.hotel_id
            details = hotel_client.get_hotel_details(
                hotel_id=hotel_id,
                check_in="2025-08-18",
                check_out="2025-08-22",
                adults=1
            )
            print(f"Hotel details retrieved for hotel {hotel_id}: {details}")
        else:
            print("No hotels found to test details with")
    except Exception as e:
        print(f"Error testing hotel details: {e}")
    
    # Test booking URL generation
    print("\n4. Testing booking URL generation...")
    try:
        if result.hotels:
            hotel_id = result.hotels[0].hotel.hotel_id
            booking_url = hotel_client.generate_hotel_booking_url(
                hotel_id=hotel_id,
                check_in="2025-08-18",
                check_out="2025-08-22",
                adults=1,
                children=[],
                rooms=1,
                currency="AED"
            )
            print(f"Generated booking URL for hotel {hotel_id}: {booking_url}")
        else:
            print("No hotels found to test booking URL with")
    except Exception as e:
        print(f"Error testing booking URL generation: {e}")
    
    # Test popular destinations
    print("\n5. Testing popular destinations...")
    try:
        # This would typically call an API endpoint
        popular_destinations = [
            {"name": "New York", "country": "United States", "dest_id": "20088325"},
            {"name": "London", "country": "United Kingdom", "dest_id": "-2601889"},
            {"name": "Paris", "country": "France", "dest_id": "-1456928"}
        ]
        print(f"Popular destinations: {popular_destinations}")
    except Exception as e:
        print(f"Error testing popular destinations: {e}")

def test_hotel_models():
    """Test hotel model creation"""
    print("\nTesting Hotel Models...")
    
    try:
        from api.models import HotelSearchRequest, HotelInfo, HotelRoom, HotelSearchResult
        
        # Test HotelSearchRequest
        request = HotelSearchRequest(
            location="Paris",
            check_in="2024-12-20",
            check_out="2024-12-23",
            adults=2,
            children=[5, 8],
            rooms=1
        )
        print(f"HotelSearchRequest created: {request}")
        
        # Test HotelInfo
        hotel_info = HotelInfo(
            hotel_id="12345",
            name="Grand Hotel Paris",
            address="123 Champs-Élysées",
            city="Paris",
            country="France",
            rating=4.5,
            star_rating=5
        )
        print(f"HotelInfo created: {hotel_info}")
        
        # Test HotelRoom
        room = HotelRoom(
            room_id="room123",
            room_type="Deluxe Double",
            price_per_night=200.0,
            total_price=600.0,
            currency="USD"
        )
        print(f"HotelRoom created: {room}")
        
        # Test HotelSearchResult
        result = HotelSearchResult(
            hotel=hotel_info,
            rooms=[room],
            average_price_per_night=200.0,
            total_price=600.0,
            currency="USD"
        )
        print(f"HotelSearchResult created: {result}")
        
    except Exception as e:
        print(f"Error testing hotel models: {e}")

if __name__ == "__main__":
    print("Hotel API Integration Test")
    print("=" * 50)
    
    # Test models first
    test_hotel_models()
    
    # Test API functionality
    asyncio.run(test_hotel_search())
    
    print("\nTest completed!") 