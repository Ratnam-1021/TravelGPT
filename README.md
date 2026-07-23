# ✈️ TravelGPT – AI Trip Planner

[![FastAPI](https://img.shields.io/badge/FastAPI-005587?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-RAG_Vector_Search-orange?style=for-the-badge)](https://www.trychroma.com/)
[![Groq](https://img.shields.io/badge/Groq_LLM-Llama_3.3_70B-purple?style=for-the-badge)](https://groq.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF_Exporter-red?style=for-the-badge)](https://www.reportlab.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)

**TravelGPT** is an enterprise-grade AI Trip Planner built with **FastAPI**, **ChromaDB (RAG)**, **Groq/OpenAI LLM Agents**, **Cost Estimation Engine**, **ReportLab PDF Exporter**, and a modern dark glassmorphism Web UI.

---

## 🌟 Key Features

1. **AI Agent Itinerary Planner**: Converts natural language requests into structured day-by-day itineraries (Morning, Afternoon, Evening activities) with venue locations and insider tips.
2. **RAG Vector Search Engine**: Ingests destination guides and travel policy documents (visas, baggage limits, travel insurance, budgeting strategies) into **ChromaDB** for context-augmented planning.
3. **Smart Cost Engine**: Itemizes estimated expenses into Accommodation, Food & Dining, Flights/Intercity, Local Transit, Activities, and Emergency Reserve with budget status tracking.
4. **PDF Itinerary Exporter**: Generates beautifully styled PDF travel documents with tables, timetables, and summaries.
5. **Modern Glassmorphism UI**: High-aesthetic dark mode web app with dynamic day timelines, visual budget consumption meters, and interactive chip selectors.
6. **Multi-Provider LLM Integration**: Pre-configured for high-speed inference via **Groq** (`llama-3.3-70b-versatile`), with support for **OpenAI** (`gpt-4o`) and **Claude**.
7. **Docker Containerization**: Ready to launch using Docker and `docker-compose`.

---

## 🛠️ Architecture Overview

```
TravelGPT/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI endpoints & static UI serving
│   │   ├── config.py            # Environment configuration
│   │   ├── models/schemas.py    # Pydantic schemas
│   │   ├── services/
│   │   │   ├── agent.py         # AI Agent planner (Groq/OpenAI)
│   │   │   ├── rag.py           # ChromaDB vector retrieval & document chunking
│   │   │   ├── cost.py          # Cost calculator engine
│   │   │   └── pdf_generator.py # ReportLab PDF builder
│   │   └── data/                # Destination guides & policy documents
│   └── requirements.txt
├── frontend/
│   ├── index.html               # Modern Web App HTML
│   ├── css/style.css            # Dark glassmorphism design system
│   └── js/app.js                # Interactive UI & API integration
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .env.example
```

---

## 🚀 Quick Start (Local Execution)

### Prerequisites
- Python 3.10+
- pip

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/MANu13151/TravelGPT.git
cd TravelGPT
cp .env.example .env
```

### 2. Install Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run FastAPI Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at **`http://localhost:8000`**.

---

## 🐳 Docker Deployment

To launch the full application with Docker Compose:

```bash
docker-compose up --build -d
```
Access the application at **`http://localhost:8000`**.

---

## 📡 API Reference

- `POST /api/plan`: Build full itinerary using RAG context + AI agent.
- `POST /api/cost`: Calculate trip cost breakdown vs. target budget.
- `POST /api/export-pdf`: Stream downloadable ReportLab PDF.
- `GET /api/destinations`: List pre-indexed vector destinations.
- `GET /health`: System health status.

---

## 📄 License
MIT License.
