from typing import List, Dict, Any
from app.models.schemas import CostEstimate, CostCategoryBreakdown

# Destination cost multipliers relative to base USD estimates
DESTINATION_MULTIPLIERS = {
    "paris": 1.25,
    "tokyo": 1.15,
    "new york": 1.45,
    "nyc": 1.45,
    "bali": 0.55,
    "rome": 1.10,
    "dubai": 1.35,
    "london": 1.35,
    "barcelona": 1.05,
    "singapore": 1.30,
    "bangkok": 0.50
}

TRAVEL_STYLE_MULTIPLIERS = {
    "budget": 0.60,
    "backpacking": 0.50,
    "balanced": 1.00,
    "mid-range": 1.00,
    "cultural": 1.05,
    "adventure": 1.10,
    "luxury": 2.20
}

class CostCalculatorService:
    @staticmethod
    def calculate_trip_cost(
        destination: str,
        duration_days: int,
        travelers_count: int,
        target_budget: float,
        currency: str = "USD",
        travel_style: str = "Balanced",
        activity_items_cost: float = 0.0
    ) -> CostEstimate:
        """Calculates precise cost breakdown based on travel parameters."""
        
        dest_key = destination.lower().strip()
        dest_mult = DESTINATION_MULTIPLIERS.get(dest_key, 1.0)
        style_mult = TRAVEL_STYLE_MULTIPLIERS.get(travel_style.lower().strip(), 1.0)
        
        # Base daily rates per traveler (in USD)
        base_hotel_per_night = 110.0 * dest_mult * style_mult
        base_food_per_day = 45.0 * dest_mult * style_mult
        base_transport_per_day = 15.0 * dest_mult
        base_intercity_flights = 250.0 * travelers_count * dest_mult
        
        # Totals
        accommodation_total = base_hotel_per_night * duration_days * (1 if travelers_count <= 2 else (travelers_count / 1.8))
        food_total = base_food_per_day * duration_days * travelers_count
        local_transit_total = base_transport_per_day * duration_days * travelers_count
        flights_total = base_intercity_flights
        activities_total = max(activity_items_cost, (30.0 * duration_days * travelers_count * style_mult))
        emergency_buffer = (accommodation_total + food_total + local_transit_total + activities_total) * 0.08

        total_cost = round(accommodation_total + food_total + local_transit_total + flights_total + activities_total + emergency_buffer, 2)
        
        # Categorized breakdown
        breakdown = [
            CostCategoryBreakdown(
                category="Accommodation",
                amount=round(accommodation_total, 2),
                percentage=round((accommodation_total / total_cost) * 100, 1),
                notes=f"{duration_days} nights hotel/villa ({travel_style} tier)"
            ),
            CostCategoryBreakdown(
                category="Food & Dining",
                amount=round(food_total, 2),
                percentage=round((food_total / total_cost) * 100, 1),
                notes=f"3 meals + snacks daily for {travelers_count} travelers"
            ),
            CostCategoryBreakdown(
                category="Flights & Intercity Transport",
                amount=round(flights_total, 2),
                percentage=round((flights_total / total_cost) * 100, 1),
                notes=f"Roundtrip transit & airport transfers"
            ),
            CostCategoryBreakdown(
                category="Local Transit & Metro",
                amount=round(local_transit_total, 2),
                percentage=round((local_transit_total / total_cost) * 100, 1),
                notes=f"Subway/Metro passes & local taxis"
            ),
            CostCategoryBreakdown(
                category="Activities & Sightseeing",
                amount=round(activities_total, 2),
                percentage=round((activities_total / total_cost) * 100, 1),
                notes=f"Museum tickets, tours & entry passes"
            ),
            CostCategoryBreakdown(
                category="Emergency Reserve / Misc",
                amount=round(emergency_buffer, 2),
                percentage=round((emergency_buffer / total_cost) * 100, 1),
                notes="8% travel contingency buffer"
            )
        ]

        diff = round(target_budget - total_cost, 2)
        if diff >= 0:
            budget_status = "Under Budget" if diff > (target_budget * 0.1) else "On Budget"
        else:
            budget_status = "Over Budget"

        return CostEstimate(
            total_estimated_cost=total_cost,
            target_budget=target_budget,
            currency=currency,
            budget_status=budget_status,
            difference=abs(diff),
            breakdown=breakdown
        )

cost_calculator = CostCalculatorService()
