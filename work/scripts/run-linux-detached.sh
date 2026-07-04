#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_PATH="${ROOT_DIR}/work/scripts/run-linux-detached.sh"
ROOT_KEY="$(printf '%s' "${ROOT_DIR}" | sha256sum | cut -c1-16)"
STATE_DIR="${LOOPFORGE_LAUNCH_STATE_DIR:-${TMPDIR:-/tmp}/loopforge-${UID}-${ROOT_KEY}}"
PID_FILE="${STATE_DIR}/pid"
EXIT_FILE="${STATE_DIR}/exit-code"
STARTED_FILE="${STATE_DIR}/started"
OUTPUT_FILE="${STATE_DIR}/runner-output.log"

status() {
  if [[ -f "${ROOT_DIR}/result/output.md" ]]; then
    printf 'completed report=%s\n' "${ROOT_DIR}/result/output.md"
    return
  fi
  if [[ -f "${PID_FILE}" ]]; then
    local pid
    pid="$(cat "${PID_FILE}")"
    if [[ "${pid}" =~ ^[0-9]+$ ]] && kill -0 "${pid}" 2>/dev/null; then
      printf 'running pid=%s state=%s\n' "${pid}" "${STATE_DIR}"
      return
    fi
  fi
  if [[ -f "${EXIT_FILE}" ]]; then
    printf 'completed_without_report exit_code=%s output=%s\n' "$(cat "${EXIT_FILE}")" "${OUTPUT_FILE}"
  elif [[ -f "${STARTED_FILE}" ]]; then
    printf 'interrupted_without_report output=%s\n' "${OUTPUT_FILE}"
  else
    printf 'not_started state=%s\n' "${STATE_DIR}"
  fi
}

worker() {
  local source_root="$1"
  mkdir -p "${STATE_DIR}"
  printf '%s\n' "$$" > "${PID_FILE}"
  local exit_code=0
  trap 'exit_code=$?; printf "%s\n" "${exit_code}" > "${EXIT_FILE}"' EXIT
  cd "${ROOT_DIR}"
  SOURCE_ROOT="${source_root}" bash work/scripts/run.sh --run
}

case "${1:-}" in
  --start)
    if [[ -z "${SOURCE_ROOT:-}" ]]; then
      printf '[LoopForge] ERROR: SOURCE_ROOT is required.\n' >&2
      exit 2
    fi
    mkdir -p "${STATE_DIR}"
    if ! (set -o noclobber; printf '%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${STARTED_FILE}") 2>/dev/null; then
      status
      exit 0
    fi
    setsid bash "${SCRIPT_PATH}" --worker "${SOURCE_ROOT}" > "${OUTPUT_FILE}" 2>&1 < /dev/null &
    launcher_pid="$!"
    printf '%s\n' "${launcher_pid}" > "${PID_FILE}"
    printf 'started launcher_pid=%s state=%s\n' "${launcher_pid}" "${STATE_DIR}"
    ;;
  --status)
    status
    ;;
  --worker)
    worker "$2"
    ;;
  *)
    printf 'Usage: SOURCE_ROOT=/path %s --start | %s --status\n' "$0" "$0" >&2
    exit 2
    ;;
esac
