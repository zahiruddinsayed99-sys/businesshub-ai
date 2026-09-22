# 03_Indian_Business_Case_Studies_and_Functional_Specs.md

# BusinessHub AI: Indian Business Case Studies, Domain Workflows aur Functional Specifications

> **Document Classification:** Functional Architecture, Indian Regulatory Specs & Domain Workflows
> 
> 
> **Applicable Markets:** India B2B SaaS, MSME Digitization, Enterprise Compliance
> 
> 

---

## 1. Domain Business Rules Engine (Validation Engine)

BusinessHub AI ke architecture mein business logic code aur database integrity ko enforce karne ke liye strict validation rules define kiye gaye hain:

### 1.1 Platform-Wide Rules

* **BR-PLT-001 (Row-Level Multi-Tenant Isolation):**
Har API call, SQL select/insert/update/delete query, Redis cache lookup, aur Cloudflare R2 file storage path mein `organization_id` mandatory hai. Kisi bhi request mein agar `X-Organization-Id` missing ho ya token holder kisi doosri company ka data access karne ki koshish kare, toh system turant **HTTP 403 Forbidden (`ERR_TENANT_001`)** throw karta hai.


* **BR-PLT-002 (Subscription Limits & Atomic Metering):**
Free Tier organizations par strict boundary hai: **1 Workspace**, **Maximum 3 Active Users**, aur **100 AI Execution Credits per month**. Application-level check ke bajay database-level atomic statement run hoti hai. Agar limits exceed ho jayein, toh API task discard karke **HTTP 402 Payment Required (`ERR_BILLING_001`)** return karti hai.


* **BR-PLT-003 (Immutable Audit Integrity):**
Koi bhi state-changing transaction (`POST`, `PUT`, `PATCH`, `DELETE`) database table `audit_logs` mein ek immutable record insert karti hai jisme `user_id`, `organization_id`, `ip_address`, `action`, `resource`, aur `delta_json` store hota hai.



### 1.2 CRM Domain Rules

* **BR-CRM-001 (Strict Deal State Machine):**
Sales rep kisi bhi Deal ko `LEAD` ya `QUALIFIED` se directly `CLOSED_WON` mein nahi le ja sakta. Deal ko win mark karne se pehle pipeline mein kam se kam ek **Proposal Sent** activity log physically exist karna mandatory hai.


* **BR-CRM-002 (INR Currency Constraint):**
Indian B2B operations ko dhyan mein rakhte hue har deal ki base valuation currency **INR** mein validate hoti hai.



### 1.3 LMS Domain Rules

* **BR-LMS-001 (80% Passing Criteria for Certification):**
LMS module ke andar course completion certificate tabhi unlock aur generate hota hai jab learner ka aggregate AI quiz score **$\ge 80\%$** ho. $80\%$ se kam aane par status `FAILED` rehta hai aur certificate endpoint access block rehta hai.


* **BR-LMS-002 (Authoring Role Restriction):**
Courses, modules, lessons create karna aur AI quizzes generate karna strictly administrative roles (`TENANT_OWNER`, `TENANT_ADMIN`, `LMS_MANAGER`) ke liye reserved hai. Normal `DOMAIN_MEMBER` ko create call par **HTTP 403 Forbidden (`ERR_RBAC_001`)** milta hai.



---

## 2. Indian B2B Case Studies (Real-World Scenarios)

---

### Case Study 1: Central AI Platform (Enterprise RAG & Knowledge Engine)

* **Target Enterprise:** **"PrimeTech B2B Consulting"** (Shivajinagar, Pune, Maharashtra)
* **Company Profile:** Ek tier-2 business consulting firm jo manufacturing MSMEs ko company law, labour laws, ISO audits, aur Indian GST guidelines par advisory deti hai.
* **Core Business Problem:**
Firm ke paas 500+ pages ke complex internal SOPs, GST circulars aur vendor audit guidelines the. Associates ko specific compliance clause dhoondhne mein ghanto lag jate the, jisse client turnaround time (TAT) slow hota tha.
* **BusinessHub AI Implementation:**
1. Firm ne **Centralized AI Gateway** ka RAG ingestion feature use kiya.


2. Cloudflare R2 par secure presigned URL ke through internal legal PDFs direct browser se upload kiye gaye.


3. Celery asynchronous background workers ne files ko extract kiya, text chunks banaye, aur Gemini embeddings model se vectors generate karke PostgreSQL ke **pgvector** extension mein save kiya.


4. Har chunk ke sath `organization_id` tag hone ki wajah se zero-data leakage enforce hua.




* **Day-to-Day User Workflow:**
Consultant simple query type karta hai: *"What is the deadline for filing GSTR-3B under QRMP scheme?"*
System internally vector similarity search chalata hai (strictly tenant scope ke andar) aur grounded answer generate karke cite karta hai.


* **Economic & Business Value Achieved:**
* Document retrieval TAT 45 minutes se ghat kar **under 2 seconds** ho gaya.
* Research overhead mein 85% reduction mila.
* Atomic credit metering ensure karti hai ki concurrent queries run hone par credit leakage na ho.





---

### Case Study 2: CRM Sales Engine (B2B Solar EPC Pipeline)

