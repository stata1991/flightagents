#!/usr/bin/env python3

import requests
import json

def test_smart_budget():
    """Test the new smart budget categorization system"""
    
    # Test cases with different destinations and budgets
    test_cases = [
        {
            "name": "US Disney World with $1000 budget",
            "query": "I want to go to Disney World from New York on August 10th for 5 days with 3 adults and 1 child, budget $1000"
        },
        {
            "name": "India trip with $1000 budget",
            "query": "I want to go to Mumbai India from New York on August 10th for 5 days with 2 adults, budget $1000"
        },
        {
            "name": "Japan trip with $1000 budget",
            "query": "I want to go to Tokyo Japan from New York on August 10th for 5 days with 2 adults, budget $1000"
        },
        {
            "name": "Switzerland trip with $1000 budget",
            "query": "I want to go to Zurich Switzerland from New York on August 10th for 5 days with 2 adults, budget $1000"
        },
        {
            "name": "Thailand trip with $1000 budget",
            "query": "I want to go to Bangkok Thailand from New York on August 10th for 5 days with 2 adults, budget $1000"
        }
    ]
    
    base_url = "http://localhost:8000"
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print(f"{'='*60}")
        
        try:
            response = requests.post(
                f"{base_url}/trip-planner/plan-trip-natural",
                json={"query": test_case['query']},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    extraction = result.get("extraction", {})
                    trip_plan = result.get("trip_plan", {})
                    summary = trip_plan.get("summary", {})
                    
                    print(f"✅ Success!")
                    print(f"Budget Amount: ${extraction.get('budget_amount', 'N/A')}")
                    print(f"Budget Preference: {extraction.get('budget_preference', 'N/A')}")
                    
                    budget_analysis = extraction.get('budget_analysis', {})
                    if budget_analysis:
                        print(f"Destination Country: {budget_analysis.get('destination_country', 'N/A')}")
                        print(f"Categorized As: {budget_analysis.get('categorized_as', 'N/A')}")
                        print(f"Cost of Living Adjusted: {budget_analysis.get('cost_of_living_adjusted', 'N/A')}")
                    
                    print(f"Flights Found: {len(trip_plan.get('flights', {}))}")
                    print(f"Hotels Found: {len(trip_plan.get('hotels', {}))}")
                    
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    if result.get("missing_fields"):
                        print(f"Missing fields: {result['missing_fields']}")
                    if result.get("follow_up_questions"):
                        print(f"Follow-up questions: {len(result['follow_up_questions'])}")
                        
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        print()

if __name__ == "__main__":
    test_smart_budget() 