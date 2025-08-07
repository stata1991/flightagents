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
from services.enhanced_entity_extractor import enhanced_entity_extractor
from services.contextual_followup_service import contextual_followup_service

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
        
        # Check if we have existing trip_data in conversation_state
        existing_trip_data = conversation_state.get("trip_data", {})
        
        # If we have existing trip_data, always use conversation service to allow updates
        if existing_trip_data:
            # Extract any new information from the message
            new_budget = _extract_budget(message)
            new_interests = _extract_interests(message)
            
            # Update existing trip_data with new information
            if new_budget:
                existing_trip_data["budget_range"] = new_budget
            if new_interests:
                existing_trip_data["interests"] = new_interests
            
            # Create trip_request from updated trip_data
            trip_request = TripPlanningRequest(
                origin=existing_trip_data.get("origin"),
                destination=existing_trip_data.get("destination"),
                travelers=existing_trip_data.get("travelers"),
                start_date=existing_trip_data.get("start_date"),
                end_date=existing_trip_data.get("end_date"),
                duration_days=existing_trip_data.get("duration_days"),
                budget_range=existing_trip_data.get("budget_range"),
                interests=existing_trip_data.get("interests", []),
                trip_type=TripType.LEISURE,
                special_requirements=""
            )
        else:
            # No existing trip_data, try to extract complete trip request
            trip_request = await _extract_trip_request(message, conversation_state)
        
        # Get missing information if trip request exists
        missing_info = None
        if trip_request:
            missing_info = _get_missing_info(trip_request)
            
            # If we have existing trip_data in conversation_state, merge it with the new trip_request
            if conversation_state.get("trip_data"):
                existing_trip_data = conversation_state["trip_data"]
                # Update trip_request with existing data that might not be in the new extraction
                if not trip_request.budget_range and existing_trip_data.get("budget_range"):
                    trip_request.budget_range = existing_trip_data["budget_range"]
                if not trip_request.interests and existing_trip_data.get("interests"):
                    trip_request.interests = existing_trip_data["interests"]
            
            # If we have existing trip_data, always call conversation service to allow updates
            if conversation_state.get("trip_data"):
                # Update conversation_state with the updated trip_data
                conversation_state["trip_data"] = existing_trip_data
                
                # Recalculate missing_info based on updated trip_data
                updated_missing_info = _get_missing_info(trip_request)
                
                # Call conversation service to allow updates to existing trip_data
                # Pass the updated trip_data directly to the conversation service
                response = await conversation_service.process_user_input(message, conversation_state.get("current_state", "greeting"), existing_trip_data, updated_missing_info)
                
                # Update conversation state with the response state
                conversation_state["current_state"] = response.get("state", "greeting")
                conversation_state.update(response.get("trip_data", {}))
                
                # Check if we now have sufficient info after the update
                if _has_sufficient_info(trip_request):
                    # We now have enough info to start planning
                    planning_result = await _start_trip_planning(trip_request)
                    
                    return {
                        "session_id": session_id,
                        "response": {
                            "message": "Perfect! I have all the information I need. Let me craft your perfect itinerary!",
                            "quick_replies": ["Show me the plan", "Modify details", "Start over"],
                            "state": "planning"
                        },
                        "can_start_planning": True,
                        "trip_request": trip_request.dict() if trip_request else None,
                        "planning_result": planning_result,
                        "next_step": "show_itinerary",
                        "conversation_state": conversation_state
                    }
                else:
                    return {
                        "session_id": session_id,
                        "response": response,
                        "can_start_planning": False,
                        "missing_info": missing_info,
                        "next_step": "continue_conversation",
                        "conversation_state": conversation_state
                    }
            else:
                # No existing trip_data, check if we have enough info to start planning
                if _has_sufficient_info(trip_request):
                    # We have enough info to start planning immediately
                    planning_result = await _start_trip_planning(trip_request)
                    
                    return {
                        "session_id": session_id,
                        "response": {
                            "message": "Perfect! I have all the information I need. Let me craft your perfect itinerary!",
                            "quick_replies": ["Show me the plan", "Modify details", "Start over"],
                            "state": "planning"
                        },
                        "can_start_planning": True,
                        "trip_request": trip_request.dict() if trip_request else None,
                        "planning_result": planning_result,
                        "next_step": "show_itinerary",
                        "conversation_state": conversation_state
                    }
                else:
                    # Need more information - call conversation service
                    response = await conversation_service.process_user_input(message, conversation_state.get("current_state", "greeting"), conversation_state, missing_info)
                    
                    # Update conversation state with the response state
                    conversation_state["current_state"] = response.get("state", "greeting")
                    conversation_state.update(response.get("trip_data", {}))
                    
                    return {
                        "session_id": session_id,
                        "response": response,
                        "can_start_planning": False,
                        "missing_info": missing_info,
                        "next_step": "continue_conversation",
                        "conversation_state": conversation_state
                    }
        else:
            # If trip_request is None, we need to extract basic info to determine what's missing
            origin = _extract_origin(message)
            destination = _extract_destination(message)
            travelers = _extract_travelers(message)
            duration_days = _extract_duration_days(message)
            start_date = _extract_start_date(message)
            
            missing_info = []
            if not origin:
                missing_info.append("origin")
            if not destination:
                missing_info.append("destination")
            if not travelers:
                missing_info.append("number of travelers")
            if not duration_days:
                missing_info.append("duration_days")
            if not start_date:
                missing_info.append("start date")
            
            # Create trip_request to check if we have sufficient info
            trip_request = await _extract_trip_request(message, conversation_state)
            
            # Check if we have enough info to start planning BEFORE calling conversation service
            if trip_request and _has_sufficient_info(trip_request):
                # We have enough info to start planning immediately
                planning_result = await _start_trip_planning(trip_request)
                
                return {
                    "session_id": session_id,
                    "response": {
                        "message": "Perfect! I have all the information I need. Let me craft your perfect itinerary!",
                        "quick_replies": ["Show me the plan", "Modify details", "Start over"],
                        "state": "planning"
                    },
                    "can_start_planning": True,
                    "trip_request": trip_request.dict() if trip_request else None,
                    "planning_result": planning_result,
                    "next_step": "show_itinerary",
                    "conversation_state": conversation_state
                }
            else:
                # Need more information - call conversation service
                if not missing_info:  # If we have basic info but validation failed
                    missing_info.append("complete trip details")
                
                # Process the message through conversation service with missing info context
                response = await conversation_service.process_user_input(message, conversation_state.get("current_state", "greeting"), conversation_state, missing_info)
                
                # Update conversation state with the response state
                conversation_state["current_state"] = response.get("state", "greeting")
                conversation_state.update(response.get("trip_data", {}))
                
                return {
                    "session_id": session_id,
                    "response": response,
                    "can_start_planning": False,
                    "missing_info": missing_info,
                    "next_step": "continue_conversation",
                    "conversation_state": conversation_state
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
        
        logger.info(f"Starting trip planning for: {trip_request.origin} to {trip_request.destination}")
        logger.info(f"Trip request fields: {trip_request.dict()}")
        
        # Use the _start_trip_planning function which has proper error handling
        result = await _start_trip_planning(trip_request)
        
        if result.get("success"):
            return result
        else:
            error_msg = result.get("error", "Failed to generate trip plan")
            logger.error(f"Trip planning failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
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
    """Extract trip planning request from message and conversation state using enhanced entity extraction"""
    try:
        # Use enhanced entity extraction if available (temporarily disabled due to API issues)
        if False and enhanced_entity_extractor.is_available():
            logger.info("Using enhanced entity extraction")
            extracted_data = await enhanced_entity_extractor.extract_trip_entities(message, conversation_state)
            
            # Update conversation state with extracted data
            conversation_state.update(extracted_data)
            
            # Extract from updated conversation state
            origin = conversation_state.get("origin")
            destination = conversation_state.get("destination")
            travelers = conversation_state.get("travelers")
            start_date = conversation_state.get("start_date")
            end_date = conversation_state.get("end_date")
            budget_range = conversation_state.get("budget_range")
            interests = conversation_state.get("interests")
            duration_days = conversation_state.get("duration_days")
        else:
            # Fallback to regex-based extraction
            logger.info("Using fallback regex extraction")
            # Always try to extract new information from the message first
            new_origin = _extract_origin(message)
            new_destination = _extract_destination(message)
            new_travelers = _extract_travelers(message)
            new_start_date = _extract_start_date(message)
            new_end_date = _extract_end_date(message)
            new_budget_range = _extract_budget(message)
            new_interests = _extract_interests(message)
            new_duration_days = _extract_duration_days(message)
            
            # Use new information if available, otherwise fall back to existing conversation state
            origin = new_origin or conversation_state.get("origin")
            destination = new_destination or conversation_state.get("destination")
            travelers = new_travelers or conversation_state.get("travelers")
            start_date = new_start_date or conversation_state.get("start_date")
            end_date = new_end_date or conversation_state.get("end_date")
            budget_range = new_budget_range or conversation_state.get("budget_range")
            interests = new_interests or conversation_state.get("interests")
            duration_days = new_duration_days or conversation_state.get("duration_days")
        
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
            
        # Calculate end_date from start_date + duration_days if both are available
        calculated_end_date = None
        if start_date and duration_days:
            try:
                from datetime import datetime, timedelta
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=duration_days)
                calculated_end_date = end_dt.strftime("%Y-%m-%d")
            except:
                calculated_end_date = end_date  # Fallback to original end_date if calculation fails
        
        return TripPlanningRequest(
            origin=origin,
            destination=destination,
            travelers=travelers,  # Don't default to 1, let it be None if not provided
            start_date=start_date,
            end_date=calculated_end_date or end_date,
            duration_days=duration_days,  # Can be None, will be handled by model
            budget_range=budget_range,  # Don't default, let it be None if not provided
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
    # Use word boundaries to avoid capturing "for" as part of destination
    from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for\s+\d+|\s+with|\s+in|\s+on|$)"
    match = re.search(from_to_pattern, message.lower())
    if match:
        destination = match.group(2).strip()
        # Clean up destination - remove any trailing words that are not city names
        destination_words = destination.split()
        # Remove common non-city words from the end
        non_city_words = ['for', 'with', 'in', 'on', 'and', 'or']
        while destination_words and destination_words[-1].lower() in non_city_words:
            destination_words.pop()
        return ' '.join(destination_words).title()
    
    # Look for "go to X" pattern - improved to handle more cases
    go_to_patterns = [
        r"go\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)",
        r"want\s+to\s+go\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)",
        r"travel\s+to\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)",
        r"visit\s+([a-zA-Z\s]+?)(?:\s+for|\s+with|\s+in|\s+on|$)"
    ]
    
    for pattern in go_to_patterns:
        match = re.search(pattern, message.lower())
        if match:
            destination = match.group(1).strip()
            # Clean up destination - remove any trailing words that are not city names
            destination_words = destination.split()
            # Remove common non-city words from the end
            non_city_words = ['for', 'with', 'in', 'on', 'and', 'or']
            while destination_words and destination_words[-1].lower() in non_city_words:
                destination_words.pop()
            return ' '.join(destination_words).title()
    
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
    # Convert word numbers to digits for easier processing
    word_to_number = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    # Replace word numbers with digits
    message_processed = message.lower()
    for word, number in word_to_number.items():
        message_processed = message_processed.replace(word, str(number))
    
    # Look for numbers followed by traveler keywords
    traveler_patterns = [
        r"(\d+)\s+(people|travelers|guests|adults)",
        r"(\d+)\s+(person|traveler|guest|adult)",
        r"(solo|alone|myself)",
        r"(couple|romantic|boyfriend|girlfriend)",
        r"(family|kids|children)"
    ]
    
    for pattern in traveler_patterns:
        match = re.search(pattern, message_processed)
        if match:
            if pattern == r"(solo|alone|myself)":
                return 1
            elif pattern == r"(couple|romantic|boyfriend|girlfriend)":
                return 2
            elif pattern == r"(family|kids|children)":
                # Extract family size if mentioned, otherwise default to 4 for family
                family_size_match = re.search(r"(\d+)\s+(people|travelers|guests|adults)", message_processed)
                if family_size_match:
                    return int(family_size_match.group(1))
                return 4  # Default family size
            else:
                return int(match.group(1))
    
    return None

def _extract_start_date(message: str) -> Optional[str]:
    """Extract start date from message"""
    # Look for date patterns - only match actual month names
    month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                  'july', 'august', 'september', 'october', 'november', 'december']
    month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    date_patterns = [
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # MM/DD/YYYY
    ]
    
    # Add patterns for each month name
    for month in month_names + month_abbr:
        date_patterns.append(rf"({month})\s+(\d{{1,2}})(?:st|nd|rd|th)?")  # Month Day
        date_patterns.append(rf"(\d{{1,2}})\s+({month})(?:st|nd|rd|th)?")  # Day Month
    
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
        "budget": ["budget", "cheap", "affordable", "low cost", "economy", "thrifty", "backpacker"],
        "moderate": ["moderate", "reasonable", "standard", "mid-range", "comfortable", "balanced"],
        "luxury": ["luxury", "premium", "high end", "expensive", "upscale", "deluxe", "premium"]
    }
    
    message_lower = message.lower()
    for budget_range, keywords in budget_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            return budget_range
    
    # Also check for dollar amounts and price ranges
    dollar_patterns = [
        r"\$(\d+)(?:-\d+)?\s*(?:per\s+day|daily|budget)",
        r"(\d+)(?:-\d+)?\s*dollars?\s*(?:per\s+day|daily|budget)",
        r"budget\s*of\s*\$?(\d+)",
        r"spend\s*\$?(\d+)",
        r"luxury\s*\(\$(\d+)\+/day\)",  # "Luxury ($300+/day)"
        r"moderate\s*\(\$(\d+)-(\d+)/day\)",  # "Moderate ($100-300/day)"
        r"budget-friendly\s*\(\$(\d+)-(\d+)/day\)"  # "Budget-friendly ($50-100/day)"
    ]
    
    for pattern in dollar_patterns:
        match = re.search(pattern, message_lower)
        if match:
            if "luxury" in pattern:
                return "luxury"
            elif "moderate" in pattern:
                return "moderate"
            elif "budget-friendly" in pattern:
                return "budget"
            else:
                # Check amount ranges
                amounts = [int(match.group(i)) for i in range(1, len(match.groups()) + 1)]
                avg_amount = sum(amounts) / len(amounts)
                if avg_amount < 100:
                    return "budget"
                elif avg_amount < 300:
                    return "moderate"
                else:
                    return "luxury"
    
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
        trip_request.travelers and
        trip_request.duration_days and
        trip_request.start_date and
        trip_request.budget_range
        # interests is optional
    )

def _get_missing_info(trip_request: TripPlanningRequest) -> List[str]:
    """Get list of missing mandatory information"""
    missing = []
    
    if not trip_request.origin:
        missing.append("origin")
    if not trip_request.destination:
        missing.append("destination")
    if not trip_request.travelers:
        missing.append("number of travelers")
    if not trip_request.duration_days:
        missing.append("duration_days")
    if not trip_request.start_date:
        missing.append("start date")
    if not trip_request.budget_range:
        missing.append("budget preference")
    
    # Note: end_date is calculated from start_date + duration_days
    # interests is optional
    
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
    if not trip_request.duration_days:
        suggestions.append("How many days would you like to travel?")
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