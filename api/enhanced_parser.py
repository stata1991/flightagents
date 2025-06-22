from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime, timedelta
import json
import re
import requests
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _resolve_relative_dates(query: str) -> str:
    """Resolve relative dates in the query string."""
    today = datetime.now()
    query_lower = query.lower()

    # Handle specific dates like "June 23rd", "June 30th", "March 15th"
    # Pattern: month name + day with ordinal suffix
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    # Pattern to match "Month Day" or "Month Dayth/st/nd/rd"
    # Process all matches, not just the first one
    for month_name, month_number in months.items():
        # Match patterns like "june 23rd", "june 30th", "march 15th"
        pattern = r'\b' + month_name + r'\s+(\d{1,2})(?:st|nd|rd|th)?\b'
        
        # Find all matches for this month
        matches = list(re.finditer(pattern, query_lower))
        for match in reversed(matches):  # Process in reverse order to avoid index issues
            day = int(match.group(1))
            target_year = today.year
            
            # If the date is in the past for the current year, use next year
            target_date = datetime(target_year, month_number, day)
            if target_date < today:
                target_date = datetime(target_year + 1, month_number, day)
            
            # Replace the matched text with the formatted date
            start, end = match.span()
            query_lower = query_lower[:start] + target_date.strftime('%Y-%m-%d') + query_lower[end:]
            logger.info(f"Resolved specific date: {month_name} {day} -> {target_date.strftime('%Y-%m-%d')}")

    # Handle "tomorrow"
    if 'tomorrow' in query_lower:
        tomorrow_date = today + timedelta(days=1)
        query_lower = re.sub(r'\btomorrow\b', tomorrow_date.strftime('%Y-%m-%d'), query_lower)

    # Handle "next week"
    if 'next week' in query_lower:
        next_week_date = today + timedelta(days=7)
        query_lower = query_lower.replace('next week', next_week_date.strftime('%Y-%m-%d'))

    # Handle "next month"
    if 'next month' in query_lower:
        next_month_date = today + relativedelta(months=1)
        query_lower = query_lower.replace('next month', next_month_date.strftime('%Y-%m-%d'))

    # Handle days of the week (e.g., "this Friday")
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(days_of_week):
        if re.search(r'\b' + day + r'\b', query_lower):
            days_ahead = (i - today.weekday() + 7) % 7
            if days_ahead == 0:  # If it's today, assume next week
                days_ahead = 7
            target_date = today + timedelta(days=days_ahead)
            query_lower = re.sub(r'\b' + day + r'\b', target_date.strftime('%Y-%m-%d'), query_lower)
            break
            
    # Handle month names (e.g., "in August") - only if no specific date was found
    for month_name, month_number in months.items():
        # Use regex to find whole word, not followed by a number (to avoid "August 15th")
        pattern = r'\b' + month_name + r'\b(?!\s+\d)'
        if re.search(pattern, query_lower):
            target_year = today.year
            # If the month is in the past for the current year, use next year
            if month_number < today.month:
                target_year += 1
            
            target_date = datetime(target_year, month_number, 1)
            query_lower = re.sub(pattern, target_date.strftime('%Y-%m-%d'), query_lower)
            break
            
    return query_lower

