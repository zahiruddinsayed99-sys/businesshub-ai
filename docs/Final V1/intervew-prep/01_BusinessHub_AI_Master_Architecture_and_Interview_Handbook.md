# 01_BusinessHub_AI_Master_Architecture_and_Interview_Handbook.md

# BusinessHub AI: Architecture, System Design aur Interview Master Handbook

> **Project Classification:** Enterprise Multi-Tenant Modular Business Operating Platform
> 
> 
> **Production Topology:** Zero-Cost Cloud Staging (Vercel + Render + Supabase + Upstash + Cloudflare R2)
> 
> 

---

## 1. System Vision & Architectural Rationale

### 1.1 Modular Monolith vs Microservices ka Decision (ADR-001)

BusinessHub AI ko shuruat mein microservices banane ke bajay ek **Modular Monolith** pattern par banaya gaya hai:

* **Microservices ki Problem:** Agar Day 1 se microservices banate, toh distributed network latency, distributed transaction rollbacks (2PC/Saga patterns), service mesh configuration aur multi-repo deployment ka overhead choti teams ko slow kar deta.


* **Modular Monolith Solution:** Saare modules (`CRM`, `LMS`, `Billing`, `AI Gateway`) ek hi deployable container aur repository ke andar rehte hain, lekin domain boundaries strict hain (`app/domain/{module}`). Database operations isolated repositories handle karti hain.


* **Future-Proofing:** Codebase clean architecture follow karta hai; agar aage chal kar kisi heavy module ko independent scale karna ho, toh bina poora code rewrite kiye use separate microservice mein nikal sakte hain.



### 1.2 System Topology Diagram

```
┌────────────────────────────────────────────────────────┐
│               Angular 20+ Frontend (SPA)               │
│  Standalone Components | Signals Reactive State        │
│  ChangeDetectionStrategy.OnPush | HTTP Interceptors    │
└───────────────────────────┬────────────────────────────┘
                            │ Bearer JWT + X-Organization-Id
                            ▼
┌────────────────────────────────────────────────────────┐
│                 FastAPI Backend (ASGI)                 │
│  TenantContextMiddleware (RS256 JWT, RBAC, ContextVar) │
│  Clean Architecture: Routers ➔ Services ➔ Repositories │
└───────┬───────────────────┬────────────────────┬───────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌─────────────────┐
│  PostgreSQL  │    │ Redis Cache  │    │ Cloudflare R2   │
│ 16+pgvector  │    │ & Celery     │    │ Object Storage  │
│ Multi-Tenant │    │ Sessions,    │    │ Presigned URLs, │
│ Data Scopes  │    │ Webhook Lock │    │ Documents       │
└──────────────┘    └──────────────┘    └─────────────────┘

```

### 1.3 Zero-Cost Production Infrastructure Setup

Application ko bina heavy infra cost ke enterprise production level par deploy kiya gaya hai:

* **Frontend CDN:** Vercel (Angular 20 static edge hosting).


* **Backend Web Service:** Render (Dockerized FastAPI ASGI service).


* **Primary Relational DB:** Supabase / Neon (Managed PostgreSQL 16 with `pgvector` extension).


* **Cache & Message Broker:** Upstash Serverless Redis 7.


* **Object / Document Storage:** Cloudflare R2 (S3-compatible, zero egress bandwidth fee).



---

## 2. Multi-Tenancy & Zero-Trust Security Deep-Dive

### 2.1 Row-Level Tenant Isolation (ADR-002)

* **Database/Schema per Tenant kyu nahi choose kiya?** Har tenant ke liye alag database ya schema banane se free/hobby cloud tiers par connection pool instantly exhaust ho jate hain aur Alembic migrations run karna complex ho jata hai.


* **Row-Level Isolation:** Single PostgreSQL database mein har entity table ke andar `organization_id UUID NOT NULL` mandatory foreign key column hoti hai.


* **Session Query Scoping:** Repositories ensure karti hain ki har `SELECT`, `UPDATE` aur `DELETE` query ke sath `WHERE organization_id = :current_tenant_id` filter automatically execute ho.



### 2.2 Request Lifecycle & Tenant Middleware Pipeline

