#!/usr/bin/env python3
"""
Location Discovery Router
API endpoints for location-based destination discovery
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging
from services.location_detection_service import LocationDetectionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/location-discovery", tags=["location-discovery"])

# Initialize the location detection service
location_service = LocationDetectionService()

@router.get("/detect-location")
async def detect_user_location(
    user_consent: bool = Query(False, description="Whether user has given consent for location detection"),
    ip_address: Optional[str] = Query(None, description="IP address for location detection")
):
    """Detect user's location with proper consent handling."""
    try:
        location = await location_service.detect_user_location_with_consent(
            user_consent=user_consent,
            ip_address=ip_address
        )
        
        return {
            "success": True,
            "location": location,
            "message": "Location detection completed"
        }
    except Exception as e:
        logger.error(f"Error detecting location: {e}")
        raise HTTPException(status_code=500, detail="Location detection failed")

@router.get("/recommendations")
async def get_destination_recommendations(
    user_country: Optional[str] = Query(None, description="User's country (optional, will be detected if not provided)"),
    trip_type: Optional[str] = Query(None, description="Trip type: summer, winter, spring, fall, business, celebration"),
    interests: Optional[str] = Query(None, description="Comma-separated interests: beach, mountains, city, cultural")
):
    """Get personalized destination recommendations based on user location and interests."""
    try:
        # Get user location if not provided
        if not user_country:
            location = await location_service.detect_user_location_with_consent(user_consent=True)
            if location and location.get("consent_given"):
                user_country = location.get("country_code", "default")
            else:
                user_country = "default"
        
        # Parse interests if provided
        interest_list = []
        if interests:
            interest_list = [interest.strip() for interest in interests.split(",")]
        
        # Get destination suggestions
        suggestions = await location_service.get_destination_suggestions(
            country_code=user_country,
            trip_type=trip_type,
            interests=interest_list
        )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "user_country": user_country,
            "trip_type": trip_type,
            "interests": interest_list,
            "message": f"Found {suggestions.get('total_suggestions', 0)} destination suggestions"
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.get("/seasonal-recommendations")
async def get_seasonal_recommendations(
    user_country: Optional[str] = Query(None, description="User's country (optional, will be detected if not provided)"),
    season: Optional[str] = Query(None, description="Season: winter, spring, summer, fall (defaults to current season)")
):
    """Get seasonal destination recommendations."""
    try:
        # Get user location if not provided
        if not user_country:
            location = await location_service.detect_user_location_with_consent(user_consent=True)
            if location and location.get("consent_given"):
                user_country = location.get("country_code", "default")
            else:
                user_country = "default"
        
        recommendations = await location_service.get_seasonal_recommendations(
            country_code=user_country,
            season=season
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "season": season,
            "user_country": user_country,
            "total_count": len(recommendations),
            "message": f"Found {len(recommendations)} seasonal destination recommendations"
        }
        
    except Exception as e:
        logger.error(f"Error getting seasonal recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get seasonal recommendations")

@router.get("/celebration-recommendations")
async def get_celebration_recommendations(
    celebration_type: str = Query(..., description="Celebration type: honeymoon, anniversary, birthday, bachelor_party, family_vacation")
):
    """Get destination recommendations for special celebrations."""
    try:
        recommendations = await location_service.get_celebration_recommendations(celebration_type)
        
        return {
            "success": True,
            "recommendations": recommendations,
            "celebration_type": celebration_type,
            "total_count": len(recommendations),
            "message": f"Found {len(recommendations)} destinations perfect for {celebration_type}"
        }
        
    except Exception as e:
        logger.error(f"Error getting celebration recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get celebration recommendations")

@router.get("/global-suggestions")
async def get_global_suggestions(
    trip_type: Optional[str] = Query(None, description="Trip type: summer, winter, spring, fall, business, celebration"),
    interests: Optional[str] = Query(None, description="Comma-separated interests: beach, mountains, city, cultural")
):
    """Get global destination suggestions when user location is unknown."""
    try:
        # Parse interests if provided
        interest_list = []
        if interests:
            interest_list = [interest.strip() for interest in interests.split(",")]
        
        suggestions = await location_service.get_global_destination_suggestions(
            trip_type=trip_type,
            interests=interest_list
        )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "trip_type": trip_type,
            "interests": interest_list,
            "message": f"Found {suggestions.get('total_suggestions', 0)} global destination suggestions"
        }
        
    except Exception as e:
        logger.error(f"Error getting global suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get global suggestions")

@router.get("/discovery-homepage")
async def get_discovery_homepage_data(
    user_consent: bool = Query(False, description="Whether user has given consent for location detection"),
    lat: Optional[float] = Query(None, description="GPS latitude"),
    lon: Optional[float] = Query(None, description="GPS longitude")
):
    """Get location discovery data for the homepage/interface."""
    try:
        # Detect user location with consent
        location = await location_service.detect_user_location_with_consent(
            user_consent=user_consent,
            gps_coordinates={"lat": lat, "lon": lon} if lat and lon else None
        )
        
        # Get destination suggestions based on location
        country_code = location.get("country_code", "default") if location and location.get("consent_given") else "default"
        
        suggestions = await location_service.get_destination_suggestions(
            country_code=country_code,
            trip_type=None,
            interests=None
        )
        
        return {
            "success": True,
            "user_location": location,
            "domestic_suggestions": suggestions.get("domestic_suggestions", []),
            "international_suggestions": suggestions.get("international_suggestions", []),
            "data_source": suggestions.get("data_source", "dynamic_api"),
            "message": "Location discovery data loaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting discovery homepage data: {e}")
        raise HTTPException(status_code=500, detail="Failed to load discovery data")

@router.get("/health")
async def health_check():
    """Health check endpoint for the location discovery service."""
    return {
        "status": "healthy",
        "service": "location-discovery",
        "message": "Location discovery service is running"
    }