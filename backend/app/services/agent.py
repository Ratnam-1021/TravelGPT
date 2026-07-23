import json
import re
from datetime import datetime
from typing import Dict, Any, List
import openai

from app.config import settings
from app.models.schemas import (
    TripRequest, ItineraryResponse, DayItinerary, ActivityItem, 
    CostEstimate, RAGContextItem
)
from app.services.rag import rag_service
from app.services.cost import cost_calculator

SYSTEM_PROMPT = """You are TravelGPT, an expert AI Travel Planner Agent.
Your job is to build detailed, highly realistic, and visually structured travel itineraries based on natural language user requests.

CRITICAL INSTRUCTIONS:
1. You MUST incorporate the retrieved Destination Guides and Travel Policies context provided below.
2. Produce realistic day-by-day timetables split into Morning, Afternoon, and Evening activities.
3. Include specific venue names, attraction tips, insider recommendations, and approximate local costs.
4. Output MUST be valid JSON adhering strictly to the JSON Schema requested. No commentary, no conversational fluff outside the JSON.
"""

class TravelAgentService:
    def __init__(self):
        pass

    def _get_llm_client(self):
        """Construct OpenAI client pointing to Groq or OpenAI backend."""
        if settings.DEFAULT_PROVIDER == "groq" or (not settings.OPENAI_API_KEY and settings.GROQ_API_KEY):
            return openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=settings.GROQ_API_KEY
            ), settings.GROQ_MODEL
        elif settings.OPENAI_API_KEY:
            return openai.OpenAI(
                api_key=settings.OPENAI_API_KEY
            ), settings.OPENAI_MODEL
        else:
            raise ValueError("No valid LLM API key configured! Please set GROQ_API_KEY or OPENAI_API_KEY.")

    def plan_trip(self, req: TripRequest) -> ItineraryResponse:
        """Main agent function: retrieves RAG context, invokes LLM, parses response, calculates cost."""
        
        # 1. RAG Search
        query = f"{req.destination} {req.travel_style} {' '.join(req.interests)} visa budget policies guide"
        retrieved_docs = rag_service.search(query=query, top_k=4)
        
        rag_context_str = "\n\n".join([
            f"--- Context Source: {doc['source']} ---\n{doc['content']}"
            for doc in retrieved_docs
        ])

        # 2. Build User Prompt
        user_prompt = f"""Plan a {req.duration_days}-day trip to {req.destination}.
User Parameters:
- Duration: {req.duration_days} days
- Travelers: {req.travelers_count} person(s)
- Budget Target: {req.currency} {req.budget}
- Travel Style: {req.travel_style}
- Interests: {', '.join(req.interests) if req.interests else 'General Exploration'}
- Special Requirements: {req.special_requirements or 'None'}

RETRIEVED KNOWLEDGE BASE CONTEXT (Destination Guides & Travel Policies):
{rag_context_str}

Please generate a JSON object matching this EXACT format:
{{
  "trip_title": "Descriptive Title for Trip",
  "summary": "2-3 sentence overview highlighting the experience",
  "days": [
    {{
      "day": 1,
      "theme": "Theme of Day 1",
      "activities": [
        {{
          "time_slot": "Morning",
          "title": "Activity Name",
          "description": "Short explanation and what to do",
          "location": "Specific Neighborhood or Place",
          "estimated_cost": 25.0,
          "category": "Sightseeing"
        }},
        {{
          "time_slot": "Afternoon",
          "title": "Activity Name",
          "description": "Short explanation",
          "location": "Place",
          "estimated_cost": 30.0,
          "category": "Food"
        }},
        {{
          "time_slot": "Evening",
          "title": "Activity Name",
          "description": "Short explanation",
          "location": "Place",
          "estimated_cost": 40.0,
          "category": "Activity"
        }}
      ],
      "daily_estimated_cost": 95.0,
      "insider_tips": ["Tip 1", "Tip 2"]
    }}
  ]
}}
Ensure exactly {req.duration_days} days are generated.
"""

        # 3. Call LLM
        client, model_name = self._get_llm_client()
        
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            raw_content = response.choices[0].message.content.strip()
            parsed_json = self._clean_and_parse_json(raw_content)
        except Exception as e:
            print(f"[Agent] LLM Execution Error: {e}. Generating structured fallback itinerary.")
            parsed_json = self._fallback_itinerary_generator(req)

        # 4. Process Days & Compute Activity Costs
        days_list = []
        total_activity_cost = 0.0
        
        for d in parsed_json.get("days", []):
            act_items = []
            day_cost = 0.0
            for act in d.get("activities", []):
                cost_val = float(act.get("estimated_cost", 15.0))
                day_cost += cost_val
                act_items.append(ActivityItem(
                    time_slot=act.get("time_slot", "Morning"),
                    title=act.get("title", "City Tour"),
                    description=act.get("description", "Explore local landmarks."),
                    location=act.get("location", req.destination),
                    estimated_cost=cost_val,
                    category=act.get("category", "Sightseeing")
                ))
            total_activity_cost += day_cost
            
            days_list.append(DayItinerary(
                day=d.get("day", len(days_list) + 1),
                theme=d.get("theme", f"Exploring {req.destination}"),
                activities=act_items,
                daily_estimated_cost=round(day_cost, 2),
                insider_tips=d.get("insider_tips", ["Keep your passport secure.", "Use public transportation passes."])
            ))

        # 5. Cost Engine Calculation
        cost_estimate = cost_calculator.calculate_trip_cost(
            destination=req.destination,
            duration_days=req.duration_days,
            travelers_count=req.travelers_count,
            target_budget=req.budget,
            currency=req.currency,
            travel_style=req.travel_style,
            activity_items_cost=total_activity_cost
        )

        # 6. Build Final Response
        rag_context_items = [
            RAGContextItem(
                source=doc.get("source", "Guide"),
                content=doc.get("content", ""),
                relevance_score=doc.get("relevance_score", 0.8)
            ) for doc in retrieved_docs
        ]

        return ItineraryResponse(
            trip_title=parsed_json.get("trip_title", f"{req.duration_days}-Day {req.travel_style} Getaway to {req.destination}"),
            destination=req.destination,
            duration_days=req.duration_days,
            travelers_count=req.travelers_count,
            currency=req.currency,
            summary=parsed_json.get("summary", f"A customized {req.duration_days}-day itinerary covering highlights of {req.destination}."),
            days=days_list,
            cost_estimate=cost_estimate,
            retrieved_policies_and_guides=rag_context_items,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        )

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        """Strip markdown codeblocks and parse JSON safely."""
        cleaned = re.sub(r"^```json\s*", "", raw_str, flags=re.MULTILINE)
        cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        return json.loads(cleaned)

    def _fallback_itinerary_generator(self, req: TripRequest) -> Dict[str, Any]:
        """Fallback JSON generator if LLM service is offline."""
        days = []
        for i in range(1, req.duration_days + 1):
            days.append({
                "day": i,
                "theme": f"Discovering {req.destination} - Highlights Part {i}",
                "activities": [
                    {
                        "time_slot": "Morning",
                        "title": f"Morning Tour of Key Landmarks in {req.destination}",
                        "description": "Guided walking tour visiting primary monuments and historical sites.",
                        "location": f"Central {req.destination}",
                        "estimated_cost": 25.0,
                        "category": "Sightseeing"
                    },
                    {
                        "time_slot": "Afternoon",
                        "title": "Local Gastronomy & Market Visit",
                        "description": "Sample famous local street food and popular regional specialties.",
                        "location": "Historic Food Market",
                        "estimated_cost": 30.0,
                        "category": "Food"
                    },
                    {
                        "time_slot": "Evening",
                        "title": "Sunset View & Evening Culture",
                        "description": "Enjoy scenic evening panoramas followed by dinner.",
                        "location": "Downtown Waterfront",
                        "estimated_cost": 45.0,
                        "category": "Leisure"
                    }
                ],
                "daily_estimated_cost": 100.0,
                "insider_tips": ["Buy subway passes online in advance.", "Always carry a small water bottle."]
            })
        return {
            "trip_title": f"{req.duration_days}-Day Trip to {req.destination}",
            "summary": f"An unforgettable trip to {req.destination} tailored to your {req.travel_style} travel preferences.",
            "days": days
        }

travel_agent_service = TravelAgentService()
