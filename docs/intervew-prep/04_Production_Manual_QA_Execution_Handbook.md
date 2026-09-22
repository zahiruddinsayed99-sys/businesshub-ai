# 04_Production_Manual_QA_Execution_Handbook.md

# BusinessHub AI: Production Manual QA Execution & Verification Handbook

> **Document Classification:** Manual Testing Runbook, Happy Path & Negative Scenarios, Realistic Production Payloads
> 
> 
> **Environment Context:** Production-Ready Staging / Local Docker Compose (`/api/v1`)
> 
> 

---

## 1. Global Setup, Headers & Security Prerequisites

Sabhi HTTP requests mein security headers aur tenant context hona mandatory hai. Missing headers seedha middleware par drop ho jayenge.

* **Base Endpoint:** `http://localhost:8000/api/v1` (Local) ya `[https://api.yourdomain.com/api/v1](https://api.yourdomain.com/api/v1)` (Production)


* **Standard Test Headers:**
* `Authorization`: `Bearer <jwt_access_token>` (15-min RS256 token)


* `X-Organization-Id`: `c8a2b534-11e2-4bf1-8a6e-71f0092ad34a` (Tenant UUID)


* `Content-Type`: `application/json`




---

## 2. Module 5: Central AI Platform (RAG & Enterprise AI Engine)

### 2.1 Happy Path Scenario

* **Goal:** Admin dwara proprietary SOP document upload karna, Celery asynchronous worker dwara text chunking & `pgvector` embedding generation complete hona, aur semantic search se grounded answer retrieve karna.


* **Step 1: Document Upload & Ingestion Trigger**
* **Method / Endpoint:** `POST /api/v1/ai/documents/upload`

* **RBAC Role Required:** `TENANT_OWNER`, `TENANT_ADMIN`, ya `ai:write` scope


* **Request Payload:**
```json
{
  "title": "Vendor Procurement & Audit Policy 2026",
  "content": "All Tier-1 engineering suppliers delivering hardware components to warehouse facilities must be ISO 9001 certified. Tax invoices must be submitted by the 25th calendar day of each month with valid GSTIN and HSN codes to process input tax credit (ITC). Failure to submit prior to the 25th defers settlement to the subsequent billing month."
}

```


* **Expected Response (HTTP 202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "PENDING"
  }
}

```




* **Step 2: Polling Async Background Task**
* **Method / Endpoint:** `GET /api/v1/ai/jobs/f47ac10b-58cc-4372-a567-0e02b2c3d479`

* **Expected Response (HTTP 200 OK):**

```json
{
  "status": "success",
  "data": {
    "job_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "SUCCESS",
    "progress": 100,
    "error": null
  }
}

```




* **Step 3: RAG Semantic Query & Verification**
* **Method / Endpoint:** `POST /api/v1/ai/rag/query`

* **Request Payload:**
```json
{
  "query": "What is the monthly invoice deadline for vendors to claim ITC?"
}

```


* **Expected Response (HTTP 200 OK):**

* Response context strictly uploaded document ko cite karega: *"According to the Vendor Procurement & Audit Policy 2026, tax invoices must be submitted by the 25th calendar day of each month to process ITC."*





### 2.2 Exception Scenarios

* **Exception Scenario A: Atomic AI Credit Limit Breached (BR-PLT-002)**

* **Pre-condition:** Organization Free tier par hai aur database mein `ai_credits_used = 98` set hai (Monthly Limit: 100).


* **Action:** 4 credits wali action execute karein (`POST /crm/deals/{deal_id}/ai-score`).


* **Expected Response (HTTP 402 Payment Required):**

```json
{
  "status": "error",
  "error": {
    "code": "ERR_BILLING_001",
    "message": "Tenant credit limit or subscription tier breached. Upgrade subscription tier via Stripe Customer Portal."
  }
}

