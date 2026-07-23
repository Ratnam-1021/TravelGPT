from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TripRequest(BaseModel):
    destination: str = Field(..., json_schema_extra={"example": "Paris"})
    duration_days: int = Field(..., ge=1, le=14, json_schema_extra={"example": 5})
    budget: float = Field(..., ge=100, json_schema_extra={"example": 2000})
    currency: str = Field(default="USD", json_schema_extra={"example": "USD"})
    travelers_count: int = Field(default=2, ge=1, json_schema_extra={"example": 2})
    travel_style: str = Field(default="Balanced", json_schema_extra={"example": "Luxury / Mid-range / Budget / Adventure / Cultural / Relaxing"})
    interests: List[str] = Field(default=[], json_schema_extra={"example": ["Art & Museums", "Gastronomy", "Historical Sites"]})
    special_requirements: Optional[str] = Field(default="", json_schema_extra={"example": "Vegetarian food options, low walking distance"})

class ActivityItem(BaseModel):
    time_slot: str # Morning / Afternoon / Evening
    title: str
    description: str
    location: str
    estimated_cost: float
    category: str # Sightseeing / Food / Transport / Activity / Leisure

class DayItinerary(BaseModel):
    day: int
    theme: str
    activities: List[ActivityItem]
    daily_estimated_cost: float
    insider_tips: List[str]

class CostCategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    notes: str

class CostEstimate(BaseModel):
    total_estimated_cost: float
    target_budget: float
    currency: str
    budget_status: str # Under Budget / On Budget / Over Budget
    difference: float
    breakdown: List[CostCategoryBreakdown]

class RAGContextItem(BaseModel):
    source: str
    content: str
    relevance_score: float

class ItineraryResponse(BaseModel):
    trip_title: str
    destination: str
    duration_days: int
    travelers_count: int
    currency: str
    summary: str
    days: List[DayItinerary]
    cost_estimate: CostEstimate
    retrieved_policies_and_guides: List[RAGContextItem]
    generated_at: str

class PDFExportRequest(BaseModel):
    itinerary: Dict[str, Any]