1. **Client Request:** Angular frontend se har API call ke sath mandatory headers jate hain:


* `Authorization: Bearer <access_token>`

* `X-Organization-Id: <tenant_uuid>`



2. **FastAPI Middleware Interception (`TenantContextMiddleware`):**
* Token ko RS256 Public Key ke against decode karke signature verify karta hai.


* Redis key `sess:{user_id}:{token_id}` se session validity check karta hai.


* Confirm karta hai ki authenticated user request ke `X-Organization-Id` ka verified active member hai ya nahi.


* Missing header ya unauthorized tenant hone par request ko turant block karke **HTTP 403 Forbidden (`ERR_TENANT_001`)** throw karta hai.




3. **Context Injection:** Verification pass hone ke baad tenant ID ko Python ke thread-safe `ContextVar` (`current_tenant_id`) aur SQLAlchemy session info (`db.info["tenant_id"]`) mein inject kar diya jata hai.



### 2.3 Cryptographic Token Lifecycle & Redis Stateful Sessions

* **RS256 vs HS256:** HS256 symmetric hota hai (ek hi secret key encryption aur verification dono karti hai, leak hone par forged tokens ban sakte hain). Isliye humne **RS256** (Asymmetric 2048-bit RSA Private/Public Key) use kiya hai.


* **Dual-Token System:**
* `Access Token`: 15-minute expiry, fast API authorization ke liye use hota hai.


* `Refresh Token`: 7-day expiry, strictly `HttpOnly`, `SameSite=Strict`, `Secure` cookies mein rakha jata hai (JavaScript access blocked hone ki wajah se XSS token theft impossible ho jata hai).




* **Stateful Session Revocation:** JWT stateless hota hai, isliye instant revocation ke liye har login par Redis mein key banti hai: `sess:{user_id}:{token_id}` (TTL: 7 days). Logout par specific key delete hoti hai. Password reset par `sess:{user_id}:*` pattern scan karke all-device logout trigger ho jata hai.


* **Cached RBAC:** Har API hit par database hit na ho, isliye user permissions ko `org:{org_id}:usr:{user_id}:perms` key mein 15 minutes ke liye cache kiya jata hai. Role change hone par `evict_user_permissions_cache` function is key ko instantly invalidate kar deta hai.



---

## 3. Billing, Concurrency & Indian Market Compliance

### 3.1 Indian Regulatory Stack (INR, RBI & GST)

* **INR Currency Lock:** SaaS platform pricing globally Indian Rupee (INR) mein hardcoded hai.


* **RBI e-Mandate Compliance:** Reserve Bank of India ke AFA (Additional Factor of Authentication) auto-debit rules follow karne ke liye Stripe Checkout mein **3D Secure (challenge)** mandate registration enforce kiya gaya hai.


* **18% GST B2B Invoicing:** Database mein tenant ka 15-character `gstin` aur `billing_state` capture hota hai. System calculate karta hai ki CGST/SGST (intra-state) lagega ya IGST (inter-state) taaki clients ko Input Tax Credit (ITC) mil sake.



### 3.2 TOCTOU Mitigation & Atomic Credit Metering (BR-PLT-002)

Jab multiple users simultaneously AI triggers chalate hain, toh application layer check-then-write mein **Time-Of-Check to Time-Of-Use (TOCTOU)** race condition aati hai, jisse credits negative ho sakte hain.

* **Database-Level Atomic Execution:** Application check hata kar single atomic database query lagayi gayi hai:



```sql
UPDATE organizations 
SET ai_credits_used = ai_credits_used + :cost 
WHERE id = :tenant_id 
  AND (ai_credits_used + :cost) <= (monthly_credit_limit + bonus_ai_credits)
RETURNING ai_credits_used;

```

Agar limit cross ho, toh update 0 rows return karta hai aur API Celery task dispatch kiye bina seedha **HTTP 402 Payment Required (`ERR_BILLING_001`)** return karta hai.

### 3.3 3-State Redis Webhook Lock

Stripe webhooks ke network retries ya out-of-order execution ko sambhalne ke liye idempotency mechanism:

1. **Lock State:** Webhook aate hi Redis key banti hai: `SET lock:stripe_evt:{event_id} "locked" NX EX 60` (duplicate webhook turant drop ho jata hai).