class EnhancedQueryParser:
    def __init__(self, api_key: str):
        """Initialize the parser with API key."""
        self.api_key = api_key
        self.airports = self._load_airports_data()
        self.major_airports = self._load_major_airports()
        self.airport_importance = self._calculate_airport_importance()
        logger.info(f"Initialized parser with API key: {api_key[:10]}...")
        logger.info(f"Loaded {len(self.airports)} airports from full database")
        logger.info(f"Loaded {len(self.major_airports)} airports from major airports database")
        logger.info(f"Calculated importance scores for {len(self.airport_importance)} airports.")

    def _calculate_airport_importance(self) -> Dict[str, int]:
        """
        Pre-calculate an importance score for all airports.
        This uses the full airport database to create a score that can be
        used to resolve ambiguities when looking up airports.
        """
        if not self.airports:
            return {}

        scores = {}
        for airport in self.airports:
            iata_code = airport.get('column_1')
            if not iata_code:
                continue

            score = 0
            name = airport.get('airport_name', '').lower()
            
            # Highest bonus for major international hubs by name
            major_hubs = ['heathrow', 'jfk', 'charles de gaulle', 'changi', 'incheon', 'dubai', 'amsterdam', 'frankfurt', 'tokyo haneda', 'orly', 'peking', 'beijing capital', 'pudong', 'hongqiao']
            if 'international' in name or any(hub in name for hub in major_hubs):
                score += 2000
            
            # Bonus for "capital" airports (like Beijing Capital)
            if 'capital' in name:
                score += 1500
            
            # Bonus for major city names in airport names
            major_cities = ['beijing', 'shanghai', 'london', 'paris', 'new york', 'tokyo', 'dubai', 'singapore', 'seoul', 'frankfurt', 'amsterdam']
            if any(city in name for city in major_cities):
                score += 1000
            
            # Generic 'airport' is good
            if 'airport' in name:
                score += 100

            # Penalties for non-primary airports
            penalty_terms = ['heliport', 'seaplane', 'base', 'station', 'regional', 'pontoise', 'beauvais', 'la defense', 'le bourget', 'nanyuan', 'hongqiao']
            if any(term in name for term in penalty_terms):
                score -= 3000
            
            scores[iata_code] = score
        return scores

    def _load_airports_data(self) -> List:
        """Load airports data from JSON file."""
        try:
            # The airport codes file is stored in the repository as
            # ``airports-code.json``. The previous path used an
            # ``@public`` suffix which does not exist and resulted in the
            # parser failing to load the full airport database.  Attempting
            # to open the missing file caused an exception and left
            # ``self.airports`` empty, so lookups relied solely on the small
            # ``major_airports_filtered.json`` dataset.  This led to
            # incorrect matches such as returning ``VGT`` for queries about
            # Las Vegas.  Use the correct file name instead so the full
            # airport list is available as a fallback.
            with open('api/airports-code.json', 'r', encoding='utf-8') as f:
                self.airports = json.load(f)
                
            # Log data structure analysis
            if self.airports:
                first_airport = self.airports[0]
                logger.info("Airport data structure analysis:")
                logger.info(f"Total airports: {len(self.airports)}")
                logger.info("Sample airport fields:")
                for key, value in first_airport.items():
                    logger.info(f"- {key}: {value}")
                
                # Analyze common patterns
                international_count = sum(1 for a in self.airports if 'international' in a.get('airport_name', '').lower())
                hub_count = sum(1 for a in self.airports if 'hub' in a.get('airport_name', '').lower())
                terminal_count = sum(1 for a in self.airports if 'terminal' in a.get('airport_name', '').lower())
                
                logger.info(f"\nAirport characteristics:")
                logger.info(f"- International airports: {international_count}")
                logger.info(f"- Hub airports: {hub_count}")
                logger.info(f"- Airports with terminals: {terminal_count}")
                
            return self.airports
        except Exception as e:
            logger.error(f"Error loading airports data: {str(e)}")
            return []

    def _load_major_airports(self) -> List[Dict[str, Any]]:
        """Load major airports data from JSON file."""
        try:
            with open('major_airports_filtered.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded {len(data)} major airports")
                return data
        except Exception as e:
            logger.error(f"Error loading major airports data: {str(e)}")
            return []

    def _lookup_iata_code(self, location: str, context: Dict[str, Any] = None, country_hint: str = None) -> Optional[str]:
        """
        Look up IATA code for a location using a two-tier approach:
        1. First check major_airports_filtered.json
        2. If multiple airports found, use detailed scoring from airports-code.json
        """
        if not location:
            return None
            
        location = location.lower().strip()
        logger.info(f"Looking up IATA code for: {location}")
        
        if self._is_iata_code(location):
            return location.upper()

        logger.info(f"Expected country for {location}: {country_hint}")

        # Step 1: Find all potential matches in the major airports list
        candidate_airports = []
        for airport in self.major_airports:
            city_name = airport.get('city_name', '').lower()
            country_name = airport.get('country_name', '').lower()

            # First, filter by country if a hint is provided
            if country_hint and country_name != country_hint.lower():
                continue
            
            # Then, check if the location is mentioned in the city name
            if location in city_name:
                iata_code = airport.get('column_1')
                if iata_code:
                    candidate_airports.append(airport)

        if not candidate_airports:
            logger.warning(f"No candidates found for '{location}' in major airports. Falling back to full search.")
            return self._fallback_lookup(location, context, country_hint)

        # Step 2: If multiple candidates, use detailed scoring from full airport database
        if len(candidate_airports) > 1:
            logger.info(f"Found {len(candidate_airports)} airports for {location}, using detailed scoring...")
            scored_candidates = []
            
            for airport in candidate_airports:
                iata_code = airport.get('column_1')
                
                # Get detailed information from the full airport database
                detailed_info = self._get_detailed_airport_info(iata_code)
                if detailed_info:
                    score = self._score_airport_detailed(detailed_info, context)
                else:
                    # Fallback to basic scoring if not found in detailed database
                    score = self.airport_importance.get(iata_code, -10000)
                
                scored_candidates.append((airport, iata_code, score))
                logger.info(f"Candidate: {airport.get('airport_name')} ({iata_code}), Score: {score}")

            # Select the best candidate
            if scored_candidates:
                scored_candidates.sort(key=lambda x: x[2], reverse=True)
                best_airport, best_iata, best_score = scored_candidates[0]
                
                logger.info(f"Selected airport: {best_airport.get('airport_name')} ({best_iata}) for {location} with score {best_score}")
                return best_iata
        else:
            # Only one candidate, use it directly
            best_airport = candidate_airports[0]
            best_iata = best_airport.get('column_1')
            logger.info(f"Single candidate found: {best_airport.get('airport_name')} ({best_iata}) for {location}")
            return best_iata

        logger.warning(f"Could not find a suitable airport for {location}.")
        return None

    def _get_detailed_airport_info(self, iata_code: str) -> Optional[Dict]:
        """Get detailed airport information from the full airport database."""
        if not self.airports:
            return None
            
        for airport in self.airports:
            if airport.get('column_1') == iata_code:
                return airport
        return None

    def _score_airport_detailed(self, airport: Dict, context: Dict[str, Any] = None) -> float:
        """Score an airport using detailed information from the full database."""
        score = 0.0
        name = airport.get('airport_name', '').lower()
        iata_code = airport.get('column_1', '').lower()

        # Major international indicators
        if 'international' in name:
            score += 2000.0
        
        # Capital airports (like Beijing Capital)
        if 'capital' in name:
            score += 1500.0
        
        # Major hub indicators
        major_hubs = ['heathrow', 'jfk', 'lga', 'charles de gaulle', 'changi', 'incheon', 'dubai', 'amsterdam', 'frankfurt', 'tokyo haneda', 'orly', 'peking', 'beijing capital', 'pudong']
        if any(hub in name for hub in major_hubs) or iata_code in major_hubs:
            score += 2000.0
        
        # Major city names in airport names
        major_cities = ['beijing', 'shanghai', 'london', 'paris', 'new york', 'tokyo', 'dubai', 'singapore', 'seoul', 'frankfurt', 'amsterdam']
        if any(city in name for city in major_cities):
            score += 1000.0
        
        # Generic airport bonus
        if 'airport' in name:
            score += 100.0
        
        # Context-based scoring
        if context:
            if context.get('is_international', False) and 'international' in name:
                score += 500.0
            if context.get('preferred_airport_type') == 'primary' and 'international' in name:
                score += 300.0
        
        # Penalties for non-primary airports
        penalty_terms = ['heliport', 'seaplane', 'base', 'station', 'regional', 'pontoise', 'beauvais', 'la defense', 'le bourget', 'nanyuan']
        if any(term in name for term in penalty_terms):
            score -= 3000.0
        
        return score

    def _fallback_lookup(self, location: str, context: Dict[str, Any], country_hint: str) -> Optional[str]:
        """Fallback to searching the full airport database."""
        logger.info("Step 2: No match in major airports, checking full database...")
        if not self.airports:
            logger.error("No airports data loaded")
            return None
            
        def analyze_airport_data(airport: dict) -> dict:
            """
            Analyze airport data to determine its characteristics.
            Uses only the data available in our database.
            """
            name = airport.get('airport_name', '').lower()
            city = airport.get('city_name', '').lower()
            country = airport.get('country_name', '')
            
            # Analyze the airport name for patterns
            # Detect common keywords that indicate the airport's type.  In
            # addition to the full word ``international`` we also consider
            # the abbreviation ``intl`` which appears in many datasets.
            name_patterns = {
                'international': 'international' in name or 'intl' in name,
                'hub': 'hub' in name,
                'terminal': 'terminal' in name,
                'regional': 'regional' in name,
                'municipal': 'municipal' in name,
                'local': 'local' in name,
                'private': 'private' in name,
                'military': 'military' in name or 'air force' in name,
                'cargo': 'cargo' in name,
                'business': 'business' in name or 'executive' in name
            }
            
            # Count how many patterns indicate a major airport
            major_indicators = sum(1 for v in name_patterns.values() if v)
            
            return {
                'patterns': name_patterns,
                'major_indicators': major_indicators,
                'is_primary_city': location in city,
                'name_length': len(name),
                'has_city_name': location in name,
                'country': country,
                'is_correct_country': country_hint and country == country_hint
            }

        def score_airport(airport: dict, analysis: dict, context: Dict[str, Any] = None) -> float:
            """
            Score an airport based on its data analysis and context.
            Higher score means better airport.
            """
            score = 0.0
            
            # Country matching is the most important factor
            if country_hint:
                if analysis['country'].lower() == country_hint.lower():
                    score += 2000.0  # Strongly favor correct country
                else:
                    return -10000.0  # Completely reject wrong country
            
            # Context-based scoring
            if context:
                # Airport type preference
                preferred_type = context.get('preferred_airport_type', 'any')
                if preferred_type == 'primary' and analysis['major_indicators'] > 0:
                    score += 3.0
                elif preferred_type == 'international' and analysis['patterns']['international']:
                    score += 5.0 # Increased bonus for international preference
            
            # Base scoring from patterns
            if analysis['patterns']['international']:
                # International airports are typically the primary choice for
                # commercial flights, so give them extra weight.
                score += 8.0 # Increased bonus
            if analysis['patterns']['hub']:
                score += 3.0
            if analysis['patterns']['terminal']:
                # Facilities described only as terminals are usually secondary
                # or regional airports, so slightly penalize them instead of
                # providing a bonus.
                score -= 2.0
                
            # Major airport indicators
            score += analysis['major_indicators'] * 1.5 # Increased weight
            
            # Primary city and name factors
            if analysis['is_primary_city']:
                score += 3.0
            if analysis['has_city_name']:
                score += 2.0
                
            # Add importance score
            iata_code = airport.get('column_1')
            score += self.airport_importance.get(iata_code, 0) / 100.0 # Scale down for fallback search

            # Penalties
            if any(p in analysis['patterns'] for p in ['regional', 'municipal', 'private', 'military', 'cargo']):
                score -= 5.0
                
            return score

        # Find all matching airports
        matching_airports = []
        for airport in self.airports:
            city_name = airport.get('city_name', '').lower()
            airport_name = airport.get('airport_name', '').lower()
            
            # Check for matches in city name or airport name
            if (location in city_name or location in airport_name):
                analysis = analyze_airport_data(airport)
                
                # Skip if country hint is provided and doesn't match
                if country_hint and not analysis['is_correct_country']:
                    continue

                score = score_airport(airport, analysis, context)
                matching_airports.append((airport, analysis, score))

        if not matching_airports:
            logger.warning(f"No matching airports found for: {location}")
            return None

        # Sort airports by score
        matching_airports.sort(key=lambda x: x[2], reverse=True)
        
        # Log detailed information about top matches
        logger.info(f"\nFound {len(matching_airports)} matching airports:")
        for airport, analysis, score in matching_airports[:3]:
            logger.info(f"\nAirport: {airport.get('airport_name')} ({airport.get('column_1')})")
            logger.info(f"Country: {analysis['country']}")
            logger.info(f"Score: {score:.1f}")
            logger.info("Characteristics:")
            for pattern, value in analysis['patterns'].items():
                if value:
                    logger.info(f"- {pattern}")
            logger.info(f"Major indicators: {analysis['major_indicators']}")
            if country_hint:
                logger.info(f"Country match: {analysis['is_correct_country']}")

        # Get the best matching airport
        best_airport, best_analysis, best_score = matching_airports[0]
        iata_code = best_airport.get('column_1')
        
        # If we have multiple good options, log them
        if len(matching_airports) > 1 and matching_airports[0][2] - matching_airports[1][2] < 1.0:
            logger.info("\nMultiple good options found. Consider adding more specific criteria.")
            for airport, analysis, score in matching_airports[:3]:
                if score > 0:
                    logger.info(f"Alternative: {airport.get('airport_name')} ({airport.get('column_1')})")

        logger.info(f"\nSelected airport: {iata_code} ({best_airport.get('airport_name')}) for {location}")
        return iata_code

    @staticmethod
    def _is_iata_code(code: str) -> bool:
        """Check if a string is a valid IATA code."""
        return len(code) == 3 and code.isalpha()

    async def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse a natural language query to extract flight search parameters.
        Returns a dictionary with origin, destination, and date.
        """
        try:
            # Pre-process the query to handle relative dates
            processed_query = _resolve_relative_dates(query)
            logger.info(f"Processed query with resolved dates: {processed_query}")

            # Call X API to extract flight information
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "grok-3",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a flight search assistant. Extract flight search parameters from user queries. Return a JSON object with 'origin': {'city': 'City Name', 'country': 'Country Name'}, 'destination': {'city': 'City Name', 'country': 'Country Name'}, 'date' (in YYYY-MM-DD format), 'return_date' (in YYYY-MM-DD format, if present), and 'context'. For context, determine if the flight is likely 'is_international' (boolean) and the 'preferred_airport_type' ('primary' for major cities, 'any' otherwise)."
                    },
                    {
                        "role": "user",
                        "content": processed_query
                    }
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"X API error: {error_text}")
                        raise Exception(f"X API error: {error_text}")
                    
                    result = await response.json()
                    logger.info(f"X API response: {json.dumps(result, indent=2)}")
                    
                    # Extract the response content
                    content = result['choices'][0]['message']['content']
                    
                    # Try to parse the content as JSON first
                    try:
                        extracted_data = json.loads(content)
                    except json.JSONDecodeError:
                        # If not JSON, try to extract information using regex
                        logger.info("Response is not JSON, using regex to extract information")
                        
                        # Extract origin
                        origin_match = re.search(r'Origin City:?\s*([^\n]+)', content, re.IGNORECASE)
                        if not origin_match:
                            origin_match = re.search(r'origin:?\s*([^\n,]+)', content, re.IGNORECASE)
                        
                        # Extract destination
                        dest_match = re.search(r'Destination City:?\s*([^\n]+)', content, re.IGNORECASE)
                        if not dest_match:
                            dest_match = re.search(r'destination:?\s*([^\n,]+)', content, re.IGNORECASE)
                        
                        # Extract date (departure)
                        date_match = re.search(r'Date:?\s*(\d{4}-\d{2}-\d{2})', content)
                        # Extract return_date (for round-trip)
                        return_date_match = re.search(r'Return Date:?\s*(\d{4}-\d{2}-\d{2})', content)
                        if not return_date_match:
                            # Try alternative phrasing
                            return_date_match = re.search(r'return_date:?\s*(\d{4}-\d{2}-\d{2})', content)
                        
                        # Extract context
                        is_international = bool(re.search(r'international', content, re.IGNORECASE))
                        preferred_type = 'international' if is_international else 'any'
                        
                        extracted_data = {
                            "origin": origin_match.group(1).strip() if origin_match else None,
                            "destination": dest_match.group(1).strip() if dest_match else None,
                            "date": date_match.group(1) if date_match else None,
                            "return_date": return_date_match.group(1) if return_date_match else None,
                            "context": {
                                "is_international": is_international,
                                "preferred_airport_type": preferred_type
                            }
                        }
                    
                    logger.info(f"Extracted data: {json.dumps(extracted_data, indent=2)}")
                    
                    # Get context from the response
                    context = extracted_data.get('context', {})
                    
                    # Look up IATA codes
                    origin_details = extracted_data.get('origin')
                    destination_details = extracted_data.get('destination')
                    
                    if not origin_details or not destination_details:
                        logger.error("Could not determine origin or destination details from LLM")
                        return {"error": "Could not determine origin or destination details"}
                    
                    origin_iata = self._lookup_iata_code(origin_details.get('city'), context, origin_details.get('country'))
                    dest_iata = self._lookup_iata_code(destination_details.get('city'), context, destination_details.get('country'))
                    
                    if not origin_iata or not dest_iata:
                        logger.error("Could not find IATA codes for airports")
                        return {"error": "Could not find IATA codes for airports"}
                    
                    # Return the structured data
                    return {
                        "origin": origin_iata,
                        "destination": dest_iata,
                        "date": extracted_data.get('date'),
                        "return_date": extracted_data.get('return_date'),
                        "context": context
                    }
                    
        except Exception as e:
            logger.error(f"Error parsing query: {str(e)}")
            return {"error": str(e)}

# Create a singleton instance
query_parser = None

def get_parser(api_key: str) -> EnhancedQueryParser:
    """Factory function to create a parser instance."""
    global query_parser
    if query_parser is None:
        query_parser = EnhancedQueryParser(api_key)
    return query_parser 