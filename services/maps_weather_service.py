#!/usr/bin/env python3
"""
Maps and Weather Integration Service
Provides dynamic destination analysis, airport proximity, and weather-based recommendations.
"""

import os
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MapsWeatherService:
    """Service for dynamic maps and weather integration."""
    
    def __init__(self):
        self.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY")
        self.rapid_api_key = os.getenv("RAPID_API_KEY")
        
        if not self.google_maps_api_key:
            logger.warning("GOOGLE_MAPS_API_KEY not found - maps features will be limited")
        if not self.openweather_api_key:
            logger.warning("OPENWEATHER_API_KEY not found - weather features will be limited")
    
    async def get_destination_coordinates(self, destination: str) -> Optional[Dict[str, float]]:
        """
        Get coordinates for a destination using free APIs with Google Maps fallback.
        """
        # Try free Nominatim API first
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": destination,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and len(data) > 0:
                            result = data[0]
                            return {
                                "lat": float(result["lat"]),
                                "lng": float(result["lon"]),
                                "formatted_address": result["display_name"],
                                "source": "nominatim"
                            }
        except Exception as e:
            logger.warning(f"Nominatim API failed for {destination}: {e}")
        
        # Fallback to Google Maps if available
        if self.google_maps_api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "address": destination,
                    "key": self.google_maps_api_key
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            if data.get("status") == "OK" and data.get("results"):
                                location = data["results"][0]["geometry"]["location"]
                                return {
                                    "lat": location["lat"],
                                    "lng": location["lng"],
                                    "formatted_address": data["results"][0]["formatted_address"],
                                    "source": "google_maps"
                                }
            except Exception as e:
                logger.error(f"Google Maps API failed for {destination}: {e}")
        
        return None
    
    async def find_nearby_airports(self, lat: float, lng: float, radius_km: int = 200) -> List[Dict[str, Any]]:
        """
        Find airports near a destination using free APIs with Google Places fallback.
        """
        # Try free airport database approach first
        airports = await self._find_airports_from_database(lat, lng, radius_km)
        
        if airports:
            return airports
        
        # Fallback to Google Places API if available
        if self.google_maps_api_key:
            try:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lng}",
                    "radius": radius_km * 1000,  # Convert to meters
                    "type": "airport",
                    "key": self.google_maps_api_key
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            airports = []
                            for place in data.get("results", []):
                                # Calculate distance from destination
                                airport_lat = place["geometry"]["location"]["lat"]
                                airport_lng = place["geometry"]["location"]["lng"]
                                distance = self._calculate_distance(lat, lng, airport_lat, airport_lng)
                                
                                airports.append({
                                    "id": place["place_id"],
                                    "name": place["name"],
                                    "code": self._extract_airport_code(place["name"]),
                                    "lat": airport_lat,
                                    "lng": airport_lng,
                                    "distance": distance,
                                    "rating": place.get("rating", 0),
                                    "types": place.get("types", []),
                                    "source": "google_places"
                                })
                            
                            # Sort by distance
                            airports.sort(key=lambda x: x["distance"])
                            return airports
            
            except Exception as e:
                logger.error(f"Google Places API failed: {e}")
        
        return []
    
    async def _find_airports_from_database(self, lat: float, lng: float, radius_km: int) -> List[Dict[str, Any]]:
                """
                Find airports using our existing airport database (free alternative).
                """
                try:
                    # Import our existing airport database
                    import json
                    from pathlib import Path
                    
                    # Try to load airports database with coordinates
                    airport_file = Path("api/airports-code.json")
                    if not airport_file.exists():
                        # Fallback to major airports if the full database doesn't exist
                        airport_file = Path("major_airports_filtered.json")
                        if not airport_file.exists():
                            return []
                    
                    with open(airport_file, 'r') as f:
                        airports_data = json.load(f)
                    
                    nearby_airports = []
                    for airport in airports_data:
                        # Handle both database formats
                        airport_lat = airport.get("latitude") or airport.get("lat")
                        airport_lng = airport.get("longitude") or airport.get("lon")
                        
                        if airport_lat and airport_lng:
                            distance = self._calculate_distance(lat, lng, airport_lat, airport_lng)
                            
                            if distance <= radius_km:
                                airport_code = airport.get("column_1", "")
                                airport_name = airport.get("airport_name", "")
                                
                                # Skip if no meaningful airport info
                                if not airport_code or not airport_name:
                                    continue
                                
                                nearby_airports.append({
                                    "id": airport_code,
                                    "name": airport_name,
                                    "code": airport_code,
                                    "lat": airport_lat,
                                    "lng": airport_lng,
                                    "distance": distance,
                                    "city": airport.get("city_name", ""),
                                    "country": airport.get("country_name", ""),
                                    "source": "airport_database"
                                })
                    
                    # Sort by distance and return top results
                    nearby_airports.sort(key=lambda x: x["distance"])
                    return nearby_airports[:10]  # Return top 10 closest airports
                    
                except Exception as e:
                    logger.warning(f"Airport database search failed: {e}")
                    return []
    
    async def get_weather_forecast(self, lat: float, lng: float, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for a destination using OpenWeather API.
        """
        if not self.openweather_api_key:
            return None
            
        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.openweather_api_key,
                "units": "metric"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process daily forecasts
                        daily_forecasts = []
                        current_date = None
                        daily_data = {}
                        
                        for item in data.get("list", []):
                            date = datetime.fromtimestamp(item["dt"]).date()
                            
                            if current_date != date:
                                if current_date and daily_data:
                                    daily_forecasts.append(daily_data)
                                
                                current_date = date
                                daily_data = {
                                    "date": date.strftime("%Y-%m-%d"),
                                    "temp_min": item["main"]["temp_min"],
                                    "temp_max": item["main"]["temp_max"],
                                    "weather": item["weather"][0]["main"],
                                    "description": item["weather"][0]["description"],
                                    "humidity": item["main"]["humidity"],
                                    "wind_speed": item["wind"]["speed"]
                                }
                        
                        if daily_data:
                            daily_forecasts.append(daily_data)
                        
                        return {
                            "destination": data["city"]["name"],
                            "country": data["city"]["country"],
                            "forecasts": daily_forecasts[:days]
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting weather forecast: {e}")
            return None
    
    async def get_driving_directions(self, origin: str, destination: str) -> Optional[Dict[str, Any]]:
        """
        Get driving directions between two points using Google Maps Directions API.
        """
        if not self.google_maps_api_key:
            return None
            
        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": "driving",
                "key": self.google_maps_api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "OK" and data.get("routes"):
                            route = data["routes"][0]["legs"][0]
                            
                            return {
                                "distance": route["distance"]["text"],
                                "duration": route["duration"]["text"],
                                "start_address": route["start_address"],
                                "end_address": route["end_address"],
                                "steps": [
                                    {
                                        "instruction": step["html_instructions"],
                                        "distance": step["distance"]["text"],
                                        "duration": step["duration"]["text"]
                                    }
                                    for step in route["steps"]
                                ]
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting driving directions: {e}")
            return None
    
    async def analyze_destination_for_travel(self, destination: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of a destination using maps and weather data.
        """
        try:
            # Get destination coordinates
            coords = await self.get_destination_coordinates(destination)
            if not coords:
                return {"error": "Could not get coordinates for destination"}
            
            # Get nearby airports
            airports = await self.find_nearby_airports(coords["lat"], coords["lng"])
            
            # Get weather forecast
            weather = await self.get_weather_forecast(coords["lat"], coords["lng"])
            
            # Analyze airport types and prioritize
            major_airports = []
            regional_airports = []
            
            for airport in airports:
                if self._is_major_airport(airport["name"], airport["code"]):
                    major_airports.append(airport)
                else:
                    regional_airports.append(airport)
            
            # Sort by distance
            major_airports.sort(key=lambda x: x["distance"])
            regional_airports.sort(key=lambda x: x["distance"])
            
            # Determine best airport recommendation
            if major_airports:
                primary_airport = major_airports[0]
                recommendation_type = "major_airport"
                reasoning = f"Major airport ({primary_airport['code']}) offers best connectivity and typically cheaper flights"
            elif regional_airports:
                primary_airport = regional_airports[0]
                recommendation_type = "regional_airport"
                reasoning = f"Closest regional airport - consider major airports in nearby cities for better flight options"
            else:
                primary_airport = None
                recommendation_type = "no_airports"
                reasoning = "No airports found within reasonable distance"
            
            # Get transportation recommendations
            transportation_options = await self._get_transportation_recommendations(
                destination, coords, primary_airport
            )
            
            return {
                "destination": destination,
                "coordinates": coords,
                "airports": {
                    "primary": primary_airport,
                    "major_alternatives": major_airports[1:3] if len(major_airports) > 1 else [],
                    "regional_alternatives": regional_airports[:2],
                    "recommendation_type": recommendation_type,
                    "reasoning": reasoning
                },
                "weather": weather,
                "transportation": transportation_options,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing destination {destination}: {e}")
            return {"error": str(e)}
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * asin(sqrt(a))
        
        # Earth's radius in kilometers
        r = 6371
        return c * r
    
    def _extract_airport_code(self, airport_name: str) -> str:
        """Extract airport code from airport name."""
        # Common patterns for airport codes
        import re
        
        # Look for 3-letter codes in parentheses or brackets
        code_match = re.search(r'[\(\[]([A-Z]{3})[\)\]]', airport_name)
        if code_match:
            return code_match.group(1)
        
        # Look for 3-letter codes at the end
        code_match = re.search(r'([A-Z]{3})$', airport_name)
        if code_match:
            return code_match.group(1)
        
        # Look for 3-letter codes in the middle
        code_match = re.search(r'([A-Z]{3})', airport_name)
        if code_match:
            return code_match.group(1)
        
        return ""
    
    def _is_major_airport(self, airport_name: str, airport_code: str) -> bool:
        """Determine if an airport is a major airport."""
        major_indicators = [
            "International", "International Airport", "Airport", "Field"
        ]
        
        # Check if it's a known major airport code
        major_codes = ["SFO", "LAX", "JFK", "ORD", "ATL", "DFW", "DEN", "SEA", "PHX", "LAS"]
        if airport_code in major_codes:
            return True
        
        # Check airport name for major indicators
        for indicator in major_indicators:
            if indicator in airport_name:
                return True
        
        return False
    
    async def _get_transportation_recommendations(self, destination: str, coords: Dict, primary_airport: Dict) -> List[str]:
        """Get transportation recommendations based on destination type and airport."""
        recommendations = []
        
        # Check if it's a national park or remote destination
        national_park_keywords = ["national park", "park", "reserve", "wilderness"]
        is_national_park = any(keyword in destination.lower() for keyword in national_park_keywords)
        
        if is_national_park:
            recommendations.extend([
                "Rental car (highly recommended for park access)",
                "Shuttle service (if available)",
                "Private tour with transportation"
            ])
        else:
            recommendations.extend([
                "Rental car (for flexibility)",
                "Public transportation",
                "Ride-sharing services",
                "Hotel shuttle (if available)"
            ])
        
        # Add airport-specific recommendations
        if primary_airport:
            if primary_airport.get("distance", 0) > 100:  # More than 100km
                recommendations.append("Consider closer regional airports for convenience")
            else:
                recommendations.append("Airport is reasonably close - rental car recommended")
        
        return recommendations
    
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
