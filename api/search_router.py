from fastapi import APIRouter, HTTPException
from api.models import SearchRequest
from api.search_one_way import search_one_way_flights
from api.search_round_trip import search_round_trip_flights
from api.normalize_results import rank_flight_results
from api.utils import generate_flexible_dates
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search")
def search_flights(request: SearchRequest):
    try:
        # Generate flexible dates based on trip type
        if request.trip_type == "round-trip":
            outbound_dates, return_dates = generate_flexible_dates(
                request.departure_date, request.return_date, request.flex_days
            )
            raw_result = search_round_trip_flights({
                "origin": request.origin,
                "destination": request.destination,
                "departure_date": request.departure_date,
                "return_date": request.return_date,
                "flex_days": request.flex_days
            })
            date_range = {
                "outbound": outbound_dates,
                "return": return_dates
            }
        else:
            outbound_dates = generate_flexible_dates(request.departure_date, flex_days=request.flex_days)
            raw_result = search_one_way_flights(request, outbound_dates)
            date_range = {
                "outbound": outbound_dates
            }

        # Extract metadata safely for both one-way and round-trip
        trip_type = raw_result.get("trip_type", "one-way")
        origin = raw_result.get("origin", "")
        destination = raw_result.get("destination", "")

        required_keys = ["trip_type", "origin", "destination", "results"]
        if not isinstance(raw_result, dict) or not all(key in raw_result for key in required_keys):
            logger.error(f"Invalid raw_result format: {raw_result}")
            raise HTTPException(status_code=500, detail="Invalid search result format")

        ranked = rank_flight_results(raw_result["results"])
        logger.info(f"Ranked results: {ranked}")

        return {
            "trip_type": trip_type,
            "origin": origin,
            "destination": destination,
            "date_range": date_range,
            "results": ranked
        }

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))