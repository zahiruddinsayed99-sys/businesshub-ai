# Automated Testing & API Integration Guide

This document provides explicit instructions for executing automated tests and details the major API data contracts for the core workflows in the BusinessHub AI platform.

---

## Section 1: Automated Testing Execution Guide

### Backend (Pytest)

The backend uses Pytest with AsyncIO support. Tests are located in `backend/tests/`. Ensure you have an active PostgreSQL database and Redis server running.

**1. Database Setup & Environment Initialization**
```bash
cd backend
# Use the global Python environment or an existing virtual environment
source .venv/bin/activate
pip install -r requirements.txt

# Export required environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-test-db"
export REDIS_URL="redis://localhost:6379/1"
export PYTHONPATH=.

# Initialize the test database schema using Alembic
alembic upgrade head
```

**2. Running the Full Test Suite**
```bash
pytest -v
```

**3. Running Tests for a Specific Module**
You can filter tests by module directory or filename:
```bash
# Run only Billing module tests
pytest tests/test_billing_integration.py -v

# Run only Core/Auth tests
pytest tests/test_auth.py -v
```

**4. Generating Coverage Reports**
```bash
# Run tests with coverage output
pytest --cov=app --cov-report=term-missing --cov-report=html -v

# Open the HTML report
open htmlcov/index.html
```

### Frontend (Angular)

The frontend uses Angular CLI, Jasmine, and Karma for unit testing.

**1. Running Jasmine/Karma Unit Tests (Headless)**
To avoid X11 display errors in headless environments (like sandboxes or CI/CD):
```bash
cd frontend
npm install
npx ng test --watch=false --browsers=ChromeHeadless
```

**2. Running End-to-End (E2E) Tests**
The platform uses Playwright for frontend UI verification. Make sure the backend and frontend servers are running locally (`ng serve` on `http://127.0.0.1:4200`).
```bash
# Install Playwright browsers (first time)
npx playwright install chromium

# Run the Playwright scripts (usually located in an e2e directory or via custom Python scripts)
pytest e2e/ -v  # Or run specific Playwright python scripts
```

---

## Section 2: Major API Endpoints & Data Contracts

Base URL: `http://localhost:8000/api/v1`

### Module 0: Core Platform Foundation

#### `POST /auth/onboard`
* **Authentication/RBAC:** None (Public)
* **Parameters:** None
* **Request Body:**
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "email": "admin@acme.com",
  "password": "SecurePassword123!",
  "full_name": "Alice Admin"
}
```
* **Sample Success Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "organization_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "987fcdeb-51a2-43d7-9012-345678901234",
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 900
  }
}
```

#### `POST /auth/login`
* **Authentication/RBAC:** None (Public)
* **Parameters:** None
* **Request Body:**
```json
{
  "email": "admin@acme.com",
  "password": "SecurePassword123!"
}
```
* **Sample Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Module 1: Billing & Indian Market Compliance

#### `POST /billing/checkout`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC scope: `tenant:billing`.
* **Parameters:** None
* **Request Body:** None
* **Sample Success Response (200 OK):**
```json
{
  "url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4..."
}
```
* **Sample Error Response (402 Payment Required - Soft Lock):**
```json
{
  "code": "ERR_BILLING_001",
  "detail": "Organization is soft-locked due to user overage on FREE tier."
}
```

### Module 2: CRM Engine

#### `POST /crm/deals`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC scope: `crm:write`.
* **Parameters:** None
* **Request Body:**
```json
{
  "title": "Enterprise Software License",
  "value_amount": 15000.50,
  "currency": "USD",
  "stage": "LEAD"
}
```
* **Sample Success Response (201 Created):**
```json
{
  "id": "abc12345-6789-0123-4567-89abcdef0123",
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Enterprise Software License",
  "value_amount": 15000.50,
  "currency": "USD",
  "stage": "LEAD",
  "created_at": "2023-10-27T10:00:00Z",
  "updated_at": "2023-10-27T10:00:00Z"
}
```

### Module 5: Centralised AI Platform & RAG

#### `POST /ai/documents/upload`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC scope: `ai:write`.
* **Parameters:** None
* **Request Body:**
```json
{
  "title": "Sales Playbook 2024",
  "content": "# Executive Summary\n\nThis playbook outlines the strategies for Q1 2024..."
}
```
* **Sample Success Response (202 Accepted):**
```json
{
  "job_id": "celery-task-id-987654321",
  "document_id": "def45678-9012-3456-7890-abcdef123456"
}
```

#### `POST /crm/deals/{deal_id}/ai-score`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC scope: `crm:write`.
* **Parameters:**
  - Path: `deal_id` (UUID)
* **Request Body:** None
* **Sample Success Response (202 Accepted):**
```json
{
  "job_id": "celery-task-id-11223344",
  "deal_id": "abc12345-6789-0123-4567-89abcdef0123"
}
```

### Module 4: LMS

#### `POST /lms/courses`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC roles: `TENANT_OWNER`, `TENANT_ADMIN`, `LMS_MANAGER`.
* **Parameters:** None
* **Request Body:**
```json
{
  "title": "Advanced Sales Tactics",
  "description": "Learn to close enterprise deals faster."
}
```
* **Sample Success Response (201 Created):**
```json
{
  "id": "course-id-uuid-1111",
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Advanced Sales Tactics",
  "description": "Learn to close enterprise deals faster.",
  "status": "DRAFT",
  "created_at": "2023-10-27T12:00:00Z",
  "updated_at": "2023-10-27T12:00:00Z"
}
```
* **Sample Error Response (403 Forbidden - Insufficient Permissions):**
```json
{
  "code": "ERR_RBAC_001",
  "detail": "Insufficient permissions"
}
```

#### `POST /lms/quizzes/generate`
* **Authentication/RBAC:** `Bearer Token`, `X-Organization-Id` header required. RBAC roles: `TENANT_OWNER`, `TENANT_ADMIN`, `LMS_MANAGER`.
* **Parameters:** None
* **Request Body:**
```json
{
  "lesson_id": "lesson-id-uuid-2222"
}
```
* **Sample Success Response (202 Accepted):**
```json
{
  "status": "accepted",
  "job_id": "celery-task-id-quiz-gen"
}
```
