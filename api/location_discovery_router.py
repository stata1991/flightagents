#!/usr/bin/env python3
"""
Location Discovery Router
Handles user consent-based location detection and provides dynamic destination recommendations.
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
import aiohttp

# Add the services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

from location_detection_service import LocationDetectionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/location", tags=["Location Discovery"])

class LocationConsentRequest(BaseModel):
    """Request model for location consent."""
    user_consent: bool = False
    gps_coordinates: Optional[Dict[str, float]] = None
    ip_address: Optional[str] = None
    trip_type: Optional[str] = None
    interests: Optional[List[str]] = None

class LocationConsentResponse(BaseModel):
    """Response model for location consent."""
    success: bool
    location_info: Dict[str, Any]
    destination_suggestions: Dict[str, Any]
    message: str

class DiscoveryHomepageRequest(BaseModel):
    """Request model for discovery homepage."""
    user_consent: bool = False
    gps_coordinates: Optional[Dict[str, float]] = None
    ip_address: Optional[str] = None
    trip_type: Optional[str] = None
    interests: Optional[List[str]] = None

class DiscoveryHomepageResponse(BaseModel):
    """Response model for discovery homepage."""
    success: bool
    user_location: Dict[str, Any]
    domestic_suggestions: List[Dict[str, Any]]
    international_suggestions: List[Dict[str, Any]]
    seasonal_recommendations: List[Dict[str, Any]]
    celebration_recommendations: List[Dict[str, Any]]
    data_source: str
    message: str

@router.post("/consent", response_model=LocationConsentResponse)
async def handle_location_consent(request: LocationConsentRequest, client_request: Request):
    """
    Handle user location consent and provide personalized recommendations.
    
    This endpoint:
    1. Respects user consent for location detection
    2. Uses GPS coordinates if provided with consent
    3. Falls back to IP-based detection if consented
    4. Provides default suggestions if no consent given
    5. Returns dynamic destination recommendations
    """
    try:
        logger.info(f"Location consent request received: consent={request.user_consent}, has_gps={bool(request.gps_coordinates)}")
        
        # Initialize location detection service
        location_service = LocationDetectionService()
        
        # Get client IP if not provided
        if not request.ip_address:
            request.ip_address = client_request.client.host
        
        # Detect user location with consent
        location_info = await location_service.detect_user_location_with_consent(
            user_consent=request.user_consent,
            gps_coordinates=request.gps_coordinates,
            ip_address=request.ip_address
        )
        
        logger.info(f"Location detected: {location_info['country']} ({location_info['country_code']}) via {location_info['detection_method']}")
        
        # Get destination suggestions based on detected location
        country_code = location_info.get("country_code", "default")
        
        if country_code == "default" or not request.user_consent:
            # No consent or unknown location - provide global suggestions
            destination_suggestions = await location_service.get_global_destination_suggestions(
                trip_type=request.trip_type,
                interests=request.interests
            )
        else:
            # User consented and location detected - provide personalized suggestions
            destination_suggestions = await location_service.get_destination_suggestions(
                country_code=country_code,
                trip_type=request.trip_type,
                interests=request.interests
            )
        
        return LocationConsentResponse(
            success=True,
            location_info=location_info,
            destination_suggestions=destination_suggestions,
            message=f"Location-based recommendations generated successfully. Data source: {destination_suggestions.get('data_source', 'unknown')}"
        )
        
    except Exception as e:
        logger.error(f"Error handling location consent: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process location consent: {str(e)}")

@router.get("/discovery-homepage", response_model=DiscoveryHomepageResponse)
async def get_discovery_homepage(
    user_consent: bool = Query(False, description="Whether user has given consent for location detection"),
    lat: Optional[float] = Query(None, description="GPS latitude"),
    lon: Optional[float] = Query(None, description="GPS longitude"),
    trip_type: Optional[str] = Query(None, description="Type of trip (summer, winter, celebration, business, etc.)"),
    interests: Optional[str] = Query(None, description="Comma-separated list of interests"),
    client_request: Request = None
):
    """
    Get comprehensive discovery homepage data with location-based recommendations.
    
    This endpoint provides:
    - User location detection (with consent)
    - Domestic destination suggestions
    - International destination suggestions
    - Seasonal recommendations
    - Celebration-specific recommendations
    
    Query Parameters:
    - user_consent: Whether user has given consent
    - lat, lon: GPS coordinates (if provided with consent)
    - trip_type: Type of trip for filtering
    - interests: Comma-separated interests for filtering
    """
    try:
        logger.info(f"Discovery homepage request: consent={user_consent}, has_gps={lat is not None and lon is not None}")
        
        # Initialize location detection service
        location_service = LocationDetectionService()
        
        # Parse interests
        interests_list = None
        if interests:
            interests_list = [interest.strip() for interest in interests.split(",")]
        
        # Prepare GPS coordinates
        gps_coordinates = None
        if user_consent and lat is not None and lon is not None:
            gps_coordinates = {"lat": lat, "lon": lon}
        
        # Get client IP
        client_ip = client_request.client.host if client_request else None
        
        # Detect user location with consent
        location_info = await location_service.detect_user_location_with_consent(
            user_consent=user_consent,
            gps_coordinates=gps_coordinates,
            ip_address=client_ip
        )
        
        logger.info(f"Location detected for homepage: {location_info['country']} ({location_info['country_code']})")
        
        # Get comprehensive destination suggestions
        country_code = location_info.get("country_code", "default")
        
        if country_code == "default" or not user_consent:
            # No consent or unknown location - provide global suggestions
            destination_suggestions = await location_service.get_global_destination_suggestions(
                trip_type=trip_type,
                interests=interests_list
            )
            
            domestic_suggestions = []
            international_suggestions = destination_suggestions.get("global_suggestions", [])
            data_source = destination_suggestions.get("data_source", "fallback")
            
        else:
            # User consented and location detected - provide personalized suggestions
            destination_suggestions = await location_service.get_destination_suggestions(
                country_code=country_code,
                trip_type=trip_type,
                interests=interests_list
            )
            
            domestic_suggestions = destination_suggestions.get("domestic_suggestions", [])
            international_suggestions = destination_suggestions.get("international_suggestions", [])
            data_source = destination_suggestions.get("data_source", "fallback")
        
        # Get seasonal recommendations
        seasonal_recommendations = await location_service.get_seasonal_recommendations(
            country_code=country_code,
            season=trip_type if trip_type and trip_type.lower() in ["summer", "winter", "spring", "fall"] else None
        )
        
        # Get celebration recommendations
        celebration_recommendations = await location_service.get_celebration_recommendations(
            celebration_type=trip_type if trip_type and trip_type.lower() in ["birthday", "anniversary", "honeymoon", "babymoon"] else None
        )
        
        return DiscoveryHomepageResponse(
            success=True,
            user_location=location_info,
            domestic_suggestions=domestic_suggestions,
            international_suggestions=international_suggestions,
            seasonal_recommendations=seasonal_recommendations,
            celebration_recommendations=celebration_recommendations,
            data_source=data_source,
            message=f"Discovery homepage data generated successfully. Location: {location_info['country']} ({location_info['detection_method']})"
        )
        
    except Exception as e:
        logger.error(f"Error getting discovery homepage data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get discovery homepage data")

@router.get("/suggestions")
async def get_destination_suggestions(
    country_code: str = Query("default", description="Country code for suggestions"),
    trip_type: Optional[str] = Query(None, description="Type of trip"),
    interests: Optional[str] = Query(None, description="Comma-separated interests")
):
    """
    Get destination suggestions for a specific country.
    
    This endpoint provides dynamic destination suggestions based on:
    - Country code
    - Trip type filtering
    - Interest-based filtering
    """
    try:
        logger.info(f"Destination suggestions request: country={country_code}, trip_type={trip_type}")
        
        # Initialize location detection service
        location_service = LocationDetectionService()
        
        # Parse interests
        interests_list = None
        if interests:
            interests_list = [interest.strip() for interest in interests.split(",")]
        
        # Get suggestions
        if country_code == "global" or country_code == "default":
            suggestions = await location_service.get_global_destination_suggestions(
                trip_type=trip_type,
                interests=interests_list
            )
        else:
            suggestions = await location_service.get_destination_suggestions(
                country_code=country_code,
                trip_type=trip_type,
                interests=interests_list
            )
        
        return {
            "success": True,
            "suggestions": suggestions,
            "message": f"Destination suggestions generated for {country_code}"
        }
        
    except Exception as e:
        logger.error(f"Error getting destination suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get destination suggestions")

@router.get("/seasonal")
async def get_seasonal_recommendations(
    country_code: str = Query("default", description="Country code"),
    season: str = Query(..., description="Season (summer, winter, spring, fall)")
):
    """
    Get seasonal destination recommendations.
    """
    try:
        logger.info(f"Seasonal recommendations request: country={country_code}, season={season}")
        
        location_service = LocationDetectionService()
        
        recommendations = await location_service.get_seasonal_recommendations(
            country_code=country_code,
            season=season
        )
        
        return {
            "success": True,
            "season": season,
            "country_code": country_code,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting seasonal recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get seasonal recommendations")

@router.get("/celebration")
async def get_celebration_recommendations(
    celebration_type: str = Query(..., description="Celebration type (birthday, anniversary, honeymoon, babymoon)")
):
    """
    Get celebration-specific destination recommendations.
    """
    try:
        logger.info(f"Celebration recommendations request: type={celebration_type}")
        
        location_service = LocationDetectionService()
        
        recommendations = await location_service.get_celebration_recommendations(
            celebration_type=celebration_type
        )
        
        return {
            "success": True,
            "celebration_type": celebration_type,
            "recommendations": recommendations,
            "count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error getting celebration recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get celebration recommendations")
