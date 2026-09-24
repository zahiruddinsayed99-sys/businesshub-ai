# 05_FastAPI_Angular_Code_Architecture_Templates.md

# BusinessHub AI: Code Architecture Patterns aur Implementation Templates

> **Document Classification:** Code-Level Architectural Reference, Backend Patterns aur Angular 20+ Primitives
> 
> 
> **Applicable Stack:** FastAPI (Python 3.12+), SQLAlchemy 2.0 Async, Pydantic v2, Angular 20+ Standalone Signals
> 
> 

---

## 1. Backend Clean Architecture Layers (FastAPI & SQLAlchemy 2.0)

Codebase inward dependency rule follow karta hai: `API Router` $\rightarrow$ `Service` $\rightarrow$ `Repository` $\rightarrow$ `Database Engine`.

```
┌────────────────────────────────────────────────────────┐
│   API Layer (FastAPI Routers: Request / DTO Parsing)   │
└───────────────────────────┬────────────────────────────┘
                            │ Calls
                            ▼
┌────────────────────────────────────────────────────────┐
│   Application Service Layer (Business Rules & Orchestration)
└───────┬────────────────────────────────────────┬───────┘
        │ Enforces BR-PLT/BR-CRM                 │ Fetches/Saves
        ▼                                        ▼
┌───────────────────────────┐        ┌───────────────────────────┐
│   Domain Logic / Entities │        │ Repositories (Async SQL)  │
└───────────────────────────┘        └─────────────┬─────────────┘
                                                   │ Scoped Queries
                                                   ▼
                                     ┌───────────────────────────┐
                                     │  PostgreSQL 16 Engine     │
                                     └───────────────────────────┘

```

---

### 1.1 Tenant Context Middleware & Thread-Safe Injection

FastAPI middleware har request se Bearer token aur `X-Organization-Id` pakadta hai, RS256 signature verify karta hai, aur Python `ContextVar` mein bind karta hai.

```python
# app/core/tenant_middleware.py
from contextvars import ContextVar
import uuid
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import verify_rs256_jwt, redis_client

# Thread-safe context local storage for tenant
current_tenant_id: ContextVar[uuid.UUID | None] = ContextVar("current_tenant_id", default=None)

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Public endpoints skip tenant validation
        if request.url.path in ["/api/v1/auth/onboard", "/api/v1/auth/login", "/healthz"]:
            return await call_next(request)

        # 1. Extract Bearer Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "ERR_AUTH_001", "message": "Missing or invalid Bearer token"}
            )
        
        token = auth_header.split(" ")[1]
        payload = verify_rs256_jwt(token)
        user_id = payload.get("sub")
        token_id = payload.get("jti")

        # 2. Redis Stateful Session Revocation Check
        session_exists = await redis_client.exists(f"sess:{user_id}:{token_id}")
        if not session_exists:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "ERR_AUTH_001", "message": "Session has been revoked or expired"}
            )

        # 3. Validate Mandatory X-Organization-Id Header
        org_id_header = request.headers.get("X-Organization-Id")
        if not org_id_header:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ERR_TENANT_001", "message": "Missing mandatory X-Organization-Id header"}
            )

        try:
            tenant_uuid = uuid.UUID(org_id_header)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "ERR_TENANT_001", "message": "Invalid X-Organization-Id format"}
            )

        # 4. Bind Tenant ID to ContextVar for this async task
        token_reset = current_tenant_id.set(tenant_uuid)
        try:
            response = await call_next(request)
            return response
        finally:
            current_tenant_id.reset(token_reset)

```

---

### 1.2 Pydantic v2 DTO Contracts

Validation layer strict schemas follow karti hai. Pydantic v2 ka `model_config = ConfigDict(from_attributes=True)` ORM objects ko DTOs mein map karta hai.

```python
# app/schemas/crm.py
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
import uuid
from datetime import datetime
from typing import Optional

class CrmDealCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, example="Industrial Rooftop Solar 250kW")
    value_amount: Decimal = Field(..., gt=0, decimal_places=2, example=7500000.00)
    currency: str = Field(default="INR", pattern="^[A-Z]{3}$", example="INR")
    stage: str = Field(default="LEAD", example="LEAD")
    contact_id: Optional[uuid.UUID] = None

class CrmDealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    value_amount: Decimal
    currency: str
    stage: str
    ai_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

```

---

### 1.3 Repository Pattern (SQLAlchemy 2.0 Async Scoping)

Legacy `session.query()` deprecated hai. Repository ensure karti hai ki `WHERE organization_id = :tenant_id` query level par enforced rahe.

```python
# app/repositories/crm_deal_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import uuid
from app.models.crm import CrmDeal
from app.core.tenant_middleware import current_tenant_id

class CrmDealRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, deal_id: uuid.UUID) -> CrmDeal | None:
        tenant_id = current_tenant_id.get()
        # Row-level tenant isolation + Soft-delete check
        stmt = (
            select(CrmDeal)
            .where(
                CrmDeal.id == deal_id,
                CrmDeal.organization_id == tenant_id,
                CrmDeal.deleted_at.is_(None)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, deal_data: dict) -> CrmDeal:
        tenant_id = current_tenant_id.get()
        new_deal = CrmDeal(
            **deal_data,
            organization_id=tenant_id
        )
        self.db.add(new_deal)
        await self.db.commit()
        await self.db.refresh(new_deal)
        return new_deal

```

