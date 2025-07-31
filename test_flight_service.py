import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock
import pytest

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.flight_service import FlightService

class TestFlightService:
    """Test class for FlightService functionality"""
    
    def setup_method(self):
        """Setup method to ensure RAPID_API_KEY is available"""
        if not os.getenv("RAPID_API_KEY"):
            os.environ["RAPID_API_KEY"] = "test_key_for_testing"
    
    @pytest.mark.asyncio
    async def test_search_destination_hyderabad(self):
        """Test searching for Hyderabad airport/city ID"""
        # Mock the API response for Hyderabad
        mock_response = {
            "status": True,
            "data": [
                {
                    "id": "HYD.AIRPORT",
                    "type": "AIRPORT",
                    "name": "Rajiv Gandhi International Airport",
                    "code": "HYD",
                    "city": "HYD",
                    "cityName": "Hyderabad",
                    "regionName": "Telangana",
                    "country": "IN"
                },
                {
                    "id": "HYD.CITY",
                    "type": "CITY",
                    "name": "Hyderabad",
                    "cityName": "Hyderabad",
                    "regionName": "Telangana",
                    "country": "IN"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj
            
            result = await FlightService._get_airport_id("hyderabad")
            
            assert result == "HYD.AIRPORT"
    
    @pytest.mark.asyncio
    async def test_search_destination_bangalore(self):
        """Test searching for Bangalore airport/city ID"""
        # Mock the API response for Bangalore
        mock_response = {
            "status": True,
            "data": [
                {
                    "id": "BLR.AIRPORT",
                    "type": "AIRPORT",
                    "name": "Kempegowda International Airport",
                    "code": "BLR",
                    "city": "BLR",
                    "cityName": "Bangalore",
                    "regionName": "Karnataka",
                    "country": "IN"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj
            
            result = await FlightService._get_airport_id("bangalore")
            
            assert result == "BLR.AIRPORT"
    
    @pytest.mark.asyncio
    async def test_search_destination_indian_city_fallback(self):
        """Test fallback for Indian cities without specific airport codes"""
        # Mock the API response for a city without airport
        mock_response = {
            "status": True,
            "data": [
                {
                    "id": "CITY123",
                    "type": "LOCATION",
                    "name": "Test City",
                    "cityName": "Test City",
                    "regionName": "Test State",
                    "country": "IN"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value = mock_response_obj
            
            result = await FlightService._get_airport_id("testcity")
            
            assert result == "CITY123"
    
    @pytest.mark.asyncio
    async def test_search_flights_hyderabad_to_bangalore(self):
        """Test flight search from Hyderabad to Bangalore"""
        # Mock the destination search responses
        hyderabad_response = {
            "status": True,
            "data": [{"id": "HYD.AIRPORT", "type": "AIRPORT", "name": "Rajiv Gandhi International Airport"}]
        }
        
        bangalore_response = {
            "status": True,
            "data": [{"id": "BLR.AIRPORT", "type": "AIRPORT", "name": "Kempegowda International Airport"}]
        }
        
        # Mock the flight search response
        flight_response = {
            "status": True,
            "data": {
                "flightOffers": [
                    {
                        "token": "test_token_123",
                        "segments": [{
                            "duration": 5400,  # 1.5 hours in seconds
                            "legs": [{
                                "carriersData": [{
                                    "name": "IndiGo",
                                    "code": "6E"
                                }],
                                "flightInfo": {
                                    "flightNumber": "289"
                                },
                                "departure": "2025-08-21T10:00:00",
                                "arrival": "2025-08-21T11:30:00"
                            }]
                        }],
                        "priceBreakdown": {
                            "total": {
                                "currency": "USD",
                                "units": 5000,
                                "nanos": 0
                            }
                        }
                    }
                ]
            }
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 200
            mock_response_obj.json = AsyncMock(side_effect=[
                hyderabad_response,  # First call for Hyderabad
                bangalore_response,  # Second call for Bangalore
                flight_response      # Third call for flight search
            ])
            mock_get.return_value.__aenter__.return_value = mock_response_obj
            
            context = {
                "origin": "hyderabad",
                "destination": "bangalore",
                "start_date": "2025-08-21",
                "return_date": "2025-08-24",
                "travelers": 2
            }
            
            result = await FlightService.search_flights(context)
            
            assert result["success"] == True
            assert len(result["flights"]) > 0
            assert "categorized_flights" in result
    
    @pytest.mark.asyncio
    async def test_search_flights_api_error(self):
        """Test flight search when API returns error"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.status = 400
            mock_response_obj.text = AsyncMock(return_value="Bad Request")
            mock_get.return_value.__aenter__.return_value = mock_response_obj
            
            context = {
                "origin": "invalid",
                "destination": "invalid",
                "start_date": "2025-08-21",
                "return_date": "2025-08-24",
                "travelers": 2
            }
            
            result = await FlightService.search_flights(context)
            
            assert result["success"] == False
            assert "error" in result
    
    def test_parse_flight_offer(self):
        """Test parsing flight offer from API response"""
        offer = {
            "token": "test_token_123",
            "segments": [{
                "duration": 5400,  # 1.5 hours in seconds
                "legs": [{
                    "carriersData": [{
                        "name": "IndiGo",
                        "code": "6E"
                    }],
                    "flightInfo": {
                        "flightNumber": "289"
                    },
                    "departure": "2025-08-21T10:00:00",
                    "arrival": "2025-08-21T11:30:00"
                }]
            }],
            "priceBreakdown": {
                "total": {
                    "currency": "USD",
                    "units": 5000,
                    "nanos": 0
                }
            }
        }
        
        result = FlightService._parse_flight_offer(offer)
        
        assert result is not None
        assert result["airline"] == "IndiGo"
        assert result["flight_number"] == "6E 289"
        assert result["booking_link"] == "test_token_123"
    
    def test_categorize_flights(self):
        """Test flight categorization logic"""
        flights = [
            {"airline": "6E", "cost": 100, "duration": 90},
            {"airline": "AI", "cost": 150, "duration": 85},
            {"airline": "6E", "cost": 120, "duration": 95}
        ]
        
        result = FlightService._categorize_flights(flights)
        
        assert "fastest" in result
        assert "cheapest" in result
        assert "optimal" in result
        assert len(result["fastest"]) > 0
        assert len(result["cheapest"]) > 0
        assert len(result["optimal"]) > 0

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 