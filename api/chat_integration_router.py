#!/usr/bin/env python3
"""
Chat Integration Router
Connects the enhanced chat interface with the main trip planning flow
"""
import uuid
import logging
from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import re
from dateutil import parser as date_parser

from api.models import TripPlanningRequest, TripType, BudgetRange
from api.enhanced_ai_provider import EnhancedAITripProvider
from api.trip_planner_interface import TripPlanRequest
from services.conversation_service import ConversationService
from services.smart_destination_service import SmartDestinationService

router = APIRouter(prefix="/chat-integration", tags=["Chat Integration"])
logger = logging.getLogger(__name__)

# Initialize services
conversation_service = ConversationService()
smart_destination_service = SmartDestinationService()
enhanced_ai_provider = EnhancedAITripProvider()

@router.post("/process-message")
async def process_chat_message(request: Dict[str, Any]):
    """
    Process a message from the enhanced chat interface and return appropriate response
    """
    try:
        message = request.get("message", "").strip()
        session_id = request.get("session_id")
        conversation_state = request.get("conversation_state", {})
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Process the message through conversation service
        response = conversation_service.process_user_input(message, conversation_state.get("current_state", "greeting"), conversation_state)
        
        # Check if we have enough information to start trip planning
        trip_request = await _extract_trip_request(message, conversation_state)
        
        if trip_request and _has_sufficient_info(trip_request):
            # We have enough info to start planning
            planning_result = await _start_trip_planning(trip_request)
            
            return {
                "session_id": session_id,
                "response": response,
                "can_start_planning": True,
                "trip_request": trip_request.dict() if trip_request else None,
                "planning_result": planning_result,
                "next_step": "show_itinerary"
            }
        else:
            # Need more information
            return {
                "session_id": session_id,
                "response": response,
                "can_start_planning": False,
                "missing_info": _get_missing_info(trip_request) if trip_request else None,
                "next_step": "continue_conversation"
            }
            
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-planning")
async def start_planning_from_chat(request: Dict[str, Any]):
    """
    Start trip planning with extracted information from chat
    """
    try:
        trip_request = TripPlanningRequest(**request.get("trip_request", {}))
        
        # Create enhanced AI trip plan request
        logger.info(f"Creating TripPlanRequest with duration_days: {trip_request.duration_days}")
        logger.info(f"trip_request type: {type(trip_request)}")
        logger.info(f"trip_request fields: {trip_request.dict()}")
        
        enhanced_request = TripPlanRequest(
            origin=trip_request.origin,
            destination=trip_request.destination,
            duration_days=trip_request.duration_days,
            start_date=trip_request.start_date,
            end_date=trip_request.end_date,
            travelers=trip_request.travelers,
            budget_range=str(trip_request.budget_range.value),  # Convert enum to string
            trip_type=str(trip_request.trip_type.value),  # Convert enum to string
            interests=trip_request.interests or [],
            special_requirements=trip_request.special_requirements or ""
        )
        logger.info(f"TripPlanRequest created successfully: {enhanced_request}")
        logger.info(f"enhanced_request fields: {enhanced_request.dict()}")
        
        # Generate trip plan using enhanced AI provider
        result = await enhanced_ai_provider.plan_trip(enhanced_request)
        
        if result.success:
            return {
                "success": True,
                "itinerary": result.itinerary,
                "booking_links": result.booking_links,
                "estimated_costs": result.estimated_costs,
                "metadata": result.metadata.dict() if result.metadata else None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate trip plan")
            
    except Exception as e:
        logger.error(f"Error starting planning from chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/extract-trip-info")
async def extract_trip_information(request: Dict[str, Any]):
    """
    Extract trip information from natural language input
    """
    try:
        message = request.get("message", "")
        conversation_state = request.get("conversation_state", {})
        
        # Use smart destination service to analyze the message
        smart_request = await smart_destination_service.create_smart_itinerary_request(message)
        
        # Extract trip details using conversation service
        trip_request = await _extract_trip_request(message, conversation_state)
        
        return {
            "extracted_info": smart_request,
            "trip_request": trip_request.dict() if trip_request else None,
            "confidence": _calculate_extraction_confidence(trip_request),
            "suggestions": _generate_suggestions(trip_request)
        }
        
    except Exception as e:
        logger.error(f"Error extracting trip information: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _extract_trip_request(message: str, conversation_state: Dict[str, Any]) -> Optional[TripPlanningRequest]:
    """Extract trip planning request from message and conversation state"""
    try:
        # Extract basic information from message
        origin = conversation_state.get("origin") or _extract_origin(message)
        destination = conversation_state.get("destination") or _extract_destination(message)
        travelers = conversation_state.get("travelers") or _extract_travelers(message)
        start_date = conversation_state.get("start_date") or _extract_start_date(message)
        end_date = conversation_state.get("end_date") or _extract_end_date(message)
        budget_range = conversation_state.get("budget_range") or _extract_budget(message)
        interests = conversation_state.get("interests") or _extract_interests(message)
        
        # Debug logging
        logger.info(f"Extracted origin: {origin}")
        logger.info(f"Extracted destination: {destination}")
        logger.info(f"Extracted travelers: {travelers}")
        logger.info(f"Extracted start_date: {start_date}")
        logger.info(f"Extracted budget_range: {budget_range}")
        logger.info(f"Message being processed: {message}")
        
        if not origin or not destination:
            logger.info("Missing origin or destination")
            return None
            
        return TripPlanningRequest(
            origin=origin,
            destination=destination,
            travelers=travelers or 1,
            start_date=start_date,
            end_date=end_date,
            duration_days=_extract_duration_days(message),
            budget_range=budget_range or BudgetRange.MODERATE,  # Use model default if None
            trip_type=TripType.LEISURE,  # Use model default
            interests=interests or [],
            special_requirements=""
        )
        
    except Exception as e:
        logger.error(f"Error extracting trip request: {e}")
        return None

def _extract_origin(message: str) -> Optional[str]:
    """Extract origin from message"""
    # Look for "from X to Y" pattern - handle multi-word cities
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    # Look for "go from X" pattern
    go_from_pattern = r"go\s+from\s+([a-zA-Z\s]+)"
    match = re.search(go_from_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    return None

def _extract_destination(message: str) -> Optional[str]:
    """Extract destination from message"""
    # Look for "from X to Y" pattern - handle multi-word cities
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        return match.group(2).strip().title()
    
    # Look for "go to X" pattern
    go_to_pattern = r"go\s+to\s+([a-zA-Z\s]+)"
    match = re.search(go_to_pattern, message.lower())
    if match:
        return match.group(1).strip().title()
    
    # Look for destination keywords
    destination_keywords = ["visit", "travel to", "explore"]
    for keyword in destination_keywords:
        if keyword in message.lower():
            # Extract the word after the keyword
            pattern = rf"{keyword}\s+([a-zA-Z\s]+)"
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1).strip().title()
    
    return None

def _extract_travelers(message: str) -> Optional[int]:
    """Extract number of travelers from message"""
    # Look for numbers followed by traveler keywords
    traveler_patterns = [
        r"(\d+)\s+(people|travelers|guests|adults)",
        r"(\d+)\s+(person|traveler|guest|adult)",
        r"(solo|alone|myself)",
        r"(couple|romantic|boyfriend|girlfriend)",
        r"(family|kids|children)"
    ]
    
    for pattern in traveler_patterns:
        match = re.search(pattern, message.lower())
        if match:
            if pattern == r"(solo|alone|myself)":
                return 1
            elif pattern == r"(couple|romantic|boyfriend|girlfriend)":
                return 2
            elif pattern == r"(family|kids|children)":
                # Extract family size if mentioned, otherwise default to 4 for family
                family_size_match = re.search(r"(\d+)\s+(people|travelers|guests|adults)", message.lower())
                if family_size_match:
                    return int(family_size_match.group(1))
                return 4  # Default family size
            else:
                return int(match.group(1))
    
    return None

def _extract_start_date(message: str) -> Optional[str]:
    """Extract start date from message"""
    # Look for date patterns
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # MM/DD/YYYY
        r"(\w+)\s+(\d{1,2})",  # Month Day
        r"(\d{1,2})\s+(\w+)",  # Day Month
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, message.lower())
        if match:
            try:
                # Try to parse the date
                date_str = match.group(0)
                parsed_date = date_parser.parse(date_str, fuzzy=True)
                return parsed_date.strftime("%Y-%m-%d")
            except:
                continue
    
    # If no specific date found, return None and let the planning system handle it
    return None

def _extract_end_date(message: str) -> Optional[str]:
    """Extract end date from message"""
    # For now, we'll use start_date + 7 days as default
    # This can be enhanced with more sophisticated date extraction
    return None

def _extract_budget(message: str) -> Optional[str]:
    """Extract budget range from message"""
    budget_keywords = {
        "budget": ["budget", "cheap", "affordable", "low cost"],
        "moderate": ["moderate", "reasonable", "standard"],
        "luxury": ["luxury", "premium", "high end", "expensive"]
    }
    
    message_lower = message.lower()
    for budget_range, keywords in budget_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return budget_range
    
    return None

def _extract_duration_days(message: str) -> Optional[int]:
    """Extract duration in days from message"""
    # Look for patterns like "for X days", "X days", "X-day trip"
    duration_patterns = [
        r"for\s+(\d+)\s+days?",
        r"(\d+)\s+days?",
        r"(\d+)-day\s+trip",
        r"(\d+)\s+day\s+trip"
    ]
    
    message_lower = message.lower()
    for pattern in duration_patterns:
        match = re.search(pattern, message_lower)
        if match:
            days = int(match.group(1))
            return days
    
    return None

def _extract_interests(message: str) -> Optional[List[str]]:
    """Extract interests from message"""
    interests = []
    
    interest_keywords = {
        "beach": ["beach", "ocean", "sea", "coastal"],
        "culture": ["culture", "museum", "history", "art", "heritage"],
        "adventure": ["adventure", "hiking", "outdoor", "nature"],
        "nightlife": ["nightlife", "party", "club", "bar"],
        "shopping": ["shopping", "market", "mall", "retail"],
        "food": ["food", "cuisine", "restaurant", "dining", "gastronomy"],
        "relaxation": ["relax", "spa", "wellness", "peaceful"],
        "romance": ["romantic", "couple", "honeymoon", "romance"]
    }
    
    message_lower = message.lower()
    for interest, keywords in interest_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            interests.append(interest)
    
    return interests if interests else None

def _has_sufficient_info(trip_request: TripPlanningRequest) -> bool:
    """Check if we have sufficient information to start planning"""
    return (
        trip_request.origin and 
        trip_request.destination and 
        trip_request.travelers
        # start_date is optional - we can plan without a specific date
    )

def _get_missing_info(trip_request: TripPlanningRequest) -> List[str]:
    """Get list of missing information"""
    missing = []
    
    if not trip_request.origin:
        missing.append("origin")
    if not trip_request.destination:
        missing.append("destination")
    if not trip_request.travelers:
        missing.append("number of travelers")
    if not trip_request.start_date:
        missing.append("start date")
    if not trip_request.end_date:
        missing.append("end date")
    if not trip_request.budget_range:
        missing.append("budget preference")
    
    return missing

def _calculate_extraction_confidence(trip_request: Optional[TripPlanningRequest]) -> float:
    """Calculate confidence score for extracted information"""
    if not trip_request:
        return 0.0
    
    total_fields = 6  # origin, destination, travelers, start_date, end_date, budget_range
    filled_fields = 0
    
    if trip_request.origin:
        filled_fields += 1
    if trip_request.destination:
        filled_fields += 1
    if trip_request.travelers:
        filled_fields += 1
    if trip_request.start_date:
        filled_fields += 1
    if trip_request.end_date:
        filled_fields += 1
    if trip_request.budget_range:
        filled_fields += 1
    
    return filled_fields / total_fields

def _generate_suggestions(trip_request: Optional[TripPlanningRequest]) -> List[str]:
    """Generate suggestions based on extracted information"""
    suggestions = []
    
    if not trip_request:
        suggestions.append("Please provide your origin and destination")
        return suggestions
    
    if not trip_request.origin:
        suggestions.append("Where are you traveling from?")
    if not trip_request.destination:
        suggestions.append("Where would you like to go?")
    if not trip_request.travelers:
        suggestions.append("How many people are traveling?")
    if not trip_request.start_date:
        suggestions.append("When would you like to travel?")
    if not trip_request.budget_range:
        suggestions.append("What's your budget preference?")
    
    return suggestions

async def _start_trip_planning(trip_request: TripPlanningRequest) -> Dict[str, Any]:
    """Start the trip planning process"""
    try:
        # Create enhanced AI trip plan request
        enhanced_request = TripPlanRequest(
            origin=trip_request.origin,
            destination=trip_request.destination,
            duration_days=trip_request.duration_days,
            start_date=trip_request.start_date,
            end_date=trip_request.end_date,
            travelers=trip_request.travelers,
            budget_range=str(trip_request.budget_range.value),  # Convert enum to string
            trip_type=str(trip_request.trip_type.value),  # Convert enum to string
            interests=trip_request.interests or [],
            special_requirements=trip_request.special_requirements or ""
        )
        
        # Generate trip plan using enhanced AI provider
        result = await enhanced_ai_provider.plan_trip(enhanced_request)
        
        return {
            "success": result.success,
            "itinerary": result.itinerary if result.success else {},
            "booking_links": result.booking_links if result.success else {},
            "estimated_costs": result.estimated_costs if result.success else {},
            "metadata": result.metadata.dict() if result.metadata else None
        }
        
    except Exception as e:
        logger.error(f"Error starting trip planning: {e}")
        return {
            "success": False,
            "error": str(e)
        } 