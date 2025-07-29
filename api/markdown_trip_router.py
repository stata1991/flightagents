from fastapi import APIRouter, HTTPException
from api.ai_agents import ai_agent
from api.models import TripPlanningRequest

router = APIRouter(prefix="/markdown-trip", tags=["Markdown Agents"])

@router.post("/plan")
async def plan_trip(request: TripPlanningRequest):
    """
    Endpoint to run the full markdown-based trip planning flow.
    """
    try:
        result = await ai_agent.plan_trip_with_agents(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
