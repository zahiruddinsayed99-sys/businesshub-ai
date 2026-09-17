Here is your beginner-friendly, step-by-step master plan to take BusinessHub AI live on a staging environment using **Supabase** (Database), **Render or Railway** (Backend & Redis), and **Vercel** (Frontend).

---

## Phase 1: Database Setup (Supabase)

*Supabase gives you a free PostgreSQL database with `pgvector` built-in, so your RAG document embedding features will work right out of the box.*

1. **Create Account & Project:** Go to [Supabase](https://www.google.com/search?q=https://supabase.com), log in, and create a new project. Give it a name and secure database password (save this password!).
2. **Enable Vector Extension:**
* In your Supabase dashboard sidebar, click on **SQL Editor**.
* Run this quick command:
```sql
create extension if not exists vector;

```




3. **Get Your Connection String:**
* Go to **Project Settings** (gear icon) -> **Database**.
* Copy the **URI** connection string. It will look like `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`.



---

## Phase 2: Backend & Redis Setup (Render)

*Render is beginner-friendly and handles both your FastAPI backend and a Redis instance cleanly.*

1. **Deploy Redis:**
* Go to [Render](https://www.google.com/search?q=https://render.com) and click **New+** -> **Redis**.
* Name your instance (e.g., `businesshub-redis`), choose the free/hobby tier, and click **Create Redis**. Once active, copy its **Internal/External Redis URL**.


2. **Deploy FastAPI Backend:**
* Click **New+** -> **Web Service** and connect your GitHub repository.
* Configure the service:
* **Root Directory:** `backend`
* **Environment:** Python 3
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`


* **Add Environment Variables** under the settings tab:
* `DATABASE_URL`: Change your Supabase URI to start with async driver syntax: `postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
* `REDIS_URL`: Paste the Redis URL you copied from Render.
* `TESTING`: `False` (since this is staging/production).




3. **Run Migrations:**
* Once your backend service builds successfully, use Render's **Shell** feature (or run Alembic locally targeting the Supabase URL once) to execute your database migrations:
```bash
alembic upgrade head

```




4. **Save your Backend URL:** Once deployed, Render will give you a live URL (e.g., `[https://businesshub-backend.onrender.com](https://businesshub-backend.onrender.com)`). Keep this handy!

---

## Phase 3: Frontend Setup (Vercel)

*Vercel is the easiest place to host modern Angular applications with zero configuration hassle.*

1. **Import to Vercel:** Go to [Vercel](https://www.google.com/search?q=https://vercel.com), click **Add New...** -> **Project**, and import your GitHub repository.
2. **Configure Project Settings:**
* **Root Directory:** Click *Edit* and select the `frontend` folder.
* **Framework Preset:** Angular (Vercel will auto-detect this).
* **Build Command:** `npm run build`
* **Output Directory:** `dist/frontend/browser` (or check your local `angular.json` output path if it differs).


3. **Add Environment Variables:**
* Add a variable named `API_BASE_URL` (or whatever your Angular environment files use to point to the backend) and set its value to your Render backend URL (`[https://businesshub-backend.onrender.com](https://businesshub-backend.onrender.com)`).


4. **Deploy:** Click **Deploy**! Vercel will build your Angular app and give you a live public URL (e.g., `[https://businesshub-ai.vercel.app](https://businesshub-ai.vercel.app)`).

---

## Phase 4: Final Verification

1. Open your Vercel frontend URL in your browser.
2. Test critical paths: Try logging in, uploading a test document to the RAG chat, or viewing a CRM deal. Because Supabase has `pgvector` and Render has Redis, everything will behave just like it did in your local environment and passing test suites!

Whenever you are ready to kick this off, take it one phase at a time. Do you want to start by setting up Supabase, or tackle the backend configuration first?