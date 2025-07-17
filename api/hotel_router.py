from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from .models import (
    HotelSearchRequest, 
    HotelSearchResponse, 
    HotelInfo, 
    HotelRoom, 
    HotelSearchResult
)
from .hotel_client import HotelClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hotels", tags=["hotels"])

# Initialize hotel client
hotel_client = HotelClient()

@router.post("/search", response_model=HotelSearchResponse)
async def search_hotels(request: HotelSearchRequest):
    """
    Search for hotels based on location, dates, and guest requirements
    
    Args:
        request: HotelSearchRequest with search parameters
        
    Returns:
        HotelSearchResponse with hotel results
    """
    try:
        logger.info(f"Hotel search request received: {request.location} from {request.check_in} to {request.check_out}")
        
        # Validate dates
        check_in_date = datetime.strptime(request.check_in, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(request.check_out, "%Y-%m-%d").date()
        
        if check_in_date >= check_out_date:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
        
        if check_in_date < date.today():
            raise HTTPException(status_code=400, detail="Check-in date cannot be in the past")
        
        # Perform hotel search
        result = hotel_client.search_hotels(request)
        
        logger.info(f"Hotel search completed. Found {result.total_results} hotels")
        return result
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is to preserve their status codes and details
        raise
    except ValueError as e:
        logger.error(f"Date validation error: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Hotel search error: {e}")
        raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")

@router.get("/search", response_model=HotelSearchResponse)
async def search_hotels_get(
    location: str = Query(..., description="Destination location (city, country)"),
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult guests"),
    children: Optional[str] = Query("", description="Children ages (comma-separated, e.g., '5,10')"),
    rooms: int = Query(1, description="Number of rooms"),
    currency: str = Query("USD", description="Currency code"),
    language: str = Query("en-us", description="Language code"),
    page_number: int = Query(1, description="Page number for pagination"),
    order: str = Query("price", description="Sort order (price, rating, distance)"),
    dest_id: Optional[str] = Query(None, description="Destination ID"),
    dest_type: str = Query("CITY", description="Destination type")
):
    """
    Search for hotels using GET request with query parameters
    
    Args:
        location: Destination location
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adult guests
        children: Children ages (comma-separated)
        rooms: Number of rooms
        currency: Currency code
        language: Language code
        page_number: Page number
        order: Sort order
        dest_id: Destination ID
        dest_type: Destination type
        
    Returns:
        HotelSearchResponse with hotel results
    """
    try:
        logger.info(f"Hotel search GET request received: {location} from {check_in} to {check_out}")
        
        # Parse children ages
        children_ages = []
        if children:
            try:
                children_ages = [int(age.strip()) for age in children.split(",") if age.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid children ages format")
        
        # Create request object
        request = HotelSearchRequest(
            location=location,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children_ages,
            rooms=rooms,
            currency=currency,
            language=language,
            page_number=page_number,
            order=order,
            dest_id=dest_id,
            dest_type=dest_type
        )
        
        logger.info(f"Created HotelSearchRequest: {request}")
        
        # Call the POST endpoint directly
        result = await search_hotels(request)
        logger.info(f"Hotel search completed successfully")
        return result
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is to preserve their status codes and details
        raise
    except Exception as e:
        logger.error(f"Hotel search GET error: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Hotel search failed: {str(e)}")

@router.get("/details/{hotel_id}")
async def get_hotel_details(
    hotel_id: str,
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult guests"),
    children: Optional[str] = Query("", description="Children ages (comma-separated)")
):
    """
    Get detailed information about a specific hotel
    
    Args:
        hotel_id: Hotel ID
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adult guests
        children: Children ages (comma-separated)
        
    Returns:
        Detailed hotel information
    """
    try:
        # Parse children ages
        children_ages = []
        if children:
            try:
                children_ages = [int(age.strip()) for age in children.split(",") if age.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid children ages format")
        
        logger.info(f"Hotel details requested for hotel ID: {hotel_id}")
        
        result = hotel_client.get_hotel_details(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children_ages
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Hotel details error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel details: {str(e)}")

@router.get("/availability/{hotel_id}")
async def check_hotel_availability(
    hotel_id: str,
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult guests"),
    children: Optional[str] = Query("", description="Children ages (comma-separated)")
):
    """
    Check availability for a specific hotel
    
    Args:
        hotel_id: Hotel ID
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adult guests
        children: Children ages (comma-separated)
        
    Returns:
        Hotel availability information
    """
    try:
        # Parse children ages
        children_ages = []
        if children:
            try:
                children_ages = [int(age.strip()) for age in children.split(",") if age.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid children ages format")
        
        logger.info(f"Hotel availability check for hotel ID: {hotel_id}")
        
        result = hotel_client.search_hotel_availability(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children_ages
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Hotel availability error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check hotel availability: {str(e)}")

@router.get("/photos/{hotel_id}")
async def get_hotel_photos(hotel_id: str):
    """
    Get photos for a specific hotel
    
    Args:
        hotel_id: Hotel ID
        
    Returns:
        Hotel photos
    """
    try:
        logger.info(f"Hotel photos requested for hotel ID: {hotel_id}")
        
        result = hotel_client.get_hotel_photos(hotel_id=hotel_id)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Hotel photos error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel photos: {str(e)}")

@router.get("/reviews/{hotel_id}")
async def get_hotel_reviews(
    hotel_id: str,
    page: int = Query(1, description="Page number for pagination"),
    language: str = Query("en-us", description="Language code for reviews")
):
    """
    Get reviews for a specific hotel
    
    Args:
        hotel_id: Hotel ID
        page: Page number
        language: Language code
        
    Returns:
        Hotel reviews
    """
    try:
        logger.info(f"Hotel reviews requested for hotel ID: {hotel_id}")
        
        result = hotel_client.get_hotel_reviews(
            hotel_id=hotel_id,
            page=page,
            language=language
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"Hotel reviews error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel reviews: {str(e)}")

@router.get("/booking-url/{hotel_id}")
async def generate_hotel_booking_url(
    hotel_id: str,
    check_in: str = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: str = Query(..., description="Check-out date (YYYY-MM-DD)"),
    adults: int = Query(1, description="Number of adult guests"),
    children: Optional[str] = Query("", description="Children ages (comma-separated)"),
    rooms: int = Query(1, description="Number of rooms"),
    currency: str = Query("USD", description="Currency code")
):
    """
    Generate a booking URL for a hotel
    
    Args:
        hotel_id: Hotel ID
        check_in: Check-in date
        check_out: Check-out date
        adults: Number of adult guests
        children: Children ages (comma-separated)
        rooms: Number of rooms
        currency: Currency code
        
    Returns:
        Booking URL for the hotel
    """
    try:
        # Parse children ages
        children_ages = []
        if children:
            try:
                children_ages = [int(age.strip()) for age in children.split(",") if age.strip()]
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid children ages format")
        
        logger.info(f"Hotel booking URL requested for hotel ID: {hotel_id}")
        
        booking_url = hotel_client.generate_hotel_booking_url(
            hotel_id=hotel_id,
            check_in=check_in,
            check_out=check_out,
            adults=adults,
            children=children_ages,
            rooms=rooms,
            currency=currency
        )
        
        return {"booking_url": booking_url}
        
    except Exception as e:
        logger.error(f"Hotel booking URL error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate booking URL: {str(e)}")

@router.get("/popular-destinations")
async def get_popular_destinations():
    """
    Get list of popular hotel destinations
    
    Returns:
        List of popular destinations
    """
    try:
        logger.info("Popular destinations requested")
        
        # This would typically call an API endpoint for popular destinations
        # For now, return a static list
        popular_destinations = [
            {"name": "New York", "country": "United States", "dest_id": "20088325"},
            {"name": "London", "country": "United Kingdom", "dest_id": "-2601889"},
            {"name": "Paris", "country": "France", "dest_id": "-1456928"},
            {"name": "Tokyo", "country": "Japan", "dest_id": "-246227"},
            {"name": "Dubai", "country": "United Arab Emirates", "dest_id": "-782831"},
            {"name": "Singapore", "country": "Singapore", "dest_id": "-73635"},
            {"name": "Barcelona", "country": "Spain", "dest_id": "-37287"},
            {"name": "Rome", "country": "Italy", "dest_id": "-126693"},
            {"name": "Amsterdam", "country": "Netherlands", "dest_id": "-2140479"},
            {"name": "Sydney", "country": "Australia", "dest_id": "-3040055"}
        ]
        
        return {"destinations": popular_destinations}
        
    except Exception as e:
        logger.error(f"Popular destinations error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get popular destinations: {str(e)}")

@router.get("/amenities")
async def get_hotel_amenities():
    """
    Get list of available hotel amenities
    
    Returns:
        List of hotel amenities
    """
    try:
        logger.info("Hotel amenities requested")
        
        amenities = [
            {"id": "wifi", "name": "Free WiFi", "category": "internet"},
            {"id": "parking", "name": "Free Parking", "category": "transportation"},
            {"id": "pool", "name": "Swimming Pool", "category": "recreation"},
            {"id": "gym", "name": "Fitness Center", "category": "recreation"},
            {"id": "spa", "name": "Spa", "category": "wellness"},
            {"id": "restaurant", "name": "Restaurant", "category": "dining"},
            {"id": "bar", "name": "Bar/Lounge", "category": "dining"},
            {"id": "room_service", "name": "Room Service", "category": "dining"},
            {"id": "concierge", "name": "Concierge", "category": "services"},
            {"id": "laundry", "name": "Laundry Service", "category": "services"},
            {"id": "business_center", "name": "Business Center", "category": "business"},
            {"id": "meeting_rooms", "name": "Meeting Rooms", "category": "business"},
            {"id": "airport_shuttle", "name": "Airport Shuttle", "category": "transportation"},
            {"id": "pet_friendly", "name": "Pet Friendly", "category": "policies"},
            {"id": "accessible", "name": "Accessible", "category": "accessibility"}
        ]
        
        return {"amenities": amenities}
        
    except Exception as e:
        logger.error(f"Hotel amenities error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get hotel amenities: {str(e)}") 