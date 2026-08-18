# BusinessHub AI - Developer's Cheat Sheet

A quick reference guide for day-to-day development, testing, and deployment tasks.

---

## 1. Docker & Infrastructure

The project relies on Docker Compose to run local services like PostgreSQL (with pgvector) and Redis.

```bash
# Start all infrastructure services in detached mode
docker compose up -d

# Start only the database and redis (commonly used when running app natively)
docker compose up -d db redis

# Stop all running containers and remove them
docker compose down

# Stop containers and destroy volumes (WARNING: This wipes your local DB data!)
docker compose down -v

# View logs for the database container in real-time
docker compose logs -f db

# Open an interactive psql shell inside the database container
docker compose exec db psql -U postgres -d app-db

# Open a redis-cli shell to check cache or session keys
docker compose exec redis redis-cli
```

---

## 2. Database & Alembic (Migrations)

Alembic manages our PostgreSQL schema.

### Alembic Commands

```bash
cd backend

# Ensure your virtual environment is active and DATABASE_URL is exported!
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-db"

# Apply all pending migrations to bring the DB to the latest state
alembic upgrade head

# Generate a new migration script based on changes in app/domain/models/
# NOTE: If using pgvector, you must manually add 'import pgvector' to the generated file!
alembic revision --autogenerate -m "Add new field to crm_deals"

# Rollback the last applied migration
alembic downgrade -1

# Show the current migration version of the database
alembic current
```

### Useful SQL Snippets (BusinessHub Specific)

```sql
-- Query 1: Verify row-level isolation (Get all users belonging to a specific tenant)
SELECT u.id, u.email, u.full_name, ur.role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
WHERE ur.organization_id = 'YOUR-ORG-UUID-HERE';

-- Query 2: Check AI credit balances and Soft-Lock status for an organization
SELECT id, name, subscription_tier, ai_credits_used, bonus_ai_credits,
       (100 + bonus_ai_credits - ai_credits_used) as remaining_credits
FROM organizations
WHERE slug = 'acme-corp';

-- Query 3: Find soft-deleted CRM deals for audit purposes
SELECT id, title, stage, deleted_at
FROM crm_deals
WHERE deleted_at IS NOT NULL;
```

---

## 3. Backend Development & Testing (Python/FastAPI/Celery)

### Setup & Running

```bash
cd backend

# Create and activate virtual environment (skip creation if using system python in docker)
# (Use virtualenv or python3 venv module)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI development server with hot-reloading on port 8000
uvicorn app.main:app --reload --port 8000

# Start a Celery worker for processing background AI and LMS tasks
celery -A app.core.celery_app worker --loglevel=info

# Start Celery Flower to monitor queues on http://localhost:5555
celery -A app.core.celery_app flower
```

### Testing (Pytest)

```bash
# Export PYTHONPATH so imports work correctly from the backend root
export PYTHONPATH=.
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-test-db"

# Run the entire test suite
pytest -v

# Run a specific test file (e.g., Billing integration tests)
pytest tests/test_billing_integration.py -v

# Run the test suite and generate an HTML coverage report
pytest --cov=app --cov-report=html -v
```

---

## 4. Frontend Development (Angular & NPM)

### Setup & Running

```bash
cd frontend

# Install Node.js dependencies
npm install

# Clear the npm cache if you run into weird dependency errors
npm cache clean --force

# Serve the Angular application locally with hot-reloading (runs on http://localhost:4200)
npx ng serve

# Build the application for production (outputs to /dist folder)
npx ng build --configuration production
```

### Testing & Code Generation

```bash
# Run Karma/Jasmine unit tests in Chrome Headless mode (required for CI/CD or sandboxes without display)
npx ng test --watch=false --browsers=ChromeHeadless

# Generate a new component named 'billing-dashboard' in the features folder
npx ng generate component features/billing-dashboard

# Generate a new service named 'auth' in the core/services folder
npx ng generate service core/services/auth
```

---

## 5. Git & Branching Workflow

Follow standard Git workflows, ensuring commit messages use Conventional Commits (e.g., `feat: ...`, `fix: ...`, `docs: ...`).

```bash
# Ensure you are on the develop branch and have the latest changes
git checkout develop
git fetch origin
# Pull latest changes with rebase
git pull --rebase origin develop

git reset --hard origin/develop

# Create a new feature branch from develop
git checkout -b feat/add-new-crm-model

# ... make your code changes ...

# Add files and commit using Conventional Commits format
git add .
git commit -m "feat(crm): add expected_close_date field to Deal model"

# If conflicts occur during rebase, resolve them in your editor, then:
# git add <resolved-files>
# git rebase --continue

# Push your feature branch to the remote repository
# (e.g., 'git push' to your remote)

# Open a PR (Draft) targeting the 'develop' branch.
```
