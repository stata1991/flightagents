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
        Get smart airport recommendation prioritizing major airports for better connectivity and cost-effectiveness.
        """
        try:
            if trip_type == "national_park":
                # Get airports near the national park
                airport_data = await self.get_airports_near_destination(destination)
                if airport_data and airport_data["airports"]:
                    airports = airport_data["airports"]
                    
                    # Define major airports with high connectivity (these are typically cheaper and have more flights)
                    major_airports = {
                        "SFO": "San Francisco International Airport",
                        "SJC": "San Jose International Airport", 
                        "OAK": "Oakland International Airport",
                        "LAX": "Los Angeles International Airport",
                        "LAS": "Las Vegas McCarran International Airport",
                        "PHX": "Phoenix Sky Harbor International Airport",
                        "DEN": "Denver International Airport",
                        "SEA": "Seattle-Tacoma International Airport",
                        "PDX": "Portland International Airport",
                        "SLC": "Salt Lake City International Airport"
                    }
                    
                    # Categorize airports into major and regional
                    major_airport_options = []
                    regional_airport_options = []
                    
                    for airport in airports:
                        airport_code = airport.get("code", "")
                        if airport_code in major_airports:
                            # Major airport - prioritize for better connectivity and cheaper flights
                            major_airport_options.append({
                                **airport,
                                "type": "major",
                                "connectivity": "high",
                                "cost_advantage": "better_flight_prices"
                            })
                        else:
                            # Regional airport - closer but potentially more expensive
                            regional_airport_options.append({
                                **airport,
                                "type": "regional", 
                                "connectivity": "limited",
                                "cost_advantage": "closer_distance"
                            })
                    
                    # Prioritize major airports for cost-effectiveness and connectivity
                    if major_airport_options:
                        # Sort major airports by distance (closest major airport first)
                        major_airport_options.sort(key=lambda x: x.get("distance", float('inf')))
                        primary_airport = major_airport_options[0]
                        alternative_majors = major_airport_options[1:3]
                        
                        # Add closest regional airport as alternative option
                        if regional_airport_options:
                            regional_airport_options.sort(key=lambda x: x.get("distance", float('inf')))
                            alternative_airports = alternative_majors + regional_airport_options[:1]
                        else:
                            alternative_airports = alternative_majors
                            
                        recommendation_type = "major_airport"
                        reasoning = f"Major airport with high connectivity and typically cheaper flights"
                        
                    else:
                        # Fallback to regional airports if no major airports found
                        regional_airport_options.sort(key=lambda x: x.get("distance", float('inf')))
                        primary_airport = regional_airport_options[0]
                        alternative_airports = regional_airport_options[1:3]
                        recommendation_type = "regional_airport"
                        reasoning = f"Closest regional airport - check major airports in nearby cities for better prices"
                    
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