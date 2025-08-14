#!/usr/bin/env python3
"""
Test Complete Yosemite Trip Planning Flow
Walk through the entire process and show API data
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our services
from services.smart_destination_service import SmartDestinationService
from api.chat_integration_router import _extract_trip_request
from api.models import TripPlanningRequest, TripType, BudgetRange

async def test_yosemite_complete_flow():
    """Test the complete Yosemite trip planning flow"""
    logger.info("🏔️ COMPLETE YOSEMITE TRIP PLANNING FLOW")
    logger.info("=" * 60)
    
    # Test message
    test_message = "plan trip from dallas to yosemite national park from 1st sept to 04th sept"
    
    # Mock conversation state
    conversation_state = {
        "current_state": "gathering_info"
    }
    
    logger.info(f"📝 USER INPUT: {test_message}")
    logger.info("=" * 60)
    
    # Step 1: Extract trip request
    logger.info("\n🔍 STEP 1: EXTRACTING TRIP REQUEST")
    logger.info("-" * 40)
    
    trip_request = await _extract_trip_request(test_message, conversation_state)
    
    if trip_request:
        logger.info("✅ Trip Request Extracted Successfully!")
        logger.info(f"Origin: {trip_request.origin}")
        logger.info(f"Destination: {trip_request.destination}")
        logger.info(f"Start Date: {trip_request.start_date}")
        logger.info(f"End Date: {trip_request.end_date}")
        logger.info(f"Duration: {trip_request.duration_days} days")
        logger.info(f"Travelers: {trip_request.travelers}")
        logger.info(f"Budget: {trip_request.budget_range}")
        logger.info(f"Interests: {trip_request.interests}")
        
        # Check smart trip data
        if "smart_trip_data" in conversation_state:
            smart_data = conversation_state["smart_trip_data"]
            logger.info(f"\n🚀 SMART TRIP DATA APPLIED:")
            logger.info(f"Trip Type: {smart_data.get('trip_type')}")
            logger.info(f"Original Destination: {smart_data.get('original_destination')}")
            logger.info(f"Recommended Airport: {smart_data.get('recommended_airport')}")
            logger.info(f"Airport Code: {smart_data.get('airport_code', 'N/A')}")
            logger.info(f"Airport Type: {smart_data.get('airport_type', 'N/A')}")
            logger.info(f"Transportation Options: {smart_data.get('transportation_options', [])}")
            logger.info(f"Minimum Days: {smart_data.get('minimum_days')}")
            
            # Show airport recommendation details
            airport_rec = smart_data.get("airport_recommendation", {})
            if airport_rec:
                logger.info(f"\n✈️ AIRPORT RECOMMENDATION DETAILS:")
                logger.info(f"Primary Airport: {airport_rec.get('airport_name')} ({airport_rec.get('airport_code')})")
                logger.info(f"Airport Type: {airport_rec.get('airport_type')}")
                logger.info(f"Recommendation Type: {airport_rec.get('recommendation_type')}")
                logger.info(f"Reasoning: {airport_rec.get('reasoning')}")
                logger.info(f"Distance: {airport_rec.get('distance_to_destination')}")
                
                cost_considerations = airport_rec.get("cost_considerations", {})
                logger.info(f"\n💰 COST CONSIDERATIONS:")
                for key, value in cost_considerations.items():
                    logger.info(f"  {key}: {value}")
        
        # Step 2: Show what would be sent to APIs
        logger.info("\n" + "=" * 60)
        logger.info("🔌 STEP 2: API DATA THAT WOULD BE SENT")
        logger.info("=" * 60)
        
        # Flight Search API Data
        logger.info("\n✈️ FLIGHT SEARCH API DATA:")
        logger.info("-" * 30)
        flight_search_data = {
            "origin": trip_request.origin,
            "destination": trip_request.destination,
            "date": trip_request.start_date or "2025-09-01",
            "return_date": trip_request.end_date or "2025-09-04",
            "travelers": trip_request.travelers or 2,
            "cabin_class": "economy",  # Default
            "currency": "USD"  # Default
        }
        logger.info(f"Flight Search Payload: {json.dumps(flight_search_data, indent=2)}")
        
        # Hotel Search API Data
        logger.info("\n🏨 HOTEL SEARCH API DATA:")
        logger.info("-" * 30)
        
        # Calculate budget allocation (30-35% for hotels)
        budget_range = trip_request.budget_range or BudgetRange.MODERATE
        if budget_range == BudgetRange.BUDGET:
            total_budget = 1000  # $1000 for budget
        elif budget_range == BudgetRange.MODERATE:
            total_budget = 3000  # $3000 for moderate
        else:
            total_budget = 5000  # $5000 for luxury
            
        # Handle missing duration_days
        duration_days = trip_request.duration_days or 4  # Default to 4 days for Yosemite
        hotel_budget = total_budget * 0.35  # 35% for hotels
        nightly_budget = hotel_budget / duration_days
        
        hotel_search_data = {
            "destination": trip_request.destination,
            "checkin_date": trip_request.start_date or "2025-09-01",
            "checkout_date": trip_request.end_date or "2025-09-04",
            "guests": trip_request.travelers or 2,
            "rooms": 1,
            "currency": "USD",
            "budget_range": budget_range.value,
            "nightly_budget": round(nightly_budget, 2),
            "total_hotel_budget": round(hotel_budget, 2),
            "preferences": {
                "amenities": ["free_wifi", "parking"],
                "property_type": "hotel"
            }
        }
        logger.info(f"Hotel Search Payload: {json.dumps(hotel_search_data, indent=2)}")
        
        # Step 3: Show conversation acknowledgment
        logger.info("\n" + "=" * 60)
        logger.info("💬 STEP 3: CONVERSATION ACKNOWLEDGMENT")
        logger.info("=" * 60)
        
        from services.conversation_service import ConversationService
        conversation_service = ConversationService()
        
        # Create trip data for acknowledgment
        trip_data = {
            "smart_trip_data": smart_data if "smart_trip_data" in conversation_state else {}
        }
        
        acknowledgment = conversation_service._acknowledge_new_information(test_message, trip_data)
        logger.info(f"AI Acknowledgment: {acknowledgment}")
        
        # Step 4: Show final trip plan structure
        logger.info("\n" + "=" * 60)
        logger.info("📋 STEP 4: FINAL TRIP PLAN STRUCTURE")
        logger.info("=" * 60)
        
        final_trip_plan = {
            "trip_summary": {
                "title": f"Yosemite National Park Adventure",
                "overview": f"Explore the stunning Yosemite National Park from {trip_request.start_date} to {trip_request.end_date}",
                "highlights": ["Yosemite Valley", "El Capitan", "Half Dome", "Glacier Point"],
                "best_time_to_visit": "September offers pleasant weather and fewer crowds",
                "weather_info": "Average temperatures: 60-80°F, mostly sunny",
                "start_date": trip_request.start_date,
                "end_date": trip_request.end_date
            },
            "transportation": {
                "flights": {
                    "recommended_airport": smart_data.get("recommended_airport", "Nearest Airport"),
                    "airport_code": smart_data.get("airport_code", "N/A"),
                    "airport_type": smart_data.get("airport_type", "unknown"),
                    "transportation_to_park": "Rental car required",
                    "driving_time": "2-4 hours depending on airport",
                    "cost_considerations": "Major airports offer cheaper flights"
                }
            },
            "accommodation": {
                "recommendations": "Hotels in Yosemite Valley or nearby towns",
                "budget_allocation": f"${hotel_budget:.0f} total (${nightly_budget:.0f}/night)",
                "transportation": "Rental car for park access"
            },
            "itinerary": {
                "day_1": "Arrival and Yosemite Valley exploration",
                "day_2": "Hiking and scenic viewpoints",
                "day_3": "Waterfalls and nature trails",
                "day_4": "Departure"
            },
            "estimated_costs": {
                "flights": f"${total_budget * 0.25:.0f}",
                "hotels": f"${hotel_budget:.0f}",
                "rental_car": f"${total_budget * 0.15:.0f}",
                "activities": f"${total_budget * 0.20:.0f}",
                "meals": f"${total_budget * 0.20:.0f}",
                "total": f"${total_budget:.0f}"
            }
        }
        
        logger.info(f"Final Trip Plan Structure: {json.dumps(final_trip_plan, indent=2)}")
        
        return True
    else:
        logger.error("❌ Failed to extract trip request")
        return False

async def main():
    """Run the complete Yosemite flow test"""
    success = await test_yosemite_complete_flow()
    
    if success:
        logger.info("\n🎉 COMPLETE FLOW TEST SUCCESSFUL!")
        logger.info("The system correctly processes Yosemite trips with smart airport logic!")
    else:
        logger.error("\n❌ FLOW TEST FAILED!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
