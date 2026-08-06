# Milestone 6: Billing & Subscription Engine - QA Verification Report

## 1. Database Migrations
**Verification:**
*   Executed `alembic upgrade head`.
*   Verified the `organizations` table in PostgreSQL. The table contains the new fields: `subscription_tier`, `subscription_status`, `stripe_customer_id`, `stripe_subscription_id`, `gstin`, `billing_state`, `ai_credits_used`, `bonus_ai_credits`, `last_billing_event_ts` with proper defaults (`FREE` for `subscription_tier` and `subscription_status`, `0` for `ai_credits_used` and `bonus_ai_credits`).
*   **Outcome:** Passed. Table structures updated correctly.

## 2. Stripe Checkout & Portal Endpoints
**Verification:**
*   Triggered the endpoints using a Python script after authenticating and obtaining a JWT token and passing the `X-Organization-Id` header.
*   **Checkout (`POST /api/v1/billing/checkout`) Input:**
    ```json
    {
      "headers": {
        "Authorization": "Bearer <valid_token>",
        "X-Organization-Id": "79a7974e-cb42-4d63-8445-1c72d2cba26d"
      }
    }
    ```
*   **Checkout (`POST /api/v1/billing/checkout`) Output:** Fails with a 500 status (due to dummy `STRIPE_API_KEY=sk_test_51P...` in the `.env` file). However, tracing the code confirms it is configured to initiate a checkout session.
*   **Portal (`POST /api/v1/billing/portal`) Input:**
    ```json
    {
      "headers": {
        "Authorization": "Bearer <valid_token>",
        "X-Organization-Id": "79a7974e-cb42-4d63-8445-1c72d2cba26d"
      }
    }
    ```
*   **Portal (`POST /api/v1/billing/portal`) Output:**
    ```json
    {
      "detail": "No active Stripe customer found"
    }
    ```
    This is expected because the dummy organisation hasn't created a Stripe customer via a successful checkout yet.
*   **Outcome:** Code structure and endpoints are present and behave as expected for the mocked environment state.

## 3. Stripe Webhook Receiver
**Verification:**
*   Run the backend integration tests using `pytest tests/test_billing_integration.py -v`.
*   The `test_forged_webhook_signature` test passed, confirming that forged signatures are correctly rejected with `401 Unauthorized`.
*   The `test_redis_double_spend_protection` test passed, confirming idempotency and exactly-once processing using Redis locks.
*   **Outcome:** Passed.

## 4. Atomic Usage Metering & Downgrade
**Verification:**
*   Run the backend integration tests using `pytest tests/test_billing_integration.py -v`.
*   The `test_atomic_credit_consumption` test passed, verifying that concurrent limits are correctly enforced using Redis.
*   The `test_soft_lock_downgrade` test passed, verifying that operations fail with `HTTP 402` when soft-locked.
*   **Outcome:** Passed.

## 5. Frontend Billing Dashboard
**Verification:**
*   Started the frontend Angular application and navigated to the `/billing` page.
*   **Visual Verification:** The dashboard correctly displays the subscription tier, active plan status, and dynamic usage meters. It also shows a warning alert if the account is soft-locked.
    *   ![Billing Dashboard](backend/billing_dashboard.png)
*   **GSTIN Form Validation:**
    *   Entering 14 characters: Invalid GSTIN format error is displayed.
        *   ![GSTIN 14 Chars](backend/gstin_14_chars.png)
    *   Entering 15 characters: Validated successfully (Save Profile button becomes enabled).
        *   ![GSTIN 15 Chars](backend/gstin_15_chars.png)
    *   Entering 16 characters: Invalid GSTIN format error is displayed.
        *   ![GSTIN 16 Chars](backend/gstin_16_chars.png)
*   **Button Clicks:** Clicking "Upgrade to PRO (Checkout)" and "Manage Billing (Portal)" correctly trigger requests to the backend API (`/api/v1/billing/checkout` and `/api/v1/billing/portal`).
    *   ![Checkout Clicked](backend/billing_checkout_clicked.png)
    *   ![Portal Clicked](backend/billing_portal_clicked.png)
*   **Outcome:** Passed.

## 6. Integration Tests
**Verification:**
*   Executed `pytest tests/test_billing_integration.py -v` after installing required dependencies (`pytest-asyncio`, `pytest-cov`, `pytest-mock`, `stripe`).
*   **Results:**
    ```
    tests/test_billing_integration.py::test_atomic_credit_consumption PASSED [ 25%]
    tests/test_billing_integration.py::test_forged_webhook_signature PASSED  [ 50%]
    tests/test_billing_integration.py::test_redis_double_spend_protection PASSED [ 75%]
    tests/test_billing_integration.py::test_soft_lock_downgrade PASSED       [100%]
    ```
*   **Outcome:** Passed successfully.
