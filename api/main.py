from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from .search_one_way import search_one_way_flights
from .search_round_trip import search_round_trip_flights
from .enhanced_parser import get_parser, EnhancedQueryParser
from itertools import product
import os
from dotenv import load_dotenv
import aiohttp
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize parser with X API key
api_key = os.getenv("X_API_KEY")
if not api_key:
    raise ValueError("X API key not configured")
enhanced_parser = get_parser(api_key)

class SearchRequest(BaseModel):
    trip_type: str
    origin: str
    destination: str
    date_range: Dict[str, List[str]]
    flex_days: Optional[int] = 0
    filters: Optional[Dict[str, Any]] = {
        "non_stop_only": False,
        "max_price": None,
        "preferred_airlines": [],
        "max_stops": None
    }

class SearchQuery(BaseModel):
    """Model for flight search parameters."""
    origin: str
    destination: str
    date: str  # Departure date
    return_date: Optional[str] = None  # Add return_date for round-trip
    query: Optional[str] = None  # Make query optional

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/search")
async def search_flights(query: SearchQuery) -> Dict[str, Any]:
    """
    Search for flights using the provided parameters.
    """
    try:
        # Get Skyscanner API key from environment
        api_key = os.getenv("SKYSCANNER_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Skyscanner API key not configured")
        
        logger.info(f"Using Skyscanner API key: {api_key[:10]}...")  # Log first 10 chars for debugging
        
        # Call Skyscanner API to search for flights
        headers = {
            "Accept": "application/json",
            "x-apihub-key": api_key.strip(),
            "x-apihub-host": "Skyscanner.allthingsdev.co",
            "x-apihub-endpoint": "0e8a330d-269e-42cc-a1a8-fde0445ee552"
        }
        
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
        
        # Construct query parameters
        params = {
            "adults": 1,
            "origin": query.origin,
            "destination": query.destination,
            "departureDate": formatted_date,
            "cabinClass": "economy",
            "currency": "USD",
            "market": "US",
            "locale": "en-US"
        }
        if formatted_return_date:
            params["returnDate"] = formatted_return_date
        
        logger.info(f"Searching for flights with parameters: {json.dumps(params, indent=2)}")
        logger.info(f"Request headers: {json.dumps({k: v[:10] + '...' if k == 'x-apihub-key' else v for k, v in headers.items()}, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://Skyscanner.proxy-production.allthingsdev.co/search",
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Skyscanner API error: {error_text}")
                    logger.error(f"Request URL: {response.url}")
                    logger.error(f"Request headers: {json.dumps({k: v[:10] + '...' if k == 'x-apihub-key' else v for k, v in headers.items()}, indent=2)}")
                    logger.error(f"Request params: {json.dumps(params, indent=2)}")
                    raise HTTPException(status_code=500, detail="Error searching for flights")
                
                result = await response.json()
                logger.info(f"Skyscanner API response: {json.dumps(result, indent=2)}")
                
                # Extract flights from the response
                flights = []
                if "itineraries" in result and "buckets" in result["itineraries"]:
                    for bucket in result["itineraries"]["buckets"]:
                        for item in bucket.get("items", []):
                            flights.append(item)
                # Defensive fallback: if no flights found, try legacy path
                if not flights and "flights" in result and "results" in result["flights"]:
                    flights = result["flights"]["results"]

                logger.info(f"Found {len(flights)} flights in response")
                
                formatted_results = []
                for flight in flights:
                    try:
                        # Log the raw flight data for debugging
                        logger.debug(f"Processing flight: {json.dumps(flight, indent=2)}")
                        
                        # Get the first leg and segment
                        legs = flight.get("legs", [])
                        if not legs:
                            logger.warning("No legs found in flight")
                            continue
                            
                        leg = legs[0]
                        segments = leg.get("segments", [])
                        if not segments:
                            logger.warning("No segments found in leg")
                            continue
                            
                        segment = segments[0]
                        
                        # Calculate layover times for each leg
                        def format_leg(leg):
                            segments = leg.get("segments", [])
                            if not segments:
                                return None

                            # Overall timing
                            first_segment = segments[0]
                            last_segment = segments[-1]
                            duration = leg.get("durationInMinutes", 0)

                            # Layover calculations
                            layovers = []
                            if leg.get("stopCount", 0) > 0 and len(segments) > 1:
                                for i in range(len(segments) - 1):
                                    arrival_time = datetime.fromisoformat(segments[i].get("arrival"))
                                    departure_time = datetime.fromisoformat(segments[i+1].get("departure"))
                                    layover_duration = departure_time - arrival_time
                                    
                                    layover_hours = layover_duration.seconds // 3600
                                    layover_minutes = (layover_duration.seconds % 3600) // 60
                                    
                                    layovers.append({
                                        "duration_str": f"{layover_hours}h {layover_minutes}m",
                                        "airport": segments[i+1]['origin'].get('name', 'N/A')
                                    })

                            return {
                                "departure": {
                                    "time": first_segment.get("departure"),
                                    "airport": { "code": first_segment.get("origin", {}).get("displayCode") }
                                },
                                "arrival": {
                                    "time": last_segment.get("arrival"),
                                    "airport": { "code": last_segment.get("destination", {}).get("displayCode") }
                                },
                                "duration": duration,
                                "stops": leg.get("stopCount", 0),
                                "layovers": layovers,
                                "airline": {
                                    "name": leg.get("carriers", {}).get("marketing", [{}])[0].get("name"),
                                    "logo": leg.get("carriers", {}).get("marketing", [{}])[0].get("logoUrl")
                                }
                            }

                        # Handle round-trip (2 legs) and one-way (1 leg)
                        if len(legs) == 2:
                            outbound_leg = format_leg(legs[0])
                            inbound_leg = format_leg(legs[1])
                            if not outbound_leg or not inbound_leg:
                                logger.warning("Skipping flight due to missing leg data")
                                continue
                                
                            formatted_flight = {
                                "id": flight.get("id"),
                                "date": outbound_leg['departure']['time'],
                                "trip_type": "round_trip",
                                "price": {
                                    "amount": flight.get("price", {}).get("raw", 0),
                                    "currency": "USD",
                                    "formatted": flight.get("price", {}).get("formatted", "N/A")
                                },
                                "outbound": outbound_leg,
                                "inbound": inbound_leg,
                                "booking_url": flight.get("deeplink", ""),
                                "fare_policy": {
                                    "is_changeable": flight.get("farePolicy", {}).get("isChangeAllowed", False),
                                    "is_refundable": flight.get("farePolicy", {}).get("isCancellationAllowed", False)
                                },
                                "tags": flight.get("tags", [])
                            }
                        else:
                            # One-way (or fallback)
                            outbound_leg = format_leg(legs[0])
                            if not outbound_leg:
                                logger.warning("Skipping flight due to missing leg data")
                                continue
                                
                            formatted_flight = {
                                "id": flight.get("id"),
                                "date": outbound_leg['departure']['time'],
                                "trip_type": "one_way",
                                "price": {
                                    "amount": flight.get("price", {}).get("raw", 0),
                                    "currency": "USD",
                                    "formatted": flight.get("price", {}).get("formatted", "N/A")
                                },
                                "outbound": outbound_leg,
                                "booking_url": flight.get("deeplink", ""),
                                "fare_policy": {
                                    "is_changeable": flight.get("farePolicy", {}).get("isChangeAllowed", False),
                                    "is_refundable": flight.get("farePolicy", {}).get("isCancellationAllowed", False)
                                },
                                "tags": flight.get("tags", [])
                            }
                        formatted_results.append(formatted_flight)
                    except Exception as e:
                        logger.error(f"Error processing flight: {str(e)}")
                        continue
                
                # Return the formatted response
                return {
                    "status": "success",
                    "query_details": {
                        "origin": query.origin,
                        "destination": query.destination,
                        "date": query.date,
                        "return_date": query.return_date,
                        "natural_query": query.query
                    },
                    "results": {
                        "fastest": sorted(formatted_results, key=lambda x: (
                            x["outbound"]["duration"] + 
                            (x["inbound"]["duration"] if x["trip_type"] == "round_trip" else 0)
                        ))[:3],
                        "cheapest": sorted(formatted_results, key=lambda x: x["price"]["amount"])[:3],
                        "optimal": sorted(formatted_results, key=lambda x: (
                            x["price"]["amount"] * 0.7 +
                            (x["outbound"]["duration"] + 
                             (x["inbound"]["duration"] if x["trip_type"] == "round_trip" else 0)) * 0.2 +
                            (x["outbound"]["stops"] + 
                             (x["inbound"]["stops"] if x["trip_type"] == "round_trip" else 0)) * 100 * 0.1
                        ))[:3]
                    },
                    "total_results": len(formatted_results)
                }
                
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error searching for flights: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while searching for flights. Please try again."
        )

@app.post("/api/search/natural")
async def search_flights_natural(request: Request):
    try:
        # Get the query from the request body
        body = await request.json()
        query = body.get('query')
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={"error": "No query provided"}
            )
        
        # Parse the natural language query
        parser = EnhancedQueryParser(api_key=os.getenv('X_API_KEY'))
        result = await parser.parse_query(query)
        
        if "error" in result:
            return JSONResponse(
                status_code=400,
                content={"error": result["error"]}
            )
        
        # Create a SearchQuery object for the search_flights function
        search_params = SearchQuery(
            origin=result['origin'],
            destination=result['destination'],
            date=result['date'],
            return_date=result.get('return_date'),  # Pass return_date if present
            query=query  # Include the original query
        )
        
        # Use the parsed parameters to search for flights
        return await search_flights(search_params)
        
    except Exception as e:
        logger.error(f"Error in search_flights_natural: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        ) 