# Functional & Technical Map

This document bridges business requirements to the exact technical paths in the codebase.

| Functional Feature | FastAPI Backend Route | Database Models | Core Services / BackgroundTasks | Angular Frontend Context |
|---|---|---|---|---|
| **User/Tenant Registration** | `POST /api/v1/auth/onboard`<br>`POST /api/v1/tenants/onboard` | `User`, `Organization`, `UserRole` | Password hashing, JWT RSA creation | Auth routes (Dark Theme scoped) |
| **RBAC / Auth Validation** | Global Depends on Route definitions | `UserRole` (cached in Redis/JWT) | `app.core.rbac.RequiresPermission` | Route Guards checking JWT claims in `localStorage` |
| **Billing / Subscription Upgrades** | `POST /api/v1/billing/checkout`<br>`POST /api/v1/billing/webhooks` | `Organization` (`subscription_tier`, `stripe_customer_id`) | `stripe` Python SDK, Redis Lock for webhooks | Billing Settings UI |
| **CRM Contact Management** | `GET/POST /api/v1/crm/contacts` | `Contact` | SQLAlchemy `select()`, Tenant isolation | CRM List View |
| **CRM Deal Stages** | `GET/POST /api/v1/crm/deals` | `CrmDeal` | Validates token `user_id` against `owner_user_id` | Drag-and-drop Kanban (Angular CDK) |
| **LMS Authoring (Courses)** | `CRUD /api/v1/lms/courses` | `Course`, `Lesson` | Direct SQLAlchemy async operations | LMS Authoring Module |
| **LMS Learner Catalog** | `GET /api/v1/lms/catalog` | `Course`, `Lesson` | Strict read-only isolation, markdown sanitization | LMS Learner Dashboard (`marked`, `dompurify`) |
| **AI Quiz Generation** | `POST /api/v1/lms/lessons/{id}/quiz` | `Quiz`, `QuizQuestion`, `AiJob` | `generate_ai_quiz` in `app/tasks/ai_tasks.py` (Gemini API) | Lesson view -> Launch Quiz |
| **RAG Document Ingestion** | `POST /api/v1/ai/documents/upload` | `OrganizationDocument`, `AiJob` | `process_document_embeddings` in `app/tasks/ai_tasks.py` | Settings/AI Context Dashboard |
| **RAG Interactive Chat** | `POST /api/v1/ai/chat` | `OrganizationDocument` (Vector read) | `AiGatewayService` RAG prompting (Gemini) | Floating Chat Widget / Dashboard |
| **Task Status Polling** | `GET /api/v1/ai/jobs/{id}` | `AiJob` | Native Postgres Read | Frontend `setInterval` polling job ID |
