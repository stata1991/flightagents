#!/usr/bin/env python3
"""
Deep Link Testing Script
Tests the deep link generation logic for flights and hotels
"""

import json
from datetime import datetime, timedelta

def test_flight_deep_links():
    """Test flight deep link generation"""
    print("🛫 Testing Flight Deep Links")
    print("=" * 50)
    
    # Test parameters
    trip_origin = "Dallas"
    trip_destination = "Las Vegas"
    start_date = "2025-08-27"
    travelers = 2
    children = 0
    
    # Test Expedia link generation
    formatted_date = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    
    # Expedia parameters
    expedia_params = {
        'leg1': f'from:{trip_origin},to:{trip_destination},departure:{formatted_date}TANYT',
        'passengers': f'adults:{travelers},children:{children}'
    }
    
    expedia_url = f"https://www.expedia.com/Flights-Search?{'&'.join([f'{k}={v}' for k, v in expedia_params.items()])}"
    
    # Skyscanner URL
    skyscanner_url = f"https://www.skyscanner.com/transport/flights/{trip_origin}/{trip_destination}/{formatted_date}/?adults={travelers}&children={children}"
    
    # Kayak URL
    kayak_url = f"https://www.kayak.com/flights/{trip_origin}-{trip_destination}/{formatted_date}?adults={travelers}&children={children}"
    
    print(f"Origin: {trip_origin}")
    print(f"Destination: {trip_destination}")
    print(f"Date: {start_date}")
    print(f"Travelers: {travelers}")
    print()
    
    print("Generated URLs:")
    print(f"Expedia: {expedia_url}")
    print(f"Skyscanner: {skyscanner_url}")
    print(f"Kayak: {kayak_url}")
    print()
    
    return {
        "expedia": expedia_url,
        "skyscanner": skyscanner_url,
        "kayak": kayak_url
    }

def test_hotel_deep_links():
    """Test hotel deep link generation"""
    print("🏨 Testing Hotel Deep Links")
    print("=" * 50)
    
    # Test parameters
    trip_destination = "Las Vegas"
    start_date = "2025-08-27"
    duration = 5
    travelers = 2
    children = 0
    
    # Calculate end date
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = start + timedelta(days=duration)
    end_date = end.strftime("%Y-%m-%d")
    formatted_start_date = start.strftime("%Y-%m-%d")
    
    # Booking.com parameters
    booking_params = {
        'ss': trip_destination,
        'checkin': formatted_start_date,
        'checkout': end_date,
        'group_adults': travelers,
        'group_children': children,
        'no_rooms': 1
    }
    
    booking_url = f"https://www.booking.com/search.html?{'&'.join([f'{k}={v}' for k, v in booking_params.items()])}"
    
    # Expedia parameters
    expedia_params = {
        'destination': trip_destination,
        'checkin': formatted_start_date,
        'checkout': end_date,
        'adults': travelers,
        'children': children
    }
    
    expedia_url = f"https://www.expedia.com/Hotel-Search?{'&'.join([f'{k}={v}' for k, v in expedia_params.items()])}"
    
    # Hotels.com URL
    hotels_url = f"https://www.hotels.com/search.html?destination={trip_destination}&checkin={formatted_start_date}&checkout={end_date}&adults={travelers}&children={children}"
    
    print(f"Destination: {trip_destination}")
    print(f"Check-in: {start_date}")
    print(f"Check-out: {end_date}")
    print(f"Duration: {duration} days")
    print(f"Travelers: {travelers}")
    print()
    
    print("Generated URLs:")
    print(f"Booking.com: {booking_url}")
    print(f"Expedia: {expedia_url}")
    print(f"Hotels.com: {hotels_url}")
    print()
    
    return {
        "booking": booking_url,
        "expedia": expedia_url,
        "hotels": hotels_url
    }

def test_url_validation():
    """Test if URLs are properly formatted"""
    print("🔍 Testing URL Validation")
    print("=" * 50)
    
    flight_urls = test_flight_deep_links()
    hotel_urls = test_hotel_deep_links()
    
    all_urls = {**flight_urls, **hotel_urls}
    
    print("URL Validation Results:")
    for name, url in all_urls.items():
        # Basic validation
        is_valid = url.startswith('http') and '?' in url
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{name}: {status}")
        
        # Check for required parameters
        if 'expedia' in name.lower():
            has_params = 'leg1=' in url or 'destination=' in url
            param_status = "✅ Has params" if has_params else "❌ Missing params"
            print(f"  {param_status}")
        elif 'booking' in name.lower():
            has_params = 'ss=' in url or 'checkin=' in url
            param_status = "✅ Has params" if has_params else "❌ Missing params"
            print(f"  {param_status}")
    
    print()

if __name__ == "__main__":
    print("🚀 Deep Link Testing Suite")
    print("=" * 60)
    print()
    
    test_flight_deep_links()
    print()
    test_hotel_deep_links()
    print()
    test_url_validation()
    
    print("✅ Deep link testing completed!") 