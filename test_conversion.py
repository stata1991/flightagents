#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import TripPlanningRequest, TripType, BudgetRange
from api.trip_planner_interface import TripPlanRequest

# Test creating a TripPlanningRequest with enums
try:
    trip_request = TripPlanningRequest(
        origin="Dallas",
        destination="Las Vegas",
        duration_days=5,
        start_date="2025-08-05",
        end_date=None,
        travelers=4,
        trip_type=TripType.LEISURE,
        budget_range=BudgetRange.MODERATE,
        interests=[],
        special_requirements=""
    )
    print("✅ TripPlanningRequest created successfully!")
    print(f"trip_type: {trip_request.trip_type} (type: {type(trip_request.trip_type)})")
    print(f"budget_range: {trip_request.budget_range} (type: {type(trip_request.budget_range)})")
    
    # Test conversion to TripPlanRequest
    enhanced_request = TripPlanRequest(
        origin=trip_request.origin,
        destination=trip_request.destination,
        duration_days=trip_request.duration_days,
        start_date=trip_request.start_date,
        end_date=trip_request.end_date,
        travelers=trip_request.travelers,
        budget_range=str(trip_request.budget_range.value),
        trip_type=str(trip_request.trip_type.value),
        interests=trip_request.interests or [],
        special_requirements=trip_request.special_requirements or ""
    )
    print("✅ TripPlanRequest created successfully!")
    print(f"enhanced_request: {enhanced_request}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}") 