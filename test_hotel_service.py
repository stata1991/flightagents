import os
import sys
from unittest.mock import patch, Mock
import pytest

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.hotel_client import HotelClient
from api.enhanced_ai_provider import EnhancedAITripProvider

class TestHotelService:
    """Test class for HotelService functionality"""
    
    def setup_method(self):
        """Setup method to ensure RAPID_API_KEY is available"""
        if not os.getenv("RAPID_API_KEY"):
            os.environ["RAPID_API_KEY"] = "test_key_for_testing"
    
    def test_generate_hotel_booking_url(self):
        """Test generating hotel booking URL"""
        client = HotelClient()
        
        # Test with valid parameters
        url = client.generate_hotel_booking_url(
            hotel_id="88948",
            check_in="2025-08-21",
            check_out="2025-08-26",
            adults=2,
            children=[10, 12],
            rooms=1,
            currency="USD"
        )
        
        expected_url = "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD&children=10,12"
        assert url == expected_url
    
    def test_generate_hotel_booking_url_no_children(self):
        """Test generating hotel booking URL without children"""
        client = HotelClient()
        
        url = client.generate_hotel_booking_url(
            hotel_id="88948",
            check_in="2025-08-21",
            check_out="2025-08-26",
            adults=2,
            rooms=1,
            currency="USD"
        )
        
        expected_url = "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD"
        assert url == expected_url
    
    @patch('requests.get')
    def test_search_destination_bangalore(self, mock_get):
        """Test searching for Bangalore destination"""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mock response text"
        mock_response.json.return_value = {
            "status": True,
            "data": [
                {
                    "dest_id": "-2090174",
                    "search_type": "city",
                    "dest_type": "city",
                    "region": "Karnataka",
                    "latitude": 12.976346,
                    "city_name": "Bangalore",
                    "label": "Bangalore, Karnataka, India",
                    "country": "India",
                    "name": "Bangalore",
                    "hotels": 2923
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = HotelClient()
        result = client.search_destination("bangalore")
        
        assert result["status"] == True
        assert len(result["destinations"]) > 0
        assert result["destinations"][0]["dest_id"] == "-2090174"
        assert result["destinations"][0]["name"] == "Bangalore"
    
    @patch('requests.get')
    def test_search_hotels_with_filters(self, mock_get):
        """Test searching hotels with filters"""
        # Mock the API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Mock response text"
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "hotels": [
                    {
                        "hotel_id": 1162756,
                        "property": {
                            "name": "Test Hotel",
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
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        client = HotelClient()
        result = client.search_hotels_with_filters(
            dest_id="-2090174",
            search_type="CITY",
            check_in="2025-08-21",
            check_out="2025-08-26",
            adults=2,
            rooms=1,
            filters={"price": "0-300"}
        )
        
        assert result["status"] == True
        assert "hotels" in result["data"]
        assert len(result["data"]["hotels"]) > 0
    
    def test_generate_hotel_deep_link_existing_url(self):
        """Test generating hotel deep link with existing booking URL"""
        provider = EnhancedAITripProvider()
        
        hotel = {
            "name": "Test Hotel",
            "booking_link": "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD",
            "hotel_id": "88948"
        }
        
        result = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        # Should return the existing URL since it's already a proper Booking.com URL
        assert result == hotel["booking_link"]
    
    def test_generate_hotel_deep_link_from_hotel_id(self):
        """Test generating hotel deep link from hotel ID"""
        provider = EnhancedAITripProvider()
        
        hotel = {
            "name": "Test Hotel",
            "hotel_id": "88948",
            "booking_link": "invalid_url"
        }
        
        result = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        expected_url = "https://www.booking.com/hotel/88948.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD"
        assert result == expected_url
    
    def test_generate_hotel_deep_link_extract_from_url(self):
        """Test generating hotel deep link by extracting hotel ID from URL"""
        provider = EnhancedAITripProvider()
        
        hotel = {
            "name": "Test Hotel",
            "booking_link": "https://www.booking.com/hotel/88948.html?some=params",
            "hotel_id": ""  # Empty hotel_id
        }
        
        result = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        # Should return the existing URL since it's already a proper Booking.com URL
        assert result == hotel["booking_link"]
    
    def test_generate_hotel_deep_link_fallback(self):
        """Test generating hotel deep link with fallback to existing URL"""
        provider = EnhancedAITripProvider()
        
        hotel = {
            "name": "Test Hotel",
            "booking_link": "https://some-other-site.com/hotel/123",
            "hotel_id": ""  # Empty hotel_id
        }
        
        result = provider._generate_hotel_deep_link(
            hotel=hotel,
            checkin_date="2025-08-21",
            checkout_date="2025-08-26",
            travelers=2
        )
        
        # Should extract hotel_id from URL and generate new URL
        expected_url = "https://www.booking.com/hotel/123.html?checkin=2025-08-21&checkout=2025-08-26&adults=2&rooms=1&currency=USD"
        assert result == expected_url
    
    @patch('requests.get')
    def test_smart_hotel_search_bangalore(self, mock_get):
        """Test smart hotel search for Bangalore"""
        # Mock the destination search response
        destination_response = Mock()
        destination_response.status_code = 200
        destination_response.text = "Mock response text"
        destination_response.json.return_value = {
            "status": True,
            "data": [{
                "dest_id": "-2090174",
                "search_type": "city",
                "dest_type": "city",
                "label": "Bangalore, Karnataka, India",
                "name": "Bangalore",
                "country": "India",
                "region": "Karnataka"
            }]
        }
        
        # Mock the filters response
        filters_response = Mock()
        filters_response.status_code = 200
        filters_response.text = "Mock response text"
        filters_response.json.return_value = {
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
        
        # Mock the hotel search response
        hotel_response = Mock()
        hotel_response.status_code = 200
        hotel_response.text = "Mock response text"
        hotel_response.json.return_value = {
            "status": True,
            "data": {
                "hotels": [{
                    "hotel_id": 1162756,
                    "property": {
                        "name": "Test Hotel",
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
        
        # Set up mock to return different responses for different calls
        mock_get.side_effect = [destination_response, filters_response, hotel_response]
        
        from api.models import HotelSearchRequest
        
        request = HotelSearchRequest(
            location="bangalore",
            check_in="2025-08-21",
            check_out="2025-08-26",
            adults=2,
            children=[],
            rooms=1,
            currency="USD"
        )
        
        client = HotelClient()
        result = client.smart_hotel_search(request, max_budget=300)
        
        assert result.success == True
        assert len(result.hotels) > 0
        assert result.hotels[0].name == "Test Hotel"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 