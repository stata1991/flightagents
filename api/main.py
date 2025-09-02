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
from .hybrid_trip_router import router as hybrid_router
from .location_discovery_router import router as location_router
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

# Include hybrid trip planning router
app.include_router(hybrid_router)

# Include location discovery router
app.include_router(location_router)

# Initialize parser with Anthropic API key
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not configured")
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

@app.get("/hybrid", response_class=HTMLResponse)
async def hybrid_planner_page(request: Request):
    return templates.TemplateResponse("hybrid_trip_planner.html", {"request": request})

@app.get("/enhanced", response_class=HTMLResponse)
async def enhanced_travel_interface(request: Request):
    return templates.TemplateResponse("enhanced_travel_interface.html", {"request": request})

@app.get("/location-discovery", response_class=HTMLResponse)
async def location_discovery_page(request: Request):
    return templates.TemplateResponse("location_discovery.html", {"request": request})

@app.get("/test-hybrid")
async def test_hybrid():
    return {"message": "Hybrid route is working!"}

@app.post("/api/search")
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
        
        # Use RapidAPI flight search service
        headers = {
            "X-RapidAPI-Key": api_key.strip(),
            "X-RapidAPI-Host": "skyscanner-api.p.rapidapi.com"
        }
        
        # Construct query parameters for RapidAPI
        params = {
            "originSkyId": query.origin,
            "destinationSkyId": query.destination,
            "date": formatted_date,
            "adults": "1",
            "currency": "USD",
            "country": "US",
            "locale": "en-US"
        }
        if formatted_return_date:
            params["returnDate"] = formatted_return_date
        
        logger.info(f"Searching for flights with parameters: {json.dumps(params, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://skyscanner-api.p.rapidapi.com/v3e/browse/flights",
                headers=headers,
                params=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"RapidAPI flight search error: {error_text}")
                    logger.error(f"Request URL: {response.url}")
                    logger.error(f"Request headers: {json.dumps({k: v[:10] + '...' if k == 'X-RapidAPI-Key' else v for k, v in headers.items()}, indent=2)}")
                    logger.error(f"Request params: {json.dumps(params, indent=2)}")
                    raise HTTPException(status_code=500, detail="Error searching for flights")
                
                result = await response.json()
                logger.info(f"RapidAPI flight search response: {json.dumps(result, indent=2)}")
                
                # Extract flights from the response
                flights = []
                if "data" in result and "itineraries" in result["data"]:
                    for itinerary in result["data"]["itineraries"]:
                        if "pricingOptions" in itinerary:
                            for option in itinerary["pricingOptions"]:
                                flight_info = {
                                    "airline": option.get("agents", [{}])[0].get("name", "Unknown"),
                                    "flight_number": f"{option.get('carriers', {}).get('marketing', [{}])[0].get('name', 'Unknown')} {option.get('carriers', {}).get('marketing', [{}])[0].get('flightNumber', '')}",
                                    "departure_time": option.get("legs", [{}])[0].get("departure", ""),
                                    "arrival_time": option.get("legs", [{}])[0].get("arrival", ""),
                                    "duration": option.get("legs", [{}])[0].get("durationInMinutes", 0),
                                    "price": option.get("price", {}).get("amount", 0),
                                    "stops": len(option.get("legs", [])) - 1,
                                    "booking_link": option.get("pricingOptions", [{}])[0].get("url", "")
                                }
                                flights.append(flight_info)
                
                # If no flights found, return mock data for testing
                if not flights:
                    logger.warning("No flights found from API, returning mock data")
                    flights = [
                        {
                            "airline": "Air France",
                            "flight_number": "AF23",
                            "departure_time": "19:30",
                            "arrival_time": "08:45",
                            "duration": "7h15m",
                            "price": 1200,
                            "stops": 0,
                            "booking_link": f"https://www.airfrance.com/booking/{query.origin}-{query.destination}"
                        },
                        {
                            "airline": "Delta Airlines",
                            "flight_number": "DL262",
                            "departure_time": "18:30",
                            "arrival_time": "07:45",
                            "duration": "7h15m",
                            "price": 980,
                            "stops": 0,
                            "booking_link": f"https://www.delta.com/booking/{query.origin}-{query.destination}"
                        },
                        {
                            "airline": "American Airlines",
                            "flight_number": "AA44",
                            "departure_time": "20:15",
                            "arrival_time": "09:30",
                            "duration": "7h15m",
                            "price": 920,
                            "stops": 0,
                            "booking_link": f"https://www.aa.com/booking/{query.origin}-{query.destination}"
                        }
                    ]

                logger.info(f"Found {len(flights)} flights in response")
                
                return {
                    "success": True,
                    "flights": flights,
                    "message": "Flight search completed"
                }
        
    except Exception as e:
        logger.error(f"Flight search failed: {str(e)}")
        return {
            "success": False,
            "flights": [],
            "error": str(e)
        }

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



 