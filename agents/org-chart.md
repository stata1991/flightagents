# 🧠 TripPlanner.ai – AI Agent Org Chart

This document outlines the AI-powered org structure for TripPlanner.ai.  
Each agent is a Claude-style subagent defined in a Markdown file with specific skills, instructions, tone, and decision logic.

---

## 🏗️ Engineering

| Role               | File                                      | Description |
|--------------------|-------------------------------------------|-------------|
| Frontend Developer | `engineering/frontend-developer.md`       | Builds mobile-first, clean React UIs. |
| Backend Engineer   | `engineering/backend-engineer.md`         | Owns FastAPI backend, NLP logic, API integrations. |
| DevOps Engineer    | `engineering/devops-engineer.md`          | Manages AWS EC2 deployment, Docker, CI/CD pipelines. |

---

## 🎯 Product

| Role             | File                               | Description |
|------------------|------------------------------------|-------------|
| Product Manager  | `product/product-manager.md`       | Prioritizes roadmap, connects user pain to features. |
| UX Designer      | `product/ux-designer.md`           | Ensures the product is intuitive, delightful, and frictionless. |

---

## 📦 Operations

| Role            | File                                 | Description |
|------------------|--------------------------------------|-------------|
| Conversation Agent | `operations/conversation_agent.md`   | Creates engaging conversational experiences with structured questioning and personality. |
| Itinerary Agent | `operations/itinerary-agent.md`      | Generates personalized, themed daily trip itineraries from natural language prompts. |
| Destination Specialist | `product/destination_specialist.md` | Creates intelligent multi-city itineraries with smart airport logic and optimal routing. |
| Budget Analyst  | `operations/budget_analyst.md`       | Analyzes trip costs, provides budget breakdowns and cost-saving strategies. |
| Flight Search Agent | `operations/flight_search_agent.md` | Searches and analyzes flight options using real-time API data. |
| Hotel Search Agent | `operations/hotel_search_agent.md` | Searches and analyzes hotel options using real-time API data. |
| API Error Handler | `operations/api_error_handler.md`   | Manages API failures gracefully with fallback strategies. |

---

## 📈 Growth

| Role           | File                              | Description |
|----------------|-----------------------------------|-------------|
| Growth Hacker  | `growth/growth-hacker.md`         | Designs growth loops, runs A/B tests, boosts user acquisition & retention. |

---

## 📣 Marketing

| Role                | File                                      | Description |
|---------------------|-------------------------------------------|-------------|
| TikTok Strategist   | `marketing/tiktok-strategist.md`          | Creates short-form content using trends, humor, and hooks. |
| Instagram Strategist| `marketing/instagram-strategist.md`       | Crafts Reels, carousels, and aesthetic content to inspire users. |
| Twitter Strategist  | `marketing/twitter-strategist.md`         | Writes threads and tweets that spark curiosity and go viral. |

---

## 🧩 How to Use This Org

- **Claude / GPT Setup**: Each markdown file acts as a long-term memory instruction block for that subagent.
- **Task Flow**: You can route prompts through Product Manager → Itinerary Agent → Frontend/Backend → Growth.
- **Execution**: Use a system prompt like:  
  `"You are the AI Product Manager for TripPlanner.ai. Follow the instructions in product-manager.md and decide the next highest-impact feature to build."`

---

> 💡 Want to add real task queues? Create a `tasks/` folder and assign markdown-based tickets per agent.

> 🛠 Future Upgrade: Connect this org to a planner agent that routes tasks based on agent role + expertise.

---

---

## 🗺️ Visual Org Chart (Mermaid)

```mermaid
graph TD
    A[CEO / You 🧠] --> B1[Engineering]
    A --> B2[Product]
    A --> B3[Operations]
    A --> B4[Growth]
    A --> B5[Marketing]

    B1 --> C1[Frontend Developer]
    B1 --> C2[Backend Engineer]
    B1 --> C3[DevOps Engineer]

    B2 --> D1[Product Manager]
    B2 --> D2[UX Designer]

    B3 --> E1[Itinerary Agent]
    B3 --> E2[Destination Specialist]
    B3 --> E3[Budget Analyst]
    B3 --> E4[Flight Search Agent]
    B3 --> E5[Hotel Search Agent]
    B3 --> E6[API Error Handler]

    B4 --> F1[Growth Hacker]

    B5 --> G1[TikTok Strategist]
    B5 --> G2[Instagram Strategist]
    B5 --> G3[Twitter Strategist]
