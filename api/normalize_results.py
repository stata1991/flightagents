import json
import re
import logging
from typing import List, Dict, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_flight_result_card(result):
    price = result.get("price", "N/A")
    provider = result.get("provider", "Unknown")
    airlines = result.get("airlines", "Unknown Airline")
    booking_url = result.get("booking_url", "#")

    if "outbound_date" in result:
        date_str = f"Outbound: {result.get('outbound_date', 'N/A')} / Return: {result.get('return_date', 'N/A')}"
        duration_str = result.get("duration", "N/A")
        outbound_info = result.get("outbound", {})
        return_info = result.get("inbound", {})
        details = (
            f"  Outbound: {outbound_info.get('airlines', 'N/A')} ({outbound_info.get('duration', 'N/A')})\n"
            f"  Return: {return_info.get('airlines', 'N/A')} ({return_info.get('duration', 'N/A')})"
        )
    else:
        date_str = result.get("date", "N/A")
        duration_str = result.get("duration", "N/A")
        details = ""

    if duration_str and isinstance(duration_str, str):
        match = re.match(r"(\d+)h\s*(\d*)m?", duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            duration_str = f"{hours}h {minutes}m" if minutes else f"{hours}h"
        else:
            logger.warning(f"Invalid duration format: {duration_str}")

    return (
        f"\ud83d\uddd5\ufe0f **Dates:** {date_str}\n"
        f"\u2708\ufe0f **Airlines:** {airlines}\n"
        f"\ud83d\udd52 **Total Duration:** {duration_str}\n"
        f"\ud83d\udcb0 **Price:** ${price}\n"
        f"\ud83c\udfe2 **Provider:** {provider}\n"
        f"{details}\n"
        f"[\ud83d\udd17 Book Now]({booking_url})\n"
    )

def parse_duration_to_seconds(duration_str):
    if not duration_str:
        return float("inf")
    if isinstance(duration_str, str):
        match = re.match(r"(\d+)h\s*(\d*)m?", duration_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            return hours * 3600 + minutes * 60
    elif isinstance(duration_str, dict):
        total_seconds = 0
        for seg in ["outbound", "inbound"]:
            seg_dur = duration_str.get(seg)
            if isinstance(seg_dur, str):
                match = re.match(r"(\d+)h\s*(\d*)m?", seg_dur)
                if match:
                    hours = int(match.group(1))
                    minutes = int(match.group(2)) if match.group(2) else 0
                    total_seconds += hours * 3600 + minutes * 60
        return total_seconds
    return float("inf")

def rank_flight_results(results: Union[Dict, List]) -> Dict:
    ranked = {
        "cheapest": {"cheapest": []},
        "fastest": {"fastest": []},
        "optimal": {"optimal": []}
    }

    def process_flights(flights: List) -> List:
        if isinstance(flights, str):
            try:
                flights = json.loads(flights)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode flights JSON: {e}")
                return []
        if not isinstance(flights, list):
            logger.error(f"Expected list of flights, got {type(flights)}")
            return []
        return [f for f in flights if isinstance(f, dict) and f.get("price") is not None]

    all_flights = []
    if isinstance(results, dict):
        for category in results.keys():
            inner = results.get(category, {})
            if isinstance(inner, dict):
                all_flights.extend(process_flights(inner.get(category, [])))
            else:
                logger.error(f"Expected dict for category {category}, got {type(inner)}")
    else:
        all_flights = process_flights(results)

    if not all_flights:
        return ranked

    seen = set()
    unique_flights = []
    for flight in all_flights:
        if "outbound" in flight and "inbound" in flight:
            key = (
                flight.get("price"),
                json.dumps(flight.get("outbound", {})),
                json.dumps(flight.get("inbound", {})),
                flight.get("outbound_date"),
                flight.get("return_date")
            )
        else:
            key = (
                flight.get("price"),
                flight.get("duration"),
                flight.get("date"),
                flight.get("airlines")
            )
        if key not in seen:
            seen.add(key)
            unique_flights.append(flight)

    def extract_price(x):
        try:
            return float(x["price"].replace("$", "").replace(",", "").strip())
        except:
            return float("inf")

    ranked["cheapest"]["cheapest"] = sorted(
        unique_flights,
        key=extract_price
    )[:3]

    ranked["fastest"]["fastest"] = sorted(
        unique_flights,
        key=lambda x: parse_duration_to_seconds(x.get("duration"))
    )[:3]

    def get_optimal_score(flight):
        price = extract_price(flight)
        duration_val = flight.get("duration")
        if isinstance(duration_val, str) or isinstance(duration_val, dict):
            duration_seconds = parse_duration_to_seconds(duration_val)
        else:
            duration_seconds = float("inf")
        return price + (duration_seconds / 3600 * 10)

    ranked["optimal"]["optimal"] = sorted(
        unique_flights,
        key=get_optimal_score
    )[:3]

    return ranked