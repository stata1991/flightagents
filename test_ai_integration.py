#!/usr/bin/env python3
"""
Test script for AI Trip Planner integration with Booking.com flight search
"""

import asyncio
import json
from api.ai_trip_planner import AITripPlanner
from api.models import TripPlanningRequest, TripType, BudgetRange
from dotenv import load_dotenv
load_dotenv()

import os
print("ANTHROPIC_API_KEY loaded:", os.getenv("ANTHROPIC_API_KEY")[:10], "..." if os.getenv("ANTHROPIC_API_KEY") else "NOT FOUND")

async def test_ai_trip_planner_with_flights():
    """Test the AI Trip Planner with flight search integration"""
    
    print("🚀 Testing AI Trip Planner with Booking.com Flight Search Integration")
    print("=" * 70)
    
    # Initialize the AI Trip Planner
    ai_planner = AITripPlanner()
    
    # Create a test trip planning request
    test_request = TripPlanningRequest(
        origin="New York",
        destination="Paris",
        duration_days=7,
        start_date="2024-07-15",
        travelers=2,
        trip_type=TripType.LEISURE,
        budget_range=BudgetRange.MODERATE,
        interests=["food", "art", "history"]
    )
    
    print(f"📋 Trip Request:")
    print(f"   Origin: {test_request.origin}")
    print(f"   Destination: {test_request.destination}")
    print(f"   Duration: {test_request.duration_days} days")
    print(f"   Start Date: {test_request.start_date}")
    print(f"   Travelers: {test_request.travelers}")
    print(f"   Trip Type: {test_request.trip_type.value}")
    print(f"   Budget: {test_request.budget_range.value}")
    print(f"   Interests: {test_request.interests}")
    print()
    
    try:
        print("🤖 Generating itinerary with AI agents (including flight search)...")
        print("   This may take a few moments as it searches for real flights...")
        print()
        
        # Generate itinerary with all agents including flight search
        itinerary = await ai_planner.generate_itinerary(test_request)
        
        if "error" in itinerary:
            print(f"❌ Error generating itinerary: {itinerary['error']}")
            return
        
        print("✅ Itinerary generated successfully!")
        print()
        
        # Display flight search results
        flight_results = itinerary.get("flight_search_results", {})
        if flight_results:
            print("✈️  Flight Search Results:")
            print(f"   Origin: {flight_results.get('origin', 'N/A')}")
            print(f"   Destination: {flight_results.get('destination', 'N/A')}")
            print(f"   Departure Date: {flight_results.get('departure_date', 'N/A')}")
            print(f"   Return Date: {flight_results.get('return_date', 'N/A')}")
            print(f"   Total Flights Found: {flight_results.get('total_flights_found', 0)}")
            print()
            
            flights = flight_results.get('flights', [])
            if flights:
                print("   Available Flights:")
                for i, flight in enumerate(flights[:3], 1):  # Show top 3
                    print(f"   {i}. {flight.get('airline', 'Unknown')}")
                    print(f"      Departure: {flight.get('departure_time', 'N/A')}")
                    print(f"      Arrival: {flight.get('arrival_time', 'N/A')}")
                    print(f"      Duration: {flight.get('duration', 'N/A')}")
                    print(f"      Stops: {flight.get('stops', 'N/A')}")
                    print(f"      Price: {flight.get('price', 'N/A')} {flight.get('currency', 'USD')}")
                    print()
            
            booking_links = flight_results.get('booking_links', {})
            if booking_links:
                print("🔗 Booking Links:")
                for link_type, url in booking_links.items():
                    print(f"   {link_type}: {url}")
                print()
        else:
            print("⚠️  No flight search results found in itinerary")
            print()
        
        # Display agent insights
        agent_insights = itinerary.get("agent_insights", {})
        if agent_insights:
            print("🤖 Agent Insights:")
            for agent_type, insight in agent_insights.items():
                confidence = insight.get('confidence', 0)
                reasoning = insight.get('reasoning', 'No reasoning provided')
                print(f"   {agent_type.replace('_', ' ').title()}: {confidence:.1%} confidence")
                print(f"      Reasoning: {reasoning[:100]}...")
                print()
        
        # Display overview
        overview = itinerary.get("overview", {})
        if overview:
            print("📊 Trip Overview:")
            recommended_cities = overview.get("recommended_cities", [])
            if recommended_cities:
                print("   Recommended Cities:")
                for city in recommended_cities:
                    print(f"      {city.get('city', 'N/A')} ({city.get('nights', 'N/A')} nights)")
                print()
            
            route_sequence = overview.get("route_sequence", [])
            if route_sequence:
                print(f"   Route Sequence: {' → '.join(route_sequence)}")
                print()
        
        # Display budget breakdown
        budget_breakdown = itinerary.get("budget_breakdown", {})
        if budget_breakdown:
            print("💰 Budget Breakdown:")
            for category, details in budget_breakdown.items():
                if isinstance(details, dict):
                    estimated_cost = details.get("estimated_cost", "N/A")
                    print(f"   {category.title()}: {estimated_cost}")
            print()
        
        print("🎉 AI Trip Planner with Flight Search Integration Test Complete!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_trip_planner_with_flights()) 