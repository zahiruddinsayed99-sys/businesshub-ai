#!/bin/bash
set -e

echo "======================================"
echo "Executing Tier 1 Unit Tests (Backend)..."
echo "======================================"
cd backend
source .venv/bin/activate
pytest tests/test_tier1_unit.py
cd ..

echo "======================================"
echo "Executing Tier 1 Unit Tests (Frontend)..."
echo "======================================"
cd frontend
npx ng test --watch=false --browsers=ChromeHeadless --include=src/app/tier1.spec.ts
cd ..

echo "======================================"
echo "Executing Tier 2 Integration Tests..."
echo "======================================"
cd backend
source .venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-db"
pytest tests/test_tier2_api.py
cd ..

echo "======================================"
echo "Executing Tier 3 Playwright E2E Tests..."
echo "======================================"
cd e2e
export E2E_SERVER_URL="http://127.0.0.1:4200"
# npx playwright test  # Note: Requires fully working env
echo "E2E skipped during standalone script execution as they require full backend/frontend servers running."
cd ..

echo "======================================"
echo "All Testing Pyramid Suites Completed!"
echo "======================================"
