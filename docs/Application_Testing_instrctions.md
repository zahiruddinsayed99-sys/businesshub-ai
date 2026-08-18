### **BusinessHub AI: Step-by-Step QA Manual Testing Manual**

This manual is designed for QA engineers, junior developers, and manual testing teams. It details the step-by-step procedures to manually verify each of the five core modules of **BusinessHub AI**. 

#### **Global Testing Configuration & Setup**
Before beginning, ensure your local development stack is fully active:
*   **Backend Server Base URL:** `http://localhost:8000/api/v1`
*   **Frontend Client URL:** `http://localhost:4200`
*   **Tools Required:** Postman, Chrome DevTools (F12), and access to the local Redis CLI or pgAdmin/PostgreSQL shell.

---

### **Module 0: Core Platform, Auth & Multi-Tenancy**

#### **TC-AUTH-001: Self-Service Tenant Onboarding (Onboarding)**
*   **Objective:** Verify that a new organization and administrative user can be successfully registered in a single atomic database transaction.
*   **API Endpoint:** `POST /auth/onboard`
*   **Headers:** None (Public Access)
*   **Request Payload (JSON):**
    ```json
    {
      "name": "Acme Systems",
      "slug": "acme-sys",
      "email": "owner@acme.com",
      "password": "SecurePassword123!",
      "full_name": "Alice Owner"
    }
    ```
*   **Action Steps:**
    1. Open Postman, set the method to `POST`, and input `http://localhost:8000/api/v1/auth/onboard`.
    2. Under the **Body** tab, select `raw` and `JSON`, then paste the request payload above.
    3. Click **Send**.
*   **Expected Success Response (201 Created):**
    *   The database writes complete atomically. The response returns an `organization_id`, `user_id`, and `access_token`.
    *   In the response's **Cookies** tab, a `refresh_token` cookie is present with security flags: `HttpOnly`, `SameSite=Strict`, and `Secure`.
*   **Negative Scenarios to Test:**
    *   **Duplicate Workspace Slug:** Send the exact same request again.
        *   *Expected Result:* `409 Conflict` containing the message `"Organization slug already taken"`.
    *   **Invalid Slug Formatting:** Modify the email but change the slug parameter to `"Acme Systems!"` (violating slug regex `^[a-z0-9]+(?:-[a-z0-9]+)*$`).
        *   *Expected Result:* `422 Unprocessable Entity` containing the error code **`ERR_VALIDATION_001`**.

---

#### **TC-AUTH-002: User Login & Redis Session Creation**
*   **Objective:** Verify that registered users can successfully authenticate, receive a signed RS256 token, and establish a stateful Redis session.
*   **API Endpoint:** `POST /auth/login`
*   **Headers:** None (Public Access)
*   **Request Payload (JSON):**
    ```json
    {
      "email": "owner@acme.com",
      "password": "SecurePassword123!"
    }
    ```
*   **Action Steps:**
    1. Send a `POST` request to `/auth/login`.
    2. Retrieve the `access_token` and `organization_id` from the response JSON.
*   **Expected Success Response (200 OK):**
    *   JSON contains `access_token` and `expires_in: 900` (15-minute lifespan).
    *   *Verification (Redis CLI):* Open a terminal, run `redis-cli`, and run `KEYS sess:*`. You should see a session key matching `sess:{user_id}:{token_id}` with a TTL of ~604800 seconds (7 days).

---

#### **TC-AUTH-003: Secure Team Invitation**
*   **Objective:** Verify that a workspace administrator can issue a team invitation, generating a safe link containing a token that expires in 48 hours.
*   **API Endpoint:** `POST /organizations/invitations`
*   **Headers:** 
    *   `Authorization: Bearer <owner_access_token>`
    *   `X-Organization-Id: <acme-sys_organization_uuid>`
*   **Request Payload (JSON):**
    ```json
    {
      "email": "sales@acme.com"
    }
    ```
*   **Action Steps:**
    1. Prepare the request utilizing the administrative Bearer token and the organization ID obtained in the onboarding step.
    2. Execute the request and save the plaintext `token` returned in the JSON body.
*   **Expected Success Response (200 OK):**
    *   The payload contains a secure, random plaintext token string.
    *   *Verification (PostgreSQL):* Run `SELECT token_hash FROM invitations;` in your SQL shell. Confirm that the plaintext invitation is **never** written to the database; only its one-way **SHA-256 hash** must exist in the table.

---

