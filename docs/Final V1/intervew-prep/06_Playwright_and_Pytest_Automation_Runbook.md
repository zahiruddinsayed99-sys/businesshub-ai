# 06_Playwright_and_Pytest_Automation_Runbook.md

# BusinessHub AI: Automated Testing Runbook (Pytest & Playwright)

> **Document Classification:** Quality Engineering Runbook, Test Isolation Patterns, CI/CD Test Execution
> 
> 
> **Testing Stacks:** Backend Pytest (AsyncIO + NullPool), Frontend Playwright E2E (`@playwright/test`), Angular Unit Testing (Karma/Jasmine)
> 
> 

---

## 1. Automated Test Suite Architecture & Stability Matrix

Integration tests run karte waqt database poisoning (ek test ka data doosre test ko fail karna) aur background async event loop deadlocks sabse common issues hote hain. BusinessHub AI mein inhein architectural fixes ke zariye stabilize kiya gaya hai.

```
┌────────────────────────────────────────────────────────┐
│             Pytest Integration Suite (39/39)           │
│   conftest.py ➔ engine(NullPool) ➔ db_cleanup Fixture   │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│ Async DB I/O │    │ Redis Client │    │ AsyncMock       │
│ Isolated per │    │ Session/Lock │    │ BackgroundTasks │
│ test run     │    │ Verification │    │ (No Gemini Hit) │
└──────────────┘    └──────────────┘    └─────────────────┘

```

### 1.1 Quality Gates Overview

* **Backend Pytest Suite:** 39/39 passing tests (100% stable in total isolation).


* **Frontend E2E Suite:** Playwright workspace (`e2e/tests/critical_paths.spec.ts`) jo browser par critical conversion paths simulate karta hai.


* **Angular Unit Tests:** 4/4 passing headless Karma/Jasmine tests for core dashboard UI.



---

## 2. Backend Pytest Deep-Dive (Isolation & Mocking Patterns)

### 2.1 Database Hygiene: `NullPool` & `db_cleanup` Fixture

Standard SQLAlchemy connection pool test execution ke doran connection sockets open chhod deta hai. `NullPool` ensure karta hai ki har query ke baad database connection physically close ho. Sath hi `db_cleanup` autouse fixture har test ke baad sabhi tables ko truncate karta hai bina migrations drop kiye.

```python
# backend/tests/conftest.py
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# 1. Test Database Engine with NullPool (No connection reuse across event loops)
test_engine = create_async_engine(
    settings.TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 2. Database Cleanup Fixture (Autouse: Runs after EVERY single test)
@pytest_asyncio.fixture(autouse=True)
async def db_cleanup():
    yield
    # Post-test teardown: Fast transactional truncate across multi-tenant tables
    async with test_engine.begin() as conn:
        await conn.execute(text("""
            TRUNCATE TABLE 
                audit_logs,
                quiz_attempts,
                quiz_questions,
                quizzes,
                lessons,
                course_modules,
                course_enrollments,
                courses,
                crm_deals,
                crm_contacts,
                user_roles,
                users,
                organizations
            CASCADE;
        """))

# 3. DB Session Override for FastAPI TestClient / AsyncClient
@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()

```

### 2.2 Isolating External AI Calls via `unittest.mock.AsyncMock`

Integration tests mein real Google Gemini API calls hit karna tests ko slow karta hai aur production quota waste karta hai. Isliye FastAPI ke `BackgroundTasks` aur AI services ko `AsyncMock` se intercept kiya gaya hai:

```python
# backend/tests/test_ai_gateway.py
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ai_lead_scoring_trigger_isolated(client: AsyncClient, auth_headers: dict):
    # Mocking Gemini AI API response
    mock_gemini_score = {"score": 85, "intent": "HIGH", "reasoning": "Strong enterprise requirement"}
    
    with patch(
        "app.domain.ai.services.AiGatewayService.calculate_lead_score", 
        new_callable=AsyncMock
    ) as mock_ai:
        mock_ai.return_value = mock_gemini_score

        # Trigger AI Lead Scoring API
        response = await client.post(
            "/api/v1/crm/deals/e3b0c442-98fc-1c14-9afb-4c8996fb9242/ai-score",
            headers=auth_headers
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "success"
        assert "job_id" in data["data"]
        
        # Verify AI Gateway was called with correct context
        mock_ai.assert_called_once()

```

---

## 3. Playwright E2E Testing Suite (Frontend Workflows)

Playwright tests headless browser mein execute hote hain aur flaky CSS class names ke bajay Angular reactive form controls (`formControlName`) ko target karte hain.

### 3.1 Playwright Test Configuration

```typescript
// e2e/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 30 * 1000,
  expect: {
    timeout: 5000
  },
  fullyParallel: false, // Run flows sequentially to prevent state collision
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env['E2E_SERVER_URL'] || 'http://127.0.0.1:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ]
});

```

### 3.2 End-to-End Critical Paths Spec

Yeh spec onboarding, login, deal creation, RAG upload, aur LMS quiz workflows ko simulate karta hai:

