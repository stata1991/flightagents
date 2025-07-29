from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from .search_one_way import search_one_way_flights
from .search_round_trip import search_round_trip_flights
from .booking_client import booking_client
from pydantic import BaseModel
import os
import logging
from datetime import datetime, timedelta
import aiohttp
import json

# Configure logging
logger = logging.getLogger(__name__)

class SearchQuery(BaseModel):
    """Model for flight search parameters."""
    origin: str
    destination: str
    date: str  # Departure date
    return_date: Optional[str] = None  # Add return_date for round-trip
    query: Optional[str] = None  # Make query optional

router = APIRouter()

@router.post("/api/search")
async def search_flights(query: SearchQuery) -> Dict[str, Any]:
    """
    Search for flights using the provided parameters.
    """
    try:
        # Get RapidAPI key from environment
        api_key = os.getenv("RAPID_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="RapidAPI key not configured")
        
        logger.info(f"Using RapidAPI key: {api_key[:10]}...")  # Log first 10 chars for debugging
        
        # Parse and validate the date
        try:
            search_date = datetime.strptime(query.date, "%Y-%m-%d")
            today = datetime.now()
            
            # If date is in the past, use next week's date
            if search_date < today:
                search_date = today + timedelta(days=7)  # Next week
                logger.info(f"Date {query.date} is in the past, using next week's date: {search_date.strftime('%Y-%m-%d')}")
            
            # Format date for API
            formatted_date = search_date.strftime("%Y-%m-%d")
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Parse and validate the return date if present
        formatted_return_date = None
        if hasattr(query, 'return_date') and query.return_date:
            try:
                return_date = datetime.strptime(query.return_date, "%Y-%m-%d")
                if return_date < today:
                    return_date = today + timedelta(days=14)  # Two weeks from now
                    logger.info(f"Return date {query.return_date} is in the past, using two weeks from now: {return_date.strftime('%Y-%m-%d')}")
                formatted_return_date = return_date.strftime("%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid return date format. Use YYYY-MM-DD")
        
        # Use Booking.com RapidAPI for flight search
        headers = {
            "X-RapidAPI-Key": api_key.strip(),
            "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
        }
        
        # First, we need to get the airport IDs for origin and destination
        # For now, let's use the airport codes directly as IDs (this is a simplification)
        # In a real implementation, you'd want to search for airports first
        
        # Construct query parameters for flight search
        params = {
            "fromId": f"{query.origin}.AIRPORT",  # Assuming airport code format
            "toId": f"{query.destination}.AIRPORT",  # Assuming airport code format
            "departDate": formatted_date,
            "stops": "none",
            "pageNo": "1",
            "adults": "1",
            "children": "0,17",
            "sort": "BEST",
            "cabinClass": "ECONOMY",
            "currency_code": "USD"
        }
        if formatted_return_date:
            params["returnDate"] = formatted_return_date
        
        logger.info(f"Searching for flights with parameters: {json.dumps(params, indent=2)}")
        logger.info(f"Request headers: {json.dumps({k: v[:10] + '...' if k == 'X-RapidAPI-Key' else v for k, v in headers.items()}, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://booking-com15.p.rapidapi.com/api/v1/flights/searchFlights",
                headers=headers,
                params=params
            ) as response:
                logger.info(f"Response status: {response.status}")
                logger.info(f"Response URL: {response.url}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Booking.com API flight search error: {error_text}")
                    logger.error(f"Request URL: {response.url}")
                    logger.error(f"Request headers: {json.dumps({k: v[:10] + '...' if k == 'X-RapidAPI-Key' else v for k, v in headers.items()}, indent=2)}")
                    logger.error(f"Request params: {json.dumps(params, indent=2)}")
                    raise HTTPException(status_code=500, detail=f"Error searching for flights: {error_text}")
                
                result = await response.json()
                logger.info(f"Booking.com API flight search response: {json.dumps(result, indent=2)}")
                
                # Extract flights from the response
                flights = []
                categorized_flights = {
                    "fastest": [],
                    "cheapest": [],
                    "optimal": []
                }
                
                if "data" in result and "flightOffers" in result["data"]:
                    # Extract all flights for fallback categorization
                    for flight_offer in result["data"]["flightOffers"]:
                        # Get the first segment for flight details
                        if "segments" in flight_offer and len(flight_offer["segments"]) > 0:
                            segment = flight_offer["segments"][0]
                            
                            # Get airline info from legs
                            airline_name = "Unknown"
                            flight_number = "Unknown"
                            if "legs" in segment and len(segment["legs"]) > 0:
                                leg = segment["legs"][0]
                                # Get airline info from carriersData
                                if "carriersData" in leg and len(leg["carriersData"]) > 0:
                                    carrier = leg["carriersData"][0]
                                    airline_name = carrier.get("name", "Unknown")
                                    flight_number = f"{carrier.get('code', 'Unknown')} {leg.get('flightNumber', '')}"
                                else:
                                    # Fallback to marketingCarrier if carriersData is not available
                                    airline_name = leg.get("marketingCarrier", {}).get("name", "Unknown")
                                    flight_number = f"{leg.get('marketingCarrier', {}).get('code', 'Unknown')} {leg.get('marketingCarrier', {}).get('flightNumber', '')}"
                            
                            # Get price from priceBreakdown
                            price = 0
                            if "priceBreakdown" in flight_offer:
                                price = flight_offer["priceBreakdown"].get("total", 0)
                            
                            flight_info = {
                                "airline": airline_name,
                                "flight_number": flight_number,
                                "departure_time": segment.get("departureTime", ""),
                                "arrival_time": segment.get("arrivalTime", ""),
                                "duration": segment.get("totalTime", ""),
                                "price": price,
                                "stops": len(segment.get("legs", [])) - 1,
                                "booking_link": flight_offer.get("token", "")  # Use token as booking link
                            }
                            flights.append(flight_info)
                
                # Extract categorized deals from flightDeals if available
                if "data" in result and "flightDeals" in result["data"]:
                    logger.info("Found flightDeals, using categorized deals")
                    for deal in result["data"]["flightDeals"]:
                        deal_key = deal.get("key", "").lower()
                        if deal_key in ["cheapest", "fastest", "best"]:
                            # Map "best" to "optimal" for our structure
                            category = "optimal" if deal_key == "best" else deal_key
                            
                            # Find the corresponding flight offer using the offerToken
                            offer_token = deal.get("offerToken", "")
                            corresponding_flight = None
                            
                            # Find the flight that matches this deal
                            for flight in flights:
                                if flight.get("booking_link") == offer_token:
                                    corresponding_flight = flight
                                    break
                            
                            if corresponding_flight:
                                categorized_flights[category].append(corresponding_flight)
                                logger.info(f"Added {deal_key} flight: {corresponding_flight['airline']}")
                
                # If no categorized deals found, use manual categorization
                if not any(categorized_flights.values()):
                    logger.info("No categorized deals found, using manual categorization")
                    if flights:
                        # Sort by duration for fastest
                        fastest_flights = sorted(flights, key=lambda x: x.get('duration', 0))[:3]
                        # Sort by price for cheapest
                        cheapest_flights = sorted(flights, key=lambda x: x.get('price', {}).get('units', 0) if isinstance(x.get('price'), dict) else x.get('price', 0))[:3]
                        # Sort by combination of price and duration for optimal
                        optimal_flights = sorted(flights, key=lambda x: (x.get('price', {}).get('units', 0) if isinstance(x.get('price'), dict) else x.get('price', 0) + x.get('duration', 0)))[:3]
                        
                        categorized_flights["fastest"] = fastest_flights
                        categorized_flights["cheapest"] = cheapest_flights
                        categorized_flights["optimal"] = optimal_flights
                
                logger.info(f"Found {len(flights)} total flights")
                logger.info(f"Categorized: {len(categorized_flights['fastest'])} fastest, {len(categorized_flights['cheapest'])} cheapest, {len(categorized_flights['optimal'])} optimal")
                
                if not flights:
                    logger.error("No flights found in API response")
                    logger.error(f"Full API response: {json.dumps(result, indent=2)}")
                    raise HTTPException(status_code=500, detail="No flights found in API response")
                
                return {
                    "success": True,
                    "flights": flights,
                    "categorized_flights": categorized_flights,
                    "message": "Flight search completed"
                }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Flight search failed: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "flights": [],
            "error": str(e)
        }