#### **TC-AUTH-004: Consuming & Accepting Team Invitation**
*   **Objective:** Verify that an invited user can register their profile, consume the token, and automatically receive the standard `DOMAIN_MEMBER` role.
*   **API Endpoint:** `POST /auth/invite/accept`
*   **Headers:** None (Public Access)
*   **Request Payload (JSON):**
    ```json
    {
      "token": "<plaintext_saved_invitation_token>",
      "full_name": "Bob Sales",
      "password": "SalesSecurePass123!"
    }
    ```
*   **Action Steps:**
    1. Execute a `POST` request with the invitation token and new account credentials.
*   **Expected Success Response (200 OK):**
    *   The response confirms success: `{"status": "success", "message": "Invitation accepted"}`.
    *   The database marks the invitation as consumed. The active user permission cache in Redis under **`org:{org_id}:usr:{user_id}:perms`** is automatically evicted to refresh authorization scopes.

---

### **Module 1: Multi-Tenant Billing & Indian Market Compliance**

#### **TC-BIL-001: Trigger Indian Compliance Stripe Checkout Session**
*   **Objective:** Verify that a Tenant Owner can launch a checkout session locked strictly to INR currency, configured for B2B GST tax invoices, and compliant with RBI e-mandates.
*   **API Endpoint:** `POST /billing/checkout`
*   **Headers:**
    *   `Authorization: Bearer <owner_access_token>`
    *   `X-Organization-Id: <acme-sys_organization_uuid>`
*   **Action Steps:**
    1. First, make a `PATCH` request to `/organizations/me` to update your corporate billing details:
        *   `{"gstin": "27AADCB2230M1Z2", "billing_state": "Maharashtra"}` (Standard Indian 15-character GSTIN format).
    2. Make a `POST` request to the checkout endpoint `/billing/checkout`.
*   **Expected Success Response (200 OK):**
    *   Returns a secure Stripe checkout redirection URL (`checkout.stripe.com/...`).
    *   *Verification (Stripe Sandbox UI):* Open the URL. The transaction amount must be in **INR currency** and apply a structured **18% GST tax rate** (calculated as CGST + SGST since the tenant resides in Maharashtra) with the organization's GSTIN clearly listed on the tax invoice.

---

#### **TC-BIL-002: Webhook Idempotency & 3-State Redis Locking**
*   **Objective:** Verify that concurrent checkout webhooks are securely handled, preventing double-provisioning or race conditions.
*   **API Endpoint:** `POST /billing/webhooks`
*   **Headers:**
    *   `Stripe-Signature: t=123,v1=fake_signature_hash`
*   **Action Steps:**
    1. Formulate a mock JSON webhook body containing a standard Stripe event (e.g. `customer.subscription.updated`).
    2. Dispatch the payload using a mock signature header.
*   **Expected Security Result:**
    *   An invalid signature returns `401 Unauthorized` with the message `"Invalid signature"`.
    *   Upon sending a valid mock webhook signature twice concurrently: The first request triggers our **3-State Redis Lock** (`stripe_lock:{event_id}`) and updates the database, while the second request immediately short-circuits and returns a fast `200 OK` to prevent duplicate transaction increments.

---

#### **TC-BIL-003: Free-Tier Write-Lock Overage Policy**
*   **Objective:** Verify that the platform automatically soft-locks write actions when a downgraded Free tier organization exceeds its user seat limits.
*   **Action Steps:**
    1. Ensure the organization is configured on the `FREE` plan tier in your database.
    2. Repeat the invite process (**TC-AUTH-003** and **TC-AUTH-004**) until the workspace contains **4 active users** (exceeding the limit of 3).
    3. Authenticate as any user in this organization and attempt to write a new CRM deal:
        *   `POST /api/v1/crm/deals` with `{"title": "Test Under Soft Lock", ...}`.
*   **Expected Result (402 Payment Required):**
    *   The API rejects the write operation, returning HTTP Status `402` and system error code **`ERR_BILLING_001`**.
    *   *Read-Only Integrity Check:* Try executing `GET /api/v1/crm/deals`. The query must resolve successfully, proving that overage workspaces are soft-locked (write-locked) but remain strictly readable.

---

### **Module 2: CRM Pipeline**

#### **TC-CRM-001: Pipeline Deal Creation & Stage Updates**
*   **Objective:** Verify that authorized users can create active deals and modify their placement on the Kanban board.
*   **API Endpoint:** `POST /crm/deals`
*   **Headers:**
    *   `Authorization: Bearer <member_access_token>`
    *   `X-Organization-Id: <acme-sys_organization_uuid>`
*   **Request Payload (JSON):**
    ```json
    {
      "title": "Acme Enterprise Deal",
      "value_amount": 750000.00,
      "currency": "INR",
      "stage": "LEAD"
    }
    ```
