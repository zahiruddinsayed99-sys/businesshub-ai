# API Documentation Reference

## Base API URL
`http://localhost:8000/api/v1`

## Required Headers (Multi-Tenant Isolation)

All endpoints (except `/auth/*` and public webhooks) require the following HTTP headers:

*   **`Authorization`**: `Bearer <access_token>`
*   **`X-Organization-Id`**: `<uuid_of_organization>`

Requests lacking these will be rejected by the `TenantContext` middleware.

## Standard Payload Responses

### Success
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "success",
  ...data
}
```

### Error Exceptions
Mapped globally via FastAPI exception handlers.
```json
{
  "code": "ERR_VALIDATION_001",
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```
*   `ERR_BILLING_001`: Returned when a `FREE` tier workspace exceeds limits (HTTP 402).

## Auth Lifecycle Endpoints

### `POST /auth/login`
- **Request Body:** JSON payload containing `email` and `password` (Not OAuth2 Form Data).
- **Response:**
```json
{
  "access_token": "eyJhb...",
  "refresh_token": "eyJhb...",
  "token_type": "bearer",
  "user": { ... },
  "organizations": [ ... ]
}
```

### `POST /auth/onboard`
- **Request Body:** `{ "email": "admin@example.com", "password": "...", "organization_name": "Acme Corp" }`
- **Scope:** Public self-service flow. Creates Organization and Tenant Owner.

### `POST /tenants/onboard`
- **Scope:** Internal Super Admin flow. Creates Organization, an Admin user, and a Domain Member user.

## Stripe Webhook Endpoints

### `POST /billing/webhooks`
- Receives events (`customer.subscription.updated`, `customer.subscription.deleted`) from Stripe.
- Validates the `Stripe-Signature` header against `STRIPE_WEBHOOK_SECRET`.
- Modifies `organization.subscription_tier` natively.

## LMS & Context Endpoints

### Learner APIs vs Author APIs
- **Learners:** Requests to `/api/v1/lms/catalog/*`. Strictly read-only for course data.
- **Authors:** Requests to `/api/v1/lms/courses/*`. Full CRUD capabilities.

### `POST /ai/documents/upload`
- Uploads text context. Returns an `AiJob` ID.

### `GET /ai/jobs/{job_id}`
- Polled endpoint to track async state (`PENDING`, `SUCCESS`, `FAILURE`) of embeddings or quiz generation.
