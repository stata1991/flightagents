from datetime import datetime, timedelta
from typing import List, Tuple, Optional,Union
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