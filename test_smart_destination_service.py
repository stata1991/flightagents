#!/usr/bin/env python3

import asyncio
import os
import sys
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.smart_destination_service import SmartDestinationService

class TestSmartDestinationService:
    """Test cases for SmartDestinationService."""
    
    @pytest.fixture
    def service(self):
        """Create a SmartDestinationService instance for testing."""
        os.environ["RAPID_API_KEY"] = "test_key"
        return SmartDestinationService()
    
    @pytest.mark.asyncio
    async def test_analyze_trip_type_national_park(self, service):
        """Test trip type analysis for national parks."""
        
        test_cases = [
            ("Plan a trip to Yosemite National Park", "national_park", "yosemite"),
            ("I want to visit Yellowstone", "national_park", "yellowstone"),
            ("Planning a Grand Canyon adventure", "national_park", "grand canyon"),
            ("Zion National Park trip", "national_park", "zion"),
            ("Rocky Mountain National Park vacation", "national_park", "rocky mountain")
        ]
        
        for user_input, expected_type, expected_destination in test_cases:
            result = await service.analyze_trip_type(user_input)
            
            assert result["trip_type"] == expected_type
            assert expected_destination in result["destination"]
            assert result["requires_airport_logic"] == True
    
    @pytest.mark.asyncio
    async def test_analyze_trip_type_multi_city(self, service):
        """Test trip type analysis for multi-city trips."""
        
        test_cases = [
            ("Plan a trip from Dallas to Italy", "multi_city", "italy"),
            ("France vacation with multiple cities", "multi_city", "france"),
            ("Spain tour", "multi_city", "spain"),
            ("Japan travel itinerary", "multi_city", "japan"),
            ("Germany multi-city trip", "multi_city", "germany")
        ]
        
        for user_input, expected_type, expected_destination in test_cases:
            result = await service.analyze_trip_type(user_input)
            
            assert result["trip_type"] == expected_type
            assert result["destination"] == expected_destination
            assert result["requires_route_planning"] == True
    
    @pytest.mark.asyncio
    async def test_analyze_trip_type_specific_cities(self, service):
        """Test trip type analysis for specific city mentions."""
        
        test_cases = [
            ("Rome Florence Venice trip", "multi_city", "italy"),
            ("Paris Lyon Nice vacation", "multi_city", "france"),
            ("Madrid Barcelona Seville tour", "multi_city", "spain")
        ]
        
        for user_input, expected_type, expected_destination in test_cases:
            result = await service.analyze_trip_type(user_input)
            
            assert result["trip_type"] == expected_type
            assert result["destination"] == expected_destination
            assert result["requires_route_planning"] == True
    
    @pytest.mark.asyncio
    async def test_analyze_trip_type_single_destination(self, service):
        """Test trip type analysis for single destinations."""
        
        test_cases = [
            "Plan a trip to Paris",
            "Visit London",
            "Go to Tokyo",
            "Travel to New York",
            "Vacation in Sydney"
        ]
        
        for user_input in test_cases:
            result = await service.analyze_trip_type(user_input)
            
            assert result["trip_type"] == "single_destination"
            assert result["destination"] is None
            assert result["requires_basic_planning"] == True
    
    @pytest.mark.asyncio
    @patch('services.smart_destination_service.aiohttp.ClientSession')
    async def test_get_airports_near_destination_success(self, mock_session, service):
        """Test successful airport retrieval for a destination."""
        
        # Mock API response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": True,
            "data": [
                {
                    "id": "SFO.AIRPORT",
                    "type": "AIRPORT",
                    "name": "San Francisco International Airport",
                    "code": "SFO",
                    "cityName": "San Francisco",
                    "distanceToCity": {"value": 20.5, "unit": "km"}
                },
                {
                    "id": "SJC.AIRPORT",
                    "type": "AIRPORT",
                    "name": "San Jose International Airport",
                    "code": "SJC",
                    "cityName": "San Jose",
                    "distanceToCity": {"value": 45.2, "unit": "km"}
                },
                {
                    "id": "SFO.CITY",
                    "type": "CITY",
                    "name": "San Francisco",
                    "code": "SFO"
                }
            ]
        })
        
        # Set up the mock chain properly
        mock_session_instance = Mock()
        mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
        mock_session_instance.__aexit__ = AsyncMock(return_value=None)
        mock_session_instance.get = AsyncMock(return_value=mock_response)
        mock_session.return_value = mock_session_instance
        
        result = await service.get_airports_near_destination("Yosemite")
        
        assert result is not None
        assert result["destination"] == "Yosemite"
        assert len(result["airports"]) == 2
        assert len(result["cities"]) == 1
        
        # Check airports are sorted by distance
        assert result["airports"][0]["distance"] == 20.5
        assert result["airports"][1]["distance"] == 45.2
    
    @pytest.mark.asyncio
    @patch('services.smart_destination_service.aiohttp.ClientSession')
    async def test_get_airports_near_destination_api_failure(self, mock_session, service):
        """Test airport retrieval when API fails."""
        
        # Mock API failure
        mock_response = Mock()
        mock_response.status = 500
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await service.get_airports_near_destination("Yosemite")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('services.smart_destination_service.aiohttp.ClientSession')
    async def test_get_smart_airport_recommendation_national_park(self, mock_session, service):
        """Test smart airport recommendation for national parks."""
        
        # Mock API response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "status": True,
            "data": [
                {
                    "id": "SFO.AIRPORT",
                    "type": "AIRPORT",
                    "name": "San Francisco International Airport",
                    "code": "SFO",
                    "cityName": "San Francisco",
                    "distanceToCity": {"value": 20.5, "unit": "km"}
                },
                {
                    "id": "SJC.AIRPORT",
                    "type": "AIRPORT",
                    "name": "San Jose International Airport",
                    "code": "SJC",
                    "cityName": "San Jose",
                    "distanceToCity": {"value": 45.2, "unit": "km"}
                }
            ]
        })
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        result = await service.get_smart_airport_recommendation("yosemite", "national_park")
        
        assert result is not None
        assert result["primary_airport"] == "SFO.AIRPORT"
        assert result["airport_name"] == "San Francisco International Airport"
        assert "SJC.AIRPORT" in result["alternative_airports"]
        assert result["distance_to_destination"] == "20.5 km"
        assert "Rental car" in result["transportation_options"]
        assert result["minimum_days"] == 4
    
    @pytest.mark.asyncio
    async def test_get_smart_airport_recommendation_multi_city(self, service):
        """Test smart airport recommendation for multi-city trips."""
        
        result = await service.get_smart_airport_recommendation("italy", "multi_city")
        
        assert result is not None
        assert result["requires_destination_specialist"] == True
        assert result["destination"] == "italy"
        assert result["trip_type"] == "multi_city"
    
    @pytest.mark.asyncio
    async def test_get_multi_city_route_suggestion_italy(self, service):
        """Test multi-city route suggestion for Italy."""
        
        result = service.get_multi_city_route_suggestion("italy")
        
        assert result is not None
        assert result["cities"] == ["Rome", "Florence", "Venice"]
        assert result["route_type"] == "Cultural Renaissance"
        assert "Rome_to_Florence" in result["transportation"]
        assert "Florence_to_Venice" in result["transportation"]
        assert "Ancient Rome" in result["themes"]
        assert result["minimum_days"] == 10
    
    @pytest.mark.asyncio
    async def test_get_multi_city_route_suggestion_france(self, service):
        """Test multi-city route suggestion for France."""
        
        result = service.get_multi_city_route_suggestion("france")
        
        assert result is not None
        assert result["cities"] == ["Paris", "Lyon", "Nice"]
        assert result["route_type"] == "French Culture & Cuisine"
        assert "Paris_to_Lyon" in result["transportation"]
        assert "Lyon_to_Nice" in result["transportation"]
        assert "Parisian Culture" in result["themes"]
        assert result["minimum_days"] == 12
    
    @pytest.mark.asyncio
    async def test_get_multi_city_route_suggestion_unknown_country(self, service):
        """Test multi-city route suggestion for unknown country."""
        
        result = service.get_multi_city_route_suggestion("unknown_country")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('services.smart_destination_service.SmartDestinationService.get_smart_airport_recommendation')
    async def test_create_smart_itinerary_request_national_park(self, mock_airport_rec, service):
        """Test creating smart itinerary request for national park."""
        
        # Mock airport recommendation
        mock_airport_rec.return_value = {
            "primary_airport": "SFO.AIRPORT",
            "airport_name": "San Francisco International Airport",
            "alternative_airports": ["SJC.AIRPORT"],
            "distance_to_destination": "20.5 km",
            "transportation_options": ["Rental car"],
            "minimum_days": 4
        }
        
        result = await service.create_smart_itinerary_request("Plan a trip to Yosemite National Park")
        
        assert result["trip_type"] == "national_park"
        assert result["destination"] == "yosemite"
        assert result["requires_smart_airport_logic"] == True
        assert result["airport_recommendation"] is not None
    
    @pytest.mark.asyncio
    @patch('services.smart_destination_service.SmartDestinationService.get_multi_city_route_suggestion')
    async def test_create_smart_itinerary_request_multi_city(self, mock_route_suggestion, service):
        """Test creating smart itinerary request for multi-city trip."""
        
        # Mock route suggestion
        mock_route_suggestion.return_value = {
            "cities": ["Rome", "Florence", "Venice"],
            "route_type": "Cultural Renaissance",
            "transportation": {},
            "themes": ["Ancient Rome"],
            "minimum_days": 10
        }
        
        result = await service.create_smart_itinerary_request("Plan a trip from Dallas to Italy")
        
        assert result["trip_type"] == "multi_city"
        assert result["destination"] == "italy"
        assert result["requires_multi_city_planning"] == True
        assert result["route_suggestion"] is not None
    
    @pytest.mark.asyncio
    async def test_create_smart_itinerary_request_single_destination(self, service):
        """Test creating smart itinerary request for single destination."""
        
        result = await service.create_smart_itinerary_request("Plan a trip to Paris")
        
        assert result["trip_type"] == "single_destination"
        assert result["destination"] is None
        assert result["requires_basic_planning"] == True
    
    @pytest.mark.asyncio
    async def test_service_initialization_without_api_key(self):
        """Test service initialization without API key."""
        
        # Remove API key temporarily
        original_key = os.environ.get("RAPID_API_KEY")
        if "RAPID_API_KEY" in os.environ:
            del os.environ["RAPID_API_KEY"]
        
        service = SmartDestinationService()
        
        # Restore API key
        if original_key:
            os.environ["RAPID_API_KEY"] = original_key
        
        # Service should still be created but log an error
        assert service is not None

