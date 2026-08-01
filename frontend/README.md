# Frontend

Vite + React + TypeScript + Tailwind SPA. Auth is Amazon Cognito; the API is
FastAPI on Lambda. Deployed via S3 + CloudFront.

## Run locally

```bash
npm install
cp .env.example .env
# Fill Cognito + API values from tofu output (see below)
npm run dev      # http://localhost:5173
npm run build
```

Wire from `tofu output` (dev):

| Variable | Source |
|----------|--------|
| `VITE_API_BASE_URL` | `<api_endpoint>/api/v1` |
| `VITE_COGNITO_USER_POOL_ID` | `cognito_user_pool_id` |
| `VITE_COGNITO_USER_POOL_CLIENT_ID` | `cognito_user_pool_client_id` |
| `VITE_COGNITO_DOMAIN` | `cognito_hosted_ui_domain` (Hosted UI / Google) |
| `VITE_AWS_REGION` | `us-east-1` |

Set `VITE_API_BASE_URL=mock` for the in-memory mock store (no backend).

## Pages (authenticated AppShell)

| Route | Page |
|-------|------|
| `/` | Dashboard |
| `/companies` | Company types, languages, companies |
| `/applications` | Applications + trackers |
| `/documents` | Resume / cover letter text |
| `/generator` | Templates + document generation |
| `/attachments` | Per-application PDF uploads |
| `/sites` | Job board URLs |
| `/analytics` | Summary charts |

Auth routes: `/login`, `/signup`, `/forgot-password`, `/auth/callback`.

## Deploy

```bash
./scripts/deploy-frontend.sh dev
```
