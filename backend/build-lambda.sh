#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_DIR="${ROOT}/.lambda-package"
OUTPUT_ZIP="${ROOT}/lambda.zip"

rm -rf "${PACKAGE_DIR}" "${OUTPUT_ZIP}"
mkdir -p "${PACKAGE_DIR}"

PYTHON="${PYTHON:-python3}"
if ! command -v "${PYTHON}" >/dev/null 2>&1; then
  PYTHON="uv run python"
fi

"${PYTHON}" -m pip install -r "${ROOT}/backend/requirements-lambda.txt" -t "${PACKAGE_DIR}" --upgrade
cp -r "${ROOT}/backend" "${PACKAGE_DIR}/backend"

(
  cd "${PACKAGE_DIR}"
  zip -r "${OUTPUT_ZIP}" . -x '*.pyc' -x '__pycache__/*'
)

echo "Created ${OUTPUT_ZIP}"
echo "Lambda handler: backend.app.main.handler"
