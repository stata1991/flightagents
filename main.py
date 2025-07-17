from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from api.search_router import router as search_router
from api.trip_planner_router import router as trip_planner_router
from api.destination_router import router as destination_router
from api.hotel_router import router as hotel_router

app = FastAPI(title="FlightTickets.ai API")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

app.include_router(search_router)
app.include_router(trip_planner_router)
app.include_router(destination_router)
app.include_router(hotel_router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/trip-planner", response_class=HTMLResponse)
async def trip_planner_page(request: Request):
    return templates.TemplateResponse("trip_planner.html", {"request": request})
