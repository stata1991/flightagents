import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BookingComClient:
    """Client for Booking.com Rapid API integration"""
    
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
            logger.info(f"Making API request to: {url}")
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
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
                return {"error": f"API request failed: {e.response.status_code} - {e.response.text}"}
            return {"error": f"API request failed: {str(e)}"}
    
    def search_destination(self, query: str) -> Dict[str, Any]:
        """
        Search for airports and destinations using Booking.com API
        
        Args:
            query: Search query (city name, airport code, etc.)
            
        Returns:
            Dict containing destination data with airports and cities
        """
        endpoint = "/api/v1/flights/searchDestination"
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
                    "id": item.get("id"),
                    "type": item.get("type"),  # CITY or AIRPORT
                    "name": item.get("name"),
                    "code": item.get("code"),
                    "city": item.get("city"),
                    "cityName": item.get("cityName"),
                    "regionName": item.get("regionName"),
                    "country": item.get("country"),
                    "countryName": item.get("countryName"),
                    "distanceToCity": item.get("distanceToCity"),
                    "photoUri": item.get("photoUri")
                }
                destinations.append(destination)
        
        return {
            "status": result.get("status", False),
            "message": result.get("message", ""),
            "destinations": destinations
        }
    
    def search_flights(self, 
                      from_id: str,
                      to_id: str,
                      depart_date: str,
                      return_date: Optional[str] = None,
                      adults: int = 1,
                      children: str = "0,17",
                      cabin_class: str = "ECONOMY",
                      stops: str = "none",
                      page_no: int = 1,
                      sort: str = "BEST",
                      currency_code: str = "USD") -> Dict[str, Any]:
        """
        Search for flights using Booking.com API
        
        Args:
            from_id: Departure location ID (from destination search)
            to_id: Destination location ID (from destination search)
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (YYYY-MM-DD)
            adults: Number of adult passengers
            children: Children ages (comma-separated, e.g., "0,17")
            cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            stops: Stop preferences (none, one, two)
            page_no: Page number for pagination
            sort: Sort order (BEST, PRICE, DURATION)
            currency_code: Currency code (USD, EUR, AED, etc.)
        """
        endpoint = "/api/v1/flights/searchFlights"
        
        # Build parameters
        params = {
            "fromId": from_id,
            "toId": to_id,
            "departDate": depart_date,
            "stops": stops,
            "pageNo": page_no,
            "adults": adults,
            "children": children,
            "sort": sort,
            "cabinClass": cabin_class,
            "currency_code": currency_code
        }
        
        # Add return date for round trips
        if return_date:
            params["returnDate"] = return_date
        
        logger.info(f"Flight search requested: {from_id} to {to_id} on {depart_date}")
        result = self._make_request(endpoint, params)
        
        if "error" in result:
            return result
        
        # Return the full response for now, will be processed based on actual response structure
        return result
    
    def search_hotels(self,
                     location: str,
                     check_in: str,
                     check_out: str,
                     adults: int = 1,
                     rooms: int = 1) -> Dict[str, Any]:
        """
        Search for hotels using Booking.com API
        
        Args:
            location: Destination location
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adult guests
            rooms: Number of rooms
        """
        # This will be implemented once we have the specific endpoint details
        logger.info(f"Hotel search requested: {location} from {check_in} to {check_out}")
        return {"message": "Hotel search endpoint to be implemented with specific API details"}
    
    def search_activities(self,
                         location: str,
                         date: str,
                         participants: int = 1) -> Dict[str, Any]:
        """
        Search for activities using Booking.com API
        
        Args:
            location: Destination location
            date: Activity date (YYYY-MM-DD)
            participants: Number of participants
        """
        # This will be implemented once we have the specific endpoint details
        logger.info(f"Activity search requested: {location} on {date}")
        return {"message": "Activity search endpoint to be implemented with specific API details"}
    
    def search_restaurants(self,
                          location: str,
                          date: str,
                          guests: int = 2) -> Dict[str, Any]:
        """
        Search for restaurants using Booking.com API
        
        Args:
            location: Destination location
            date: Reservation date (YYYY-MM-DD)
            guests: Number of guests
        """
        # This will be implemented once we have the specific endpoint details
        logger.info(f"Restaurant search requested: {location} on {date}")
        return {"message": "Restaurant search endpoint to be implemented with specific API details"}

    def get_destination_id(self, query: str, destination_type: str = "AIRPORT") -> Optional[str]:
        """
        Get the first matching destination ID for a given query
        
        Args:
            query: Search query (city name, airport code, etc.)
            destination_type: Type of destination to prefer (AIRPORT, CITY)
            
        Returns:
            Destination ID if found, None otherwise
        """
        result = self.search_destination(query)
        
        if "error" in result or not result.get("destinations"):
            return None
        
        destinations = result["destinations"]
        
        # First try to find exact match by type
        for dest in destinations:
            if dest.get("type") == destination_type:
                return dest.get("id")
        
        # If no exact type match, return the first result
        if destinations:
            return destinations[0].get("id")
        
        return None
    
    def search_flights_by_location(self,
                                  from_location: str,
                                  to_location: str,
                                  depart_date: str,
                                  return_date: Optional[str] = None,
                                  adults: int = 1,
                                  children: str = "0,17",
                                  cabin_class: str = "ECONOMY",
                                  stops: str = "none",
                                  page_no: int = 1,
                                  sort: str = "BEST",
                                  currency_code: str = "USD") -> Dict[str, Any]:
        """
        Search for flights using location names (automatically converts to IDs)
        
        Args:
            from_location: Departure location name
            to_location: Destination location name
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (YYYY-MM-DD)
            adults: Number of adult passengers
            children: Children ages (comma-separated, e.g., "0,17")
            cabin_class: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            stops: Stop preferences (none, one, two)
            page_no: Page number for pagination
            sort: Sort order (BEST, PRICE, DURATION)
            currency_code: Currency code (USD, EUR, AED, etc.)
        """
        # Get destination IDs
        from_id = self.get_destination_id(from_location, "AIRPORT")
        to_id = self.get_destination_id(to_location, "AIRPORT")
        
        if not from_id:
            return {"error": f"Could not find departure location: {from_location}"}
        if not to_id:
            return {"error": f"Could not find destination location: {to_location}"}
        
        # Search flights using IDs
        return self.search_flights(
            from_id=from_id,
            to_id=to_id,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )

    def generate_booking_url(self,
                            from_location: str,
                            to_location: str,
                            depart_date: str,
                            return_date: Optional[str] = None,
                            adults: int = 1,
                            children: int = 0,
                            cabin_class: str = "ECONOMY") -> str:
        """
        Generate a deep link URL to Booking.com for flight search
        
        Args:
            from_location: Departure location (city name or airport code)
            to_location: Destination location (city name or airport code)
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (YYYY-MM-DD)
            adults: Number of adult passengers
            children: Number of children
            cabin_class: Cabin class (ECONOMY, BUSINESS, FIRST)
            
        Returns:
            Booking.com URL for flight search
        """
        # Base Booking.com flights URL
        base_url = "https://www.booking.com/flights"
        
        # Build query parameters
        params = []
        
        # Add locations
        params.append(f"from={from_location}")
        params.append(f"to={to_location}")
        
        # Add dates
        params.append(f"departure={depart_date}")
        if return_date:
            params.append(f"return={return_date}")
        
        # Add passengers
        params.append(f"adults={adults}")
        if children > 0:
            params.append(f"children={children}")
        
        # Add cabin class
        cabin_mapping = {
            "ECONOMY": "economy",
            "PREMIUM_ECONOMY": "premium_economy", 
            "BUSINESS": "business",
            "FIRST": "first"
        }
        cabin_param = cabin_mapping.get(cabin_class.upper(), "economy")
        params.append(f"cabin={cabin_param}")
        
        # Add trip type
        trip_type = "roundtrip" if return_date else "oneway"
        params.append(f"trip_type={trip_type}")
        
        # Construct final URL
        query_string = "&".join(params)
        booking_url = f"{base_url}?{query_string}"
        
        logger.info(f"Generated Booking.com URL: {booking_url}")
        return booking_url
    
    def get_flight_booking_info(self,
                               from_location: str,
                               to_location: str,
                               depart_date: str,
                               return_date: Optional[str] = None,
                               adults: int = 1,
                               children: int = 0,
                               cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """
        Get flight search results and generate booking URL
        
        Args:
            from_location: Departure location
            to_location: Destination location
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (YYYY-MM-DD)
            adults: Number of adult passengers
            children: Number of children
            cabin_class: Cabin class
            
        Returns:
            Dict containing flight results and booking URL
        """
        # Search for flights
        flight_results = self.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=f"0,{children}" if children > 0 else "0,17",
            cabin_class=cabin_class
        )
        
        # Generate booking URL
        booking_url = self.generate_booking_url(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class
        )
        
        return {
            "flight_results": flight_results,
            "booking_url": booking_url,
            "search_params": {
                "from_location": from_location,
                "to_location": to_location,
                "depart_date": depart_date,
                "return_date": return_date,
                "adults": adults,
                "children": children,
                "cabin_class": cabin_class
            }
        }
    
    def generate_booking_links(self,
                              from_id: str,
                              to_id: str,
                              depart_date: str,
                              return_date: Optional[str] = None,
                              adults: int = 1,
                              cabin_class: str = "ECONOMY") -> Dict[str, Any]:
        """
        Generate Booking.com deep link URLs for flight searches
        
        Args:
            from_id: Departure location ID
            to_id: Destination location ID
            depart_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trips (YYYY-MM-DD)
            adults: Number of adult passengers
            cabin_class: Cabin class
            
        Returns:
            Dict containing booking links and metadata
        """
        try:
            # Generate the main booking URL
            booking_url = self.generate_booking_url(
                from_location=from_id,
                to_location=to_id,
                depart_date=depart_date,
                return_date=return_date,
                adults=adults,
                cabin_class=cabin_class
            )
            
            return {
                "booking_url": booking_url,
                "search_params": {
                    "from_id": from_id,
                    "to_id": to_id,
                    "depart_date": depart_date,
                    "return_date": return_date,
                    "adults": adults,
                    "cabin_class": cabin_class
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating booking links: {e}")
            return {
                "error": f"Failed to generate booking links: {str(e)}",
                "booking_url": None
            }

# Global instance
booking_client = BookingComClient() 