2. **DB Transaction:** Payload ka event timestamp check hota hai: agar `last_billing_event_ts` already new timestamp par hai, toh out-of-order puraane event ko ignore kiya jata hai.


3. **Done State:** Success hone par key transition ho jati hai to `done:stripe_evt:{event_id}` (TTL: 24 hours). Agar crash ho jaye, toh 60-second lock expire hone par Stripe ka retry safely process ho sake.



### 3.4 Soft-Lock Overage Policy

Agar tenant PRO se FREE plan par downgrade karta hai, toh platform existing users ya deals ko delete nahi karta.

* Free plan par maximum 3 active users allowed hain.


* Agar downgrade ke waqt organization mein >3 users hain, toh `check_soft_lock_overage` trigger ho jata hai.


* System existing records ko safe rakhta hai (read-only), par saare naye write operations (deals, invite, quiz generation) **HTTP 402 ERR_BILLING_001** ke sath freeze ho jate hain jab tak admin extra seats remove na kar de.



---

## 4. Asynchronous Processing, AI Platform & Modern Frontend

### 4.1 FastAPI ASGI Event Loop Protection

* FastAPI async single-threaded event loop par chalta hai.


* Synchronous heavy SDK calls (jaise Stripe SDK) ko directly async route mein chalane se event loop freeze ho jata hai.


* Is issue ko resolve karne ke liye sync operations ko `run_in_threadpool(func, *args)` mein wrap karke dedicated worker threads par run kiya gaya hai.



### 4.2 Distributed Celery Queue & Multi-Tenant RAG

* **Offloading:** Heavy tasks (file parsing, embeddings, quiz creation) par API immediately **HTTP 202 Accepted** with `job_id` dekar free ho jati hai aur task Celery worker ko pass ho jata hai.


* **RAG Pipeline:** Documents Cloudflare R2 par pre-signed URLs ke through direct browser se upload hote hain. Background tasks unke text chunks ko Gemini embedding model se process karke PostgreSQL `pgvector` extension mein persist karte hain.


* **Cross-Tenant Vector Isolation:** Similarity queries execute karte waqt `organization_id` filter compulsory rehta hai, jisse company A ka AI prompt kabhi company B ke documents ko read na kar sake.



### 4.3 Angular 20+ Frontend Architecture

* **Standalone Paradigm:** Bulky `NgModule` ko poori tarah drop karke sabhi components ko `standalone: true` banaya gaya hai.


* **Fine-Grained Signals Reactivity:** Heavy NgRx boilerplate ke bajay Angular Signals (`signal()`, `computed()`, `effect()`) use hue hain. Jab signal mutate hota hai, toh Angular poore DOM tree ko traverse karne ke bajay strictly us specific node ko update karta hai.


* **ChangeDetectionStrategy.OnPush:** Har component par default OnPush set hai, jisse background dirty-checking overhead zero ho jata hai.


* **RxJS to Signals Bridge:** Form debouncing jaisi streams ko memory leaks se bachane ke liye `.subscribe()` ke bajay seedha `toSignal()` se handle kiya gaya hai.


* **Route Guard Lifecycle Stabilization:** Onboarding ke baad token write hone aur route guard (`AuthGuard`) chalne ke beech ki race condition ko door karne ke liye tokens ko localStorage mein daal kar hard redirect (`window.location.href = '/crm'`) lagaya gaya hai.



---

## 5. Testing Hygiene & Production Stability

### 5.1 Pytest Database Isolation (`NullPool` & `db_cleanup`)

Integration tests run karte waqt database poisoning (ek test ka data doosre test ko fail karna) aur background async hangs ko solve kiya gaya:

* **NullPool Connection:** Standard connection pool connections open chhod deta hai. Test suite ke andar `NullPool` use kiya gaya hai taaki test complete hote hi connection physically close ho jaye.


* **Transactional Truncate Cleanup:** Auto-use fixture `db_cleanup` har test function ke baad saare tables ko truncate karta hai bina migrations drop kiye.


* **Async Mocking:** External AI calls se bachne ke liye FastAPI `BackgroundTasks` ko `unittest.mock.AsyncMock` se isolate kiya gaya hai (Achieving 100% test pass rate: 39/39 passing).