def run_integration_tests():
    """Run integration tests with real API calls (optional)."""
    
    async def test_real_api_calls():
        """Test real API calls (only run if you want to test actual API)."""
        
        print("🧪 Running Integration Tests with Real APIs...")
        
        service = SmartDestinationService()
        
        # Test 1: Trip type analysis
        print("\n1. Testing Trip Type Analysis:")
        test_inputs = [
            "Plan a trip to Yosemite National Park",
            "Plan a trip from Dallas to Italy",
            "Visit Paris for a week"
        ]
        
        for user_input in test_inputs:
            result = await service.analyze_trip_type(user_input)
            print(f"   Input: {user_input}")
            print(f"   Result: {result}")
        
        # Test 2: Airport recommendations (if API key is available)
        if service.rapid_api_key:
            print("\n2. Testing Airport Recommendations:")
            destinations = ["Yosemite", "Yellowstone", "Grand Canyon"]
            
            for destination in destinations:
                result = await service.get_airports_near_destination(destination)
                print(f"   {destination}: {len(result['airports']) if result else 0} airports found")
        
        print("\n✅ Integration tests completed!")
    
    # Only run if explicitly requested
    if "--integration" in sys.argv:
        asyncio.run(test_real_api_calls())

if __name__ == "__main__":
    # Run unit tests
    pytest.main([__file__, "-v"])
    
    # Run integration tests if requested
    run_integration_tests() 