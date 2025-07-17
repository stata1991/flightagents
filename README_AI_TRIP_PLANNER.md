# AI Trip Planner - FlightTickets.ai

## Overview

This is an **AI-powered conversational trip planner** that uses a **team of specialized AI agents** to help users plan multi-city, budget-aware trips through a smart chat interface. The system leverages Claude Sonnet with a multi-agent architecture to provide comprehensive, intelligent travel planning.

## 🤖 AI Agent System

### **Multi-Agent Architecture**

The system uses **6 specialized AI agents** working together:

1. **🧠 Coordinator Agent** - Master trip planning coordinator
   - Analyzes user requests and breaks them into specialized tasks
   - Coordinates between different specialist agents
   - Makes final decisions on itinerary structure
   - Ensures all aspects are properly planned

2. **🗺️ Destination Specialist** - Local destination expert
   - Best times to visit recommendations
   - Must-see attractions and hidden gems
   - Local favorites and cultural highlights
   - Seasonal considerations

3. **💰 Budget Analyst** - Cost optimization specialist
   - Detailed budget breakdowns
   - Cost-saving strategies
   - Seasonal price variations
   - Budget optimization recommendations

4. **🚄 Logistics Planner** - Transportation and route expert
   - Optimal transportation planning
   - Route optimization between cities
   - Travel tips and contingency plans
   - Booking timing recommendations

5. **🌍 Cultural Advisor** - Local customs and culture expert
   - Cultural etiquette guidelines
   - Local customs and traditions
   - Language tips and phrases
   - Cultural do's and don'ts

6. **📅 Booking Agent** - Booking strategy specialist
   - Best booking platforms and timing
   - Money-saving strategies
   - Flexibility recommendations
   - Cancellation policies

### **Agent Collaboration Flow**

```
User Request → Coordinator Agent → Specialized Agents → Combined Results → Final Itinerary
     ↓              ↓                    ↓                    ↓              ↓
Initial Input → Task Breakdown → Parallel Processing → Intelligent Synthesis → User Output
```

## Features

- **🧠 Multi-Agent Intelligence**: 6 specialized AI agents working in concert
- **💬 Conversational Interface**: Natural language trip planning
- **🏙️ Multi-City Support**: Complex itineraries with multiple destinations
- **💰 Budget Awareness**: Real-time cost tracking and optimization
- **🔄 Adaptive Updates**: Intelligent refinement using relevant agents
- **📊 Agent Insights**: View reasoning and confidence scores from each agent
- **🎯 Bookable Results**: Direct booking links for flights and hotels (future integration)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# Anthropic API Key for Claude Sonnet (Required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI API Key (for existing functionality)
OPENAI_API_KEY=your_openai_api_key_here

# Rapid API Key (for future Booking.com integration)
RAPID_API_KEY=your_rapid_api_key_here
```

### 3. Run the Application

```bash
uvicorn main:app --reload
```

## API Endpoints

### Trip Planner Endpoints

- `POST /trip-planner/start` - Start a new trip planning session with AI agents
- `POST /trip-planner/{session_id}/answer` - Answer follow-up questions
- `POST /trip-planner/{session_id}/refine` - Refine itinerary using specialized agents
- `GET /trip-planner/{session_id}/agents` - Get insights from AI agents
- `GET /trip-planner/{session_id}/status` - Get session status
- `POST /trip-planner/{session_id}/finalize` - Finalize itinerary for booking
- `DELETE /trip-planner/{session_id}` - Delete a session

### Web Interface

- `GET /` - Main flight search interface
- `GET /trip-planner` - AI Trip Planner chat interface with agent visualization

## Usage Flow

### 1. Start Planning
User provides initial request: "Plan a trip from Dallas to Italy for 7 days"

### 2. AI Agent Coordination
**Coordinator Agent** analyzes the request and determines what information is needed

### 3. Follow-up Questions
System asks for missing information:
- Preferred start date
- Number of travelers
- Trip interests
- Budget preference

### 4. Multi-Agent Itinerary Generation
All 6 AI agents work together:
- **Coordinator**: Creates overall structure
- **Destination Specialist**: Recommends attractions and timing
- **Budget Analyst**: Provides cost breakdown
- **Logistics Planner**: Plans transportation
- **Cultural Advisor**: Adds cultural insights
- **Booking Agent**: Suggests booking strategies

### 5. Intelligent Refinement
User can make changes up to 5 times:
- "Change Rome to 4 nights" → **Coordinator + Logistics + Budget** agents
- "Add Milan to the itinerary" → **Coordinator + Destination + Logistics** agents
- "Increase budget to luxury" → **Budget + Destination** agents

### 6. Finalization
System prepares booking options and provides:
- Flight recommendations
- Hotel bookings
- Total cost summary
- Direct booking links

## Architecture

### Core Components

1. **AITripPlanningAgent** (`api/ai_agents.py`)
   - Multi-agent orchestration system
   - Specialized agent implementations
   - Agent task management and execution
   - Result combination and synthesis

2. **AITripPlanner** (`api/ai_trip_planner.py`)
   - Conversation session management
   - Agent-based itinerary generation
   - Intelligent refinement system
   - Agent result analysis

3. **Trip Planner Router** (`api/trip_planner_router.py`)
   - API endpoints for the conversational flow
   - Agent insights endpoints
   - Session management
   - Request/response handling

4. **Data Models** (`api/models.py`)
   - Pydantic models for type safety
   - Agent task and result structures
   - Conversation state management

5. **Frontend Interface** (`templates/trip_planner.html`)
   - Chat-like interface with agent visualization
   - Real-time conversation
   - Agent insights display
   - Refinement controls

### Agent Communication Flow

```
User Input → Coordinator Agent → Task Distribution → Specialized Agents → Result Synthesis → User Output
     ↓              ↓                    ↓                    ↓              ↓              ↓
