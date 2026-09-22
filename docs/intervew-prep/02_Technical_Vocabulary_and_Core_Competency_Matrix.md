# 02_Technical_Vocabulary_and_Core_Competency_Matrix.md

# BusinessHub AI: Technical Vocabulary aur Full-Lifecycle Competency Matrix

> **Document Classification:** Engineering Vocabulary, Core Competencies aur Hands-On Lifecycle Skills
> 
> 
> **Target Audience:** Comeback Engineers, Senior Full-Stack Developers aur Technical Interviewees
> 
> 

---

## 1. Domain & Technical Vocabulary Dictionary (A to Z Terminology)

Neeche un specific keywords aur technical terms ki list di gayi hai jo BusinessHub AI ke pure lifecycle mein use huye hain:

### A

* **ADR (Architectural Decision Record):** Architecture level par liye gaye structural decisions aur trade-offs ka formal documentation (jaise ADR-001: Modular Monolith, ADR-002: Row-Level Isolation).


* **Alembic Migrations:** Python SQLAlchemy ka schema migration engine jo Git commits ki tarah database schema versions ko track aur migrate karta hai (`alembic upgrade head`).


* **Angular Signals:** Angular 20 ka reactive primitive (`signal()`, `computed()`, `effect()`) jo fine-grained DOM updates enable karta hai bina poore tree ko dirty-check kiye.


* **Asynchronous Task Offloading:** Heavy CPU/IO tasks ko main FastAPI HTTP loop se hata kar background workers (Celery) ko सौंपna taaki response time $< 200\text{ ms}$ rahe.


* **Atomic Check-and-Increment:** Database engine par single query level par data evaluate aur increment karna taaki race conditions avoid hon (`UPDATE ... RETURNING`).



### C

* **Celery Workers:** Distributed background task queue workers jo Redis broker se jobs utha kar background mein AI parsing aur embeddings execute karte hain.


* **ChangeDetectionStrategy.OnPush:** Angular component rendering optimization jisme framework component ko tabhi re-render karta hai jab uske `@Input()` references change hon ya Signals fire hon.


* **Clean Architecture:** Inward dependency rule jisme domain business rules framework-independent rehte hain (`API Routers` $\rightarrow$ `Services` $\rightarrow$ `Domain Logic` $\leftarrow$ `Repositories`).


* **ContextVar:** Python ka thread-safe context-local storage primitive, jisse asynchronous pipeline ke andar request-level tenant context (`current_tenant_id`) safely pass hota hai.



### D

* **db_cleanup Fixture:** Pytest ka transactional truncate autouse fixture jo har individual test ke baad tables clean kar deta hai bina schemas drop kiye.


* **Dual-Token System:** Short-lived access token (15 mins) aur long-lived refresh token (7 days) ka secure combination.



### E

* **evict_user_permissions_cache:** Role-Based Access Control (RBAC) method jo role change hote hi Redis cache se user permissions ko dynamically invalidate karta hai.



### G

* **GSTIN (Goods and Services Tax Identification Number):** 15-character ka Indian tax identifier jo B2B invoicing aur CGST/SGST vs IGST calculation ke liye capture kiya jata hai.



### H

* **HttpOnly Cookie:** Browser storage flag jo JavaScript ko cookie read karne se block karta hai, jisse client-side XSS token theft impossible ho jata hai.



### K

* **Kanban Deal Pipeline:** Visual sales management board jisme drag-and-drop state changes optimistic UI pattern par execute hoti hain.



### M

* **Modular Monolith:** Single deployable codebase jisme feature domains strict package boundaries (`app/domain/{module}`) mein isolated rehte hain.



### N

* **NullPool:** SQLAlchemy testing engine configuration jo connection pooling ko disable karke har test ke baad database sockets physically close kar deta hai.



### O

* **Optimistic UI:** User action (jaise deal stage change) hote hi browser UI ko bina network response ka wait kiye update kar dena, aur API fail hone par previous state par rollback karna.



### P

