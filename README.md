# Career Manager

A job-application pipeline for tracking companies, applications, documents, and outreach. The active stack is a **React** frontend, **FastAPI** backend on **AWS Lambda**, **API Gateway**, and **PostgreSQL on Neon** (with **Neon Auth**).

A legacy **Streamlit** UI and Word document generator remain in the repo for reference and local workflows.

---

## Live deployment (AWS)

| What | URL |
|------|-----|
| **Web app (HTTPS — use this)** | https://d1op72z71x0vy8.cloudfront.net |
| **Web app (legacy HTTP)** | http://career-app-frontend.s3-website-us-east-1.amazonaws.com |
| **API base** | https://uhyi1tayu5.execute-api.us-east-1.amazonaws.com/api/v1 |
| **Health check** | https://uhyi1tayu5.execute-api.us-east-1.amazonaws.com/api/v1/health |

The API URL serves JSON only — it is **not** the web UI. If you open the API root (`https://uhyi1tayu5.execute-api.us-east-1.amazonaws.com/`) you will see a blank page or `{"message":"Not Found"}`. Use the **S3 website URL** above for the app.

---

## Architecture

```
Browser  →  S3 static site (React/Vite)
              ↓ Neon Auth (sign-in)
              ↓ REST calls
           API Gateway  →  Lambda (FastAPI + Mangum)  →  Neon PostgreSQL
```

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, TanStack Query, Tailwind CSS |
| Auth | Neon Auth (`@neondatabase/neon-js`) |
| API | FastAPI, Mangum, JWT validation |
| Compute | AWS Lambda (`career-api-backend`, Python 3.12, x86_64) |
| Gateway | API Gateway HTTP API (`career-api`) |
| Database | Neon PostgreSQL (`consulting_tracker` schema) |
| Legacy UI | Streamlit (`pages/`, `Library/concept_filing.py`) |

---

## Project structure

```
career_manager/
├── frontend/                 # React SPA (production UI)
│   ├── src/
│   │   ├── api/              # API client + mock store
│   │   ├── auth/             # Neon Auth client + token storage
│   │   ├── pages/            # Dashboard, companies, applications, …
│   │   └── context/          # Auth provider
│   └── .env.production       # Production build env (not committed)
├── backend/                  # FastAPI app for Lambda
│   ├── app/
│   │   ├── main.py           # App + Lambda handler
│   │   ├── routers/          # companies, applications
│   │   └── config.py         # Settings from env vars
│   └── build-lambda.sh       # Build lambda.zip for AWS
├── SQL/                      # PostgreSQL DDL (Postgres 17)
├── pages/                    # Legacy Streamlit pages
├── Library/                  # DB utils, CV generation, Streamlit helpers
├── config/config.yml
└── lambda.zip                # Built artifact (gitignored)
```

---

## Prerequisites

- **Python 3.12** (matches Lambda runtime)
- **Node.js 20+** and npm
- **PostgreSQL 17** schema on Neon (see `SQL/`)
- **Neon Auth** enabled for your project
- **AWS CLI** configured (for deployment)

---

## Local development

### 1. Environment

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Root `.env` (backend):

```bash
DB_POSTGRESQL=postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
NEON_AUTH_URL=https://ep-xxx.neonauth.region.aws.neon.tech/neondb/auth
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
API_GATEWAY_BASE_PATH=/
```

`frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_NEON_AUTH_URL=https://ep-xxx.neonauth.region.aws.neon.tech/neondb/auth
```

Set `VITE_API_BASE_URL=mock` to run the UI with in-memory data (no backend).

### 2. Backend (FastAPI)

```bash
pip install -r backend/requirements-lambda.txt
# or: uv sync

uvicorn backend.app.main:app --reload --port 8000
```

Verify: http://localhost:8000/api/v1/health

### 3. Frontend (Vite)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Neon Auth (required for sign-in)

In **Neon Console → Auth → Configuration**, add your app origins:

- `http://localhost:5173` (local)
- `http://career-app-frontend.s3-website-us-east-1.amazonaws.com` (production)

