# Career Manager

Job-application tracker. Stack: **Vite/React** (CloudFront) + **FastAPI on
Lambda** (HTTP API) + **Cognito** auth + **Neon PostgreSQL** data.

## Branches & environments

| Branch | AWS resources | Flow |
|--------|---------------|------|
| `dev` | `career-app-dev-*` | Feature PRs land here; CI deploys app |
| `prod` | `career-app-prod-*` | PR from `dev` after test; CI deploys app |

Infra is applied manually with OpenTofu (`infra/envs/{dev,prod}`). App code
deploys via GitHub Actions (see [docs/DEPLOY.md](docs/DEPLOY.md)).

## Rebuild from code

Full destroy/recreate and **self-serve prod** steps:
→ **[docs/DEPLOY.md](docs/DEPLOY.md)**

Short path (dev):

```bash
./backend/scripts/package.sh
cd infra/envs/dev && cp terraform.tfvars.example terraform.tfvars
# set db_postgresql, then:
tofu init && tofu plan -out=tfplan && tofu apply tfplan
cd ../../.. && ./scripts/deploy-frontend.sh dev
```

Local: copy `backend/.env.example` / `frontend/.env.example`, then
`uvicorn app.main:app --reload` and `npm run dev`.

## Schema

- Greenfield: [`SQL/ddl_postgres17.sql`](SQL/ddl_postgres17.sql)
- Drop Neon Auth FKs (existing DB): [`SQL/migrate_drop_neon_auth_fks.sql`](SQL/migrate_drop_neon_auth_fks.sql)
- Optional user remap: `scripts/migrate_neon_to_cognito.py`
