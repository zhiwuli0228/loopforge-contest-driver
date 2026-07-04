# c2r-00: Preflight

## Role

Verify the environment is ready for C-to-Rust migration. Read-only phase. No files written.

## Context You Receive

- `SOURCE_ROOT` — path to C source tree
- `WORK_DIR` — path to work directory

## SuperPower Rules (this phase only)

- **Allowed tools**: none (tools.py will be tested but no data commands needed)
- **Allowed filesystem**: read `work/**` only
- **Forbidden**: any write operations, any source modification

## Steps

### 1. Verify tools.py

Run a basic Python import check to confirm tools.py loads without error:

```
python -c "import sys; sys.path.insert(0, 'WORK_DIR/runtime'); from tools import main; print('tools.py OK')"
```

If this fails, tools.py is broken — this is a blocker.

### 2. Verify SOURCE_ROOT

Check that `SOURCE_ROOT` exists as a directory and contains at least one `.c` or `.h` file:

```
ls SOURCE_ROOT/
find SOURCE_ROOT -name "*.c" -o -name "*.h" | head -20
```

Record: exists (yes/no), C file count, H file count.

### 3. Verify WORK_DIR

Check that `WORK_DIR` exists and is writable:

```
test -d WORK_DIR && test -w WORK_DIR && echo "WORK_DIR OK"
```

### 4. Verify Rust toolchain

```
cargo --version
rustc --version
```

Record versions. If either is missing, this is a blocker.

### 5. Verify openspec CLI

```
openspec --version 2>/dev/null || echo "openspec not found"
```

If missing, note it — phases 2-4 and 10 need it for templates. Migration can proceed without it (subagents will create files directly), but report as warning.

## Output

Produce a concise status block:

```
Preflight Report
================
tools.py:        OK / FAIL
SOURCE_ROOT:     <path> (exists, N .c files, M .h files) / MISSING
WORK_DIR:        OK / FAIL
cargo:           <version>
rustc:           <version>
openspec:        <version> / NOT FOUND
```

## Gate

- `PHASE_PASS` — tools.py loads, SOURCE_ROOT has C files, cargo+rustc available
- `PHASE_BLOCKED` — tools.py broken, no C source found, or no Rust toolchain
