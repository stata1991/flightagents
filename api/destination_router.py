from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
import os
from api.enhanced_parser import EnhancedQueryParser

router = APIRouter(prefix="/api/destinations", tags=["destinations"])

# Initialize the parser for airport data
parser = EnhancedQueryParser()

@router.get("/search")
async def search_destinations(q: str, limit: int = 10):
    """
    Search for destinations (cities, airports) with autocomplete functionality.
    
    Args:
        q: Search query (city name, airport code, or partial match)
        limit: Maximum number of results to return (default: 10)
    
    Returns:
        List of matching destinations with details
    """
    if not q or len(q.strip()) < 2:
        return {"destinations": []}
    
    query = q.strip().lower()
    results = []
    
    try:
        # Search in major airports first (faster and more relevant)
        major_airports = parser.major_airports if hasattr(parser, 'major_airports') else []
        
        for airport in major_airports:
            if _matches_query(airport, query):
                result = _format_airport_result(airport, query)
                if result:
                    results.append(result)
                    if len(results) >= limit:
                        break
        
        # If we don't have enough results, search in full database
        if len(results) < limit:
            full_airports = parser.airports if hasattr(parser, 'airports') else []
            
            for airport in full_airports:
                if _matches_query(airport, query) and not _already_in_results(airport, results):
                    result = _format_airport_result(airport, query)
                    if result:
                        results.append(result)
                        if len(results) >= limit:
                            break
        
        # Sort results by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return {
            "destinations": results[:limit],
            "query": q,
            "total_found": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching destinations: {str(e)}")

def _matches_query(airport, query):
    """Check if airport matches the search query."""
    # Check various fields for matches
    searchable_fields = [
        airport.get('airport_name', '').lower(),
        airport.get('city_name', '').lower(),
        airport.get('country_name', '').lower(),
        airport.get('column_1', '').lower(),  # IATA code
    ]
    
    # Check for exact matches first
    for field in searchable_fields:
        if query in field or field.startswith(query):
            return True
    
    # Check for partial word matches
    query_words = query.split()
    for field in searchable_fields:
        field_words = field.split()
        if any(word in field_words for word in query_words):
            return True
    
    return False

def _format_airport_result(airport, query):
    """Format airport data for API response."""
    try:
        # Calculate relevance score
        relevance_score = _calculate_relevance_score(airport, query)
        
        # Only include airports with reasonable relevance
        if relevance_score < 0.1:
            return None
        
        return {
            "id": airport.get('column_1', ''),  # IATA code
            "name": airport.get('airport_name', ''),
            "city": airport.get('city_name', ''),
            "country": airport.get('country_name', ''),
            "iata_code": airport.get('column_1', ''),
            "display_name": f"{airport.get('city_name', '')}, {airport.get('country_name', '')} ({airport.get('column_1', '')})",
            "relevance_score": relevance_score,
            "type": "airport",
            "coordinates": airport.get('coordinates', {})
        }
    except Exception:
        return None

def _calculate_relevance_score(airport, query):
    """Calculate relevance score for ranking results."""
    score = 0.0
    
    # Exact matches get highest scores
    if query == airport.get('column_1', '').lower():  # IATA code exact match
        score += 100
    elif query == airport.get('city_name', '').lower():  # City exact match
        score += 80
    elif query == airport.get('airport_name', '').lower():  # Airport name exact match
        score += 70
    
    # Partial matches
    if query in airport.get('column_1', '').lower():
        score += 50
    if query in airport.get('city_name', '').lower():
        score += 40
    if query in airport.get('airport_name', '').lower():
        score += 30
    
    # Boost major airports
    if hasattr(parser, 'major_airports') and airport in parser.major_airports:
        score += 20
    
    # Boost international airports
    if airport.get('world_area_code') == '67':  # International indicator
        score += 15
    
    return score

def _already_in_results(airport, results):
    """Check if airport is already in results to avoid duplicates."""
    airport_id = airport.get('column_1', '')
    return any(result['id'] == airport_id for result in results)

@router.get("/popular")
async def get_popular_destinations():
    """Get list of popular destinations for quick selection."""
    popular_destinations = [
        {"id": "NYC", "name": "New York", "country": "United States", "iata_code": "JFK", "display_name": "New York, United States (JFK)"},
        {"id": "LAX", "name": "Los Angeles", "country": "United States", "iata_code": "LAX", "display_name": "Los Angeles, United States (LAX)"},
        {"id": "LHR", "name": "London", "country": "United Kingdom", "iata_code": "LHR", "display_name": "London, United Kingdom (LHR)"},
        {"id": "CDG", "name": "Paris", "country": "France", "iata_code": "CDG", "display_name": "Paris, France (CDG)"},
        {"id": "FRA", "name": "Frankfurt", "country": "Germany", "iata_code": "FRA", "display_name": "Frankfurt, Germany (FRA)"},
        {"id": "NRT", "name": "Tokyo", "country": "Japan", "iata_code": "NRT", "display_name": "Tokyo, Japan (NRT)"},
        {"id": "SYD", "name": "Sydney", "country": "Australia", "iata_code": "SYD", "display_name": "Sydney, Australia (SYD)"},
        {"id": "YYZ", "name": "Toronto", "country": "Canada", "iata_code": "YYZ", "display_name": "Toronto, Canada (YYZ)"},
        {"id": "DXB", "name": "Dubai", "country": "United Arab Emirates", "iata_code": "DXB", "display_name": "Dubai, United Arab Emirates (DXB)"},
        {"id": "SIN", "name": "Singapore", "country": "Singapore", "iata_code": "SIN", "display_name": "Singapore, Singapore (SIN)"},
    ]
    
    return {"destinations": popular_destinations} 