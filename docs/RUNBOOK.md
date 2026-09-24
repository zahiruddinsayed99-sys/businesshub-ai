# Operations Runbook (Day-2)

This document provides operational procedures for maintaining the BusinessHub AI platform.

## 1. Database Migrations & Rollbacks (Alembic)

Alembic manages all schema changes. Migrations reside in `backend/alembic/versions`.

### Applying Migrations (Upgrade)
*   **Command:** `alembic upgrade head`
*   **When to use:** During deployment or after pulling new code.
*   **Note on pgvector:** If a migration adds a vector column, ensure the file imports `pgvector`.

### Rolling Back Migrations (Downgrade)
*   **Command:** `alembic downgrade -1` (rolls back a single step).
*   **Command:** `alembic downgrade <revision_id>` (rolls back to a specific version).
*   **Critical Constraint:** All `downgrade()` functions *must* be strictly reversible to avoid `UndefinedTableError` or foreign key violations. Always test downgrades locally on a clean DB (`app_db_mig_test`) before production.

## 2. Monitoring & Logging

### Application Logs
*   The application uses `structlog` for structured JSON logging.
*   On Render, log streams can be captured and forwarded (e.g., to Datadog or AWS CloudWatch) natively. Ensure `LOG_LEVEL` is set to `info` in production.
*   Background tasks natively catch and output exceptions via the logging module to prevent silent failures.

### Infrastructure Health Checks
*   FastAPI exposes `/api/v1/healthz` to check basic application responsiveness.
*   Supabase provides a dashboard for connection pooling stats and DB CPU/RAM usage. Monitor for asyncpg connection exhaustion. Ensure `poolclass=NullPool` is only used in tests, not production.

## 3. Disaster Recovery & Backups

### Database (Supabase)
*   Enable Point-in-Time Recovery (PITR) within the Supabase dashboard for the production environment.
*   **Restoration Steps:** Navigate to Supabase Dashboard -> Database -> Backups -> Restore. The backend will temporarily disconnect; Render services will automatically restart and reconnect.

### Redis Cache
*   Redis is considered ephemeral. If the Redis instance fails, user sessions will drop (requiring re-login) and currently executing background tasks may fail. No persistent backup is strictly required.

## 4. Secure Environment Variables

*   **Never commit `.env` or temporary RSA PEM files to source control.**
*   In Render/Vercel, manage secrets via the respective platform UI.
*   **Key Rotation:** If the JWT RSA keys (`JWT_PRIVATE_KEY`, `JWT_PUBLIC_KEY`) are compromised, generate a new pair via OpenSSL, update the Render environment variables, and restart the service. All active user sessions will immediately invalidate.
