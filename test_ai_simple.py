#!/usr/bin/env python3
"""
Simple test script for AI Trip Planner (without flight search)
"""

from dotenv import load_dotenv
load_dotenv()

import os
import asyncio
from api.ai_trip_planner import AITripPlanner
from api.models import TripPlanningRequest, TripType, BudgetRange

async def test_ai_trip_planner_simple():
    """Test the AI Trip Planner without flight search"""
    
    print("🚀 Testing AI Trip Planner (Simple Version)")
    print("=" * 50)
    
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
        print("🤖 Generating itinerary with AI agents (excluding flight search)...")
        print("   This should complete quickly...")
        print()
        
        # Temporarily modify the ai_agent to exclude flight search
        from api.ai_agents import ai_agent, AgentType, AgentTask
        import logging
        logger = logging.getLogger(__name__)
        
        # Store original agents
        original_agents = ai_agent.agents.copy()
        
        # Remove flight search agent temporarily
        if AgentType.FLIGHT_SEARCH_AGENT in ai_agent.agents:
            del ai_agent.agents[AgentType.FLIGHT_SEARCH_AGENT]
        
        try:
            # Create a custom version of plan_trip_with_agents without flight search
            async def plan_trip_without_flights(request):
                try:
                    coordinator_task = AgentTask(
                        agent_type=AgentType.COORDINATOR,
                        task_description="Create initial trip structure and coordination plan",
                        required_data=request.dict()
                    )
                    coordinator_result = await ai_agent.execute_agent_task(coordinator_task)
                    if "error" in coordinator_result.result:
                        return {"error": coordinator_result.result["error"]}
                    
                    destination_task = AgentTask(
                        agent_type=AgentType.DESTINATION_SPECIALIST,
                        task_description="Provide destination-specific recommendations",
                        required_data={
                            "destination": request.destination,
                            "duration_days": request.duration_days,
                            "interests": request.interests,
                            "coordinator_recommendations": coordinator_result.result
                        }
                    )
                    destination_result = await ai_agent.execute_agent_task(destination_task)
                    
                    budget_task = AgentTask(
                        agent_type=AgentType.BUDGET_ANALYST,
                        task_description="Analyze budget requirements and provide cost breakdown",
                        required_data={
                            **request.dict(),
                            "coordinator_recommendations": coordinator_result.result,
                            "destination_recommendations": destination_result.result
                        }
                    )
                    budget_result = await ai_agent.execute_agent_task(budget_task)
                    
                    logistics_task = AgentTask(
                        agent_type=AgentType.LOGISTICS_PLANNER,
                        task_description="Plan transportation and logistics between destinations",
                        required_data={
                            "cities": coordinator_result.result.get("recommended_cities", []),
                            "duration_days": request.duration_days,
                            "coordinator_recommendations": coordinator_result.result
                        }
                    )
                    logistics_result = await ai_agent.execute_agent_task(logistics_task)
                    
                    cultural_task = AgentTask(
                        agent_type=AgentType.CULTURAL_ADVISOR,
                        task_description="Provide cultural insights and local customs",
                        required_data={
                            "destination": request.destination,
                            "trip_type": request.trip_type.value,
                            "coordinator_recommendations": coordinator_result.result
                        }
                    )
                    cultural_result = await ai_agent.execute_agent_task(cultural_task)
                    
                    booking_task = AgentTask(
                        agent_type=AgentType.BOOKING_AGENT,
                        task_description="Provide booking strategies and recommendations",
                        required_data={
                            **request.dict(),
                            "coordinator_recommendations": coordinator_result.result,
                            "budget_analysis": budget_result.result,
                            "logistics_plan": logistics_result.result
                        }
                    )
                    booking_result = await ai_agent.execute_agent_task(booking_task)
                    
                    # Combine results without flight search
                    final_itinerary = ai_agent._combine_agent_results([
                        coordinator_result,
                        destination_result,
                        budget_result,
                        logistics_result,
                        cultural_result,
                        booking_result
                    ])
                    return final_itinerary
                except Exception as e:
                    logger.error(f"Error in multi-agent planning: {e}")
                    return {"error": str(e)}
            
            # Generate itinerary without flight search
            itinerary = await plan_trip_without_flights(test_request)
            
            if "error" in itinerary:
                print(f"❌ Error generating itinerary: {itinerary['error']}")
                return
            
            print("✅ Itinerary generated successfully!")
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
            
            print("🎉 AI Trip Planner Simple Test Complete!")
            print("✅ Core AI functionality is working!")
            
        finally:
            # Restore original agents
            ai_agent.agents = original_agents
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_trip_planner_simple()) 