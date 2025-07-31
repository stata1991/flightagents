import aiohttp
import logging
from typing import Dict, Optional, Union
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class CurrencyConverter:
    """Currency converter using Exchange Rate API"""
    
    def __init__(self):
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(hours=1)  # Cache rates for 1 hour
        
    async def get_exchange_rate(self, from_currency: str, to_currency: str = "USD") -> Optional[float]:
        """
        Get exchange rate from one currency to USD
        
        Args:
            from_currency: Source currency code (e.g., 'INR', 'EUR', 'GBP')
            to_currency: Target currency code (default: 'USD')
            
        Returns:
            Exchange rate as float, or None if failed
        """
        if from_currency == to_currency:
            return 1.0
            
        cache_key = f"{from_currency}_{to_currency}"
        now = datetime.now()
        
        # Check cache first
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if now - cached_data['timestamp'] < self.cache_duration:
                logger.info(f"Using cached exchange rate for {from_currency} to {to_currency}: {cached_data['rate']}")
                return cached_data['rate']
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{from_currency}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        rates = data.get('rates', {})
                        rate = rates.get(to_currency)
                        
                        if rate:
                            # Cache the result
                            self.cache[cache_key] = {
                                'rate': rate,
                                'timestamp': now
                            }
                            logger.info(f"Got exchange rate for {from_currency} to {to_currency}: {rate}")
                            return rate
                        else:
                            logger.error(f"Currency {to_currency} not found in response")
                            return None
                    else:
                        logger.error(f"Exchange rate API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting exchange rate for {from_currency} to {to_currency}: {e}")
            return None
    
    async def convert_price(self, price: Union[int, float], from_currency: str, to_currency: str = "USD") -> Optional[float]:
        """
        Convert price from one currency to another
        
        Args:
            price: Price amount
            from_currency: Source currency code
            to_currency: Target currency code (default: 'USD')
            
        Returns:
            Converted price as float, or None if conversion failed
        """
        if from_currency == to_currency:
            return float(price)
            
        rate = await self.get_exchange_rate(from_currency, to_currency)
        if rate is not None:
            return float(price) * rate
        return None
    
    async def convert_price_for_display(self, price: Union[int, float], from_currency: str, to_currency: str) -> Optional[float]:
        """
        Convert price for display purposes (USD to local currency)
        
        Args:
            price: Price amount in USD
            from_currency: Source currency (usually USD)
            to_currency: Target currency (user's local currency)
            
        Returns:
            Converted price as float, or None if conversion failed
        """
        if from_currency == to_currency:
            return float(price)
        
        # For display conversion (USD to local), we need to get the reverse rate
        if from_currency == "USD" and to_currency != "USD":
            # Get rate from local currency to USD, then calculate reverse
            rate = await self.get_exchange_rate(to_currency, "USD")
            if rate is not None and rate > 0:
                return float(price) / rate
            else:
                logger.error(f"Could not get exchange rate for {to_currency} to USD")
                return None
        else:
            # Standard conversion
            return await self.convert_price(price, from_currency, to_currency)
    


# Global instance
currency_converter = CurrencyConverter() 