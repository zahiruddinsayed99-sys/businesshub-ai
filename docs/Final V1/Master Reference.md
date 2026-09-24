Here is your consolidated master guide, featuring the indexed index of all 7 underlying documents and their specific operational purposes for your quick reference and interview prep:

---

# BusinessHub AI — Master Reference & Interview Guide

*Enterprise Multi-Tenant AI Platform: Architecture, Specs, and Operations*

## Document Index & Purpose

Use this index as your roadmap to navigate and dive deeper into any specific technical or functional aspect of the platform:

1. **`README.md`**

* **Purpose:** High-level project overview, tech stack highlights, local development prerequisites, and environment setup instructions across Supabase, Render, and Vercel.


2. **`Functional_Specifications.md`**

* **Purpose:** Comprehensive functional scope defining user features across all modules (Auth, Billing, CRM, LMS, RAG) and detailed role-wise process flows at the end.


3. **`Technical_Specifications.md`**

* **Purpose:** Deep dive into the backend architecture, asynchronous task handling (`BackgroundTasks` + Redis), `pgvector` database configurations, security (RSA JWT), and CORS rules.


4. **`Functional_Technical_Map.md`**

* **Purpose:** A cross-reference matrix mapping business features directly to their corresponding FastAPI routes, database models, backend services, and Angular frontend views.


5. **`Architecture_Framework.md`**

* **Purpose:** High-level topology, cloud deployment architecture (Vercel, Render, Supabase), data flow pipelines (RAG sync, CRM state management), and security perimeters.


6. **`RUNBOOK.md`**

* **Purpose:** Day-2 operations guide covering Alembic database migration rollbacks, monitoring/logging best practices, disaster recovery steps, and secret management.


7. **`API_DOCUMENTATION.md`**

* **Purpose:** Detailed API contract reference covering mandatory multi-tenant headers (`X-Organization-Id`), endpoint specifications, error payloads, and Stripe webhook handlers.



---

## 1. Executive Summary & Tech Stack

BusinessHub AI is an enterprise-grade, multi-tenant SaaS platform that unifies workspace management, CRM workflows, an AI-powered Learning Management System (LMS), and Retrieval-Augmented Generation (RAG) chat into a single seamless experience.

* **Frontend:** Angular 19 (Standalone components, Signals, Tailwind/Dark-scoped UI) deployed on **Vercel**.


* **Backend API:** FastAPI (Python 3.11, Async SQLAlchemy 2.0) deployed on **Render**.


* **Database & Vector Search:** Supabase PostgreSQL 16 with the `pgvector` extension for 1536-dimensional embeddings.


* **Task Queue & Caching:** FastAPI `BackgroundTasks` + **Render Redis** (handling distributed locks, rate-limiting primitives, and webhooks).


* **AI Engine:** Google Gemini SDK (`google-genai`) using `text-embedding-004` and `gemini-2.0-flash`.



---

## 2. Core Functional Modules

* **Core Foundation & Auth:** Multi-tenant workspace isolation, Role-Based Access Control (RBAC), and asymmetric RSA JWT authentication (`RS256`).


* **Billing & Compliance:** Stripe subscription integration supporting Pro vs. Free tier enforcement (e.g., 100 AI credits/month limit) and soft-lock overage policies (`BR-PLT-002`).


* **CRM Engine:** Lead and contact management, Kanban stage tracking (`LEAD`), and smart lead scoring.


* **Learning Management System (LMS):** Separated authoring and learner endpoints (`/courses` vs `/catalog`), AI-generated quizzes, and mandatory 80% passing grade logic (`BR-LMS-001`).


* **RAG & Centralized AI:** Document text ingestion, asynchronous vectorization, and interactive context-aware chatbot.



---

## 3. System Architecture & Data Flow