Without this, the app may hang on “Loading session…” or fail to sign in.

---

## AWS deployment

### Build Lambda package

On **Linux x86_64** or **ARM/macOS** (script cross-compiles wheels for Lambda):

```bash
# Debian/Ubuntu: sudo apt install -y python3.12-venv python3-pip zip
PYTHON=python3.12 ./backend/build-lambda.sh
```

Produces `lambda.zip` with handler `backend.app.main.handler`.

> **Important:** Lambda is `x86_64`. Building on ARM (OrbStack, Apple Silicon) requires the cross-compile path in `build-lambda.sh` — do not `pip install -t` without `--platform manylinux2014_x86_64`.

### Upload backend

```bash
aws lambda update-function-code \
  --function-name career-api-backend \
  --zip-file fileb://lambda.zip

aws lambda update-function-configuration \
  --function-name career-api-backend \
  --timeout 30 \
  --memory-size 512
```

### Lambda environment variables

| Variable | Example / notes |
|----------|-----------------|
| `DB_POSTGRESQL` | Neon pooled connection string |
| `NEON_AUTH_URL` | Neon Auth base URL |
| `CORS_ORIGINS` | `http://career-app-frontend.s3-website-us-east-1.amazonaws.com` (website origin, **not** the S3 REST URL) |
| `API_GATEWAY_BASE_PATH` | `/` for HTTP API without a stage prefix |

Do **not** set `DB_MONGO` — the API uses PostgreSQL only.

### Deploy frontend

```bash
cd frontend
# ensure frontend/.env.production has VITE_API_BASE_URL and VITE_NEON_AUTH_URL
npm run build
aws s3 sync dist/ s3://career-app-frontend/ --delete
```

S3 bucket `career-app-frontend` is configured for static website hosting (`index.html` + SPA error document).

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Liveness |
| GET | `/api/v1/health/db` | Database connectivity |
| * | `/api/v1/companies/*` | Company CRUD |
| * | `/api/v1/applications/*` | Application CRUD |

All protected routes expect `Authorization: Bearer <jwt>` from Neon Auth.

---

## Database

Schema lives in `SQL/ddl_postgres17.sql` and `SQL/ddl_postgres17_metadata.sql`. Core tables:

- `dim_company` — target organizations
- `fact_application` — job applications
- `dim_tracker` — pipeline status

Interactive ER diagram: [Data Model/index.html](Data%20Model/index.html)

---

## Legacy Streamlit app

The original Streamlit interface is still available for local use:

```bash
pip install -r requirements.txt
streamlit run pages/00_companies.py
```

Document generation (Word templates) is in `Library/CV_generation.py`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Blank/dark page at API URL | Opened API Gateway instead of S3 website | Use the **Web app** URL in the table above |
| `crypto.randomUUID is not a function` | S3 website is HTTP; Web Crypto UUID API needs HTTPS | Polyfill added in `index.html`; long-term fix: CloudFront + HTTPS |
| Stuck on “Loading Career Manager…” (static text, React never loads) | Vite’s `crossorigin` tags + S3 without CORS blocks the JS module | Fixed in `vite.config.ts` (strips `crossorigin`); bucket CORS also configured |
| Stuck on “Loading session…” / blank dark page | `getSession()` blocked by cross-origin cookies from the S3 HTTP site, or wrong URL (API Gateway) | Use the **S3 website URL**; hard-refresh (`Ctrl+Shift+R`). Auth restores from local JWT only on load. |
| Lambda `Internal Server Error` | Wrong-architecture zip (e.g. ARM wheels on x86_64 Lambda) | Rebuild with `./backend/build-lambda.sh` on Linux or with cross-compile |
| `pydantic_core` import error | Same as above | Rebuild zip with `manylinux2014_x86_64` wheels |
| CORS errors in browser | `CORS_ORIGINS` mismatch | Use the S3 **website** endpoint, not `bucket.s3.region.amazonaws.com` |

---

## License

MIT License