* **pgvector:** PostgreSQL ka vector extension jo multi-dimensional floating-point embeddings store karta hai aur Cosine Distance / Inner Product similarity search chalata hai.


* **Playwright E2E:** Headless automated end-to-end browser testing framework jo real Angular form controls (`formControlName`) ko simulate karke UI verify karta hai.


* **Presigned Upload URLs:** Cloudflare R2 / S3 storage ke temporary cryptographic tokens jo client browser ko backend server bypass karke direct bucket par upload allow karte hain.



### R

* **RAG (Retrieval-Augmented Generation):** Custom tenant documentation se embeddings retrieve karke generative prompts ko factual context ke sath ground karna.


* **RBI e-Mandate Compliance:** Reserve Bank of India ka rule jiske tehat recurring subscriptions par AFA (Additional Factor of Authentication) enforce karne ke liye 3D Secure challenge session execute hota hai.


* **RS256 Algorithm:** Asymmetric cryptographic algorithm jisme 2048-bit Private Key token sign karti hai aur Public Key use verify karti hai.



### S

* **Soft Delete:** Records ko permanently database se drop karne ke bajay unka `deleted_at` timestamp set karke inactive mark karna.


* **Soft-Lock Policy:** Plan downgrade hone par data delete na karke, extra seat capacity hone par nayi write operations ko `HTTP 402 ERR_BILLING_001` ke sath freeze karna.


* **Standalone Components:** Angular components jo `NgModule` ke bina directly apne dependencies ko import karte hain.



### T

* **TenantContextMiddleware:** Custom ASGI FastAPI middleware jo JWT tokens aur `X-Organization-Id` headers ko intercept karke database session mein enforce karta hai.


* **TOCTOU (Time-Of-Check to Time-Of-Use):** Concurrency bug jisme check aur execution ke gap ke beech doosra concurrent user resource deplete kar deta hai.



---

## 2. End-to-End Application Lifecycle Skills Matrix

Neeche complete project lifecycle (Design $\rightarrow$ Development $\rightarrow$ Deployment $\rightarrow$ Testing) ke technical aur functional competencies ka map diya gaya hai:

### Phase A: Architecture, System Design & Modeling

* **Domain-Driven Design (DDD):** Clean Architecture boundaries banana taaki business logic database ya UI framework se independent rahe.


* **Multi-Tenant Isolation Design:** Free-tier limits ko dhyan mein rakhte hue row-level tenant separation model design karna jisme har query scoped rahe.


* **Schema Decoupling:** Subscription tiers (`FREE`, `PRO`, `ENTERPRISE`) ko billing status (`ACTIVE`, `TRIALING`, `PAST_DUE`, `CANCELED`) se separate entities mein architecture karna.


* **Zero-Cost Infra Topology:** Multi-cloud modern ecosystem (Render + Supabase + Upstash + Cloudflare R2 + Vercel) ka architectural alignment.



### Phase B: Backend API & Database Engineering

* **FastAPI Async Framework:** Asynchronous REST endpoints banana, Pydantic v2 schemas se request/response models ko strongly type karna, aur automatic OpenAPI documentation maintain karna.


* **SQLAlchemy 2.0 Async:** Purane `session.query()` syntax ko drop karke modern async syntax (`select()`, `scalars()`, `execute()`) aur repository-service design pattern implement karna.


* **Alembic Database Versioning:** Schema changes ko database migration scripts mein structure karna aur unke reversible rollbacks test karna (`upgrade head` / `downgrade -1`).


* **Threadpool Offloading:** Heavy synchronous external SDKs (jaise Stripe) ko non-blocking banaye rakhne ke liye `run_in_threadpool` ka use karna taaki async event loop choke na ho.



### Phase C: Zero-Trust Security & Cryptography

* **Asymmetric RS256 Auth:** Private/Public RSA keys ke zariye JWT signing aur authorization headers validation engine banana.


