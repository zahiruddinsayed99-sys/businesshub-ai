Here is your complete, updated deployment record and reference guide for **BusinessHub AI**. This captures all the working configurations, including the Python version fix and service wiring for your portfolio staging environment.

---

# BusinessHub AI — Staging Deployment Guide

## Architecture Overview

* **Frontend:** Angular Standalone $\rightarrow$ Hosted on **Vercel**
* **Backend:** FastAPI (Python 3.11) + Celery Workers $\rightarrow$ Hosted on **Render**
* **Database (`pgvector`):** PostgreSQL $\rightarrow$ Hosted on **Supabase**
* **Cache & Broker (Redis):** Key Value instance $\rightarrow$ Hosted on **Render**

---

## Step 1: Database Setup (Supabase)

1. **Create Project:** Set up a new project on [Supabase](https://www.google.com/search?q=https://supabase.com) and save your database password.
2. **Enable Vector Extension:** Navigate to the **SQL Editor** in your Supabase dashboard and run:
```sql
create extension if not exists vector;

```


3. **Get Connection String:** Go to **Database Settings** $\rightarrow$ **Connection string** $\rightarrow$ **Direct Connection string**, and copy your URI. It will look like:
```text
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

```



---

## Step 2: Cache Setup (Render Key Value)

1. In your Render dashboard, click **New+** $\rightarrow$ **Key Value**.
2. Name your instance (e.g., `businesshub-redis`), select your region, and create it.
3. Copy the **Internal/External Connection URL** for your backend configuration.

---

## Step 3: Backend Setup (Render Web Service)

1. Connect your GitHub repository to Render as a **Web Service**.
2. Configure the core settings:
* **Root Directory:** `backend`
* **Environment:** Python 3
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`


3. **Add Environment Variables** in the Render dashboard:
* `DATABASE_URL`: Your Supabase connection string updated with the async driver: `postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
* `REDIS_URL`: Your Render Key Value connection URL.
* `TESTING`: `False`
* **`PYTHON_VERSION`**: `3.11.11` *(Crucial to bypass Python 3.14 compilation/SQLAlchemy compatibility bugs)*.


4. **Database Migrations:** Once your service builds successfully, run your Alembic migrations via Render's shell or locally against the Supabase URI:
```bash
alembic upgrade head

```



---

## Step 4: Frontend Setup (Vercel)

1. Import your repository into [Vercel](https://www.google.com/search?q=https://vercel.com).
2. Configure project options:
* **Root Directory:** `frontend`
* **Framework Preset:** Angular
* **Build Command:** `npm run build`
* **Output Directory:** `dist/frontend/browser`


3. Add the environment variable:
* `API_BASE_URL`: Your live Render backend URL (`[https://businesshub-ai.onrender.com](https://businesshub-ai.onrender.com)`).


4. Click **Deploy**.

---

Would you like to review how to connect your Angular frontend environment files to the Vercel deployment URL next?