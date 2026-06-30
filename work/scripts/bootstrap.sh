#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
CODE_DIR="${ROOT_DIR}/code"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "python interpreter not found" >&2
    exit 1
  fi
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --work-dir)
      WORK_DIR="$2"
      ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
      shift 2
      ;;
    --code-dir)
      CODE_DIR="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ ! "$CODE_DIR" = /* ]]; then
  CODE_DIR="${ROOT_DIR}/${CODE_DIR}"
fi

CODING_SKILL_PATH="$WORK_DIR/skills/code-implementation/SKILL.md"
CODING_SKILL_READY="no"
if [[ -f "$CODING_SKILL_PATH" ]]; then
  CODING_SKILL_READY="yes"
fi

echo "Coding skill: work/skills/code-implementation/SKILL.md"
echo "Coding skill ready: $CODING_SKILL_READY"

"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" \
  --work-dir "$WORK_DIR" \
  --code-dir "$CODE_DIR" \
  --init \
  --self-check \
  --detect