* **Secure Cookie Governance:** Refresh tokens ko `HttpOnly`, `SameSite=Strict`, aur `Secure` transport flags ke sath set karke XSS vulnerabilities ko eliminate karna.


* **Redis Stateful Session Management:** JWT stateless hone ke bawajood `sess:{user_id}:{token_id}` keys ke zariye instantaneous logout aur all-device invalidation implement karna.


* **Dynamic Permission Invalidation:** User RBAC permissions ko Redis mein 15-minute cache rakhna aur role change hone par cache-eviction hooks trigger karna.



### Phase D: FinTech, Concurrency & Indian Market Compliance

* **RBI Regulations & 3D Secure:** Auto-debit e-Mandates ke liye Stripe Checkout mein 3D Secure AFA challenges register karna.


* **Dynamic GST Invoicing:** Tenant GSTIN aur billing state ke hisab se CGST/SGST ya IGST (18% tax) dynamically apply karna.


* **Race Condition Defense:** Concurrency bugs se bachne ke liye application code ke bajay atomic database statements (`UPDATE organizations SET ai_credits_used = ai_credits_used + :cost ... RETURNING`) lagana.


* **3-State Distributed Webhook Lock:** Stripe webhooks mein payment duplicate charges aur out-of-order execution rokne ke liye short-lived Redis locks (`lock` $\rightarrow$ DB Transaction $\rightarrow$ `done`) banana.



### Phase E: AI Platforms & Distributed Background Processing

* **Universal AI Gateway:** Single integration boundary banana jo Gemini API SDKs aur prompts ko business features se decoupled rakhe.


* **Celery + Redis Task Queue:** AI chunking, document parsing aur quiz creation jaise heavy jobs ko background Celery workers ko handover karke frontend ko `202 Accepted` return karna.


* **pgvector Multi-Tenant Isolation:** Vector embeddings ko database mein tenant ID metadata ke sath store karna aur vector similarity search ko strictly tenant boundaries ke andar run karna.



### Phase F: Modern Frontend Engineering (Angular 20+)

* **Standalone Architecture:** Purane `NgModule` ko completely remove karke saare components ko `standalone: true` banana.


* **Signal-Driven State Management:** Heavy NgRx boilerplate ke bina `signal()`, `computed()`, aur `effect()` se clean local aur global UI reactive state manage karna.


* **ChangeDetectionStrategy.OnPush:** Har component par OnPush strategy enforce karke browser performance aur dirty checks optimize karna.


* **Functional Interceptors:** Outgoing HTTP calls par automatically Bearer tokens aur `X-Organization-Id` inject karne wale interceptors implement karna.


* **Route Guard Lifecycle Stabilization:** Onboarding ke waqt tokens sync karne aur AuthGuard race-conditions prevent karne ke liye hard navigation reload strategy lagana.



### Phase G: Automated Testing & Test Hygiene

* **Pytest Test Isolation:** Database connection pooling ko `NullPool` par rakh kar tests ke beech connections physically close karna taaki test poisoning eliminate ho.


* **Dynamic Table Truncation:** `db_cleanup` fixture banakar bina migration reset kiye fast table truncations execute karna.


* **Async External Mocking:** Third-party Gemini LLM calls ko `unittest.mock.AsyncMock` se intercept karke 100% deterministic test pass rate (39/39 passing) maintain karna.


* **Playwright E2E Automation:** Headless browsers par automated user conversion paths verify karna targeting real reactive form controls (`formControlName`).



### Phase H: Manual Quality Assurance & Security Pen-Testing

* **Cross-Tenant Attack Vectors:** Malicious `X-Organization-Id` inject karke `403 Forbidden` (`ERR_TENANT_001`) verify karna.


* **Boundary & Negative Testing:** Duplicate slugs par `409 Conflict`, regex failures par `422 Unprocessable`, aur fake signatures par `401 Unauthorized` test karna.


* **Soft-Lock Limit Verification:** Free tier mein 4th user add karke write actions par `HTTP 402 ERR_BILLING_001` trigger verify karna.



---