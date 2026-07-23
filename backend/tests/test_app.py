import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.models.schemas import TripRequest
from app.services.cost import cost_calculator
from app.services.rag import rag_service
from app.services.agent import travel_agent_service
from app.services.pdf_generator import pdf_generator_service

def test_cost_calculator():
    cost = cost_calculator.calculate_trip_cost(
        destination="Paris",
        duration_days=5,
        travelers_count=2,
        target_budget=2000.0,
        currency="USD",
        travel_style="Balanced"
    )
    assert cost.total_estimated_cost > 0
    assert cost.budget_status in ["Under Budget", "On Budget", "Over Budget"]
    assert len(cost.breakdown) == 6

def test_rag_search():
    results = rag_service.search("Paris Louvre museum visa policy", top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0

def test_agent_plan_and_pdf():
    req = TripRequest(
        destination="Paris",
        duration_days=3,
        budget=1800.0,
        currency="USD",
        travelers_count=2,
        travel_style="Balanced",
        interests=["Art & Museums", "Gastronomy"]
    )
    itinerary = travel_agent_service.plan_trip(req)
    assert itinerary.destination == "Paris"
    assert itinerary.duration_days == 3
    assert len(itinerary.days) == 3

    # PDF Test
    pdf_bytes = pdf_generator_service.generate_itinerary_pdf(itinerary.model_dump())
    assert pdf_bytes is not None
    assert len(pdf_bytes.getvalue()) > 500
