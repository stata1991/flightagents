from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from .search_one_way import search_one_way_flights
from .search_round_trip import search_round_trip_flights
from .booking_client import booking_client

router = APIRouter()

@router.get("/flights/search")
async def search_flights_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Simple flight search endpoint using location names
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-destination")
async def search_destination(query: str = Query(..., description="Search query for destination/airport")):
    """
    Search for destinations and airports using Booking.com API
    """
    try:
        result = booking_client.search_destination(query)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-one-way")
async def search_one_way(
    from_id: str = Query(..., description="Departure location ID (from destination search)"),
    to_id: str = Query(..., description="Destination location ID (from destination search)"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for one-way flights using Booking.com API (with location IDs)
    """
    try:
        result = booking_client.search_flights(
            from_id=from_id,
            to_id=to_id,
            depart_date=depart_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-round-trip")
async def search_round_trip(
    from_id: str = Query(..., description="Departure location ID (from destination search)"),
    to_id: str = Query(..., description="Destination location ID (from destination search)"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Return date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for round-trip flights using Booking.com API (with location IDs)
    """
    try:
        result = booking_client.search_flights(
            from_id=from_id,
            to_id=to_id,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-one-way-simple")
async def search_one_way_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for one-way flights using location names (automatically converts to IDs)
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-round-trip-simple")
async def search_round_trip_simple(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: str = Query(..., description="Return date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: str = Query("0,17", description="Children ages (comma-separated)"),
    cabin_class: str = Query("ECONOMY", description="Cabin class"),
    stops: str = Query("none", description="Stop preferences (none, one, two)"),
    page_no: int = Query(1, description="Page number"),
    sort: str = Query("BEST", description="Sort order (BEST, PRICE, DURATION)"),
    currency_code: str = Query("USD", description="Currency code")
):
    """
    Search for round-trip flights using location names (automatically converts to IDs)
    """
    try:
        result = booking_client.search_flights_by_location(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class,
            stops=stops,
            page_no=page_no,
            sort=sort,
            currency_code=currency_code
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search-with-booking-url")
async def search_with_booking_url(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: int = Query(0, description="Number of children"),
    cabin_class: str = Query("ECONOMY", description="Cabin class")
):
    """
    Search for flights and generate Booking.com deep link URL
    """
    try:
        result = booking_client.get_flight_booking_info(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class
        )
        
        if "error" in result.get("flight_results", {}):
            raise HTTPException(status_code=500, detail=result["flight_results"]["error"])
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-booking-url")
async def generate_booking_url(
    from_location: str = Query(..., description="Departure location name"),
    to_location: str = Query(..., description="Destination location name"),
    depart_date: str = Query(..., description="Departure date (YYYY-MM-DD)"),
    return_date: Optional[str] = Query(None, description="Return date (YYYY-MM-DD) for round trips"),
    adults: int = Query(1, description="Number of adult passengers"),
    children: int = Query(0, description="Number of children"),
    cabin_class: str = Query("ECONOMY", description="Cabin class")
):
    """
    Generate only the Booking.com deep link URL without searching flights
    """
    try:
        booking_url = booking_client.generate_booking_url(
            from_location=from_location,
            to_location=to_location,
            depart_date=depart_date,
            return_date=return_date,
            adults=adults,
            children=children,
            cabin_class=cabin_class
        )
        
        return {
            "success": True,
            "booking_url": booking_url,
            "search_params": {
                "from_location": from_location,
                "to_location": to_location,
                "depart_date": depart_date,
                "return_date": return_date,
                "adults": adults,
                "children": children,
                "cabin_class": cabin_class
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))