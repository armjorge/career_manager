#!/usr/bin/env bash
# Build the React app and publish it to the selected OpenTofu environment.
set -euo pipefail

ENVIRONMENT="${1:-dev}"
if [[ "${ENVIRONMENT}" != "dev" && "${ENVIRONMENT}" != "prod" ]]; then
  echo "Usage: $0 [dev|prod]" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
TOFU_DIR="${ROOT_DIR}/infra/envs/${ENVIRONMENT}"

if [[ ! -d "${TOFU_DIR}" ]]; then
  echo "OpenTofu environment does not exist: ${TOFU_DIR}" >&2
  exit 1
fi

cd "${FRONTEND_DIR}"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run build

cd "${TOFU_DIR}"
BUCKET_NAME="$(tofu output -raw frontend_bucket_name)"
DISTRIBUTION_ID="$(tofu output -raw frontend_distribution_id)"

if [[ -z "${BUCKET_NAME}" || -z "${DISTRIBUTION_ID}" ]]; then
  echo "Frontend infrastructure outputs are empty. Apply the environment first." >&2
  exit 1
fi

aws s3 sync "${FRONTEND_DIR}/dist/" "s3://${BUCKET_NAME}/" --delete
aws cloudfront create-invalidation --distribution-id "${DISTRIBUTION_ID}" --paths "/*"
