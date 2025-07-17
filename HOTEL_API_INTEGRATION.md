# Hotel API Integration Documentation

## Overview

The AI Trip Planner now includes comprehensive hotel search functionality powered by the Booking.com RapidAPI. This integration allows users to search for hotels, get detailed information, check availability, and generate booking links directly within the trip planning system.

## Features

### 1. Hotel Search
- Search hotels by location, dates, and guest requirements
- Filter by price, rating, amenities, and more
- Support for adults, children, and multiple rooms
- Real-time availability checking

### 2. Hotel Details
- Comprehensive hotel information including photos, reviews, and amenities
- Room availability and pricing
- Cancellation policies and booking terms

### 3. Booking Integration
- Direct booking links to Booking.com
- Price comparison and availability tracking
- Multi-currency support

### 4. AI Agent Integration
- Hotel search agent integrated into the multi-agent trip planning system
- Automatic hotel recommendations based on trip requirements
- Budget-aware hotel suggestions

## API Endpoints

### Hotel Search

#### POST `/hotels/search`
Search for hotels using a structured request.

**Request Body:**
```json
{
  "location": "New York",
  "check_in": "2024-12-15",
  "check_out": "2024-12-18",
  "adults": 2,
  "children": [5, 8],
  "rooms": 1,
  "currency": "USD",
  "language": "en-us",
  "page_number": 1,
  "order": "price"
}
```

**Response:**
```json
{
  "location": "New York",
  "check_in": "2024-12-15",
  "check_out": "2024-12-18",
  "total_results": 150,
  "hotels": [
    {
      "hotel": {
        "hotel_id": "12345",
        "name": "Grand Hotel New York",
        "address": "123 Broadway",
        "city": "New York",
        "country": "United States",
        "rating": 4.5,
        "review_score": 8.5,
        "review_count": 1250,
        "star_rating": 5,
        "amenities": ["wifi", "pool", "gym"],
        "photos": ["url1", "url2"]
      },
      "rooms": [
        {
          "room_id": "room123",
          "room_type": "Deluxe Double",
          "price_per_night": 200.0,
          "total_price": 600.0,
          "currency": "USD"
        }
      ],
      "average_price_per_night": 200.0,
      "total_price": 600.0,
      "currency": "USD",
      "availability": true
    }
  ]
}
```

#### GET `/hotels/search`
Search for hotels using query parameters.

**Parameters:**
- `location` (required): Destination location
- `check_in` (required): Check-in date (YYYY-MM-DD)
- `check_out` (required): Check-out date (YYYY-MM-DD)
- `adults` (optional): Number of adult guests (default: 1)
- `children` (optional): Children ages (comma-separated)
- `rooms` (optional): Number of rooms (default: 1)
- `currency` (optional): Currency code (default: USD)
- `order` (optional): Sort order (price, rating, distance)

### Hotel Details

#### GET `/hotels/details/{hotel_id}`
Get detailed information about a specific hotel.

**Parameters:**
- `hotel_id` (path): Hotel ID
- `check_in` (query): Check-in date
- `check_out` (query): Check-out date
- `adults` (query): Number of adult guests
- `children` (query): Children ages (comma-separated)

### Hotel Availability

#### GET `/hotels/availability/{hotel_id}`
Check availability for a specific hotel.

**Parameters:**
- `hotel_id` (path): Hotel ID
- `check_in` (query): Check-in date
- `check_out` (query): Check-out date
- `adults` (query): Number of adult guests
- `children` (query): Children ages (comma-separated)

### Hotel Photos

#### GET `/hotels/photos/{hotel_id}`
Get photos for a specific hotel.

**Parameters:**
- `hotel_id` (path): Hotel ID

### Hotel Reviews

#### GET `/hotels/reviews/{hotel_id}`
Get reviews for a specific hotel.

**Parameters:**
- `hotel_id` (path): Hotel ID
- `page` (query): Page number (default: 1)
- `language` (query): Language code (default: en-us)

### Booking URL Generation

#### GET `/hotels/booking-url/{hotel_id}`
Generate a booking URL for a hotel.

**Parameters:**
- `hotel_id` (path): Hotel ID
- `check_in` (query): Check-in date
- `check_out` (query): Check-out date
- `adults` (query): Number of adult guests
- `children` (query): Children ages (comma-separated)
- `rooms` (query): Number of rooms
- `currency` (query): Currency code

### Popular Destinations

#### GET `/hotels/popular-destinations`
Get list of popular hotel destinations.

### Hotel Amenities

#### GET `/hotels/amenities`
Get list of available hotel amenities.

## Data Models

### HotelSearchRequest
```python
class HotelSearchRequest(BaseModel):
    location: str
    check_in: str
    check_out: str
    adults: int = 1
    children: List[int] = []
    rooms: int = 1
    currency: str = "USD"
    language: str = "en-us"
    page_number: int = 1
    order: str = "price"
```

