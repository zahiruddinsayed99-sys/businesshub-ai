Here is a beginner-friendly onboarding guide designed specifically for junior developers joining your team. It explains the entire product, how each piece connects, and the core frontend concepts they need to know to write code on day one.

---

# 🚀 Junior Developer Onboarding Guide: Business Hub AI

Welcome to the team! This document explains what **Business Hub AI** is, how the entire system works under the hood, and how we write code for it.

---

## 1. What is Business Hub AI? (The Plain English Summary)

Think of **Business Hub AI** as an all-in-one workspace for companies:

* Sales reps use it to track deals (**CRM**).
* Employees use it to read training manuals and take tests (**LMS**).
* Managers use built-in **AI** to score sales leads, search internal company documents, and automatically write quiz questions.
* We charge money for it using **Stripe** subscriptions.

---

## 2. System Architecture: How the Whole App Fits Together

Here is a visual map of how data moves from a user's click all the way to the database and AI models:

```text
  [ User Browser / Chrome ]
            │
            ▼ (1. Clicks a button)
┌─────────────────────────────────────────────────────────────┐
│                    ANGULAR FRONTEND                         │
│  - Checks who you are (Route Guards)                        │
│  - Attaches your security pass to requests (Interceptor)    │
│  - Displays screens: Login, CRM, Training, Settings         │
└───────────────────────────┬─────────────────────────────────┘
                            │ (2. Sends API request over the web)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND API                            │
│  - Checks passwords and creates tokens (Auth Service)       │
│  - Makes sure Company A never sees Company B's data (Tenant)│
│  - Checks if user paid their subscription (Billing)         │
└─────────────┬─────────────────┬────────────────────┬────────┘
              │                 │                    │
              ▼                 ▼                    ▼
     [ PostgreSQL DB ]   [ Redis Cache ]     [ AI Engine ]
     Stores regular      Stores fast,        Reads documents &
     tables (deals,      temporary data      generates smart
     users, courses)     (active sessions)   quiz questions

```

---

## 3. The 4 Main Modules & How We Built Them

### 🔑 Module 1: Auth & User Permissions (Who can see what?)

* **The Business Goal:** Stop random people from seeing private company data. Normal employees should not see company billing or settings.
* **How We Build It on Frontend:**
* **JWT Token (The Digital Badge):** When a user logs in, the backend sends back an encrypted string called an `access_token`. We save this in browser storage.
* **HTTP Interceptor:** A piece of code that runs silently before *every* API call. It automatically adds the user's `access_token` and `Organization-ID` into the request header. You don't have to type it manually in every service.
* **Route Guards (`AdminGuard`):** If a regular worker types `http://localhost:4200/billing` directly into their browser address bar, the route guard intercepts them, cancels the page load, and kicks them back to the `/crm` dashboard.



---

### 💼 Module 2: CRM Sales Pipeline (Tracking deals)

* **The Business Goal:** Give sales reps a drag-and-drop board to track potential customers and use AI to predict which deals will close.
* **How We Build It on Frontend:**
* **Kanban Board:** Displays deals organized in columns (e.g., *New lead* $\rightarrow$ *Contacted* $\rightarrow$ *Won/Lost*).
* **AI Deal Scoring:** When a user clicks **"AI Score Deal"**, the frontend sends a `POST` request to the backend. The AI analyzes deal details and returns a win probability percentage that updates the card on screen.



---

### 📚 Module 3: LMS Learning System (Training employees)

* **The Business Goal:** Managers write training manuals, and the AI automatically turns those manuals into 5-question quizzes for workers.
* **How We Build It on Frontend:**
* **Markdown Editor:** A clean text box where managers format lessons using headings and bullet points.
* **Polling (No Frozen Screens):** AI generation takes 3 to 6 seconds. Instead of making the screen freeze, the frontend shows a progress bar and asks the backend every 2 seconds: *"Is the quiz ready yet?"* (This is called **Polling**).
* **The 80% Rule:** When an employee finishes a quiz, our frontend checks the score. It strictly shows a green **PASS** only if they get 80% or higher (at least 4 out of 5 correct).



---

### 💳 Module 4: Billing Guard (Protecting cloud costs)

* **The Business Goal:** AI API calls cost money. If a company runs out of credits or stops paying, the app must freeze write actions automatically.
* **How We Build It on Frontend:**
* **Catching Error `402`:** If a user with 0 credits tries to click an AI button, the backend returns an HTTP status code `402 Payment Required`.
* **The Global Soft-Lock:** Our global interceptor catches this `402` error, pops up an alert saying *"Workspace limit reached"*, and immediately redirects the user to `/billing`.
* **Stripe Integration:** The billing screen has a button that opens a secure Stripe billing portal where the customer can update their payment card.



---

## 4. Junior Dev Cheat Sheet: Key Terms to Know

| Term | What it means in simple words |
| --- | --- |
| **Multi-Tenancy** | One software instance serving multiple different companies while keeping their data completely isolated from each other. |
| **HTTP Interceptor** | A helper that grabs every outgoing API request and automatically injects authentication headers or catches global errors. |
| **Route Guard** | A security bouncer in Angular that decides whether a user is allowed to navigate to a specific URL. |
| **Polling** | Repeatedly pinging the server on a timer (e.g., every 2 seconds) to check if a long background job is done. |
| **JWT (JSON Web Token)** | A secure, encrypted string that proves who the user is after they log in. |

---

## 5. First Day Assignment for New Devs

