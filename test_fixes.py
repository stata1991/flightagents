#!/usr/bin/env python3
"""
Test script to verify the fixes work
"""

import asyncio
import json
import sys
import os
import time
from dotenv import load_dotenv

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

load_dotenv()

from api.ai_agents import AITripPlanningAgent
from api.models import TripPlanningRequest, TripType, BudgetRange

async def test_fixes():
    """Test the fixes for the errors"""
    
    # Test 1: Trip with missing origin/destination
    print("🧪 Test 1: Trip with missing origin/destination")
    print("=" * 50)
    
    request1 = TripPlanningRequest(
        origin=None,  # Missing origin
        destination="San Francisco",
        start_date="2025-08-20",
        duration_days=3,
        travelers=2,
        trip_type=TripType.LEISURE,
        budget_range=BudgetRange.MODERATE,
        interests=["landmarks", "culture", "food"]
    )
    
    agent = AITripPlanningAgent()
    
    try:
        start_time = time.time()
        result1 = await agent.plan_trip_with_agents(request1)
        end_time = time.time()
        
        if "error" in result1:
            print(f"❌ Error: {result1['error']}")
        else:
            print(f"✅ Success! Generated in {end_time - start_time:.2f} seconds")
            
            # Check flight search results
            flight_results = result1.get("flight_search_results", {})
            if "message" in flight_results and "skipped" in flight_results["message"]:
                print("✅ Flight search correctly skipped for missing origin")
            else:
                print("❌ Flight search should have been skipped")
        
        print()
        
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
        print()
    
    # Test 2: Trip with complete information
    print("🧪 Test 2: Trip with complete information")
    print("=" * 50)
    
    request2 = TripPlanningRequest(
        origin="New York",
        destination="San Francisco",
        start_date="2025-08-20",
        duration_days=3,
        travelers=2,
        trip_type=TripType.LEISURE,
        budget_range=BudgetRange.MODERATE,
        interests=["landmarks", "culture", "food"]
    )
    
    try:
        start_time = time.time()
        result2 = await agent.plan_trip_with_agents(request2)
        end_time = time.time()
        
        if "error" in result2:
            print(f"❌ Error: {result2['error']}")
        else:
            print(f"✅ Success! Generated in {end_time - start_time:.2f} seconds")
            
            # Check itinerary generation
            itinerary = result2.get("itinerary", [])
            if itinerary:
                print(f"✅ Itinerary generated with {len(itinerary)} days")
                
                # Check for specific attractions
                destination_recs = result2.get("destination_recommendations", {})
                must_see = destination_recs.get("must_see_attractions", [])
                if must_see:
                    print(f"✅ Found {len(must_see)} must-see attractions")
                    for attraction in must_see[:3]:
                        print(f"   • {attraction.get('name', 'Attraction')}")
                else:
                    print("❌ No must-see attractions found")
            else:
                print("❌ No itinerary generated")
            
            # Check flight search results
            flight_results = result2.get("flight_search_results", {})
            if "flights" in flight_results:
                print(f"✅ Flight search successful with {len(flight_results['flights'])} flights")
            else:
                print("❌ Flight search failed")
        
        print()
        
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
        print()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_fixes()) 