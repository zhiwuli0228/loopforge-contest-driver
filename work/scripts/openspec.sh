#!/usr/bin/env bash
# openspec.sh — Smart wrapper for OpenSpec CLI.
# Resolution order:
#   1. Global `openspec` in PATH
#   2. Local install at work/vendor/openspec/node_modules/.bin/openspec
#   3. Auto-install from bundled tarball (requires node + npm)
#   4. Bash fallback for core commands (schemas, status, instructions)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT_DIR="$(cd "${WORK_DIR}/.." && pwd)"
VENDOR_DIR="${WORK_DIR}/vendor/openspec"
LOCAL_BIN="${VENDOR_DIR}/node_modules/.bin/openspec"
SCHEMAS_DIR="${ROOT_DIR}/openspec/schemas"
CHANGES_DIR="${ROOT_DIR}/openspec/changes"

# --- Resolution: find an openspec binary ---

resolve_openspec() {
  # 1. Global
  if command -v openspec >/dev/null 2>&1; then
    echo "openspec"
    return 0
  fi
  # 2. Local install
  if [[ -x "${LOCAL_BIN}" ]]; then
    echo "${LOCAL_BIN}"
    return 0
  fi
  # 3. Auto-install
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    if [[ -f "${VENDOR_DIR}/fission-ai-openspec-1.5.0.tgz" ]]; then
      echo "[openspec.sh] Installing from bundled tarball..." >&2
      bash "${VENDOR_DIR}/install.sh" >&2
      if [[ -x "${LOCAL_BIN}" ]]; then
        echo "${LOCAL_BIN}"
        return 0
      fi
    fi
  fi
  # 4. No binary available
  return 1
}

# --- Bash fallback helpers ---

# Extract a field value from a YAML block starting with "- id: <artifact_id>"
# Usage: _yaml_field <file> <artifact_id> <field>
_yaml_field() {
  local file="$1" aid="$2" field="$3"
  local in_block=false
  while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]*${aid}[[:space:]]*$ ]]; then
      in_block=true
      continue
    fi
    if $in_block && [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id: ]]; then
      break
    fi
    if $in_block && [[ "$line" =~ ${field}: ]]; then
      echo "$line" | sed "s/.*${field}:[[:space:]]*//" | tr -d '"'
      return 0
    fi
  done < "$file"
}

# Extract multi-line instruction block for an artifact
# Usage: _yaml_instruction <file> <artifact_id>
_yaml_instruction() {
  local file="$1" aid="$2"
  local in_block=false
  local in_instruction=false
  local result=""
  while IFS= read -r line; do
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]*${aid}[[:space:]]*$ ]]; then
      in_block=true
      continue
    fi
    if $in_block && [[ "$line" =~ ^[[:space:]]*-[[:space:]]*id: ]]; then
      break
    fi
    if $in_block && [[ "$line" =~ ^[[:space:]]*instruction:[[:space:]]*\| ]]; then
      in_instruction=true
      continue
    fi
    if $in_instruction; then
      # Instruction block ends when a line is not indented more than the field
      if [[ "$line" =~ ^[[:space:]]*$ ]]; then
        result+=$'\n'
        continue
      fi
      if [[ ! "$line" =~ ^[[:space:]]{6,} ]]; then
        break
      fi
      result+="${line#        }"$'\n'
    fi
  done < "$file"
  echo "$result"
}

# --- Bash fallback commands ---