### 5.2 Playwright E2E Testing

Frontend user journeys ko verify karne ke liye Playwright suite headless browser mein execute hota hai (`e2e/tests/critical_paths.spec.ts`), jo CSS classes ke bajay stable Angular form controls (`formControlName="email"`, `formControlName="password"`) ko target karta hai.

---

## 6. Error Code Reference Catalog

| Error Code | HTTP Status | Root Cause & System Behavior |
| --- | --- | --- |
| `ERR_AUTH_001`<br> | **401 Unauthorized**<br> | Missing/expired RS256 JWT, ya token Redis session (`sess:*`) se revoke ho chuka hai.

 |
| `ERR_TENANT_001`<br> | **403 Forbidden**<br> | `X-Organization-Id` missing hai ya user us tenant ka active member nahi hai.

 |
| `ERR_RBAC_001`<br> | **403 Forbidden**<br> | Authenticated user ke role ke paas action execute karne ki permission nahi hai.

 |
| `ERR_BILLING_001`<br> | **402 Payment Required**<br> | AI credit limit breach ho gayi hai ya Free tier soft-lock active hai (>3 users).

 |
| `ERR_VALIDATION_001`<br> | **422 Unprocessable**<br> | Request payload Pydantic v2 schemas aur regex constraints ko fail kar gaya.

 |
| `ERR_RATE_LIMIT_001`<br> | **429 Too Many Requests**<br> | Redis sliding-window limit cross ho chuki hai.

 |
| `ERR_NOT_FOUND_001`<br> | **404 Not Found**<br> | Entity exist nahi karti, soft-deleted (`deleted_at IS NOT NULL`) hai, ya kisi aur tenant ki hai.

 |

---

## 7. Verbal Interview Speaking Frameworks

### Q1: "BusinessHub AI ke architecture ko explain kijiye."

> "BusinessHub AI ek multi-tenant modular monolith platform hai jise FastAPI (Python 3.12) aur Angular 20 par banaya gaya hai. Shuruat mein microservices ke distributed network latency aur Saga transaction rollback issues se bachne ke liye humne strict domain packaging (`app/domain/{module}`) use ki hai. Relational storage aur vector search ke liye PostgreSQL 16 with `pgvector` use hota hai, caching aur distributed queueing ke liye Redis aur Celery deploy kiye gaye hain. Row-level isolation ke sath zero-trust security enforce ki gayi hai, jisme har request tenant middleware aur ContextVar ke zariye strictly scoped rehti hai."
> 
> 

### Q2: "Concurrent user activity mein AI credit consumption ko race condition se kaise bachaya?"

> "Jab multi-user environment mein multiple log ek sath AI features trigger karte hain, toh application layer par check-then-write code Time-Of-Check to Time-Of-Use (TOCTOU) race condition create karta hai, jisse credits negative mein chale jate hain. Isko solve karne ke liye humne Python layer se check hata kar single atomic SQL execution database engine par shift kiya:
> 
> 
> `UPDATE organizations SET ai_credits_used = ai_credits_used + :cost WHERE id = :tenant_id AND (ai_credits_used + :cost) <= (monthly_credit_limit + bonus_ai_credits) RETURNING ai_credits_used;`
> 
> Agar credits exhaust ho jayein, toh query 0 rows return karti hai aur API request bina background worker ko trigger kiye turant HTTP 402 ERR_BILLING_001 throw kar deti hai."
> 
> 

### Q3: "Stripe webhooks handling aur double-spending protection kaise implement ki?"

> "Webhooks mein network retries ki wajah se duplicate ya out-of-order events aane ka risk hota hai. Pehle step mein hum Stripe HMAC SHA-256 signature verify karte hain. Uske baad ek 3-State Redis Lock protocol (`lock` $\rightarrow$ DB Transaction $\rightarrow$ `done`) execute hota hai. Webhook aate hi event ID par 60 seconds ka distributed lock lag jata hai. Database transaction ke doran hum `last_billing_event_ts` check karke out-of-order puraane events ko silently drop kar dete hain. Success par Redis key 24 hours ke liye `done` mark ho jati hai."
> 
> 

---