#!/usr/bin/env bash
# Build a Lambda deployment zip at backend/dist/lambda.zip
#
# Always installs manylinux x86_64 wheels so the zip matches the default
# Lambda architecture — even when packaging on Apple Silicon / aarch64 hosts.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILD_DIR="${DIST_DIR}/build"
ZIP_PATH="${DIST_DIR}/lambda.zip"

# Match infra/modules/api default: architectures = ["x86_64"], runtime python3.13
LAMBDA_PYTHON_VERSION="${LAMBDA_PYTHON_VERSION:-3.13}"
LAMBDA_PLATFORM="${LAMBDA_PLATFORM:-x86_64-manylinux2014}"

resolve_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    echo "${PYTHON_BIN}"
    return
  fi
  # Prefer CPython 3.13 to match Lambda runtime (local .venv may be newer).
  if command -v uv >/dev/null 2>&1 && uv python find 3.13 >/dev/null 2>&1; then
    uv python find 3.13
    return
  fi
  if command -v python3.13 >/dev/null 2>&1; then
    echo "python3.13"
    return
  fi
  if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
    echo "${ROOT_DIR}/.venv/bin/python"
    return
  fi
  echo "python3"
}

PYTHON_BIN="$(resolve_python)"

echo "==> Using ${PYTHON_BIN} ($("${PYTHON_BIN}" --version 2>&1))"
echo "==> Target platform: ${LAMBDA_PLATFORM} (CPython ${LAMBDA_PYTHON_VERSION})"
echo "==> Cleaning previous build"
rm -rf "${DIST_DIR}"
mkdir -p "${BUILD_DIR}"

echo "==> Installing dependencies into build/"
# Cross-platform binary wheels are required: packaging on aarch64/macOS without
# --platform would ship the wrong pydantic_core .so and Lambda fails with
# ImportModuleError at init.
if command -v uv >/dev/null 2>&1; then
  uv pip install \
    --python "${PYTHON_BIN}" \
    --target "${BUILD_DIR}" \
    --python-platform "${LAMBDA_PLATFORM}" \
    --only-binary :all: \
    -r "${ROOT_DIR}/requirements.txt"
else
  "${PYTHON_BIN}" -m pip install \
    --upgrade \
    --target "${BUILD_DIR}" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version "${LAMBDA_PYTHON_VERSION}" \
    --only-binary=:all: \
    -r "${ROOT_DIR}/requirements.txt"
fi

echo "==> Copying application source"
cp -R "${ROOT_DIR}/app" "${BUILD_DIR}/app"

echo "==> Creating ${ZIP_PATH}"
(
  cd "${BUILD_DIR}"
  find . -type d -name "__pycache__" -prune -exec rm -rf {} +
  find . -type f -name "*.pyc" -delete
  zip -r9 "${ZIP_PATH}" . -x "*.pyc" "*__pycache__*"
)

echo "==> Done: ${ZIP_PATH}"
ls -lh "${ZIP_PATH}"

SO_FILE="$(find "${BUILD_DIR}/pydantic_core" -name '_pydantic_core*.so' 2>/dev/null | head -1 || true)"
if [[ -n "${SO_FILE}" ]]; then
  echo "==> Native wheel check: $(basename "${SO_FILE}")"
fi
