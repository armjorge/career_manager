# Deploy & rebuild guide

Everything in AWS for this app is rebuildable from this repo with OpenTofu +
the package/deploy scripts. Neon stays external (connection string only).

## Branches

| Git branch | GitHub Environment | AWS prefix | Who creates it |
|------------|--------------------|------------|----------------|
| `dev` | `dev` | `career-app-dev-*` | Already applied |
| `prod` | `prod` | `career-app-prod-*` | You (manual tofu) |

Flow: feature branches → PR into `dev` → test on CloudFront → PR `dev` → `prod`.

CI (`.github/workflows/`) deploys **app code** on push to `dev` / `prod`.
Infrastructure (`tofu apply`) stays **manual** so you can review plans.

## Rebuild dev (already done once)

```bash
# 1) Schema on Neon (greenfield) or FK drop (existing)
#    SQL/ddl_postgres17.sql  OR  SQL/migrate_drop_neon_auth_fks.sql

# 2) Package API (Python 3.13 manylinux wheels)
./backend/scripts/package.sh

# 3) Infra
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars
# set db_postgresql = "<Neon pooled URL>"
tofu init
tofu plan -out=tfplan && tofu apply tfplan
tofu output

# 4) Frontend
# Fill frontend/.env from tofu output (see frontend/.env.example)
# VITE_API_BASE_URL = <api_endpoint>/api/v1
./scripts/deploy-frontend.sh dev
```

Destroy + recreate: `tofu destroy` then repeat steps 2–4.

## Create prod yourself (checklist)

1. **Neon prod DB** — apply `SQL/ddl_postgres17.sql` (empty greenfield).
2. **Package Lambda** from repo root: `./backend/scripts/package.sh`
3. **OpenTofu prod**
   ```bash
   cd infra/envs/prod
   cp terraform.tfvars.example terraform.tfvars
   # REQUIRED:
   #   project_name = "career-app"
   #   environment  = "prod"
   #   aws_region   = "us-east-1"
   #   db_postgresql = "<your prod Neon pooled URL>"
   tofu init
   tofu plan -out=tfplan
   tofu apply tfplan
   tofu output
   ```
4. **Wire frontend locally once** (optional smoke test), then put the same
   values into the GitHub **prod** Environment secrets (table below).
5. **Protect `prod` branch** in GitHub (require PR from `dev`, required checks).
6. **Merge `dev` → `prod`** to let CI deploy Lambda + SPA.

Never commit `terraform.tfvars` or `.env` (gitignored).

## GitHub Environment secrets

Create Environments named exactly `dev` and `prod`.

### Shared AWS

| Secret | Example (dev) |
|--------|----------------|
| `AWS_ACCESS_KEY_ID` | IAM user/key with Lambda + S3 + CloudFront |
| `AWS_SECRET_ACCESS_KEY` | … |
| `AWS_REGION` | `us-east-1` |

### Backend

| Secret | Example (dev) |
|--------|----------------|
| `LAMBDA_FUNCTION_NAME` | `career-app-dev-api` |

### Frontend

| Secret | Example (dev) |
|--------|----------------|
| `S3_BUCKET` | `career-app-dev-site` |
| `CLOUDFRONT_DISTRIBUTION_ID` | from `tofu output frontend_distribution_id` |
| `VITE_API_BASE_URL` | `https://….execute-api.us-east-1.amazonaws.com/api/v1` |
| `VITE_COGNITO_USER_POOL_ID` | from `tofu output` |
| `VITE_COGNITO_USER_POOL_CLIENT_ID` | from `tofu output` |
| `VITE_COGNITO_DOMAIN` | e.g. `career-app-dev-auth` |
| `VITE_AWS_REGION` | `us-east-1` |

Optional: `VITE_POSTHOG_KEY`, `VITE_POSTHOG_HOST`, `VITE_ENABLE_GOOGLE_AUTH`.

After prod `tofu apply`, fill the **prod** Environment with `career-app-prod-*`
outputs the same way.

## Data migration (optional)

Existing Neon Auth users → Cognito:

```bash
# load DB_POSTGRESQL, AWS_REGION, COGNITO_USER_POOL_ID
python scripts/migrate_neon_to_cognito.py --create-users          # dry-run
python scripts/migrate_neon_to_cognito.py --create-users --apply
```
