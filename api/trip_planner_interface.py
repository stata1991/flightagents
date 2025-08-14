from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator
from enum import Enum

class ProviderType(str, Enum):
    AI = "ai"
    API = "api"
    HYBRID = "hybrid"

class TripPlanQuality(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    BASIC = "basic"
    UNKNOWN = "unknown"

class TripPlanMetadata(BaseModel):
    """Metadata about the trip plan including quality indicators"""
    provider: ProviderType
    quality: TripPlanQuality
    confidence_score: float  # 0.0 to 1.0
    data_freshness: str  # "real_time", "recent", "static"
    last_updated: str
    source_notes: List[str] = []
    fallback_used: bool = False

class TripPlanRequest(BaseModel):
    """Standardized request format for all trip planners"""
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
    preferred_provider: Optional[ProviderType] = None
    smart_trip_data: Optional[Dict[str, Any]] = None  # Smart trip logic data

class TripPlanResponse(BaseModel):
    """Standardized response format for all trip planners"""
    success: bool
    itinerary: Dict[str, Any]
    metadata: TripPlanMetadata
    error_message: Optional[str] = None
    warnings: List[str] = []
    booking_links: Dict[str, str] = {}
    estimated_costs: Dict[str, Any] = {}  # Changed from float to Any to handle string values
    
    @validator('estimated_costs', pre=True)
    def convert_cost_strings(cls, v):
        """Convert string costs like '$32' to float values"""
        if isinstance(v, dict):
            converted = {}
            for key, value in v.items():
                if isinstance(value, str):
                    # Remove dollar sign and convert to float
                    clean_value = value.replace('$', '').replace(',', '')
                    try:
                        converted[key] = float(clean_value)
                    except ValueError:
                        converted[key] = value  # Keep as string if conversion fails
                else:
                    converted[key] = value
            return converted
        return v

class TripPlannerProvider(ABC):
    """Abstract base class for all trip planning providers"""
    
    @abstractmethod
    async def plan_trip(self, request: TripPlanRequest) -> TripPlanResponse:
        """Generate a trip plan"""
        pass
    
    @abstractmethod
    def get_provider_type(self) -> ProviderType:
        """Return the type of this provider"""
        pass
    
    @abstractmethod
    def get_quality_estimate(self) -> TripPlanQuality:
        """Estimate the quality of plans this provider can generate"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is currently available"""
        pass

class HybridTripPlanner:
    """Main coordinator that manages multiple providers"""
    
    def __init__(self):
        self.providers: List[TripPlannerProvider] = []
        self.default_provider: Optional[TripPlannerProvider] = None
    
    def register_provider(self, provider: TripPlannerProvider, is_default: bool = False):
        """Register a trip planning provider"""
        self.providers.append(provider)
        if is_default:
            self.default_provider = provider
    
    async def plan_trip(self, request: TripPlanRequest) -> TripPlanResponse:
        """Plan a trip using the best available provider"""
        
        # Determine which provider to use
        provider = self._select_provider(request)
        
        if not provider:
            return TripPlanResponse(
                success=False,
                itinerary={},
                metadata=TripPlanMetadata(
                    provider=ProviderType.HYBRID,
                    quality=TripPlanQuality.UNKNOWN,
                    confidence_score=0.0,
                    data_freshness="unknown",
                    last_updated="",
                    source_notes=["No available providers"]
                ),
                error_message="No trip planning providers are available"
            )
        
        try:
            # Try the selected provider
            response = await provider.plan_trip(request)
            
            # If successful, return the response
            if response.success:
                return response
            
            # If failed, try fallback providers
            return await self._try_fallback_providers(request, provider)
            
        except Exception as e:
            # Try fallback providers on any error
            return await self._try_fallback_providers(request, provider, str(e))
    
    def _select_provider(self, request: TripPlanRequest) -> Optional[TripPlannerProvider]:
        """Select the best provider based on request preferences"""
        
        # If user specified a preferred provider, try to use it
        if request.preferred_provider:
            for provider in self.providers:
                if (provider.get_provider_type() == request.preferred_provider and 
                    provider.is_available()):
                    return provider
        
        # Otherwise, use the default provider
        if self.default_provider and self.default_provider.is_available():
            return self.default_provider
        
        # Fallback to any available provider
        for provider in self.providers:
            if provider.is_available():
                return provider
        
        return None
    
    async def _try_fallback_providers(self, request: TripPlanRequest, 
                                    failed_provider: TripPlannerProvider, 
                                    error_msg: str = "") -> TripPlanResponse:
        """Try other providers if the primary one fails"""
        
        for provider in self.providers:
            if provider == failed_provider:
                continue
            
            if not provider.is_available():
                continue
            
            try:
                response = await provider.plan_trip(request)
                if response.success:
                    # Mark that we used a fallback
                    response.metadata.fallback_used = True
                    response.metadata.source_notes.append(
                        f"Primary provider failed: {error_msg}. Using fallback: {provider.get_provider_type()}"
                    )
                    return response
            except Exception as e:
                continue
        
        # All providers failed
        return TripPlanResponse(
            success=False,
            itinerary={},
            metadata=TripPlanMetadata(
                provider=ProviderType.HYBRID,
                quality=TripPlanQuality.UNKNOWN,
                confidence_score=0.0,
                data_freshness="unknown",
                last_updated="",
                source_notes=[f"All providers failed. Last error: {error_msg}"]
            ),
            error_message=f"All trip planning providers failed. Last error: {error_msg}"
        )
    
    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get information about available providers"""
        providers_info = []
        for provider in self.providers:
            providers_info.append({
                "type": provider.get_provider_type(),
                "quality": provider.get_quality_estimate(),
                "available": provider.is_available()
            })
        return providers_info 