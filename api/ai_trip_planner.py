import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from api.models import (
    TripPlanningRequest, 
    ConversationState, 
    FollowUpQuestion, 
    ItineraryResponse,
    RefinementRequest
)
from api.ai_agents import ai_agent, AgentType, AgentTask

logger = logging.getLogger(__name__)

class AITripPlanner:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_sessions: Dict[str, ConversationState] = {}
        
    def create_session(self, session_id: str) -> ConversationState:
        """Create a new conversation session"""
        session = ConversationState(session_id=session_id)
        self.conversation_sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationState]:
        """Get existing conversation session"""
        return self.conversation_sessions.get(session_id)
    
    def determine_follow_up_questions(self, request: TripPlanningRequest, session: Optional[ConversationState] = None) -> List[FollowUpQuestion]:
        """Determine what follow-up questions to ask based on initial request and what's already been provided"""
        questions = []
        provided_fields = session.provided_fields if session else []
        
        # Only ask for start_date if it's truly missing and not already provided
        if (not request.start_date or request.start_date == "") and "start_date" not in provided_fields:
            questions.append(FollowUpQuestion(
                question="What's your preferred start date for the trip? (YYYY-MM-DD format)",
                field_name="start_date",
                field_type="date",
                required=True
            ))
        
        # Only ask for travelers if it's the default value and not already provided
        if request.travelers == 1 and "travelers" not in provided_fields:
            questions.append(FollowUpQuestion(
                question="How many travelers will be going on this trip?",
                field_name="travelers",
                field_type="number",
                required=True
            ))
        
        # Only ask for interests if it's empty and not already provided
        if (not request.interests or len(request.interests) == 0) and "interests" not in provided_fields:
            questions.append(FollowUpQuestion(
                question="What are your main interests for this trip? (e.g., food, art, history, nature, shopping)",
                field_name="interests",
                field_type="text",
                required=False
            ))
        
        # Only ask for budget if it's the default "moderate" value and not already provided
        if request.budget_range.value == "moderate" and "budget_range" not in provided_fields:
            questions.append(FollowUpQuestion(
                question="What's your budget preference for this trip?",
                field_name="budget_range",
                field_type="choice",
                choices=["budget", "moderate", "luxury"],
                required=True
            ))
        
        return questions
    
    async def generate_itinerary(self, request: TripPlanningRequest) -> Dict[str, Any]:
        """Generate itinerary using the multi-agent system"""
        try:
            # Use the multi-agent system instead of single Claude call
            itinerary = await ai_agent.plan_trip_with_agents(request)
            
            if "error" in itinerary:
                logger.error(f"Multi-agent planning error: {itinerary['error']}")
                return itinerary
            
            # Add agent insights to the response
            itinerary["agent_system"] = {
                "description": "This itinerary was created by a team of specialized AI agents:",
                "agents_used": [
                    "Coordinator Agent - Overall trip structure and coordination",
                    "Destination Specialist - Local attractions and hidden gems",
                    "Budget Analyst - Cost optimization and budget breakdown",
                    "Logistics Planner - Transportation and route optimization",
                    "Cultural Advisor - Local customs and cultural insights",
                    "Booking Agent - Booking strategies and recommendations"
                ],
                "confidence_scores": itinerary.get("agent_insights", {})
            }
            
            return itinerary
                
        except Exception as e:
            logger.error(f"Error generating itinerary with agents: {e}")
            return {"error": str(e)}
    
    async def refine_itinerary_with_agents(self, session_id: str, refinement: RefinementRequest) -> Dict[str, Any]:
        """Refine itinerary using specialized agents based on the type of change"""
        try:
            session = self.get_session(session_id)
            if not session:
                return {"error": "Session not found"}
            
            if session.refinement_count >= session.max_refinements:
                return {"error": "Maximum refinements reached"}
            
            # Analyze the refinement request to determine which agents to involve
            refinement_analysis = await self._analyze_refinement_request(refinement.changes)
            
            # Create tasks for relevant agents
            agent_tasks = []
            
            # Always involve coordinator for major changes
            if refinement_analysis.get("requires_coordination", False):
                agent_tasks.append(AgentTask(
                    agent_type=AgentType.COORDINATOR,
                    task_description=f"Refine trip coordination based on: {refinement.changes}",
                    required_data={
                        "original_request": session.trip_request.dict(),
                        "current_itinerary": session.itinerary,
                        "requested_changes": refinement.changes,
                        "reason": refinement.reason
                    }
                ))
            
            # Involve budget analyst for budget-related changes
            if refinement_analysis.get("affects_budget", False):
                agent_tasks.append(AgentTask(
                    agent_type=AgentType.BUDGET_ANALYST,
                    task_description=f"Recalculate budget based on changes: {refinement.changes}",
                    required_data={
                        "original_request": session.trip_request.dict(),
                        "current_budget": session.itinerary.get("budget_breakdown", {}),
                        "requested_changes": refinement.changes
                    }
                ))
            
            # Involve logistics planner for route/destination changes
            if refinement_analysis.get("affects_logistics", False):
                agent_tasks.append(AgentTask(
                    agent_type=AgentType.LOGISTICS_PLANNER,
                    task_description=f"Update logistics plan based on: {refinement.changes}",
                    required_data={
                        "current_transportation": session.itinerary.get("transportation_plan", []),
                        "requested_changes": refinement.changes,
                        "duration_days": session.trip_request.duration_days
                    }
                ))
            
            # Execute agent tasks
            agent_results = []
            for task in agent_tasks:
                result = await ai_agent.execute_agent_task(task)
                agent_results.append(result)
            
            # Update session
            session.refinement_count += 1
            session.updated_at = datetime.now()
            
            # Add to conversation history
            session.conversation_history.append({
                "type": "refinement",
                "changes": refinement.changes,
                "reason": refinement.reason,
                "agent_results": [r.agent_type.value for r in agent_results],
                "timestamp": datetime.now().isoformat()
            })
            
            # Combine agent results into refined itinerary
            refined_itinerary = self._combine_refinement_results(session.itinerary, agent_results)
            session.itinerary = refined_itinerary
            
            return {
                "message": f"Refinement processed by {len(agent_results)} specialized agents",
                "refinement_count": session.refinement_count,
                "remaining_refinements": session.max_refinements - session.refinement_count,
                "agents_involved": [r.agent_type.value for r in agent_results],
                "refined_itinerary": refined_itinerary
            }
            
        except Exception as e:
            logger.error(f"Error refining itinerary with agents: {e}")
            return {"error": str(e)}
    
    async def _analyze_refinement_request(self, changes: Dict[str, Any]) -> Dict[str, bool]:
        """Analyze refinement request to determine which agents should be involved"""
        analysis = {
            "requires_coordination": False,
            "affects_budget": False,
            "affects_logistics": False,
            "affects_destination": False
        }
        
        # Simple keyword-based analysis
        changes_text = str(changes).lower()
        
        if any(word in changes_text for word in ["budget", "cost", "price", "luxury", "budget"]):
            analysis["affects_budget"] = True
            analysis["requires_coordination"] = True
        
        if any(word in changes_text for word in ["city", "destination", "route", "add", "remove", "change"]):
            analysis["affects_logistics"] = True
            analysis["requires_coordination"] = True
            analysis["affects_destination"] = True
        
        if any(word in changes_text for word in ["days", "nights", "duration", "extend", "shorten"]):
            analysis["requires_coordination"] = True
            analysis["affects_budget"] = True
            analysis["affects_logistics"] = True
        
        return analysis
    
    def _combine_refinement_results(self, original_itinerary: Dict[str, Any], agent_results: List) -> Dict[str, Any]:
        """Combine refinement results from agents into updated itinerary"""
        refined = original_itinerary.copy()
        
        for result in agent_results:
            if result.agent_type == AgentType.COORDINATOR:
                # Update overall structure
                if "recommended_cities" in result.result:
                    refined["overview"]["recommended_cities"] = result.result["recommended_cities"]
                if "route_sequence" in result.result:
                    refined["overview"]["route_sequence"] = result.result["route_sequence"]
            
            elif result.agent_type == AgentType.BUDGET_ANALYST:
                # Update budget information
                if "budget_breakdown" in result.result:
                    refined["budget_breakdown"] = result.result["budget_breakdown"]
                if "cost_saving_tips" in result.result:
                    refined["cost_saving_tips"] = result.result["cost_saving_tips"]
            
            elif result.agent_type == AgentType.LOGISTICS_PLANNER:
                # Update transportation plan
                if "transportation_plan" in result.result:
                    refined["transportation_plan"] = result.result["transportation_plan"]
                if "travel_tips" in result.result:
                    refined["travel_tips"] = result.result["travel_tips"]
        
        # Add refinement metadata
        refined["refinement_metadata"] = {
            "last_refined": datetime.now().isoformat(),
            "agents_involved": [r.agent_type.value for r in agent_results],
            "confidence_scores": {r.agent_type.value: r.confidence for r in agent_results}
        }
        
        return refined
    
    def process_refinement(self, session_id: str, refinement: RefinementRequest) -> Dict[str, Any]:
        """Process refinement request and update itinerary"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        if session.refinement_count >= session.max_refinements:
            return {"error": "Maximum refinements reached"}
        
        # Update session
        session.refinement_count += 1
        session.updated_at = datetime.now()
        
        # Add to conversation history
        session.conversation_history.append({
            "type": "refinement",
            "changes": refinement.changes,
            "reason": refinement.reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # Here you would typically regenerate the itinerary with the new requirements
        # For now, return a placeholder
        return {
            "message": "Refinement processed",
            "refinement_count": session.refinement_count,
            "remaining_refinements": session.max_refinements - session.refinement_count
        }
    
    def get_conversation_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of the conversation session"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "current_step": session.current_step,
            "refinement_count": session.refinement_count,
            "max_refinements": session.max_refinements,
            "can_refine": session.refinement_count < session.max_refinements,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "trip_request": session.trip_request.dict() if session.trip_request else None,
            "has_itinerary": session.itinerary is not None,
            "agent_system_used": session.itinerary.get("agent_system", {}) if session.itinerary else None
        }

# Global instance
ai_planner = AITripPlanner() 