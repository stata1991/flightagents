#!/usr/bin/env python3
"""
Test script for validation error handling
Tests that the system shows proper error dialogs when required fields are missing
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.trip_planner_router import NaturalLanguageTripPlanner

async def test_validation_errors():
    """Test that the system properly validates required fields"""
    
    print("🔍 Testing Validation Error Handling")
    print("=" * 50)
    
    # Initialize the trip planner
    planner = NaturalLanguageTripPlanner()
    
    # Test queries with missing required fields
    test_queries = [
        {
            "query": "Plan a trip to New York",
            "description": "Missing origin city",
            "expected_errors": ["Origin city is not provided"]
        },
        {
            "query": "I want to go from Dallas",
            "description": "Missing destination",
            "expected_errors": ["Destination is not provided"]
        },
        {
            "query": "From Dallas to New York",
            "description": "Missing dates and duration",
            "expected_errors": ["Trip duration is not provided", "Start date is not provided"]
        },
        {
            "query": "Plan a vacation",
            "description": "Missing all required fields",
            "expected_errors": ["Origin city is not provided", "Destination is not provided", "Trip duration is not provided", "Start date is not provided"]
        },
        {
            "query": "3 days in New York",
            "description": "Missing origin and dates",
            "expected_errors": ["Origin city is not provided", "Start date is not provided"]
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
            else:
                # Check validation
                validation = result.get('validation', {})
                if validation.get('is_valid', True):
                    print("❌ FAILED: Query should have failed validation but didn't")
                else:
                    errors = validation.get('errors', [])
                    print(f"✅ Validation failed as expected")
                    print(f"   Errors found: {len(errors)}")
                    for error in errors:
                        print(f"   - {error}")
                    
                    # Check if expected errors are present
                    expected_errors = test_case['expected_errors']
                    found_errors = [error for error in errors if any(expected in error for expected in expected_errors)]
                    
                    if len(found_errors) == len(expected_errors):
                        print("✅ All expected errors found")
                    else:
                        print("❌ Some expected errors missing")
                        print(f"   Expected: {expected_errors}")
                        print(f"   Found: {found_errors}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Validation error tests completed!")

async def test_complete_queries():
    """Test that complete queries work properly"""
    
    print("\n✅ Testing Complete Queries")
    print("=" * 50)
    
    # Initialize the trip planner
    planner = NaturalLanguageTripPlanner()
    
    # Test queries with all required fields
    complete_queries = [
        {
            "query": "Plan a 3-day trip from Dallas to New York starting March 15th for 2 people",
            "description": "Complete trip request"
        },
        {
            "query": "I want to visit Disney World from New York for 5 days starting August 10th",
            "description": "Theme park vacation"
        },
        {
            "query": "Book a luxury vacation to Las Vegas for 4 days from Chicago starting July 20th",
            "description": "Luxury trip"
        }
    ]
    
    for i, test_case in enumerate(complete_queries, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"Query: {test_case['query']}")
        print("-" * 50)
        
        try:
            # Plan the trip
            result = await planner.plan_trip_from_natural_language(test_case['query'])
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                # Check validation
                validation = result.get('validation', {})
                if validation.get('is_valid', False):
                    print("✅ Query validated successfully")
                    print(f"   Trip planned: {result.get('trip_plan', {}).get('summary', {}).get('destination', 'N/A')}")
                else:
                    print("❌ FAILED: Complete query should have passed validation")
                    errors = validation.get('errors', [])
                    for error in errors:
                        print(f"   - {error}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

async def main():
    """Run all validation tests"""
    print("🚀 Starting Validation Error Tests")
    print("=" * 60)
    
    await test_validation_errors()
    await test_complete_queries()
    
    print("\n" + "=" * 60)
    print("🎉 All validation tests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 