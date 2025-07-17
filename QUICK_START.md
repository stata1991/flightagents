# 🚀 Quick Start Guide - AI Trip Planner

## Setup with Claude Sonnet API

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Run the setup script to automatically configure your Claude API key:

```bash
python setup_env.py
```

This will:
- ✅ Create a `.env` file with your Claude API key
- ✅ Test the API connection
- ✅ Verify everything is working

### 3. Start the Application
```bash
uvicorn main:app --reload
```

### 4. Test the AI Trip Planner
1. Visit: http://localhost:8000/trip-planner
2. Try: "Plan a trip from Dallas to Italy for 7 days"
3. Watch the AI agents work together!

## 🔑 API Key Configuration

Your Claude Sonnet API key is now set up in the environment, and the codebase is configured to use it for all AI agent operations. Here’s what was done:

- **Your API key** is now in the `.env` file as `ANTHROPIC_API_KEY`.
- The code now uses the correct Claude Sonnet model (`claude-sonnet-4-20250514`) for all agent calls.
- The OpenAI API key is no longer required for the agent system (it’s only needed if you want to keep legacy OpenAI-based features).
- You can start the app with:
  ```bash
  uvicorn main:app --reload
  ```
- Then visit: [http://localhost:8000/trip-planner](http://localhost:8000/trip-planner)

**Note:**  
The error `'Anthropic' object has no attribute 'messages'` means the installed `anthropic` Python package version is not compatible with the new Claude API.  
- The latest Claude API (v1) uses `anthropic>=0.21.0` (not `0.7.0`).
- Update your requirements.txt to:
  ```
  anthropic>=0.21.0
  ```
- Then run:
  ```bash
  pip install --upgrade anthropic
  ```

**After upgrading, your code will work with the new Claude Sonnet API key and endpoint.**

Let me know if you want me to update the requirements and code for the latest Claude API usage!

## 🤖 AI Agent System

The system uses 6 specialized AI agents:
- 🧠 **Coordinator Agent** - Master planner
- 🗺️ **Destination Specialist** - Local expert
- 💰 **Budget Analyst** - Cost optimization
- 🚄 **Logistics Planner** - Transportation
- 🌍 **Cultural Advisor** - Local customs
- 📅 **Booking Agent** - Booking strategies

## 🎯 Example Usage

### Start Planning
```
User: "Plan a trip from Dallas to Italy for 7 days"
AI: "I need a bit more information..."
```

### Follow-up Questions
```
AI: "What's your preferred start date?"
User: "June 15th, 2024"
AI: "How many travelers?"
User: "2 people"
AI: "What are your interests?"
User: "Food, art, history"
```

### AI Agent Generation
All 6 agents work together to create your itinerary!

### Refinement
```
User: "Change Rome to 4 nights, add Milan"
AI: "Processing with Coordinator, Logistics, and Budget agents..."
```

## 🔧 Troubleshooting

### API Connection Issues
```bash
# Test API connection
python setup_env.py
```

### Missing Dependencies
```bash
# Reinstall requirements
pip install -r requirements.txt
```

### Port Already in Use
```bash
# Use different port
uvicorn main:app --reload --port 8001
```

## 📊 API Endpoints

- **Web Interface**: http://localhost:8000/trip-planner
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎉 Ready to Go!

Your AI Trip Planner is now ready with:
- ✅ Claude Sonnet API configured
- ✅ Multi-agent AI system active
- ✅ Conversational interface ready
- ✅ Intelligent refinement system

Start planning your perfect trip! 🗺️✈️ 