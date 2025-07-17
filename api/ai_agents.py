import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from anthropic import AsyncAnthropic, HUMAN_PROMPT, AI_PROMPT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from api.models import TripPlanningRequest, ConversationState

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    COORDINATOR = "coordinator"
    DESTINATION_SPECIALIST = "destination_specialist"
    BUDGET_ANALYST = "budget_analyst"
    LOGISTICS_PLANNER = "logistics_planner"
    CULTURAL_ADVISOR = "cultural_advisor"
    BOOKING_AGENT = "booking_agent"
    FLIGHT_SEARCH_AGENT = "flight_search_agent"
    HOTEL_SEARCH_AGENT = "hotel_search_agent"

@dataclass
class AgentTask:
    agent_type: AgentType
    task_description: str
    required_data: Dict[str, Any]
    priority: int = 1
    dependencies: List[str] = None

@dataclass
class AgentResult:
    agent_type: AgentType
    result: Dict[str, Any]
    confidence: float
    reasoning: str
    timestamp: datetime

class AITripPlanningAgent:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.agents = {
            AgentType.COORDINATOR: self._coordinator_agent,
            AgentType.DESTINATION_SPECIALIST: self._destination_specialist_agent,
            AgentType.BUDGET_ANALYST: self._budget_analyst_agent,
            AgentType.LOGISTICS_PLANNER: self._logistics_planner_agent,
            AgentType.CULTURAL_ADVISOR: self._cultural_advisor_agent,
            AgentType.BOOKING_AGENT: self._booking_agent_agent,
            AgentType.FLIGHT_SEARCH_AGENT: self._flight_search_agent,
            AgentType.HOTEL_SEARCH_AGENT: self._hotel_search_agent
        }
        
    async def execute_agent_task(self, task: AgentTask) -> AgentResult:
        """Execute a specific agent task"""
        if task.agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {task.agent_type}")
        
        agent_func = self.agents[task.agent_type]
        result = await agent_func(task.task_description, task.required_data)
        
        return AgentResult(
            agent_type=task.agent_type,
            result=result,
            confidence=result.get('confidence', 0.8),
            reasoning=result.get('reasoning', ''),
            timestamp=datetime.now()
        )
    
    async def _coordinator_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Check if this is comprehensive planning mode
        if data.get("comprehensive_planning"):
            prompt = f"""You are a Comprehensive Trip Planning Expert. Create a complete trip plan including destination recommendations, detailed itinerary, and cultural insights.

USER REQUEST: {task}
TRIP DATA: {json.dumps(data, indent=2)}

Provide a comprehensive plan in JSON format including:

1. Trip Overview and Structure
2. Must-see attractions with specific names (e.g., "Golden Gate Bridge", "Eiffel Tower", "Colosseum")
3. Detailed day-by-day itinerary
4. Cultural insights and local customs
5. Budget considerations
6. Practical travel tips

Respond in JSON format:
{{
    "overview": {{
        "recommended_cities": [
            {{"city": "city_name", "nights": number, "reason": "why_visit"}}
        ],
        "route_sequence": ["city1", "city2", "city3"],
        "planning_priorities": ["priority1", "priority2"],
        "challenges": ["challenge1", "challenge2"],
        "special_considerations": ["consideration1", "consideration2"]
    }},
    "destination_recommendations": {{
        "best_time_to_visit": "season/month recommendation",
        "must_see_attractions": [
            {{
                "name": "Specific attraction name (e.g., Golden Gate Bridge, Eiffel Tower)",
                "location": "specific area/neighborhood",
                "time_needed": "2-3 hours",
                "best_time": "morning/afternoon/evening",
                "tips": "specific visiting tips",
                "category": "landmark/museum/park/entertainment",
                "entrance_fee": "free/paid amount",
                "booking_required": true/false
            }}
        ],
        "hidden_gems": [
            {{
                "name": "specific place name",
                "description": "why it's special",
                "location": "specific area",
                "category": "restaurant/viewpoint/neighborhood",
                "best_time": "time of day",
                "local_tip": "insider advice"
            }}
        ],
        "cultural_highlights": [
            {{
                "name": "specific cultural experience",
                "description": "cultural significance",
                "location": "where to find it",
                "best_time": "when to experience it",
                "duration": "how long it takes"
            }}
        ],
        "local_favorites": [
            {{
                "name": "specific restaurant/bar/activity",
                "type": "restaurant/bar/activity/shop",
                "why_recommended": "what makes it special",
                "location": "neighborhood",
                "price_range": "budget/moderate/expensive",
                "best_for": "breakfast/lunch/dinner/drinks"
            }}
        ],
        "day_by_day_suggestions": [
            {{
                "day": 1,
                "morning_activities": ["specific activity 1", "specific activity 2"],
                "afternoon_activities": ["specific activity 1", "specific activity 2", "specific activity 3"],
                "evening_activities": ["specific activity 1", "specific activity 2"],
                "lunch_spots": ["specific restaurant 1", "specific restaurant 2"],
                "dinner_spots": ["specific restaurant 1", "specific restaurant 2"],
                "accommodation_area": "specific neighborhood"
            }}
        ]
    }},
    "cultural_insights": {{
        "local_customs": ["custom1", "custom2"],
        "etiquette_tips": ["tip1", "tip2"],
        "cultural_highlights": ["highlight1", "highlight2"],
        "language_tips": ["tip1", "tip2"]
    }},
    "budget_considerations": {{
        "estimated_costs": {{
            "accommodation": "range",
            "meals": "range",
            "activities": "range",
            "transportation": "range"
        }},
        "cost_saving_tips": ["tip1", "tip2", "tip3"]
    }},
    "confidence": 0.9,
    "reasoning": "comprehensive planning explanation"
}}"""
        else:
            # Original coordinator logic for backward compatibility
            prompt = f"""You are the Master Trip Planning Coordinator. Your role is to:
1. Analyze the user's request and break it down into specialized tasks
2. Coordinate between different specialist agents
3. Ensure all aspects of the trip are properly planned
4. Make final decisions on itinerary structure

USER REQUEST: {task}
TRIP DATA: {json.dumps(data, indent=2)}

Based on this information, provide:
1. Recommended cities to visit (with number of nights)
2. Optimal route/sequence
3. Key planning priorities
4. Potential challenges to address
5. Special considerations for this trip type

Respond in JSON format:
{{
    "recommended_cities": [
        {{"city": "city_name", "nights": number, "reason": "why_visit"}}
    ],
    "route_sequence": ["city1", "city2", "city3"],
    "planning_priorities": ["priority1", "priority2"],
    "challenges": ["challenge1", "challenge2"],
    "special_considerations": ["consideration1", "consideration2"],
    "confidence": 0.9,
    "reasoning": "detailed explanation of decisions"
}}"""
        
        response = await self._call_claude(prompt)
        return response
    
    async def _destination_specialist_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Check if this is simple mode
        if data.get("simple_mode"):
            prompt = f"""You are a Destination Specialist for {data.get('destination', 'the destination')}. 
Provide essential recommendations quickly and concisely.

TASK: {task}
DESTINATION: {data.get('destination', 'Unknown')}
DURATION: {data.get('duration_days', 'Unknown')} days
INTERESTS: {data.get('interests', [])}

Provide key recommendations in JSON format with specific attraction names:

{{
    "must_see_attractions": [
        {{
            "name": "Specific attraction (e.g., Golden Gate Bridge, Eiffel Tower)",
            "location": "area",
            "time_needed": "hours",
            "tips": "brief tip"
        }}
    ],
    "day_by_day_suggestions": [
        {{
            "day": 1,
            "morning_activities": ["activity 1", "activity 2"],
            "afternoon_activities": ["activity 1", "activity 2"],
            "evening_activities": ["activity 1"],
            "lunch_spots": ["restaurant 1"],
            "dinner_spots": ["restaurant 1"],
            "accommodation_area": "neighborhood"
        }}
    ],
    "confidence": 0.9
}}"""
        else:
            # Original comprehensive prompt for backward compatibility
            prompt = f"""You are a Destination Specialist with deep knowledge of {data.get('destination', 'the destination')}. 
Your expertise includes:
- Best times to visit
- Must-see attractions with specific details
- Hidden gems and local favorites
- Cultural highlights
- Seasonal considerations
- Day-by-day activity suggestions

TASK: {task}
DESTINATION: {data.get('destination', 'Unknown')}
DURATION: {data.get('duration_days', 'Unknown')} days
INTERESTS: {data.get('interests', [])}

Provide comprehensive and specific recommendations in JSON format. For attractions, include real names like "Golden Gate Bridge", "Alcatraz Island", "Fisherman's Wharf" for San Francisco, or equivalent famous landmarks for other destinations:

{{
    "best_time_to_visit": "season/month recommendation",
    "must_see_attractions": [
        {{
            "name": "Specific attraction name (e.g., Golden Gate Bridge, Eiffel Tower, Colosseum)",
            "location": "specific area/neighborhood",
            "time_needed": "2-3 hours",
            "best_time": "morning/afternoon/evening",
            "tips": "specific visiting tips",
            "category": "landmark/museum/park/entertainment",
            "entrance_fee": "free/paid amount",
            "booking_required": true/false
        }}
    ],
    "hidden_gems": [
        {{
            "name": "specific place name",
            "description": "why it's special and worth visiting",
            "location": "specific area",
            "category": "restaurant/viewpoint/neighborhood",
            "best_time": "time of day",
            "local_tip": "insider advice"
        }}
    ],
    "cultural_highlights": [
        {{
            "name": "specific cultural experience",
            "description": "cultural significance and what to expect",
            "location": "where to find it",
            "best_time": "when to experience it",
            "duration": "how long it takes"
        }}
    ],
    "local_favorites": [
        {{
            "name": "specific restaurant/bar/activity",
            "type": "restaurant/bar/activity/shop",
            "why_recommended": "what makes it special",
            "location": "neighborhood",
            "price_range": "budget/moderate/expensive",
            "best_for": "breakfast/lunch/dinner/drinks"
        }}
    ],
    "day_by_day_suggestions": [
        {{
            "day": 1,
            "morning_activities": ["specific activity 1", "specific activity 2"],
            "afternoon_activities": ["specific activity 1", "specific activity 2", "specific activity 3"],
            "evening_activities": ["specific activity 1", "specific activity 2"],
            "lunch_spots": ["specific restaurant 1", "specific restaurant 2"],
            "dinner_spots": ["specific restaurant 1", "specific restaurant 2"],
            "accommodation_area": "specific neighborhood"
        }}
    ],
    "seasonal_considerations": ["specific consideration 1", "specific consideration 2"],
    "confidence": 0.9,
    "reasoning": "why these specific recommendations"
}}"""
        
        response = await self._call_claude(prompt)
        return response
    
    async def _budget_analyst_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # Check if this is simple mode
        if data.get("simple_mode"):
            prompt = f"""You are a Budget Analyst. Provide basic budget breakdown quickly.

TASK: {task}
TRIP DATA: {json.dumps(data, indent=2)}

Provide basic budget analysis in JSON format:
{{
    "budget_breakdown": {{
        "accommodation": "range",
        "meals": "range", 
        "activities": "range",
        "transportation": "range"
    }},
    "total_estimated_cost": "range",
    "cost_saving_tips": ["tip1", "tip2"],
    "confidence": 0.9
}}"""
        elif data.get("comprehensive_plan"):
            prompt = f"""You are a Practical Travel Planning Expert. Provide budget analysis and practical travel tips based on the comprehensive plan.

TASK: {task}
COMPREHENSIVE PLAN: {json.dumps(data.get("comprehensive_plan", {}), indent=2)}
TRIP DATA: {json.dumps(data, indent=2)}

Provide practical planning insights in JSON format:
{{
    "budget_breakdown": {{
        "flights": {{"estimated_cost": "range", "cost_factors": ["factor1", "factor2"]}},
        "accommodation": {{"estimated_cost": "range", "recommendations": ["type1", "type2"]}},
        "meals": {{"estimated_cost": "range", "dining_options": ["option1", "option2"]}},
        "activities": {{"estimated_cost": "range", "must_do": ["activity1", "activity2"]}},
        "transportation": {{"estimated_cost": "range", "options": ["option1", "option2"]}},
        "miscellaneous": {{"estimated_cost": "range", "items": ["item1", "item2"]}}
    }},
    "total_estimated_cost": "range",
    "cost_saving_tips": ["tip1", "tip2", "tip3"],
    "transportation_plan": [
        {{
            "from": "city1",
            "to": "city2",
            "method": "train/flight/bus/car",
            "duration": "time",
            "cost": "range",
            "frequency": "how_often",
            "booking_tips": "when_to_book",
            "alternatives": ["alt1", "alt2"]
        }}
    ],
    "travel_tips": ["tip1", "tip2", "tip3"],
    "booking_strategy": {{
        "accommodation": ["strategy1", "strategy2"],
        "activities": ["strategy1", "strategy2"],
        "transportation": ["strategy1", "strategy2"]
    }},
    "confidence": 0.9,
    "reasoning": "practical planning explanation"
}}"""
        else:
            # Original budget analyst logic for backward compatibility
            prompt = f"""You are a Budget Analyst specializing in travel cost optimization. 
Analyze the trip requirements and provide detailed budget breakdown.

TASK: {task}
TRIP DATA: {json.dumps(data, indent=2)}

Provide comprehensive budget analysis in JSON format:
{{
    "budget_breakdown": {{
        "flights": {{"estimated_cost": "range", "cost_factors": ["factor1", "factor2"]}},
        "accommodation": {{"estimated_cost": "range", "recommendations": ["type1", "type2"]}},
        "meals": {{"estimated_cost": "range", "dining_options": ["option1", "option2"]}},
        "activities": {{"estimated_cost": "range", "must_do": ["activity1", "activity2"]}},
        "transportation": {{"estimated_cost": "range", "options": ["option1", "option2"]}},
        "miscellaneous": {{"estimated_cost": "range", "items": ["item1", "item2"]}}
    }},
    "total_estimated_cost": "range",
    "cost_saving_tips": ["tip1", "tip2", "tip3"],
    "budget_optimization": ["optimization1", "optimization2"],
    "seasonal_price_variations": ["variation1", "variation2"],
    "confidence": 0.9,
    "reasoning": "budget analysis explanation"
}}"""
        
        response = await self._call_claude(prompt)
        return response
    
    async def _logistics_planner_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are a Logistics Planner specializing in travel logistics and transportation optimization.
