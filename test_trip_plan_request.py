#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.trip_planner_interface import TripPlanRequest

# Test creating a TripPlanRequest
try:
    request = TripPlanRequest(
        origin="Dallas",
        destination="Las Vegas",
        duration_days=5,
        start_date="2025-08-05",
        end_date=None,
        travelers=4,
        budget_range="moderate",
        trip_type="leisure",
        interests=[],
        special_requirements=""
    )
    print("✅ TripPlanRequest created successfully!")
    print(f"Request: {request}")
except Exception as e:
    print(f"❌ Error creating TripPlanRequest: {e}")
    print(f"Error type: {type(e)}") 