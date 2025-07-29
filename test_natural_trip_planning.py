#!/usr/bin/env python3
"""
Test script for Natural Language Trip Planning System
Tests various complex queries including destination intelligence
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.trip_planner_router import NaturalLanguageTripPlanner

async def test_natural_language_trip_planning():
    """Test the natural language trip planning system"""
    
    print("🚀 Testing Natural Language Trip Planning System")
    print("=" * 60)
    
    # Initialize the trip planner
    planner = NaturalLanguageTripPlanner()
    
    # Test queries
    test_queries = [
        {
            "query": "Plan a 3-day trip from Dallas to Yosemite National Park this weekend, ±1 day",
            "description": "National Park with destination intelligence"
        },
        {
            "query": "I want to visit Disney World from New York for 5 days in August",
            "description": "Theme park destination"
        },
        {
            "query": "Book a luxury vacation to Las Vegas for 4 days next month",
            "description": "Luxury entertainment destination"
        },
        {
            "query": "Plan a budget trip to Times Square for 2 people, 3 days in September",
            "description": "Budget landmark destination"
        },
        {
            "query": "I need a one-way flight from Chicago to Golden Gate Bridge for hiking and outdoor activities",
            "description": "One-way trip with interests"
        },
        {
            "query": "Plan a family vacation to Niagara Falls for 6 people, 4 days in July",
            "description": "Family trip to natural wonder"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print("-" * 50)
        
        try:
            # Plan the trip
            result = await planner.plan_trip_from_natural_language(test_case['query'])
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                if "suggestions" in result:
                    print("💡 Suggestions:")
                    for suggestion in result['suggestions']:
                        print(f"   - {suggestion}")
            else:
                print("✅ Trip planned successfully!")
                
                # Display extraction results
                extraction = result['extraction']
                print(f"\n📊 Extraction Results:")
                print(f"   Origin: {extraction.get('origin', 'N/A')}")
                print(f"   Destination: {extraction.get('destination', 'N/A')}")
                print(f"   Duration: {extraction.get('duration', 'N/A')} days")
                print(f"   Start Date: {extraction.get('start_date', 'N/A')}")
                print(f"   End Date: {extraction.get('end_date', 'N/A')}")
                print(f"   Travelers: {extraction.get('travelers', 'N/A')}")
                print(f"   Budget: {extraction.get('budget_preference', 'N/A')}")
                print(f"   Trip Type: {extraction.get('trip_type', 'N/A')}")
                print(f"   Interests: {', '.join(extraction.get('interests', []))}")
                print(f"   Flexible Days: {extraction.get('flexible_days', 0)}")
                
                # Display destination intelligence
                if extraction.get('destination_intelligence'):
                    intel = extraction['destination_intelligence']
                    print(f"\n🎯 Destination Intelligence:")
                    print(f"   Type: {intel['type']}")
                    print(f"   Description: {intel['resolved_destination']['description']}")
                    print(f"   Nearest Airports: {', '.join(intel['nearest_airports'])}")
                    print(f"   Suggested Airport: {intel['suggested_airport']}")
                
                # Display validation results
                validation = result['validation']
                print(f"\n✅ Validation Results:")
                print(f"   Valid: {validation['is_valid']}")
                if validation['errors']:
                    print(f"   Errors: {validation['errors']}")
                if validation['warnings']:
                    print(f"   Warnings: {validation['warnings']}")
                if validation['missing_fields']:
                    print(f"   Missing Fields: {validation['missing_fields']}")
                
                # Display trip plan summary
                if result.get('trip_plan'):
                    trip_plan = result['trip_plan']
                    summary = trip_plan['summary']
                    print(f"\n🎉 Trip Plan Summary:")
                    print(f"   Total Cost: ${trip_plan.get('summary', {}).get('total_estimated_cost', {}).get('total', 'N/A')}")
                    print(f"   Flight Cost: ${trip_plan.get('summary', {}).get('total_estimated_cost', {}).get('flights', 'N/A')}")
                    print(f"   Hotel Cost: ${trip_plan.get('summary', {}).get('total_estimated_cost', {}).get('hotels', 'N/A')}")
                    
                    # Display itinerary
                    if trip_plan.get('itinerary'):
                        print(f"\n📅 Itinerary Preview:")
                        for day in trip_plan['itinerary'][:2]:  # Show first 2 days
                            print(f"   Day {day['day']} ({day['date']}): {', '.join(day['activities'][:2])}")
                        if len(trip_plan['itinerary']) > 2:
                            print(f"   ... and {len(trip_plan['itinerary']) - 2} more days")
                
                # Display suggestions
                if result.get('suggestions'):
                    print(f"\n💡 Suggestions:")
                    for suggestion in result['suggestions']:
                        print(f"   - {suggestion}")
            
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print("\n" + "=" * 60)

async def test_destination_intelligence():
    """Test destination intelligence features"""
    
    print("\n🧠 Testing Destination Intelligence")
    print("=" * 60)
    
    planner = NaturalLanguageTripPlanner()
    
    # Test various destinations
    test_destinations = [
        "Yosemite National Park",
        "Disney World",
        "Las Vegas Strip",
        "Times Square",
        "Golden Gate Bridge",
        "Statue of Liberty",
        "Grand Canyon",
        "Yellowstone",
        "Niagara Falls",
        "Disneyland"
    ]
    
    for destination in test_destinations:
        print(f"\n🎯 Testing: {destination}")
        
        intel = planner._resolve_destination_intelligence(destination)
        
        if intel:
            print(f"   ✅ Found intelligence")
            print(f"   Type: {intel['type']}")
            print(f"   City: {intel['resolved_destination']['city']}")
            print(f"   State: {intel['resolved_destination']['state']}")
            print(f"   Airports: {', '.join(intel['nearest_airports'])}")
            print(f"   Description: {intel['resolved_destination']['description']}")
        else:
            print(f"   ❌ No intelligence found")

async def test_validation():
    """Test validation features"""
    
    print("\n🔍 Testing Validation System")
    print("=" * 60)
    
    planner = NaturalLanguageTripPlanner()
    
    # Test various validation scenarios
    test_cases = [
        {
            "extraction": {
                "origin": "DAL",
                "destination": "SFO",
                "duration": 3,
                "start_date": "2024-12-25",
                "travelers": 2
            },
            "description": "Valid trip"
        },
        {
            "extraction": {
                "origin": None,
                "destination": "SFO",
                "duration": 3,
                "start_date": "2024-12-25",
                "travelers": 2
            },
            "description": "Missing origin"
        },
        {
            "extraction": {
                "origin": "DAL",
                "destination": "SFO",
                "duration": 0,
                "start_date": "2024-12-25",
                "travelers": 2
            },
            "description": "Invalid duration"
        },
        {
            "extraction": {
                "origin": "DAL",
                "destination": "SFO",
                "duration": 3,
                "start_date": "2020-12-25",
                "travelers": 2
            },
            "description": "Past date"
        },
        {
            "extraction": {
                "origin": "DAL",
                "destination": "SFO",
                "duration": 3,
                "start_date": "2024-12-25",
                "travelers": 10
            },
            "description": "Large group"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['description']}")
        
        validation = planner._validate_trip_request(test_case['extraction'])
        
        print(f"   Valid: {validation['is_valid']}")
        if validation['errors']:
            print(f"   Errors: {validation['errors']}")
        if validation['warnings']:
            print(f"   Warnings: {validation['warnings']}")
        if validation['missing_fields']:
            print(f"   Missing: {validation['missing_fields']}")

async def main():
    """Run all tests"""
    
    print("🧪 Natural Language Trip Planning System Tests")
    print("=" * 80)
    
    # Test destination intelligence
    await test_destination_intelligence()
    
    # Test validation
    await test_validation()
    
    # Test natural language trip planning
    await test_natural_language_trip_planning()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 