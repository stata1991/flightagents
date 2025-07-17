import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import logging
from .models import HotelSearchRequest, HotelSearchResponse, HotelInfo, HotelRoom, HotelSearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HotelClient:
    """Client for Booking.com Hotel Rapid API integration"""
    
    def __init__(self):
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        self.base_url = "https://booking-com15.p.rapidapi.com"
        api_key = os.getenv('RAPID_API_KEY')
        if not api_key:
            raise ValueError("RAPID_API_KEY environment variable is required")
        self.headers = {
            'x-rapidapi-host': 'booking-com15.p.rapidapi.com',
            'x-rapidapi-key': api_key
        }
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Booking.com API"""
        try:
            url = f"{self.base_url}{endpoint}"
            logger.info(f"Making hotel API request to: {url}")
            logger.info(f"Parameters: {params}")
            
            response = requests.get(url, headers=self.headers, params=params)
            
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            # Log response content for debugging (first 500 chars)
            response_text = response.text[:500]
            logger.info(f"Response content (first 500 chars): {response_text}")
            
            response.raise_for_status()
            
            try:
                result = response.json()
                logger.info(f"Successfully parsed JSON response")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Full response text: {response.text}")
                return {"error": f"Invalid JSON response: {str(e)}"}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Hotel API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
                return {"error": f"Hotel API request failed: {e.response.status_code} - {e.response.text}"}
            return {"error": f"Hotel API request failed: {str(e)}"}
    
    def search_destination(self, query: str) -> Dict[str, Any]:
        """
        Search for destinations to get destination ID
        
        Args:
            query: Search query (city name, etc.)
            
        Returns:
            Dict containing destination data with dest_id
        """
        endpoint = "/api/v1/hotels/searchDestination"
        params = {"query": query}
        
        logger.info(f"Destination search requested for: {query}")
        result = self._make_request(endpoint, params)
        
        if "error" in result:
            return result
        
        # Extract and format the results
        destinations = []
        if result.get("status") and result.get("data"):
            for item in result["data"]:
                destination = {
                    "dest_id": item.get("dest_id"),
                    "search_type": item.get("search_type"),
                    "dest_type": item.get("dest_type"),
                    "label": item.get("label"),
                    "name": item.get("name"),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "country": item.get("country"),
                    "region": item.get("region"),
                    "city_name": item.get("city_name"),
                    "hotels": item.get("hotels"),
                    "nr_hotels": item.get("nr_hotels"),
                    "image_url": item.get("image_url"),
                    "type": item.get("type")
                }
                destinations.append(destination)
        
        return {
            "status": result.get("status", False),
            "message": result.get("message", ""),
            "destinations": destinations
        }

    def search_hotels(self, request: HotelSearchRequest) -> HotelSearchResponse:
        """
        Search for hotels using Booking.com API
        """
        # First, search for destination to get dest_id
        dest_search = self.search_destination(request.location)
        logger.info(f"Destination search result: {dest_search}")
        if "error" in dest_search or not dest_search.get("destinations"):
            error_msg = dest_search.get("error", "Destination not found")
            logger.error(f"Hotel search error: {error_msg}")
            return HotelSearchResponse(
                location=request.location,
                check_in=request.check_in,
                check_out=request.check_out,
                total_results=0,
                hotels=[],
                search_metadata={"error": error_msg}
            )
        
        # Get the first destination (usually the city)
        dest_id = dest_search["destinations"][0]["dest_id"]
        search_type = dest_search["destinations"][0]["search_type"].upper()
        
        endpoint = "/api/v1/hotels/searchHotels"
        
        # Build parameters based on actual API structure
        params = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": request.check_in,
            "departure_date": request.check_out,
            "adults": request.adults,
            "children_age": ",".join(map(str, request.children)) if request.children else "0,17",
            "room_qty": request.rooms,
            "page_number": request.page_number,
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": request.language,
            "currency_code": request.currency,
            "location": "US"
        }
        
        logger.info(f"Hotel search API params: {params}")
        result = self._make_request(endpoint, params)
        logger.info(f"Hotel search API result: {result}")
        
        if "error" in result:
            logger.error(f"Hotel search API error: {result['error']}")
            return HotelSearchResponse(
                location=request.location,
                check_in=request.check_in,
                check_out=request.check_out,
                total_results=0,
                hotels=[],
                search_metadata={"error": result["error"]}
            )
        
        # Parse the response and convert to our models
        hotels = []
        total_results = 0
        
        if result.get("status") and result.get("data"):
            data = result["data"]
            total_results = len(data.get("hotels", []))
            
            for hotel_data in data.get("hotels", []):
                hotel_info = self._parse_hotel_info(hotel_data)
                rooms = self._parse_hotel_rooms(hotel_data.get("property", {}))
                
                # Calculate average price from property data
                property_data = hotel_data.get("property", {})
                price_breakdown = property_data.get("priceBreakdown", {})
                gross_price = price_breakdown.get("grossPrice", {})
                avg_price = gross_price.get("value") if gross_price else None
                
                hotel_result = HotelSearchResult(
                    hotel=hotel_info,
                    rooms=rooms,
                    average_price_per_night=avg_price,
                    total_price=avg_price,
                    currency=request.currency,
                    availability=True
                )
                hotels.append(hotel_result)
        else:
            logger.error(f"Hotel search API returned no data or status is false: {result}")
            return HotelSearchResponse(
                location=request.location,
                check_in=request.check_in,
                check_out=request.check_out,
                total_results=0,
                hotels=[],
                search_metadata={"error": "No hotels found or API returned no data"}
            )
        
        return HotelSearchResponse(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            total_results=total_results,
            hotels=hotels,
            search_metadata=result
        )
    
    def _parse_hotel_info(self, hotel_data: Dict[str, Any]) -> HotelInfo:
        """Parse hotel information from API response"""
        property_data = hotel_data.get("property", {})
        
        return HotelInfo(
            hotel_id=str(hotel_data.get("hotel_id", "")),
            name=property_data.get("name", ""),
            address=property_data.get("address", ""),
            city=property_data.get("city_name", ""),
            country=property_data.get("countryCode", ""),
            latitude=property_data.get("latitude"),
            longitude=property_data.get("longitude"),
            rating=property_data.get("reviewScore"),
            review_score=property_data.get("reviewScore"),
            review_count=property_data.get("reviewCount"),
            star_rating=property_data.get("propertyClass"),
            property_type=property_data.get("type"),
            amenities=[],  # Will be populated from separate API call if needed
            photos=property_data.get("photoUrls", []),
            description=hotel_data.get("accessibilityLabel", ""),
            booking_url=None  # Will be generated separately
        )
    
    def _parse_hotel_rooms(self, property_data: Dict[str, Any]) -> List[HotelRoom]:
        """Parse room information from API response"""
        # Since the API doesn't provide detailed room info in search results,
        # we'll create a basic room entry based on the property data
        price_breakdown = property_data.get("priceBreakdown", {})
        gross_price = price_breakdown.get("grossPrice", {})
        
        room = HotelRoom(
            room_id=f"room_{property_data.get('id', 'default')}",
            room_type="Standard Room",  # Default since not provided in search
            bed_configuration="1 bed",  # Default
            max_occupancy=2,  # Default
            cancellation_policy="Standard",  # Default
            meal_plan="Room Only",  # Default
            price_per_night=gross_price.get("value") if gross_price else None,
            total_price=gross_price.get("value") if gross_price else None,
            currency=gross_price.get("currency", "USD"),
            availability=True
        )
        return [room]
    
    def get_hotel_details(self, hotel_id: str, check_in: str, check_out: str, 
                         adults: int = 1, children: List[int] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific hotel
        
        Args:
            hotel_id: Hotel ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            children: Ages of children
        """
        endpoint = "/api/v1/hotels/getHotelDetails"
        
        params = {
            "hotel_id": hotel_id,
            "arrival_date": check_in,
            "departure_date": check_out,
            "adults": adults
        }
        
        if children:
            params["children_age"] = ",".join(map(str, children))
        
        logger.info(f"Hotel details requested for hotel ID: {hotel_id}")
        return self._make_request(endpoint, params)
    
    def search_hotel_availability(self, hotel_id: str, check_in: str, check_out: str,
                                 adults: int = 1, children: List[int] = None) -> Dict[str, Any]:
        """
        Check availability for a specific hotel
        
        Args:
            hotel_id: Hotel ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            children: Ages of children
        """
        endpoint = "/api/v1/hotels/getHotelAvailability"
        
        params = {
            "hotel_id": hotel_id,
            "arrival_date": check_in,
            "departure_date": check_out,
            "adults": adults
        }
        
        if children:
            params["children_age"] = ",".join(map(str, children))
        
        logger.info(f"Hotel availability check for hotel ID: {hotel_id}")
        return self._make_request(endpoint, params)
    
    def get_hotel_photos(self, hotel_id: str) -> Dict[str, Any]:
        """
        Get photos for a specific hotel
        
        Args:
            hotel_id: Hotel ID
        """
        endpoint = "/api/v1/hotels/getHotelPhotos"
        
        params = {"hotel_id": hotel_id}
        
        logger.info(f"Hotel photos requested for hotel ID: {hotel_id}")
        return self._make_request(endpoint, params)
    
    def get_hotel_reviews(self, hotel_id: str, page: int = 1, 
                         language: str = "en-us") -> Dict[str, Any]:
        """
        Get reviews for a specific hotel
        
        Args:
            hotel_id: Hotel ID
            page: Page number for pagination
            language: Language code for reviews
        """
        endpoint = "/api/v1/hotels/getHotelReviews"
        
        params = {
            "hotel_id": hotel_id,
            "page": page,
            "language": language
        }
        
        logger.info(f"Hotel reviews requested for hotel ID: {hotel_id}")
        return self._make_request(endpoint, params)
    
    def search_hotels_by_location(self, location: str, check_in: str, check_out: str,
                                 adults: int = 1, children: List[int] = None,
                                 rooms: int = 1, currency: str = "USD") -> HotelSearchResponse:
        """
        Convenience method to search hotels by location string
        
        Args:
            location: Location string (city, country)
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            children: Ages of children
            rooms: Number of rooms
            currency: Currency code
        """
        request = HotelSearchRequest(
            location=location,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children or [],
            rooms=rooms,
            currency=currency
        )
        
        return self.search_hotels(request)
    
    def generate_hotel_booking_url(self, hotel_id: str, check_in: str, check_out: str,
                                  adults: int = 1, children: List[int] = None,
                                  rooms: int = 1, currency: str = "USD") -> str:
        """
        Generate a booking URL for a hotel
        
        Args:
            hotel_id: Hotel ID
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            children: Ages of children
            rooms: Number of rooms
            currency: Currency code
        """
        base_url = "https://www.booking.com/hotel"
        
        # Build URL parameters
        params = {
            "checkin": check_in,
            "checkout": check_out,
            "adults": adults,
            "rooms": rooms,
            "currency": currency
        }
        
        if children:
            params["children"] = ",".join(map(str, children))
        
        # Convert params to URL query string
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        
        return f"{base_url}/{hotel_id}.html?{query_string}" 