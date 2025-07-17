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

def search_one_way_flights(request, dates):
    """This function is deprecated. Skyscanner API integration has been removed."""
    raise NotImplementedError("Skyscanner API integration has been removed. Use the new Booking.com API integration.")
