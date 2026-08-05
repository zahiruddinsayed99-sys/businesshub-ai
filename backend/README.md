# BusinessHub AI - Backend Service

FastAPI backend service built using Python 3.12+, Async SQLAlchemy 2.0, Pydantic v2, PostgreSQL 16 + pgvector, Redis, Celery, and Structlog following Clean Architecture principles.

## Prerequisites

- Python 3.12+
- PostgreSQL 16 with `pgvector` extension
- Redis 7

## Getting Started

### 1. Create Virtual Environment

Create and activate a Python 3.12 virtual environment inside the `backend` directory:

```bash
cd backend
python -m venv .venv

# On Linux / WSL / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

Install the production and development dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration

Ensure the root `.env` file exists at the repository root (`../.env`). Key configuration parameters including Database, Redis, and MinIO connections will automatically be parsed by `pydantic-settings`.

### 4. Run Development Server

Start the FastAPI ASGI development server with auto-reload:

```bash
uvicorn app.main:app --reload
```

The service will be accessible at:
- **API Base URL**: `http://localhost:8000/api/v1`
- **Health Check**: `http://localhost:8000/api/v1/healthz`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

### 5. Running Tests

Run the Pytest suite:

```bash
pytest
```