Natural Language → Analysis → Parallel Processing → Expert Insights → Intelligent Combination → Structured Response
```

## Example API Usage

### Start Trip Planning with AI Agents

```bash
curl -X POST "http://localhost:8000/trip-planner/start" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "Dallas",
    "destination": "Italy",
    "duration_days": 7,
    "travelers": 2,
    "trip_type": "leisure",
    "budget_range": "moderate"
  }'
```

### Get Agent Insights

```bash
curl -X GET "http://localhost:8000/trip-planner/{session_id}/agents"
```

### Refine with AI Agents

```bash
curl -X POST "http://localhost:8000/trip-planner/{session_id}/refine" \
  -H "Content-Type: application/json" \
  -d '{
    "changes": {
      "request": "Change Rome to 4 nights and add Milan"
    },
    "reason": "Want to spend more time in Rome and visit Milan"
  }'
```

## Agent Intelligence Features

### **Smart Refinement Analysis**
The system automatically determines which agents to involve based on the type of change:
- **Budget changes** → Budget Analyst + Coordinator
- **Route changes** → Logistics Planner + Coordinator + Destination Specialist
- **Duration changes** → All agents (affects everything)
- **Destination changes** → Destination Specialist + Logistics + Cultural Advisor

### **Confidence Scoring**
Each agent provides confidence scores and reasoning for their recommendations:
- High confidence (0.9+) → Strong recommendation
- Medium confidence (0.7-0.9) → Good recommendation with alternatives
- Low confidence (<0.7) → Suggests additional research

### **Agent Collaboration**
Agents share information and build upon each other's insights:
- Coordinator uses destination recommendations for route planning
- Budget Analyst considers logistics costs
- Cultural Advisor influences destination recommendations
- Booking Agent optimizes based on all other agents' insights

## Future Enhancements

1. **🔗 Booking.com Integration**: Real-time flight and hotel booking via Rapid API
2. **🧠 Advanced NLP**: Better natural language understanding for complex requests
3. **🌐 Multi-language Support**: Support for multiple languages
4. **👥 Group Planning**: Collaborative trip planning for groups
5. **📊 Real-time Pricing**: Live pricing updates during planning
6. **🌤️ Weather Integration**: Weather-aware itinerary planning
7. **🎉 Local Events**: Integration with local events and festivals
8. **🤖 Agent Learning**: Agents learn from user feedback and preferences
9. **📱 Mobile App**: Native mobile application
10. **🎯 Personalization**: User preference learning and customization

## Development

### Adding New Agents

1. **Define Agent Type**: Add to `AgentType` enum in `ai_agents.py`
2. **Implement Agent Function**: Create `_new_agent_agent()` method
3. **Add to Agent Registry**: Register in `__init__()` method
4. **Update Task Analysis**: Modify `_analyze_refinement_request()` for new agent types
5. **Test Integration**: Ensure agent works in the full pipeline

### Example: Adding a Food Specialist Agent

```python
# In ai_agents.py
class AgentType(str, Enum):
    # ... existing agents ...
    FOOD_SPECIALIST = "food_specialist"

# Add agent implementation
async def _food_specialist_agent(self, task: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation for food recommendations
    pass

# Register in __init__
self.agents[AgentType.FOOD_SPECIALIST] = self._food_specialist_agent
```

### Testing

```bash
# Test the API endpoints
curl -X GET "http://localhost:8000/docs"  # OpenAPI documentation

# Test the web interface
open http://localhost:8000/trip-planner

# Test agent insights
curl -X GET "http://localhost:8000/trip-planner/{session_id}/agents"
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure your Anthropic API key is set correctly
2. **Agent Communication Errors**: Check agent task dependencies
3. **JSON Parsing Errors**: Verify agent response format
4. **Session Not Found**: Verify session ID is correct
5. **Maximum Refinements**: Users are limited to 5 refinements per session

### Agent Debugging

```bash
# Enable debug logging
uvicorn main:app --reload --log-level debug

# Check agent insights for debugging
curl -X GET "http://localhost:8000/trip-planner/{session_id}/agents"
```

## Performance Considerations

- **Agent Parallelization**: Agents run in parallel where possible
- **Caching**: Agent results are cached for similar requests
- **Rate Limiting**: Respects API rate limits for Claude Sonnet
- **Session Management**: Efficient session storage and cleanup
- **Error Handling**: Graceful degradation if individual agents fail

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new agents
5. Submit a pull request

## License

This project is part of the FlightTickets.ai platform.

---

**🤖 Powered by Claude Sonnet and Multi-Agent AI Architecture** 