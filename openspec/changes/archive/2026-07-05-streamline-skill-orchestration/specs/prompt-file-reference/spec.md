## ADDED Requirements

### Requirement: Subagent prompt files referenced by path only

The main agent SHALL construct subagent dispatch prompts as a 2-3 line block containing only the subagent prompt file path and context variable assignments. The Agent tool `prompt` field MUST follow this exact format:

```
Execute <subagent_prompt_path> with:
KEY1=VALUE1
KEY2=VALUE2
...
```

The main agent MUST NOT read subagent prompt files into the main context before dispatching. The subagent reads its own prompt file from disk in its own isolated context.

#### Scenario: Phase 3 Spec dispatch
- **WHEN** the main agent dispatches Phase 3 (Spec)
- **THEN** the Agent tool prompt field SHALL be exactly:
  ```
  Execute work/subagent/c2r-03-spec.md with:
  OPENSPEC_CHANGE=<name>
  SOURCE_ROOT=<path>
  WORK_DIR=<path>
  PRIOR_OUTPUTS.inventory=<path>
  PRIOR_OUTPUTS.design=<path>
  PRIOR_OUTPUTS.capability_map=<path>
  ```

#### Scenario: Phase 5 batch dispatch
- **WHEN** the main agent dispatches a Phase 5 implementation batch
- **THEN** the Agent tool prompt field SHALL be exactly:
  ```
  Execute work/subagent/c2r-05-implement.md with:
  BATCH_ID=<id>
  OPENSPEC_CHANGE=<name>
  SOURCE_ROOT=<path>
  OUTPUT_DIR=<path>
  PRIOR_OUTPUTS.implement_plan=<path>
  PRIOR_OUTPUTS.specs_dir=<path>
  PRIOR_OUTPUTS.design=<path>
  ```

#### Scenario: Inline prompt fabrication prohibited
- **WHEN** the main agent constructs an Agent tool prompt that includes embedded execution steps, file content, Rust type definitions, or duplicated subagent prompt instructions
- **THEN** this SHALL be considered a delegation violation and is forbidden

### Requirement: Subagent prompt file read prohibition

The main agent SHALL NOT use the Read tool on any `work/subagent/c2r-*.md` file. Subagent prompt content is the subagent's responsibility and must never enter the main context.

#### Scenario: Main agent attempts to read subagent prompt
- **WHEN** the main agent invokes `read` on `work/subagent/c2r-03-spec.md` or any other `c2r-*.md` file
- **THEN** this SHALL be considered a delegation violation

#### Scenario: Subagent reads its own prompt
- **WHEN** a subagent is spawned with a reference to `work/subagent/c2r-03-spec.md`
- **THEN** the subagent SHALL read that file from disk in its own isolated context
