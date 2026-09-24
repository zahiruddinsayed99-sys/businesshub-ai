# BusinessHub AI

Enterprise Multi-Tenant SaaS Platform built with FastAPI, Angular, PostgreSQL, and AI.

## Architecture & Tech Stack

*   **Backend:** Python 3.12+, FastAPI, Async SQLAlchemy 2.0, Pydantic v2
*   **Database:** PostgreSQL 16 with `pgvector` extension for vector embeddings (Supabase ready)
*   **Migrations:** Alembic
*   **Caching & Tasks:** Redis 7 (used for session state, rate limiting, distributed locking, and FastAPI BackgroundTasks—Celery is removed)
*   **Frontend:** Angular 19 (Standalone Components, Signals, CDK)
*   **AI:** Gemini AI via `google-genai` SDK for RAG chat and Quiz generation
*   **Payment/Billing:** Stripe

## Environment Configuration

Copy `env.example` to `.env` in the repository root and configure it. Key parameters automatically map to Pydantic Settings in `backend/app/core/config.py`:

*   `DATABASE_URL`: e.g., `postgresql+asyncpg://postgres:postgres_dev_password_secure_123@localhost:5432/businesshub_db`
*   `REDIS_URL`: e.g., `redis://localhost:6379/0`
*   `JWT_PRIVATE_KEY_PATH` & `JWT_PUBLIC_KEY_PATH`: Paths to RSA key pair for JWT (auto-generated if missing)
*   `STRIPE_API_KEY` & `STRIPE_WEBHOOK_SECRET`
*   `GEMINI_API_KEY`: API key for Gemini RAG capabilities
*   `BACKEND_CORS_ORIGINS`: e.g., `["http://localhost:4200", "https://businesshub-ai-five.vercel.app"]`

## Local Development Setup

### 1. Infrastructure Services

Start PostgreSQL, Redis, and MinIO via Docker Compose:

```bash
docker-compose up -d
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```
*   **API Base:** `http://localhost:8000/api/v1`
*   **Swagger Docs:** `http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run start # or npx @angular/cli serve
```
*   **Angular App:** `http://localhost:4200`

## Production Deployment Guidelines

### Database (Supabase)
1. Provision a PostgreSQL 16+ instance.
2. Ensure the `vector` extension is enabled: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Connect the backend via `DATABASE_URL` (use `postgresql+asyncpg://...`).

### Backend (Render)
1. Configure a Web Service.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Define environment variables in the Render dashboard, particularly `DATABASE_URL`, `REDIS_URL`, and AI/Stripe keys. Ensure CORS origins include the Vercel frontend URL.

### Frontend (Vercel)
1. Connect Vercel to your repository focusing on the `frontend` directory.
2. Build command: `npm run build` or `ng build --configuration production`
3. Output directory: `dist/frontend/browser` (or as configured in `angular.json`).
4. Ensure environment variables in Vercel point to the Render backend URL.
