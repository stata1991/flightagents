import requests
import time
import logging
from api.utils import generate_flexible_dates
from api.models import SearchRequest
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Skyscanner API configuration
SKYSCANNER_API_HOST = "Skyscanner.proxy-production.allthingsdev.co"
SKYSCANNER_API_KEY = "Njuc82BYStFO0rzRK8PkKmdMGP-SMgDdHYt5keHLsriWbZhe1t"
POLLING_INTERVAL = 2
MAX_POLLS = 15

def _get_api_headers() -> Dict[str, str]:
    return {
        "Accept": "application/json",
        "x-apihub-key": SKYSCANNER_API_KEY,
        "x-apihub-host": SKYSCANNER_API_HOST,
        "x-apihub-endpoint": "0e8a330d-269e-42cc-a1a8-fde0445ee552"
    }

def create_search(params: Dict[str, Any]) -> Optional[str]:
    """Initiates a search and returns a session token."""
    url = f"https://{SKYSCANNER_API_HOST}/search"
    try:
        response = requests.get(url, headers=_get_api_headers(), params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('error'):
            logger.error(f"Skyscanner initial search error: {data.get('message')}")
            return None
        
        # The session ID is often in the `context` dictionary
        session_id = data.get('context', {}).get('sessionId')
        if not session_id:
            logger.error("No session ID returned from initial search.")
            return None
            
        logger.info(f"Skyscanner search initiated. Session ID: {session_id}")
        return session_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating Skyscanner search: {e}")
        return None

def poll_results(session_id: str) -> Dict:
    """Polls for results using the session token."""
    url = f"https://{SKYSCANNER_API_HOST}/search"
    params = {'sessionId': session_id}
    
    for i in range(MAX_POLLS):
        try:
            response = requests.get(url, headers=_get_api_headers(), params=params)
            response.raise_for_status()
            data = response.json()
            
            status = data.get('context', {}).get('status', 'unknown')
            logger.info(f"Polling attempt {i + 1}/{MAX_POLLS}: Status is '{status}'")
            
            if status == 'complete' or data.get('itineraries', {}).get('buckets'):
                logger.info("Search complete.")
                return data
            
            time.sleep(POLLING_INTERVAL)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error polling Skyscanner results: {e}")
            time.sleep(POLLING_INTERVAL)
            
    logger.warning("Polling timed out. Returning last known data.")
    return {} # Return empty dict if polling fails

def extract_leg_details(leg: Dict) -> Dict:
    """Extracts and formats details from a flight leg."""
    duration_min = leg.get('durationInMinutes', 0)
    hours = duration_min // 60
    minutes = duration_min % 60
    
    layovers = []
    if leg.get('stopCount', 0) > 0 and len(leg.get('segments', [])) > 1:
        for i in range(len(leg['segments']) - 1):
            # Layover is the time between arrival of one segment and departure of the next
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

def search_one_way_flights(request: SearchRequest, dates: List[str]):
    all_results = []

    for date in dates:
        params = {
            "adults": 1,
            "origin": request.origin,
            "destination": request.destination,
            "departureDate": date,
            "cabinClass": "economy",
            "currency": "USD",
            "market": "US",
            "locale": "en-US"
        }

        session_id = create_search(params)
        if not session_id:
            logger.error(f"Failed to create search for date {date}")
            continue

        data = poll_results(session_id)
        if not data:
            logger.error("Failed to get valid response from Skyscanner API after polling")
            continue

        # --- REVISED LOGIC: Use extract_leg_details ---
        buckets = data.get('itineraries', {}).get('buckets', [])
        seen_ids = set()
        if buckets:
            for bucket in buckets:
                for item in bucket.get('items', []):
                    flight_id = item.get('id')
                    if not flight_id or flight_id in seen_ids:
                        continue
                    seen_ids.add(flight_id)
                    
                    leg = item.get('legs', [{}])[0]
                    leg_details = extract_leg_details(leg)

                    # Apply filters
                    airline_code = leg.get('carriers', {}).get('marketing', [{}])[0].get('alternateId', '')
                    if request.filters.get('preferred_airlines') and airline_code not in request.filters['preferred_airlines']:
                        continue
                    price_str = item.get('price', {}).get('formatted', 'N/A')
                    if request.filters.get('max_price'):
                        try:
                            flight_price = float(price_str.replace("$", "").replace(",", ""))
                            if flight_price > request.filters['max_price']:
                                continue
                        except (ValueError, TypeError):
                            pass
                    if request.filters.get('non_stop_only') and leg_details['stops'] > 0:
                        continue
                    if request.filters.get('max_stops') is not None and leg_details['stops'] > request.filters['max_stops']:
                        continue

                    flight = {
                        'id': flight_id,
                        'date': date,
                        'price': item.get('price'),
                        'outbound': leg_details,
                        'booking_url': item.get('deeplink', ''),
                        'provider': 'Skyscanner',
                        'raw_duration_minutes': leg_details['raw_duration_minutes']
                    }
                    all_results.append(flight)
                    logger.info(f"Added flight from bucket: {flight_id}")
        else:
            # --- FALLBACK: Use filterStats.carriers as before ---
            metadata = data.get("metadata", {})
            carriers = metadata.get("carriers", [])
            if not carriers:
                itineraries = data.get("itineraries", {})
                filter_stats = itineraries.get("filterStats", {})
                carriers = filter_stats.get("carriers", [])
            if not carriers:
                logger.error("No carriers found in API response (fallback)")
                continue
            for carrier in carriers:
                airline_name = carrier.get("name", "Unknown")
                airline_code = carrier.get("code", carrier.get("alternateId", ""))
                # Apply airline filter
                if request.filters.get("preferred_airlines") and airline_code not in request.filters["preferred_airlines"]:
                    continue
                price = carrier.get("minPrice", "N/A")
                if price != "N/A" and not price.startswith("$"):
                    price = f"${price}"
                if request.filters.get("max_price"):
                    try:
                        flight_price = float(price.replace("$", "").replace(",", ""))
                        if flight_price > request.filters["max_price"]:
                            continue
                    except (ValueError, TypeError):
                        pass
                # Fallback: No segment/leg info, so set as N/A
                flight = {
                    'date': date,
                    'price': price,
                    'booking_url': '',
                    'provider': 'Skyscanner',
                    'duration': 'N/A',
                    'airlines': f"{airline_name} ({airline_code})",
                    'departure_time': 'N/A',
                    'arrival_time': 'N/A',
                    'stops': 0,
                    'aircraft': 'Unknown',
                    'raw_duration_minutes': 0
                }
                all_results.append(flight)
                logger.info(f"Added flight from fallback: {flight}")

    if not all_results:
        logger.error("No flights found for any dates")
        return {
            "trip_type": "one-way",
            "origin": request.origin,
            "destination": request.destination,
            "date_range": {
                "outbound": dates
            },
            "results": {
                "cheapest": {"cheapest": []},
                "fastest": {"fastest": []},
                "optimal": {"optimal": []}
            }
        }

    # Sort results by price for cheapest
    cheapest_flights = sorted(all_results, key=lambda x: float(x["price"].replace("$", "").replace(",", "")) if x["price"] != "N/A" else float("inf"))
    
    # Sort results by duration for fastest
    fastest_flights = sorted(all_results, key=lambda x: x["raw_duration_minutes"])
    
    # For optimal, combine price and duration with more balanced weights
    def optimal_score(flight):
        try:
            price = float(flight["price"].replace("$", "").replace(",", "")) if flight["price"] != "N/A" else float("inf")
            duration = flight["raw_duration_minutes"]
            stops = flight["stops"]
            
            # Normalize values
            max_price = max(float(f["price"].replace("$", "").replace(",", "")) for f in all_results if f["price"] != "N/A")
            max_duration = max(f["raw_duration_minutes"] for f in all_results)
            
            # Calculate normalized scores (lower is better)
            price_score = price / max_price
            duration_score = duration / max_duration
            stops_score = stops / 2  # Assuming max 2 stops
            
            # Weight the factors (40% price, 40% duration, 20% stops)
            return (price_score * 0.4) + (duration_score * 0.4) + (stops_score * 0.2)
        except Exception as e:
            logger.error(f"Error calculating optimal score: {e}")
            return float("inf")
    
    optimal_flights = sorted(all_results, key=optimal_score)

    return {
        "trip_type": "one-way",
        "origin": request.origin,
        "destination": request.destination,
        "date_range": {
            "outbound": dates
        },
        "results": {
            "cheapest": {"cheapest": cheapest_flights[:5]},
            "fastest": {"fastest": fastest_flights[:5]},
            "optimal": {"optimal": optimal_flights[:5]}
        }
    }
