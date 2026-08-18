# Milestone 6: Billing & Subscription Engine - QA Verification Guide

## 1. Database Migrations
- **Verify**: Run `alembic upgrade head`. Check the `organizations` table in PostgreSQL to ensure new fields (`subscription_tier`, `subscription_status`, `stripe_customer_id`, `stripe_subscription_id`, `gstin`, `billing_state`, `ai_credits_used`, `bonus_ai_credits`, `last_billing_event_ts`) exist and have proper defaults.
- **Expected Outcome**: Table structures updated without data loss.

## 2. Stripe Checkout & Portal Endpoints
- **Verify Checkout (`POST /api/v1/billing/checkout`)**:
  - Authenticate as a tenant owner.
  - Call the endpoint to get a Stripe Checkout URL.
  - Verify that the URL initiates a checkout session in INR currency with 3D Secure options enabled.
  - If a GSTIN was provided in the organization, ensure the tax ID is mapped correctly.
- **Verify Portal (`POST /api/v1/billing/portal`)**:
  - Authenticate as a tenant owner for an organization with an active Stripe Customer ID.
  - Call the endpoint to get a Stripe Customer Portal URL.
  - Check that the URL directs the user to the Stripe manage subscription page.

## 3. Stripe Webhook Receiver
- **Verify Webhook (`POST /api/v1/billing/webhooks`)**:
  - Send a forged signature and ensure it fails with `401 Unauthorized`.
  - Send a valid signature with an out-of-order `created` timestamp and check that it safely discards (`200 OK`).
  - Send a valid event (`customer.subscription.updated` / `deleted`) and verify the Redis 3-state locking ensures it processes exactly once (test idempotency).
  - **Expected Outcome**: DB `subscription_tier` updates to PRO/FREE appropriately based on status.

## 4. Atomic Usage Metering & Downgrade
- **Verify Atomic Usage**:
  - Run the `consume_ai_credits_br_plt_002` function concurrently.
  - Ensure the check-and-increment properly hits limits at exactly 100 on the FREE tier, failing any transaction that exceeds the limit with a `402 Payment Required`.
- **Verify Soft-Lock Downgrade**:
  - Set a tenant's subscription to FREE and add > 3 active users.
  - Attempt to execute operations in CRM pipeline or invite users.
  - **Expected Outcome**: Operations fail with `HTTP 402 ERR_BILLING_001` (Soft-locked). Read operations should still succeed.

## 5. Frontend Billing Dashboard
- **Verify Standalone Component**:
  - Navigate to `/billing` path.
  - Check the component displays current subscription tier, active plan status, and dynamic usage meters.
  - Ensure the GSTIN form enforces the 15-character alphanumeric format.
  - Test checkout/portal button clicks redirect properly.
  - If the account is soft-locked, ensure the warning alert is visible.

## 6. Run Integration Tests
- **Verify**: Execute `pytest tests/test_billing_integration.py -v`.
- **Expected Outcome**: Tests for forged webhooks, redis double-spend protection, atomic limits, and soft-lock downgrade pass successfully.
