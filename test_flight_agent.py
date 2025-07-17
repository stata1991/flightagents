#!/usr/bin/env python3
"""
Test script for the updated flight agent with Booking.com API
"""

import asyncio
import json
import sys
import os

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from ai_agents import AITripPlanningAgent, AgentTask, AgentType

async def test_flight_agent():
    """Test the flight search agent with real Booking.com API"""
    
    print("🧪 Testing Flight Search Agent with Booking.com API")
    print("=" * 60)
    
    # Initialize the agent
    agent = AITripPlanningAgent()
    
    # Test data
    test_data = {
        "origin": "Dallas",
        "destination": "Los Angeles", 
        "start_date": "2025-08-21",
        "duration_days": 5,
        "travelers": 1
    }
    
    print(f"📋 Test Parameters:")
    print(f"   Origin: {test_data['origin']}")
    print(f"   Destination: {test_data['destination']}")
    print(f"   Start Date: {test_data['start_date']}")
    print(f"   Duration: {test_data['duration_days']} days")
    print(f"   Travelers: {test_data['travelers']}")
    print()
    
    # Create agent task
    task = AgentTask(
        agent_type=AgentType.FLIGHT_SEARCH_AGENT,
        task_description="Search for flights from Dallas to Los Angeles",
        required_data=test_data
    )
    
    try:
        print("🔍 Executing flight search agent...")
        result = await agent.execute_agent_task(task)
        
        print(f"✅ Agent execution completed")
        print(f"   Confidence: {result.confidence}")
        print(f"   Reasoning: {result.reasoning}")
        print()
        
        if "error" in result.result:
            print(f"❌ Error: {result.result['error']}")
            return False
        
        flight_results = result.result.get("flight_search_results", {})
        
        if "error" in flight_results:
            print(f"❌ Flight search error: {flight_results['error']}")
            return False
        
        print(f"📊 Flight Search Results:")
        print(f"   Total flights found: {flight_results.get('total_flights_found', 0)}")
        print(f"   Origin: {flight_results.get('origin', 'N/A')}")
        print(f"   Destination: {flight_results.get('destination', 'N/A')}")
        print(f"   Departure Date: {flight_results.get('departure_date', 'N/A')}")
        print(f"   Return Date: {flight_results.get('return_date', 'N/A')}")
        print()
        
        # Display flight details
        flights = flight_results.get('flights', [])
        if flights:
            print("✈️  Flight Details:")
            for i, flight in enumerate(flights[:3], 1):  # Show first 3 flights
                print(f"   Flight {i}:")
                print(f"     Airline: {flight.get('airline', 'N/A')}")
                print(f"     Departure: {flight.get('departure_time', 'N/A')}")
                print(f"     Arrival: {flight.get('arrival_time', 'N/A')}")
                print(f"     Duration: {flight.get('duration', 'N/A')}")
                print(f"     Stops: {flight.get('stops', 'N/A')}")
                print(f"     Price: ${flight.get('price', 'N/A')} {flight.get('currency', 'USD')}")
                print(f"     Trip Type: {flight.get('trip_type', 'N/A')}")
                print()
        else:
            print("⚠️  No flights found")
        
        # Display search metadata
        metadata = flight_results.get('search_metadata', {})
        if metadata:
            print("🔧 Search Metadata:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
            print()
        
        # Display booking links
        booking_links = flight_results.get('booking_links', {})
        if booking_links:
            print("🔗 Booking Links:")
            for key, value in booking_links.items():
                print(f"   {key}: {value}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_comprehensive_planning():
    """Test comprehensive planning with flight search"""
    
    print("🧪 Testing Comprehensive Planning with Flight Search")
    print("=" * 60)
    
    # Initialize the agent
    agent = AITripPlanningAgent()
    
    # Test data for comprehensive planning
    test_data = {
        "origin": "Dallas",
        "destination": "Los Angeles",
        "start_date": "2025-08-21", 
        "duration_days": 5,
        "travelers": 1,
        "budget_range": "moderate",
        "interests": ["food", "culture"],
        "comprehensive_planning": True
    }
    
    print(f"📋 Comprehensive Planning Test Parameters:")
    for key, value in test_data.items():
        print(f"   {key}: {value}")
    print()
    
    # Create coordinator task for comprehensive planning
    task = AgentTask(
        agent_type=AgentType.COORDINATOR,
        task_description="Create comprehensive trip plan including flights",
        required_data=test_data
    )
    
    try:
        print("🔍 Executing comprehensive planning...")
        result = await agent.execute_agent_task(task)
        
        print(f"✅ Comprehensive planning completed")
        print(f"   Confidence: {result.confidence}")
        print(f"   Reasoning: {result.reasoning}")
        print()
        
        if "error" in result.result:
            print(f"❌ Error: {result.result['error']}")
            return False
        
        # Display overview
        overview = result.result.get("overview", {})
        if overview:
            print("📋 Trip Overview:")
            print(f"   Recommended Cities: {overview.get('recommended_cities', [])}")
            print(f"   Route Sequence: {overview.get('route_sequence', [])}")
            print(f"   Planning Priorities: {overview.get('planning_priorities', [])}")
            print()
        
        # Display destination recommendations
        dest_recs = result.result.get("destination_recommendations", {})
        if dest_recs:
            print("🏛️  Destination Recommendations:")
            must_see = dest_recs.get("must_see_attractions", [])
            print(f"   Must-see attractions: {len(must_see)} found")
            for i, attraction in enumerate(must_see[:3], 1):
                print(f"     {i}. {attraction.get('name', 'N/A')} - {attraction.get('location', 'N/A')}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive planning test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Flight Agent Tests")
    print("=" * 60)
    
    # Test 1: Flight search agent
    print("\n" + "="*60)
    success1 = await test_flight_agent()
    
    # Test 2: Comprehensive planning
    print("\n" + "="*60)
    success2 = await test_comprehensive_planning()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary:")
    print(f"   Flight Search Agent: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"   Comprehensive Planning: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Flight agent is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main()) 