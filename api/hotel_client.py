import requests
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import logging
from .models import HotelSearchRequest, HotelSearchResponse, HotelInfo, HotelRoom, HotelSearchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HotelClient:
    """Enhanced Client for Booking.com Hotel Rapid API integration with smart budget handling"""
    
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
        Step 1: Search for destinations to get multiple destination IDs
        
        Args:
            query: Search query (city name, etc.)
            
        Returns:
            Dict containing all destination options with dest_ids
        """
        endpoint = "/api/v1/hotels/searchDestination"
        params = {"query": query}
        
        logger.info(f"Destination search requested for: {query}")
        result = self._make_request(endpoint, params)
        
        if "error" in result:
            return result
        
        # Extract and format all destination options
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

    def get_filters(self, dest_id: str, search_type: str, check_in: str, check_out: str,
                   adults: int = 1, children: List[int] = None, rooms: int = 1) -> Dict[str, Any]:
        """
        Step 2: Get filters and price ranges for a specific destination
        
        Args:
            dest_id: Destination ID from step 1
            search_type: Search type (CITY, DISTRICT, etc.)
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Ages of children
            rooms: Number of rooms
            
        Returns:
            Dict containing filters, price ranges, and availability info
        """
        endpoint = "/api/v1/hotels/getFilter"
        
        params = {
            "dest_id": dest_id,
            "search_type": search_type.upper(),
            "arrival_date": check_in,
            "departure_date": check_out,
            "adults": adults,
            "children_age": ",".join(map(str, children)) if children else "0,17",
            "room_qty": rooms
        }
        
        logger.info(f"Getting filters for dest_id: {dest_id}")
        result = self._make_request(endpoint, params)
        
        if "error" in result:
            return result
        
        return result

    def search_hotels_with_filters(self, dest_id: str, search_type: str, check_in: str, check_out: str,
                                 adults: int = 1, children: List[int] = None, rooms: int = 1,
                                 currency: str = "USD", page_number: int = 1,
                                 filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Step 3: Search hotels with optional filters
        
        Args:
            dest_id: Destination ID
            search_type: Search type
            check_in: Check-in date
            check_out: Check-out date
            adults: Number of adults
            children: Ages of children
            rooms: Number of rooms
            currency: Currency code
            page_number: Page number for pagination
            filters: Optional filters to apply
            
        Returns:
            Dict containing hotel search results
        """
        endpoint = "/api/v1/hotels/searchHotels"
        
        params = {
            "dest_id": dest_id,
            "search_type": search_type.upper(),
            "arrival_date": check_in,
            "departure_date": check_out,
            "adults": adults,
            "children_age": ",".join(map(str, children)) if children else "0,17",
            "room_qty": rooms,
            "page_number": page_number,
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": "en-us",
            "currency_code": currency,
            "location": "US"
        }
        
        # Add filters if provided
        if filters:
            params.update(filters)
        
        logger.info(f"Searching hotels for dest_id: {dest_id} with filters: {filters}")
        result = self._make_request(endpoint, params)
        
        if "error" in result:
            return result
        
        return result

    def smart_hotel_search(self, request: HotelSearchRequest, 
                          max_budget: Optional[float] = None,
                          budget_expansion_steps: int = 3) -> HotelSearchResponse:
        """
        Smart hotel search with budget handling and destination fallback
        
        Args:
            request: Hotel search request
            max_budget: Maximum budget per night (optional)
            budget_expansion_steps: Number of budget expansion steps to try
            
        Returns:
            HotelSearchResponse with best available hotels
        """
        logger.info(f"Starting smart hotel search for: {request.location}")
        
        # Step 1: Get all destination options
        dest_search = self.search_destination(request.location)
        if "error" in dest_search or not dest_search.get("destinations"):
            error_msg = dest_search.get("error", "Destination not found")
            logger.error(f"Smart search error: {error_msg}")
            return HotelSearchResponse(
                location=request.location,
                check_in=request.check_in,
                check_out=request.check_out,
                total_results=0,
                hotels=[],
                search_metadata={"error": error_msg}
            )
        
        destinations = dest_search["destinations"]
        logger.info(f"Found {len(destinations)} destination options")
        
        # Step 2: Try each destination with budget expansion
        all_hotels = []
        search_attempts = []
        
        for dest in destinations:
            dest_id = dest["dest_id"]
            search_type = dest["search_type"]
            
            logger.info(f"Trying destination: {dest['label']} (ID: {dest_id})")
            
            # Get filters for this destination
            filters_result = self.get_filters(
                dest_id, search_type, request.check_in, request.check_out,
                request.adults, request.children, request.rooms
            )
            
            if "error" in filters_result:
                logger.warning(f"Could not get filters for {dest['label']}: {filters_result['error']}")
                continue
            
            # Extract price range from filters
            price_range = self._extract_price_range(filters_result)
            if not price_range:
                logger.warning(f"No price range found for {dest['label']}")
                continue
            
            logger.info(f"Price range for {dest['label']}: ${price_range['min']} - ${price_range['max']}")
            
            # Try different budget levels
            budget_levels = self._calculate_budget_levels(
                price_range, max_budget, budget_expansion_steps
            )
            
            for budget_level in budget_levels:
                logger.info(f"Trying budget level: ${budget_level}")
                
                # Apply price filter
                filters = {"price": f"0-{int(budget_level)}"}
                
                # Search hotels with this budget
                search_result = self.search_hotels_with_filters(
                    dest_id, search_type, request.check_in, request.check_out,
                    request.adults, request.children, request.rooms,
                    request.currency, 1, filters
                )
                
                search_attempts.append({
                    "destination": dest,
                    "budget": budget_level,
                    "result": search_result
                })
                
                if "error" in search_result:
                    logger.warning(f"Search failed for {dest['label']} with budget ${budget_level}")
                    continue
                
                # Parse hotels from this search
                hotels = self._parse_hotels_from_search(search_result, request)
                if hotels:
                    logger.info(f"Found {len(hotels)} hotels in {dest['label']} with budget ${budget_level}")
                    all_hotels.extend(hotels)
                    
                    # If we found enough hotels, we can stop expanding budget
                    if len(all_hotels) >= 10:
                        break
                
                # If we found hotels, try relaxing other filters
                if not hotels and budget_level > price_range['min']:
                    relaxed_hotels = self._try_relaxed_filters(
                        dest_id, search_type, request, budget_level
                    )
                    if relaxed_hotels:
                        all_hotels.extend(relaxed_hotels)
                        logger.info(f"Found {len(relaxed_hotels)} hotels with relaxed filters")
            
            # If we found enough hotels, we can stop trying other destinations
            if len(all_hotels) >= 15:
                break
        
        # Sort hotels by price and quality
        all_hotels = self._sort_hotels_by_value(all_hotels)
        
        # Take the best hotels
        best_hotels = all_hotels[:10]
        
        logger.info(f"Smart search completed. Found {len(best_hotels)} hotels from {len(search_attempts)} attempts")
        
        return HotelSearchResponse(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            total_results=len(best_hotels),
            hotels=best_hotels,
            search_metadata={
                "search_attempts": len(search_attempts),
                "destinations_tried": len(destinations),
                "smart_search": True
            }
        )

    def _extract_price_range(self, filters_result: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Extract price range from filters result"""
        if not filters_result.get("data", {}).get("filters"):
            return None
        
        for filter_item in filters_result["data"]["filters"]:
            if filter_item.get("field") == "price":
                return {
                    "min": float(filter_item.get("min", 0)),
                    "max": float(filter_item.get("max", 0)),
                    "currency": filter_item.get("currency", "USD")
                }
        
        return None

    def _calculate_budget_levels(self, price_range: Dict[str, float], 
                                max_budget: Optional[float], 
                                steps: int) -> List[float]:
        """Calculate budget levels to try"""
        min_price = price_range["min"]
        max_price = price_range["max"]
        
        if max_budget:
            max_price = min(max_price, max_budget)
        
        # Start with minimum price, then expand
        budget_levels = [min_price]
        
        if steps > 1:
            step_size = (max_price - min_price) / (steps - 1)
            for i in range(1, steps):
                level = min_price + (step_size * i)
                budget_levels.append(level)
        
        return budget_levels

    def _try_relaxed_filters(self, dest_id: str, search_type: str, 
                           request: HotelSearchRequest, budget: float) -> List[HotelSearchResult]:
        """Try searching with relaxed filters (lower star ratings, etc.)"""
        # Try with lower star ratings
        relaxed_filters = {
            "price": f"0-{int(budget)}",
            "class": "class::3,class::4,class::5"  # 3+ stars instead of 4+
        }
        
        search_result = self.search_hotels_with_filters(
            dest_id, search_type, request.check_in, request.check_out,
            request.adults, request.children, request.rooms,
            request.currency, 1, relaxed_filters
        )
        
        if "error" not in search_result:
            return self._parse_hotels_from_search(search_result, request)
        
        return []

    def _parse_hotels_from_search(self, search_result: Dict[str, Any], 
                                 request: HotelSearchRequest) -> List[HotelSearchResult]:
        """Parse hotels from search result"""
        hotels = []
        
        if not search_result.get("status") or not search_result.get("data"):
            return hotels
        
        data = search_result["data"]
        hotel_list = data.get("hotels", [])
        
        for hotel_data in hotel_list:
            try:
                hotel_info = self._parse_hotel_info(hotel_data)
                rooms = self._parse_hotel_rooms(hotel_data.get("property", {}))
                
                # Calculate average price
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
            except Exception as e:
                logger.warning(f"Error parsing hotel: {e}")
                continue
        
        return hotels

    def _sort_hotels_by_value(self, hotels: List[HotelSearchResult]) -> List[HotelSearchResult]:
        """Sort hotels by value (combination of price and quality)"""
        def value_score(hotel):
            price = hotel.average_price_per_night or float('inf')
            rating = hotel.hotel.rating or 0
            
            if price == float('inf'):
                return float('inf')
            
            # Value score: lower price and higher rating is better
            # Weight: 70% price, 30% rating
            return (price * 0.7) - (rating * 0.3)
        
        return sorted(hotels, key=value_score)

    # Keep existing methods for backward compatibility
    def search_hotels(self, request: HotelSearchRequest) -> HotelSearchResponse:
        """Legacy method - now uses smart search"""
        return self.smart_hotel_search(request)

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
        
        return self.smart_hotel_search(request)
    
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