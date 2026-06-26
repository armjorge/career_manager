#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PACKAGE_DIR="${ROOT}/.lambda-package"
OUTPUT_ZIP="${ROOT}/lambda.zip"
REQUIREMENTS="${ROOT}/backend/requirements-lambda.txt"

die() {
  echo "error: $*" >&2
  exit 1
}

resolve_python() {
  if [[ -n "${PYTHON:-}" ]] && command -v "${PYTHON}" >/dev/null 2>&1; then
    echo "${PYTHON}"
    return
  fi
  for candidate in python3.12 python3 python; do
    if command -v "${candidate}" >/dev/null 2>&1; then
      echo "${candidate}"
      return
    fi
  done
  if command -v uv >/dev/null 2>&1; then
    echo "uv run python"
    return
  fi
  die "No Python interpreter found. Install Python 3.12+ or uv."
}

resolve_pip() {
  local python_cmd="$1"

  if command -v pip3 >/dev/null 2>&1; then
    echo "pip3"
    return
  fi
  if command -v pip >/dev/null 2>&1; then
    echo "pip"
    return
  fi
  if ${python_cmd} -m pip --version >/dev/null 2>&1; then
    echo "${python_cmd} -m pip"
    return
  fi
  if command -v uv >/dev/null 2>&1; then
    echo "uv pip"
    return
  fi

  cat >&2 <<'EOF'
error: pip is not available.

Install pip on your Linux machine, then rerun ./backend/build-lambda.sh

Debian / Ubuntu:
  sudo apt update
  sudo apt install -y python3-pip python3-venv zip

Fedora / RHEL:
  sudo dnf install -y python3-pip zip

Or bootstrap pip for the current user:
  python3 -m ensurepip --upgrade
EOF
  exit 1
}

install_dependencies() {
  local pip_cmd="$1"

  # On macOS, cross-build Linux wheels for Lambda (x86_64).
  if [[ "$(uname -s)" == "Darwin" ]]; then
  echo "Building Linux-compatible dependencies for AWS Lambda..."
    ${pip_cmd} install \
      -r "${REQUIREMENTS}" \
      -t "${PACKAGE_DIR}" \
      --platform manylinux2014_x86_64 \
      --implementation cp \
      --python-version 3.12 \
      --only-binary=:all: \
      --upgrade
    return
  fi

  echo "Building dependencies for Linux Lambda..."
  ${pip_cmd} install -r "${REQUIREMENTS}" -t "${PACKAGE_DIR}" --upgrade
}

command -v zip >/dev/null 2>&1 || die "zip is not installed. On Debian/Ubuntu: sudo apt install zip"

PYTHON_CMD="$(resolve_python)"
PIP_CMD="$(resolve_pip "${PYTHON_CMD}")"

rm -rf "${PACKAGE_DIR}" "${OUTPUT_ZIP}"
mkdir -p "${PACKAGE_DIR}"

install_dependencies "${PIP_CMD}"
cp -r "${ROOT}/backend" "${PACKAGE_DIR}/backend"

(
  cd "${PACKAGE_DIR}"
  zip -r "${OUTPUT_ZIP}" . -x '*.pyc' -x '__pycache__/*'
)

echo "Created ${OUTPUT_ZIP}"
echo "Lambda handler: backend.app.main.handler"
echo "Upload this zip to function: career-api-backend"
