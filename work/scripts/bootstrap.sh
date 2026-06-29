#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="work"
CODE_DIR="code"

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

python "$WORK_DIR/runtime/loopforge_runner.py" \
  --work-dir "$WORK_DIR" \
  --code-dir "$CODE_DIR" \
  --init \
  --self-check \
  --detect
