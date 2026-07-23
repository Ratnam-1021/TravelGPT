import os
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

from app.config import settings
from app.models.schemas import TripRequest, ItineraryResponse, CostEstimate, PDFExportRequest
from app.services.agent import travel_agent_service
from app.services.cost import cost_calculator
from app.services.rag import rag_service
from app.services.pdf_generator import pdf_generator_service

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Agent Trip Planner powered by FastAPI, ChromaDB RAG, Groq/OpenAI, & ReportLab PDF Exporter.",
    version="1.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "default_provider": settings.DEFAULT_PROVIDER,
        "groq_model": settings.GROQ_MODEL,
        "rag_status": "ready" if rag_service.collection is not None else "fallback"
    }

# API Endpoints
@app.post("/api/plan", response_model=ItineraryResponse)
def plan_trip_endpoint(request: TripRequest):
    """Generate complete AI itinerary using RAG knowledge base & LLM Agent."""
    try:
        itinerary = travel_agent_service.plan_trip(request)
        return itinerary
    except Exception as e:
        print(f"[API Error] /api/plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cost", response_model=CostEstimate)
def calculate_cost_endpoint(request: TripRequest):
    """Calculate approximate trip cost and budget feasibility."""
    try:
        cost = cost_calculator.calculate_trip_cost(
            destination=request.destination,
            duration_days=request.duration_days,
            travelers_count=request.travelers_count,
            target_budget=request.budget,
            currency=request.currency,
            travel_style=request.travel_style
        )
        return cost
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export-pdf")
def export_pdf_endpoint(request: PDFExportRequest):
    """Generates and downloads a beautifully formatted PDF itinerary."""
    try:
        pdf_buffer = pdf_generator_service.generate_itinerary_pdf(request.itinerary)
        filename = f"Itinerary_{request.itinerary.get('destination', 'Trip').replace(' ', '_')}.pdf"
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"[API Error] /api/export-pdf: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation failed: {str(e)}")

@app.get("/api/destinations")
def get_destinations_endpoint():
    """List available pre-indexed destinations in ChromaDB RAG."""
    data_dir = settings.DATA_DIR
    guides_dir = os.path.join(data_dir, "guides")
    destinations = []
    if os.path.exists(guides_dir):
        for f in os.listdir(guides_dir):
            if f.endswith(".md"):
                destinations.append(f.replace(".md", "").title())
    return {"destinations": destinations}

# Static Files & Web UI mounting
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    def read_root():
        return FileResponse(os.path.join(frontend_dir, "index.html"))
