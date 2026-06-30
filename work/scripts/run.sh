#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${ROOT_DIR}/result"
LOG_DIR="${ROOT_DIR}/logs"

mkdir -p "${RESULT_DIR}/issues" "${LOG_DIR}/trace"
if [[ ! -f "${LOG_DIR}/interaction.md" ]]; then
  printf '# Interaction Log\n\nNo manual interaction.\n' > "${LOG_DIR}/interaction.md"
fi

python "${WORK_DIR}/runtime/loopforge_runner.py" \
  --work-dir "${WORK_DIR}" \
  --result-dir "${RESULT_DIR}" \
  --log-dir "${LOG_DIR}" \
  "$@" \
  --run
