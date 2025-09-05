import os
import aiohttp
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class FlightService:
    @staticmethod
    async def search_flights(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search flights using the context provided by the AI agent.
        This method matches the interface expected by ai_agents.py.
        """
        try:
            logger.info(f"Flight search called with context: {context}")
            
            origin = context.get("origin")
            destination = context.get("destination")
            start_date = context.get("start_date")
            return_date = context.get("return_date")
            travelers = context.get("travelers", 1)
            
            logger.info(f"Extracted parameters: origin={origin}, destination={destination}, start_date={start_date}, return_date={return_date}, travelers={travelers}")
            
            if not all([origin, destination, start_date, return_date]):
                logger.error(f"Missing required parameters: origin={origin}, destination={destination}, start_date={start_date}, return_date={return_date}")
                return {"success": False, "flights": [], "error": "Missing required parameters"}
            
            # Check if RAPID_API_KEY is available
            rapid_api_key = os.getenv("RAPID_API_KEY")
            if not rapid_api_key:
                logger.error("RAPID_API_KEY not found in environment variables")
                return {"success": False, "flights": [], "error": "RAPID_API_KEY not configured"}
            
            logger.info(f"RAPID_API_KEY found: {rapid_api_key[:10]}...")
            
            result = await FlightService.get_recommendations(origin, destination, start_date, return_date, travelers)
            logger.info(f"Flight search result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return {"success": False, "flights": [], "error": str(e)}

    @staticmethod
    async def get_recommendations(origin: str, destination: str, start_date: str, return_date: str, travelers: int = 1) -> Dict[str, Any]:
        """
        Fetches flight recommendations using Booking.com API with proper airport ID lookup.
        """
        try:
            # Step 1: Get airport IDs for origin and destination
            logger.info(f"Getting airport ID for origin: {origin}")
            origin_id = await FlightService._get_airport_id(origin)
            logger.info(f"Origin airport ID: {origin_id}")
            
            logger.info(f"Getting airport ID for destination: {destination}")
            destination_id = await FlightService._get_airport_id(destination, context={"destination": destination})
            logger.info(f"Destination airport ID: {destination_id}")
            
            # Debug: Check if we have valid airport IDs
            if not origin_id:
                logger.error(f"Could not find airport ID for origin: {origin}")
                return {"success": False, "flights": [], "error": f"Airport not found for origin: {origin}"}
            
            if not destination_id:
                logger.error(f"Could not find airport ID for destination: {destination}")
                return {"success": False, "flights": [], "error": f"Airport not found for destination: {destination}"}
            
            if not origin_id or not destination_id:
                logger.error(f"Could not find airport IDs for {origin} or {destination}")
                return {"success": False, "flights": [], "error": "Airport not found"}
            
            # Step 2: Search flights with airport IDs
            return await FlightService._search_flights(origin_id, destination_id, start_date, return_date, travelers)
            
        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return {"success": False, "flights": [], "error": str(e)}

    @staticmethod
    def _get_airport_code_direct(city_name: str) -> Optional[str]:
        """Dynamic airport code lookup using the airports database"""
        try:
            import json
            import os
            
            # Load airports database dynamically
            airports_file = os.path.join(os.path.dirname(__file__), '..', 'api', 'airports-code.json')
            if not os.path.exists(airports_file):
                return None
                
            with open(airports_file, 'r', encoding='utf-8') as f:
                airports_data = json.load(f)
            
            # Normalize city name for matching
            normalized_city = city_name.lower().strip()
            
            # Search for matching airports
            for airport in airports_data:
                airport_city = airport.get('city_name', '').lower()
                airport_name = airport.get('airport_name', '').lower()
                airport_code = airport.get('column_1', '')  # CRS code
                
                # Exact city match
                if normalized_city == airport_city:
                    return airport_code
                
                # Partial city match
                if normalized_city in airport_city or airport_city in normalized_city:
                    return airport_code
                
                # Airport name match
                if normalized_city in airport_name or airport_name in normalized_city:
                    return airport_code
            
            return None
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in dynamic airport lookup: {e}")
            return None

    async def _get_airport_id(location: str, context: dict = None) -> Optional[str]:
        """
        Get airport ID using Booking.com searchDestination API, robustly selecting the correct airport.
        - If user specifies country, use it for filtering (highest precedence).
        - Otherwise, use geocoding to infer country.
        - Filter by country, then by city/region, then prefer major airports.
        """
        try:
            import logging
            logger = logging.getLogger(__name__)
            # from services.location_detection_service import location_detection_service
            import os
            import aiohttp
            rapid_api_key = os.getenv("RAPID_API_KEY")
            if not rapid_api_key:
                logger.error("RAPID_API_KEY not found")
                return None
            url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination"
            headers = {
                "X-RapidAPI-Key": rapid_api_key,
                "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
            }
            params = {"query": location}
            logger.info(f"[AIRPORT] Searching for airports for '{location}' with params: {params}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"[AIRPORT] Raw search result: {result}")
                        airports = result.get("data", [])
                        if not airports:
                            logger.warning(f"[AIRPORT] No airports found for {location}")
                            return None
                        # Step 1: Determine country to use for filtering
                        user_country = None
                        if context and context.get("country"):
                            user_country = context["country"].strip().lower()
                            logger.info(f"[AIRPORT] Using user-specified country: {user_country}")
                        else:
                            # Use default country (US) for now
                            user_country = "us"
                            if user_country:
                                user_country = user_country.strip().lower()
                                logger.info(f"[AIRPORT] Geocoded country: {user_country}")
                        # Step 2: Filter by country
                        filtered = []
                        for a in airports:
                            cands = [a.get("country", ""), a.get("countryName", ""), a.get("countryNameShort", "")]
                            if any(user_country and user_country in (c or c.lower()) for c in cands):
                                filtered.append(a)
                        logger.info(f"[AIRPORT] {len(filtered)} airports after country filter ({user_country})")
                        if not filtered:
                            logger.warning(f"[AIRPORT] No airports matched country '{user_country}', using all results")
                            filtered = airports
                        # Step 3: Further filter by city/region
                        city_match = location.strip().lower()
                        city_filtered = [a for a in filtered if any(city_match in (a.get(k, "").lower()) for k in ["regionName", "cityName", "name"])]
                        logger.info(f"[AIRPORT] {len(city_filtered)} airports after city/region filter ('{city_match}')")
                        if city_filtered:
                            filtered = city_filtered
                        # Step 4: Prefer type=='AIRPORT', then shortest distanceToCity
                        airport_only = [a for a in filtered if a.get("type") == "AIRPORT"]
                        if airport_only:
                            filtered = airport_only
                        # Step 5: Pick closest by distanceToCity if available
                        def get_distance(a):
                            d = a.get("distanceToCity", {}).get("value")
                            return float(d) if d is not None else float('inf')
                        filtered = sorted(filtered, key=get_distance)
                        selected = filtered[0]
                        logger.info(f"[AIRPORT] Selected airport: {selected.get('name')} (ID: {selected.get('id')}) [country={selected.get('country')}, city={selected.get('cityName')}, region={selected.get('regionName')}, distance={get_distance(selected)}]")
                        return selected.get("id")
                    else:
                        logger.error(f"[AIRPORT] Search destination failed for {location}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"[AIRPORT] Error getting airport ID for {location}: {e}")
            # Fallback to dynamic airport lookup
            logger.info(f"[AIRPORT] Trying dynamic airport lookup for {location}")
            airport_code = FlightService._get_airport_code_direct(location)
            if airport_code:
                logger.info(f"[AIRPORT] Found airport code via dynamic lookup: {airport_code}")
                return airport_code
            return None

    @staticmethod
    async def _search_flights(origin_id: str, destination_id: str, start_date: str, return_date: str, travelers: int) -> Dict[str, Any]:
        """
        Search flights using Booking.com searchFlights API.
        """
        try:
            rapid_api_key = os.getenv("RAPID_API_KEY")
            if not rapid_api_key:
                logger.error("RAPID_API_KEY not found")
                return {"success": False, "flights": []}
            
            url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights"
            
            headers = {
                "X-RapidAPI-Key": rapid_api_key,
                "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
            }
            
            params = {
                "fromId": origin_id,
                "toId": destination_id,
                "departDate": start_date,
                "returnDate": return_date,
                "stops": "none",  # Fixed: use "none" instead of "0,1,2"
                "pageNo": "1",
                "adults": str(travelers),
                "children": "0",
                "sort": "CHEAPEST",  # Fixed: use "CHEAPEST" instead of "PRICE"
                "cabinClass": "ECONOMY",
                "currency_code": "USD"
            }
            
            logger.info(f"Searching flights with params: {params}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Flight search result: {result}")
                        
                        logger.info(f"API Response status: {result.get('status')}")
                        logger.info(f"API Response data keys: {result.get('data', {}).keys()}")
                        logger.info(f"Flight offers count: {len(result.get('data', {}).get('flightOffers', []))}")
                        
                        if result.get("status") and result.get("data", {}).get("flightOffers"):
                            flights = []
                            logger.info(f"Processing {len(result['data']['flightOffers'])} flight offers")
                            for i, offer in enumerate(result["data"]["flightOffers"]):
                                logger.info(f"Processing offer {i+1}: {offer.get('token', 'no-token')[:20]}...")
                                logger.info(f"Offer structure: segments={len(offer.get('segments', []))}, priceBreakdown={bool(offer.get('priceBreakdown'))}")
                                flight = FlightService._parse_flight_offer(offer)
                                if flight:
                                    flights.append(flight)
                                    logger.info(f"Successfully parsed flight: {flight.get('airline')} {flight.get('flight_number')}")
                                else:
                                    logger.error(f"Failed to parse flight offer {i+1}")
                                    logger.error(f"Offer data: {offer}")
                            
                            return {
                                "success": True,
                                "flights": flights,
                                "categorized_flights": FlightService._categorize_flights(flights)
                            }
                        else:
                            logger.error(f"No flightOffers found in response. Response keys: {result.get('data', {}).keys()}")
                            logger.error(f"Full response structure: {result}")
                            return {"success": False, "flights": []}
                    else:
                        error_text = await response.text()
                        logger.error(f"Flight search API error: {error_text}")
                        return {"success": False, "flights": []}
                        
        except Exception as e:
            logger.error(f"Error searching flights: {e}")
            return {"success": False, "flights": []}

    @staticmethod
    def _parse_flight_offer(offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a flight offer from the API response.
        """
        try:
            logger.info(f"Parsing flight offer with keys: {offer.keys()}")
            if not offer.get("segments"):
                logger.error("No segments found in offer")
                return None
            
            # Get the first segment (outbound flight)
            segment = offer["segments"][0]
            logger.info(f"Segment keys: {segment.keys()}")
            leg = segment["legs"][0]
            logger.info(f"Leg keys: {leg.keys()}")
            
            # Get airline info
            carrier = leg.get("carriersData", [{}])[0]
            airline = carrier.get("name", "Unknown")
            flight_number = f"{carrier.get('code', '')} {leg.get('flightInfo', {}).get('flightNumber', '')}"
            
            # Get times from segment level
            departure_time = segment.get("departureTime", "")
            arrival_time = segment.get("arrivalTime", "")
            
            # Format times if they exist
            if departure_time:
                try:
                    # Parse ISO datetime and format as HH:MM
                    from datetime import datetime
                    dt = datetime.fromisoformat(departure_time.replace('Z', '+00:00'))
                    departure_time = dt.strftime("%H:%M")
                except:
                    departure_time = departure_time[:5] if len(departure_time) >= 5 else departure_time
            
            if arrival_time:
                try:
                    # Parse ISO datetime and format as HH:MM
                    from datetime import datetime
                    dt = datetime.fromisoformat(arrival_time.replace('Z', '+00:00'))
                    arrival_time = dt.strftime("%H:%M")
                except:
                    arrival_time = arrival_time[:5] if len(arrival_time) >= 5 else arrival_time
            
            # Get duration and format it
            duration_seconds = segment.get("totalTime", 0)
            if duration_seconds:
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                duration = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            else:
                duration = "N/A"
            
            # Get price
            price_breakdown = offer.get("priceBreakdown", {})
            total_price = price_breakdown.get("total", {})
            price_units = total_price.get("units", 0)
            
            # Get booking link
            booking_link = offer.get("token", "")
            
            return {
                "airline": airline,
                "flight_number": flight_number,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": duration,
                "price": {
                    "currencyCode": "USD",
                    "units": price_units,
                    "nanos": 0
                },
                "stops": len(offer.get("segments", [])) - 1,
                "booking_link": booking_link
            }
            
        except Exception as e:
            logger.error(f"Error parsing flight offer: {e}")
            return None

    @staticmethod
    def _categorize_flights(flights: list) -> Dict[str, list]:
        """
        Categorize flights into fastest, cheapest, and optimal.
        """
        logger.info(f"Categorizing {len(flights)} flights")
        if not flights:
            logger.warning("No flights to categorize")
            return {"fastest": [], "cheapest": [], "optimal": []}
        
        # Helper function to convert duration string to minutes
        def duration_to_minutes(duration_str):
            if not duration_str or duration_str == "N/A":
                return float('inf')
            try:
                # Parse "1h 30m" format
                parts = duration_str.split()
                hours = 0
                minutes = 0
                for i, part in enumerate(parts):
                    if 'h' in part:
                        hours = int(part.replace('h', ''))
                    elif 'm' in part:
                        minutes = int(part.replace('m', ''))
                return hours * 60 + minutes
            except Exception as e:
                logger.error(f"Error parsing duration '{duration_str}': {e}")
                return float('inf')
        
        # Sort by duration for fastest
        fastest = sorted(flights, key=lambda x: duration_to_minutes(x.get('duration', '')))[:5]
        logger.info(f"Fastest flights: {len(fastest)}")
        
        # Sort by price for cheapest - filter out zero prices first
        valid_priced_flights = [f for f in flights if f.get('price', {}).get('units', 0) > 0]
        cheapest = sorted(valid_priced_flights, key=lambda x: x.get('price', {}).get('units', float('inf')))[:5]
        logger.info(f"Cheapest flights: {len(cheapest)}")
        
        # Sort by combination of price and duration for optimal
        optimal = sorted(valid_priced_flights, key=lambda x: (x.get('price', {}).get('units', 0) + duration_to_minutes(x.get('duration', '')) / 60))[:5]
        logger.info(f"Optimal flights: {len(optimal)}")
        
        result = {
            "fastest": fastest,
            "cheapest": cheapest,
            "optimal": optimal
        }
        
        logger.info(f"Categorization result: fastest={len(result['fastest'])}, cheapest={len(result['cheapest'])}, optimal={len(result['optimal'])}")
        return result