Plan the most efficient routes and transportation between destinations.

TASK: {task}
CITIES: {data.get('cities', [])}
DURATION: {data.get('duration_days', 'Unknown')} days

Provide logistics plan in JSON format:
{{
    "transportation_plan": [
        {{
            "from": "city1",
            "to": "city2",
            "method": "train/flight/bus/car",
            "duration": "time",
            "cost": "range",
            "frequency": "how_often",
            "booking_tips": "when_to_book",
            "alternatives": ["alt1", "alt2"]
        }}
    ],
    "optimal_route": ["city1", "city2", "city3"],
    "travel_tips": ["tip1", "tip2"],
    "potential_issues": ["issue1", "issue2"],
    "contingency_plans": ["plan1", "plan2"],
    "confidence": 0.9,
    "reasoning": "logistics planning explanation"
}}"""
        response = await self._call_claude(prompt)
        return response
    
    async def _cultural_advisor_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are a Cultural Advisor with deep knowledge of local customs, etiquette, and cultural insights.
Provide cultural guidance for the destination.

TASK: {task}
DESTINATION: {data.get('destination', 'Unknown')}
TRIP_TYPE: {data.get('trip_type', 'Unknown')}

Provide cultural insights in JSON format:
{{
    "cultural_etiquette": [
        {{"topic": "dining", "guidelines": ["guideline1", "guideline2"]}},
        {{"topic": "greetings", "guidelines": ["guideline1", "guideline2"]}},
        {{"topic": "dress_code", "guidelines": ["guideline1", "guideline2"]}}
    ],
    "local_customs": ["custom1", "custom2", "custom3"],
    "cultural_highlights": [
        {{"experience": "activity", "cultural_significance": "explanation"}}
    ],
    "language_tips": ["phrase1", "phrase2", "phrase3"],
    "cultural_do_dont": {{
        "do": ["do1", "do2", "do3"],
        "dont": ["dont1", "dont2", "dont3"]
    }},
    "seasonal_cultural_events": ["event1", "event2"],
    "confidence": 0.9,
    "reasoning": "cultural insights explanation"
}}"""
        response = await self._call_claude(prompt)
        return response
    
    async def _booking_agent_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""You are a Booking Agent specializing in finding the best deals and booking strategies.
