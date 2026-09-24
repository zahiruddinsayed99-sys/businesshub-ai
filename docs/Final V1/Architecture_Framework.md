# Architecture Framework

## High-Level Topology

BusinessHub AI operates on a modern, decoupled client-server architecture distributed across multiple platforms:

1.  **Frontend Presentation Layer (Vercel)**
    *   Hosted purely on Vercel's global CDN.
    *   Single Page Application (SPA) compiled via Angular 19.
    *   Communicates strictly over HTTPS via RESTful JSON APIs.
2.  **API Application Layer (Render)**
    *   A state-less containerized Python environment running FastAPI + Uvicorn ASGI.
    *   Handles all business logic, RBAC validation, Stripe interactions, and Gemini API inference.
    *   Internal tasks are queued and managed via FastAPI BackgroundTasks and Redis locks (no Celery worker).
3.  **Data Persistence Layer (Supabase/Managed Postgres)**
    *   Relational and Vector data storage.
    *   Maintains isolation utilizing UUIDs as Foreign Keys across models pointing back to an `Organization` record.
4.  **Ephemeral Data Layer (Render/Managed Redis)**
    *   Handles active session validity tracking, webhook concurrency locking, and rate limiting primitive states.

## Data Flow Pipelines

### 1. RAG Sync & Query Pipeline
1.  **Upload:** User sends a Markdown/Text document via Frontend to Backend `/upload`.
2.  **Job Creation:** Backend writes document metadata and immediately creates an `AiJob` status record set to `PENDING`. Returns `job_id` to client.
3.  **Background Async:** `process_document_embeddings` task triggers.
    *   Acquires a Redis lock for the document ID.
    *   Calls Gemini API `text-embedding-004` to receive a 1536-dim vector array.
    *   Writes vector array into `organization_documents.embedding` column.
    *   Updates `AiJob` to `SUCCESS`.
4.  **Query:** User opens Chat UI and sends question.
5.  **Retrieval:** Backend pulls text context from `organization_documents` strictly where `organization_id == Context`.
6.  **Inference:** Backend feeds context + question to Gemini (`gemini-2.0-flash`). Returns synthesized markdown string to the UI.

### 2. CRM State Management
1.  **Read:** Angular UI requests Kanban boards via `/api/v1/crm/deals`. Token scopes + Tenant Headers validate identity.
2.  **Verification:** Database queries strictly append `.where(CrmDeal.organization_id == Context.org_id)`. If user is a Domain Member, it also appends `.where(CrmDeal.owner_user_id == Token.user_id)`.
3.  **Sync:** UI drag-and-drop operations trigger `PATCH` requests updating `stage`.

## Security Perimeter
*   **JWT Handshake:** All requests (except public endpoints like Onboarding/Login/Webhook) require a Bearer token signed via RS256.
*   **IDOR Prevention:** Implicit injection of Tenant constraints (`TenantContext`) guarantees no data leaks between organizational workspaces, even if UUIDs are guessed.
