import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

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
    
    def process_user_input(self, user_input: str, current_state: str, trip_data: Dict = None) -> Dict[str, Any]:
        """Process user input and return appropriate response."""
        trip_data = trip_data or {}
        
        if current_state == 'greeting':
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
        
        else:
            return {
                'message': "I'm not sure what you mean. Could you tell me more about your travel plans?",
                'quick_replies': ['Start over', 'Help me plan', 'Show options'],
                'state': 'greeting'
            }
    
    def _extract_destination(self, text: str) -> str:
        """Extract destination from user input using dynamic analysis."""
        text_lower = text.lower()
        
        # Look for destination indicators
        destination_indicators = ['to', 'visit', 'go to', 'travel to', 'explore', 'see']
        
        # Find destination after indicators
        for indicator in destination_indicators:
            if indicator in text_lower:
                parts = text_lower.split(indicator)
                if len(parts) > 1:
                    potential_dest = parts[1].strip()
                    # Clean up the destination name
                    words = potential_dest.split()
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