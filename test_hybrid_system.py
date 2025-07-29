#!/usr/bin/env python3
"""
Test script for the hybrid trip planning system
"""

import asyncio
import json
import sys
import os

# Add the api directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.hybrid_trip_router import hybrid_planner
from api.trip_planner_interface import TripPlanRequest, ProviderType

async def test_hybrid_system():
    """Test the hybrid trip planning system"""
    
    print("🧪 Testing Hybrid Trip Planning System")
    print("=" * 50)
    
    # Test 1: Check available providers
    print("\n1. Checking available providers...")
    providers = hybrid_planner.get_available_providers()
    for provider in providers:
        print(f"   - {provider['type']}: {provider['quality']} (available: {provider['available']})")
    
    # Test 2: Test AI provider
    print("\n2. Testing AI provider...")
    ai_request = TripPlanRequest(
        origin="New York",
        destination="Paris",
        duration_days=3,
        travelers=2,
        budget_range="moderate",
        interests=["food", "culture"],
        trip_type="leisure",
        preferred_provider=ProviderType.AI
    )
    
    try:
        ai_response = await hybrid_planner.plan_trip(ai_request)
        print(f"   ✅ AI Provider: {ai_response.success}")
        print(f"   📊 Quality: {ai_response.metadata.quality}")
        print(f"   🎯 Confidence: {ai_response.metadata.confidence_score}")
        print(f"   📅 Data Freshness: {ai_response.metadata.data_freshness}")
        if ai_response.success:
            print(f"   📋 Has Itinerary: {bool(ai_response.itinerary)}")
            print(f"   💰 Estimated Cost: ${ai_response.estimated_costs.get('total', 0):.2f}")
    except Exception as e:
        print(f"   ❌ AI Provider failed: {str(e)}")
    
    # Test 3: Test API provider
    print("\n3. Testing API provider...")
    api_request = TripPlanRequest(
        origin="New York",
        destination="London",
        duration_days=2,
        travelers=1,
        budget_range="moderate",
        interests=["sightseeing"],
        trip_type="leisure",
        preferred_provider=ProviderType.API
    )
    
    try:
        api_response = await hybrid_planner.plan_trip(api_request)
        print(f"   ✅ API Provider: {api_response.success}")
        print(f"   📊 Quality: {api_response.metadata.quality}")
        print(f"   🎯 Confidence: {api_response.metadata.confidence_score}")
        print(f"   📅 Data Freshness: {api_response.metadata.data_freshness}")
        if api_response.success:
            print(f"   📋 Has Itinerary: {bool(api_response.itinerary)}")
            print(f"   💰 Estimated Cost: ${api_response.estimated_costs.get('total', 0):.2f}")
    except Exception as e:
        print(f"   ❌ API Provider failed: {str(e)}")
    
    # Test 4: Test auto-selection (default provider)
    print("\n4. Testing auto-selection (default provider)...")
    auto_request = TripPlanRequest(
        origin="San Francisco",
        destination="Tokyo",
        duration_days=5,
        travelers=2,
        budget_range="luxury",
        interests=["technology", "food"],
        trip_type="leisure"
    )
    
    try:
        auto_response = await hybrid_planner.plan_trip(auto_request)
        print(f"   ✅ Auto Selection: {auto_response.success}")
        print(f"   🤖 Provider Used: {auto_response.metadata.provider}")
        print(f"   📊 Quality: {auto_response.metadata.quality}")
        print(f"   🎯 Confidence: {auto_response.metadata.confidence_score}")
        if auto_response.success:
            print(f"   📋 Has Itinerary: {bool(auto_response.itinerary)}")
            print(f"   💰 Estimated Cost: ${auto_response.estimated_costs.get('total', 0):.2f}")
    except Exception as e:
        print(f"   ❌ Auto Selection failed: {str(e)}")
    
    # Test 5: Test fallback mechanism
    print("\n5. Testing fallback mechanism...")
    # Create a request that might fail with one provider
    fallback_request = TripPlanRequest(
        origin="Invalid",
        destination="Invalid",
        duration_days=1,
        travelers=1,
        budget_range="budget",
        interests=[],
        trip_type="leisure"
    )
    
    try:
        fallback_response = await hybrid_planner.plan_trip(fallback_request)
        print(f"   ✅ Fallback Test: {fallback_response.success}")
        print(f"   🤖 Provider Used: {fallback_response.metadata.provider}")
        print(f"   🔄 Fallback Used: {fallback_response.metadata.fallback_used}")
        if not fallback_response.success:
            print(f"   ❌ Expected failure: {fallback_response.error_message}")
    except Exception as e:
        print(f"   ❌ Fallback test failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Hybrid System Test Complete!")
    
    # Summary
    print("\n📋 Summary:")
    print(f"   - AI Provider Available: {any(p['type'] == 'ai' and p['available'] for p in providers)}")
    print(f"   - API Provider Available: {any(p['type'] == 'api' and p['available'] for p in providers)}")
    print(f"   - Default Provider: {hybrid_planner.default_provider.get_provider_type() if hybrid_planner.default_provider else 'None'}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_system()) 