# LoopForge GitHub Acceptance Report

> Repository: `https://github.com/zhiwuli0228/loopforge-contest-driver`  
> Review target: accept the current LoopForge repository against the latest generic platform blueprint plus the merged cross-platform execution design.  
> Review date: 2026-06-29  
> Scope: `work/` package structure, `work/code` boundary, runner behavior, scripts, skill entrypoint, rules, profiles, cross-platform execution path, and residual legacy assets.

---

## 1. Executive Verdict

Current status:

```text
Core architecture accepted.
Cross-platform execution support accepted.
Repository is ready to move into follow-up feature development.
```

Recommended acceptance state:

```text
ACCEPTED_WITH_MINOR_FOLLOW_UPS
```

Reason:

- the generic `work/` platform layout is in place
- the runner is a real Python file and no longer extracted from Markdown
- Windows local development entrypoints and Linux-first submission entrypoints are both defined
- platform-specific verification command selection is implemented
- negative-path contract checks pass
- Windows PowerShell smoke test passes locally

The remaining items are not release blockers for continued platform work, but they should stay on the cleanup list:

```text
1. Linux shell path was not executed in this Windows host during this acceptance run.
2. Verification failure is still reported as BLOCKED_WITH_REPORT rather than a distinct degraded state.
3. Root-level legacy and design files still exist outside work/.
```

---

## 2. Acceptance Evidence

The following validation was executed against the current repository state:

```text
python work/scripts/runner-negative-check.py
powershell -ExecutionPolicy Bypass -File work/scripts/smoke-test.ps1 -WorkDir work -CodeDir code
python work/runtime/loopforge_runner.py --work-dir work --code-dir code --init --self-check --detect --verify --finalize
```

Observed results:

- negative-path acceptance passed with 6 scenarios
- Windows PowerShell smoke test passed
- runner self-check passed with cross-platform assets present
- final report now includes runtime-platform and verification-command-selection sections
- `.loopforge` artifacts are written under `code/.loopforge/`

Additional targeted verification was also executed for command fallback behavior:

```text
Windows platform command removed from config copy
-> runner selected verification.commands.default
-> fallback_used = true
```

This confirms the intended selection order:

```text
current platform -> default -> blocked-with-report
```

---

## 3. Accepted Areas

### 3.1 `work/` package model is correct

The repository now uses the expected formal package model:

```text
workspace/
├── work/
└── code/
```

`work/` contains:

```text
docs/
profiles/
rules/
runtime/
scripts/
skills/
INSTRUCTION.md
README.md
SUBMISSION.md
loopforge.config.yaml
```

This matches the generic LoopForge hosting-platform direction.

### 3.2 Platform positioning is correct

The repository consistently expresses:

```text
LoopForge is a reusable Loop Engineering hosting platform.
Contest tasks are profiles.
Static policy lives under work/.
Mutable target changes live under code/.
Runtime artifacts live under code/.loopforge/.
```

The runner, docs, and skill all preserve the non-submission boundary:

```text
no commit
no push
no PR creation
no contest submission action
```

### 3.3 Five generic modes are implemented

The current mode set is present and validated by the runner:

```text
feature-development
migration
defect-repair
consistency-check
skill-generation
```

Each mode has the expected minimal rule pack:

```text
00-flow.md
01-phase-policy.md
02-required-artifacts.md
03-forbidden-actions.md
04-final-report.md
```

### 3.4 Profiles are correctly split into templates and examples

The repository contains:

```text
work/profiles/templates/*.yaml
work/profiles/examples/*.yaml
```

Current runner checks confirm:

```text
template_count = 5
example_count = 5
```

This satisfies the generic Mode + Profile design.

### 3.5 Runner implementation is real and contract-aware

The runner is a real Python file:

```text
work/runtime/loopforge_runner.py
```

Supported actions:

```text
--work-dir
--code-dir
--init
--self-check
--detect
--snapshot
--verify
--finalize
```

Current runner behavior includes:

- `work/code` layout validation
- profile structure validation
- work-package completeness validation
- output path containment under `code/`
- mode-specific artifact index initialization
- final-report generation
- fail-soft Git snapshot handling

### 3.6 Cross-platform execution support is now merged

This was the major gap in the previous acceptance report. It is now resolved.

Cross-platform assets present:

```text
work/scripts/bootstrap.sh
work/scripts/bootstrap.ps1
work/scripts/smoke-test.sh
work/scripts/smoke-test.ps1
work/docs/CROSS_PLATFORM_DESIGN.md
.gitattributes
```

Config now includes:

```yaml
platform:
  official_submission_os: "linux"
  local_development_os:
    - "windows"
    - "linux"
```

Verification commands now support:

```yaml
verification:
  commands:
    default: [...]
    linux: [...]
    windows: [...]
```