@router.get("/flights/search")
async def search_flights_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Simple flight search endpoint using location names
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
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
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/search-destination")
async def search_destination(query: str = Query(..., description="Search query for destination/airport")):
    """
    Search for destinations and airports using Booking.com API
    """
    try:
        # Get RapidAPI key from environment
        api_key = os.getenv("RAPID_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="RapidAPI key not configured")
        
        logger.info(f"Searching for destination: {query}")
        
        # Use Booking.com RapidAPI for destination search
        headers = {
            "X-RapidAPI-Key": api_key.strip(),
            "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
        }
        
        # Construct query parameters for destination search
        params = {
            "query": query
        }
        
        logger.info(f"Searching for destinations with parameters: {json.dumps(params, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination",
                headers=headers,
                params=params
            ) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Booking.com API destination search error: {error_text}")
                    raise HTTPException(status_code=500, detail=f"Error searching for destinations: {error_text}")
                
                result = await response.json()
                logger.info(f"Booking.com API destination search response: {json.dumps(result, indent=2)}")
                
                # Extract destinations from the response
                destinations = []
                if "data" in result:
                    for destination in result["data"]:
                        dest_info = {
                            "id": destination.get("id", ""),
                            "type": destination.get("type", ""),
                            "name": destination.get("name", ""),
                            "code": destination.get("code", ""),
                            "city": destination.get("city", ""),
                            "cityName": destination.get("cityName", ""),
                            "regionName": destination.get("regionName", ""),
                            "country": destination.get("country", ""),
                            "countryName": destination.get("countryName", ""),
                            "photoUri": destination.get("photoUri", "")
                        }
                        destinations.append(dest_info)
                
                logger.info(f"Found {len(destinations)} destinations in response")
                
                return {
                    "success": True,
                    "destinations": destinations,
                    "message": "Destination search completed"
                }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Destination search failed: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "destinations": [],
            "error": str(e)
        }

