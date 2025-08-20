import os
import json
import logging
from typing import Dict, Any, Optional, List
import anthropic
from datetime import datetime
import calendar
import re

logger = logging.getLogger(__name__)

class EnhancedEntityExtractor:
    """Enhanced entity extraction using Claude's function-calling capabilities"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self._available = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    def is_available(self) -> bool:
        return self._available
    
    async def extract_trip_entities(self, message: str, conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trip entities using Claude's function-calling"""
        if not self._available:
            return self._fallback_extraction(message, conversation_state)
        
        try:
            # Define the function schema for entity extraction
            functions = [
                {
                    "type": "function",
                    "function": {
                        "name": "extract_trip_entities",
                        "description": "Extract travel-related entities from user message",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "origin": {
                                    "type": "string",
                                    "description": "Origin city/airport (e.g., 'New York', 'JFK')"
                                },
                                "destination": {
                                    "type": "string", 
                                    "description": "Destination city/airport (e.g., 'London', 'LHR')"
                                },
                                "travelers": {
                                    "type": "integer",
                                    "description": "Number of travelers (1-10)"
                                },
                                "start_date": {
                                    "type": "string",
                                    "description": "Start date in YYYY-MM-DD format"
                                },
                                "duration_days": {
                                    "type": "integer",
                                    "description": "Trip duration in days (1-30)"
                                },
                                "budget_range": {
                                    "type": "string",
                                    "description": "Budget preference (budget, moderate, luxury)"
                                },
                                "trip_type": {
                                    "type": "string",
                                    "description": "Type of trip (leisure, business, family, solo, adventure, cultural, romantic)"
                                },
                                "interests": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "List of interests (beach, culture, adventure, etc.)"
                                }
                            },
                            "required": []
                        }
                    }
                }
            ]
            
            # Create context-aware prompt
            context = self._create_context_prompt(conversation_state)
            
            prompt = f"""You are a travel assistant extracting trip planning information from user messages.

{context}

Current user message: "{message}"

Extract any travel-related entities from this message. Only extract information that is explicitly mentioned or clearly implied. If a field is not mentioned, leave it as null.

Focus on:
- Origin and destination cities/airports
- Number of travelers (convert words like "two people" to numbers)
- Start dates (convert natural language to YYYY-MM-DD format)
- Trip duration in days
- Budget preferences
- Trip type and interests

Be precise and only extract what's actually mentioned."""

            # Call Claude with function-calling
            response = await self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
                tools=functions,
                tool_choice={"type": "function", "function": {"name": "extract_trip_entities"}}
            )
            
            # Parse the function call response
            if response.content and len(response.content) > 0:
                tool_use = response.content[0]
                if hasattr(tool_use, 'input') and tool_use.input:
                    extracted_data = json.loads(tool_use.input)
                    
                    # Post-process the extracted data
                    processed_data = self._post_process_extraction(extracted_data, conversation_state)
                    return processed_data
            
            return self._fallback_extraction(message, conversation_state)
            
        except Exception as e:
            logger.error(f"Enhanced entity extraction failed: {e}")
            return self._fallback_extraction(message, conversation_state)
    
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
    
    def _post_process_extraction(self, extracted_data: Dict[str, Any], conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process extracted data and merge with conversation state"""
        processed = {}
        
        # Merge with existing conversation state (don't overwrite existing data)
        for key, value in extracted_data.items():
            if value is not None and value != "":
                if key == "start_date" and value:
                    # Convert natural language dates to YYYY-MM-DD
                    processed_date = self._parse_natural_date(value)
                    if processed_date:
                        processed[key] = processed_date
                elif key == "travelers" and isinstance(value, str):
                    # Convert word numbers to integers
                    processed[key] = self._word_to_number(value)
                else:
                    processed[key] = value
        
        # Preserve existing conversation state
        for key, value in conversation_state.items():
            if key not in processed and value is not None:
                processed[key] = value
        
        return processed
    
    def _parse_natural_date(self, date_str: str) -> Optional[str]:
        """Parse natural language dates to YYYY-MM-DD format"""
        try:
            # Handle common date formats
            date_str = date_str.lower().strip()
            
            # Remove ordinal suffixes
            date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
            
            # Try to parse with dateparser first
            try:
                from dateparser import parse
                parsed_date = parse(date_str)
                if parsed_date:
                    return parsed_date.strftime("%Y-%m-%d")
            except:
                pass
            
            # Manual parsing for common patterns
            month_names = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
            month_abbr = {name.lower(): i for i, name in enumerate(calendar.month_abbr) if name}
            
            # Pattern: "August 28" or "28 August" or "28th August"
            patterns = [
                r'(\w+)\s+(\d+)',  # Month Day
                r'(\d+)\s+(\w+)',  # Day Month
                r'(\d+)(?:st|nd|rd|th)?\s+(\w+)',  # Day Month with ordinal
                r'(\w+)\s+(\d+)(?:st|nd|rd|th)?',  # Month Day with ordinal
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_str)
                if match:
                    if match.group(1).isdigit():
                        day = int(match.group(1))
                        month_str = match.group(2).lower()
                    else:
                        day = int(match.group(2))
                        month_str = match.group(1).lower()
                    
                    month = month_names.get(month_str) or month_abbr.get(month_str)
                    if month and 1 <= day <= 31:
                        current_year = datetime.now().year
                        date_obj = datetime(current_year, month, day)
                        
                        # If date has passed, use next year
                        if date_obj < datetime.now():
                            date_obj = datetime(current_year + 1, month, day)
                        
                        return date_obj.strftime("%Y-%m-%d")
            
            # Handle year-only or month-year patterns
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                year = int(year_match.group(1))
                # Extract month if present
                for month_name, month_num in month_names.items():
                    if month_name in date_str:
                        return f"{year}-{month_num:02d}-01"
            
            # Handle "28th August 2025" pattern specifically
            full_date_pattern = r'(\d+)(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})'
            full_match = re.search(full_date_pattern, date_str)
            if full_match:
                day = int(full_match.group(1))
                month_str = full_match.group(2).lower()
                year = int(full_match.group(3))
                
                month = month_names.get(month_str) or month_abbr.get(month_str)
                if month and 1 <= day <= 31:
                    return f"{year}-{month:02d}-{day:02d}"
            
            return None
        except Exception as e:
            logger.error(f"Date parsing error: {e}")
            return None
    
    def _word_to_number(self, text: str) -> Optional[int]:
        """Convert word numbers to integers"""
        word_to_number = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        text_lower = text.lower()
        
        # Check for word numbers
        for word, number in word_to_number.items():
            if word in text_lower:
                return number
        
        # Check for numeric patterns
        number_match = re.search(r'(\d+)', text)
        if number_match:
            return int(number_match.group(1))
        
        return None
    
    def _fallback_extraction(self, message: str, conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to regex-based extraction if Claude is unavailable"""
        # This would use the existing regex-based extraction methods
        # For now, return the conversation state as-is
        return conversation_state.copy()

# Global instance
enhanced_entity_extractor = EnhancedEntityExtractor() 