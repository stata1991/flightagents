#!/usr/bin/env python3

import logging
from typing import Dict, Optional, Union, List
from api.currency_converter import currency_converter
from services.location_detection_service import LocationDetectionService

logger = logging.getLogger(__name__)

class PriceDisplayService:
    """Service to handle price conversion and display for user's local currency"""
    
    def __init__(self):
        self.currency_converter = currency_converter
        self.location_service = LocationDetectionService()
    
    async def convert_and_format_price(self, price_usd: float, user_currency: str = "USD") -> Dict[str, str]:
        """
        Convert USD price to user's local currency and format for display
        
        Args:
            price_usd: Price in USD
            user_currency: User's local currency (default: USD)
            
        Returns:
            Dictionary with original_price, converted_price, currency_symbol, formatted_price
        """
        try:
            # Convert price to user's currency
            converted_price = await self.currency_converter.convert_price_for_display(
                price_usd, "USD", user_currency
            )
            
            if converted_price is None:
                # Fallback to USD if conversion fails
                logger.warning(f"Currency conversion failed, using USD for {user_currency}")
                return {
                    "original_price": price_usd,
                    "converted_price": price_usd,
                    "currency": "USD",
                    "currency_symbol": "$",
                    "formatted_price": f"${price_usd:,.2f}",
                    "conversion_failed": True
                }
            
            # Get currency symbol
            currency_symbol = self.location_service.get_currency_symbol(user_currency)
            
            # Format price for display
            formatted_price = self.location_service.format_price_for_display(
                converted_price, user_currency
            )
            
            return {
                "original_price": price_usd,
                "converted_price": converted_price,
                "currency": user_currency,
                "currency_symbol": currency_symbol,
                "formatted_price": formatted_price,
                "conversion_failed": False
            }
            
        except Exception as e:
            logger.error(f"Error converting price {price_usd} USD to {user_currency}: {e}")
            return {
                "original_price": price_usd,
                "converted_price": price_usd,
                "currency": "USD",
                "currency_symbol": "$",
                "formatted_price": f"${price_usd:,.2f}",
                "conversion_failed": True
            }
    
    async def convert_hotel_prices(self, hotels: List[Dict], user_currency: str = "USD") -> List[Dict]:
        """
        Convert hotel prices to user's local currency
        
        Args:
            hotels: List of hotel dictionaries
            user_currency: User's local currency
            
        Returns:
            List of hotels with converted prices
        """
        converted_hotels = []
        
        for hotel in hotels:
            try:
                # Get original price (assume USD if not specified)
                original_price = hotel.get('price_per_night') or hotel.get('average_price_per_night', 0)
                original_currency = hotel.get('currency', 'USD')
                
                # Convert price
                price_info = await self.convert_and_format_price(original_price, user_currency)
                
                # Update hotel with converted price info
                converted_hotel = hotel.copy()
                converted_hotel.update({
                    'display_price': price_info['formatted_price'],
                    'display_currency': price_info['currency'],
                    'display_currency_symbol': price_info['currency_symbol'],
                    'original_price_usd': original_price,
                    'converted_price': price_info['converted_price'],
                    'price_conversion_failed': price_info['conversion_failed']
                })
                
                converted_hotels.append(converted_hotel)
                
            except Exception as e:
                logger.error(f"Error converting hotel price: {e}")
                # Keep original hotel data if conversion fails
                converted_hotels.append(hotel)
        
        return converted_hotels
    
    async def convert_flight_prices(self, flights: List[Dict], user_currency: str = "USD") -> List[Dict]:
        """
        Convert flight prices to user's local currency
        
        Args:
            flights: List of flight dictionaries
            user_currency: User's local currency
            
        Returns:
            List of flights with converted prices
        """
        converted_flights = []
        
        for flight in flights:
            try:
                # Get original price (assume USD if not specified)
                original_price = flight.get('price', {}).get('units') or flight.get('cost', 0)
                original_currency = flight.get('currency', 'USD')
                
                # Convert price
                price_info = await self.convert_and_format_price(original_price, user_currency)
                
                # Update flight with converted price info
                converted_flight = flight.copy()
                converted_flight.update({
                    'display_price': price_info['formatted_price'],
                    'display_currency': price_info['currency'],
                    'display_currency_symbol': price_info['currency_symbol'],
                    'original_price_usd': original_price,
                    'converted_price': price_info['converted_price'],
                    'price_conversion_failed': price_info['conversion_failed']
                })
                
                converted_flights.append(converted_flight)
                
            except Exception as e:
                logger.error(f"Error converting flight price: {e}")
                # Keep original flight data if conversion fails
                converted_flights.append(flight)
        
        return converted_flights
    
    def get_currency_info(self, currency: str) -> Dict[str, str]:
        """
        Get currency information for display
        
        Args:
            currency: Currency code
            
        Returns:
            Dictionary with currency info
        """
        return {
            "currency": currency,
            "symbol": self.location_service.get_currency_symbol(currency),
            "is_different_from_usd": self.location_service.is_currency_different_from_usd(currency)
        }

# Global instance
price_display_service = PriceDisplayService() 