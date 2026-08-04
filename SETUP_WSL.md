# BusinessHub AI — Local Development Setup (WSL Guide)

This document provides step-by-step instructions for human operators to spin up the local development environment using Windows Subsystem for Linux (WSL).

---

## 1. Environment Configuration

Copy the provided environment template to create your local `.env` file at the repository root:

```bash
cp env.example .env
```

---

## 2. Infrastructure Containers Setup

Spin up PostgreSQL (with `pgvector`), Redis, MinIO, and automated bucket initialization using Docker Compose inside WSL:

```bash
docker compose up -d
```

Verify that all containers are running and healthy:

```bash
docker compose ps
```

---

## 3. Verify Container Connectivity

### Database Connection (PostgreSQL + pgvector)
Test connectivity to PostgreSQL using `pg_isready`:

```bash
docker exec -it businesshub_postgres pg_isready -U postgres -d businesshub_db
```

### Redis Connection
Ping the Redis server:

```bash
docker exec -it businesshub_redis redis-cli ping
```
*(Expected response: `PONG`)*

### MinIO Object Storage
Access the MinIO Web Console in your browser:
- **Console URL:** [http://localhost:9001](http://localhost:9001)
- **User:** `minio_admin_user`
- **Password:** `minio_admin_password_secure_123`

---

## 4. Backend Setup & Local Server Launch

Navigate to the `/backend` directory and set up a Python 3.12+ virtual environment:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Launch the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

Verify health check endpoints:
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/api/v1/healthz](http://localhost:8000/api/v1/healthz)
