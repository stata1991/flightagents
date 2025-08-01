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
        
        # Destination-specific responses for contextual conversations
        self.destination_contexts = {
            'goa': {
                'description': "Goa is a paradise of golden beaches, vibrant culture, and endless adventures",
                'highlights': ['golden beaches', 'Portuguese churches', 'beachside music', 'hidden beach shacks', 'Arabian Sea'],
                'quick_replies': ['Beach relaxation', 'Cultural exploration', 'Nightlife excitement', 'Pure discovery'],
                'romantic_tips': "candlelit dinners by the Arabian Sea, sunset walks on pristine beaches, couples' spa experiences"
            },
            'bali': {
                'description': "Bali is a spiritual paradise with ancient temples, lush rice terraces, and pristine beaches",
                'highlights': ['ancient temples', 'rice terraces', 'pristine beaches', 'spiritual vibes', 'Ubud culture'],
                'quick_replies': ['Temple exploration', 'Beach paradise', 'Rice terrace adventures', 'Wellness retreat'],
                'romantic_tips': "romantic dinners overlooking emerald rice terraces, couples' traditional massages, sunset at Tanah Lot temple"
            },
            'paris': {
                'description': "Paris is the city of love, art, and culinary excellence",
                'highlights': ['romance', 'art', 'culinary excellence', 'Eiffel Tower', 'Louvre Museum'],
                'quick_replies': ['Romantic escape', 'Art exploration', 'Culinary journey', 'Fashion discovery'],
                'romantic_tips': "romantic dinners by the Seine River, sunset at Trocadéro, couples' wine tasting in hidden bistros"
            },
            'tokyo': {
                'description': "Tokyo is a mesmerizing blend of ancient traditions and futuristic innovation",
                'highlights': ['ancient traditions', 'futuristic innovation', 'culinary excellence', 'sacred temples', 'fashion districts'],
                'quick_replies': ['Culinary adventure', 'Tech exploration', 'Cultural immersion', 'Fashion discovery'],
                'romantic_tips': "romantic dinners in hidden izakayas, couples' traditional onsen experience, cherry blossom viewing in peaceful gardens"
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
        """Generate contextual response based on destination."""
        destination_lower = destination.lower()
        
        # Find matching destination context
        context = None
        for key, dest_context in self.destination_contexts.items():
            if key in destination_lower:
                context = dest_context
                break
        
        if not context:
            # Generic response for unknown destinations
            context = {
                'description': f"{destination} sounds amazing! I'd love to help you plan the perfect trip there.",
                'highlights': ['exploration', 'adventure', 'discovery'],
                'quick_replies': ['Tell me more', 'Show me options', 'Plan this trip'],
                'romantic_tips': "romantic experiences and memorable moments"
            }
        
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
    
    def _get_romantic_tips(self, destination: str) -> str:
        """Get romantic tips for a destination."""
        destination_lower = destination.lower() if destination else ''
        
        for key, context in self.destination_contexts.items():
            if key in destination_lower:
                return context['romantic_tips']
        
        return "romantic dinners, sunset walks, and unforgettable moments"
    
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
        """Extract destination from user input."""
        # Simple extraction - in real implementation, use NLP
        common_destinations = ['goa', 'bali', 'paris', 'tokyo', 'new york', 'london', 'barcelona']
        text_lower = text.lower()
        
        for dest in common_destinations:
            if dest in text_lower:
                return dest.title()
        
        # Return first few words as destination
        words = text.split()
        return ' '.join(words[:3]) if words else "Unknown Destination"
    
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
        """Extract dates from user input."""
        # Simple extraction - in real implementation, use date parsing
        if 'august' in text.lower():
            return 'August 25th'
        elif 'september' in text.lower():
            return 'September'
        elif 'october' in text.lower():
            return 'October'
        else:
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