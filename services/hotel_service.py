from typing import Any, Dict
from api.enhanced_ai_provider import EnhancedAITripProvider
from api.trip_planner_interface import TripPlanRequest

class HotelService:
    @staticmethod
    async def get_recommendations(destination: str, start_date: str, end_date: str, travelers: int = 1, budget_range: str = "moderate") -> Dict[str, Any]:
        """
        Fetches hotel recommendations using EnhancedAITripProvider and Booking.com API.
        """
        provider = EnhancedAITripProvider()
        
        # Create TripPlanRequest object
        request = TripPlanRequest(
            origin="",  # Not needed for hotel search
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            duration_days=5,  # Default duration
            travelers=travelers,
            budget_range=budget_range,
            interests=["general"]
        )
        
        return await provider._get_hotel_recommendations(request)