---

### 1.4 Atomic AI Credit Metering Dependency (BR-PLT-002)

TOCTOU (Time-Of-Check to Time-Of-Use) race condition se bachne ke liye database engine par single atomic SQL execution:

```python
# app/dependencies/billing_guards.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from app.core.tenant_middleware import current_tenant_id

def verify_and_consume_ai_credits(cost: int):
    async def _guard(db: AsyncSession = Depends(get_db)):
        tenant_id = current_tenant_id.get()
        
        # Single atomic check-and-increment query
        stmt = text("""
            UPDATE organizations 
            SET ai_credits_used = ai_credits_used + :cost 
            WHERE id = :tenant_id 
              AND (ai_credits_used + :cost) <= (monthly_credit_limit + bonus_ai_credits)
            RETURNING ai_credits_used;
        """)
        
        result = await db.execute(stmt, {"tenant_id": tenant_id, "cost": cost})
        row = result.fetchone()
        
        if not row:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "ERR_BILLING_001",
                    "message": "Tenant monthly credit limit exhausted or plan quota breached."
                }
            )
        await db.commit()
        return row[0]
        
    return _guard

```

---

## 2. Modern Angular 20+ Architecture Templates

Angular 20 Standalone Architecture, Signals reactivity, aur `OnPush` change detection paradigm.

---

### 2.1 Functional Tenant HTTP Interceptor

Outgoing API calls par `Authorization: Bearer <token>` aur `X-Organization-Id` auto-append karta hai.

```typescript
// src/app/core/interceptors/tenant.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const tenantInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getAccessToken();
  const currentOrgId = authService.getActiveOrganizationId();

  let modifiedHeaders = req.headers;

  if (token) {
    modifiedHeaders = modifiedHeaders.set('Authorization', `Bearer ${token}`);
  }

  if (currentOrgId) {
    modifiedHeaders = modifiedHeaders.set('X-Organization-Id', currentOrgId);
  }

  const clonedRequest = req.clone({
    headers: modifiedHeaders
  });

  return next(clonedRequest);
};

```

---

### 2.2 Angular 20 Standalone Component (Signals + OnPush + Optimistic UI)

Kanban deal management component jisme Signals aur `computed()` state use hoti hai bina NgRx boilerplate ke:

```typescript
// src/app/domains/crm/deal-pipeline.component.ts
import { Component, ChangeDetectionStrategy, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CrmService, Deal } from './crm.service';

@Component({
  selector: 'app-deal-pipeline',
  standalone: true,
  imports: [CommonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="pipeline-container">
      <header class="summary">
        <h2>Active Sales Pipeline (INR)</h2>
        <p>Total Pipeline Value: ₹{{ totalValue() }}</p>
      </header>

      <div class="columns-grid">
        <div class="column">
          <h3>Lead Stage</h3>
          @for (deal of leadDeals(); track deal.id) {
            <div class="deal-card" (click)="advanceStage(deal, 'QUALIFIED')">
              <h4>{{ deal.title }}</h4>
              <p>₹{{ deal.value_amount }}</p>
            </div>
          }
        </div>

        <div class="column">
          <h3>Qualified Stage</h3>
          @for (deal of qualifiedDeals(); track deal.id) {
            <div class="deal-card">
              <h4>{{ deal.title }}</h4>
              <p>₹{{ deal.value_amount }}</p>
            </div>
          }
        </div>
      </div>
    </div>
  `,
  styles: [`
    .pipeline-container { padding: 1.5rem; }
    .columns-grid { display: flex; gap: 1rem; margin-top: 1rem; }
    .column { flex: 1; background: #1e293b; border-radius: 8px; padding: 1rem; color: #fff; }
    .deal-card { background: #334155; padding: 0.75rem; border-radius: 6px; margin-bottom: 0.5rem; cursor: pointer; }
  `]
})
export class DealPipelineComponent implements OnInit {
  private crmService = inject(CrmService);

  // 1. Reactive Signal State
  deals = signal<Deal[]>([]);

  // 2. Computed Read-Only Derived Signals
  leadDeals = computed(() => this.deals().filter(d => d.stage === 'LEAD'));
  qualifiedDeals = computed(() => this.deals().filter(d => d.stage === 'QUALIFIED'));
  totalValue = computed(() => 
    this.deals().reduce((acc, curr) => acc + Number(curr.value_amount), 0)
  );

  ngOnInit(): void {
    this.loadPipeline();
  }

  loadPipeline(): void {
    this.crmService.fetchDeals().subscribe({
      next: (data) => this.deals.set(data),
      error: (err) => console.error('Failed to load deals', err)
    });
  }

  // 3. Optimistic UI State Handler
  advanceStage(targetDeal: Deal, newStage: string): void {
    const previousState = this.deals();

    // Instantly update UI without waiting for network response
    this.deals.update(current =>
      current.map(d => d.id === targetDeal.id ? { ...d, stage: newStage } : d)
    );

    // Call backend asynchronously
    this.crmService.updateStage(targetDeal.id, newStage).subscribe({
      error: (err) => {
        // Rollback state if API fails
        console.error('Rollback triggered due to API failure', err);
        this.deals.set(previousState);
      }
    });
  }
}

```

---