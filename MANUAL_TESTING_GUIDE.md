# End-to-End Manual Testing Guide - BusinessHub AI Platform

This guide provides explicit, step-by-step instructions for testing the core modules of the BusinessHub AI Platform. It is designed for manual testing teams.

## Module 0: Core Platform Foundation

### Setup & Prerequisites
* Base URL: `http://localhost:8000/api/v1`
* Tools: Postman, Swagger UI (`http://localhost:8000/docs`)
* No API keys are required for this module.

### Test Scenarios

#### TC-AUTH-001: Tenant Registration (Onboarding)
* **Objective:** Verify a new organization and admin user can be created.
* **Test Data:**
  * `name`: `Acme Corp`
  * `slug`: `acme-corp`
  * `email`: `admin@acme.com`
  * `password`: `SecurePass123!`
  * `full_name`: `Alice Admin`
* **Step-by-Step Actions:**
  1. Open Postman or Swagger.
  2. Make a `POST` request to `/auth/onboard`.
  3. Provide the Test Data in the JSON body.
* **Expected Result:**
  * HTTP 201 Created.
  * The response body contains `organization_id`, `user_id`, and `access_token`.
  * A `refresh_token` cookie is set (HttpOnly, SameSite=strict).

#### TC-AUTH-002: User Login
* **Objective:** Verify a user can authenticate and receive a JWT.
* **Test Data:**
  * `email`: `admin@acme.com`
  * `password`: `SecurePass123!`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/auth/login` with the Test Data.
* **Expected Result:**
  * HTTP 200 OK.
  * The response body contains `access_token`, `token_type` ("bearer"), and `expires_in` (900).
  * A `refresh_token` cookie is set.

#### TC-AUTH-003: Invite Team Member
* **Objective:** Verify tenant admins can invite new users.
* **Test Data:**
  * Context: Use the `access_token` and `organization_id` from TC-AUTH-001.
  * `email`: `member@acme.com`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/organizations/invitations`.
  2. Headers: `Authorization: Bearer <access_token>`, `X-Organization-Id: <organization_id>`.
  3. Body: `{"email": "member@acme.com"}`.
* **Expected Result:**
  * HTTP 200 OK.
  * The response contains a plaintext `token`. Save this `token`.

#### TC-AUTH-004: Accept Invitation
* **Objective:** Verify a user can accept an invite using a token.
* **Test Data:**
  * `token`: The token saved from TC-AUTH-003.
  * `full_name`: `Bob Member`
  * `password`: `MemberPass123!`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/auth/invite/accept`.
  2. Body: Provide the Test Data in JSON format.
* **Expected Result:**
  * HTTP 200 OK.
  * Response body: `{"status": "success", "message": "Invitation accepted"}`.

### Edge Cases & Negative Testing
* **Duplicate Slug:** Run TC-AUTH-001 again with the exact same data. Expect HTTP 409 Conflict with message "Organization slug already taken".
* **Duplicate Email:** Run TC-AUTH-001 with a different slug but the same email. Expect HTTP 409 Conflict with message "Email already registered".
* **Missing X-Organization-Id Header:** Run TC-AUTH-003 without the `X-Organization-Id` header. Expect HTTP 403 Forbidden with `ERR_TENANT_001` (Missing mandatory X-Organization-Id header).
* **Cross-Tenant Access (Row-Level Isolation):** Register a second tenant (Tenant B). Try to use Tenant B's access token to fetch Tenant A's details using Tenant A's `X-Organization-Id`. Expect HTTP 403 Forbidden (User is not a member of the specified organization).

---

## Module 1: Billing & Indian Market Compliance

### Setup & Prerequisites
* Base URL: `http://localhost:8000/api/v1`
* Requires a valid Tenant Context (Access Token + Organization ID).
* Ensure Stripe API keys are configured in the backend environment.

### Test Scenarios

