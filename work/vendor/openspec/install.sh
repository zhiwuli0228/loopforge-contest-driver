#!/usr/bin/env bash
set -euo pipefail

# Install openspec locally from bundled tarball.
# Requires: node, npm
# Usage: bash work/vendor/openspec/install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARBALL="${SCRIPT_DIR}/fission-ai-openspec-1.5.0.tgz"
INSTALL_DIR="${SCRIPT_DIR}"

if [[ ! -f "${TARBALL}" ]]; then
  echo "[openspec-install] ERROR: tarball not found at ${TARBALL}" >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  echo "[openspec-install] ERROR: node is not in PATH" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[openspec-install] ERROR: npm is not in PATH" >&2
  exit 1
fi

echo "[openspec-install] Installing openspec to ${INSTALL_DIR} ..."
npm install --prefix "${INSTALL_DIR}" "${TARBALL}" --no-save 2>&1

OPENSPEC_BIN="${INSTALL_DIR}/node_modules/.bin/openspec"
if [[ -x "${OPENSPEC_BIN}" ]]; then
  echo "[openspec-install] OK: openspec installed at ${OPENSPEC_BIN}"
  "${OPENSPEC_BIN}" --version 2>/dev/null || true
else
  echo "[openspec-install] ERROR: installation failed, binary not found" >&2
  exit 1
fi
