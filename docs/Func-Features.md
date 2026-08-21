Namaste! Yahan aapke diye gaye document ka ek friendly Hinglish translation hai:

# **BusinessHub AI: Detailed Functional Features Specification**

Yeh specification BusinessHub AI platform ke paanch primary modules ke business-facing workflows, operational capabilities, aur governance models ko outline karta hai. Yeh strictly user-facing capabilities, business logic, aur organizational workflows par focus karta hai, aur kisi bhi underlying codebase structures ya database architectures ko ignore karta hai.

---

### **1. Core Platform & Workspace Access**

* **Module Overview:**
Yeh ek secure, multi-tenant entry point ki tarah kaam karta hai jo business entities ko structured organizational boundaries ke andar isolated virtual workspaces register, bootstrap, aur manage karne ki permission deta hai.
* **Key Functional Features:**
* **Self-Service Workspace Registration:** Nayi business entities apni company ko register kar sakti hain ek unique, customized tenant slug select karke jo unke workspace URL ko represent karta hai.
* **Dynamic Slug Verification:** Registration ke time, platform dynamically validate karta hai ki chuna gaya workspace slug available hai ya nahi, jisse yeh ensure hota hai ki businesses ke beech koi URL conflicts na hon.
* **Automated Tenant Bootstrapping:** Successful registration hone par, system automatically tenant workspace ko provision karta hai, core access configurations ko hook up karta hai, aur registrant ko primary workspace administrator designate kar deta hai.
* **Stateful Multi-Device Sessions:** Active logins 7 dino tak verified rehte hain, aur inme aisi security controls hoti hain jo user ke password change karne par sabhi active devices se sessions ko automatically revoke kar deti hain.
* **Granular Permission Evaluations:** Yeh system actions ko dynamically restrict karta hai, aur yeh validate karta hai ki specific modules display karne ya unse interact karne ki permission dene se pehle users ke paas necessary scopes hain ya nahi.


* **User Roles & Permissions:**
* **Tenant Owner / Admin:** Inke paas full workspace override privileges hoti hain, jisme user seats manage karna, partners ko invite karna, aur company settings modify karna shamil hai.
* **Domain Member / Standard User:** Inhe assigned workspaces aur modules ko access karne ki authority hoti hai, lekin ye tenant-wide administrative configurations perform nahi kar sakte.



---

### **2. Multi-Tenant Billing & Indian Financial Compliance**

* **Module Overview:**
Yeh module customer subscription tiers, billing checkouts, aur invoicing portals ko manage karta hai, aur sath hi Indian market ke liye strict regulatory tax aur auto-debit compliance standards ko enforce karta hai.
* **Key Functional Features:**
* **Tiered Subscription Management:** Yeh Free, Pro, aur Enterprise subscription tiers ko support karta hai, jisme Free tier workspaces ko maximum 3 active user seats aur 100 monthly AI credits tak restrict karta hai.
* **Self-Service Billing Portal:** Tenant Owners ek dedicated subscription portal access kar sakte hain jahan wo apna active plan dekh sakte hain, historical invoices retrieve kar sakte hain, aur upgrades ya downgrades khud manage kar sakte hain.
* **INR Price Locking:** Yeh sabhi checkouts aur subscription prices ko strictly Indian Rupees (INR) mein lock karta hai, taki exchange rate fluctuations aur processing issues ko eliminate kiya ja sake.
* **RBI e-Mandate Authentication:** Yeh checkout setup ke time multi-factor card challenges (3D Secure) enforce karta hai taki reserve bank ki guidelines ke according recurring payment mandates register kiye ja sakein.
* **B2B GST Tax Invoicing:** Yeh 15-character corporate GSTIN numbers aur Billing States capture karta hai jisse intra-state (CGST + SGST) aur inter-state (IGST) taxations dynamically determine hote hain, aur Input Tax Credit (ITC) claims ke liye compliant tax invoices generate hote hain.
* **Write-Lock Overage Policy:** Agar koi company apna plan downgrade karti hai, toh existing workspace data strictly readable rehta hai (koi hard deletions nahi hote). Lekin, agar current user seat count naye tier ki limits se zyada ho jata hai (jaise Free plan par >3 active users), toh workspace ek soft-lock state mein chala jata hai—jisse write operations aur invitations freeze ho jate hain jab tak seat count kam na kiya jaye ya subscription upgrade na kiya jaye.


* **User Roles & Permissions:**
* **Tenant Owner:** Sirf inke paas financial records dekhne, company tax identifiers input karne, active subscription tiers change karne, aur external payment customer portal access karne ki exclusive authority hoti hai.



---

### **3. Collaborative CRM Pipeline**

* **Module Overview:**
Yeh sales teams ko visual pipelines ke through business opportunities ko organize, assign, aur transition karne ki suvidha deta hai, jisse isolated tenant environments ke andar collaboration aasan ho jata hai.
* **Key Functional Features:**
* **Interactive Kanban Board:** Yeh deal flows ko paanch primary pipeline stages (`LEAD`, `QUALIFIED`, `PROPOSAL`, `WON`, aur `LOST`) mein visualize karta hai, jisse users responsive drag-and-drop actions ke zariye deal cards move kar sakte hain.
* **Contact Directory Management:** Yeh standard customer contact details (names, emails, phone numbers) ko track karta hai aur unhe directly pipeline mein active deals ke sath link karta hai.
* **Deal Ownership & Allocation:** Deals ko specific team members ko assign kiya ja sakta hai taki operational responsibility track ki ja sake.
* **Secure Team Invitations:** Administrators external employees ya partners ko secure registration tokens use karke organization mein standard members ki tarah join karne ke liye invite kar sakte hain. Yeh tokens 48 hours ke baad automatically expire ho jate hain.
* **Optimistic UI Handlers:** Yeh drag-and-drop card movements ko screen par turant reflect karta hai taki zero-latency feel aaye, aur connection failure ya security block hone par card ko automatically uske starting column mein wapas bhej kar user ko notify kar deta hai.