### HotelInfo
```python
class HotelInfo(BaseModel):
    hotel_id: str
    name: str
    address: str
    city: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_score: Optional[float] = None
    review_count: Optional[int] = None
    star_rating: Optional[int] = None
    property_type: Optional[str] = None
    amenities: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    description: Optional[str] = None
    booking_url: Optional[str] = None
```

### HotelRoom
```python
class HotelRoom(BaseModel):
    room_id: str
    room_type: str
    bed_configuration: Optional[str] = None
    max_occupancy: Optional[int] = None
    cancellation_policy: Optional[str] = None
    meal_plan: Optional[str] = None
    price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    availability: bool = True
```

### HotelSearchResult
```python
class HotelSearchResult(BaseModel):
    hotel: HotelInfo
    rooms: List[HotelRoom]
    average_price_per_night: Optional[float] = None
    total_price: Optional[float] = None
    currency: str = "USD"
    availability: bool = True
```

## AI Agent Integration

The hotel search functionality is integrated into the AI trip planning system through the `HOTEL_SEARCH_AGENT`. This agent:

1. **Automatically searches for hotels** based on trip requirements
2. **Recommends hotels** based on budget and preferences
3. **Generates booking links** for top recommendations
4. **Integrates with the overall itinerary** planning

### Hotel Search Agent

The hotel search agent is automatically triggered during trip planning and provides:

- Real hotel search results from Booking.com
- Price comparisons and availability
- Booking links for easy reservation
- Integration with the overall trip budget

## Usage Examples

### Basic Hotel Search
```python
from api.hotel_client import HotelClient
from api.models import HotelSearchRequest

# Initialize client
hotel_client = HotelClient()

# Create search request
request = HotelSearchRequest(
    location="Paris",
    check_in="2024-12-20",
    check_out="2024-12-23",
    adults=2,
    children=[5, 8],
    rooms=1
)

# Search for hotels
result = hotel_client.search_hotels(request)

# Process results
for hotel_result in result.hotels:
    print(f"Hotel: {hotel_result.hotel.name}")
    print(f"Price: ${hotel_result.average_price_per_night}/night")
```

### Generate Booking URL
```python
# Generate booking URL for a specific hotel
booking_url = hotel_client.generate_hotel_booking_url(
    hotel_id="12345",
    check_in="2024-12-20",
    check_out="2024-12-23",
    adults=2,
    children=[5, 8],
    rooms=1,
    currency="USD"
)
print(f"Booking URL: {booking_url}")
```

### AI Trip Planning with Hotels
```python
from api.ai_agents import AITripPlanningAgent
from api.models import TripPlanningRequest

# Create trip planning request
request = TripPlanningRequest(
    origin="New York",
    destination="Paris",
    duration_days=7,
    start_date="2024-12-20",
    travelers=2,
    budget_range="moderate"
)

# Plan trip with hotel search
agent = AITripPlanningAgent()
result = await agent.plan_trip_with_agents(request)

# Access hotel search results
hotel_results = result.get("hotel_search_results", {})
hotels = hotel_results.get("hotels", [])
```

## Error Handling

The hotel API integration includes comprehensive error handling:

1. **API Errors**: Network issues, rate limits, and API failures
2. **Validation Errors**: Invalid dates, missing required fields
3. **Data Errors**: Malformed responses, missing hotel data

All errors are logged and returned with appropriate HTTP status codes.

## Configuration

### API Keys
The hotel API uses the same Booking.com RapidAPI key as the flight search:

```python
# In hotel_client.py
self.headers = {
    'x-rapidapi-host': 'booking-com15.p.rapidapi.com',
    'x-rapidapi-key': 'your-api-key-here'
}
```

### Environment Variables
No additional environment variables are required beyond the existing Booking.com API key.

## Testing

Run the test script to verify the hotel API integration:

```bash
python test_hotel_api.py
```

This will test:
- Hotel search functionality
- Model creation and validation
- Booking URL generation
- Error handling

## Future Enhancements

Planned improvements for the hotel API integration:

1. **Advanced Filtering**: More granular filters for amenities, location, etc.
2. **Price Alerts**: Track price changes and notify users
3. **Hotel Reviews**: Integrate user reviews and ratings
4. **Alternative Accommodations**: Support for vacation rentals, hostels, etc.
5. **Group Bookings**: Enhanced support for large group reservations
6. **Loyalty Programs**: Integration with hotel loyalty programs

## Support

For issues or questions about the hotel API integration:

1. Check the logs for detailed error messages
2. Verify API key configuration
3. Test with the provided test script
4. Review the API documentation for parameter requirements

The hotel API integration is designed to be robust, scalable, and user-friendly, providing comprehensive hotel search and booking capabilities within the AI Trip Planner system. 