Provide booking recommendations and strategies.

TASK: {task}
TRIP_DATA: {json.dumps(data, indent=2)}

Provide booking strategy in JSON format:
{{
    "booking_timeline": {{
        "flights": "when_to_book",
        "hotels": "when_to_book",
        "activities": "when_to_book"
    }},
    "booking_platforms": [
        {{"type": "flights", "platforms": ["platform1", "platform2"], "tips": "booking_tips"}},
        {{"type": "hotels", "platforms": ["platform1", "platform2"], "tips": "booking_tips"}},
        {{"type": "activities", "platforms": ["platform1", "platform2"], "tips": "booking_tips"}}
    ],
    "money_saving_strategies": ["strategy1", "strategy2", "strategy3"],
    "flexibility_recommendations": ["recommendation1", "recommendation2"],
    "cancellation_policies": ["policy1", "policy2"],
    "confidence": 0.9,
    "reasoning": "booking strategy explanation"
}}"""
        response = await self._call_claude(prompt)
        return response
    
    async def _flight_search_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flight Search Agent that integrates with Booking.com API for real flight searches"""
        try:
            from api.booking_client import booking_client
            from api.enhanced_parser import EnhancedQueryParser
            from datetime import datetime, timedelta
            
            # Extract flight search parameters from the data
            origin = data.get('origin', '')
            destination = data.get('destination', '')
            start_date = data.get('start_date', '')
            duration_days = data.get('duration_days', 7)
            
            # Skip flight search if origin or destination is missing
            if not origin or not destination:
                return {
                    "flight_search_results": {
                        "message": "Flight search skipped - origin or destination not provided",
                        "origin": origin,
                        "destination": destination
                    },
                    "confidence": 0.5,
                    "reasoning": "Cannot search flights without origin and destination"
                }
            
            # If no start date provided, use a default (next week)
            if not start_date:
                start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Calculate return date for round-trip
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            return_date = (start_dt + timedelta(days=duration_days)).strftime('%Y-%m-%d')
            
            # Use the enhanced parser to get IATA codes
            parser = EnhancedQueryParser()
            origin_iata = parser._lookup_iata_code(origin)
            dest_iata = parser._lookup_iata_code(destination)
            
            if not origin_iata or not dest_iata:
                return {
                    "error": f"Could not find airport codes for {origin} or {destination}",
                    "confidence": 0.3,
                    "reasoning": "Airport lookup failed"
                }
            
            # Search for destinations to get location IDs
            origin_search = booking_client.search_destination(origin)
            dest_search = booking_client.search_destination(destination)
            
            if "error" in origin_search or "error" in dest_search:
                return {
                    "error": "Failed to search destinations",
                    "confidence": 0.3,
                    "reasoning": "Destination search failed"
                }
            
            # Get the first result for each location
            origin_id = origin_search.get('destinations', [{}])[0].get('id') if origin_search.get('destinations') else None
            dest_id = dest_search.get('destinations', [{}])[0].get('id') if dest_search.get('destinations') else None
            
            if not origin_id or not dest_id:
                return {
                    "error": "Could not find location IDs for flight search",
                    "confidence": 0.3,
                    "reasoning": "Location ID lookup failed"
                }
            
            # Search for round-trip flights
            flight_results = booking_client.search_flights(
                from_id=origin_id,
                to_id=dest_id,
                depart_date=start_date,
                return_date=return_date,
                adults=1,
                cabin_class="ECONOMY"
            )
            
            if "error" in flight_results:
                return {
                    "error": f"Flight search failed: {flight_results['error']}",
                    "confidence": 0.3,
                    "reasoning": "Flight search API error"
                }
            
            # Generate booking links
            booking_links = booking_client.generate_booking_links(
                from_id=origin_id,
                to_id=dest_id,
                depart_date=start_date,
                return_date=return_date,
                adults=1,
                cabin_class="ECONOMY"
            )
            
            # Process and format flight results based on actual API response structure
            formatted_flights = []
            if flight_results.get('status') and flight_results.get('data', {}).get('flightOffers'):
                flight_offers = flight_results['data']['flightOffers']
                
                for flight_offer in flight_offers[:5]:  # Top 5 results
                    try:
                        # Extract basic flight info
                        token = flight_offer.get('token', '')
                        segments = flight_offer.get('segments', [])
                        price_breakdown = flight_offer.get('priceBreakdown', {})
                        
                        if not segments:
                            continue
                        
                        # Process outbound segment (first segment)
                        outbound_segment = segments[0]
                        outbound_legs = outbound_segment.get('legs', [])
                        
                        if not outbound_legs:
                            continue
                        
                        outbound_leg = outbound_legs[0]
                        
                        # Extract airline info
                        carriers_data = outbound_leg.get('carriersData', [])
                        airline_name = carriers_data[0].get('name', 'Unknown') if carriers_data else 'Unknown'
                        airline_code = carriers_data[0].get('code', '') if carriers_data else ''
                        
                        # Extract flight times
                        departure_time = outbound_leg.get('departureTime', '')
                        arrival_time = outbound_leg.get('arrivalTime', '')
                        
                        # Convert duration from seconds to hours and minutes
                        total_time_seconds = outbound_leg.get('totalTime', 0)
                        hours = total_time_seconds // 3600
                        minutes = (total_time_seconds % 3600) // 60
                        duration_str = f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"
                        
                        # Extract price info
                        total_price = price_breakdown.get('total', {})
                        price_amount = total_price.get('units', 0) + (total_price.get('nanos', 0) / 1_000_000_000)
                        currency = total_price.get('currencyCode', 'USD')
                        
                        # Count stops
                        flight_stops = outbound_leg.get('flightStops', [])
                        stops_count = len(flight_stops)
                        
                        # Process return segment if it exists (round trip)
                        return_info = None
                        if len(segments) > 1:
                            return_segment = segments[1]
                            return_legs = return_segment.get('legs', [])
                            
                            if return_legs:
                                return_leg = return_legs[0]
                                return_carriers = return_leg.get('carriersData', [])
                                return_airline = return_carriers[0].get('name', 'Unknown') if return_carriers else 'Unknown'
                                
                                return_time_seconds = return_leg.get('totalTime', 0)
                                return_hours = return_time_seconds // 3600
                                return_minutes = (return_time_seconds % 3600) // 60
                                return_duration = f"{return_hours}h {return_minutes}m" if return_minutes > 0 else f"{return_hours}h"
                                
                                return_info = {
                                    "airline": return_airline,
                                    "departure_time": return_leg.get('departureTime', ''),
                                    "arrival_time": return_leg.get('arrivalTime', ''),
                                    "duration": return_duration,
                                    "stops": len(return_leg.get('flightStops', []))
                                }
                        
                        formatted_flight = {
                            "token": token,
                            "airline": airline_name,
                            "airline_code": airline_code,
                            "departure_time": departure_time,
                            "arrival_time": arrival_time,
                            "duration": duration_str,
                            "stops": stops_count,
                            "price": price_amount,
                            "currency": currency,
                            "trip_type": "round_trip" if return_info else "one_way",
                            "outbound": {
                                "airline": airline_name,
                                "departure_time": departure_time,
                                "arrival_time": arrival_time,
                                "duration": duration_str,
                                "stops": stops_count
                            }
                        }
                        
                        if return_info:
                            formatted_flight["inbound"] = return_info
                        
                        formatted_flights.append(formatted_flight)
                        
                    except Exception as e:
                        logger.error(f"Error processing flight offer: {e}")
                        continue
            
            return {
                "flight_search_results": {
                    "origin": origin,
                    "destination": destination,
                    "departure_date": start_date,
                    "return_date": return_date,
                    "total_flights_found": len(formatted_flights),
                    "flights": formatted_flights,
                    "booking_links": booking_links,
                    "search_metadata": {
                        "origin_iata": origin_iata,
                        "dest_iata": dest_iata,
                        "origin_id": origin_id,
                        "dest_id": dest_id,
                        "api_response_status": flight_results.get('status', False),
                        "total_offers_available": len(flight_results.get('data', {}).get('flightOffers', []))
                    }
                },
                "confidence": 0.9,
                "reasoning": f"Successfully found {len(formatted_flights)} flights from {origin} to {destination}"
            }
            
        except Exception as e:
            logger.error(f"Flight search agent error: {e}")
            return {
                "error": f"Flight search failed: {str(e)}",
                "confidence": 0.2,
                "reasoning": "Exception in flight search agent"
            }
    
    async def _hotel_search_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hotel Search Agent that integrates with Booking.com API for real hotel searches"""
        try:
            from api.hotel_client import HotelClient
            from api.models import HotelSearchRequest
            from datetime import datetime, timedelta
            
            # Extract hotel search parameters from the data
            destination = data.get('destination', '')
            start_date = data.get('start_date', '')
            duration_days = data.get('duration_days', 7)
            travelers = data.get('travelers', 1)
            budget_range = data.get('budget_range', 'moderate')
            
            # Skip hotel search if destination is missing
            if not destination:
                return {
                    "hotel_search_results": {
                        "message": "Hotel search skipped - destination not provided",
                        "destination": destination
                    },
                    "confidence": 0.5,
                    "reasoning": "Cannot search hotels without destination"
                }
            
            # If no start date provided, use a default (next week)
            if not start_date:
                start_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Calculate check-out date
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            check_out_date = (start_dt + timedelta(days=duration_days)).strftime('%Y-%m-%d')
            
            # Initialize hotel client
            hotel_client = HotelClient()
            
            # Create hotel search request
            hotel_request = HotelSearchRequest(
                location=destination,
                check_in=start_date,
                check_out=check_out_date,
                adults=travelers,
                children=[],
                rooms=1,
                currency="USD",
                language="en-us",
                page_number=1,
                order="price" if budget_range == "budget" else "rating"
            )
            
            # Search for hotels
            hotel_results = hotel_client.search_hotels(hotel_request)
            
            if hotel_results.search_metadata and "error" in hotel_results.search_metadata:
                return {
                    "error": f"Hotel search failed: {hotel_results.search_metadata['error']}",
                    "confidence": 0.3,
                    "reasoning": "Hotel search API error"
                }
            
            # Process and format hotel results
            formatted_hotels = []
            for hotel_result in hotel_results.hotels[:5]:  # Top 5 results
                hotel = hotel_result.hotel
                formatted_hotel = {
                    "hotel_id": hotel.hotel_id,
                    "name": hotel.name,
                    "address": hotel.address,
                    "city": hotel.city,
                    "country": hotel.country,
                    "rating": hotel.rating,
                    "review_score": hotel.review_score,
                    "review_count": hotel.review_count,
                    "star_rating": hotel.star_rating,
                    "property_type": hotel.property_type,
                    "amenities": hotel.amenities,
                    "photos": hotel.photos,
                    "average_price_per_night": hotel_result.average_price_per_night,
                    "total_price": hotel_result.total_price,
                    "currency": hotel_result.currency,
                    "availability": hotel_result.availability,
                    "rooms_available": len(hotel_result.rooms),
                    "booking_url": hotel.booking_url
                }
                formatted_hotels.append(formatted_hotel)
            
            # Generate booking URLs for top hotels
            booking_urls = {}
            for hotel in formatted_hotels[:3]:  # Top 3 hotels
                booking_url = hotel_client.generate_hotel_booking_url(
                    hotel_id=hotel["hotel_id"],
                    check_in=start_date,
                    check_out=check_out_date,
                    adults=travelers,
                    children=[],
                    rooms=1,
                    currency="USD"
                )
                booking_urls[hotel["hotel_id"]] = booking_url
            
            return {
                "hotel_search_results": {
                    "destination": destination,
                    "check_in_date": start_date,
                    "check_out_date": check_out_date,
                    "total_hotels_found": len(formatted_hotels),
                    "hotels": formatted_hotels,
                    "booking_urls": booking_urls,
                    "search_metadata": {
                        "total_results": hotel_results.total_results,
                        "currency": "USD"
                    }
                },
                "confidence": 0.9,
                "reasoning": f"Successfully found {len(formatted_hotels)} hotels in {destination}"
            }
            
        except Exception as e:
            logger.error(f"Hotel search agent error: {e}")
            return {
                "error": f"Hotel search failed: {str(e)}",
                "confidence": 0.2,
                "reasoning": "Exception in hotel search agent"
            }
    
    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """Make a call to Claude Sonnet v1 API (async) with timeout and retry logic"""
        import asyncio
        from anthropic import RateLimitError, APIError
        
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Add timeout to prevent hanging
                response = await asyncio.wait_for(
                    self.client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=4000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    ),
                    timeout=180.0  # 180 second timeout
                )
                
                # Claude v1 API: response.content is a list of MessageContentBlock objects
                content = response.content[0].text if response.content else ""
                
                # Log the raw response for debugging
                logger.info(f"Claude raw response (first 500 chars): {content[:500]}")
                
                # Extract JSON from response
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    try:
                        return json.loads(json_content)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error: {e}")
                        logger.error(f"Attempted to parse: {json_content[:200]}...")
                        return {"error": f"Invalid JSON format: {str(e)}", "raw_response": content[:500]}
                else:
                    logger.error(f"No JSON found in Claude response. Response preview: {content[:500]}")
                    return {"error": "No JSON found in response", "raw_response": content[:500]}
                    
            except asyncio.TimeoutError:
                logger.warning(f"Claude API timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    return {"error": "API request timed out after multiple attempts"}
                    
            except RateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return {"error": "API rate limit exceeded"}
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                await asyncio.sleep(delay)
                
            except APIError as e:
                logger.error(f"Claude API error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return {"error": f"API error: {str(e)}"}
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Unexpected error calling Claude on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    return {"error": str(e)}
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        return {"error": "All retry attempts failed"}
    
    async def plan_trip_with_agents(self, request: TripPlanningRequest) -> Dict[str, Any]:
        try:
            # Store the current request for duration calculation
            self._current_request = request
            
            # Start with a simple destination specialist for core attractions
            destination_task = AgentTask(
                agent_type=AgentType.DESTINATION_SPECIALIST,
                task_description="Provide essential destination recommendations and day-by-day itinerary",
                required_data={
                    "destination": request.destination,
                    "duration_days": request.duration_days,
                    "interests": request.interests,
                    "simple_mode": True
                }
            )
            destination_result = await self.execute_agent_task(destination_task)
            if "error" in destination_result.result:
                return {"error": destination_result.result["error"]}
            
            # Simple budget analysis
            budget_task = AgentTask(
                agent_type=AgentType.BUDGET_ANALYST,
                task_description="Provide basic budget breakdown and travel tips",
                required_data={
                    **request.dict(),
                    "simple_mode": True
                }
            )
            budget_result = await self.execute_agent_task(budget_task)
            
            # Flight search agent (keep this separate as it uses external API)
            flight_search_task = AgentTask(
                agent_type=AgentType.FLIGHT_SEARCH_AGENT,
                task_description="Search for real flight options using Booking.com API",
                required_data={
                    "origin": request.origin,
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "duration_days": request.duration_days,
                    "travelers": request.travelers
                }
            )
            flight_search_result = await self.execute_agent_task(flight_search_task)
            
            # Hotel search agent
            hotel_search_task = AgentTask(
                agent_type=AgentType.HOTEL_SEARCH_AGENT,
                task_description="Search for real hotel options using Booking.com API",
                required_data={
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "duration_days": request.duration_days,
                    "travelers": request.travelers,
                    "budget_range": request.budget_range
                }
            )
            hotel_search_result = await self.execute_agent_task(hotel_search_task)
            
            final_itinerary = self._combine_agent_results([
                destination_result,
                budget_result,
                flight_search_result,
                hotel_search_result
            ])
            return final_itinerary
        except Exception as e:
            logger.error(f"Error in multi-agent planning: {e}")
            return {"error": str(e)}
    def _combine_agent_results(self, agent_results: List[AgentResult]) -> Dict[str, Any]:
        combined = {
            "overview": {},
            "itinerary": [],
            "budget_breakdown": {},
            "practical_tips": [],
            "booking_notes": [],
            "cultural_insights": {},
            "agent_insights": {}
        }
        
        for result in agent_results:
            if result.agent_type == AgentType.DESTINATION_SPECIALIST:
                # Handle destination specialist results
                combined["destination_recommendations"] = result.result
                combined["agent_insights"]["destination"] = {
                    "confidence": result.confidence,
                    "reasoning": result.reasoning
                }
                
            elif result.agent_type == AgentType.BUDGET_ANALYST:
                # Handle budget analysis results
                combined["budget_breakdown"] = result.result.get("budget_breakdown", {})
                combined["cost_saving_tips"] = result.result.get("cost_saving_tips", [])
                
                combined["agent_insights"]["budget"] = {
                    "confidence": result.confidence,
                    "reasoning": result.reasoning
                }
                
            elif result.agent_type == AgentType.FLIGHT_SEARCH_AGENT:
                combined["flight_search_results"] = result.result.get("flight_search_results", {})
                combined["agent_insights"]["flight_search"] = {
                    "confidence": result.confidence,
                    "reasoning": result.reasoning
                }
            
            elif result.agent_type == AgentType.HOTEL_SEARCH_AGENT:
                combined["hotel_search_results"] = result.result.get("hotel_search_results", {})
                combined["agent_insights"]["hotel_search"] = {
                    "confidence": result.confidence,
                    "reasoning": result.reasoning
                }
        
        combined["itinerary"] = self._generate_daily_itinerary(combined)
        return combined
    def _generate_daily_itinerary(self, combined_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed day-by-day itinerary using AI agent recommendations"""
        try:
            # Extract key data from combined agent results
            destination_recs = combined_data.get("destination_recommendations", {})
            must_see_attractions = destination_recs.get("must_see_attractions", [])
            hidden_gems = destination_recs.get("hidden_gems", [])
            local_favorites = destination_recs.get("local_favorites", [])
            cultural_highlights = destination_recs.get("cultural_highlights", [])
            day_by_day_suggestions = destination_recs.get("day_by_day_suggestions", [])
            
            # Get trip details - use destination recommendations if overview not available
            overview = combined_data.get("overview", {})
            recommended_cities = overview.get("recommended_cities", [])
            
            # Calculate duration from the trip request if available
            duration_days = 1  # Default fallback
            if hasattr(self, '_current_request') and self._current_request:
                # Calculate days from start_date to return_date
                from datetime import datetime
                try:
                    start_date = datetime.strptime(self._current_request.start_date, '%Y-%m-%d')
                    return_date = datetime.strptime(self._current_request.end_date, '%Y-%m-%d')
                    duration_days = (return_date - start_date).days + 1  # Include both start and end days
                    logger.info(f"Calculated duration: {duration_days} days from {self._current_request.start_date} to {self._current_request.end_date}")
                except Exception as e:
                    logger.error(f"Error calculating duration from dates: {e}")
                    # Fallback to duration_days from request
                    duration_days = getattr(self._current_request, 'duration_days', 1)
            
            if not recommended_cities:
                # Fallback: create a simple city structure
                destination_recs = combined_data.get("destination_recommendations", {})
                if destination_recs:
                    recommended_cities = [{"city": "Destination", "nights": duration_days, "reason": "Main destination"}]
                else:
                    recommended_cities = [{"city": "Destination", "nights": duration_days, "reason": "Main destination"}]
            
            # Create detailed daily itinerary
            daily_itinerary = []
            
            for day in range(1, duration_days + 1):
                city_info = recommended_cities[day - 1] if day <= len(recommended_cities) else recommended_cities[0]
                city_name = city_info.get("city", "Destination")
                
                # Use day-by-day suggestions if available, otherwise distribute attractions
                day_suggestion = day_by_day_suggestions[day - 1] if day <= len(day_by_day_suggestions) else None
                
                if day_suggestion:
                    # Use specific day suggestions
                    morning_activities = day_suggestion.get("morning_activities", [])
                    afternoon_activities = day_suggestion.get("afternoon_activities", [])
                    evening_activities = day_suggestion.get("evening_activities", [])
                    lunch_spots = day_suggestion.get("lunch_spots", [])
                    dinner_spots = day_suggestion.get("dinner_spots", [])
                    accommodation_area = day_suggestion.get("accommodation_area", f"{city_name} City Center")
                else:
                    # Fallback: distribute attractions across multiple days
                    morning_activities = []
                    afternoon_activities = []
                    evening_activities = []
                    lunch_spots = []
                    dinner_spots = []
                    accommodation_area = f"{city_name} City Center"
                    
                    # Distribute must-see attractions across days
                    if must_see_attractions:
                        attractions_per_day = max(1, len(must_see_attractions) // duration_days)
                        start_idx = (day - 1) * attractions_per_day
                        end_idx = min(start_idx + attractions_per_day, len(must_see_attractions))
                        day_attractions = must_see_attractions[start_idx:end_idx]
                        
                        # Distribute day's attractions across morning/afternoon/evening
                        for i, attraction in enumerate(day_attractions):
                            if i < len(day_attractions) // 3:
                                morning_activities.append(attraction)
                            elif i < 2 * len(day_attractions) // 3:
                                afternoon_activities.append(attraction)
                            else:
                                evening_activities.append(attraction)
                    
                    # Add hidden gems and local favorites for this specific day
                    if hidden_gems and day <= len(hidden_gems):
                        afternoon_activities.append(hidden_gems[day - 1])
                    elif hidden_gems and len(hidden_gems) > 0:
                        # Cycle through hidden gems if more days than gems
                        afternoon_activities.append(hidden_gems[(day - 1) % len(hidden_gems)])
                    
                    if local_favorites and day <= len(local_favorites):
                        evening_activities.append(local_favorites[day - 1])
                    elif local_favorites and len(local_favorites) > 0:
                        # Cycle through local favorites if more days than favorites
                        evening_activities.append(local_favorites[(day - 1) % len(local_favorites)])
                
                # Create day structure
                day_plan = {
                    "day": day,
                    "city": city_name,
                    "morning": {
                        "activities": morning_activities[:2] if isinstance(morning_activities, list) else [],  # Limit to 2 morning activities
                        "start_time": "09:00",
                        "end_time": "12:00",
                        "transportation": "Walking/Public Transit"
                    },
                    "lunch": {
                        "recommendations": lunch_spots if lunch_spots else [
                            {"name": "Local Cafe", "type": "casual", "specialty": "Local cuisine"},
                            {"name": "Food Market", "type": "street food", "specialty": "Fresh local ingredients"}
                        ],
                        "time": "12:00-13:30"
                    },
                    "afternoon": {
                        "activities": afternoon_activities[:3] if isinstance(afternoon_activities, list) else [],  # Limit to 3 afternoon activities
                        "start_time": "13:30",
                        "end_time": "18:00",
                        "transportation": "Walking/Public Transit"
                    },
                    "dinner": {
                        "recommendations": dinner_spots if dinner_spots else [
                            {"name": "Fine Dining Restaurant", "type": "upscale", "specialty": "Regional specialties"},
                            {"name": "Local Bistro", "type": "casual", "specialty": "Authentic local dishes"}
                        ],
                        "time": "19:00-21:00"
                    },
                    "evening": {
                        "activities": evening_activities[:2] if isinstance(evening_activities, list) else [],  # Limit to 2 evening activities
                        "start_time": "21:00",
                        "end_time": "23:00",
                        "transportation": "Walking/Taxi"
                    },
                    "accommodation": {
                        "area": accommodation_area,
                        "recommendations": ["Boutique Hotel", "Luxury Hotel", "Budget Hotel"],
                        "booking_tip": "Book 2-3 months in advance for best rates"
                    },
                    "transportation": {
                        "within_city": "Public Transit/Walking",
                        "tips": ["Get a city pass for attractions", "Use ride-sharing for late night"]
                    },
                    "cultural_notes": cultural_highlights[:2] if cultural_highlights else [],
                    "practical_tips": [
                        "Wear comfortable walking shoes",
                        "Carry water and snacks",
                        "Check opening hours for attractions",
                        "Book popular attractions in advance"
                    ]
                }
                
                daily_itinerary.append(day_plan)
            
            return daily_itinerary
            
        except Exception as e:
            logger.error(f"Error generating daily itinerary: {e}")
            # Fallback to basic structure
            return [
                {
                    "day": 1,
                    "city": "Destination",
                    "morning": {
                        "activities": [{"name": "Explore city center", "location": "Downtown", "time_needed": "3 hours"}],
                        "start_time": "09:00",
                        "end_time": "12:00"
                    },
                    "lunch": {
                        "recommendations": [{"name": "Local restaurant", "type": "casual"}],
                        "time": "12:00-13:30"
                    },
                    "afternoon": {
                        "activities": [{"name": "Visit main attractions", "location": "Various", "time_needed": "4 hours"}],
                        "start_time": "13:30",
                        "end_time": "18:00"
                    },
                    "dinner": {
                        "recommendations": [{"name": "Dinner at local spot", "type": "casual"}],
                        "time": "19:00-21:00"
                    },
                    "evening": {
                        "activities": [{"name": "Evening entertainment", "location": "City center"}],
                        "start_time": "21:00",
                        "end_time": "23:00"
                    },
                    "accommodation": {"area": "City Center"},
                    "transportation": {"within_city": "Public Transit/Walking"},
                    "practical_tips": ["Wear comfortable shoes", "Carry water"]
                }
            ]

# Global instance
ai_agent = AITripPlanningAgent() 