1. Clone the repository and run `npm install`.
2. Run `npm start` and open `http://localhost:4200/login`.
3. Open Chrome DevTools (`F12`), click the **Network** tab, and log in.
4. Watch the login API request return the `access_token` and inspect how subsequent requests automatically carry that token in the headers.
5. ---
6. ## Onboard version 2
7. Here is the complete, text-only documentation for your portfolio. This is designed so you can print it, study it offline, and hand it to an interviewer to prove you understand how to build a full, saleable software product from start to finish.

---

# Business Hub AI: Product & Architecture Showcase

## 1. System Architecture Diagram & Summary

### The Big Picture (Summary)

**Business Hub AI** is a multi-tenant B2B SaaS (Software as a Service) platform. It is designed to replace multiple disconnected tools by combining a Sales CRM, an Employee Training System (LMS), and AI Assistant tools into one secure workspace.

As a saleable product, it is built with enterprise-grade architecture: it keeps different companies' data completely separate (multi-tenancy), protects revenue with automated billing guards, and uses AI (Retrieval-Augmented Generation) to automate heavy business tasks safely.

### Text-Based Architecture Diagram (Offline View)

```text
[ USER BROWSER ] 
       │
       ▼ (HTTP Requests & Angular Interceptors)
┌────────────────────────────────────────────────────────┐
│               FRONTEND (Angular 18+)                   │
│  - Route Guards (Role-Based Access)                    │
│  - State Management (RxJS)                             │
│  - Modules: Auth, CRM, LMS, Admin, Billing             │
└──────────────────────────┬─────────────────────────────┘
                           │ (JWT Auth Token + Org ID Header)
                           ▼
┌────────────────────────────────────────────────────────┐
│                BACKEND API (REST)                      │
│  - Auth Service (Login, JWT, Sessions)                 │
│  - Tenant Service (Multi-tenant data isolation)        │
│  - Billing Service (Stripe Integration)                │
└────────┬─────────────────┬────────────────────┬────────┘
         │                 │                    │
         ▼                 ▼                    ▼
[ POSTGRESQL DB ]    [ REDIS CACHE ]      [ AI / RAG ENGINE ]
- Users & Roles      - User Sessions      - Document Chunking
- CRM Deals          - API Rate Limits    - Embedding Models
- LMS Courses        - Quiz Polling       - LLM Generation
- Vector Data (pgvector)

```

---

## 2. Feature-Wise Explanation & Tech Implementation

When you talk to an interviewer, explain the **Product Value** (why a customer buys it) first, then explain the **Tech Implementation** (how you built it).

### Feature 1: Secure Workspace Setup & Team Access

* **Product Value:** Companies need a secure way to sign up, pay, and invite their workers without IT help. The system must ensure normal workers cannot see admin settings or billing pages.
* **Tech Implementation:**
* **Authentication:** I built a secure login system using JWT (JSON Web Tokens). When a user logs in, the token is saved securely in the browser.
* **HTTP Interceptor:** I wrote an Angular Interceptor that automatically attaches the user's Token and `Organization-ID` to every API request so the backend knows exactly who is asking for data.
* **UI Security (RBAC):** I implemented Role-Based Access Control. I created an `AdminGuard` in Angular's router. If a standard worker tries to type `/billing` or `/settings` into the URL, the guard blocks them and kicks them back to the main dashboard.



### Feature 2: AI-Powered CRM (Sales Pipeline)

* **Product Value:** Sales teams waste time guessing which customers are likely to buy. This CRM uses AI to instantly score deals and tell the sales rep where to focus their time.
* **Tech Implementation:**
* **Dynamic UI:** I built a visual Kanban board for tracking deals using Angular.
* **AI Integration:** I added an "AI Score Deal" action. When clicked, it calls a backend API (`POST /api/v1/crm/deals/{id}/ai-score`). The AI looks at the deal data, calculates a win probability, and the UI updates the deal card in real-time.



### Feature 3: Smart LMS (Learning Management System)

* **Product Value:** Managers hate writing training quizzes. In this app, a manager just types the training manual, and the AI automatically reads it and generates a passing-grade quiz for the employees.
* **Tech Implementation:**
* **Content Editor:** I integrated a Markdown text editor for managers to write lessons.
* **AI Polling:** Because AI takes a few seconds to generate a quiz, the browser cannot just "hang." I implemented a polling system. The frontend asks the backend "Is it done yet?" every 2 seconds while showing a progress bar, keeping the UI smooth.
* **Business Rules Engine:** I hardcoded a strict grading rule on the frontend. When a student submits a quiz, the system calculates the score. The UI will only render a green "PASS" if the score is 80% or higher.



### Feature 4: Financial Protections (The Billing Guard)

* **Product Value:** AI costs me money every time a user clicks it. The product must automatically stop users from using the app if they run out of AI credits or their free trial ends, without me having to watch it manually.
* **Tech Implementation:**
* **Global Error Catching:** I built a global error handler in the frontend.
* **The Soft-Lock:** If the backend realizes a user is out of credits, it sends back a specific HTTP error: `402 Payment Required`. My Angular interceptor catches this exact error, instantly freezes whatever the user is doing, shows a "Workspace Locked" warning, and forces the browser to route to the `/billing` page.
* **Stripe Portal:** On the billing page, a button calls an API to generate a secure Stripe Customer Portal link, allowing the user to put in their credit card to unlock their account.



---

### How to use this in an interview:

If the interviewer asks, *"Are you a frontend or full-stack developer?"*
You point to this document and say: *"I specialize in frontend, but I understand the entire product lifecycle. I don't just build buttons; I build features that connect to databases, protect cloud costs, and solve real business problems."*