fallback_schemas() {
  local json_output=false
  for arg in "$@"; do [[ "$arg" == "--json" ]] && json_output=true; done

  if $json_output; then
    echo "["
    local first=true
    for schema_dir in "${SCHEMAS_DIR}"/*/; do
      [[ -d "$schema_dir" ]] || continue
      local schema_file="${schema_dir}schema.yaml"
      [[ -f "$schema_file" ]] || continue
      local name desc
      name=$(grep '^name:' "$schema_file" 2>/dev/null | head -1 | sed 's/^name:[[:space:]]*//')
      desc=$(grep '^description:' "$schema_file" 2>/dev/null | head -1 | sed 's/^description:[[:space:]]*//')
      [[ -z "$name" ]] && continue

      # Collect artifact IDs
      local arts=""
      while IFS= read -r line; do
        local aid
        aid=$(echo "$line" | sed 's/.*- id:[[:space:]]*//' | tr -d ' ')
        [[ -n "$aid" ]] && arts+="\"${aid}\","
      done < <(grep '^\s*- id:' "$schema_file" 2>/dev/null)
      arts="${arts%,}"

      $first || echo ","
      first=false
      printf '  {"name":"%s","description":"%s","artifacts":[%s],"source":"project"}' "$name" "$desc" "$arts"
    done
    echo ""
    echo "]"
  else
    for schema_dir in "${SCHEMAS_DIR}"/*/; do
      [[ -d "$schema_dir" ]] || continue
      local name
      name=$(grep '^name:' "${schema_dir}schema.yaml" 2>/dev/null | head -1 | sed 's/^name:[[:space:]]*//')
      [[ -n "$name" ]] && echo "- ${name} (project)"
    done
  fi
}

fallback_status() {
  local change_name=""
  local json_output=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --change) change_name="$2"; shift 2 ;;
      --json) json_output=true; shift ;;
      *) shift ;;
    esac
  done

  if [[ -z "$change_name" ]]; then
    echo "[openspec.sh] ERROR: --change required" >&2
    return 1
  fi

  local change_dir="${CHANGES_DIR}/${change_name}"
  if [[ ! -d "$change_dir" ]]; then
    echo "[openspec.sh] ERROR: change '${change_name}' not found" >&2
    return 1
  fi

  # Determine schema from .openspec.yaml
  local schema_name="c2r-migration"
  if [[ -f "${change_dir}/.openspec.yaml" ]]; then
    schema_name=$(grep 'schema:' "${change_dir}/.openspec.yaml" 2>/dev/null | head -1 | sed 's/^schema:[[:space:]]*//' || echo "c2r-migration")
  fi

  local schema_file="${SCHEMAS_DIR}/${schema_name}/schema.yaml"
  if [[ ! -f "$schema_file" ]]; then
    # Package schema (e.g. spec-driven) — fall back to c2r-migration if available
    schema_file="${SCHEMAS_DIR}/c2r-migration/schema.yaml"
    if [[ ! -f "$schema_file" ]]; then
      echo "[openspec.sh] ERROR: schema '${schema_name}' not found and no fallback available" >&2
      return 1
    fi
    schema_name="c2r-migration"
  fi

  # Parse artifact IDs from schema
  local artifacts=()
  while IFS= read -r line; do
    local aid
    aid=$(echo "$line" | sed 's/.*- id:[[:space:]]*//' | tr -d ' ')
    [[ -n "$aid" ]] && artifacts+=("$aid")
  done < <(grep '^\s*- id:' "$schema_file" 2>/dev/null)

  local total=${#artifacts[@]}
  local done_count=0
  local artifact_json=""

  for aid in "${artifacts[@]}"; do
    local gen_pattern
    gen_pattern=$(_yaml_field "$schema_file" "$aid" "generates")
    local status="ready"
    local output_path="${gen_pattern}"

    if [[ -n "$gen_pattern" ]]; then
      if [[ "$gen_pattern" == *"*"* ]]; then
        local matches
        matches=$(find "${change_dir}" -name "*.md" 2>/dev/null | head -1)
        if [[ -n "$matches" ]]; then
          status="done"
          done_count=$((done_count + 1))
        fi
      else
        if [[ -f "${change_dir}/${gen_pattern}" ]]; then
          status="done"
          done_count=$((done_count + 1))
        fi
      fi
    fi

    [[ -n "$artifact_json" ]] && artifact_json+=","
    artifact_json+="{\"id\":\"${aid}\",\"outputPath\":\"${output_path}\",\"status\":\"${status}\"}"
  done

  if $json_output; then
    cat <<EOF
{
  "changeName": "${change_name}",
  "schemaName": "${schema_name}",
  "isComplete": $([ "$done_count" -eq "$total" ] && echo true || echo false),
  "artifacts": [${artifact_json}],
  "progress": {"total": ${total}, "complete": ${done_count}, "remaining": $((total - done_count))}
}
EOF
  else
    echo "Change: ${change_name}"
    echo "Schema: ${schema_name}"
    echo "Progress: ${done_count}/${total} artifacts complete"
    echo ""
    for aid in "${artifacts[@]}"; do
      local gen_pattern
      gen_pattern=$(_yaml_field "$schema_file" "$aid" "generates")
      local status_icon="[ ]"
      if [[ -n "$gen_pattern" ]]; then
        if [[ "$gen_pattern" == *"*"* ]]; then
          local matches
          matches=$(find "${change_dir}" -name "*.md" 2>/dev/null | head -1)
          [[ -n "$matches" ]] && status_icon="[x]"
        else
          [[ -f "${change_dir}/${gen_pattern}" ]] && status_icon="[x]"
        fi
      fi
      echo "${status_icon} ${aid}"
    done
  fi
}

