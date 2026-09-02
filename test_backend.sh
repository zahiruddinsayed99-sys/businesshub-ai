#!/bin/bash
export PYTHONPATH=/app/backend
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-test-db"
cd /app/backend
pytest tests/test_tenant_onboarding.py -v
