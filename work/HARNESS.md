# LoopForge Harness

## 1. Workspace layout

Repository root:

```text
.
├── INSTRUCTION.md
├── code/
├── work/
├── result/
└── logs/
```

Framework assets:

```text
work/
├── loopforge.config.yaml
├── runtime/
├── scripts/
├── subagent/
├── rules/
├── profiles/
└── skills/
    └── loopforge-driver/
        └── SKILL.md
```

## 2. Agent entrypoint

Read and follow:

```text
work/skills/loopforge-driver/SKILL.md
```

## 3. Configuration

Read framework configuration from:

```text
work/loopforge.config.yaml
```

## 4. Bootstrap

Official Linux execution:

```bash
bash work/scripts/bootstrap.sh
```

Windows local smoke execution:

```powershell
powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1
```

## 5. Source path resolution

The source project path must be resolved by the following priority:

1. Platform-provided source path.
2. Explicit `--source-root` or `SOURCE_ROOT`, when provided.
3. Auto-detected contest Linux source mount, when present.
4. Local repository fallback: `code/`.

For local development, placing the source tree under `code/` is sufficient. No extra path argument is required.

## 6. Required root-level records

Keep these files or directories available:

```text
result/output.md
logs/interaction.md
logs/trace/
```

`logs/interaction.md` may be empty if execution is fully unattended.
