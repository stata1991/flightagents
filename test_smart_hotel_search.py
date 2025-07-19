#!/usr/bin/env python3
"""
Test script for the enhanced hotel search with smart budget handling
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# Import with proper path handling
from api.hotel_client import HotelClient
from api.models import HotelSearchRequest

async def test_smart_hotel_search():
    """Test the smart hotel search functionality"""
    
    print("🧪 Testing Smart Hotel Search with Budget Handling")
    print("=" * 60)
    
    # Initialize the hotel client
    hotel_client = HotelClient()
    
    # Test parameters
    destination = "New York"
    start_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
    end_date = (datetime.now() + timedelta(days=18)).strftime('%Y-%m-%d')
    travelers = 2
    
    print(f"📍 Destination: {destination}")
    print(f"📅 Check-in: {start_date}")
    print(f"📅 Check-out: {end_date}")
    print(f"👥 Travelers: {travelers}")
    print()
    
    # Test 1: Budget search
    print("🔍 Test 1: Budget Search (max $150/night)")
    print("-" * 40)
    
    budget_request = HotelSearchRequest(
        location=destination,
        check_in=start_date,
        check_out=end_date,
        adults=travelers,
        children=[],
        rooms=1,
        currency="USD"
    )
    
    budget_results = hotel_client.smart_hotel_search(
        request=budget_request,
        max_budget=150,
        budget_expansion_steps=3
    )
    
    print(f"✅ Budget search completed")
    print(f"📊 Total hotels found: {budget_results.total_results}")
    print(f"🔍 Search attempts: {budget_results.search_metadata.get('search_attempts', 0)}")
    print(f"🌍 Destinations tried: {budget_results.search_metadata.get('destinations_tried', 0)}")
    
    # Categorize results
    budget_hotels = []
    moderate_hotels = []
    luxury_hotels = []
    
    for hotel_result in budget_results.hotels:
        price = hotel_result.average_price_per_night or 0
        if price <= 150:
            budget_hotels.append(hotel_result)
        elif price <= 300:
            moderate_hotels.append(hotel_result)
        else:
            luxury_hotels.append(hotel_result)
    
    print(f"💰 Budget hotels (≤$150): {len(budget_hotels)}")
    print(f"🏨 Moderate hotels ($151-$300): {len(moderate_hotels)}")
    print(f"🌟 Luxury hotels (>$300): {len(luxury_hotels)}")
    print()
    
    # Show sample hotels
    if budget_hotels:
        print("💰 Sample Budget Hotels:")
        for i, hotel in enumerate(budget_hotels[:2]):
            print(f"  {i+1}. {hotel.hotel.name}")
            print(f"     💰 ${hotel.average_price_per_night}/night")
            print(f"     ⭐ {hotel.hotel.rating}/10 ({hotel.hotel.star_rating} stars)")
            print(f"     📍 {hotel.hotel.address}")
            print()
    
    if moderate_hotels:
        print("🏨 Sample Moderate Hotels:")
        for i, hotel in enumerate(moderate_hotels[:2]):
            print(f"  {i+1}. {hotel.hotel.name}")
            print(f"     💰 ${hotel.average_price_per_night}/night")
            print(f"     ⭐ {hotel.hotel.rating}/10 ({hotel.hotel.star_rating} stars)")
            print(f"     📍 {hotel.hotel.address}")
            print()
    
    # Test 2: Moderate search
    print("🔍 Test 2: Moderate Search (max $300/night)")
    print("-" * 40)
    
    moderate_results = hotel_client.smart_hotel_search(
        request=budget_request,
        max_budget=300,
        budget_expansion_steps=3
    )
    
    print(f"✅ Moderate search completed")
    print(f"📊 Total hotels found: {moderate_results.total_results}")
    print(f"🔍 Search attempts: {moderate_results.search_metadata.get('search_attempts', 0)}")
    print(f"🌍 Destinations tried: {moderate_results.search_metadata.get('destinations_tried', 0)}")
    print()
    
    # Test 3: Luxury search
    print("🔍 Test 3: Luxury Search (max $500/night)")
    print("-" * 40)
    
    luxury_results = hotel_client.smart_hotel_search(
        request=budget_request,
        max_budget=500,
        budget_expansion_steps=3
    )
    
    print(f"✅ Luxury search completed")
    print(f"📊 Total hotels found: {luxury_results.total_results}")
    print(f"🔍 Search attempts: {luxury_results.search_metadata.get('search_attempts', 0)}")
    print(f"🌍 Destinations tried: {luxury_results.search_metadata.get('destinations_tried', 0)}")
    print()
    
    # Test 4: No budget limit (smart expansion)
    print("🔍 Test 4: No Budget Limit (Smart Expansion)")
    print("-" * 40)
    
    unlimited_results = hotel_client.smart_hotel_search(
        request=budget_request,
        max_budget=None,  # No limit
        budget_expansion_steps=5
    )
    
    print(f"✅ Unlimited search completed")
    print(f"📊 Total hotels found: {unlimited_results.total_results}")
    print(f"🔍 Search attempts: {unlimited_results.search_metadata.get('search_attempts', 0)}")
    print(f"🌍 Destinations tried: {unlimited_results.search_metadata.get('destinations_tried', 0)}")
    print()
    
    # Test 5: Destination search (Step 1 of the API flow)
    print("🔍 Test 5: Destination Search (Step 1)")
    print("-" * 40)
    
    dest_results = hotel_client.search_destination(destination)
    
    if dest_results.get("status") and dest_results.get("destinations"):
        print(f"✅ Found {len(dest_results['destinations'])} destination options:")
        for i, dest in enumerate(dest_results['destinations'][:5]):
            print(f"  {i+1}. {dest['label']}")
            print(f"     🆔 ID: {dest['dest_id']}")
            print(f"     🏨 Hotels: {dest.get('hotels', 'N/A')}")
            print(f"     📍 Type: {dest.get('search_type', 'N/A')}")
            print()
    else:
        print(f"❌ Destination search failed: {dest_results.get('error', 'Unknown error')}")
    
    # Test 6: Get filters for first destination
    if dest_results.get("destinations"):
        print("🔍 Test 6: Get Filters (Step 2)")
        print("-" * 40)
        
        first_dest = dest_results['destinations'][0]
        filters_result = hotel_client.get_filters(
            dest_id=first_dest['dest_id'],
            search_type=first_dest['search_type'],
            check_in=start_date,
            check_out=end_date,
            adults=travelers,
            rooms=1
        )
        
        if filters_result.get("status") and filters_result.get("data"):
            data = filters_result["data"]
            print(f"✅ Filters retrieved for {first_dest['label']}")
            print(f"📊 Total results available: {data.get('pagination', {}).get('nbResultsTotal', 'N/A')}")
            print(f"🏨 Available hotels: {data.get('availabilityInfo', {}).get('totalAvailableNotAutoextended', 'N/A')}")
            
            # Extract price range
            for filter_item in data.get("filters", []):
                if filter_item.get("field") == "price":
                    price_filter = filter_item
                    print(f"💰 Price range: ${price_filter.get('min', 'N/A')} - ${price_filter.get('max', 'N/A')}")
                    print(f"💱 Currency: {price_filter.get('currency', 'N/A')}")
                    break
        else:
            print(f"❌ Filters retrieval failed: {filters_result.get('error', 'Unknown error')}")
    
    print("\n🎉 Smart Hotel Search Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_smart_hotel_search()) 