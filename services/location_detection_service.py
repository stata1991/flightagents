#!/usr/bin/env python3

import aiohttp
import logging
from typing import Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class LocationDetectionService:
    """Service to detect user location and determine appropriate currency"""
    
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json"
        self.country_currency_map = {
            "IN": "INR",  # India
            "US": "USD",  # United States
            "GB": "GBP",  # United Kingdom
            "EU": "EUR",  # European Union
            "CA": "CAD",  # Canada
            "AU": "AUD",  # Australia
            "JP": "JPY",  # Japan
            "CN": "CNY",  # China
            "BR": "BRL",  # Brazil
            "MX": "MXN",  # Mexico
            "SG": "SGD",  # Singapore
            "AE": "AED",  # UAE
            "SA": "SAR",  # Saudi Arabia
            "ZA": "ZAR",  # South Africa
            "RU": "RUB",  # Russia
            "KR": "KRW",  # South Korea
            "TH": "THB",  # Thailand
            "MY": "MYR",  # Malaysia
            "ID": "IDR",  # Indonesia
            "PH": "PHP",  # Philippines
        }
        
        # Default to USD if location detection fails
        self.default_currency = "USD"
    
    async def detect_user_location(self, ip_address: Optional[str] = None) -> Dict[str, str]:
        """
        Detect user location based on IP address
        
        Args:
            ip_address: Optional IP address (if not provided, uses client IP)
            
        Returns:
            Dictionary with country_code, country_name, currency
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.ip_api_url}/{ip_address}" if ip_address else self.ip_api_url
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        country_code = data.get('countryCode', 'US')
                        country_name = data.get('country', 'United States')
                        currency = self.country_currency_map.get(country_code, self.default_currency)
                        
                        logger.info(f"Detected location: {country_name} ({country_code}), Currency: {currency}")
                        
                        return {
                            "country_code": country_code,
                            "country_name": country_name,
                            "currency": currency,
                            "city": data.get('city', ''),
                            "region": data.get('regionName', ''),
                            "timezone": data.get('timezone', '')
                        }
                    else:
                        logger.warning(f"IP API error: {response.status}")
                        return self._get_default_location()
                        
        except Exception as e:
            logger.error(f"Error detecting location: {e}")
            return self._get_default_location()
    
    def _get_default_location(self) -> Dict[str, str]:
        """Get default location (US) when detection fails"""
        return {
            "country_code": "US",
            "country_name": "United States",
            "currency": "USD",
            "city": "",
            "region": "",
            "timezone": "UTC"
        }
    
    def get_currency_for_country(self, country_code: str) -> str:
        """
        Get currency code for a given country code
        
        Args:
            country_code: ISO country code (e.g., 'IN', 'US')
            
        Returns:
            Currency code (e.g., 'INR', 'USD')
        """
        return self.country_currency_map.get(country_code.upper(), self.default_currency)
    
    def is_currency_different_from_usd(self, currency: str) -> bool:
        """
        Check if currency is different from USD
        
        Args:
            currency: Currency code
            
        Returns:
            True if currency is not USD
        """
        return currency.upper() != "USD"
    
    def get_currency_symbol(self, currency: str) -> str:
        """
        Get currency symbol for display
        
        Args:
            currency: Currency code
            
        Returns:
            Currency symbol
        """
        currency_symbols = {
            "USD": "$",
            "INR": "₹",
            "EUR": "€",
            "GBP": "£",
            "CAD": "C$",
            "AUD": "A$",
            "JPY": "¥",
            "CNY": "¥",
            "BRL": "R$",
            "MXN": "$",
            "SGD": "S$",
            "AED": "د.إ",
            "SAR": "ر.س",
            "ZAR": "R",
            "RUB": "₽",
            "KRW": "₩",
            "THB": "฿",
            "MYR": "RM",
            "IDR": "Rp",
            "PHP": "₱"
        }
        return currency_symbols.get(currency.upper(), "$")
    
    def format_price_for_display(self, price: float, currency: str, decimal_places: int = 2) -> str:
        """
        Format price for display with appropriate currency symbol
        
        Args:
            price: Price amount
            currency: Currency code
            decimal_places: Number of decimal places
            
        Returns:
            Formatted price string
        """
        symbol = self.get_currency_symbol(currency)
        
        # Special formatting for certain currencies
        if currency.upper() == "INR":
            # Indian Rupees - no decimal places
            return f"{symbol}{int(price):,}"
        elif currency.upper() == "JPY":
            # Japanese Yen - no decimal places
            return f"{symbol}{int(price):,}"
        else:
            # Standard formatting with decimal places
            return f"{symbol}{price:,.{decimal_places}f}"

# Global instance
location_detection_service = LocationDetectionService() 