```


* **Backend Verification:** Database mein single atomic SQL statement execute hone ki wajah se credit count 98 par hi rehta hai (no partial/negative write) aur Celery task dispatch nahi hota.




* **Exception Scenario B: Zero Cross-Tenant Knowledge Leakage**

* **Pre-condition:** Tenant A ne proprietary vendor policy upload ki hui hai. Tenant B ka valid JWT access token generate karein.


* **Action:** Tenant B ke context se `POST /api/v1/ai/rag/query` hit karein aur Tenant A ki policy ka exact content search karein.


* **Expected Response (HTTP 200 OK):**
* Vector similarity search mein `WHERE organization_id = :tenant_b_id` filter hone ke karan AI jawab dega: *"No relevant document found in your organization workspace."*






### 2.3 Business Value Achievement

* **Operational Efficiency:** 500+ pages ke legal, tax aur corporate policies mein se specific rule search karne ka time ghanto se kam hokar seconds mein aa jata hai.
* **Cost Governance:** Atomic database-level credit deduction ensure karta hai ki concurrent users ek sath AI run karein tab bhi cloud/model overspending zero rahe.



---

## 3. Module 2: CRM Sales Engine (Deals Pipeline & AI Copilot)

### 3.1 Happy Path Scenario

* **Goal:** B2B solar EPC lead ko INR valuation ke sath create karna, Kanban board stage advance karna, aur AI Copilot se lead scoring generate karwana.


* **Step 1: Create B2B Deal**
* **Method / Endpoint:** `POST /api/v1/crm/deals`

* **RBAC Role Required:** `crm:write`

* **Request Payload:**
```json
{
  "title": "Industrial Rooftop Solar 250kW - Phase 1",
  "value_amount": 7500000.00,
  "currency": "INR",
  "stage": "LEAD",
  "expected_close_date": "2026-12-31T18:30:00Z"
}

```


* **Expected Response (HTTP 201 Created):**

```json
{
  "status": "success",
  "data": {
    "id": "e3b0c442-98fc-1c14-9afb-4c8996fb9242",
    "title": "Industrial Rooftop Solar 250kW - Phase 1",
    "value_amount": 7500000.00,
    "currency": "INR",
    "stage": "LEAD",
    "organization_id": "c8a2b534-11e2-4bf1-8a6e-71f0092ad34a",
    "created_at": "2026-09-22T08:55:00Z"
  }
}

```




* **Step 2: Advance Stage (Optimistic UI Update)**
* **Method / Endpoint:** `PATCH /api/v1/crm/deals/e3b0c442-98fc-1c14-9afb-4c8996fb9242/stage`

* **Request Payload:**
```json
{
  "stage": "QUALIFIED"
}

```


* **Expected Response (HTTP 200 OK):** Stage field successfully updates to `QUALIFIED`.




* **Step 3: Trigger AI Lead Scoring Copilot**
* **Method / Endpoint:** `POST /api/v1/crm/deals/e3b0c442-98fc-1c14-9afb-4c8996fb9242/ai-score`

* **Expected Response (HTTP 202 Accepted):**

```json
{
  "status": "success",
  "data": {
    "deal_id": "e3b0c442-98fc-1c14-9afb-4c8996fb9242",
    "job_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
  }
}

```


* **Verification:** Database mein `organizations.ai_credits_used` 4 credits se badhta hai aur background task deal object mein score (0–100) populate kar deta hai.





### 3.2 Exception Scenarios

* **Exception Scenario A: Deal State Machine Violation (BR-CRM-001)**

* **Pre-condition:** Deal abhi `stage = "QUALIFIED"` mein hai aur koi proposal document upload nahi hua hai.


* **Action:** `PATCH /crm/deals/{deal_id}/stage` par stage seedha `"CLOSED_WON"` bhejne ka try karein.


* **Expected Response (HTTP 400 Bad Request):**
```json
{
  "status": "error",
  "error": {
    "code": "ERR_VALIDATION_001",
    "message": "Domain Rule BR-CRM-001: Deal cannot transition to CLOSED_WON without an associated Proposal activity."
  }
}

```




* **Exception Scenario B: Unauthorized Deletion Attempt (RBAC Guard)**

* **Pre-condition:** User ke paas sirf `VIEWER` ya `DOMAIN_MEMBER` role hai (no `crm:delete` permission).


* **Action:** `DELETE /api/v1/crm/deals/e3b0c442-98fc-1c14-9afb-4c8996fb9242` call karein.


* **Expected Response (HTTP 403 Forbidden):**

```json
{
  "status": "error",
  "error": {
    "code": "ERR_RBAC_001",
    "message": "Role lacks necessary permission scope 'crm:delete'."
  }
}

