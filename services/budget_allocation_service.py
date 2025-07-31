#!/usr/bin/env python3
"""
Budget Allocation Service
Handles smart budget allocation with 30-35% for hotels.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class BudgetAllocationService:
    """Service for smart budget allocation and hotel recommendations."""
    
    def __init__(self):
        self.hotel_budget_percentage = 0.325  # 32.5% (middle of 30-35% range)
        self.min_hotel_percentage = 0.30
        self.max_hotel_percentage = 0.35
    
    def calculate_budget_allocation(self, total_budget: float, trip_duration: int, travelers: int) -> Dict[str, Any]:
        """
        Calculate smart budget allocation with 30-35% for hotels.
        
        Args:
            total_budget: Total trip budget in USD
            trip_duration: Number of days
            travelers: Number of travelers
            
        Returns:
            Dictionary with budget breakdown and percentages
        """
        try:
            # Calculate hotel budget (30-35% of total)
            hotel_budget = total_budget * self.hotel_budget_percentage
            
            # Calculate per-night hotel budget
            hotel_budget_per_night = hotel_budget / trip_duration
            
            # Calculate per-person hotel budget
            hotel_budget_per_person = hotel_budget_per_night / travelers
            
            # Allocate remaining budget to other categories
            remaining_budget = total_budget - hotel_budget
            
            # Typical allocation for remaining budget:
            # Flights: 40% of remaining
            # Meals: 30% of remaining  
            # Activities: 30% of remaining
            flight_budget = remaining_budget * 0.40
            meal_budget = remaining_budget * 0.30
            activity_budget = remaining_budget * 0.30
            
            # Calculate percentages
            hotel_percentage = (hotel_budget / total_budget) * 100
            flight_percentage = (flight_budget / total_budget) * 100
            meal_percentage = (meal_budget / total_budget) * 100
            activity_percentage = (activity_budget / total_budget) * 100
            
            return {
                "budget_breakdown": {
                    "flights": f"${flight_budget:.0f}",
                    "accommodation": f"${hotel_budget:.0f}",
                    "meals": f"${meal_budget:.0f}",
                    "activities": f"${activity_budget:.0f}"
                },
                "budget_percentages": {
                    "flights": f"{flight_percentage:.1f}%",
                    "accommodation": f"{hotel_percentage:.1f}%",
                    "meals": f"{meal_percentage:.1f}%",
                    "activities": f"{activity_percentage:.1f}%"
                },
                "total_estimated_cost": f"${total_budget:.0f}",
                "hotel_budget_allocation": {
                    "allocated_amount": f"${hotel_budget:.0f}",
                    "percentage": f"{hotel_percentage:.1f}%",
                    "per_night": f"${hotel_budget_per_night:.0f}",
                    "per_person_per_night": f"${hotel_budget_per_person:.0f}",
                    "recommendation": f"Hotels within ${hotel_budget_per_night:.0f}/night budget"
                },
                "budget_optimization": {
                    "hotel_recommendations": f"Focus on hotels under ${hotel_budget_per_night:.0f}/night",
                    "flight_optimization": "Balance cost vs convenience",
                    "activity_budgeting": "Prioritize must-see attractions"
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating budget allocation: {e}")
            return None
    
    def get_hotel_price_range(self, total_budget: float, trip_duration: int, travelers: int) -> Dict[str, Any]:
        """
        Get recommended hotel price range based on budget allocation.
        
        Args:
            total_budget: Total trip budget
            trip_duration: Number of days
            travelers: Number of travelers
            
        Returns:
            Dictionary with hotel price recommendations
        """
        allocation = self.calculate_budget_allocation(total_budget, trip_duration, travelers)
        
        if not allocation:
            return None
        
        hotel_budget = float(allocation["hotel_budget_allocation"]["allocated_amount"].replace("$", ""))
        per_night = float(allocation["hotel_budget_allocation"]["per_night"].replace("$", ""))
        
        # Calculate price ranges (suggest hotels within 80-120% of budget)
        min_price = per_night * 0.8
        max_price = per_night * 1.2
        
        return {
            "budget_range": {
                "min_price": f"${min_price:.0f}",
                "max_price": f"${max_price:.0f}",
                "target_price": f"${per_night:.0f}"
            },
            "hotel_recommendations": {
                "budget_tier": "mid-range" if per_night < 200 else "luxury",
                "suggested_types": self._get_hotel_types_by_budget(per_night),
                "booking_tips": self._get_booking_tips_by_budget(per_night)
            },
            "budget_allocation": allocation
        }
    
    def _get_hotel_types_by_budget(self, price_per_night: float) -> List[str]:
        """Get suggested hotel types based on budget."""
        if price_per_night < 100:
            return ["Hostels", "Budget hotels", "Short-term rentals"]
        elif price_per_night < 200:
            return ["Mid-range hotels", "Boutique hotels", "Short-term rentals"]
        elif price_per_night < 400:
            return ["Upscale hotels", "Resorts", "Boutique hotels"]
        else:
            return ["Luxury hotels", "Resorts", "Premium accommodations"]
    
    def _get_booking_tips_by_budget(self, price_per_night: float) -> List[str]:
        """Get booking tips based on budget."""
        tips = [
            "Book 3-6 months in advance for best rates",
            "Consider flexible dates for better prices",
            "Look for package deals with flights"
        ]
        
        if price_per_night < 150:
            tips.extend([
                "Check for student/AAA discounts",
                "Consider alternative accommodations (hostels, rentals)",
                "Book during off-peak seasons"
            ])
        elif price_per_night > 300:
            tips.extend([
                "Look for luxury hotel packages",
                "Consider loyalty programs for upgrades",
                "Book through premium travel agencies"
            ])
        
        return tips
    
    def validate_hotel_recommendations(self, hotels: List[Dict], budget_range: Dict) -> Dict[str, Any]:
        """
        Validate if hotel recommendations fit within budget allocation.
        
        Args:
            hotels: List of hotel recommendations
            budget_range: Budget allocation data
            
        Returns:
            Dictionary with validation results and filtered hotels
        """
        target_price = float(budget_range["budget_range"]["target_price"].replace("$", ""))
        min_price = float(budget_range["budget_range"]["min_price"].replace("$", ""))
        max_price = float(budget_range["budget_range"]["max_price"].replace("$", ""))
        
        budget_friendly_hotels = []
        over_budget_hotels = []
        
        for hotel in hotels:
            # Extract price from hotel data (this would need to match your hotel data structure)
            hotel_price = self._extract_hotel_price(hotel)
            
            if hotel_price and min_price <= hotel_price <= max_price:
                budget_friendly_hotels.append(hotel)
            elif hotel_price:
                over_budget_hotels.append(hotel)
        
        return {
            "budget_friendly_count": len(budget_friendly_hotels),
            "over_budget_count": len(over_budget_hotels),
            "budget_friendly_hotels": budget_friendly_hotels,
            "over_budget_hotels": over_budget_hotels,
            "budget_compliance": f"{len(budget_friendly_hotels)}/{len(hotels)} hotels within budget"
        }
    
    def _extract_hotel_price(self, hotel: Dict) -> Optional[float]:
        """Extract price from hotel data (placeholder - adjust based on your hotel data structure)."""
        # This would need to be adjusted based on your actual hotel data structure
        if "price" in hotel:
            return float(hotel["price"])
        elif "cost" in hotel:
            return float(hotel["cost"])
        elif "rate" in hotel:
            return float(hotel["rate"])
        return None
    
    def generate_budget_report(self, total_budget: float, trip_duration: int, travelers: int, 
                             hotels: List[Dict] = None) -> Dict[str, Any]:
        """
        Generate comprehensive budget report with hotel recommendations.
        
        Args:
            total_budget: Total trip budget
            trip_duration: Number of days
            travelers: Number of travelers
            hotels: Optional list of hotel recommendations
            
        Returns:
            Complete budget report
        """
        allocation = self.calculate_budget_allocation(total_budget, trip_duration, travelers)
        price_range = self.get_hotel_price_range(total_budget, trip_duration, travelers)
        
        report = {
            "budget_allocation": allocation,
            "hotel_price_range": price_range,
            "cost_saving_tips": [
                "Book flights 3-4 months early for best rates",
                "Use public transport city passes to save on transportation",
                "Stay in boutique hotels or short-term rentals for better value",
                "Consider all-inclusive packages for predictable costs",
                "Travel during shoulder seasons for lower prices"
            ]
        }
        
        if hotels:
            validation = self.validate_hotel_recommendations(hotels, price_range)
            report["hotel_validation"] = validation
        
        return report 