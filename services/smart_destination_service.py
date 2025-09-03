#!/usr/bin/env python3
"""
Smart Destination Service
Uses real APIs to get airport and destination information dynamically.
"""

import os
import aiohttp
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SmartDestinationService:
    """Service for smart destination and airport logic using real APIs."""
    
    def __init__(self):
        self.rapid_api_key = os.getenv("RAPID_API_KEY")
        if not self.rapid_api_key:
            logger.error("RAPID_API_KEY not found")
        
        # Initialize maps and weather service for dynamic analysis
        try:
            from .maps_weather_service import MapsWeatherService
            self.maps_weather_service = MapsWeatherService()
            logger.info("Maps and Weather service initialized")
        except ImportError:
            self.maps_weather_service = None
            logger.warning("Maps and Weather service not available - using fallback methods")
    
    async def get_airports_near_destination(self, destination: str) -> Optional[Dict[str, Any]]:
        """
        Get airports near a destination using real API calls.
        """
        try:
            # Use the existing flight search API to find airports
            url = "https://booking-com15.p.rapidapi.com/api/v1/flights/searchDestination"
            
            headers = {
                "X-RapidAPI-Key": self.rapid_api_key,
                "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
            }
            
            params = {"query": destination}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get("status") and result.get("data"):
                            airports = []
                            cities = []
                            
                            for item in result["data"]:
                                if item.get("type") == "AIRPORT":
                                    airports.append({
                                        "id": item.get("id"),
                                        "name": item.get("name"),
                                        "code": item.get("code"),
                                        "city": item.get("cityName"),
                                        "distance": item.get("distanceToCity", {}).get("value", 0)
                                    })
                                elif item.get("type") == "CITY":
                                    cities.append({
                                        "id": item.get("id"),
                                        "name": item.get("name"),
                                        "code": item.get("code")
                                    })
                            
                            return {
                                "airports": airports,
                                "cities": cities,
                                "destination": destination
                            }
            
            logger.error(f"Failed to get airports for {destination}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting airports for {destination}: {e}")
            return None
    
    async def analyze_trip_type(self, user_input: str) -> Dict[str, Any]:
        """
        Analyze the type of trip from user input using AI logic.
        """
        input_lower = user_input.lower()
        
        # Check for national parks (common ones)
        national_parks = [
            "yosemite", "yellowstone", "grand canyon", "zion", "rocky mountain",
            "glacier", "acadia", "shenandoah", "smoky mountains", "arches"
        ]
        
        for park in national_parks:
            if park in input_lower:
                return {
                    "trip_type": "national_park",
                    "destination": park,
                    "requires_airport_logic": True
                }
        
        # Check for multi-city countries
        multi_city_countries = [
            "italy", "france", "spain", "japan", "germany", "netherlands",
            "belgium", "switzerland", "austria", "czech republic"
        ]
        
        for country in multi_city_countries:
            if country in input_lower:
                return {
                    "trip_type": "multi_city",
                    "destination": country,
                    "requires_route_planning": True
                }
        
        # Check for specific cities that suggest multi-city trips
        # Only trigger if multiple cities are mentioned
        italy_cities = ["rome", "florence", "venice", "milan", "naples"]
        france_cities = ["paris", "lyon", "nice", "marseille", "bordeaux"]
        spain_cities = ["madrid", "barcelona", "seville", "valencia", "granada"]
        
        # Count mentions of cities
        italy_mentions = sum(1 for city in italy_cities if city in input_lower)
        france_mentions = sum(1 for city in france_cities if city in input_lower)
        spain_mentions = sum(1 for city in spain_cities if city in input_lower)
        
        # Only treat as multi-city if multiple cities are mentioned
        if italy_mentions >= 2:
            return {
                "trip_type": "multi_city",
                "destination": "italy",
                "requires_route_planning": True
            }
        elif france_mentions >= 2:
            return {
                "trip_type": "multi_city",
                "destination": "france",
                "requires_route_planning": True
            }
        elif spain_mentions >= 2:
            return {
                "trip_type": "multi_city",
                "destination": "spain",
                "requires_route_planning": True
            }
        
        return {
            "trip_type": "single_destination",
            "destination": None,
            "requires_basic_planning": True
        }
    
    async def get_smart_airport_recommendation(self, destination: str, trip_type: str) -> Optional[Dict[str, Any]]:
        """
        Get smart airport recommendation using dynamic maps and weather analysis.
        """
        try:
            if trip_type == "national_park":
                # Use dynamic maps and weather service for comprehensive analysis
                if self.maps_weather_service:
                    logger.info(f"Using dynamic maps and weather service for {destination}")
                    
                    # Get comprehensive destination analysis
                    analysis = await self.maps_weather_service.analyze_destination_for_travel(destination)
                    
                    if analysis and "error" not in analysis:
                        airports_data = analysis["airports"]
                        weather_data = analysis.get("weather")
                        transportation_data = analysis.get("transportation", [])
                        
                        # Extract airport information
                        primary_airport = airports_data.get("primary")
                        major_alternatives = airports_data.get("major_alternatives", [])
                        regional_alternatives = airports_data.get("regional_alternatives", [])
                        
                        if primary_airport:
                            # Build comprehensive recommendation
                            recommendation = {
                                "primary_airport": primary_airport["id"],
                                "airport_name": primary_airport["name"],
                                "airport_code": primary_airport["code"],
                                "airport_type": "major" if airports_data["recommendation_type"] == "major_airport" else "regional",
                                "recommendation_type": airports_data["recommendation_type"],
                                "reasoning": airports_data["reasoning"],
                                "alternative_airports": [ap["id"] for ap in major_alternatives + regional_alternatives],
                                "alternative_names": [ap["name"] for ap in major_alternatives + regional_alternatives],
                                "alternative_codes": [ap["code"] for ap in major_alternatives + regional_alternatives],
                                "distance_to_destination": f"{primary_airport['distance']:.1f} km",
                                "transportation_options": transportation_data,
                                "minimum_days": 4,
                                "cost_considerations": {
                                    "primary": "Dynamic analysis based on real-time airport data",
                                    "transportation": "Personalized recommendations based on destination type",
                                    "time_tradeoff": f"Drive time: {primary_airport['distance']:.1f} km from destination",
                                    "weather_considerations": "Weather data available for trip planning" if weather_data else "Weather data not available"
                                }
                            }
                            
                            # Add weather information if available
                            if weather_data:
                                recommendation["weather_forecast"] = {
                                    "destination": weather_data["destination"],
                                    "forecasts": weather_data["forecasts"][:5],  # Next 5 days
                                    "recommendations": self._get_weather_based_recommendations(weather_data)
                                }
                            
                            # Add maps integration information
                            recommendation["maps_integration"] = {
                                "coordinates": analysis["coordinates"],
                                "analysis_timestamp": analysis["analysis_timestamp"]
                            }
                            
                            return recommendation
                    
                    # Fallback to API-based search if dynamic service fails
                    logger.info(f"Dynamic service failed, falling back to API search for {destination}")
                
                # Fallback to original API-based airport search
                airport_data = await self.get_airports_near_destination(destination)
                if airport_data and airport_data["airports"]:
                    airports = airport_data["airports"]
                    
                    # Dynamic airport classification using major_airports_filtered.json
                    # No hardcoded lists - everything is data-driven!
                    
                    # Categorize airports into major and regional
                    major_airport_options = []
                    regional_airport_options = []
                    
                    # Load major airports database dynamically
                    major_airports_db = self._load_major_airports_database()
                    
                    for airport in airports:
                        airport_code = airport.get("code", "")
                        airport_name = airport.get("name", "")
                        distance = airport.get("distance", 0)
                        
                        # Check if this airport is in our major airports database
                        is_major = self._is_major_airport(airport_code, airport_name, major_airports_db)
                        
                        if is_major:
                            # Major airport - prioritize for better connectivity and cheaper flights
                            major_airport_options.append({
                                **airport,
                                "type": "major",
                                "connectivity": "high",
                                "cost_advantage": "better_flight_prices",
                                "reasoning": "Major airport with better connectivity and typically cheaper flights"
                            })
                        else:
                            # Regional airport - closer but potentially more expensive
                            regional_airport_options.append({
                                **airport,
                                "type": "regional", 
                                "connectivity": "limited",
                                "cost_advantage": "closer_distance",
                                "reasoning": "Regional airport - closer distance but check major airports for better prices"
                            })
                    
                    # Smart prioritization: Balance distance vs connectivity
                    if major_airport_options:
                        # Sort major airports by smart score (distance + connectivity factor)
                        major_airport_options.sort(key=lambda x: self._calculate_airport_score(x))
                        primary_airport = major_airport_options[0]
                        alternative_majors = major_airport_options[1:3]
                        
                        # Add closest regional airport as alternative option
                        if regional_airport_options:
                            regional_airport_options.sort(key=lambda x: x.get("distance", float('inf')))
                            alternative_airports = alternative_majors + regional_airport_options[:1]
                        else:
                            alternative_airports = alternative_majors
                            
                        recommendation_type = "major_airport"
                        reasoning = primary_airport.get("reasoning", "Major airport with high connectivity and typically cheaper flights")
                        
                    else:
                        # Fallback to regional airports if no major airports found
                        regional_airport_options.sort(key=lambda x: x.get("distance", float('inf')))
                        primary_airport = regional_airport_options[0]
                        alternative_airports = regional_airport_options[1:3]
                        recommendation_type = "regional_airport"
                        reasoning = primary_airport.get("reasoning", "Closest regional airport - check major airports in nearby cities for better prices")
                    
                    return {
                        "primary_airport": primary_airport["id"],
                        "airport_name": primary_airport["name"],
                        "airport_code": primary_airport.get("code", ""),
                        "airport_type": primary_airport.get("type", "unknown"),
                        "recommendation_type": recommendation_type,
                        "reasoning": reasoning,
                        "alternative_airports": [ap["id"] for ap in alternative_airports],
                        "alternative_names": [ap["name"] for ap in alternative_airports],
                        "alternative_codes": [ap.get("code", "") for ap in alternative_airports],
                        "distance_to_destination": f"{primary_airport['distance']:.1f} km",
                        "transportation_options": ["Rental car", "Shuttle service", "Private tour"],
                        "minimum_days": 4,
                        "cost_considerations": {
                            "primary": "Major airports typically offer cheaper flights due to higher competition",
                            "transportation": "Rental car required for park access",
                            "time_tradeoff": "Longer drive but significant flight cost savings"
                        }
                    }
            
            elif trip_type == "multi_city":
                # For multi-city trips, we'll use the destination specialist agent
                # to create the route, but we can get airport info for the main cities
                return {
                    "requires_destination_specialist": True,
                    "destination": destination,
                    "trip_type": "multi_city"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting smart airport recommendation: {e}")
            return None
    
    def _get_weather_based_recommendations(self, weather_data: Dict[str, Any]) -> List[str]:
        """Generate weather-based travel recommendations."""
        recommendations = []
        
        if not weather_data or "forecasts" not in weather_data:
            return recommendations
        
        # Analyze weather patterns
        forecasts = weather_data["forecasts"]
        if not forecasts:
            return recommendations
        
        # Get average temperatures
        temps = [f.get("temp_max", 0) for f in forecasts if f.get("temp_max")]
        if temps:
            avg_temp = sum(temps) / len(temps)
            
            if avg_temp < 10:  # Cold weather
                recommendations.extend([
                    "Pack warm clothing and layers",
                    "Consider indoor activities for bad weather days",
                    "Check road conditions for driving to national parks"
                ])
            elif avg_temp > 25:  # Hot weather
                recommendations.extend([
                    "Pack light, breathable clothing",
                    "Plan outdoor activities for early morning or evening",
                    "Stay hydrated and use sun protection"
                ])
        
        # Check for rain/snow
        weather_conditions = [f.get("weather", "").lower() for f in forecasts]
        if any("rain" in w for w in weather_conditions):
            recommendations.append("Pack rain gear and waterproof shoes")
        if any("snow" in w for w in weather_conditions):
            recommendations.append("Check road closures and pack winter gear")
        
        return recommendations
    
    def get_multi_city_route_suggestion(self, country: str) -> Optional[Dict[str, Any]]:
        """
        Get multi-city route suggestion based on country.
        This would ideally use AI to generate routes, but for now we'll use common patterns.
        """
        # Common multi-city routes (this could be enhanced with AI)
        common_routes = {
            "italy": {
                "cities": ["Rome", "Florence", "Venice"],
                "route_type": "Cultural Renaissance",
                "transportation": {
                    "Rome_to_Florence": {"method": "High-speed train", "duration": "1.5 hours", "cost": "$25-35"},
                    "Florence_to_Venice": {"method": "High-speed train", "duration": "2 hours", "cost": "$30-40"}
                },
                "themes": ["Ancient Rome", "Renaissance Art", "Venetian Culture"],
                "minimum_days": 10
            },
            "france": {
                "cities": ["Paris", "Lyon", "Nice"],
                "route_type": "French Culture & Cuisine",
                "transportation": {
                    "Paris_to_Lyon": {"method": "High-speed train", "duration": "2 hours", "cost": "$50-70"},
                    "Lyon_to_Nice": {"method": "High-speed train", "duration": "4 hours", "cost": "$60-80"}
                },
                "themes": ["Parisian Culture", "Lyon Cuisine", "French Riviera"],
                "minimum_days": 12
            },
            "spain": {
                "cities": ["Madrid", "Barcelona", "Seville"],
                "route_type": "Spanish Heritage",
                "transportation": {
                    "Madrid_to_Barcelona": {"method": "High-speed train", "duration": "2.5 hours", "cost": "$60-80"},
                    "Barcelona_to_Seville": {"method": "High-speed train", "duration": "5.5 hours", "cost": "$80-100"}
                },
                "themes": ["Madrid Culture", "Barcelona Architecture", "Andalusian Flamenco"],
                "minimum_days": 12
            }
        }
        
        return common_routes.get(country.lower(), None)
    
    async def create_smart_itinerary_request(self, user_input: str) -> Dict[str, Any]:
        """
        Create a smart itinerary request that can be passed to the destination specialist.
        """
        trip_analysis = await self.analyze_trip_type(user_input)
        
        if trip_analysis["trip_type"] == "national_park":
            airport_rec = await self.get_smart_airport_recommendation(
                trip_analysis["destination"], 
                trip_analysis["trip_type"]
            )
            
            return {
                "trip_type": "national_park",
                "destination": trip_analysis["destination"],
                "airport_recommendation": airport_rec,
                "requires_smart_airport_logic": True
            }
        
        elif trip_analysis["trip_type"] == "multi_city":
            route_suggestion = self.get_multi_city_route_suggestion(trip_analysis["destination"])
            
            return {
                "trip_type": "multi_city",
                "destination": trip_analysis["destination"],
                "route_suggestion": route_suggestion,
                "requires_multi_city_planning": True
            }
        
        else:
            return {
                "trip_type": "single_destination",
                "destination": None,
                "requires_basic_planning": True
            } 
    
    def _load_major_airports_database(self) -> Dict[str, Any]:
        """Load the major airports database from major_airports_filtered.json."""
        try:
            import json
            from pathlib import Path
            
            airport_file = Path("major_airports_filtered.json")
            if not airport_file.exists():
                logger.warning("Major airports database not found")
                return {}
            
            with open(airport_file, 'r') as f:
                airports_data = json.load(f)
            
            # Create a lookup dictionary for fast airport code checking
            airports_lookup = {}
            for airport in airports_data:
                airport_code = airport.get("column_1", "")
                if airport_code:
                    airports_lookup[airport_code] = airport
            
            logger.info(f"Loaded {len(airports_lookup)} airports from database")
            return airports_lookup
            
        except Exception as e:
            logger.error(f"Error loading major airports database: {e}")
            return {}
    
    def _is_major_airport(self, airport_code: str, airport_name: str, major_airports_db: Dict[str, Any]) -> bool:
        """Determine if an airport is major based on database lookup and name analysis."""
        if not airport_code or not airport_name:
            return False
        
        # Check if airport code exists in our major airports database
        if airport_code in major_airports_db:
            return True
        
        # Additional heuristics for major airports based on name patterns
        major_indicators = [
            "international", "intl", "int'l", "international airport",
            "major", "hub", "gateway", "central", "main"
        ]
        
        airport_name_lower = airport_name.lower()
        return any(indicator in airport_name_lower for indicator in major_indicators)
    
    def _calculate_airport_score(self, airport: Dict[str, Any]) -> float:
        """Calculate a smart score for airport prioritization (lower is better)."""
        distance = airport.get("distance", 0)
        
        # Base score is distance
        score = distance
        
        # Bonus for major airports (prioritize connectivity over distance)
        if airport.get("type") == "major":
            score *= 0.7  # 30% bonus for major airports
        
        # Additional bonus for very close major airports
        if airport.get("type") == "major" and distance < 100:
            score *= 0.8  # Extra 20% bonus for close major airports
        
        return score 