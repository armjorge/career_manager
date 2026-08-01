# Infrastructure

Modular OpenTofu infrastructure for the `career-app` prefix in `us-east-1`:

| Module | Path | Resources |
|--------|------|-----------|
| Frontend | `modules/frontend` | Private S3 + CloudFront **OAC** + SPA 403/404 → `index.html` |
| Auth | `modules/auth` | Cognito User Pool, SPA client (SRP), optional Hosted UI + Google |
| API | `modules/api` | HTTP API + Lambda (no VPC / NAT) |
| Documents | `modules/documents` | Per-environment S3 bucket for attachments and templates |

Environments: `envs/dev`, `envs/prod`. Feature flags keep modules removable.

## Fresh deploy (dev)

```bash
# 1) Package Lambda (when enable_api = true)
./backend/scripts/package.sh

# 2) Configure
cd infra/envs/dev
cp terraform.tfvars.example terraform.tfvars
# Set db_postgresql to the Neon PostgreSQL connection string.

# 3) Apply (CloudFront URL is merged into CORS/Cognito automatically)
tofu init
tofu plan -out=tfplan
tofu apply tfplan
tofu output
```

Then wire `frontend/.env` and publish:

```bash
../../scripts/deploy-frontend.sh dev
```

### Useful outputs

| Output | Use |
|--------|-----|
| `frontend_site_url` | Browser entrypoint (also auto-wired into CORS/Cognito) |
| `frontend_bucket_name` | `aws s3 sync` target |
| `frontend_distribution_id` | CloudFront invalidation |
| `api_endpoint` | Base for `VITE_API_BASE_URL` — append `/api/v1` |
| `cognito_user_pool_id` / `cognito_user_pool_client_id` | Frontend Cognito config |
| `cognito_hosted_ui_domain` | `VITE_COGNITO_DOMAIN` |
| `cognito_hosted_ui_base_url` | Google OAuth redirect base |
| `cognito_google_enabled` | Whether Google IdP was created |
| `documents_bucket_name` | Documents module bucket |

### Notes

- Default `project_name` is `career-app`; use that prefix consistently for environments and resources.
- OAuth callback path must be `/auth/callback`.
- Optional Google: set `google_client_id` + `google_client_secret` in tfvars, then `VITE_ENABLE_GOOGLE_AUTH=true` on the frontend.
- Put only **extra** origins (localhost / custom domains) in tfvars — CloudFront is appended by the env composition.