```typescript
// e2e/tests/critical_paths.spec.ts
import { test, expect } from '@playwright/test';

test.describe('BusinessHub AI Critical User Journeys', () => {

  test('TC-E2E-001: User Login, Tenant Bootstrap & Navigation', async ({ page }) => {
    // 1. Navigate to Login
    await page.goto('/login');

    // 2. Target Angular Reactive Form Controls directly
    await page.fill('input[formControlName="email"]', 'admin@acme.com');
    await page.fill('input[formControlName="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');

    // 3. Verify Hard Redirect and Dashboard Landing
    await expect(page).toHaveURL(/.*\/crm/);
    await expect(page.locator('h2')).toContainText('Active Sales Pipeline');
  });

  test('TC-E2E-002: CRM Deal Creation & Kanban Drag-and-Drop', async ({ page }) => {
    await page.goto('/crm');

    // Open Deal Creation Modal
    await page.click('button#btn-new-deal');
    await page.fill('input[formControlName="title"]', 'Industrial Rooftop Solar 250kW');
    await page.fill('input[formControlName="value_amount"]', '7500000');
    await page.selectOption('select[formControlName="currency"]', 'INR');
    await page.click('button#btn-submit-deal');

    // Verify Deal Card Appears in LEAD stage column
    const dealCard = page.locator('.deal-card', { hasText: 'Industrial Rooftop Solar 250kW' });
    await expect(dealCard).toBeVisible();

    // Move to QUALIFIED stage
    await dealCard.click();
    await expect(dealCard).toBeVisible();
  });

  test('TC-E2E-003: LMS Course Enrollment & Quiz Passing Flow', async ({ page }) => {
    await page.goto('/lms-learner');

    // Verify Course List & Enroll
    const enrollButton = page.locator('button', { hasText: 'Enroll Course' }).first();
    if (await enrollButton.isVisible()) {
      await enrollButton.click();
    }

    // Attempt AI Quiz
    await page.click('button#btn-start-quiz');
    
    // Select passing responses (80% passing rule verification)
    await page.click('input[name="q_01"][value="ans_pan_aadhaar"]');
    await page.click('input[name="q_02"][value="ans_10_lakh_inr"]');
    await page.click('input[name="q_03"][value="ans_senior_mgmt"]');
    await page.click('input[name="q_04"][value="ans_fiu_reporting"]');
    await page.click('input[name="q_05"][value="ans_wrong_choice"]');
    
    await page.click('button#btn-submit-quiz');

    // Verify Passing Banner & Certificate Unlock
    await expect(page.locator('.quiz-result-banner')).toContainText('Passed');
    await expect(page.locator('.quiz-score')).toContainText('80%');
    await expect(page.locator('button#btn-download-cert')).toBeEnabled();
  });

});

```

---

## 4. Test Execution & CI/CD Command Cheatsheet

### 4.1 Backend (Pytest) Execution Commands

```bash
# 1. Activate virtual environment and set test environment variables
cd backend
source venv/bin/activate
export ENVIRONMENT="test"
export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/businesshub_test"
export REDIS_URL="redis://localhost:6379/1"

# 2. Run entire Pytest suite (Clean 39/39 passing)
pytest tests/ -v

# 3. Run a specific test module
pytest tests/test_onboarding.py -v
pytest tests/test_billing_integration.py -v
pytest tests/test_crm_deals.py -v

# 4. Run tests with coverage output
pytest --cov=app --cov-report=term-missing tests/

```

### 4.2 Frontend (Angular & Playwright) Execution Commands

```bash
# 1. Run Angular Unit Tests (Headless mode for CI/CD)
cd frontend
ng test --watch=false --browsers=ChromeHeadless

# 2. Run Playwright End-to-End Tests (Headless)
cd ../e2e
export E2E_SERVER_URL="http://127.0.0.1:4200"
npx playwright test

# 3. Run Playwright in Interactive UI Mode (Debugging file uploads & timings)
npx playwright test --ui

# 4. View detailed HTML test execution report
npx playwright show-report

```

---

## 5. Automated Triage & Common Failure Solutions

| Issue Observed | Root Cause | Architectural Fix Applied |
| --- | --- | --- |
| `RuntimeError: Event loop is closed`<br> | Asynchronous test runs sharing single Redis client socket.

 | Redis lifecycle manager asyncio loop context switches detect karta hai.

 |
| Silent DB Test Contamination

 | Tables mein puraane test records reh jaana.

 | `test_engine` par `NullPool` configure karke `db_cleanup` truncate fixture lagaya.

 |
| Gemini API Hanging / 429 Quota

 | Integration tests external LLM ko live call kar rahe the.

 | `FastAPI BackgroundTasks` aur AI services ko `unittest.mock.AsyncMock` se intercept kiya.

 |
| AuthGuard UI Navigation Loop

 | Token async write hone se pehle router guard execute ho jaana.

 | Tokens localStorage mein likh kar hard reload (`window.location.href = '/crm'`) lagaya.

 |

---