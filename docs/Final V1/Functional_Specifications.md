# Functional Specifications

## Project Scope & Overview

BusinessHub AI is an enterprise multi-tenant SaaS application that unifies core business workflows. Core functionalities include:
1. **Module 0: Core Foundation & Auth** - Tenant-based architecture, RBAC, workspace isolation.
2. **Module 1: Billing & Compliance** - Stripe integration, Pro vs. Free tier enforcement, soft-lock overage policy.
3. **Module 2: CRM Engine** - Deal and Contact management, AI lead scoring.
4. **Module 4: LMS (Learning Management System)** - Course/Lesson authoring, AI-generated quizzes (80% passing grade logic).
5. **Module 5: RAG & Centralized AI** - Document ingestion, async embedding vectorization, RAG-powered chatbot.

## Detailed Features

### 1. Workspace Onboarding & Tenant Management
- **Self-Service Flow:** Public users can onboard themselves creating a single Tenant Owner.
- **Super Admin Flow:** Internal users can onboard tenants (creating an Admin and a Domain Member user simultaneously).
- **Workspace Isolation:** All tenant data is strictly partitioned via `organization_id` injected through headers.

### 2. CRM Deals & Stages
- **Contact Management:** Standard CRUD for leads, associated heavily with RBAC (`crm:read`, `crm:write`, `crm:delete`).
- **Deals:** Represent potential revenue. Stages default to `LEAD`.
- **Domain Member Constraints:** Deal modification for standard users strictly verifies the deal's `owner_user_id` against the authenticated token.
- **AI Additions:** Lead score calculation, AI intent signals.

### 3. Learning Management System (LMS)
- **Authoring vs. Learner APIs:** Strictly separated API routes (`/courses` vs `/catalog`) to avoid RBAC collisions.
- **AI Quizzes:** Lessons can have AI-generated quizzes created asynchronously.
- **Passing Grades:** Business rule `BR-LMS-001` dictates learners must achieve an 80% minimum score.

### 4. RAG Chat & Document Ingestion
- **Document Ingestion:** Users upload text/documents. Background tasks generate embeddings via Gemini and store them in PostgreSQL `pgvector`.
- **RAG Chat:** Interactive chat queries context from ingested documents.

### 5. Billing & Subscription Management
- **Stripe Checkout & Portal:** Integration to manage payments.
- **Tier Enforcement:** `FREE` tier allows up to 100 AI credits/month. Exceeding triggers a 402 error (`ERR_BILLING_001`).
- **Soft-Lock Policy:** Non-compliant users lose write operations while keeping read access (`BR-PLT-002`).

---

## Role-Wise Process Flow Breakdown

### Tenant Owner / Admin User
- **Login/Onboarding:** Signs up, receives a tenant isolated workspace.
- **Billing:** Connects Stripe, upgrades to `PRO` tier to bypass credit limits.
- **User Management:** Can invite Domain Members.
- **CRM Management:** Full view and write access across all deals within the organization.
- **LMS Authoring:** Can create courses, lessons, and trigger AI quiz generation.
- **AI Settings:** Ingests context documents for the workspace AI chatbot.

### Domain Member (Standard User)
- **CRM Operations:** Can view organizational contacts but can only edit Deals where they are assigned as the `owner_user_id`.
- **LMS Learning:** Accesses the course catalog, reads lessons, takes AI quizzes (must pass with 80%).
- **AI Chat:** Interacts with the RAG chat using the organization's ingested knowledgebase.

### System Processes (Async BackgroundTasks)
- **Document Vectorization:** Upon document upload, a FastAPI background task takes the text, calls Gemini for 1536-dim embeddings, and stores it in `pgvector`.
- **Quiz Generation:** On AI Quiz trigger, a background task sends lesson content to Gemini to extract questions and answers, storing them atomically.
- **Stripe Webhooks:** Asynchronously listens to `customer.subscription.updated/deleted` via Redis-locked webhooks to sync tier status (`PRO` vs `FREE`) to the `Organization` DB model.