#### TC-BIL-001: Create Stripe Checkout Session
* **Objective:** Verify generating a checkout session for PRO tier subscription.
* **Test Data:** N/A (Uses context organization).
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/billing/checkout`.
  2. Headers: `Authorization: Bearer <access_token>`, `X-Organization-Id: <organization_id>`.
* **Expected Result:**
  * HTTP 200 OK.
  * Response contains a `url` pointing to a Stripe Checkout page (e.g., `checkout.stripe.com/...`).
  * The checkout amount should be for INR 1000.

#### TC-BIL-002: Customer Portal Access
* **Objective:** Verify access to Stripe Customer Portal for active users.
* **Step-by-Step Actions:**
  1. First, complete a checkout or have a backend-assigned `stripe_customer_id` for the org.
  2. Make a `POST` request to `/billing/portal`.
  3. Headers: `Authorization: Bearer <access_token>`, `X-Organization-Id: <organization_id>`.
* **Expected Result:**
  * HTTP 200 OK.
  * Response contains a `url` pointing to the Stripe billing portal.

### Edge Cases & Negative Testing
* **Trigger ERR_BILLING_001 (Soft-Lock Overage):**
  1. Ensure the Organization is on the `FREE` tier (`subscription_tier = 'FREE'`).
  2. Use the invite endpoint (`/organizations/invitations`) and accept endpoint to add 3 more users (Total 4 users in the org).
  3. Attempt to create a CRM Deal (`POST /crm/deals`).
  4. Expect HTTP 402 Payment Required with code `ERR_BILLING_001` and message indicating soft-lock due to user overage.
* **Invalid Webhook Signature:**
  1. Send a `POST` request to `/billing/webhooks` with dummy JSON data.
  2. Provide a fake header: `Stripe-Signature: t=123,v1=fake_signature`.
  3. Expect HTTP 401 Unauthorized with "Invalid signature".

---

## Module 2: CRM Engine

### Setup & Prerequisites
* Base URL: `http://localhost:8000/api/v1`
* Valid Tenant Context required.
* Ensure organization is NOT soft-locked.

### Test Scenarios

#### TC-CRM-001: Create CRM Deal
* **Objective:** Verify creating a deal in the Kanban pipeline.
* **Test Data:**
  * `title`: `Big Enterprise Deal`
  * `value_amount`: `50000.00`
  * `currency`: `USD`
  * `stage`: `LEAD`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/crm/deals`.
  2. Headers: `Authorization`, `X-Organization-Id`.
  3. Body: Provide Test Data in JSON.
* **Expected Result:**
  * HTTP 201 Created.
  * Response contains the deal object with a generated `id` and `created_at`. Save this `id`.

#### TC-CRM-002: Update Deal Stage
* **Objective:** Verify a deal's stage can be moved (e.g., Kanban drag-and-drop simulation).
* **Test Data:**
  * `deal_id`: Saved from TC-CRM-001.
  * `stage`: `PROPOSAL`
* **Step-by-Step Actions:**
  1. Make a `PATCH` request to `/crm/deals/<deal_id>/stage`.
  2. Headers: `Authorization`, `X-Organization-Id`.
  3. Body: `{"stage": "PROPOSAL"}`.
* **Expected Result:**
  * HTTP 200 OK.
  * Response shows the deal with `stage` updated to `PROPOSAL`.

#### TC-CRM-003: Soft Delete Deal
* **Objective:** Verify soft-delete functionality.
* **Test Data:**
  * `deal_id`: Saved from TC-CRM-001.
* **Step-by-Step Actions:**
  1. Make a `DELETE` request to `/crm/deals/<deal_id>`.
  2. Headers: `Authorization`, `X-Organization-Id`.
* **Expected Result:**
  * HTTP 204 No Content.
  * A subsequent `GET /crm/deals/<deal_id>` should return HTTP 404 Not Found (or excluded from lists).

### Edge Cases & Negative Testing
* **Read-Only Access:** Attempt to delete a CRM deal using an account with only `VIEWER` role permissions. Expect HTTP 403 Forbidden with `ERR_RBAC_001` (Operation requires permission 'crm:delete').

---

## Module 5: Centralised AI Platform & RAG

### Setup & Prerequisites
* Base URL: `http://localhost:8000/api/v1`
* Valid Tenant Context required.
* Background worker (Celery) and Redis must be running for async processing.

### Test Scenarios

