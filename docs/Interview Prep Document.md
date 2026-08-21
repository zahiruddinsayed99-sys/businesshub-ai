# Business Hub AI: Interview Prep Document

## 1. The Elevator Pitch (Explain in 1 Minute)

*When interviewer say: "Tell me about your portfolio project."*

**You say:**
"Business Hub AI is a multi-tenant B2B SaaS platform. It brings CRM, Training (LMS), and Billing into one place. I built it to show how AI can help daily business work. The frontend is built in Angular. It uses strict route guards and role-based access. The backend uses a RAG (Retrieval-Augmented Generation) pipeline to read company documents and uses AI to score sales deals and generate training quizzes. I also built a Stripe billing interceptor to lock the app if a company runs out of AI credits."

## 2. Tech Stack (What You Used)

Memorize this list.

* **Frontend:** Angular, RxJS (for state), HTTP Interceptors.
* **Backend:** API architecture, JWT Auth.
* **Database:** PostgreSQL with `pgvector` (for AI search).
* **AI:** RAG pipeline, Embedding models, LLM (Large Language Model).
* **Payments:** Stripe Customer Portal.

---

## 3. Top Interview Questions & Simple Answers

### Frontend Questions

**Q: How did you secure the frontend for different users?**
**Your Answer:**
"I used Role-Based Access Control (RBAC). When user logs in, I read their role from the JWT token. I use Angular Route Guards like `AdminGuard` to stop normal workers from opening the Settings or Billing URLs. I also use `*ngIf` in the HTML to hide the admin links in the side menu."

**Q: How do you handle API errors if a user runs out of money?**
**Your Answer:**
"I built a global HTTP Interceptor. If the backend sends a `402 Payment Required` error, my interceptor catches it before the UI breaks. It freezes the screen, shows a warning modal, and forces the user to the `/billing` page."

**Q: How did you handle long AI wait times?**
**Your Answer:**
"When the AI generates a quiz, it takes time. I did not want the screen to freeze. I built a polling system. The frontend asks the backend for updates, and I show a progress bar to the user so they know the system is working."

### Backend & AI Questions

**Q: Explain how your RAG document search works.**
**Your Answer:**
"First, I extract text from uploaded documents. I break the text into small pieces called 'chunks'. I pass chunks through an embedding model to turn them into number vectors. I save vectors in `pgvector`. When a user asks a question, I turn the question into a vector, find the closest document chunks in the database, and send them to the LLM to write the final answer."

**Q: Multi-tenant apps are hard. How did you keep company data separate?**
**Your Answer:**
"Strict data isolation. Every row in my database, and every AI vector chunk, has an `organization_id`. When a user queries the database, I force a hard filter: `WHERE org_id = user.org_id`. Tenant A can never see Tenant B data."

---

## 4. How to Talk About Challenges (The STAR Method)

Interviewers always ask: *"What was hard?"* Use this story.

**The Situation:** I needed to build AI lead scoring and AI quiz generation, but AI costs money.
**The Task:** I had to protect my API so free-tier users do not bankrupt my project.
**The Action:** I built a Stripe billing guard. The backend checks AI credits before every AI call. If credits are zero, backend throws `402`. The frontend interceptor catches this and routes to Stripe portal.
**The Result:** The app is completely safe. Zero credit over-use. The user experience is smooth because the UI explains why they are locked out.

---
