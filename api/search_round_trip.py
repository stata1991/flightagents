import logging
import json
from typing import Dict, List
from api.utils import generate_flexible_dates
import httpx
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Skyscanner API configuration
SKYSCANNER_API_HOST = "Skyscanner.proxy-production.allthingsdev.co"
SKYSCANNER_API_KEY = "Njuc82BYStFO0rzRK8PkKmdMGP-SMgDdHYt5keHLsriWbZhe1t"
POLLING_INTERVAL = 2
MAX_POLLS = 15

def _get_api_headers() -> Dict[str, str]:
    return {
        'Accept': 'application/json',
        'x-apihub-key': SKYSCANNER_API_KEY,
        'x-apihub-host': SKYSCANNER_API_HOST,
        'x-apihub-endpoint': '0e8a330d-269e-42cc-a1a8-fde0445ee552'
    }

def create_search(params: Dict) -> str:
    """Initiates a search and returns a session token."""
    with httpx.Client() as client:
        response = client.get(f"https://{SKYSCANNER_API_HOST}/search", params=params, headers=_get_api_headers(), timeout=30.0)
        response.raise_for_status()
        data = response.json()
        session_id = data.get('context', {}).get('sessionId')
        if not session_id:
            raise ValueError("No session ID found in initial response")
        logger.info(f"Created search session: {session_id}")
        return session_id

def poll_results(session_id: str) -> Dict:
    """Polls for results using the session token."""
    with httpx.Client() as client:
        for i in range(MAX_POLLS):
            response = client.get(f"https://{SKYSCANNER_API_HOST}/search", params={'sessionId': session_id}, headers=_get_api_headers(), timeout=30.0)
            response.raise_for_status()
            data = response.json()
            status = data.get('context', {}).get('status', 'unknown')
            logger.info(f"Polling attempt {i + 1}/{MAX_POLLS}: Status is '{status}'")
            if status == 'complete' or data.get('itineraries', {}).get('buckets'):
                logger.info("Search complete.")
                return data
            time.sleep(POLLING_INTERVAL)
    logger.warning("Polling timed out.")
    return {}

def extract_leg_details(leg: Dict) -> Dict:
    """Extracts and formats details from a flight leg."""
    duration_min = leg.get('durationInMinutes', 0)
    hours = duration_min // 60
    minutes = duration_min % 60

    layovers = []
    if leg.get('stopCount', 0) > 0 and len(leg.get('segments', [])) > 1:
        for i in range(len(leg['segments']) - 1):
            arrival_str = leg['segments'][i]['arrival']
            departure_str = leg['segments'][i+1]['departure']
            arrival_time = datetime.fromisoformat(arrival_str)
            departure_time = datetime.fromisoformat(departure_str)
            layover_duration = departure_time - arrival_time
            
            layover_hours = layover_duration.seconds // 3600
            layover_minutes = (layover_duration.seconds % 3600) // 60
            
            layovers.append({
                "duration_str": f"{layover_hours}h {layover_minutes}m",
                "airport": leg['segments'][i+1]['origin'].get('name', 'N/A')
            })

    marketing_carrier = leg.get('carriers', {}).get('marketing', [{}])[0]

    return {
        "departure_time": leg.get('departure'),
        "arrival_time": leg.get('arrival'),
        "duration": f"{hours}h {minutes}m" if minutes else f"{hours}h",
        "raw_duration_minutes": duration_min,
        "stops": leg.get('stopCount', 0),
        "layovers": layovers,
        "airline": {
            "name": marketing_carrier.get('name', 'N/A'),
            "logo": marketing_carrier.get('logoUrl', '')
        }
    }

