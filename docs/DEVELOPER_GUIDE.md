# BusinessHub AI - Developer Guide

This document serves as a comprehensive reference for onboarding, daily development, infrastructure management, and production deployments for the BusinessHub AI platform.

---

## 1. Beginner-Friendly Onboarding Document

Welcome to the BusinessHub AI team! This project is a modern web application consisting of a FastAPI backend (Python) and an Angular frontend (TypeScript).

### Prerequisites
Before you start, ensure you have the following installed on your machine:
- **Python 3.12+**
- **Node.js (v22+) & npm (v11+)**
- **Docker & Docker Compose**
- **Git**

### First-Time Setup
1. **Clone the repository:**
   ```bash
   # git clone <repo-url>
   # cd businesshub-ai
   ```

2. **Start Infrastructure (Database & Cache):**
   ```bash
   docker compose up -d db redis
   ```

3. **Backend Setup:**
   ```bash
   cd backend
   # create your virtual environment (e.g. using virtualenv or venv)
   # activate the environment
   pip install -r requirements.txt

   # Setup environment variables
   cp .env.example .env
   # Edit .env with your local database URL: postgresql+asyncpg://postgres:postgres@localhost:5432/app-db

   # Run database migrations
   alembic upgrade head
   ```

4. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Run the Application:**
   - **Backend:** In the `backend` folder, run `uvicorn app.main:app --reload --port 8000`
   - **Frontend:** In the `frontend` folder, run `npm start` (or `npx ng serve`)
   - **Background Workers:** In the `backend` folder, run `celery -A app.core.celery_app worker --loglevel=info`

You can now access the frontend at `http://localhost:4200` and the backend API docs at `http://localhost:8000/docs`.

---

## 2. Developer's Cheat Sheet

### Development & Maintenance
- **Frontend Code Generation:** `npx @angular/cli generate component features/my-new-component`
- **Backend Migrations:**
  - Generate a new migration: `alembic revision --autogenerate -m "Added new table"` (Ensure your model is imported in `backend/app/domain/models/__init__.py`)
  - Apply migrations: `alembic upgrade head`
  - Rollback migration: `alembic downgrade -1`
- **Frontend Build:** `npm run build` (Check bundle size warnings!)
- **Dependencies:**
  - Python: `pip freeze > requirements.txt`
  - Node: `npm install <package> --save`

### QA & Testing
- **Backend Unit Tests:** `cd backend && export PYTHONPATH=. && pytest -v`
- **Frontend Unit Tests (Headless):** `cd frontend && npx ng test --watch=false --browsers=ChromeHeadless`
- **Full Pyramid Test (E2E & Integrated):** `./run_pyramid_tests.sh` from the root directory.

### Support & Debugging
- **Clear Redis Cache (Local):** `docker exec -it businesshub-ai-redis-1 redis-cli flushall`
- **Check Backend Logs:** Look at the terminal running `uvicorn`.
- **RBAC Debugging:** Decode the JWT token in `localStorage` in your browser console to verify your `role` claim (`atob(localStorage.getItem('access_token').split('.')[1])`).

---

## 3. Infrastructure and Resource Management

The platform utilizes Postgres (with pgvector) for storage and Redis for caching/sessions/Celery brokering.

### Essential Commands
- **Start Services:** `docker compose up -d`
- **Stop Services:** `docker compose down`
- **View Database Logs:** `docker compose logs -f db`
- **View Redis Logs:** `docker compose logs -f redis`
- **Access PostgreSQL CLI:** `docker exec -it businesshub-ai-db-1 psql -U postgres -d app-db`

### Resource Limits (Soft-Lock Policy - BR-PLT-002)
- FREE tier organizations receive **100 AI credits** monthly.
- Attempting to bypass limits without sufficient credits will yield a `402 Payment Required` (ERR_BILLING_001).
- To manually bump a tenant's limits during testing, modify their record directly in the `organizations` table in PostgreSQL.

---

## 4. Stage/Production Deployment Checklist

### Pre-Deployment Checks
- [ ] **Tests Pass:** All backend tests (`pytest`) and frontend tests (`ng test`) pass successfully.
- [ ] **Linting & Formatting:** No linting errors or massive bundle size warnings.
- [ ] **Migrations Reversible:** Confirm `downgrade()` functions in new Alembic migrations use `op.drop_table()` in reverse dependency order.
- [ ] **Environment Variables:** Verify staging/prod `.env` files are populated (especially `DATABASE_URL`, `JWT_PRIVATE_KEY_PATH`, and secure secrets).
- [ ] **Build Artifacts:** Frontend compiles successfully (`npm run build --prod`).

### Deployment Execution
- [ ] **Database Backup:** Take a snapshot of the production database before migrating.
- [ ] **Migrate Database:** Run `alembic upgrade head` on the target database. *Note: If using pgvector, manually ensure `import pgvector` is in the generated migration script.*
- [ ] **Deploy Backend:** Restart the FastAPI and Celery worker services.
- [ ] **Deploy Frontend:** Sync the compiled `dist/` folder to your CDN or web server (e.g., S3, NGINX).
- [ ] **Cache Invalidation:** Clear any CDN edges if updating the frontend.

### Post-Deployment Verification
- [ ] **Health Check:** Hit `/api/v1/healthz` to verify database and Redis connectivity.
- [ ] **Login Flow:** Verify users can log in and session states persist.
- [ ] **Background Tasks:** Verify Celery workers are picking up jobs (e.g., AI Quiz Generation).
