import logging
import json
from typing import Dict, List
from api.utils import generate_flexible_dates
import httpx

logger = logging.getLogger(__name__)

API_URL = "https://Skyscanner.proxy-production.allthingsdev.co/search"
API_HEADERS = {
    'Accept': 'application/json',
    'x-apihub-key': 'Njuc82BYStFO0rzRK8PkKmdMGP-SMgDdHYt5keHLsriWbZhe1t',
    'x-apihub-host': 'Skyscanner.allthingsdev.co',
    'x-apihub-endpoint': '0e8a330d-269e-42cc-a1a8-fde0445ee552'
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
                response = httpx.get(API_URL, params=params, headers=API_HEADERS, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Skyscanner raw response for {out_date} to {ret_date}: {json.dumps(data)[:1000]}")

                # Process the response
                if response.status_code == 200:
                    data = response.json()
                    itineraries = data.get('itineraries', {})
                    buckets = itineraries.get('buckets', [])
                    if buckets and len(buckets) > 0:
                        items = buckets[0].get('items', [])
                        for item in items:
                            legs = item.get('legs', [])
                            if len(legs) == 2:
                                outbound_leg = legs[0]
                                inbound_leg = legs[1]
                                result = {
                                    "trip_type": "round_trip",
                                    "price": item['price'],
                                    "outbound": extract_leg_details(outbound_leg),
                                    "inbound": extract_leg_details(inbound_leg),
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