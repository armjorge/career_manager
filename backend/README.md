# Backend

FastAPI application deployed to AWS Lambda through API Gateway. It stores data
in Neon PostgreSQL. API Gateway validates Cognito JWTs; locally the app
validates Cognito ID tokens against the user-pool JWKS.

## Local development

```bash
cd backend
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Set `DB_POSTGRESQL` to the Neon connection string and configure `AWS_REGION`,
`COGNITO_USER_POOL_ID`, and `COGNITO_CLIENT_ID`. Set `DOCUMENTS_S3_BUCKET` when
testing document uploads. Health check: `http://localhost:8000/health`.

## Package for Lambda

```bash
./scripts/package.sh
```

This creates `backend/dist/lambda.zip` for the OpenTofu `lambda_zip_path`.
Packaging installs x86_64 manylinux wheels by default for Lambda compatibility.
