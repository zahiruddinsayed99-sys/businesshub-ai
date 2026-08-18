#!/bin/bash

# Stop immediately if a command exits with a non-zero status
set -e

echo "Starting automated test execution for BusinessHub AI platform..."

# 1. Create centralized reports directory
mkdir -p reports
mkdir -p reports/frontend-coverage
mkdir -p reports/backend-coverage

# 2. Pre-flight Check for Infrastructure
echo "Verifying local infrastructure..."

DB_OK=true
REDIS_OK=true

# Check PostgreSQL
if command -v pg_isready &> /dev/null; then
    if ! pg_isready -h localhost -p 5432 -U postgres >/dev/null 2>&1; then
        DB_OK=false
    fi
else
    # Fallback to python socket check if pg_isready is not installed
    if ! python3 -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2); s.connect(("localhost", 5432))' >/dev/null 2>&1; then
        DB_OK=false
    fi
fi

if [ "$DB_OK" = false ]; then
    echo "Error: Database is not reachable. Please ensure it is running (e.g., via docker-compose up -d db) before executing tests."
    exit 1
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    if ! redis-cli -h localhost -p 6379 ping >/dev/null 2>&1; then
        REDIS_OK=false
    fi
else
    # Fallback to python socket check if redis-cli is not installed
    if ! python3 -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2); s.connect(("localhost", 6379))' >/dev/null 2>&1; then
        REDIS_OK=false
    fi
fi

if [ "$REDIS_OK" = false ]; then
    echo "Error: Redis is not reachable. Please ensure it is running (e.g., via docker-compose up -d redis) before executing tests."
    exit 1
fi

echo "Infrastructure check passed."

# 3. Backend Tests
echo "Running Backend Tests..."
cd backend
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/app-db"

# Create/Activate venv
if [ ! -d "venv" ]; then
    virtualenv venv || python3 -m virtualenv venv || python3 -m venv venv || true
fi
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
pip install -r requirements.txt || true

echo "Running Alembic migrations..."
alembic upgrade head

echo "Executing Pytest..."
pytest tests/ --html=../reports/backend-test-report.html --cov=app --cov-report=html:../reports/backend-coverage
cd ..

# 4. Frontend Tests
echo "Running Frontend Tests..."
cd frontend
npm install

echo "Executing Angular tests (Karma/Jasmine)..."
# Using ChromeHeadless as specified in memory
npx ng test --watch=false --browsers=ChromeHeadless

# Move reports to centralized directory
cp reports/frontend-test-report.html ../reports/ || true
cp -r coverage/frontend-tmp/* ../reports/frontend-coverage/ || true
cd ..

echo "All tests executed successfully!"
echo "Reports are available in the 'reports/' directory:"
echo "  - Backend Test Report: reports/backend-test-report.html"
echo "  - Backend Coverage: reports/backend-coverage/index.html"
echo "  - Frontend Test Report: reports/frontend-test-report.html"
echo "  - Frontend Coverage: reports/frontend-coverage/index.html"
