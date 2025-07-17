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

def search_round_trip_flights(payload):
    """This function is deprecated. Skyscanner API integration has been removed."""
    raise NotImplementedError("Skyscanner API integration has been removed. Use the new Booking.com API integration.")