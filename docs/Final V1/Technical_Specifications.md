# Technical Specifications

## Architecture Overview
BusinessHub AI uses a modern, lightweight async Python backend tightly coupled with an Angular 19 Standalone frontend.

## Backend Details (FastAPI + Async SQLAlchemy)

### Clean Architecture
- `app/api/`: Presentation layer (FastAPI routers).
- `app/core/`: Application plumbing (Config, DB session generation, Redis, Security, Middleware).
- `app/domain/models/`: SQLAlchemy 2.0 ORM mappings using declarative base.
- `app/tasks/`: Asynchronous operations utilizing FastAPI `BackgroundTasks` instead of Celery.

### Database & `pgvector`
- **PostgreSQL 16:** Primary operational data store.
- **Asyncpg:** Utilized alongside SQLAlchemy's `async_sessionmaker` (`poolclass=NullPool` recommended during testing to prevent leaks).
- **Pgvector Extension:** The `organization_documents` table stores context for RAG. Vector columns are defined as `Vector(1536)`. Migrations specifically require `import pgvector` explicitly added manually to Alembic files to parse `Vector` type correctly.
- **Tenant Isolation:** Centralized in database relationships via foreign keys tightly bound to an `organization_id`. `TenantContext` dependency automatically restricts DB read/writes.

### Asynchronous Task Management (No Celery)
- Celery has been intentionally removed from this application footprint.
- Short/medium-lived async operations (Document embedding parsing, Quiz generation) are processed using FastAPI `BackgroundTasks` coupled with Redis distributed locks to prevent duplicate concurrent runs.
- **State Tracking:** An `AiJob` database model tracks the status of async operations (`PENDING`, `SUCCESS`, `FAILURE`) which the client can poll via `/api/v1/ai/jobs/{job_id}`.

### Caching and State (Redis)
- Used natively via `redis.asyncio`.
- Handles session state (tracking active JWT token TTLs).
- Implements Stripe webhook debouncing and lock primitives (`SET NX EX`).

### Security, Auth, and CORS
- **Authentication:** Asymmetric RSA Keys (`RS256`). Temporary keys generated on startup if PEM paths are missing.
- **Middleware Check:** RBAC and tenant resolution are injected per-route via `RequiresPermission` dependencies checking JWT claims and `X-Organization-Id` headers.
- **CORS:** Managed via `CORSMiddleware`. Vercel Production (`https://businesshub-ai-five.vercel.app`) and Localhost angular dev instances (`http://localhost:4200`, `http://127.0.0.1:4200`) are strictly defined.
- **Custom Exceptions:** Pydantic `RequestValidationError` and FastAPI `HTTPException` are intercepted in `main.py` and rewritten into standardized JSON payloads containing domain-specific `code` and `detail` fields (e.g. `ERR_VALIDATION_001`).

## Frontend Specifics (Angular)
- Standalone component structure without NgModules.
- Signals (`signal()`, `computed()`) replace RxJS subjects for synchronous state where appropriate.
- Theme isolation uses a global default Light theme with scoped `.auth-container` classes for the Dark-themed Onboarding/Login.
- `marked` and `dompurify` libraries sanitize and parse markdown returned from Gemini LMS features to avoid XSS.

## Third-Party Integrations
- **Stripe:** Used for `PRO` subscriptions. Webhooks map back to update `organization.subscription_tier`.
- **Gemini (`google-genai`):** Used extensively for AI vectorization (`text-embedding-004`) and generation (`gemini-2.0-flash`).