def search_round_trip_flights(payload: Dict) -> Dict:
    origin = payload["origin"]
    destination = payload["destination"]
    departure_date = payload["departure_date"]
    return_date = payload.get("return_date")
    flex_days = payload.get("flex_days", 0)
    filters = payload.get("filters", {})

    outbound_dates, return_dates = generate_flexible_dates(
        departure_date, return_date, flex_days
    )

    final_results = []

    for out_date in outbound_dates:
        for ret_date in return_dates:
            params = {
                "adults": 1,
                "origin": origin,
                "destination": destination,
                "departureDate": out_date,
                "returnDate": ret_date,
                "cabinClass": "economy",
                "currency": "USD",
                "market": "US",
                "locale": "en-US",
                "rtn": 1
            }

            try:
                session_id = create_search(params)
                data = poll_results(session_id)

                if data:
                    itineraries = data.get('itineraries', {})
                    buckets = itineraries.get('buckets', [])
                    if buckets and len(buckets) > 0:
                        items = buckets[0].get('items', [])
                        for item in items:
                            legs = item.get('legs', [])
                            if len(legs) == 2:
                                outbound_leg = legs[0]
                                inbound_leg = legs[1]
                                
                                outbound_details = extract_leg_details(outbound_leg)
                                inbound_details = extract_leg_details(inbound_leg)

                                result = {
                                    "trip_type": "round_trip",
                                    "price": item['price'],
                                    "outbound": outbound_details,
                                    "inbound": inbound_details,
                                    "raw_duration_minutes": outbound_details['raw_duration_minutes'] + inbound_details['raw_duration_minutes'],
                                    "booking_url": item.get('deeplink', ''),
                                    "fare_policy": item.get('farePolicy', {}),
                                    "tags": item.get('tags', [])
                                }
                                final_results.append(result)
                            else:
                                # Handle one-way or error
                                pass

            except Exception as e:
                logger.error(f"Skyscanner API error for {out_date} to {ret_date}: {e}")

    # Sort results by price for cheapest
    cheapest_flights = sorted(final_results, key=lambda x: float(x["price"].replace("$", "").replace(",", "")) if x["price"] != "N/A" else float("inf"))
    
    # Sort results by duration for fastest
    fastest_flights = sorted(final_results, key=lambda x: x["raw_duration_minutes"])
    
    # For optimal, combine price and duration with more balanced weights
    def optimal_score(flight):
        try:
            price = float(flight["price"].replace("$", "").replace(",", "")) if flight["price"] != "N/A" else float("inf")
            duration = flight["raw_duration_minutes"]
            total_stops = flight["outbound"]["stops"] + flight["inbound"]["stops"]
            
            # Normalize values
            max_price = max(float(f["price"].replace("$", "").replace(",", "")) for f in final_results if f["price"] != "N/A")
            max_duration = max(f["raw_duration_minutes"] for f in final_results)
            
            # Calculate normalized scores (lower is better)
            price_score = price / max_price
            duration_score = duration / max_duration
            stops_score = total_stops / 4  # Assuming max 2 stops each way
            
            # Weight the factors (40% price, 40% duration, 20% stops)
            return (price_score * 0.4) + (duration_score * 0.4) + (stops_score * 0.2)
        except Exception as e:
            logger.error(f"Error calculating optimal score: {e}")
            return float("inf")
    
    optimal_flights = sorted(final_results, key=optimal_score)

    # Remove duplicates while preserving order
    def remove_duplicates(flights):
        seen = set()
        unique_flights = []
        for flight in flights:
            key = (flight["airlines"], flight["price"], flight["outbound"]["departure_time"], flight["inbound"]["departure_time"])
            if key not in seen:
                seen.add(key)
                unique_flights.append(flight)
        return unique_flights

    return {
        "trip_type": "round-trip",
        "origin": origin,
        "destination": destination,
        "outbound_date": departure_date,
        "return_date": return_date,
        "date_range": {
            "outbound": outbound_dates,
            "return": return_dates
        },
        "results": {
            "cheapest": {"cheapest": remove_duplicates(cheapest_flights)[:3]},
            "fastest": {"fastest": remove_duplicates(fastest_flights)[:3]},
            "optimal": {"optimal": remove_duplicates(optimal_flights)[:3]}
        }
    }