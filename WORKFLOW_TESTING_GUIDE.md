# BusinessHub AI - End-to-End Workflow Testing Guide

This guide provides step-by-step manual testing instructions that follow a realistic user journey across the BusinessHub AI platform, validating the features outlined in the Comprehensive Functional Features Specification.

---

## Phase 1: Workspace Initialization (Module 0: Core Platform)

**Workflow Goal:** A new company signs up, creates a workspace, and sets up their initial account.

1. **Self-Service Workspace Registration:**
   * **Action:** Navigate to the registration page (or use `POST /api/v1/auth/onboard`).
   * **Input:** Enter company name "Acme Corp", slug "acme-test", email "admin@acme.com", and a secure password.
   * **Expected Result:** The system dynamically verifies the slug is available. Upon submission, the tenant workspace is bootstrapped, and you receive an `access_token` and an `organization_id`.
2. **Stateful Multi-Device Sessions:**
   * **Action:** Log in with the newly created credentials (`POST /api/v1/auth/login`).
   * **Expected Result:** You receive a valid Bearer token and a Refresh token cookie. (Optional: change the password to verify other sessions are invalidated).
3. **Verify Tenant Boundaries:**
   * **Action:** Attempt to access an endpoint (e.g., `GET /api/v1/organizations/me`) using an invalid or missing `X-Organization-Id` header.
   * **Expected Result:** The system denies access, proving granular permission evaluations and tenant isolation.

---

## Phase 2: Upgrading & Compliance (Module 1: Billing & Compliance)

**Workflow Goal:** The tenant upgrades their free account to a paid tier, entering Indian tax details.

1. **Trigger Subscription Upgrade:**
   * **Action:** Authenticated as the Tenant Owner, initiate a checkout (`POST /api/v1/billing/checkout`).
   * **Expected Result:** A Stripe checkout URL is returned. The currency is strictly locked to INR.
2. **B2B GST Tax Invoicing:**
   * **Action:** In the organization settings, update the company profile with a 15-character GSTIN (e.g., `27AADCB2230M1Z2`). Initiate checkout again.
   * **Expected Result:** Stripe checkout reflects the provided GSTIN for B2B tax compliance.
3. **Self-Service Billing Portal:**
   * **Action:** Call the billing portal endpoint (`POST /api/v1/billing/portal`).
   * **Expected Result:** The system returns a secure link to the Stripe customer portal where the user can view invoices and manage RBI e-Mandate auto-debits.

---

## Phase 3: Sales Operations & Collaboration (Module 2: CRM Pipeline)

**Workflow Goal:** The administrator invites a sales rep, creates a customer contact, and manages a deal on the Kanban board.

1. **Secure Team Invitations:**
   * **Action:** As Tenant Owner, generate an invite for `sales@acme.com` (`POST /api/v1/organizations/invitations`).
   * **Expected Result:** A 48-hour expiring token is generated.
   * **Action:** Accept the invite using the token (`POST /api/v1/auth/invite/accept`), setting a password for the new user.
2. **Contact Directory Management:**
   * **Action:** Authenticate as the new sales user. Create a contact (`POST /api/v1/crm/contacts`) with name "John Doe" and phone "555-0199".
   * **Expected Result:** Contact is saved to the directory and linked to the tenant's `organization_id`.
3. **Interactive Kanban Board & Deal Ownership:**
   * **Action:** Create a deal (`POST /api/v1/crm/deals`) titled "Acme Q3 Contract", assigning it to the sales user's ID.
   * **Expected Result:** The deal appears in the `LEAD` stage.
4. **Optimistic UI Handlers:**
   * **Action:** In the UI, drag the deal card from `LEAD` to `QUALIFIED`.
   * **Expected Result:** The card instantly snaps into the new column. The backend API is called and updates the stage seamlessly.

---

## Phase 4: AI Enablement (Module 5: Centralised Enterprise AI)

**Workflow Goal:** The team uploads product documentation and uses the AI Copilot to score the active deal and draft an email.

1. **Universal Document RAG (Upload):**
   * **Action:** As Tenant Owner, upload a product spec sheet (`POST /api/v1/ai/documents/upload`).
   * **Expected Result:** The system accepts the file and triggers asynchronous background ingestion. Polling the job ID shows progress moving to "SUCCESS".
2. **CRM Lead Scoring Copilot:**
   * **Action:** Navigate back to the CRM deal created in Phase 3. Trigger the AI Score function (`POST /api/v1/crm/deals/{deal_id}/ai-score`).
   * **Expected Result:** The AI analyzes the deal, deducting 4 credits from the organization's usage. A background task calculates the score (0-100) and updates the deal record.
3. **Draft Follow-Up Generator:**
   * **Action:** Trigger the draft generator (`POST /api/v1/crm/deals/{deal_id}/draft-followup`).
   * **Expected Result:** The system returns a context-grounded, professional draft email with native INR pricing details.

---

## Phase 5: Training & Enforcement (Module 4: LMS Engine & Billing Soft-Lock)

**Workflow Goal:** The administrator creates an onboarding course. We then test the system's "Pre-Flight Guard" and "Write-Lock Overage" policies.

1. **Course & Curriculum Authoring:**
   * **Action:** As Tenant Owner, create a Course, add a Module, and add a Markdown-formatted Lesson (containing headers, lists, code blocks).
   * **Expected Result:** The course structure is saved. Viewing the lesson in the Markdown Lesson Player securely renders the formatted HTML.
2. **AI Quiz Generator & Pre-Flight Cost Guard:**
   * **Action:** Trigger the AI Quiz generator for the lesson.
   * **Expected Result:** The system atomically deducts exactly 10 AI credits and dispatches the background worker to generate a 5-question quiz.
3. **Trigger the Write-Lock Overage Policy:**
   * **Action:** Ensure the tenant is on the `FREE` tier.
   * **Action:** Use the invitation API to add 3 *more* users, bringing the total user count to 4 (exceeding the Free tier limit of 3).
   * **Action:** Attempt to drag-and-drop a CRM deal, create a new contact, or trigger an AI quiz.
   * **Expected Result:** The system enters a "soft-lock" state. Write operations instantly fail with HTTP 402 `ERR_BILLING_001` (Soft-locked). Existing deals and courses remain readable (no hard deletions).