```
[ Angular SPA (Vercel) ] -- HTTPS / REST --> [ FastAPI Backend (Render) ]
                                                    |
                   +--------------------------------+--------------------------------+
                   | (Async SQLAlchemy + pgvector)                                   | (Asyncio Redis)
                   v                                                                 v
     [ Supabase PostgreSQL 16 ]                                            [ Render Redis Cache ]

```

### Key Data Flow Pipelines:

1. **RAG Ingestion Pipeline:** User uploads text $\rightarrow$ FastAPI creates an `AiJob` (`PENDING`) $\rightarrow$ Background task acquires a Redis lock $\rightarrow$ Calls Gemini (`text-embedding-004`) for 1536-dim vector arrays $\rightarrow$ Stores in PostgreSQL `pgvector` $\rightarrow$ Marks job `SUCCESS`.


2. **Multi-Tenant Security Enforcement:** Every request (excluding public onboarding/webhooks) requires `Authorization: Bearer <token>` and `X-Organization-Id` headers, intercepted by a `TenantContext` middleware that strictly scopes all database queries to the active organization.



---

## 4. Technical Implementation Highlights

* **Why No Celery?** The platform intentionally avoids Celery complexity, utilizing FastAPI's native `BackgroundTasks` coupled with Redis distributed locks (`SET NX EX`) to safely execute short-to-medium async tasks like quiz generation and embedding synchronization.


* **Database & Vector Mapping:** SQLAlchemy models interact via `async_sessionmaker` and `asyncpg`. Vector columns utilize `Vector(1536)` explicitly requiring `import pgvector` inside Alembic migration scripts.


* **Global Error Handling:** Pydantic validation errors and HTTP exceptions are caught globally in `main.py` and mapped to uniform custom error payloads (e.g., `ERR_VALIDATION_001`, `ERR_BILLING_001`).



---

## 5. Role-Wise Process Flows

* **Tenant Owner / Admin:** Full organizational control. Signs up via self-service or super-admin onboarding, connects Stripe to upgrade tiers, invites users, manages CRM deals globally, and handles AI document knowledgebases.


* **Domain Member (Standard User):** Restricted workspace access. Views organization contacts but can only modify CRM deals explicitly assigned to their `owner_user_id`. Interacts with the LMS course catalog, takes AI quizzes, and utilizes RAG chat.


* **System Processes:** Automated background routines handling vector embedding generation, atomic AI quiz extraction, and asynchronous Stripe webhook subscription syncing.



---

## 6. Operations Runbook & Maintenance (Day-2)

* **Alembic Migrations:** Run `alembic upgrade head` to apply updates. All `downgrade()` routines must be strictly reversible and tested locally on clean trial databases to avoid schema lockups.


* **Monitoring & Logs:** Uses `structlog` for structured JSON logs captured on Render. Health checks are exposed via `/api/v1/healthz`.


* **Disaster Recovery:** Supabase Point-in-Time Recovery (PITR) handles database rollbacks. Redis is treated as ephemeral (session invalidation on restart).


* **Free Plan Maintenance:** Zero manual shut-down required across Vercel (serverless), Render (auto-spin-down free tier), and Supabase (auto-pauses after 7 days of total inactivity).

---

## 7. API Reference Quick-Glance

* **Base URL:** `[https://businesshub-ai.onrender.com/api/v1](https://businesshub-ai.onrender.com/api/v1)` (or `http://localhost:8000/api/v1` locally).


* **Mandatory Headers:** `Authorization: Bearer <token>`, `X-Organization-Id: <uuid>`.


* **Core Endpoints:**
* `POST /auth/login` — Authenticates user via JSON payload (`email`, `password`).


* `POST /auth/onboard` — Public self-service workspace creation.


* `POST /ai/documents/upload` — Ingests text context, returns an asynchronous `AiJob` ID.


* `GET /api/v1/ai/jobs/{job_id}` — Polling route for async job states (`PENDING`, `SUCCESS`, `FAILURE`).


* `POST /billing/webhooks` — Secures Stripe subscription updates via `Stripe-Signature` verification.





---