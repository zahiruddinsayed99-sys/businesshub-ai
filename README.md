# BusinessHub AI

BusinessHub AI is a production-ready, multi-tenant B2B SaaS platform designed specifically for the Indian market. Built on a "Modular Monolith" architecture (ADR-001) using Clean Architecture principles, it provides a centralized AI pipeline, a CRM engine, a Learning Management System (LMS), and a fully RBI/GST-compliant billing infrastructure.

---

## 🏗 Architecture & Tech Stack

The platform enforces strict Domain → Application → Infrastructure → API decoupling, ensuring a highly secure, tenant-isolated environment.

*   **Backend Framework:** Python, FastAPI, Pydantic v2
*   **Frontend Framework:** Angular (featuring RxJS polling for real-time background job updates)[cite: 1]
*   **Database:** PostgreSQL 15+ (with `pgvector` for AI embeddings)
*   **ORM:** SQLAlchemy 2.0 (Alembic for migrations)
*   **Caching & Queue:** Redis, Celery (Async task orchestration)
*   **Storage:** S3/Cloudflare R2 (Tenant-isolated bucket layout)
*   **Authentication:** RS256 Asymmetric Cryptosystem (2048-bit RSA keys), Stateful Redis sessions
*   **Payments:** Stripe SDK (RBI e-Mandate / 3DS compliant)

---

## 📦 Core Modules

### Module 0: Core Platform Foundation
The bedrock of the application handling security and multi-tenancy.
*   **Row-Level Isolation:** Every database transaction is mathematically scoped via `organization_id` using FastAPI ContextVars.
*   **Session Management:** Stateful Redis tracking (`sess:{user_id}:{token_id}`) with instant revocation and 15-minute HTTP-only cookie rotation.
*   **RBAC:** Redis-cached Role-Based Access Control (`org:{org_id}:usr:{user_id}:perms`).

### Module 1: Billing & Indian Market Compliance
Purpose-built fiscal architecture for Indian SaaS operations.
*   **GST & RBI Compliance:** Automated 18% GST calculation (CGST/SGST/IGST) and 3D Secure (3DS) challenge support for INR recurring payments.
*   **Atomic Metering:** `UPDATE ... RETURNING` SQL pattern prevents AI credit leakage during high-concurrency requests.
*   **Idempotency:** 3-State Redis Lock protocol (`stripe_evt:{event_id}`) ensures Stripe webhooks are processed exactly once.

### Module 2: CRM Engine & Sales Operations
The operational core for the B2B user journey.
*   **Kanban Pipeline:** Thin controllers mapping to `crm_deals` and `crm_contacts`.
*   **AI Lead Scoring:** Async Celery background tasks (`crm.calculate_lead_score`) analyze contact interactions to generate 0-100 intent signals.

### Module 4: Learning Management System (LMS)
A comprehensive educational engine utilizing the centralized AI pipeline.
*   **Course Authoring & RBAC:** Secure course creation restricted to `TENANT_OWNER` and `LMS_MANAGER` roles, heavily guarded by tenant isolation logic[cite: 1].
*   **Learner Progression:** Automated state transitions track lesson progress; completing the final required lesson automatically updates the `CourseEnrollment` record to `COMPLETED`[cite: 1].
*   **Quiz Scoring System:** Built-in evaluation engine that verifies attempt responses, requiring a score of >= 80% to achieve a "passed" state[cite: 1].
*   **AI Quiz Generation:** Authorized users can generate quizzes from markdown lessons; Celery workers parse the content, ping the `AiGatewayService`, and persist the questions[cite: 1].
*   **Billing Guard:** Seamless integration with Module 1 ensures that if a tenant exhausts their AI credits, the system halts generation and immediately returns a `402 Payment Required` (`ERR_BILLING_001`) error[cite: 1].

### Module 5: Centralised AI & RAG Services
A cross-cutting AI platform serving all downstream modules.
*   **Tenant-Isolated Knowledge:** Embedded vectors are strictly tagged with `organization_id` in `pgvector`.
*   **Async Processing:** Heavy PDF/Markdown chunking and embedding generation are offloaded to Celery workers to maintain API event loop integrity.

---

## 🛠 Engineering Standards & Contracts

To prevent architectural drift and maintain system integrity, all contributions must adhere to the following strict standards:

### Database & Modeling
*   **Naming Conventions:** All tables use `plural_snake_case`. Primary keys are strictly UUID v4.
*   **Relational Mappings:** Mandatory `{singular_table_name}_id` for all foreign keys (e.g., `organization_id`).
*   **Data Preservation (BR-PLT-003):** Hard deletes are strictly forbidden. All entities use `deleted_at` timestamps (Soft Delete pattern).

### System Policies
*   **Soft-Lock Overage Policy (BR-PLT-002):** If a tenant exceeds seat limits, the system enforces a "Soft-Lock," instantly freezing write operations and invites until the account is upgraded.

### Error Code Catalog

| Error Code | HTTP | Trigger Condition |
| :--- | :--- | :--- |
| `ERR_AUTH_001` | 401 | Missing/invalid JWT. Client must re-authenticate. |
| `ERR_TENANT_001`| 403 | Cross-tenant access attempt detected. |
| `ERR_RBAC_001` | 403 | Missing required permission scope. |
| `ERR_VALIDATION_001`| 422| Pydantic v2 schema validation failure. |
| `ERR_BILLING_001` | 402 | Subscription or AI credit limit breached. |
| `ERR_RATE_LIMIT_001`| 429 | Redis rate limiter threshold hit. |
| `ERR_NOT_FOUND_001` | 404 | Entity missing, invalid UUID, or soft-deleted. |

---

## 🚀 Getting Started (Local Development)

### Prerequisites
*   Python 3.10+
*   Node.js & npm (for Angular frontend)[cite: 1]
*   Docker & Docker Compose (for Postgres, pgvector, and Redis)
*   Stripe Test API Keys

### Backend Setup

1.  **Environment Configuration:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-db"
    ```

2.  **Start Infrastructure & Apply Migrations:**
    ```bash
    docker compose up -d db redis
    alembic upgrade head
    ```

3.  **Start Services:**
    ```bash
    # Terminal 1: API Server
    uvicorn app.main:app --reload --port 8000
    
    # Terminal 2: Celery Worker
    celery -A app.core.celery_app worker --loglevel=info
    ```

### Frontend Setup

1.  **Install & Run Angular App:**
    ```bash
    cd frontend
    npm install
    npx ng serve
    ```
    Access the Learner Dashboard at `http://localhost:4200/lms-learner` and the Author Dashboard at `http://localhost:4200/lms-author`[cite: 1].

---

## 🗺 Roadmap

| Phase | Modules | Status |
| :--- | :--- | :--- |
| **Phase 1** | Core, Billing, CRM, LMS (Module 4), AI Engine | Completed |
| **Phase 2** | Platform Optimization & Load Testing | Planned |
| **Phase 3** | E-Commerce & Inventory Management (Module 3) | Backlogged |