```





### 3.3 Business Value Achievement

* **Pipeline Integrity:** Sales executives fake closures report nahi kar sakte jab tak formal proposal audit trail database mein na ho.


* **Conversion Velocity:** AI score sales reps ko batata hai ki high-intent B2B commercial leads par pehle dhyan diya jaye.



---

## 4. Module 4: LMS Engine (Learning Management, AI Quizzes & Certification)

### 4.1 Happy Path Scenario

* **Goal:** Compliance manager dwara course structure aur Markdown lesson banana, AI dwara 5-question multiple choice quiz generate hona, aur learner ka $\ge 80\%$ score laakar certificate unlock karna.


* **Step 1: Create Course & Module**
* **Method / Endpoint:** `POST /api/v1/lms/courses`

* **RBAC Role Required:** `TENANT_OWNER`, `TENANT_ADMIN`, ya `LMS_MANAGER`

* **Request Payload:**
```json
{
  "title": "Corporate Fair Practices & AML Compliance 2026",
  "description": "Mandatory annual certification covering RBI Fair Practices Code and KYC guidelines."
}

```


* **Expected Response (HTTP 201 Created):** Save `course_id` (e.g., `4d93b9a0-6211-4775-802c-4613c72b2257`).




* **Step 2: Add Markdown Lesson**
* **Method / Endpoint:** `POST /api/v1/lms/modules/{module_id}/lessons`

* **Request Payload:**
```json
{
  "title": "KYC Mandates & Suspicious Transaction Reporting",
  "content_body": "## Core Guidelines\n1. Customer Due Diligence (CDD) requires Officially Valid Documents (PAN, Aadhaar).\n2. Cash transactions above INR 10 Lakh must be reported to FIU-IND within 7 days.\n3. Politically Exposed Persons (PEPs) require senior management sign-off.",
  "sort_order": 1
}

```


* **Expected Response (HTTP 201 Created):** Save `lesson_id` (e.g., `3b95a678-081e-450f-90e6-a05ff7f6f120`).




* **Step 3: Generate AI Quiz (Pre-Flight 10 Credits Guard)**
* **Method / Endpoint:** `POST /api/v1/lms/quizzes/generate`

* **Request Payload:**
```json
{
  "lesson_id": "3b95a678-081e-450f-90e6-a05ff7f6f120"
}

```


* **Expected Response (HTTP 202 Accepted):**

* Organization ke `ai_credits_used` se exactly 10 credits deduct hote hain aur 5-question assessment generate ho jata hai.






* **Step 4: Learner Attempt & Pass Certification ($\ge 80\%$)**

* **Method / Endpoint:** `POST /api/v1/lms/quizzes/attempts`

* **Request Payload (4 out of 5 correct):**
```json
{
  "quiz_id": "119e7a2b-1025-4ad8-a734-d2c6e61f2211",
  "responses": {
    "q_01": "ans_pan_aadhaar",
    "q_02": "ans_10_lakh_inr",
    "q_03": "ans_senior_mgmt",
    "q_04": "ans_fiu_reporting",
    "q_05": "ans_wrong_choice"
  }
}

```


* **Expected Response (HTTP 200 OK):**

```json
{
  "status": "success",
  "data": {
    "score": 80.0,
    "passed": true,
    "certificate_eligible": true
  }
}

```





### 4.2 Exception Scenarios

* **Exception Scenario A: Failing Quiz Score Evaluation (BR-LMS-001)**

* **Pre-condition:** Learner answers submit karta hai jisme 5 mein se sirf 2 sahi hain (Score: 40%).


* **Action:** `POST /api/v1/lms/quizzes/attempts` submit karein.


* **Expected Response (HTTP 200 OK):**

```json
{
  "status": "success",
  "data": {
    "score": 40.0,
    "passed": false,
    "certificate_eligible": false
  }
}

```


* **Verification:** Backend enrollment record ko complete mark nahi karega aur certificate download request 403 throw karegi.




* **Exception Scenario B: Write-Lock Free Tier Overage Enforcement**

* **Pre-condition:** Organization Free tier par hai aur invitations ke zariye total 4 active users register ho chuke hain (Seat limit: 3).


* **Action:** LMS lesson add karne ka try karein (`POST /lms/modules/{id}/lessons`) ya deal create karein.


* **Expected Response (HTTP 402 Payment Required):**

```json
{
  "status": "error",
  "error": {
    "code": "ERR_BILLING_001",
    "message": "Tenant is in soft-lock overage state (>3 users on Free plan). Write operations are frozen."
  }
}

```


* **Verification:** Existing courses aur lessons read-only mode mein khulte hain, data delete nahi hota.





### 4.3 Business Value Achievement

* **Zero Authoring Friction:** Training managers ko multiple-choice assessments likhne mein ghanto nahi bitane padte; AI lesson context se factual questions derive kar deta hai.


* **Audit Compliance Proof:** Strict 80% passing rule aur immutable enrollment logs Indian financial audit bodies (RBI/SEBI/FIU-IND) ko inspection-ready reporting dete hain.



---