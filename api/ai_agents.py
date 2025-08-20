import os
import json
import logging
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from services.flight_service import FlightService
from services.hotel_service import HotelService

logger = logging.getLogger(__name__)
load_dotenv()

class AgentType(Enum):
    DESTINATION_SPECIALIST = "destination_specialist"
    BUDGET_ANALYST = "budget_analyst"
    FLIGHT_SEARCH_AGENT = "flight_search_agent"
    HOTEL_SEARCH_AGENT = "hotel_search_agent"

class AgentTask:
    def __init__(self, agent_type: AgentType, required_data: Dict[str, Any]):
        self.agent_type = agent_type
        self.required_data = required_data

class AITripPlanningAgent:
    def __init__(self):
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.flight_service = FlightService()
        self.hotel_service = HotelService()

    async def plan_trip_with_agents(self, request: Any) -> Dict[str, Any]:
        """
        Plan trip using the multi-agent system with markdown instructions.
        """
        try:
            # Create tasks for each agent
            tasks = [
                AgentTask(AgentType.DESTINATION_SPECIALIST, {
                    "origin": request.origin,
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "duration_days": request.duration_days,
                    "travelers": request.travelers,
                    "budget_range": request.budget_range.value if hasattr(request.budget_range, 'value') else request.budget_range,
                    "interests": request.interests
                }),
                AgentTask(AgentType.BUDGET_ANALYST, {
                    "origin": request.origin,
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "duration_days": request.duration_days,
                    "travelers": request.travelers,
                    "budget_range": request.budget_range.value if hasattr(request.budget_range, 'value') else request.budget_range,
                    "interests": request.interests
                }),
                AgentTask(AgentType.FLIGHT_SEARCH_AGENT, {
                    "origin": request.origin,
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "return_date": request.end_date,  # Use end_date as return_date
                    "travelers": request.travelers
                }),
                AgentTask(AgentType.HOTEL_SEARCH_AGENT, {
                    "destination": request.destination,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "travelers": request.travelers,
                    "budget_range": request.budget_range.value if hasattr(request.budget_range, 'value') else request.budget_range
                })
            ]

            # Execute all agents
            results = {}
            for task in tasks:
                if task.agent_type in [AgentType.FLIGHT_SEARCH_AGENT, AgentType.HOTEL_SEARCH_AGENT]:
                    # Handle special API agents
                    result = await self._handle_special_api_agent(task)
                else:
                    # Handle markdown-based agents
                    result = await self._execute_markdown_agent(task)
                
                results[task.agent_type.value] = {
                    "result": result,
                    "confidence": 0.8,
                    "reasoning": ""
                }

            return {"agents": results}

        except Exception as e:
            logger.error(f"Error in plan_trip_with_agents: {e}")
            return {"error": str(e)}

    async def _execute_markdown_agent(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a markdown-based AI agent by reading its instruction file and sending to Claude.
        """
        try:
            # Search recursively for the agent file inside agents/ (supports product, engineering, growth, etc.)
            search_pattern = os.path.join("agents", "**", f"{task.agent_type.value}.md")
            agent_files = glob.glob(search_pattern, recursive=True)

            if not agent_files:
                logger.error(f"Agent file not found: {task.agent_type.value}.md in agents/")
                return {"error": f"Agent file agents/**/{task.agent_type.value}.md not found"}

            agent_file = agent_files[0]

            with open(agent_file, "r", encoding="utf-8") as f:
                instructions = f.read()

            prompt = f"""
You are the {task.agent_type.value.replace("_", " ").title()} agent.
Instructions:
{instructions}

Context:
{json.dumps(task.required_data, indent=2)}
"""

            response = await self._call_claude(prompt)
            return response

        except Exception as e:
            logger.error(f"Error executing markdown agent {task.agent_type.value}: {e}")
            return {"error": str(e)}


    async def _handle_special_api_agent(self, task: AgentTask) -> Dict[str, Any]:
        """Handles Flight and Hotel Search Agents using the service layer."""
        
        if task.agent_type == AgentType.FLIGHT_SEARCH_AGENT:
            return await FlightService.get_recommendations(
                origin=task.required_data.get("origin"),
                destination=task.required_data.get("destination"),
                start_date=task.required_data.get("start_date"),
                return_date=task.required_data.get("return_date"),
                travelers=task.required_data.get("travelers", 1)
            )
        
        if task.agent_type == AgentType.HOTEL_SEARCH_AGENT:
            return await HotelService.get_recommendations(
                destination=task.required_data.get("destination"),
                start_date=task.required_data.get("start_date"),
                end_date=task.required_data.get("end_date"),
                travelers=task.required_data.get("travelers", 1),
                budget_range=task.required_data.get("budget_range", "moderate")
            )
        
        return {"error": "Unknown special API agent"}

    async def execute_markdown_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a markdown-based AI agent by reading its instruction file and sending to Claude.
        """
        try:
            agent_file = os.path.join("agents", "product", f"{agent_name}.md")
            if not os.path.exists(agent_file):
                logger.error(f"Agent file not found: {agent_file}")
                return {"error": f"Agent file {agent_file} not found"}

            with open(agent_file, "r") as f:
                instructions = f.read()

            prompt = f"""
You are the {agent_name.replace("_", " ").title()} agent.
Instructions:
{instructions}

Context:
{json.dumps(context, indent=2)}
"""

            response = await self._call_claude(prompt)
            return response

        except Exception as e:
            logger.error(f"Error executing markdown agent {agent_name}: {e}")
            return {"error": str(e)}

    async def execute_special_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes non-markdown agents that integrate with APIs (flight & hotel).
        """
        try:
            if agent_name == "flight_search_agent":
                logger.info("Executing special API agent: flight_search_agent")
                result = await self.flight_service.search_flights(context)
                return {"result": result, "confidence": 0.8, "reasoning": ""}

            elif agent_name == "hotel_search_agent":
                logger.info("Executing special API agent: hotel_search_agent")
                result = await self.hotel_service.search_hotels(context)
                return {"result": result, "confidence": 0.8, "reasoning": ""}

            else:
                return {"error": f"Unknown special agent {agent_name}"}

        except Exception as e:
            logger.error(f"Error executing special agent {agent_name}: {e}")
            return {"error": str(e)}

    async def plan_trip_with_markdown_agents(self, request: Any) -> Dict[str, Any]:
        """
        Orchestrates all agents: destination specialist, flight, hotel, and budget analyst.
        """
        try:
            agents_results = {}

            # 1. Destination Specialist
            agents_results["destination_specialist"] = {
                "result": await self.execute_markdown_agent("destination_specialist", request.dict()),
                "confidence": 0.8,
                "reasoning": ""
            }

            # 2. Flight Search Agent (real API)
            flight_result = await self.execute_special_agent("flight_search_agent", request.dict())
            agents_results["flight_search_agent"] = flight_result

            # 3. Hotel Search Agent (real API)
            hotel_result = await self.execute_special_agent("hotel_search_agent", request.dict())
            agents_results["hotel_search_agent"] = hotel_result

            # 4. Budget Analyst (must run last with flight/hotel data)
            budget_context = request.dict()
            budget_context["flight_search_results"] = flight_result.get("result", {})
            budget_context["hotel_search_results"] = hotel_result.get("result", {})

            budget_result = await self.execute_markdown_agent("budget_analyst", budget_context)
            agents_results["budget_analyst"] = {
                "result": budget_result,
                "confidence": 0.8,
                "reasoning": ""
            }

            return {"agents": agents_results}

        except Exception as e:
            logger.error(f"Trip planning error: {e}")
            return {"error": str(e)}

    async def _call_claude(self, prompt: str) -> Dict[str, Any]:
        """
        Calls Claude API and extracts JSON from response.
        """
        try:
            response = await self.client.messages.create(
                model="claude-opus-4-1-20250805",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text if response.content else ""

            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            if start_idx != -1 and end_idx != 0:
                return json.loads(content[start_idx:end_idx])

            logger.error(f"No JSON found in Claude response. Preview: {content[:200]}")
            return {"raw_response": content}

        except Exception as e:
            logger.error(f"Claude call failed: {e}")
            return {"error": str(e)}

# Global instance
ai_agent = AITripPlanningAgent()
