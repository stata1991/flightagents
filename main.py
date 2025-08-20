from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from api.search_router import router as search_router
from api.trip_planner_router import router as trip_planner_router
from api.destination_router import router as destination_router
from api.hotel_router import router as hotel_router
from api.hybrid_trip_router import router as hybrid_router
from api.markdown_trip_router import router as markdown_trip_router
from api.chat_integration_router import router as chat_integration_router

app = FastAPI(title="FlightTickets.ai API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

app.include_router(search_router)
app.include_router(trip_planner_router)
app.include_router(destination_router)
app.include_router(hotel_router)
app.include_router(hybrid_router)
app.include_router(markdown_trip_router)
app.include_router(chat_integration_router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("hybrid_trip_planner.html", {"request": request})

@app.get("/trip-planner", response_class=HTMLResponse)
async def trip_planner_page(request: Request):
    return templates.TemplateResponse("trip_planner.html", {"request": request})

@app.get("/enhanced-search", response_class=HTMLResponse)
async def enhanced_search_page(request: Request):
    return templates.TemplateResponse("enhanced_search.html", {"request": request})

@app.get("/ai-trip-planner", response_class=HTMLResponse)
async def ai_trip_planner_page(request: Request):
    return templates.TemplateResponse("natural_trip_planner.html", {"request": request})

@app.get("/hybrid", response_class=HTMLResponse)
async def hybrid_planner_page(request: Request):
    return templates.TemplateResponse("hybrid_trip_planner.html", {"request": request})

@app.get("/enhanced-chat", response_class=HTMLResponse)
async def enhanced_chat_page(request: Request):
    return templates.TemplateResponse("enhanced_chat_interface.html", {"request": request})

@app.get("/enhanced-travel", response_class=HTMLResponse)
async def enhanced_travel_page(request: Request):
    return templates.TemplateResponse("enhanced_travel_interface.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FlightTickets.ai API server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🎯 AI Trip Planner: http://localhost:8000/ai-trip-planner")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
