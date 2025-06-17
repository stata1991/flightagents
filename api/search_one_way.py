import requests
import time
import logging
from api.utils import generate_flexible_dates
from api.models import SearchRequest
from typing import List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Skyscanner API configuration
SKYSCANNER_API_URL = "https://Skyscanner.proxy-production.allthingsdev.co/search"
SKYSCANNER_API_HEADERS = {
    "Accept": "application/json",
    "x-apihub-key": "Njuc82BYStFO0rzRK8PkKmdMGP-SMgDdHYt5keHLsriWbZhe1t",
    "x-apihub-host": "Skyscanner.allthingsdev.co",
    "x-apihub-endpoint": "0e8a330d-269e-42cc-a1a8-fde0445ee552"
}


def search_one_way_flights(request: SearchRequest, dates: List[str]):
    all_results = []

    for date in dates:
        try:
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

            logger.info(f"Making request to Skyscanner API with params: {params}")
            max_attempts = 3
            data = None
            
            for attempt in range(max_attempts):
                try:
                    response = requests.get(SKYSCANNER_API_URL, headers=SKYSCANNER_API_HEADERS, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('error'):
                        logger.error(f"Skyscanner API error: {data.get('message')}")
                        continue

                    if data.get("status") == "complete":
                        break
                    time.sleep(2)
                except requests.exceptions.RequestException as e:
                    logger.error(f"Skyscanner API request error (attempt {attempt + 1}): {e}")
                    if hasattr(e, 'response') and e.response is not None:
                        logger.error(f"Response text: {e.response.text}")
                    time.sleep(2)
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                    time.sleep(2)
                    continue

            if not data:
                logger.error("Failed to get valid response from Skyscanner API after all attempts")
                continue

            # --- NEW LOGIC: Extract flights from buckets if present ---
            buckets = data.get('itineraries', {}).get('buckets', [])
            logger.info(f"Buckets in response: {buckets}")
            seen_ids = set()
            if buckets:
                for bucket in buckets:
                    for item in bucket.get('items', []):
                        flight_id = item.get('id')
                        if not flight_id or flight_id in seen_ids:
                            continue
                        seen_ids.add(flight_id)
                        leg = item['legs'][0] if item.get('legs') else None
                        if not leg:
                            continue
                        price = item.get('price', {}).get('formatted', 'N/A')
                        booking_url = item.get('deeplink', '')
                        duration_min = leg.get('durationInMinutes', 0)
                        hours = duration_min // 60
                        minutes = duration_min % 60
                        duration = f"{hours}h {minutes}m" if minutes else f"{hours}h"
                        airlines = leg.get('carriers', {}).get('marketing', [])
                        airline_name = airlines[0]['name'] if airlines else 'Unknown'
                        airline_code = airlines[0].get('alternateId', '') if airlines else ''
                        departure_time = leg.get('departure', 'N/A')
                        arrival_time = leg.get('arrival', 'N/A')
                        stops = leg.get('stopCount', 0)
                        # Aircraft info is not always present
                        aircraft = 'Unknown'
                        # Apply filters
                        if request.filters.get('preferred_airlines') and airline_code not in request.filters['preferred_airlines']:
                            continue
                        if request.filters.get('max_price'):
                            try:
                                flight_price = float(price.replace("$", "").replace(",", ""))
                                if flight_price > request.filters['max_price']:
                                    continue
                            except (ValueError, TypeError):
                                pass
                        if request.filters.get('non_stop_only') and stops > 0:
                            continue
                        if request.filters.get('max_stops') is not None and stops > request.filters['max_stops']:
                            continue
                        flight = {
                            'date': date,
                            'price': price,
                            'booking_url': booking_url,
                            'provider': 'Skyscanner',
                            'duration': duration,
                            'airlines': f"{airline_name} ({airline_code})",
                            'departure_time': departure_time,
                            'arrival_time': arrival_time,
                            'stops': stops,
                            'aircraft': aircraft,
                            'raw_duration_minutes': duration_min
                        }
                        all_results.append(flight)
                        logger.info(f"Added flight from bucket: {flight}")
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

        except Exception as e:
            logger.error(f"Error processing date {date}: {str(e)}")
            continue

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
