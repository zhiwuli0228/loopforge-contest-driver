#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="work"
CODE_DIR="code"
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

"$PYTHON_BIN" "$WORK_DIR/runtime/loopforge_runner.py" \
  --work-dir "$WORK_DIR" \
  --code-dir "$CODE_DIR" \
  --init \
  --self-check \
  --detect