fallback_instructions() {
  local artifact_id=""
  local change_name=""
  local json_output=false
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --change) change_name="$2"; shift 2 ;;
      --json) json_output=true; shift ;;
      -*) shift ;;
      *) artifact_id="$1"; shift ;;
    esac
  done

  if [[ -z "$artifact_id" || -z "$change_name" ]]; then
    echo "[openspec.sh] ERROR: artifact and --change required" >&2
    return 1
  fi

  local change_dir="${CHANGES_DIR}/${change_name}"
  local schema_name="c2r-migration"
  if [[ -f "${change_dir}/.openspec.yaml" ]]; then
    schema_name=$(grep 'schema:' "${change_dir}/.openspec.yaml" 2>/dev/null | head -1 | sed 's/^schema:[[:space:]]*//' || echo "c2r-migration")
  fi

  local schema_file="${SCHEMAS_DIR}/${schema_name}/schema.yaml"
  if [[ ! -f "$schema_file" ]]; then
    schema_file="${SCHEMAS_DIR}/c2r-migration/schema.yaml"
    schema_name="c2r-migration"
  fi
  local template_dir="${SCHEMAS_DIR}/${schema_name}/templates"

  local generates
  generates=$(_yaml_field "$schema_file" "$artifact_id" "generates")
  local template_file
  template_file=$(_yaml_field "$schema_file" "$artifact_id" "template")
  local instruction
  instruction=$(_yaml_instruction "$schema_file" "$artifact_id")

  if $json_output; then
    local template_content=""
    if [[ -n "$template_file" && -f "${template_dir}/${template_file}" ]]; then
      template_content=$(cat "${template_dir}/${template_file}")
    fi

    local escaped_template
    escaped_template=$(echo "$template_content" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""')
    local escaped_instruction
    escaped_instruction=$(echo "$instruction" | python3 -c 'import sys,json; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""')

    cat <<EOF
{
  "changeName": "${change_name}",
  "artifactId": "${artifact_id}",
  "schemaName": "${schema_name}",
  "outputPath": "${generates}",
  "template": ${escaped_template},
  "instruction": ${escaped_instruction},
  "dependencies": []
}
EOF
  else
    echo "Artifact: ${artifact_id}"
    echo "Output: ${generates}"
    echo "Template: ${template_dir}/${template_file}"
    [[ -n "$instruction" ]] && echo "Instruction: ${instruction:0:200}..."
  fi
}

# --- Main ---

OPENSPEC_BIN=$(resolve_openspec) || true

if [[ -n "$OPENSPEC_BIN" ]]; then
  exec $OPENSPEC_BIN "$@"
fi

# Bash fallback
echo "[openspec.sh] WARNING: openspec binary not available, using bash fallback (limited)" >&2

case "${1:-}" in
  --version) echo "bash-fallback (openspec not installed)" ;;
  schemas)   shift; fallback_schemas "$@" ;;
  status)    shift; fallback_status "$@" ;;
  instructions) shift; fallback_instructions "$@" ;;
  *)
    echo "[openspec.sh] ERROR: command '${1:-}' not supported in bash fallback" >&2
    echo "Supported: --version, schemas, status, instructions" >&2
    exit 1
    ;;
esac
