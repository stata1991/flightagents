from fastapi import FastAPI
from api.search_router import router as search_router

app = FastAPI(title="FlightTickets.ai API")

app.include_router(search_router)
