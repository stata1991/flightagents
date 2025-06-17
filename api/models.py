from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

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
