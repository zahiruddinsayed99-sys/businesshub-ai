Here is your updated, final consolidated deployment guide for **BusinessHub AI**, including the maintenance note regarding free-plan usage and inactivity handling across all three tools.

---

# BusinessHub AI — Final Staging Deployment Guide

## 1. Architecture Stack

* **Frontend:** Angular (Standalone) $\rightarrow$ Hosted on **Vercel**
* **Backend:** FastAPI (Python 3.11) + Celery $\rightarrow$ Hosted on **Render Web Service**
* **Database (`pgvector`):** PostgreSQL $\rightarrow$ Hosted on **Supabase**
* **Cache & Broker:** Redis $\rightarrow$ Hosted on **Render Key Value**

---

## 2. Database Setup (Supabase)

1. Create your project on [Supabase](https://www.google.com/search?q=https://supabase.com).
2. Go to the **SQL Editor** and run the following to enable vector support:
```sql
create extension if not exists vector;

```


3. Copy your **Direct Connection String** for migrations:
```text
postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

```



---

## 3. Backend & Cache Setup (Render)

1. **Redis Cache:** Create a new **Key Value** instance on Render to serve as your message broker and cache.
2. **FastAPI Web Service:** Connect your GitHub repository as a Web Service with these settings:
* **Root Directory:** `backend`
* **Environment:** Python 3
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`


3. **Environment Variables on Render:**
* `DATABASE_URL`: `postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
* `REDIS_URL`: Your Render Key Value connection string
* `TESTING`: `False`
* **`PYTHON_VERSION`**: `3.11.11` *(Crucial to bypass Python 3.14 compilation/SQLAlchemy compatibility bugs)*


4. **Run Migrations Locally:**
From your local `backend/` directory with your virtual environment active, run:
```bash
DATABASE_URL="postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres" alembic upgrade head

```



---

## 4. Frontend Setup (Vercel)

1. **Environment Configuration:**
* Use `src/environments/environment.ts` for local development (`http://localhost:8000/api/v1`).
* Use `src/environments/environment.prod.ts` for staging/production pointing to your live backend:
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://businesshub-ai.onrender.com/api/v1'
};

```


* Ensure services import the standard `environment` file rather than `environment.prod` directly to keep unit tests clean.


2. **`angular.json` File Replacements:**
Ensure your build configuration maps environment replacements automatically:
```json
"production": {
  "fileReplacements": [
    {
      "replace": "src/environments/environment.ts",
      "with": "src/environments/environment.prod.ts"
    }
  ]
}

```


3. **Vercel Project Settings:**
* **Root Directory:** `frontend`
* **Framework Preset:** Angular
* **Build Command:** `npm run build`
* **Output Directory:** `dist/frontend-tmp/browser`



---

## 5. Maintenance & Free Plan Inactivity Management

* **No Action Needed on Free Tiers:** If you are using free plans across all three platforms, **no manual shut down or turn off is required** when you are not working.
* **Automatic Inactivity Handling:**
* **Vercel (Frontend):** Completely serverless and incurs zero idle compute charges.
* **Render (Backend/Redis):** Free tier web services automatically spin down after periods of inactivity. *(Note: Free tier Redis instances have a set expiration limit if left completely unused for weeks).*
* **Supabase (Database):** Free tier projects automatically pause themselves after a week of total inactivity without deleting your data, and can be unpaused instantly when you return.