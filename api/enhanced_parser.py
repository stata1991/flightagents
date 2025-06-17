from typing import Dict, Any, Optional, Tuple, List
import logging
from datetime import datetime, timedelta
import json
import re
import requests
from dateutil import parser as date_parser
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedQueryParser:
    def __init__(self, api_key: str):
        """Initialize the parser with API key."""
        self.api_key = api_key
        self.airports = self._load_airports_data()
        self.major_airports = self._load_major_airports()
        logger.info(f"Initialized parser with API key: {api_key[:10]}...")
        logger.info(f"Loaded {len(self.airports)} airports from full database")
        logger.info(f"Loaded {len(self.major_airports)} airports from major airports database")

    def _load_airports_data(self) -> List:
        """Load airports data from JSON file."""
        try:
            with open('api/airports-code@public.json', 'r', encoding='utf-8') as f:
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

    def _lookup_iata_code(self, location: str, context: Dict[str, Any] = None) -> Optional[str]:
        """
        Look up IATA code for a location using a two-step process:
        1. First check major_airports_filtered.json
        2. If no match found, fall back to full airports database
        """
        if not location:
            return None
            
        # Clean and normalize the input
        location = location.lower().strip()
        logger.info(f"Looking up IATA code for: {location}")
        
        # First check if it's already an IATA code
        if self._is_iata_code(location):
            return location.upper()

        # Get expected country from context
        expected_country = None
        if context and 'country_context' in context:
            country_context = context['country_context']
            if location.lower() == 'london' and 'origin' in country_context:
                expected_country = country_context['origin']
            elif location.lower() == 'new york' and 'destination' in country_context:
                expected_country = country_context['destination']
            
        logger.info(f"Expected country for {location}: {expected_country}")

        # Step 1: Check major airports first
        logger.info("Step 1: Checking major airports database...")
        major_matches = []
        for airport in self.major_airports:
            city_name = airport.get('city_name', '').lower()
            airport_name = airport.get('airport_name', '').lower()
            iata_code = airport.get('column_1', '')
            country = airport.get('country_name', '')
            
            if location in city_name or location in airport_name:
                # Score the airport based on its characteristics
                score = 0
                
                # Country matching is most important
                if expected_country and country == expected_country:
                    score += 1000
                elif expected_country:
                    continue  # Skip airports in wrong country
                
                # Major international airport scoring
                if iata_code in ['LHR', 'JFK', 'LGW', 'LGA']:  # Major international airports
                    score += 500
                elif 'international' in airport_name.lower():
                    score += 200
                
                # Specific airport importance
                if 'heathrow' in airport_name.lower():
                    score += 300
                elif 'jfk' in airport_name.lower() or 'kennedy' in airport_name.lower():
                    score += 300
                elif 'gatwick' in airport_name.lower():
                    score += 200
                elif 'la guardia' in airport_name.lower():
                    score += 200
                
                # Penalize non-airport facilities
                if any(term in airport_name.lower() for term in ['heliport', 'terminal', 'spb', 'landing']):
                    score -= 1000
                
                # Context-based scoring
                if context:
                    if context.get('is_international', False):
                        if 'international' in airport_name.lower():
                            score += 100
                        if iata_code in ['LHR', 'JFK', 'LGW', 'LGA']:
                            score += 200
                    if context.get('preferred_airport_type') == 'international':
                        if 'international' in airport_name.lower():
                            score += 100
                        if iata_code in ['LHR', 'JFK', 'LGW', 'LGA']:
                            score += 200
                
                major_matches.append((airport, iata_code, score))
                logger.info(f"Found match in major airports: {airport_name} ({iata_code}) - Score: {score}")
        
        if major_matches:
            # Sort by score and return the highest scoring airport
            major_matches.sort(key=lambda x: x[2], reverse=True)
            best_match = major_matches[0]
            logger.info(f"Selected from major airports: {best_match[0].get('airport_name')} ({best_match[1]}) with score {best_match[2]}")
            return best_match[1]

        # Step 2: If no match in major airports, check full database
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
            name_patterns = {
                'international': 'international' in name,
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
                'is_correct_country': expected_country and country == expected_country
            }

        def score_airport(airport: dict, analysis: dict, context: Dict[str, Any] = None) -> float:
            """
            Score an airport based on its data analysis and context.
            Higher score means better airport.
            """
            score = 0.0
            
            # Country matching is the most important factor
            if expected_country:
                if analysis['country'] == expected_country:
                    score += 1000.0  # Strongly favor correct country
                else:
                    return -10000.0  # Completely reject wrong country
            
            # Context-based scoring
            if context:
                # Airport type preference
                preferred_type = context.get('preferred_airport_type', 'any')
                if preferred_type == 'major' and analysis['major_indicators'] > 0:
                    score += 3.0
                elif preferred_type == 'international' and analysis['patterns']['international']:
                    score += 3.0
            
            # Base scoring from patterns
            if analysis['patterns']['international']:
                score += 3.0
            if analysis['patterns']['hub']:
                score += 2.0
            if analysis['patterns']['terminal']:
                score += 1.0
                
            # Major airport indicators
            score += analysis['major_indicators'] * 1.0
            
            # Primary city and name factors
            if analysis['is_primary_city']:
                score += 2.0
            if analysis['has_city_name']:
                score += 1.0
                
            # Penalties
            if analysis['patterns']['regional'] or analysis['patterns']['municipal']:
                score -= 2.0
            if analysis['patterns']['private']:
                score -= 3.0
            if analysis['patterns']['military']:
                score -= 2.0
            if analysis['patterns']['cargo']:
                score -= 1.0
                
            return score

        # Find all matching airports
        matching_airports = []
        for airport in self.airports:
            city_name = airport.get('city_name', '').lower()
            airport_name = airport.get('airport_name', '').lower()
            
            # Check for matches in city name or airport name
            if (location in city_name or location in airport_name):
                analysis = analyze_airport_data(airport)
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
            if expected_country:
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
                        "content": "You are a flight search assistant. Extract flight search parameters from user queries. Return a JSON object with 'origin', 'destination', 'date' (in YYYY-MM-DD format), 'return_date' (in YYYY-MM-DD format, if present for round-trip), and 'context' (with 'is_international' and 'preferred_airport_type')."
                    },
                    {
                        "role": "user",
                        "content": query
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
                    origin = extracted_data.get('origin')
                    destination = extracted_data.get('destination')
                    
                    if not origin or not destination:
                        logger.error("Could not determine origin or destination")
                        return {"error": "Could not determine origin or destination"}
                    
                    origin_iata = self._lookup_iata_code(origin, context)
                    dest_iata = self._lookup_iata_code(destination, context)
                    
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