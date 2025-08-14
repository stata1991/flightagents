import json
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from services.contextual_followup_service import contextual_followup_service

logger = logging.getLogger(__name__)

class ConversationService:
    """
    Service to handle enhanced conversational experiences for trip planning.
    Creates our own unique travel planning conversation flow.
    """
    
    def __init__(self):
        self.conversation_states = {
            'greeting': 'initial_greeting',
            'destination': 'gathering_destination',
            'travelers': 'gathering_travelers', 
            'dates': 'gathering_dates',
            'vibe': 'gathering_vibe',
            'summary': 'trip_summary',
            'planning': 'creating_plan',
            'modification': 'modifying_plan'
        }
        
        # Dynamic destination context generation - no hardcoding
        self.destination_categories = {
            'beach': {
                'keywords': ['beach', 'coastal', 'island', 'ocean', 'sea', 'shore'],
                'description_template': "{destination} offers stunning beaches and coastal adventures",
                'highlights': ['beautiful beaches', 'water activities', 'coastal culture', 'ocean views'],
                'quick_replies': ['Beach relaxation', 'Water adventures', 'Coastal exploration', 'Island discovery'],
                'romantic_tips': "romantic beach dinners, sunset walks by the water, couples' beach activities"
            },
            'city': {
                'keywords': ['city', 'urban', 'metropolitan', 'downtown'],
                'description_template': "{destination} is a vibrant city with endless urban adventures",
                'highlights': ['urban culture', 'city attractions', 'local cuisine', 'city life'],
                'quick_replies': ['Urban exploration', 'Cultural discovery', 'City adventures', 'Local experiences'],
                'romantic_tips': "romantic city dinners, sunset city views, couples' urban exploration"
            },
            'mountain': {
                'keywords': ['mountain', 'alpine', 'hiking', 'trekking', 'peak'],
                'description_template': "{destination} offers breathtaking mountain adventures",
                'highlights': ['mountain views', 'outdoor activities', 'nature trails', 'alpine culture'],
                'quick_replies': ['Mountain adventures', 'Hiking exploration', 'Nature discovery', 'Outdoor activities'],
                'romantic_tips': "romantic mountain dinners, sunset peak views, couples' hiking adventures"
            },
            'cultural': {
                'keywords': ['temple', 'museum', 'historic', 'ancient', 'heritage'],
                'description_template': "{destination} is rich in culture and heritage",
                'highlights': ['cultural sites', 'historic landmarks', 'local traditions', 'heritage'],
                'quick_replies': ['Cultural exploration', 'Heritage discovery', 'Traditional experiences', 'Historic sites'],
                'romantic_tips': "romantic cultural experiences, sunset at historic sites, couples' cultural immersion"
            }
        }
    
    def get_greeting_message(self, user_name: str = None) -> Dict[str, Any]:
        """Generate the initial greeting message with personality."""
        name = user_name or "adventurer"
        
        return {
            'message': f"Welcome, {name}! 🌟 I'm your personal travel expert, ready to turn your dreams into incredible journeys! \n\nI can discover hidden gems, find the perfect timing, and craft experiences that will create memories for a lifetime. Where shall we start your next adventure? 🗺️",
            'quick_replies': ['Plan my dream trip', 'Discover destinations', 'Show me adventures'],
            'state': 'greeting'
        }
    
    def get_structured_questions(self) -> Dict[str, Any]:
        """Generate the 4 key structured questions for trip planning."""
        return {
            'message': """Perfect! Let's craft your dream adventure! 🚀 First, I need to understand your vision to create something truly magical:

1. **Where's calling your name?** 🌍 Got a destination in mind or shall I reveal some hidden gems?
2. **Who's joining your adventure?** 👥 Solo explorer, romantic duo, family expedition, or friend squad?
3. **When's your adventure time?** 📅 Dates and how long you want to immerse yourself?
4. **What's your adventure style?** 🎯 Relaxation, thrill-seeking, cultural immersion, or pure exploration?

Share your dreams with me! ✨""",
            'quick_replies': ['Beach paradise', 'Urban exploration', 'Mountain adventure', 'Cultural journey'],
            'state': 'destination'
        }
    
    def get_destination_response(self, destination: str, user_input: str) -> Dict[str, Any]:
        """Generate contextual response based on destination using dynamic categorization."""
        destination_lower = destination.lower()
        
        # Dynamically categorize destination based on keywords
        context = self._categorize_destination(destination)
        
        response = f"Incredible choice! 🌟 {context['description']}. I can already see you experiencing all the magical moments this destination has to offer!\n\nNow, let's craft your perfect adventure:\n• **Who's joining your journey?** Solo explorer, romantic duo, family expedition, or friend squad?\n• **When's your adventure time?** Dates and how long you want to immerse yourself?\n• **What's your adventure style?** {', '.join(context['quick_replies'])} or pure discovery?\n\nShare your vision with me! ✨"
        
        return {
            'message': response,
            'quick_replies': ['Romantic duo', 'Family expedition', 'Solo explorer', 'Friend squad'],
            'state': 'travelers',
            'destination': destination,
            'context': context
        }
    
    def get_travelers_response(self, travelers: str, destination: str = None) -> Dict[str, Any]:
        """Generate response based on traveler type."""
        traveler_responses = {
            'couple': {
                'message': f"Magical! 💕 A romantic adventure to {destination or 'your destination'} sounds absolutely enchanting. I'm dreaming of {self._get_romantic_tips(destination)} that will create memories forever.\n\nWhen are you planning this romantic journey?",
                'quick_replies': ['August 25th', 'September', 'October', 'Flexible dates'],
                'trip_type': 'romantic'
            },
            'family': {
                'message': f"Wonderful! 👨‍👩‍👧‍👦 Family expeditions are truly special. I'll craft experiences that everyone will treasure - from little explorers to wise grandparents.\n\nWhen's the perfect time for your family adventure?",
                'quick_replies': ['Summer break', 'Spring break', 'Holiday season', 'Any time'],
                'trip_type': 'family'
            },
            'solo': {
                'message': f"Adventurous! 🧳 Solo exploration is incredibly rewarding. I'll focus on experiences perfect for independent discovery and meaningful connections.\n\nWhen are you ready to embark on this solo journey?",
                'quick_replies': ['Next month', 'In 3 months', 'Flexible', 'Show me adventures'],
                'trip_type': 'solo'
            },
            'friends': {
                'message': f"Epic! 👥 Group adventures with friends create the best memories. I'll plan activities perfect for shared experiences and group excitement.\n\nWhen's your squad getting together for this adventure?",
                'quick_replies': ['Next weekend', 'Next month', 'Summer', 'Flexible'],
                'trip_type': 'group'
            }
        }
        
        response = traveler_responses.get(travelers.lower(), traveler_responses['couple'])
        
        return {
            'message': response['message'],
            'quick_replies': response['quick_replies'],
            'state': 'dates',
            'travelers': travelers,
            'trip_type': response['trip_type']
        }
    
    def get_dates_response(self, dates: str, trip_data: Dict) -> Dict[str, Any]:
        """Generate response based on travel dates."""
        return {
            'message': f"Perfect timing! 📅 {dates} sounds like an ideal time to explore {trip_data.get('destination', 'your destination')}.\n\nNow for the exciting part - what's your adventure style? Are you seeking relaxation, thrill-seeking, cultural immersion, or a perfect blend of everything?",
            'quick_replies': ['Relaxation', 'Thrill-seeking', 'Cultural immersion', 'Perfect blend'],
            'state': 'vibe',
            'dates': dates
        }
    
    def get_vibe_response(self, vibe: str, trip_data: Dict) -> Dict[str, Any]:
        """Generate response based on travel vibe and create trip summary."""
        vibe_responses = {
            'relaxation': 'soul-soothing and peaceful',
            'adventure': 'thrilling and adventurous', 
            'culture': 'culturally enriching and educational',
            'party': 'energetic and exciting',
            'mix': 'perfectly balanced and diverse'
        }
        
        vibe_desc = vibe_responses.get(vibe.lower(), 'amazing')
        
        # Create trip summary
        summary = f"""Perfect! So here's your {vibe_desc} adventure:

• **From**: Your starting point
• **To**: {trip_data.get('destination', 'Your chosen destination')}
• **When**: {trip_data.get('dates', 'Your selected dates')}
• **Who**: {trip_data.get('travelers', 'Your travel companions')}
• **Purpose**: {vibe_desc} experience

Before I craft your complete itinerary, any specific preferences or must-see places? 🎯"""
        
        return {
            'message': summary,
            'quick_replies': ['Start crafting!', 'Add more details', 'Show me adventures'],
            'state': 'summary',
            'vibe': vibe,
            'trip_summary': trip_data
        }
    
    def get_trip_summary_card(self, trip_data: Dict) -> Dict[str, Any]:
        """Generate a beautiful trip summary card."""
        return {
            'type': 'trip_card',
            'title': f"{trip_data.get('trip_type', 'Amazing')} Trip to {trip_data.get('destination', 'Your Destination')}",
            'image': self._get_destination_image(trip_data.get('destination')),
            'details': {
                'destination': trip_data.get('destination'),
                'dates': trip_data.get('dates'),
                'travelers': trip_data.get('travelers'),
                'vibe': trip_data.get('vibe'),
                'trip_type': trip_data.get('trip_type')
            },
            'actions': ['View Details', 'Modify Trip', 'Start Planning']
        }
    
    def get_modification_options(self) -> Dict[str, Any]:
        """Generate modification options after trip creation."""
        return {
            'message': "Now that we have your adventure crafted, how about we refine and reserve it? I can help you customize your journey, update your preferences and add or remove experiences. Remember, your entire adventure will be booked hassle-free! You don't have to do anything.",
            'quick_replies': ['Refine adventure', 'Make it more affordable', 'Find me flights', 'Book now'],
            'state': 'modification'
        }
    
    def _categorize_destination(self, destination: str) -> Dict[str, Any]:
        """Dynamically categorize destination based on keywords and generate context."""
        destination_lower = destination.lower()
        
        # Find matching category based on keywords
        matched_category = None
        for category, config in self.destination_categories.items():
            if any(keyword in destination_lower for keyword in config['keywords']):
                matched_category = category
                break
        
        # If no specific category found, use a general category
        if not matched_category:
            matched_category = 'general'
            general_config = {
                'description_template': "{destination} offers incredible adventures and unique experiences",
                'highlights': ['local culture', 'unique experiences', 'adventure', 'discovery'],
                'quick_replies': ['Local exploration', 'Adventure discovery', 'Cultural immersion', 'Unique experiences'],
                'romantic_tips': "romantic local experiences, sunset views, couples' adventures"
            }
        else:
            general_config = self.destination_categories[matched_category]
        
        # Generate dynamic description
        description = general_config['description_template'].format(destination=destination)
        
        return {
            'description': description,
            'highlights': general_config['highlights'],
            'quick_replies': general_config['quick_replies'],
            'romantic_tips': general_config['romantic_tips'],
            'category': matched_category
        }
    
    def _get_romantic_tips(self, destination: str) -> str:
        """Get romantic tips for a destination using dynamic categorization."""
        if not destination:
            return "romantic dinners, sunset walks, and unforgettable moments"
        
        context = self._categorize_destination(destination)
        return context['romantic_tips']
    
    def _get_destination_image(self, destination: str) -> str:
        """Get destination image URL (placeholder for now)."""
        # In a real implementation, this would fetch from an image service
        return f"/static/images/destinations/{destination.lower().replace(' ', '-')}.jpg"
    
    async def process_user_input(self, user_input: str, current_state: str, trip_data: Dict = None, missing_info: List[str] = None) -> Dict[str, Any]:
        """Process user input and return appropriate response."""
        trip_data = trip_data or {}
        missing_info = missing_info or []
        
        # Extract information from user input and update trip_data
        self._update_trip_data_from_input(user_input, trip_data)
        
        # If we have missing info, ask specific follow-up questions
        if missing_info:
            return await self._get_follow_up_questions(missing_info, trip_data)
        elif current_state == 'greeting':
            if any(word in user_input.lower() for word in ['itinerary', 'plan', 'trip']):
                return self.get_structured_questions()
            else:
                return self.get_structured_questions()
        
        elif current_state == 'destination':
            # Extract destination from user input
            destination = self._extract_destination(user_input)
            trip_data['destination'] = destination
            return self.get_destination_response(destination, user_input)
        
        elif current_state == 'travelers':
            travelers = self._extract_travelers(user_input)
            trip_data['travelers'] = travelers
            return self.get_travelers_response(travelers, trip_data.get('destination'))
        
        elif current_state == 'dates':
            dates = self._extract_dates(user_input)
            trip_data['dates'] = dates
            return self.get_dates_response(dates, trip_data)
        
        elif current_state == 'vibe':
            vibe = self._extract_vibe(user_input)
            trip_data['vibe'] = vibe
            return self.get_vibe_response(vibe, trip_data)
        
        elif current_state == 'summary':
            return self.get_modification_options()
        
        elif current_state == 'gathering_info':
            # Handle gathering_info state - check if we have all required info
            required_fields = ['origin', 'destination', 'travelers', 'duration_days', 'start_date', 'budget_range']
            missing_fields = [field for field in required_fields if not trip_data.get(field)]
            
            # Log current state for debugging
            logger.info(f"Current trip_data: {trip_data}")
            logger.info(f"Missing fields: {missing_fields}")
            
            if not missing_fields:
                # We have all the information, ready to start planning
                return {
                    'message': "🎯 Perfect! I have all the information I need to start planning your trip. Let me craft your perfect itinerary with real flights and hotels...",
                    'quick_replies': ['Show me the plan', 'Modify details', 'Start over'],
                    'state': 'planning',
                    'missing_info': [],
                    'trip_data': trip_data
                }
            else:
                # Still missing some information, ask for the next missing field
                # But first, acknowledge any new information provided
                acknowledgment = self._acknowledge_new_information(user_input, trip_data)
                follow_up = await self._get_follow_up_questions(missing_fields, trip_data)
                
                if acknowledgment:
                    follow_up['message'] = acknowledgment + "\n\n" + follow_up['message']
                
                return follow_up
        
        elif current_state == 'planning':
            # We have all the information, ready to start planning
            return {
                'message': "🎯 Perfect! I have all the information I need to start planning your trip. Let me craft your perfect itinerary with real flights and hotels...",
                'quick_replies': ['Show me the plan', 'Modify details', 'Start over'],
                'state': 'planning',
                'missing_info': [],
                'trip_data': trip_data
            }
        
        else:
            return {
                'message': "I'm not sure what you mean. Could you tell me more about your travel plans?",
                'quick_replies': ['Start over', 'Help me plan', 'Show options'],
                'state': 'greeting'
            }
    
    async def _get_follow_up_questions(self, missing_info: List[str], trip_data: Dict) -> Dict[str, Any]:
        """Generate conversational follow-up questions based on missing information."""
        questions = []
        quick_replies = []
        
        # Check what's actually missing based on what's already in trip_data
        actual_missing = []
        
        # Mandatory fields only
        if 'origin' in missing_info and 'origin' not in trip_data:
            actual_missing.append('origin')
            questions.append("**Where are you traveling from**?")
            quick_replies.extend(['I have a destination in mind', 'Show me options'])
        
        if 'destination' in missing_info and 'destination' not in trip_data:
            actual_missing.append('destination')
            questions.append("**Where would you like to go**?")
            quick_replies.extend(['Beach paradise', 'Urban exploration', 'Mountain adventure', 'Cultural journey'])
        
        if 'number of travelers' in missing_info and 'travelers' not in trip_data:
            actual_missing.append('travelers')
            questions.append("**Who's joining** your adventure?")
            quick_replies.extend(['Solo explorer', 'Romantic duo', 'Family trip', 'Friend squad'])
        
        if 'duration_days' in missing_info and 'duration_days' not in trip_data:
            actual_missing.append('duration_days')
            questions.append("**How many days** would you like to travel?")
            quick_replies.extend(['3 days', '5 days', '1 week', '2 weeks'])
        
        if 'start date' in missing_info and 'start_date' not in trip_data:
            actual_missing.append('start_date')
            questions.append("**When** would you like to travel?")
            quick_replies.extend(['Next month', 'Summer vacation', 'Holiday season', 'Flexible dates'])
        
        if 'budget preference' in missing_info and 'budget_range' not in trip_data:
            actual_missing.append('budget_range')
            questions.append("**What's your budget preference** for this trip?")
            quick_replies.extend(['Budget-friendly ($50-100/day)', 'Moderate ($100-300/day)', 'Luxury ($300+/day)'])
        
        # Interests are optional, but if mentioned in missing_info, ask for them
        if 'interests' in missing_info and 'interests' not in trip_data:
            # Don't add to actual_missing since interests are optional
            questions.append("**What type of experiences** are you looking for?")
            quick_replies.extend(['Adventure & Nature', 'Culture & History', 'Food & Dining', 'Relaxation', 'Nightlife'])
        
        # If we have all the information, start planning
        if not actual_missing:
            return {
                'message': "🎯 Perfect! I have all the information I need to start planning your trip. Let me craft your perfect itinerary with real flights and hotels...",
                'quick_replies': ['Show me the plan', 'Modify details', 'Start over'],
                'state': 'planning',
                'missing_info': [],
                'trip_data': trip_data
            }
        
        # Generate contextual follow-up if available
        if contextual_followup_service.is_available():
            try:
                contextual_response = await contextual_followup_service.generate_contextual_followup(actual_missing, trip_data)
                return {
                    'message': contextual_response.get('question', ' '.join(questions)),
                    'quick_replies': contextual_response.get('quick_replies', quick_replies),
                    'state': 'gathering_info',
                    'missing_info': actual_missing,
                    'trip_data': trip_data
                }
            except Exception as e:
                logger.error(f"Contextual followup failed: {e}")
                # Fallback to rule-based questions
        
        # Fallback to rule-based questions
        if len(questions) == 1:
            message = f"Great! I can see you want to plan a trip. {questions[0]}"
        else:
            message = f"Perfect! I can see you want to plan a trip. Let me ask a few quick questions:\n\n" + "\n".join(questions)
        
        return {
            'message': message,
            'quick_replies': quick_replies[:6],  # Limit to 6 quick replies
            'state': 'gathering_info',
            'missing_info': actual_missing,
            'trip_data': trip_data
        }
    
    def _update_trip_data_from_input(self, user_input: str, trip_data: Dict) -> None:
        """Extract and update trip data from user input."""
        user_input_lower = user_input.lower()
        
        # Log the input for debugging
        logger.info(f"Processing user input: '{user_input}'")
        logger.info(f"Current trip_data before processing: {trip_data}")
        
        # Extract duration if mentioned
        duration_match = re.search(r'(\d+)\s+days?', user_input_lower)
        if duration_match:
            trip_data['duration_days'] = int(duration_match.group(1))
            logger.info(f"Extracted duration_days: {trip_data['duration_days']}")
        
        # Extract travelers if mentioned
        # Convert word numbers to digits for easier processing
        word_to_number = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Replace word numbers with digits
        user_input_processed = user_input_lower
        for word, number in word_to_number.items():
            user_input_processed = user_input_processed.replace(word, str(number))
        
        if any(word in user_input_lower for word in ['solo', 'alone', 'myself']):
            trip_data['travelers'] = 1
        elif any(word in user_input_lower for word in ['couple', 'romantic', 'boyfriend', 'girlfriend']):
            trip_data['travelers'] = 2
        elif any(word in user_input_lower for word in ['family', 'kids', 'children']):
            trip_data['travelers'] = 4
        elif any(word in user_input_lower for word in ['friends', 'group', 'squad']):
            # Extract number if mentioned, otherwise default to 4
            number_match = re.search(r'(\d+)\s+(?:of us|people|travelers)', user_input_processed)
            if number_match:
                trip_data['travelers'] = int(number_match.group(1))
            else:
                trip_data['travelers'] = 4
        else:
            # Look for number + people/travelers pattern
            number_match = re.search(r'(\d+)\s+(people|travelers|guests|adults)', user_input_processed)
            if number_match:
                trip_data['travelers'] = int(number_match.group(1))
        
        if 'travelers' in trip_data:
            logger.info(f"Extracted travelers: {trip_data['travelers']}")
        
        # Extract dates if mentioned - only match actual month names
        month_names = ['january', 'february', 'march', 'april', 'may', 'june', 
                      'july', 'august', 'september', 'october', 'november', 'december']
        month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                     'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        date_patterns = [
            r'from\s+(\w+\s+\d+)',  # "from August 28th"
            r'starting\s+(\w+\s+\d+)',  # "starting August 28th"
        ]
        
        # Add patterns for each month name
        for month in month_names + month_abbr:
            date_patterns.append(rf'({month}\s+\d+)(?:st|nd|rd|th)?')
        
        for pattern in date_patterns:
            date_match = re.search(pattern, user_input_lower)
            if date_match:
                date_str = date_match.group(1)
                # Use the same date parsing logic as the working endpoints
                try:
                    from datetime import datetime
                    import calendar
                    
                    # Remove ordinal suffixes (th, st, nd, rd)
                    date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)
                    
                    # Try to parse month names
                    month_names = {name.lower(): i for i, name in enumerate(calendar.month_name) if name}
                    month_abbr = {name.lower(): i for i, name in enumerate(calendar.month_abbr) if name}
                    
                    parts = date_str.split()
                    if len(parts) >= 2:
                        month_str = parts[0].lower()
                        day_str = parts[1]
                        
                        month = month_names.get(month_str) or month_abbr.get(month_str)
                        if month and day_str.isdigit():
                            day = int(day_str)
                            # Assume current year or next year
                            current_year = datetime.now().year
                            date_obj = datetime(current_year, month, day)
                            
                            # If the date has passed, use next year
                            if date_obj < datetime.now():
                                date_obj = datetime(current_year + 1, month, day)
                            
                            trip_data['start_date'] = date_obj.strftime('%Y-%m-%d')
                            logger.info(f"Extracted start_date: {trip_data['start_date']}")
                except (ValueError, TypeError):
                    # Fallback to original format if parsing fails
                    trip_data['start_date'] = date_str
                    logger.info(f"Extracted start_date (fallback): {trip_data['start_date']}")
                break
        
        # Extract budget if mentioned
        budget_keywords = {
            "budget": ["budget", "cheap", "affordable", "low cost", "economy", "thrifty"],
            "moderate": ["moderate", "reasonable", "standard", "mid-range", "comfortable"],
            "luxury": ["luxury", "premium", "high end", "expensive", "upscale", "deluxe"]
        }
        
        for budget_range, keywords in budget_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                trip_data['budget_range'] = budget_range
                logger.info(f"Extracted budget_range: {trip_data['budget_range']}")
                break
        
        # Also check for specific budget patterns like "Luxury ($300+/day)"
        # Since the $ and numbers might be processed, just check for the key words
        if "luxury" in user_input_lower and ("300" in user_input or "day" in user_input_lower):
            trip_data['budget_range'] = "luxury"
            logger.info(f"Extracted budget_range (luxury): {trip_data['budget_range']}")
        elif "moderate" in user_input_lower and ("100" in user_input or "300" in user_input or "day" in user_input_lower):
            trip_data['budget_range'] = "moderate"
            logger.info(f"Extracted budget_range (moderate): {trip_data['budget_range']}")
        elif "budget-friendly" in user_input_lower or ("budget" in user_input_lower and "50" in user_input):
            trip_data['budget_range'] = "budget"
            logger.info(f"Extracted budget_range (budget): {trip_data['budget_range']}")
        
        # Extract interests if mentioned
        interest_keywords = {
            "beach": ["beach", "ocean", "sea", "coastal"],
            "culture": ["culture", "museum", "history", "art", "heritage"],
            "adventure": ["adventure", "hiking", "outdoor", "nature"],
            "nightlife": ["nightlife", "party", "club", "bar", "night life"],
            "shopping": ["shopping", "market", "mall", "retail"],
            "food": ["food", "cuisine", "restaurant", "dining", "gastronomy"],
            "relaxation": ["relax", "spa", "wellness", "peaceful"],
            "romance": ["romantic", "couple", "honeymoon", "romance"]
        }
        
        interests = []
        for interest, keywords in interest_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                interests.append(interest)
        
        if interests:
            # Merge with existing interests to avoid duplicates
            existing_interests = trip_data.get('interests', [])
            all_interests = existing_interests + [interest for interest in interests if interest not in existing_interests]
            trip_data['interests'] = all_interests
            logger.info(f"Extracted interests: {trip_data['interests']}")
        
        # Extract origin and destination if mentioned
        origin_dest_patterns = [
            r'from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for\s+\d+|\s+with|\s+in|\s+on|$)',  # "from dallas to los angeles"
            r'plan.*?from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for\s+\d+|\s+with|\s+in|\s+on|$)',  # "plan a trip from dallas to los angeles"
            r'trip.*?from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for\s+\d+|\s+with|\s+in|\s+on|$)',  # "trip from dallas to los angeles"
        ]
        
        for pattern in origin_dest_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                origin = match.group(1).strip().title()
                destination = match.group(2).strip().title()
                
                # Clean up destination - remove any trailing words that are not city names
                destination_words = destination.split()
                non_city_words = ['for', 'with', 'in', 'on', 'and', 'or']
                while destination_words and destination_words[-1].lower() in non_city_words:
                    destination_words.pop()
                destination = ' '.join(destination_words)
                
                trip_data['origin'] = origin
                trip_data['destination'] = destination
                logger.info(f"Extracted origin: {origin}, destination: {destination}")
                break
        
        # Log final trip_data for debugging
        logger.info(f"Final trip_data after processing: {trip_data}")
    
    def _acknowledge_new_information(self, user_input: str, trip_data: Dict) -> str:
        """Acknowledge new information provided by the user to avoid repetitive questions."""
        acknowledgments = []
        user_input_lower = user_input.lower()
        
        # 🚀 SMART TRIP LOGIC ACKNOWLEDGMENT
        smart_trip_data = trip_data.get("smart_trip_data", {})
        if smart_trip_data:
            trip_type = smart_trip_data.get("trip_type")
            if trip_type == "national_park":
                airport = smart_trip_data.get("recommended_airport", "nearest airport")
                transportation = smart_trip_data.get("transportation_options", [])
                min_days = smart_trip_data.get("minimum_days", 3)
                acknowledgments.append(f"🏔️ Smart planning! I've identified this as a national park trip and recommend flying into {airport}. You'll need a rental car to explore the park. I suggest at least {min_days} days for the full experience.")
            
            elif trip_type == "multi_city":
                cities = smart_trip_data.get("cities", [])
                if cities:
                    cities_str = ", ".join(cities)
                    min_days = smart_trip_data.get("minimum_days", 7)
                    acknowledgments.append(f"🌍 Excellent! I've detected a multi-city adventure. I'll plan a route through {cities_str} with high-speed train connections. This trip needs at least {min_days} days to fully experience each city.")
        
        # Check for interests
        if any(word in user_input_lower for word in ['nightlife', 'party', 'club', 'bar']):
            acknowledgments.append("✨ Great! I see you're interested in nightlife experiences.")
        
        if any(word in user_input_lower for word in ['beach', 'ocean', 'sea']):
            acknowledgments.append("🏖️ Perfect! Beach experiences are on your list.")
        
        if any(word in user_input_lower for word in ['culture', 'museum', 'history']):
            acknowledgments.append("🏛️ Excellent! Cultural experiences will be included.")
        
        if any(word in user_input_lower for word in ['food', 'cuisine', 'restaurant']):
            acknowledgments.append("🍽️ Wonderful! Culinary experiences are noted.")
        
        if any(word in user_input_lower for word in ['adventure', 'hiking', 'outdoor']):
            acknowledgments.append("🏔️ Fantastic! Adventure activities are planned.")
        
        # Check for other information
        if any(word in user_input_lower for word in ['romantic', 'couple']):
            acknowledgments.append("💕 Perfect! I'll make this a romantic getaway.")
        
        if any(word in user_input_lower for word in ['family', 'kids']):
            acknowledgments.append("👨‍👩‍👧‍👦 Great! Family-friendly activities will be included.")
        
        return " ".join(acknowledgments) if acknowledgments else ""
    
    def _extract_destination(self, text: str) -> str:
        """Extract destination from user input using dynamic analysis."""
        text_lower = text.lower()
        
        # Look for "from X to Y" pattern first (most specific)
        from_to_pattern = r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s+for\s+\d+|\s+with|\s+in|\s+on|$)"
        match = re.search(from_to_pattern, text_lower)
        if match:
            destination = match.group(2).strip()
            # Clean up destination - remove any trailing words that are not city names
            destination_words = destination.split()
            # Remove common non-city words from the end
            non_city_words = ['for', 'with', 'in', 'on', 'and', 'or']
            while destination_words and destination_words[-1].lower() in non_city_words:
                destination_words.pop()
            return ' '.join(destination_words).title()
        
        # Look for destination indicators
        destination_indicators = ['to', 'visit', 'go to', 'travel to', 'explore', 'see']
        
        # Find destination after indicators
        for indicator in destination_indicators:
            if indicator in text_lower:
                parts = text_lower.split(indicator)
                if len(parts) > 1:
                    potential_dest = parts[1].strip()
                    # Clean up the destination name - remove trailing non-city words
                    words = potential_dest.split()
                    # Remove common non-city words from the end
                    non_city_words = ['for', 'with', 'in', 'on', 'and', 'or']
                    while words and words[-1].lower() in non_city_words:
                        words.pop()
                    if words:
                        return ' '.join(word.capitalize() for word in words[:3])
        
        # If no clear indicator, look for capitalized words (likely place names)
        words = text.split()
        capitalized_words = [word for word in words if word[0].isupper() and len(word) > 2]
        if capitalized_words:
            return ' '.join(capitalized_words[:3])
        
        # Fallback: return first few meaningful words
        meaningful_words = [word for word in words if len(word) > 2 and word.lower() not in ['the', 'and', 'for', 'with']]
        return ' '.join(meaningful_words[:3]).title() if meaningful_words else "Your Dream Destination"
    
    def _extract_travelers(self, text: str) -> str:
        """Extract traveler type from user input."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['couple', 'romantic', 'boyfriend', 'girlfriend', 'husband', 'wife']):
            return 'couple'
        elif any(word in text_lower for word in ['family', 'kids', 'children', 'parents']):
            return 'family'
        elif any(word in text_lower for word in ['solo', 'alone', 'myself']):
            return 'solo'
        elif any(word in text_lower for word in ['friends', 'group', 'squad']):
            return 'friends'
        else:
            return 'couple'  # Default
    
    def _extract_dates(self, text: str) -> str:
        """Extract dates from user input using dynamic analysis."""
        text_lower = text.lower()
        
        # Month patterns
        months = {
            'january': 'January', 'february': 'February', 'march': 'March', 'april': 'April',
            'may': 'May', 'june': 'June', 'july': 'July', 'august': 'August',
            'september': 'September', 'october': 'October', 'november': 'November', 'december': 'December'
        }
        
        # Look for month mentions
        for month_lower, month_proper in months.items():
            if month_lower in text_lower:
                return month_proper
        
        # Look for time indicators
        time_indicators = {
            'next month': 'Next month',
            'next week': 'Next week',
            'this weekend': 'This weekend',
            'summer': 'Summer',
            'winter': 'Winter',
            'spring': 'Spring',
            'fall': 'Fall',
            'autumn': 'Autumn',
            'holiday': 'Holiday season',
            'christmas': 'Christmas',
            'new year': 'New Year'
        }
        
        for indicator, response in time_indicators.items():
            if indicator in text_lower:
                return response
        
        # Look for specific date patterns
        import re
        date_patterns = [
            r'(\d{1,2})/(\d{1,2})',  # MM/DD or DD/MM
            r'(\d{1,2})-(\d{1,2})',  # MM-DD or DD-MM
            r'(\d{1,2})\.(\d{1,2})',  # MM.DD or DD.MM
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return f"Date: {match.group(1)}/{match.group(2)}"
        
        return 'Flexible dates'
    
    def _extract_vibe(self, text: str) -> str:
        """Extract travel vibe from user input."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['relax', 'chill', 'beach']):
            return 'relaxation'
        elif any(word in text_lower for word in ['adventure', 'thrill', 'hike']):
            return 'adventure'
        elif any(word in text_lower for word in ['culture', 'museum', 'history']):
            return 'culture'
        elif any(word in text_lower for word in ['party', 'nightlife', 'fun']):
            return 'party'
        else:
            return 'mix' 