Legacy list-style commands are still supported and treated as `default`.

### 3.7 Final report now contains cross-platform runtime evidence

The runner-generated final report now includes:

```text
Runtime Platform
Verification Command Selection
Cross-platform Notes
Mode Artifact Summary
```

This is a meaningful improvement because it turns environment-sensitive behavior into auditable evidence.

### 3.8 Windows local path is operational

This acceptance run verified:

```powershell
powershell -ExecutionPolicy Bypass -File work/scripts/bootstrap.ps1 -WorkDir work -CodeDir code
powershell -ExecutionPolicy Bypass -File work/scripts/smoke-test.ps1 -WorkDir work -CodeDir code
```

Both executed successfully in the current Windows environment.

### 3.9 Negative-path checks are in good shape

Current negative acceptance scenarios passed:

```text
missing-profile
verification-outside-code
profile-mode-mismatch
output-outside-code
missing-mode-rule
missing-all-verification-commands
```

This indicates the runner blocks on contract failures rather than guessing or silently proceeding.

---

## 4. Remaining Issues

## 4.1 P1: Linux entrypoint was not executed in this host

Current repository state defines the Linux-first path correctly:

```bash
bash work/scripts/bootstrap.sh --work-dir work --code-dir code
```

However, this acceptance run was performed in a Windows host without a usable `/bin/bash`, so the Linux shell path was reviewed but not executed end-to-end during this pass.

Impact:

```text
Design confidence is high.
Local execution evidence exists for Windows only in this acceptance pass.
Linux path should still be smoke-tested in an actual Linux environment before a formal contest packaging cut.
```

This is not a structural defect in the repository, but it is still a validation gap.

## 4.2 P1: Verification failure state is still overloaded

Current runner behavior still maps executed-but-failed verification into:

```text
BLOCKED_WITH_REPORT
```

That is defensible for strict fail-soft reporting, but it still conflates:

```text
contract blocked
verification executed but failed
```

Recommended future state model:

```text
VERIFIED_PATCH_READY
DEGRADED_PATCH_READY
PARTIAL_DONE
BLOCKED_WITH_REPORT
```

This is a refinement item, not a blocker for feature-development readiness.

## 4.3 P2: Linux bootstrap path is less explicit than the reviewed design preferred

Current `bootstrap.sh` invokes:

```text
work/runtime/loopforge_runner.py
```

The reviewed cross-platform design had a more explicit preference:

```text
copy runner into code/.loopforge/runtime/
then invoke the copied runtime path
```

Current behavior still produces the correct runtime copy through runner initialization, so this is not incorrect. It is mainly a transparency and reviewability improvement opportunity.

## 4.4 P2: Root-level legacy and design assets remain

The repository root still contains reference material outside `work/`, including:

```text
LoopForge_Contest_Driver_DESIGN.md
LoopForge_Cross_Platform_Design.md
LoopForge_Next_Blueprint_and_Constraints*.md
RUNNING.md
legacy rules/ and skills/ trees
```

This is acceptable during active development, but before any final packaging step the team should either:

```text
1. archive or remove non-authoritative legacy assets
or
2. make submission boundaries even more explicit in submission-facing docs
```

---

## 5. Scoring

| Area | Score | Verdict |
|---|---:|---|
| `work/` root package model | 9/10 | accepted |
| `work/code` boundary enforcement | 9/10 | accepted |
| generic Mode + Profile design | 9/10 | accepted |
| real runner implementation | 9/10 | accepted |
| runner contract validation | 9/10 | accepted |
| skill entrypoint policy | 8/10 | accepted |
| cross-platform configuration model | 9/10 | accepted |
| Windows local execution path | 9/10 | accepted |
| Linux-first submission design | 8/10 | accepted with runtime validation gap |
| final-report auditability | 9/10 | accepted |
| repository cleanup maturity | 7/10 | accepted with follow-up |
| overall feature-development readiness | 8.5/10 | ready |

---

## 6. Recommended Next Actions

The repository is ready to move into real task execution. The next work should focus on product use rather than more platform resets.

Recommended order:

```text
1. Start the first real feature-development profile adaptation under work/.
2. Run one Linux-host smoke test before formal submission packaging.
3. Optionally refine final status semantics to distinguish degraded verification from blocked contracts.
4. Clean or quarantine root-level legacy assets before a final competition handoff.
```

---

## 7. Final Acceptance Opinion

Final recommendation:

```text
ACCEPTED_WITH_MINOR_FOLLOW_UPS
```

Interpretation:

```text
The repository has passed the architecture migration phase.
The cross-platform compatibility phase is now integrated.
The platform is ready for subsequent demand-driven feature development.
Remaining work is refinement and packaging hygiene, not structural rescue.
```