* **Target Enterprise:** **"Bharat Solar Tech Solutions"** (Sarkhej, Ahmedabad, Gujarat)
* **Company Profile:** Commercial aur industrial units ke liye rooftop solar plants install karne wali engineering, procurement and construction (EPC) company.
* **Core Business Problem:**
Deals ki valuation badi hoti hai (₹10 Lakhs se ₹1 Crore+), sales cycles 3 se 6 mahine chalte hain, aur multiple follow-ups lagte hain. Local reps updates excel files mein rakhte the jisse high-ticket leads drop ho jati thi.
* **BusinessHub AI Implementation:**
1. Bharat Solar ne **Interactive Kanban Deal Pipeline** deploy kiya.


2. Deals ko standard INR valuation aur stages (`LEAD` $\rightarrow$ `QUALIFIED` $\rightarrow$ `PROPOSAL` $\rightarrow$ `CLOSED_WON` / `CLOSED_LOST`) mein structure kiya gaya.


3. **BR-CRM-001** lagne se koi bhi sales rep bina proposal document upload kiye deal ko Won mark nahi kar sakta tha, jisse fake closure reporting band ho gayi.


4. **AI Lead Scoring Copilot:** Rep single click par customer notes aur meeting transcripts AI ko feed karta hai. System 4 credits deduct karke 0–100 ka intent score nikalta hai.


5. **AI Draft Follow-up Generator:** Meeting ke baad client requirement ke hisab se Indian business format mein follow-up email draft ho jati hai.




* **Front-End Architecture Experience:**
Angular 20 ke Signals aur `ChangeDetectionStrategy.OnPush` ke sath **Optimistic UI** chalne ki wajah se jab rep deal ko `LEAD` se `QUALIFIED` column mein drag karta hai, toh card turant drop ho jata hai bina browser wait kiye.


* **Economic & Business Value Achieved:**
* Sales pipeline conversion rate mein 32% ka jump aaya.
* Proposal-to-close cycle time 18 din kam ho gaya.



---

### Case Study 3: LMS Module (Regulatory Training & Employee Compliance)

* **Target Enterprise:** **"Namaste FinServ Private Limited"** (Koramangala, Bengaluru, Karnataka)
* **Company Profile:** Ek digital lending NBFC jiske 150+ loan officers field aur remote locations par kaam karte hain.
* **Core Business Problem:**
Reserve Bank of India (RBI) ke Fair Practices Code, Anti-Money Laundering (AML), aur KYC verification guidelines par har naye employee ko train karna aur compliance record maintain karna mandatory audit requirement hai. Manual physical tests conduct karna slow aur expensive tha.
* **BusinessHub AI Implementation:**
1. HR Admin (`LMS_MANAGER` role) ne BusinessHub LMS mein compliance course structure kiya.


2. **AI Quiz Generator:** Admin ne RBI AML circulars ka markdown content upload karke "Generate Quiz" trigger kiya.


3. System ne atomically 10 credits deduct kiye aur Celery worker ke zariye 5 tough MCQ questions ka evaluation set create kar diya.


4. Field officers ne mobile/desktop par Markdown lessons padhe aur quiz attempt kiya.


5. **BR-LMS-001 Enforcement:** Jab employee 5 mein se kam se kam 4 questions sahi karta hai ($\ge 80\%$), tabhi backend verification certificate release karta hai.




* **Economic & Business Value Achieved:**
* Naye field officers ki onboarding 2 hafte se ghat kar **3 din** mein complete hone lagi.
* 100% compliance audit trail available hua jisse RBI non-compliance penalties ka risk zero ho gaya.



---

## 3. Indian FinTech & Regulatory Implementation Specifications

### 3.1 INR Pricing & RBI e-Mandate Pipeline

Indian market ke SaaS platforms ko international recurring billing model chalane ke liye Reserve Bank of India ke mandates follow karne padte hain:

* **3D Secure (AFA Challenge):** Stripe Checkout sessions create karte waqt mandate registration ke liye 3DS enforce kiya gaya hai. User ka issuing bank (HDFC, ICICI, SBI) pehle payment aur mandate registration ke liye OTP challenge display karta hai.


* **Currency Lock:** Product catalog mein saari pricing INR base currency par locked hai.



### 3.2 18% GST B2B Invoicing Automation

* **Data Capture:** `organizations` table mein `gstin` (15-character alphanumeric regex `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`) aur `billing_state` store hota hai.


* **Tax Splitting Rules:**
* **Intra-State (Agar Seller State == Buyer State):** 9% CGST + 9% SGST apply hota hai.


* **Inter-State (Agar Seller State != Buyer State):** 18% IGST apply hota hai.




* Invoices par input tax credit (ITC) claim karne ke liye client ka verified GSTIN aur address render hota hai.



### 3.3 Soft-Lock Overage Policy Specification

Jab ek tenant paid PRO plan se FREE plan par downgrade karta hai, toh platform destructive behavior (data deletion) nahi apnata:

* Free tier user limit = 3 seats.


* Downgrade par agar tenant ke 5 users active hain, toh `check_soft_lock_overage` trigger hota hai.


* **System Behavior:**
* Read permissions (`GET` endpoints, dashboards, reports) poori tarah accessible rehti hain.


* Naye user invitations, nayi CRM deals add karna, ya AI tasks chalana block ho jata hai with **HTTP 402 Payment Required (`ERR_BILLING_001`)**.


* Jaise hi Tenant Admin 2 extra members ko remove karta hai aur active count $\le 3$ ho jata hai, write lock automatically release ho jata hai.





---