#### TC-AI-001: Upload Document for RAG
* **Objective:** Verify uploading a text document triggers an async embedding job.
* **Test Data:**
  * `title`: `Acme Product Specs`
  * `content`: `Acme product v2 features advanced AI integration and cloud sync...`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/ai/documents/upload`.
  2. Headers: `Authorization`, `X-Organization-Id`.
  3. Body: Provide Test Data.
* **Expected Result:**
  * HTTP 202 Accepted.
  * Response contains `job_id` and `document_id`.

#### TC-AI-002: Check AI Job Status
* **Objective:** Verify the async job status can be polled.
* **Test Data:**
  * `job_id`: Saved from TC-AI-001.
* **Step-by-Step Actions:**
  1. Make a `GET` request to `/ai/jobs/<job_id>`.
  2. Headers: `Authorization`, `X-Organization-Id`.
* **Expected Result:**
  * HTTP 200 OK.
  * Status should be `PENDING`, `STARTED`, `SUCCESS`, or `FAILURE`.

#### TC-AI-003: AI Lead Scoring
* **Objective:** Verify AI lead scoring consumes credits and triggers background job.
* **Test Data:**
  * `deal_id`: A valid, existing Deal ID.
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/crm/deals/<deal_id>/ai-score`.
  2. Headers: `Authorization`, `X-Organization-Id`.
* **Expected Result:**
  * HTTP 202 Accepted.
  * Response contains `job_id` and `deal_id`.
  * AI Credits Used should increment by 4 in the DB.

### Edge Cases & Negative Testing
* **Atomic AI Credit Limit Reached:**
  1. Ensure Organization is on FREE tier.
  2. Manually set `ai_credits_used` in the database to 98.
  3. Execute `POST /crm/deals/<deal_id>/ai-score` (which costs 4 credits).
  4. Expect HTTP 402 Payment Required with code `ERR_BILLING_001` (Insufficient AI credits or subscription limit reached).

---

## Module 4: LMS

### Setup & Prerequisites
* Base URL: `http://localhost:8000/api/v1`
* Valid Tenant Context required. Needs a user with Authoring permissions (`TENANT_OWNER`, `TENANT_ADMIN`, `LMS_MANAGER`) for Authoring tests.

### Test Scenarios

#### TC-LMS-001: Create Course & Module (Authoring)
* **Objective:** Verify LMS Author can create a course and a module.
* **Test Data:**
  * Course: `{"title": "Intro to Sales", "description": "Basic sales techniques"}`
  * Module: `{"title": "Week 1: Prospecting", "sort_order": 1}`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/lms/courses`. Save `course_id`.
  2. Make a `POST` request to `/lms/courses/<course_id>/modules`. Save `module_id`.
* **Expected Result:**
  * HTTP 200/201.
  * Course and Module objects are returned with generated IDs.

#### TC-LMS-002: Add Lesson (Authoring)
* **Objective:** Verify Author can add lessons to a module.
* **Test Data:**
  * `module_id`: Saved from TC-LMS-001.
  * Lesson: `{"title": "Cold Calling", "content_body": "Always smile...", "sort_order": 1}`
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/lms/modules/<module_id>/lessons`.
* **Expected Result:**
  * HTTP 200/201.
  * Lesson object is returned. Save the `lesson_id`.

#### TC-LMS-003: Generate AI Quiz
* **Objective:** Verify Authors can generate quizzes for a lesson using AI.
* **Test Data:**
  * `lesson_id`: Saved from TC-LMS-002.
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/lms/quizzes/generate`.
  2. Body: `{"lesson_id": "<lesson_id>"}`
* **Expected Result:**
  * HTTP 202 Accepted.
  * Response contains `job_id`.
  * AI Credits Used should increment by 10.

#### TC-LMS-004: Enroll & Log Progress (Learner)
* **Objective:** Verify a Learner can enroll in a course and log lesson progress.
* **Test Data:**
  * `course_id`: Saved from TC-LMS-001.
  * `lesson_id`: Saved from TC-LMS-002.
* **Step-by-Step Actions:**
  1. Make a `POST` request to `/lms/enrollments`. Body: `{"course_id": "<course_id>"}`.
  2. Make a `POST` request to `/lms/lessons/<lesson_id>/progress`. Body: `{"is_completed": true}`.
* **Expected Result:**
  * HTTP 200 OK.
  * Enrollment and Progress responses show updated status.

### Edge Cases & Negative Testing
* **LMS Authoring Permissions:** Try to execute TC-LMS-001 (Create Course) using a user with only `MEMBER` or `VIEWER` roles. Expect HTTP 403 Forbidden with `ERR_RBAC_001` (Insufficient permissions).
