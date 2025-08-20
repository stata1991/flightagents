import logging
from typing import Dict, Any, List, Optional
import anthropic
import os

logger = logging.getLogger(__name__)

class ContextualFollowupService:
    """Generate contextual follow-up questions based on conversation state"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._available = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    def is_available(self) -> bool:
        return self._available
    
    async def generate_contextual_followup(self, missing_info: List[str], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual follow-up questions based on what's already known"""
        if not self._available:
            return self._fallback_followup(missing_info, conversation_state)
        
        try:
            # Create context-aware prompt
            context = self._create_context_prompt(conversation_state)
            
            prompt = f"""You are a travel assistant helping users plan their trips. Generate natural, contextual follow-up questions based on what information is still needed.

{context}

Missing information: {', '.join(missing_info)}

IMPORTANT: Do NOT ask for information that has already been provided. If the user has already given dates, travelers, destination, etc., acknowledge what they've shared and ask for the NEXT missing piece.

Generate:
1. A natural follow-up question that asks for the most important missing information
2. 3-4 quick reply options that would help the user provide the missing information
3. A brief explanation of why this information is needed (optional)

Make the question feel conversational and contextual to what they've already shared. If they've mentioned specific details (like a destination), reference those in your question.

Examples:
- If they mentioned "Mumbai" and need travelers: "Great choice! Mumbai is amazing. How many people will be joining this adventure?"
- If they mentioned "3 days" and need dates: "Perfect! For your 3-day trip, when would you like to start your adventure?"
- If they've already provided dates, travelers, and destination: "Excellent! I have everything I need to start planning. Let me craft your perfect itinerary!"

Focus on the most critical missing information first. If all required information is provided, acknowledge completion and move to planning."""

            response = self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response.content and len(response.content) > 0:
                # Parse the response to extract question and quick replies
                content = response.content[0]
                try:
                    # Try to get text from the content
                    if hasattr(content, 'text'):
                        text = content.text
                    elif hasattr(content, 'content'):
                        text = str(content.content)
                    elif hasattr(content, 'type') and content.type == 'text':
                        text = content.text
                    else:
                        # Fallback - try to convert to string
                        text = str(content)
                    
                    parsed_response = self._parse_followup_response(text)
                    return parsed_response
                except Exception as e:
                    logger.error(f"Error parsing response content: {e}")
                    return self._fallback_followup(missing_info, conversation_state)
            
            return self._fallback_followup(missing_info, conversation_state)
            
        except Exception as e:
            logger.error(f"Contextual followup generation failed: {e}")
            return self._fallback_followup(missing_info, conversation_state)
    
    def _create_context_prompt(self, conversation_state: Dict[str, Any]) -> str:
        """Create context-aware prompt based on current conversation state"""
        context_parts = []
        
        if conversation_state.get("origin"):
            context_parts.append(f"Origin: {conversation_state['origin']}")
        if conversation_state.get("destination"):
            context_parts.append(f"Destination: {conversation_state['destination']}")
        if conversation_state.get("travelers"):
            context_parts.append(f"Travelers: {conversation_state['travelers']}")
        if conversation_state.get("duration_days"):
            context_parts.append(f"Duration: {conversation_state['duration_days']} days")
        if conversation_state.get("start_date"):
            context_parts.append(f"Start date: {conversation_state['start_date']}")
        
        if context_parts:
            return f"Already known information:\n" + "\n".join(f"- {part}" for part in context_parts)
        else:
            return "No previous information available."
    
    def _parse_followup_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI response to extract question and quick replies"""
        try:
            # Try to extract structured information from the response
            lines = response_text.strip().split('\n')
            
            question = ""
            quick_replies = []
            explanation = ""
            
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if "question:" in line.lower() or "follow-up:" in line.lower():
                    current_section = "question"
                    question = line.split(":", 1)[1].strip() if ":" in line else line
                elif "quick replies:" in line.lower() or "options:" in line.lower():
                    current_section = "quick_replies"
                elif "explanation:" in line.lower() or "why:" in line.lower():
                    current_section = "explanation"
                elif line.startswith("-") or line.startswith("•") or line.startswith("*"):
                    # Quick reply option
                    quick_reply = line.lstrip("-•* ").strip()
                    if quick_reply:
                        quick_replies.append(quick_reply)
                elif current_section == "question" and not question:
                    question = line
                elif current_section == "explanation":
                    explanation += line + " "
            
            # If no structured parsing worked, use the whole response as question
            if not question:
                question = response_text.strip()
            
            # Generate default quick replies if none were parsed
            if not quick_replies:
                quick_replies = self._generate_default_quick_replies()
            
            return {
                "question": question,
                "quick_replies": quick_replies[:4],  # Limit to 4 options
                "explanation": explanation.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse followup response: {e}")
            return {
                "question": response_text.strip(),
                "quick_replies": self._generate_default_quick_replies(),
                "explanation": ""
            }
    
    def _generate_default_quick_replies(self) -> List[str]:
        """Generate default quick reply options"""
        return [
            "I have a destination in mind",
            "Show me options",
            "Help me decide",
            "Tell me more"
        ]
    
    def _fallback_followup(self, missing_info: List[str], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to rule-based follow-up generation"""
        if not missing_info:
            return {
                "question": "Perfect! I have all the information I need to start planning your trip. Let me craft your perfect itinerary!",
                "quick_replies": ["Show me the plan", "Modify details", "Start over"],
                "explanation": ""
            }
        
        # Generate contextual questions based on what's missing
        primary_missing = missing_info[0]  # Focus on the most important missing info
        
        # Dynamic quick replies based on context
        def get_dynamic_quick_replies(field: str, context: Dict[str, Any]) -> List[str]:
            """Generate dynamic quick replies based on context"""
            if field in ["origin", "destination"]:
                return ["I have a destination in mind", "Show me options", "Help me decide", "Tell me more"]
            elif field in ["travelers", "number of travelers"]:
                return ["Solo explorer", "Romantic duo", "Family trip", "Friend squad"]
            elif field == "duration_days":
                return ["3 days", "5 days", "1 week", "2 weeks"]
            elif field in ["start date", "start_date"]:
                return ["Next month", "Summer vacation", "Holiday season", "Flexible dates"]
            elif field in ["budget preference", "budget_range"]:
                return ["Budget-friendly ($50-100/day)", "Moderate ($100-300/day)", "Luxury ($300+/day)"]
            else:
                return ["Tell me more", "Help me decide", "Show me options"]
        
        contextual_questions = {
            "origin": {
                "question": "Where are you traveling from?",
                "quick_replies": get_dynamic_quick_replies("origin", conversation_state)
            },
            "destination": {
                "question": "Where would you like to go?",
                "quick_replies": get_dynamic_quick_replies("destination", conversation_state)
            },
            "number of travelers": {
                "question": "Who's joining your adventure?",
                "quick_replies": get_dynamic_quick_replies("travelers", conversation_state)
            },
            "travelers": {
                "question": "Who's joining your adventure?",
                "quick_replies": get_dynamic_quick_replies("travelers", conversation_state)
            },
            "duration_days": {
                "question": "How many days would you like to travel?",
                "quick_replies": get_dynamic_quick_replies("duration_days", conversation_state)
            },
            "start date": {
                "question": "When would you like to travel?",
                "quick_replies": get_dynamic_quick_replies("start_date", conversation_state)
            },
            "start_date": {
                "question": "When would you like to travel?",
                "quick_replies": get_dynamic_quick_replies("start_date", conversation_state)
            },
            "budget preference": {
                "question": "What's your budget preference for this trip?",
                "quick_replies": ["Budget-friendly ($50-100/day)", "Moderate ($100-300/day)", "Luxury ($300+/day)"]
            }
        }
        
        # Add context to the question if we have destination info
        question = contextual_questions.get(primary_missing, {
            "question": f"Please provide {primary_missing}",
            "quick_replies": ["I have a destination in mind", "Show me options", "Help me decide"]
        })
        
        # Make it more contextual if we have destination info
        if conversation_state.get("destination") and primary_missing in ["number of travelers", "travelers"]:
            dest = conversation_state["destination"]
            question["question"] = f"Great choice! {dest} is amazing. How many people will be joining this adventure?"
        
        elif conversation_state.get("duration_days") and primary_missing in ["start date", "start_date"]:
            days = conversation_state["duration_days"]
            question["question"] = f"Perfect! For your {days}-day trip, when would you like to start your adventure?"
        
        return {
            "question": question["question"],
            "quick_replies": question["quick_replies"],
            "explanation": ""
        }

# Global instance
contextual_followup_service = ContextualFollowupService() 