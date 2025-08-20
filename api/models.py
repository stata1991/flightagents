from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class DateRange(BaseModel):
    outbound: List[str]
    return_dates: Optional[List[str]] = None

class SearchRequest(BaseModel):
    trip_type: str = Field(..., description="Type of trip: 'one-way' or 'round-trip'")
    origin: str = Field(..., description="Origin airport code")
    destination: str = Field(..., description="Destination airport code")
    date_range: DateRange
    flex_days: Optional[int] = Field(0, description="Number of flexible days")
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "non_stop_only": False,
            "max_price": None,
            "preferred_airlines": [],
            "max_stops": None
        },
        description="Search filters"
    )

class SearchResponse(BaseModel):
    trip_type: str
    origin: str
    destination: str
    date_range: DateRange
    results: Dict[str, Dict[str, List[Dict[str, Any]]]]

# Hotel-specific models
class HotelSearchRequest(BaseModel):
    location: str = Field(..., description="Destination location (city, country)")
    check_in: str = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out: str = Field(..., description="Check-out date (YYYY-MM-DD)")
    adults: int = Field(1, description="Number of adult guests")
    children: Optional[List[int]] = Field([], description="Ages of children")
    rooms: int = Field(1, description="Number of rooms")
    currency: str = Field("USD", description="Currency code")
    language: str = Field("en-us", description="Language code")
    page_number: int = Field(1, description="Page number for pagination")
    checkin_month: Optional[int] = Field(None, description="Check-in month")
    checkin_year: Optional[int] = Field(None, description="Check-in year")
    checkout_month: Optional[int] = Field(None, description="Check-out month")
    checkout_year: Optional[int] = Field(None, description="Check-out year")
    adults_number: Optional[int] = Field(None, description="Number of adults")
    children_number: Optional[int] = Field(0, description="Number of children")
    children_ages: Optional[List[int]] = Field([], description="Ages of children")
    room_number: Optional[int] = Field(1, description="Number of rooms")
    dest_type: Optional[str] = Field("CITY", description="Destination type")
    dest_id: Optional[str] = Field(None, description="Destination ID")
    search_type: Optional[str] = Field("CITY", description="Search type")
    order: Optional[str] = Field("price", description="Sort order")
    units: Optional[str] = Field("metric", description="Units")
    room1: Optional[str] = Field(None, description="Room 1 configuration")
    no_rooms: Optional[int] = Field(1, description="Number of rooms")
    group_total: Optional[int] = Field(None, description="Total group size")
    from_sf: Optional[bool] = Field(False, description="From search form")
    selected_currency: Optional[str] = Field("USD", description="Selected currency")

class HotelInfo(BaseModel):
    hotel_id: str
    name: str
    address: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_score: Optional[float] = None
    review_count: Optional[int] = None
    star_rating: Optional[int] = None
    property_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    description: Optional[str] = None
    booking_url: Optional[str] = None

class HotelRoom(BaseModel):
    room_id: str
    room_type: str
    bed_configuration: Optional[str] = None
    max_occupancy: Optional[int] = None
    cancellation_policy: Optional[str] = None
    meal_plan: Optional[str] = None
    price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    availability: bool = True

class HotelSearchResult(BaseModel):
    hotel: HotelInfo
    rooms: List[HotelRoom]
    average_price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    availability: bool = True

class HotelSearchResponse(BaseModel):
    location: str
    check_in: str
    check_out: str
    total_results: int
    hotels: List[HotelSearchResult]
    search_metadata: Optional[Dict[str, Any]] = None

# New models for AI Trip Planner
class TripType(str, Enum):
    LEISURE = "leisure"
    FAMILY = "family"
    SOLO = "solo"
    BUSINESS = "business"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    ROMANTIC = "romantic"

class BudgetRange(str, Enum):
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"

class TripPlanningRequest(BaseModel):
    origin: str = Field(..., description="Origin city/airport")
    destination: str = Field(..., description="Destination country/region")
    duration_days: Optional[int] = Field(None, description="Number of days for the trip")
    start_date: Optional[str] = Field(None, description="Preferred start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Preferred end date (YYYY-MM-DD)")
    travelers: Optional[int] = Field(None, description="Number of travelers")
    trip_type: TripType = Field(TripType.LEISURE, description="Type of trip")
    budget_range: Optional[BudgetRange] = Field(None, description="Budget preference")
    interests: Optional[List[str]] = Field([], description="Specific interests (food, art, history, etc.)")
    special_requirements: Optional[str] = Field(None, description="Any special requirements")
    total_budget: Optional[float] = Field(None, description="User's total numeric budget, if provided")

    @validator('trip_type', pre=True)
    def validate_trip_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('budget_range', pre=True)
    def validate_budget_range(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('duration_days', pre=True)
    def validate_duration_days(cls, v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v)
            except Exception:
                return None
        return None

class ConversationState(BaseModel):
    session_id: str
    current_step: str = "initial_request"
    trip_request: Optional[TripPlanningRequest] = None
    itinerary: Optional[Dict[str, Any]] = None
    refinement_count: int = 0
    max_refinements: int = 5
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    # Track which fields have been explicitly provided by the user
    provided_fields: List[str] = Field(default_factory=list)

class FollowUpQuestion(BaseModel):
    question: str
    field_name: str
    field_type: str  # "date", "number", "text", "choice"
    choices: Optional[List[str]] = None
    required: bool = True

class ItineraryResponse(BaseModel):
    session_id: str
    itinerary: Dict[str, Any]
    summary: str
    estimated_cost: Dict[str, float]
    next_actions: List[str]
    can_refine: bool = True

class RefinementRequest(BaseModel):
    session_id: str
    changes: Dict[str, Any] = Field(..., description="Requested changes to the itinerary")
    reason: Optional[str] = Field(None, description="Reason for the changes")

class BookingSummary(BaseModel):
    session_id: str
    flights: List[Dict[str, Any]]
    hotels: List[Dict[str, Any]]
    total_cost: float
    booking_links: Dict[str, str]
    itinerary_summary: str
