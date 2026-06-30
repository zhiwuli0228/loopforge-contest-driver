#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="${ROOT_DIR}/work"
RESULT_DIR="${ROOT_DIR}/result"
LOG_DIR="${ROOT_DIR}/logs"
SOURCE_ROOT_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source-root)
      SOURCE_ROOT_ARG="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [[ -n "$SOURCE_ROOT_ARG" ]]; then
  SOURCE_ROOT="$SOURCE_ROOT_ARG"
elif [[ -n "${SOURCE_ROOT:-}" ]]; then
  SOURCE_ROOT="${SOURCE_ROOT}"
else
  case "$(uname -s 2>/dev/null || echo unknown)" in
    Linux*)
      SOURCE_ROOT="/__CONTEST_PLATFORM_SOURCE_ROOT__/FlashDB"
      ;;
    *)
      SOURCE_ROOT="code"
      ;;
  esac
fi

export SOURCE_ROOT

mkdir -p "${RESULT_DIR}/issues" "${LOG_DIR}/trace"
if [[ ! -f "${LOG_DIR}/interaction.md" ]]; then
  printf '# Interaction Log\n\nNo manual interaction.\n' > "${LOG_DIR}/interaction.md"
fi

python "${WORK_DIR}/runtime/loopforge_runner.py" \
  --work-dir "${WORK_DIR}" \
  --source-root "${SOURCE_ROOT}" \
  --result-dir "${RESULT_DIR}" \
  --log-dir "${LOG_DIR}" \
  --run
