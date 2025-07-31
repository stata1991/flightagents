import asyncio
from api.ai_agents import ai_agent, AgentTask, AgentType

async def run_test():
    # Test the DESTINATION_SPECIALIST agent (uses itinerary-agent.md)
    task = AgentTask(
        agent_type=AgentType.DESTINATION_SPECIALIST,
        task_description="Plan a 5-day trip to Italy under $2000 for a couple",
        required_data={
            "destination": "Italy",
            "duration_days": 5,
            "budget": 2000,
            "interests": ["food", "culture"]
        }
    )

    result = await ai_agent.execute_agent_task(task)
    print("\n--- AGENT OUTPUT ---")
    print(result.result)

if __name__ == "__main__":
    asyncio.run(run_test())
