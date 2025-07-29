from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from .trip_planner_interface import (
    HybridTripPlanner,
    TripPlanRequest,
    TripPlanResponse,
    ProviderType
)
from .enhanced_ai_provider import EnhancedAITripProvider
from .api_trip_provider import APITripProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hybrid", tags=["hybrid-trip-planning"])

# Initialize the hybrid trip planner
hybrid_planner = HybridTripPlanner()

# Register providers
ai_provider = EnhancedAITripProvider()  # Using enhanced AI provider
api_provider = APITripProvider()

# Set AI as default provider (can be easily changed)
hybrid_planner.register_provider(ai_provider, is_default=True)
hybrid_planner.register_provider(api_provider)

class HybridTripRequest(BaseModel):
    """Request model for hybrid trip planning"""
    origin: str
    destination: str
    duration_days: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    travelers: int = 1
    budget_range: str = "moderate"  # budget, moderate, luxury
    interests: List[str] = []
    trip_type: str = "leisure"
    special_requirements: Optional[str] = None
    preferred_provider: Optional[str] = None  # "ai", "api", or None for auto

class ProviderInfoResponse(BaseModel):
    """Response model for provider information"""
    providers: List[Dict[str, Any]]
    default_provider: str
    system_status: str

@router.post("/plan", response_model=Dict[str, Any])
async def plan_trip(request: HybridTripRequest) -> Dict[str, Any]:
    """
    Plan a trip using the hybrid system (AI-first with API fallback)
    """
    try:
        # Convert to internal request format
        trip_request = TripPlanRequest(
            origin=request.origin,
            destination=request.destination,
            duration_days=request.duration_days,
            start_date=request.start_date,
            end_date=request.end_date,
            travelers=request.travelers,
            budget_range=request.budget_range,
            interests=request.interests,
            trip_type=request.trip_type,
            special_requirements=request.special_requirements,
            preferred_provider=ProviderType(request.preferred_provider) if request.preferred_provider else None
        )
        
        # Plan the trip
        response = await hybrid_planner.plan_trip(trip_request)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": response.error_message,
                    "metadata": response.metadata.dict()
                }
            )
        
        # Return the response with additional context
        return {
            "success": True,
            "itinerary": response.itinerary,
            "metadata": response.metadata.dict(),
            "booking_links": response.booking_links,
            "estimated_costs": response.estimated_costs,
            "warnings": response.warnings,
            "provider_used": response.metadata.provider,
            "fallback_used": response.metadata.fallback_used
        }
        
    except Exception as e:
        logger.error(f"Hybrid trip planning failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Trip planning failed: {str(e)}"
        )

@router.get("/providers", response_model=ProviderInfoResponse)
async def get_providers() -> ProviderInfoResponse:
    """
    Get information about available trip planning providers
    """
    try:
        providers_info = hybrid_planner.get_available_providers()
        
        return ProviderInfoResponse(
            providers=providers_info,
            default_provider=hybrid_planner.default_provider.get_provider_type() if hybrid_planner.default_provider else "none",
            system_status="operational"
        )
        
    except Exception as e:
        logger.error(f"Failed to get provider info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get provider information: {str(e)}"
        )

@router.post("/test-ai")
async def test_ai_provider() -> Dict[str, Any]:
    """
    Test the AI provider with a simple request
    """
    try:
        test_request = TripPlanRequest(
            origin="New York",
            destination="Paris",
            duration_days=3,
            travelers=2,
            budget_range="moderate",
            interests=["food", "culture"],
            trip_type="leisure",
            preferred_provider=ProviderType.AI
        )
        
        response = await hybrid_planner.plan_trip(test_request)
        
        return {
            "success": response.success,
            "provider_used": response.metadata.provider,
            "quality": response.metadata.quality,
            "confidence_score": response.metadata.confidence_score,
            "has_itinerary": bool(response.itinerary),
            "error": response.error_message if not response.success else None
        }
        
    except Exception as e:
        logger.error(f"AI provider test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/test-api")
async def test_api_provider() -> Dict[str, Any]:
    """
    Test the API provider with a simple request
    """
    try:
        test_request = TripPlanRequest(
            origin="New York",
            destination="London",
            duration_days=2,
            travelers=1,
            budget_range="moderate",
            interests=["sightseeing"],
            trip_type="leisure",
            preferred_provider=ProviderType.API
        )
        
        response = await hybrid_planner.plan_trip(test_request)
        
        return {
            "success": response.success,
            "provider_used": response.metadata.provider,
            "quality": response.metadata.quality,
            "confidence_score": response.metadata.confidence_score,
            "has_itinerary": bool(response.itinerary),
            "error": response.error_message if not response.success else None
        }
        
    except Exception as e:
        logger.error(f"API provider test failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/switch-default")
async def switch_default_provider(provider_type: str) -> Dict[str, Any]:
    """
    Switch the default provider (for testing and configuration)
    """
    try:
        if provider_type == "ai":
            hybrid_planner.default_provider = ai_provider
        elif provider_type == "api":
            hybrid_planner.default_provider = api_provider
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid provider type. Use 'ai' or 'api'"
            )
        
        return {
            "success": True,
            "new_default": provider_type,
            "message": f"Default provider switched to {provider_type}"
        }
        
    except Exception as e:
        logger.error(f"Failed to switch default provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to switch default provider: {str(e)}"
        ) 