*   **Action Steps:**
    1. Send a `POST` request to create the deal and capture the generated `id` (e.g. `deal_uuid`) from the response.
    2. Simulate a drag-and-drop column transition in Kanban by sending a `PATCH` request to `/crm/deals/<deal_uuid>/stage` with the body `{"stage": "PROPOSAL"}`.
*   **Expected Success Response:**
    *   Creating the deal returns `201 Created` with the transaction audit properties populated.
    *   Updating the stage returns `200 OK`, persisting the new stage column dynamically.

---

#### **TC-CRM-002: Zero-Leakage Horizontal Isolation**
*   **Objective:** Verify that users cannot peek or modify data belonging to other tenant organizations.
*   **Action Steps:**
    1. Sign up a completely different company, "Tenant B", obtaining their unique organization ID and JWT access token.
    2. Authenticate using Tenant B's JWT, but inject Tenant A's `X-Organization-Id` header and attempt to query the CRM pipeline:
        *   `GET /api/v1/crm/deals`.
*   **Expected Security Result (403 Forbidden):**
    *   The isolation middleware blocks the thread immediately, throwing **`ERR_TENANT_001` (HTTP 403)** because the user does not have an active role mapping under Tenant A.
    *   *IDOR Deep Probe:* Try querying the specific UUID of Tenant A's deal using Tenant B's header context:
        *   `GET /api/v1/crm/deals/<tenant_a_deal_uuid>`.
    *   *Expected Result:* The repository catches the boundary violation and throws **`ERR_NOT_FOUND_001` (HTTP 404 Not Found)** instead of a 403. This eliminates cross-tenant metadata scanning by hiding the record's existence.

---

### **Module 5: Centralised Enterprise AI Platform**

#### **TC-AI-001: Universal Document Ingestion & RAG Indexing**
*   **Objective:** Verify uploading markdown documentation triggers background text chunking, pgvector embedding generation, and progress tracking.
*   **API Endpoint:** `POST /ai/documents/upload`
*   **Request Payload (JSON):**
    ```json
    {
      "title": "Standard Negotiating Framework",
      "content": "Acme corporate strategy dictates that premium client services are priced strictly in INR terms..."
    }
    ```
*   **Action Steps:**
    1. Dispatch the request containing the markdown text block to `/ai/documents/upload`.
    2. Capture the returned asynchronous `job_id` from the response.
    3. Make a `GET` request to `/ai/jobs/<job_id>` to poll the background task status.
*   **Expected Success Response:**
    *   Uploading the document immediately returns `202 Accepted` with a tracking job ID.
    *   Polling the job status returns a structured JSON payload depicting `PENDING`, `STARTED`, or `SUCCESS` once the Celery task completes pgvector commits.

---

#### **TC-AI-002: Pre-Flight AI Credit Metering & Lead Scoring**
*   **Objective:** Verify that calculating AI lead scores atomically deducts organization credits and rejects actions once the balance is depleted.
*   **API Endpoint:** `POST /crm/deals/{deal_id}/ai-score`
*   **Action Steps:**
    1. Ensure your active organization has a positive credit balance.
    2. Make a `POST` request to calculate the score for your deal.
    3. Retrieve your organization profile to verify your `ai_credits_used` balance has increased by 4 credits.
    4. *Exhaustion Test:* Manually decrease your database's remaining credit balance to `0`. Attempt to trigger the AI scoring endpoint again.
*   **Expected Results:**
    *   Under positive credit balances: Returns `202 Accepted` and triggers lead scoring calculations asynchronously.
    *   Under exhausted balances: The pre-flight middleware blocks the thread *prior* to hitting external APIs, throwing **`ERR_BILLING_001` (HTTP 402 Payment Required)**.

---

### **Module 4: AI-Powered Learning & Enablement (LMS Engine)**

#### **TC-LMS-001: Course Authoring & Curriculum Setup**
*   **Objective:** Verify that course authors can draft full learning programs, module directories, and lesson content.
*   **API Endpoints:**
    *   `POST /api/v1/lms/courses`
    *   `POST /api/v1/lms/courses/<course_id>/modules`
    *   `POST /api/v1/lms/modules/<module_id>/lessons`
*   **Action Steps:**
    1. Authenticate as a user possessing `lms:write` privileges (e.g. `TENANT_OWNER` or `LMS_MANAGER`).
    2. Create a course: `{"title": "Advanced Pipeline Conversion", "description": "LMS for sales reps"}`. Save the returned `course_id`.
    3. Create a module: `{"title": "Module 1: Opening Pitches", "sort_order": 1}`. Save the returned `module_id`.
    4. Add a lesson: `{"title": "Dynamic Handshakes", "content_body": "Always make firm eye-contact...", "sort_order": 1}`. Save the returned `lesson_id`.
