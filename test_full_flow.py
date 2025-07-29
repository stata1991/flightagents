#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.trip_planner_router import NaturalLanguageTripPlanner

async def test_full_flow():
    """Test the full flow to see where budget extraction is lost"""
    
    # Create an instance of the trip planner
    planner = NaturalLanguageTripPlanner()
    
    # Test query
    query = "from New York to Orlando on August 10th for 5 days with 2 adults budget $1000"
    
    print(f"Testing full flow with query: '{query}'")
    print("="*60)
    
    try:
        # Step 1: Test basic extraction
        print("Step 1: Basic extraction")
        extraction = planner._extract_trip_details(query)
        print(f"  Budget amount: {extraction.get('budget_amount')}")
        print(f"  Budget preference: {extraction.get('budget_preference')}")
        print(f"  Origin: {extraction.get('origin')}")
        print(f"  Destination: {extraction.get('destination')}")
        print()
        
        # Step 2: Test enhanced parser
        print("Step 2: Enhanced parser")
        parsed_result = await planner.parser.parse_query(query)
        print(f"  Enhanced parser result: {parsed_result}")
        print(f"  Enhanced budget: {parsed_result.get('budget')}")
        print()
        
        # Step 3: Test full flow
        print("Step 3: Full flow")
        result = await planner.plan_trip_from_natural_language(query)
        print(f"  Result success: {result.get('success')}")
        if result.get('success'):
            trip_plan = result.get('trip_plan', {})
            summary = trip_plan.get('summary', {})
            print(f"  Final budget amount: {summary.get('budget_amount')}")
            print(f"  Final budget preference: {summary.get('budget_preference')}")
            print(f"  Final budget analysis: {summary.get('budget_analysis')}")
        else:
            print(f"  Error: {result.get('error')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_flow()) 