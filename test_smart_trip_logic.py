#!/usr/bin/env python3
"""
Test Smart Trip Logic
Comprehensive testing for national park and multi-city trip planning
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

class SmartTripLogicTester:
    """Test class for Smart Trip Logic functionality"""
    
    def __init__(self):
        self.smart_service = SmartDestinationService()
        
    async def test_national_park_scenario(self):
        """Test national park trip planning (Yosemite example)"""
        logger.info("🏔️ Testing National Park Scenario: Yosemite")
        
        # Test message
        test_message = "Plan a trip to Yosemite National Park for 2 travelers starting from September 10th 2025 for 5 days with $3000 budget"
        
        # Mock conversation state
        conversation_state = {
            "origin": "Dallas",
            "current_state": "gathering_info"
        }
        
        logger.info(f"Test Message: {test_message}")
        logger.info(f"Conversation State: {conversation_state}")
        
        # Test trip type analysis
        trip_analysis = await self.smart_service.analyze_trip_type(test_message)
        logger.info(f"Trip Analysis: {json.dumps(trip_analysis, indent=2)}")
        
        # Test airport recommendation
        if trip_analysis["trip_type"] == "national_park":
            airport_rec = await self.smart_service.get_smart_airport_recommendation(
                trip_analysis["destination"], 
                trip_analysis["trip_type"]
            )
            logger.info(f"Airport Recommendation: {json.dumps(airport_rec, indent=2)}")
        
        # Test trip request extraction
        trip_request = await _extract_trip_request(test_message, conversation_state)
        if trip_request:
            logger.info(f"Extracted Trip Request: {trip_request.dict()}")
            
            # Check if smart trip data was added
            if "smart_trip_data" in conversation_state:
                logger.info(f"Smart Trip Data: {json.dumps(conversation_state['smart_trip_data'], indent=2)}")
                logger.info("✅ National Park Smart Logic Applied Successfully!")
            else:
                logger.error("❌ Smart Trip Data Not Found in Conversation State")
        else:
            logger.error("❌ Failed to Extract Trip Request")
        
        return trip_request is not None and "smart_trip_data" in conversation_state
    
    async def test_multi_city_scenario(self):
        """Test multi-city trip planning (Italy example)"""
        logger.info("🌍 Testing Multi-City Scenario: Italy")
        
        # Test message
        test_message = "Plan a trip to Italy visiting Rome Florence Venice for 2 travelers starting from October 15th 2025 for 12 days with $5000 budget"
        
        # Mock conversation state
        conversation_state = {
            "origin": "New York",
            "current_state": "gathering_info"
        }
        
        logger.info(f"Test Message: {test_message}")
        logger.info(f"Conversation State: {conversation_state}")
        
        # Test trip type analysis
        trip_analysis = await self.smart_service.analyze_trip_type(test_message)
        logger.info(f"Trip Analysis: {json.dumps(trip_analysis, indent=2)}")
        
        # Test route suggestion
        if trip_analysis["trip_type"] == "multi_city":
            route_suggestion = self.smart_service.get_multi_city_route_suggestion(trip_analysis["destination"])
            logger.info(f"Route Suggestion: {json.dumps(route_suggestion, indent=2)}")
        
        # Test trip request extraction
        trip_request = await _extract_trip_request(test_message, conversation_state)
        if trip_request:
            logger.info(f"Extracted Trip Request: {trip_request.dict()}")
            
            # Check if smart trip data was added
            if "smart_trip_data" in conversation_state:
                logger.info(f"Smart Trip Data: {json.dumps(conversation_state['smart_trip_data'], indent=2)}")
                logger.info("✅ Multi-City Smart Logic Applied Successfully!")
            else:
                logger.error("❌ Smart Trip Data Not Found in Conversation State")
        else:
            logger.error("❌ Failed to Extract Trip Request")
        
        return trip_request is not None and "smart_trip_data" in conversation_state
    
    async def test_regular_city_scenario(self):
        """Test regular city trip planning (no special logic)"""
        logger.info("🏙️ Testing Regular City Scenario: New York")
        
        # Test message
        test_message = "Plan a trip to New York for 2 travelers starting from November 1st 2025 for 4 days with $2000 budget"
        
        # Mock conversation state
        conversation_state = {
            "origin": "Los Angeles",
            "current_state": "gathering_info"
        }
        
        logger.info(f"Test Message: {test_message}")
        logger.info(f"Conversation State: {conversation_state}")
        
        # Test trip type analysis
        trip_analysis = await self.smart_service.analyze_trip_type(test_message)
        logger.info(f"Trip Analysis: {json.dumps(trip_analysis, indent=2)}")
        
        # Test trip request extraction
        trip_request = await _extract_trip_request(test_message, conversation_state)
        if trip_request:
            logger.info(f"Extracted Trip Request: {trip_request.dict()}")
            
            # Check that no smart trip data was added (should be regular trip)
            if "smart_trip_data" not in conversation_state:
                logger.info("✅ Regular City Trip - No Smart Logic Applied (Correct)")
            else:
                logger.warning("⚠️ Smart Trip Data Found for Regular City Trip")
        else:
            logger.error("❌ Failed to Extract Trip Request")
        
        return trip_request is not None
    
    async def test_airport_api_integration(self):
        """Test the airport API integration"""
        logger.info("✈️ Testing Airport API Integration")
        
        # Test getting airports for Yosemite
        airport_data = await self.smart_service.get_airports_near_destination("Yosemite")
        if airport_data:
            logger.info(f"Airport Data for Yosemite: {json.dumps(airport_data, indent=2)}")
            logger.info("✅ Airport API Integration Working")
            return True
        else:
            logger.error("❌ Airport API Integration Failed")
            return False
    
    async def test_conversation_service_integration(self):
        """Test conversation service integration with smart trip logic"""
        logger.info("💬 Testing Conversation Service Integration")
        
        from services.conversation_service import ConversationService
        
        conversation_service = ConversationService()
        
        # Test with national park trip
        test_message = "Plan trip to Yellowstone National Park"
        trip_data = {
            "smart_trip_data": {
                "trip_type": "national_park",
                "recommended_airport": "Bozeman Yellowstone International Airport",
                "transportation_options": ["Rental car", "Shuttle service", "Private tour"],
                "minimum_days": 4
            }
        }
        
        # Test acknowledgment
        acknowledgment = conversation_service._acknowledge_new_information(test_message, trip_data)
        logger.info(f"Acknowledgment: {acknowledgment}")
        
        if "Smart planning" in acknowledgment and "national park" in acknowledgment:
            logger.info("✅ Conversation Service Smart Logic Working")
            return True
        else:
            logger.error("❌ Conversation Service Smart Logic Failed")
            return False
    
    async def run_all_tests(self):
        """Run all smart trip logic tests"""
        logger.info("🚀 Starting Smart Trip Logic Comprehensive Testing")
        logger.info("=" * 60)
        
        results = {}
        
        # Test 1: National Park Scenario
        logger.info("\n🏔️ TEST 1: National Park Scenario")
        results["national_park"] = await self.test_national_park_scenario()
        
        # Test 2: Multi-City Scenario
        logger.info("\n🌍 TEST 2: Multi-City Scenario")
        results["multi_city"] = await self.test_multi_city_scenario()
        
        # Test 3: Regular City Scenario
        logger.info("\n🏙️ TEST 3: Regular City Scenario")
        results["regular_city"] = await self.test_regular_city_scenario()
        
        # Test 4: Airport API Integration
        logger.info("\n✈️ TEST 4: Airport API Integration")
        results["airport_api"] = await self.test_airport_api_integration()
        
        # Test 5: Conversation Service Integration
        logger.info("\n💬 TEST 5: Conversation Service Integration")
        results["conversation_service"] = await self.test_conversation_service_integration()
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 ALL TESTS PASSED! Smart Trip Logic is working perfectly!")
        else:
            logger.warning(f"⚠️ {total - passed} tests failed. Please check the implementation.")
        
        return results

async def main():
    """Main test runner"""
    tester = SmartTripLogicTester()
    results = await tester.run_all_tests()
    
    # Return results for potential CI/CD integration
    return results

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main())