*   **Expected Success Response (201 Created):**
    *   All entities return with generated UUIDs and their default states set.
    *   *Vertical RBAC Check:* Try executing the course creation endpoint using an account with only the standard `DOMAIN_MEMBER` role. The API must reject the attempt, returning `HTTP 403 Forbidden` containing the error code **`ERR_RBAC_001`**.

---

#### **TC-LMS-002: Enrollment & Automatic Course Completion Tracker**
*   **Objective:** Verify that learners can self-enroll and log lesson progress, triggering automatic course completion once all nodes are completed.
*   **API Endpoints:**
    *   `POST /api/v1/lms/enrollments`
    *   `POST /api/v1/lms/lessons/{id}/progress`
*   **Action Steps:**
    1. Authenticate as a standard learner (`DOMAIN_MEMBER`).
    2. Enroll in the newly authored sales course: `{"course_id": "<course_uuid>"}`.
    3. Mark the course's only lesson as complete: `{"is_completed": true}`.
*   **Expected Success Response:**
    *   Enrollment returns a confirmation with status `"ENROLLED"`.
    *   Logging the final lesson progress returns a success JSON. Under the hood, the service automatically detects that all lessons in the course are checked off, updating `course_enrollments.status` to `"COMPLETED"` and stamp-dating `completed_at`.

---

#### **TC-LMS-003: AI Quiz Generator & Pre-Flight Cost Gates**
*   **Objective:** Verify that authors can generate automated multi-choice quizzes from lesson content, enforcing credit cost deductions.
*   **API Endpoint:** `POST /api/v1/lms/quizzes/generate`
*   **Request Payload (JSON):**
    ```json
    {
      "lesson_id": "<lesson_uuid>"
    }
    ```
*   **Action Steps:**
    1. Authenticate with an administrative account holding at least 10 AI credits.
    2. Request the quiz generation for your sales lesson.
    3. Verify that your organization's used credit counter has increased by 10 credits.
*   **Expected Success Response (202 Accepted):**
    *   The API returns a task ID. The Celery background worker consumes the lesson's Markdown text, prompts the centralized AI Service using the strict `lms_quiz_v1` JSON structured contract, and commits a 5-question multi-choice quiz to Postgres.
    *   *Low-Balance Check:* Set your organization's credits to zero. Attempt the quiz generation request again. The API must abort immediately, returning **`ERR_BILLING_001` (HTTP 402)** without executing any background AI tasks.

---

#### **TC-LMS-004: Lesson Assessment & Grading Engine (BR-LMS-001)**
*   **Objective:** Verify that learner quiz submissions are graded correctly, enforcing the minimum 80% passing standard.
*   **API Endpoint:** `POST /api/v1/lms/quizzes/attempts`
*   **Request Payload (JSON):**
    ```json
    {
      "quiz_id": "<generated_quiz_uuid>",
      "answers": [
        { "question_id": "<q1_uuid>", "selected_answer_id": "<a1_uuid>" },
        { "question_id": "<q2_uuid>", "selected_answer_id": "<a2_uuid>" },
        { "question_id": "<q3_uuid>", "selected_answer_id": "<a3_uuid>" },
        { "question_id": "<q4_uuid>", "selected_answer_id": "<a4_uuid>" },
        { "question_id": "<q5_uuid>", "selected_answer_id": "<a5_uuid>" }
      ]
    }
    ```
*   **Action Steps:**
    1. Authenticate as a learner and execute a quiz submission answering **at least 4 out of 5 questions correctly** (80% score).
    2. Execute a second quiz attempt, deliberately answering **only 2 questions correctly** (40% score).
*   **Expected Grading Results:**
    *   First Attempt: Returns `{"score": 80.00, "passed": true}`, satisfying **`BR-LMS-001`**.
    *   Second Attempt: Returns `{"score": 40.00, "passed": false}`.

---

### 📋 **QA Verification Command Matrix**

Junior developers can quickly run the automated test suite locally to back up their manual test assertions using these commands:

```bash
# Initialize and apply migrations to your test database
pytest --setup-show

# Execute Core Platform and Authentication tests (Module 0)
pytest backend/tests/test_onboarding.py -v

# Execute Stripe Billing and Indian tax calculation tests (Module 1)
pytest backend/tests/test_billing_integration.py -v

# Execute CRM Pipeline and RAG AI tests (Modules 2 & 5)
pytest backend/tests/test_crm_pipeline.py -v

# Execute LMS Engine and Quiz grading tests (Module 4)
pytest backend/tests/test_lms_engine.py -v
```
---