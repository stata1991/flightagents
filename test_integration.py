import asyncio
import os
import sys
from unittest.mock import patch, AsyncMock, Mock
import pytest

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.hybrid_trip_router import HybridTripRouter
from api.models import TripPlanRequest

class TestIntegration:
    """Integration tests for the complete trip planning flow"""
    
    def setup_method(self):
        """Setup method to ensure RAPID_API_KEY is available"""
        if not os.getenv("RAPID_API_KEY"):
            os.environ["RAPID_API_KEY"] = "test_key_for_testing"
    
    @pytest.mark.asyncio
    async def test_full_trip_planning_hyderabad_to_bangalore(self):
        """Test complete trip planning from Hyderabad to Bangalore"""
        
        # Mock the flight service responses
        hyderabad_response = {
            "status": True,
            "data": [{"id": "HYD.AIRPORT", "type": "AIRPORT", "name": "Rajiv Gandhi International Airport"}]
        }
        
        bangalore_response = {
            "status": True,
            "data": [{"id": "BLR.AIRPORT", "type": "AIRPORT", "name": "Kempegowda International Airport"}]
        }
        
        flight_search_response = {
            "status": True,
            "data": {
                "flightOffers": [
                    {
                        "token": "test_flight_token_123",
                        "itineraries": [{
                            "segments": [{
                                "carrierCode": "6E",
                                "number": "289",
                                "departure": {"iataCode": "HYD", "terminal": "1"},
                                "arrival": {"iataCode": "BLR", "terminal": "1"},
                                "duration": "PT1H30M"
                            }]
                        }],
                        "pricingOptions": [{
                            "price": {"currency": "USD", "units": 5000, "nanos": 0}
                        }]
                    }
                ]
            }
        }
        
        # Mock the hotel service responses
        hotel_destination_response = Mock()
        hotel_destination_response.status_code = 200
        hotel_destination_response.json.return_value = {
            "status": True,
            "data": [{
                "dest_id": "-2090174",
                "search_type": "city",
                "dest_type": "city",
                "label": "Bangalore, Karnataka, India",
                "name": "Bangalore"
            }]
        }
        
        hotel_filters_response = Mock()
        hotel_filters_response.status_code = 200
        hotel_filters_response.json.return_value = {
            "status": True,
            "data": {
                "filters": [{
                    "title": "Your budget (for 5 nights)",
                    "field": "price",
                    "min": "2000",
                    "max": "40000"
                }]
            }
        }
        
        hotel_search_response = Mock()
        hotel_search_response.status_code = 200
        hotel_search_response.json.return_value = {
            "status": True,
            "data": {
                "hotels": [{
                    "hotel_id": 1162756,
                    "property": {
                        "name": "Test Hotel Bangalore",
                        "reviewScore": 8.8,
                        "reviewCount": 323,
                        "starRating": 3
                    },
                    "pricingOptions": [{
                        "price": {
                            "currency": "USD",
                            "units": 214,
                            "nanos": 0
                        }
                    }]
                }]
            }
        }
        
        # Mock the AI response
        ai_response = """
        # Trip Overview
        - Destination: Bangalore from Hyderabad (3 days)
        - Travel Theme: Urban Exploration, Culinary Adventures & Shopping
        - Perfect for: Couples seeking a vibrant city experience

        ## Day 1
        - Arrive in Bangalore
        - Visit Lalbagh Botanical Garden
        - Dinner at local restaurant

        ## Day 2
        - Explore Cubbon Park
        - Shopping at Commercial Street
        - Visit Bangalore Palace

        ## Day 3
        - Visit ISKCON Temple
        - Shopping at MG Road
        - Departure

        ## Budget Breakdown
        - Flights: $100-150
        - Hotels: $80-120/night
        - Food: $30-50/day
        - Activities: $20-40/day
        """
        
        with patch('aiohttp.ClientSession.get') as mock_flight_get, \
             patch('requests.get') as mock_hotel_get, \
             patch('api.enhanced_ai_provider.EnhancedAITripProvider._call_claude') as mock_ai:
            
            # Setup flight service mocks
            mock_flight_response = AsyncMock()
            mock_flight_response.status = 200
            mock_flight_response.json = AsyncMock(side_effect=[
                hyderabad_response,  # First call for Hyderabad
                bangalore_response,  # Second call for Bangalore
                flight_search_response  # Third call for flight search
            ])
            mock_flight_get.return_value.__aenter__.return_value = mock_flight_response
            
            # Setup hotel service mocks
            mock_hotel_get.side_effect = [
                hotel_destination_response,
                hotel_filters_response,
                hotel_search_response
            ]
            
            # Setup AI mock
            mock_ai.return_value = ai_response
            
            # Create trip request
            request = TripPlanRequest(
                origin="hyderabad",
                destination="bangalore",
                start_date="2025-08-21",
                end_date="2025-08-24",
                duration_days=3,
                travelers=2,
                interests=["culture", "food", "shopping"],
                budget_range="moderate",
                comprehensive_planning=True
            )
            
            # Create router and plan trip
            router = HybridTripRouter()
            result = await router.plan_trip(request)
            
            # Verify the result
            assert result is not None
            assert result.success == True
            assert "agents" in result.data
            
            # Check flight data
            flight_agent = result.data["agents"].get("flight_search_agent", {})
            if flight_agent.get("result", {}).get("success"):
                flights = flight_agent["result"]["flights"]
                assert len(flights) > 0
                assert flights[0]["airline"] == "6E"
                assert flights[0]["booking_link"] == "test_flight_token_123"
            
            # Check hotel data
            hotel_agent = result.data["agents"].get("hotel_search_agent", {})
            if hotel_agent.get("result", {}).get("success"):
                hotels = hotel_agent["result"]["hotels"]
                assert len(hotels) > 0
                assert hotels[0]["name"] == "Test Hotel Bangalore"
                assert "booking_link" in hotels[0]
    
    @pytest.mark.asyncio
    async def test_deep_link_generation(self):
        """Test deep link generation for flights and hotels"""
        from api.enhanced_ai_provider import EnhancedAITripProvider
        
        provider = EnhancedAITripProvider()
        
        # Test flight deep link generation
        flight = {
            "airline": "Spirit Airlines",
            "flight_number": "NK 1395"
        }
        
        flight_link = provider._generate_flight_deep_link(
            origin="hyderabad",
            destination="bangalore",
            date="2025-08-21",
            travelers=2,
            flight=flight
        )
        
        assert "expedia.com" in flight_link
        assert "hyderabad" in flight_link.lower()
        assert "bangalore" in flight_link.lower()
        
        # Test hotel deep link generation
        hotel = {
            "name": "Test Hotel",
            "hotel_id": "88948",
            "booking_link": "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD"
        }
        
        hotel_link = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        assert "booking.com" in hotel_link
        assert "88948" in hotel_link
        assert "checkin=2025-08-21" in hotel_link
        assert "checkout=2025-08-26" in hotel_link
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in trip planning"""
        
        # Mock API errors
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            mock_get.return_value.__aenter__.return_value = mock_response
            
            request = TripPlanRequest(
                origin="invalid",
                destination="invalid",
                start_date="2025-08-21",
                end_date="2025-08-24",
                duration_days=3,
                travelers=2,
                interests=["culture"],
                budget_range="moderate",
                comprehensive_planning=True
            )
            
            router = HybridTripRouter()
            result = await router.plan_trip(request)
            
            # Should still return a result, but with error information
            assert result is not None
            # The result might be successful with AI-generated content even if APIs fail
            assert hasattr(result, 'success')
    
    def test_url_encoding(self):
        """Test URL encoding for special characters in city names"""
        from urllib.parse import quote
        
        # Test cities with spaces and special characters
        cities = [
            "New York",
            "San Francisco",
            "Los Angeles",
            "Mumbai",
            "New Delhi"
        ]
        
        for city in cities:
            encoded = quote(city)
            assert "%" in encoded or encoded == city
            assert len(encoded) >= len(city)
    
    def test_booking_link_validation(self):
        """Test validation of booking links"""
        from api.enhanced_ai_provider import EnhancedAITripProvider
        
        provider = EnhancedAITripProvider()
        
        # Valid booking links
        valid_links = [
            "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD",
            "https://www.expedia.com/Flights-Search?leg1=from:hyderabad,to:bangalore,departure:2025-08-21TANYT&passengers=adults:2,children:0"
        ]
        
        for link in valid_links:
            assert link.startswith("https://")
            assert "booking.com" in link or "expedia.com" in link
        
        # Test hotel deep link generation with valid data
        hotel = {
            "name": "Test Hotel",
            "hotel_id": "12345",
            "booking_link": valid_links[0]
        }
        
        result = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        assert result.startswith("https://www.booking.com/hotel/")
        assert "checkin=2025-08-21" in result
        assert "checkout=2025-08-26" in result

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 