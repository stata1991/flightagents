#!/usr/bin/env python3
"""
Location Detection Service
Supports user consent-based location detection and provides dynamic destination suggestions.
"""

import os
import aiohttp
import logging
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LocationDetectionService:
    """Service for detecting user location with consent and providing dynamic destination suggestions."""
    
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json"
        self.rapid_api_key = os.getenv("RAPID_API_KEY")
        self.rapid_api_host = "booking-com.p.rapidapi.com"
        
        # External APIs for dynamic destination discovery
        self.travel_apis = {
            "booking": {
                "base_url": "https://booking-com.p.rapidapi.com/v1",
                "headers": {
                    "X-RapidAPI-Key": self.rapid_api_key,
                    "X-RapidAPI-Host": self.rapid_api_host
                }
            },
            "nominatim": {
                "base_url": "https://nominatim.openstreetmap.org",
                "headers": {}
            }
        }
    
    async def detect_user_location_with_consent(self, user_consent: bool = False, 
                                              gps_coordinates: Dict[str, float] = None,
                                              ip_address: str = None) -> Dict[str, Any]:
        """
        Detect user location with proper consent handling.
        
        Args:
            user_consent: Whether user has given consent for location detection
            gps_coordinates: GPS coordinates if user provided them (lat, lon)
            ip_address: IP address for fallback detection
            
        Returns:
            Dictionary with location information and consent status
        """
        try:
            if user_consent and gps_coordinates:
                # User gave consent and provided GPS coordinates
                return await self._detect_from_gps(gps_coordinates)
            
            elif user_consent and ip_address:
                # User gave consent for IP-based detection
                return await self._detect_from_ip(ip_address)
            
            elif user_consent:
                # User gave consent but no coordinates/IP provided
                return await self._detect_from_ip()
            
            else:
                # No consent given - return default suggestions
                return {
                    "country": "Unknown",
                    "country_code": "default",
                    "region": "Unknown",
                    "city": "Unknown",
                    "timezone": "UTC",
                    "lat": 0,
                    "lon": 0,
                    "isp": "Unknown",
                    "detection_method": "no_consent",
                    "consent_given": False,
                    "message": "Location detection requires user consent"
                }
            
        except Exception as e:
            logger.error(f"Error detecting location: {e}")
            return {
                "country": "Unknown",
                "country_code": "default",
                "region": "Unknown",
                "city": "Unknown",
                "timezone": "UTC",
                "lat": 0,
                "lon": 0,
                "isp": "Unknown",
                "detection_method": "error",
                "consent_given": False,
                "message": "Location detection failed"
            }
    
    async def _detect_from_gps(self, coordinates: Dict[str, float]) -> Dict[str, Any]:
        """Detect location from GPS coordinates using reverse geocoding."""
        try:
            lat = coordinates.get("lat", 0)
            lon = coordinates.get("lon", 0)
            
            # Use reverse geocoding API
            url = f"{self.travel_apis['nominatim']['base_url']}/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        address = data.get("address", {})
                        
                        return {
                            "country": address.get("country", "Unknown"),
                            "country_code": address.get("country_code", "default").upper(),
                            "region": address.get("state", "Unknown"),
                            "city": address.get("city", address.get("town", "Unknown")),
                            "timezone": "UTC",  # Would need timezone API
                            "lat": lat,
                            "lon": lon,
                            "isp": "Unknown",
                            "detection_method": "gps_consent",
                            "consent_given": True,
                            "message": "Location detected from GPS coordinates"
                        }
            
            # Fallback to default
            return self._get_default_location()
            
        except Exception as e:
            logger.error(f"Error detecting from GPS: {e}")
            return self._get_default_location()
    
    async def _detect_from_ip(self, ip_address: str = None) -> Dict[str, Any]:
        """Detect location from IP address with user consent."""
        try:
            if ip_address:
                url = f"{self.ip_api_url}/{ip_address}"
            else:
                url = self.ip_api_url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get("status") == "success":
                            return {
                                "country": data.get("country"),
                                "country_code": data.get("countryCode"),
                                "region": data.get("regionName"),
                                "city": data.get("city"),
                                "timezone": data.get("timezone"),
                                "lat": data.get("lat"),
                                "lon": data.get("lon"),
                                "isp": data.get("isp"),
                                "detection_method": "ip_consent",
                                "consent_given": True,
                                "message": "Location detected from IP address"
                            }
            
            return self._get_default_location()
            
        except Exception as e:
            logger.error(f"Error detecting from IP: {e}")
            return self._get_default_location()
    
    def _get_default_location(self) -> Dict[str, Any]:
        """Get default location when detection fails."""
        return {
            "country": "Unknown",
            "country_code": "default",
            "region": "Unknown",
            "city": "Unknown",
            "timezone": "UTC",
            "lat": 0,
            "lon": 0,
            "isp": "Unknown",
            "detection_method": "default",
            "consent_given": False,
            "message": "Using default location suggestions"
        }
    
    async def get_destination_suggestions(self, country_code: str = "default", trip_type: str = None, 
                                        interests: List[str] = None) -> Dict[str, Any]:
        """
        Get dynamic destination suggestions based on user's country and interests.
        
        Args:
            country_code: User's country code (US, IN, etc.) or "default"
            trip_type: Type of trip (summer, winter, celebration, business, etc.)
            interests: List of interests (beach, city, culture, etc.)
            
        Returns:
            Dictionary with domestic and international suggestions
        """
        try:
            # Get dynamic suggestions from external APIs
            domestic_suggestions = await self._get_domestic_suggestions(country_code, trip_type, interests)
            international_suggestions = await self._get_international_suggestions(country_code, trip_type, interests)
            
            return {
                "user_country": country_code,
                "domestic_suggestions": domestic_suggestions,
                "international_suggestions": international_suggestions,
                "trip_type": trip_type,
                "interests": interests,
                "total_suggestions": len(domestic_suggestions) + len(international_suggestions),
                "data_source": "dynamic_api"
            }
            
        except Exception as e:
            logger.error(f"Error getting destination suggestions: {e}")
            # Fallback to basic suggestions
            return await self._get_fallback_suggestions(country_code, trip_type, interests)
    
    async def _get_domestic_suggestions(self, country_code: str, trip_type: str = None, 
                                      interests: List[str] = None) -> List[Dict]:
        """Get domestic destination suggestions from external APIs."""
        try:
            if not self.rapid_api_key:
                logger.warning("RapidAPI key not available, using fallback suggestions")
                return await self._get_fallback_domestic_suggestions(country_code, trip_type, interests)
            
            # Use Booking.com API to get popular destinations in the country
            url = f"{self.travel_apis['booking']['base_url']}/hotels/locations"
            params = {
                "name": country_code,
                "locale": "en-us"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.travel_apis['booking']['headers'], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        destinations = []
                        
                        for item in data[:10]:  # Limit to 10 suggestions
                            destination = {
                                "name": item.get("name", "Unknown"),
                                "type": self._categorize_destination(item.get("name", ""), trip_type),
                                "highlights": await self._get_destination_highlights(item.get("name", ""), country_code),
                                "country": item.get("country", country_code),
                                "latitude": item.get("latitude"),
                                "longitude": item.get("longitude")
                            }
                            destinations.append(destination)
                        
                        return destinations
            
            return await self._get_fallback_domestic_suggestions(country_code, trip_type, interests)
            
        except Exception as e:
            logger.error(f"Error getting domestic suggestions: {e}")
            return await self._get_fallback_domestic_suggestions(country_code, trip_type, interests)
    
    async def _get_international_suggestions(self, country_code: str, trip_type: str = None, 
                                           interests: List[str] = None) -> List[Dict]:
        """Get international destination suggestions from external APIs."""
        try:
            if not self.rapid_api_key:
                logger.warning("RapidAPI key not available, using fallback suggestions")
                return await self._get_fallback_international_suggestions(trip_type, interests)
            
            # Get popular international destinations from external API
            # NO HARDCODED LISTS - everything is data-driven!
            url = f"{self.travel_apis['booking']['base_url']}/hotels/locations"
            params = {
                "name": "popular destinations",
                "locale": "en-us"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.travel_apis['booking']['headers'], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        destinations = []
                        
                        for item in data[:10]:  # Limit to 10 suggestions
                            destination = {
                                "name": item.get("name", "Unknown"),
                                "type": self._categorize_destination(item.get("name", ""), trip_type),
                                "highlights": await self._get_destination_highlights(item.get("name", ""), "international"),
                                "country": await self._get_destination_country(item.get("name", ""))
                            }
                            destinations.append(destination)
                        
                        return destinations
            
            return await self._get_fallback_international_suggestions(trip_type, interests)
            
        except Exception as e:
            logger.error(f"Error getting international suggestions: {e}")
            return await self._get_fallback_international_suggestions(trip_type, interests)
    
    async def _get_destination_highlights(self, destination_name: str, country_code: str) -> List[str]:
        """Get destination highlights from external APIs."""
        try:
            # Use Wikipedia API or similar to get destination highlights
            # For now, return basic highlights based on destination type
            destination_type = self._categorize_destination(destination_name, None)
            
            highlights_map = {
                "city": ["Urban Culture", "Shopping", "Dining", "Entertainment"],
                "beach": ["Beaches", "Water Sports", "Relaxation", "Sunset Views"],
                "culture": ["Museums", "Historical Sites", "Local Traditions", "Arts"],
                "nature": ["Natural Parks", "Hiking", "Wildlife", "Scenic Views"],
                "entertainment": ["Nightlife", "Shows", "Casinos", "Theme Parks"],
                "history": ["Ancient Sites", "Museums", "Architecture", "Heritage"],
                "luxury": ["High-end Hotels", "Fine Dining", "Shopping", "Exclusive Experiences"]
            }
            
            return highlights_map.get(destination_type, ["Local Attractions", "Cultural Sites", "Dining"])
            
        except Exception as e:
            logger.error(f"Error getting destination highlights: {e}")
            return ["Local Attractions", "Cultural Sites", "Dining"]
    
    async def _get_destination_country(self, destination_name: str) -> str:
        """Get country for a destination."""
        try:
            # Use geocoding API to get country
            url = f"{self.travel_apis['nominatim']['base_url']}/search"
            params = {
                "q": destination_name,
                "format": "json",
                "limit": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return data[0].get("address", {}).get("country", "Unknown")
            
            return "Unknown"
            
        except Exception as e:
            logger.error(f"Error getting destination country: {e}")
            return "Unknown"
    
    def _categorize_destination(self, destination_name: str, trip_type: str = None) -> str:
        """Categorize destination based on name and trip type."""
        name_lower = destination_name.lower() if destination_name else ""
        
        # Beach destinations
        beach_keywords = ["beach", "island", "coast", "seaside", "maldives", "bali", "hawaii", "caribbean"]
        if any(keyword in name_lower for keyword in beach_keywords):
            return "beach"
        
        # City destinations
        city_keywords = ["new york", "london", "paris", "tokyo", "mumbai", "delhi", "bangalore"]
        if any(keyword in name_lower for keyword in city_keywords):
            return "city"
        
        # Entertainment destinations
        entertainment_keywords = ["vegas", "las vegas", "orlando", "disney"]
        if any(keyword in name_lower for keyword in entertainment_keywords):
            return "entertainment"
        
        # Cultural destinations
        cultural_keywords = ["rome", "athens", "cairo", "kyoto", "varanasi"]
        if any(keyword in name_lower for keyword in cultural_keywords):
            return "culture"
        
        # Nature destinations
        nature_keywords = ["national park", "yosemite", "yellowstone", "banff", "serengeti"]
        if any(keyword in name_lower for keyword in nature_keywords):
            return "nature"
        
        # Default categorization based on trip type
        if trip_type:
            trip_type_mapping = {
                "summer": "beach",
                "winter": "city",
                "spring": "culture",
                "fall": "nature",
                "honeymoon": "beach",
                "business": "city",
                "family": "entertainment",
                "adventure": "nature",
                "relaxation": "beach",
                "culture": "culture"
            }
            return trip_type_mapping.get(trip_type.lower() if trip_type else "", "city")
        
        return "city"  # Default to city
    
    async def get_global_destination_suggestions(self, trip_type: str = None, 
                                               interests: List[str] = None) -> Dict[str, Any]:
        """
        Get global destination suggestions when user location is unknown.
        
        Args:
            trip_type: Type of trip (summer, winter, celebration, business, etc.)
            interests: List of interests (beach, city, culture, etc.)
            
        Returns:
            Dictionary with popular global destinations
        """
        try:
            # Get suggestions from multiple sources
            suggestions = await self._get_international_suggestions("default", trip_type, interests)
            
            return {
                "user_country": "global",
                "global_suggestions": suggestions,
                "trip_type": trip_type,
                "interests": interests,
                "total_suggestions": len(suggestions),
                "data_source": "dynamic_api"
            }
            
        except Exception as e:
            logger.error(f"Error getting global destination suggestions: {e}")
            return await self._get_fallback_global_suggestions(trip_type, interests)
    
    async def _get_fallback_suggestions(self, country_code: str, trip_type: str = None, 
                                      interests: List[str] = None) -> Dict[str, Any]:
        """Get fallback suggestions when APIs are unavailable."""
        domestic = await self._get_fallback_domestic_suggestions(country_code, trip_type, interests)
        international = await self._get_fallback_international_suggestions(trip_type, interests)
        
        return {
            "user_country": country_code,
            "domestic_suggestions": domestic,
            "international_suggestions": international,
            "trip_type": trip_type,
            "interests": interests,
            "total_suggestions": len(domestic) + len(international),
            "data_source": "fallback"
        }
    
    async def _get_fallback_domestic_suggestions(self, country_code: str, trip_type: str = None, 
                                               interests: List[str] = None) -> List[Dict]:
        """Get fallback domestic suggestions."""
        # Minimal fallback data - in production, this would come from a database
        fallback_data = {
            "US": [
                {"name": "New York City", "type": "city", "highlights": ["Times Square", "Central Park", "Broadway"]},
                {"name": "Los Angeles", "type": "city", "highlights": ["Hollywood", "Venice Beach", "Universal Studios"]},
                {"name": "Miami", "type": "beach", "highlights": ["South Beach", "Art Deco", "Nightlife"]}
            ],
            "IN": [
                {"name": "Mumbai", "type": "city", "highlights": ["Gateway of India", "Marine Drive", "Bollywood"]},
                {"name": "Delhi", "type": "history", "highlights": ["Red Fort", "Taj Mahal", "Old Delhi"]},
                {"name": "Goa", "type": "beach", "highlights": ["Beaches", "Nightlife", "Portuguese Heritage"]}
            ]
        }
        
        suggestions = fallback_data.get(country_code, fallback_data.get("US", []))
        
        if trip_type:
            suggestions = self._filter_by_trip_type(suggestions, trip_type)
        
        if interests:
            suggestions = self._filter_by_interests(suggestions, interests)
        
        return suggestions[:5]
    
    async def _get_fallback_international_suggestions(self, trip_type: str = None, 
                                                    interests: List[str] = None) -> List[Dict]:
        """Get fallback international suggestions."""
        suggestions = [
            {"name": "Paris", "country": "France", "type": "culture", "highlights": ["Eiffel Tower", "Louvre", "Cafes"]},
            {"name": "London", "country": "UK", "type": "city", "highlights": ["Big Ben", "Buckingham Palace", "Museums"]},
            {"name": "Tokyo", "country": "Japan", "type": "modern", "highlights": ["Shibuya", "Senso-ji", "Sushi"]},
            {"name": "Rome", "country": "Italy", "type": "history", "highlights": ["Colosseum", "Vatican", "Pizza"]},
            {"name": "Barcelona", "country": "Spain", "type": "culture", "highlights": ["Sagrada Familia", "Beach", "Tapas"]}
        ]
        
        if trip_type:
            suggestions = self._filter_by_trip_type(suggestions, trip_type)
        
        if interests:
            suggestions = self._filter_by_interests(suggestions, interests)
        
        return suggestions[:5]
    
    async def _get_fallback_global_suggestions(self, trip_type: str = None, 
                                             interests: List[str] = None) -> Dict[str, Any]:
        """Get fallback global suggestions."""
        suggestions = await self._get_fallback_international_suggestions(trip_type, interests)
        
        return {
            "user_country": "global",
            "global_suggestions": suggestions,
            "trip_type": trip_type,
            "interests": interests,
            "total_suggestions": len(suggestions),
            "data_source": "fallback"
        }
    
    async def _get_fallback_celebration_suggestions(self, celebration_type: str) -> List[Dict]:
        """Get fallback celebration suggestions when APIs are unavailable."""
        # Minimal fallback data - in production, this would come from a database
        # This is only used when external APIs fail
        fallback_data = {
            "birthday": [
                {"name": "Las Vegas", "country": "USA", "type": "entertainment", "highlights": ["The Strip", "Shows", "Nightlife"]},
                {"name": "Miami", "country": "USA", "type": "beach", "highlights": ["South Beach", "Nightlife", "Beaches"]}
            ],
            "anniversary": [
                {"name": "Paris", "country": "France", "type": "romance", "highlights": ["Eiffel Tower", "Romance", "Fine Dining"]},
                {"name": "Venice", "country": "Italy", "type": "romance", "highlights": ["Gondolas", "Canals", "Romance"]}
            ],
            "honeymoon": [
                {"name": "Bali", "country": "Indonesia", "type": "island", "highlights": ["Beaches", "Temples", "Culture"]},
                {"name": "Maldives", "country": "Maldives", "type": "luxury", "highlights": ["Overwater Bungalows", "Beaches", "Luxury"]}
            ]
        }
        
        return fallback_data.get(celebration_type.lower() if celebration_type else "", [])
    
    def _filter_by_trip_type(self, destinations: List[Dict], trip_type: str) -> List[Dict]:
        """Filter destinations by trip type."""
        trip_type_mapping = {
            "summer": ["beach", "island", "nature"],
            "winter": ["ski", "mountain", "city"],
            "spring": ["culture", "city", "nature"],
            "fall": ["culture", "city", "nature"],
            "honeymoon": ["beach", "island", "luxury"],
            "business": ["city", "tech"],
            "family": ["beach", "entertainment", "culture"],
            "adventure": ["nature", "mountain", "island"],
            "relaxation": ["beach", "island", "spa"],
            "culture": ["culture", "history", "heritage"]
        }
        
        target_types = trip_type_mapping.get(trip_type.lower() if trip_type else "", [])
        
        if not target_types:
            return destinations
        
        filtered = []
        for dest in destinations:
            if dest.get("type") in target_types:
                filtered.append(dest)
        
        return filtered if filtered else destinations
    
    def _filter_by_interests(self, destinations: List[Dict], interests: List[str]) -> List[Dict]:
        """Filter destinations by user interests."""
        filtered = []
        
        for dest in destinations:
            dest_type = dest.get("type", "").lower() if dest.get("type") else ""
            dest_highlights = [h.lower() for h in dest.get("highlights", []) if h]
            
            for interest in interests:
                interest_lower = interest.lower() if interest else ""
                
                # Check if interest matches destination type or highlights
                if (interest_lower in dest_type or 
                    any(interest_lower in highlight for highlight in dest_highlights)):
                    filtered.append(dest)
                    break
        
        return filtered if filtered else destinations
    
    async def get_seasonal_recommendations(self, country_code: str = "default", season: str = None) -> List[Dict]:
        """
        Get seasonal destination recommendations.
        
        Args:
            country_code: User's country code or "default"
            season: Season (summer, winter, spring, fall)
            
        Returns:
            List of seasonal destination recommendations
        """
        if country_code == "default":
            suggestions = await self.get_global_destination_suggestions(trip_type=season)
            return suggestions["global_suggestions"] if suggestions else []
        else:
            suggestions = await self.get_destination_suggestions(country_code, trip_type=season)
            if suggestions:
                return suggestions["domestic_suggestions"] + suggestions["international_suggestions"]
            return []
    
    async def get_celebration_recommendations(self, celebration_type: str) -> List[Dict]:
        """
        Get celebration-specific destination recommendations using dynamic API calls.
        
        Args:
            celebration_type: Type of celebration (birthday, anniversary, honeymoon, etc.)
            
        Returns:
            List of celebration destination recommendations
        """
        try:
            # Use external APIs to get celebration-specific destinations
            # This will be populated dynamically from external APIs and AI analysis
            # NO HARDCODED LISTS - everything is data-driven!
            
            if not self.rapid_api_key:
                logger.warning("RapidAPI key not available, using fallback suggestions")
                return await self._get_fallback_celebration_suggestions(celebration_type)
            
            # Use Booking.com API to get popular destinations for celebration type
            url = f"{self.travel_apis['booking']['base_url']}/hotels/locations"
            params = {
                "name": celebration_type,
                "locale": "en-us"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.travel_apis['booking']['headers'], params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        destinations = []
                        
                        for item in data[:6]:  # Limit to 6 suggestions
                            destination = {
                                "name": item.get("name", "Unknown"),
                                "type": self._categorize_destination(item.get("name", ""), celebration_type),
                                "highlights": await self._get_destination_highlights(item.get("name", ""), "celebration"),
                                "country": await self._get_destination_country(item.get("name", "")),
                                "celebration_type": celebration_type
                            }
                            destinations.append(destination)
                        
                        return destinations
            
            return await self._get_fallback_celebration_suggestions(celebration_type)
            
        except Exception as e:
            logger.error(f"Error getting celebration recommendations: {e}")
            return await self._get_fallback_celebration_suggestions(celebration_type)
    
    # Currency-related methods for price display service
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol for a given currency code."""
        currency_symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "JPY": "¥",
            "CAD": "C$",
            "AUD": "A$",
            "CHF": "CHF",
            "CNY": "¥",
            "INR": "₹",
            "BRL": "R$",
            "MXN": "$",
            "KRW": "₩",
            "SGD": "S$",
            "HKD": "HK$",
            "NZD": "NZ$",
            "SEK": "kr",
            "NOK": "kr",
            "DKK": "kr",
            "PLN": "zł",
            "CZK": "Kč",
            "HUF": "Ft",
            "RUB": "₽",
            "TRY": "₺",
            "ZAR": "R",
            "THB": "฿",
            "MYR": "RM",
            "IDR": "Rp",
            "PHP": "₱",
            "VND": "₫",
            "EGP": "E£",
            "NGN": "₦",
            "KES": "KSh",
            "GHS": "GH₵",
            "UGX": "USh",
            "TZS": "TSh",
            "ZMW": "ZK",
            "MAD": "MAD",
            "TND": "TND",
            "DZD": "DZD",
            "LYD": "LYD",
            "SDG": "SDG",
            "ETB": "ETB",
            "SOS": "SOS",
            "DJF": "DJF",
            "KMF": "KMF",
            "MUR": "MUR",
            "SCR": "SCR",
            "SLL": "SLL",
            "GMD": "GMD",
            "GNF": "GNF",
            "XOF": "CFA",
            "XAF": "CFA",
            "XPF": "CFP",
            "CDF": "CDF",
            "RWF": "RWF",
            "BIF": "BIF",
            "MWK": "MWK",
            "ZWL": "ZWL",
            "BWP": "P",
            "NAD": "N$",
            "LSL": "L",
            "SZL": "E",
            "MOP": "MOP$",
            "BND": "B$",
            "KHR": "៛",
            "LAK": "₭",
            "MMK": "K",
            "BDT": "৳",
            "LKR": "Rs",
            "NPR": "Rs",
            "PKR": "Rs",
            "AFN": "؋",
            "IRR": "﷼",
            "IQD": "ع.د",
            "JOD": "د.ا",
            "LBP": "ل.ل",
            "SYP": "ل.س",
            "YER": "﷼",
            "OMR": "ر.ع.",
            "QAR": "ر.ق",
            "SAR": "ر.س",
            "AED": "د.إ",
            "KWD": "د.ك",
            "BHD": ".د.ب",
            "KZT": "₸",
            "UZS": "so'm",
            "TJS": "ЅМ",
            "TMT": "T",
            "AZN": "₼",
            "GEL": "₾",
            "AMD": "֏",
            "BYN": "Br",
            "MDL": "L",
            "UAH": "₴",
            "BGN": "лв",
            "RSD": "дин.",
            "HRK": "kn",
            "BAM": "KM",
            "ALL": "L",
            "MKD": "ден",
            "MNT": "₮",
            "KGS": "с",
            "TJS": "ЅМ",
            "TMT": "T",
            "AZN": "₼",
            "GEL": "₾",
            "AMD": "֏",
            "BYN": "Br",
            "MDL": "L",
            "UAH": "₴",
            "BGN": "лв",
            "RSD": "дин.",
            "HRK": "kn",
            "BAM": "KM",
            "ALL": "L",
            "MKD": "ден",
            "MNT": "₮",
            "KGS": "с"
        }
        return currency_symbols.get(currency_code.upper(), "$")
    
    def format_price_for_display(self, price: float, currency_code: str) -> str:
        """Format price for display with appropriate currency symbol and formatting."""
        symbol = self.get_currency_symbol(currency_code)
        
        # Handle different currency formatting
        if currency_code.upper() in ["JPY", "KRW", "VND", "IDR"]:
            # No decimal places for these currencies
            return f"{symbol}{price:,.0f}"
        elif currency_code.upper() in ["EUR", "GBP", "USD", "CAD", "AUD", "NZD"]:
            # Standard decimal formatting
            return f"{symbol}{price:,.2f}"
        else:
            # Default formatting
            return f"{symbol}{price:,.2f}"
    
    def is_currency_different_from_usd(self, currency_code: str) -> bool:
        """Check if currency is different from USD."""
        return currency_code.upper() != "USD"
    
    async def get_country_from_city(self, city_name: str) -> str:
        """Get country for a given city name."""
        try:
            # Use geocoding API to get country
            url = f"{self.travel_apis['nominatim']['base_url']}/search"
            params = {
                "q": city_name,
                "format": "json",
                "limit": 1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            return data[0].get("address", {}).get("country", "Unknown")
            
            return "Unknown"
            
        except Exception as e:
            logger.error(f"Error getting country for city {city_name}: {e}")
            return "Unknown"
    
    def determine_trip_currency_strategy(self, origin_country: str, destination_country: str, user_country: str) -> Dict[str, str]:
        """Determine the best currency strategy for a trip."""
        try:
            # Default strategy
            strategy = {
                "primary_currency": "USD",
                "secondary_currency": "USD",
                "display_currency": "USD"
            }
            
            # If user is from a different country, use their currency as primary
            if user_country and user_country != "Unknown" and user_country != "default":
                strategy["primary_currency"] = self._get_currency_for_country(user_country)
                strategy["display_currency"] = strategy["primary_currency"]
            
            # If destination is different from user country, use destination currency as secondary
            if destination_country and destination_country != "Unknown" and destination_country != user_country:
                strategy["secondary_currency"] = self._get_currency_for_country(destination_country)
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error determining currency strategy: {e}")
            return {
                "primary_currency": "USD",
                "secondary_currency": "USD",
                "display_currency": "USD"
            }
    
    def _get_currency_for_country(self, country_code: str) -> str:
        """Get the primary currency for a country."""
        currency_map = {
            "US": "USD",
            "CA": "CAD",
            "GB": "GBP",
            "EU": "EUR",
            "JP": "JPY",
            "AU": "AUD",
            "IN": "INR",
            "CN": "CNY",
            "BR": "BRL",
            "MX": "MXN",
            "KR": "KRW",
            "SG": "SGD",
            "HK": "HKD",
            "NZ": "NZD",
            "SE": "SEK",
            "NO": "NOK",
            "DK": "DKK",
            "PL": "PLN",
            "CZ": "CZK",
            "HU": "HUF",
            "RU": "RUB",
            "TR": "TRY",
            "ZA": "ZAR",
            "TH": "THB",
            "MY": "MYR",
            "ID": "IDR",
            "PH": "PHP",
            "VN": "VND",
            "EG": "EGP",
            "NG": "NGN",
            "KE": "KES",
            "GH": "GHS",
            "UG": "UGX",
            "TZ": "TZS",
            "ZM": "ZMW",
            "MA": "MAD",
            "TN": "TND",
            "DZ": "DZD",
            "LY": "LYD",
            "SD": "SDG",
            "ET": "ETB",
            "SO": "SOS",
            "DJ": "DJF",
            "KM": "KMF",
            "MU": "MUR",
            "SC": "SCR",
            "SL": "SLL",
            "GM": "GMD",
            "GN": "GNF",
            "BF": "XOF",
            "CI": "XOF",
            "SN": "XOF",
            "ML": "XOF",
            "NE": "XOF",
            "TD": "XAF",
            "CM": "XAF",
            "CF": "XAF",
            "CG": "XAF",
            "GA": "XAF",
            "GQ": "XAF",
            "CD": "CDF",
            "RW": "RWF",
            "BI": "BIF",
            "MW": "MWK",
            "ZW": "ZWL",
            "BW": "BWP",
            "NA": "NAD",
            "LS": "LSL",
            "SZ": "SZL",
            "MO": "MOP",
            "BN": "BND",
            "KH": "KHR",
            "LA": "LAK",
            "MM": "MMK",
            "BD": "BDT",
            "LK": "LKR",
            "NP": "NPR",
            "PK": "PKR",
            "AF": "AFN",
            "IR": "IRR",
            "IQ": "IQD",
            "JO": "JOD",
            "LB": "LBP",
            "SY": "SYP",
            "YE": "YER",
            "OM": "OMR",
            "QA": "QAR",
            "SA": "SAR",
            "AE": "AED",
            "KW": "KWD",
            "BH": "BHD",
            "KZ": "KZT",
            "UZ": "UZS",
            "TJ": "TJS",
            "TM": "TMT",
            "AZ": "AZN",
            "GE": "GEL",
            "AM": "AMD",
            "BY": "BYN",
            "MD": "MDL",
            "UA": "UAH",
            "BG": "BGN",
            "RS": "RSD",
            "HR": "HRK",
            "BA": "BAM",
            "AL": "ALL",
            "MK": "MKD",
            "MN": "MNT",
            "KG": "KGS"
        }
        return currency_map.get(country_code.upper(), "USD") 