#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.trip_planner_router import NaturalLanguageTripPlanner

def test_direct_extraction():
    """Test the budget extraction directly"""
    
    # Create an instance of the trip planner
    planner = NaturalLanguageTripPlanner()
    
    # Test queries
    test_queries = [
        "from New York to Orlando on August 10th for 5 days with 2 adults budget $1000",
        "I want to go to Disney World from New York on August 10th for 5 days with 3 adults and 1 child, budget $1000",
        "budget $1000"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query: '{query}'")
        print(f"{'='*60}")
        
        try:
            # Call the extraction method directly
            extraction = planner._extract_trip_details(query)
            
            print(f"Extraction result:")
            print(f"  Budget amount: {extraction.get('budget_amount')}")
            print(f"  Budget preference: {extraction.get('budget_preference')}")
            print(f"  Origin: {extraction.get('origin')}")
            print(f"  Destination: {extraction.get('destination')}")
            print(f"  Duration: {extraction.get('duration')}")
            print(f"  Travelers: {extraction.get('travelers')}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_direct_extraction() 