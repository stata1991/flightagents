import json
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import requests
from anthropic import AsyncAnthropic
import os

# Rapid API Booking.com credentials
RAPIDAPI_HOST = "booking-com15.p.rapidapi.com"
RAPIDAPI_KEY = os.getenv('RAPID_API_KEY')

# Claude API configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

# Initialize Claude client
claude_client = AsyncAnthropic(api_key=CLAUDE_API_KEY)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_flexible_dates(
    departure_date: str,
    return_date: Optional[str] = None,
    flex_days: int = 0
) -> Union[List[str], Tuple[List[str], List[str]]]:
    """
    Generate flexible date ranges for either one-way or round-trip flights.

    Args:
        departure_date: Required departure date (YYYY-MM-DD).
        return_date: Optional return date (YYYY-MM-DD). If None, assume one-way.
        flex_days: Number of ± days for flexibility.

    Returns:
        List of dates for one-way or tuple of (outbound_dates, return_dates) for round-trip.
    """
    def _generate(date_str: str) -> List[str]:
        try:
            base = datetime.strptime(date_str, "%Y-%m-%d")
            if base < datetime.now():
                base = datetime.now() + timedelta(days=1)
                logger.warning(f"Adjusted past date to {base.strftime('%Y-%m-%d')}")
        except ValueError:
            base = datetime.now() + timedelta(days=1)
            logger.warning(f"Invalid date format: {date_str}. Defaulting to {base.strftime('%Y-%m-%d')}")
        return [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(flex_days + 1)]

    if return_date:
        outbound_dates = _generate(departure_date)
        return_dates = _generate(return_date)
        return outbound_dates, return_dates
    else:
        return _generate(departure_date)