* **User Roles & Permissions:**
* **Tenant Owner / Admin / Domain Manager:** Inhe system mein sabhi contacts aur deals par full creation, modification, aur deletion access milta hai, aur team invitation tokens generate karne ka inke paas exclusive right hota hai.
* **Domain Member / Standard User:** Yeh workspace ke andar sabhi active deals dekh sakte hain, lekin sirf unhi opportunities ko modify kar sakte hain jo directly unhe assign ki gayi hain. CRM resources ko delete karne ki permission inhe bilkul nahi hoti hai.



---

### **4. Centralised Enterprise AI Platform**

* **Module Overview:**
Yeh artificial intelligence workflows ke liye ek secure gateway provide karta hai, jo sabhi company modules mein document ingestion, context-grounded searches, aur automated pipeline scoring ko manage karta hai.
* **Key Functional Features:**
* **Structured AI Template Gateway:** Yeh sabhi model prompts aur interactions ko centralize karta hai taki consistent outputs ki guarantee di ja sake aur direct, unmonitored model connections ko roka ja sake.
* **Universal Document RAG:** Users corporate documents (PDF, Markdown, text) upload kar sakte hain jisse ek on-demand, contextually grounded knowledge base banaya ja sake.
* **Cross-Tenant Knowledge Isolation:** Yeh sabhi semantic vector searches par strict boundary checks enforce karta hai, jisse ensure hota hai ki users sirf apne active workspace se judi information hi query kar payein.
* **Asynchronous Background Ingestion:** Yeh heavy document parsing aur indexing tasks ko background processes par offload karta hai, aur frontend par real-time task progress bars (jaise "Pending" se "Success") display karta hai.
* **CRM Lead Scoring Copilot:** Yeh pipeline records, customer histories, aur associated sales notes ko analyze karta hai taki automatically Lead Score (0–100) calculate kiya ja sake aur structured intent signals extract kiye ja sakein.
* **Draft Follow-Up Generator:** Yeh past deal history par based automatically context-grounded, professional draft emails generate karta hai, jinme native INR pricing details format hoti hain aur copy-to-clipboard actions available hote hain.


* **User Roles & Permissions:**
* **Tenant Owner / Admin / Domain Manager:** Inhe corporate knowledge base files upload karne, semantic RAG queries run karne, aur AI assessments trigger karne ki authority hoti hai.
* **Domain Member / Standard User:** Yeh central files ko upload ya modify nahi kar sakte, lekin inhe un deals par copilot tasks (jaise follow-up emails generate karna) run karne ki permission hoti hai jo unhe assign ki gayi hain.



---

### **5. AI-Powered Learning & Enablement (LMS Engine)**

* **Module Overview:**
Yeh core CRM ko support karne wale ek AI-powered enablement module ki tarah kaam karta hai, jo staff training, curriculum authoring, aur automated skill assessments ki suvidha deta hai.
* **Key Functional Features:**
* **Course & Curriculum Authoring:** Course managers poore enablement programs construct kar sakte hain, jisme materials ko structured aur sortable modules mein organize kiya jata hai.
* **Markdown Lesson Player:** Isme ek responsive player integrated hai jo formatted Markdown lessons, code blocks, checklists, aur video links display karta hai.
* **Learner Enrollment workflows:** Eligible workspace employees active courses mein khud enroll kar sakte hain taki wo apni speed se training complete kar sakein.
* **Progress Tracking & Completion:** Yeh individual lesson progression ko log karta hai, aur final lesson complete mark hone par automatically overall enrollment status ko "Completed" resolve kar deta hai.
* **Structured Quiz Assessments:** Yeh multiple-choice lesson quizzes ko support karta hai, attempts ko automatically score karta hai aur strict course completion standards enforce karta hai (jisme $\ge 80\%$ ka passing score chahiye hota hai).
* **AI Quiz Generator:** Yeh Markdown lesson content se directly 5-question multiple-choice quizzes generate karta hai taki comprehension ko automatically test kiya ja sake.
* **Pre-Flight Cost Guard:** AI quiz requests asynchronously process hoti hain. Company credits ko bachane ke liye, system plan statuses verify karta hai aur model calls activate hone se *pehle* exactly 10 AI Credits atomically deduct karta hai. Agar tenant ka balance khatam ho gaya ho ya workspace overage soft-lock mein ho, toh yeh generation ko turant rok deta hai.


* **User Roles & Permissions:**
* **LMS Manager / Tenant Owner / Admin:** Inhe courses design aur edit karne, lesson modules compile karne, curricula publish karne, aur AI quiz generator trigger karne ki authority hoti hai.
* **Domain Member / Standard User:** Yeh published courses mein self-enroll karne, lessons padhne, personal progress track karne, aur training rules meet karne ke liye quizzes lene ke liye authorized hote hain.



---

📊 Main is functional features specification ko aapke Studio panel mein ek badhiya, presentation-ready slide deck ke roop mein compile kar sakta hoon, jisse aap in 5 modules ka scope apne business stakeholders ko easily present kar sakein. Kya aapke liye yeh helpful rahega?