@router.get("/search-one-way")
async def search_one_way(
    from_id: str = Query(..., description="Departure location ID (from destination search)"),
    to_id: str = Query(..., description="Destination location ID (from destination search)"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for one-way flights using Booking.com API (with location IDs)
    """
    try:
        result = booking_client.search_flights(
            from_id=from_id,
            to_id=to_id,
            depart_date=depart_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-round-trip")
async def search_round_trip(
    from_id: str = Query(..., description="Departure location ID (from destination search)"),
    to_id: str = Query(..., description="Destination location ID (from destination search)"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Return date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for round-trip flights using Booking.com API (with location IDs)
    """
    try:
        result = booking_client.search_flights(
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
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-one-way-simple")
async def search_one_way_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for one-way flights using location names (automatically converts to IDs)
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-round-trip-simple")
async def search_round_trip_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Return date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for round-trip flights using location names (automatically converts to IDs)
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
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
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-with-booking-url")
async def search_with_booking_url(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: int = Query(0, description="Number of children"),
    cabin_class: str = Query("ECONOMY", description="Cabin class")
):
    """
    Search for flights and generate Booking.com deep link URL
    """
    try:
        result = booking_client.get_flight_booking_info(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class
        )
        
        if "error" in result.get("flight_results", {}):
            raise HTTPException(status_code=500, detail=result["flight_results"]["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-booking-url")
async def generate_booking_url(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: int = Query(0, description="Number of children"),
    cabin_class: str = Query("ECONOMY", description="Cabin class")
):
    """
    Generate only the Booking.com deep link URL without searching flights
    """
    try:
        booking_url = booking_client.generate_booking_url(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class
        )
        
        return {
            "success": True,
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))