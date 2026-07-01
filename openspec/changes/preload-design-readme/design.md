## Context

The harness currently couples two distinct inputs: task requirements and source code. It searches for README candidates below `SOURCE_ROOT`, uses README presence when selecting a project root, parses that README into the runtime contract, and retains `work/code/README.md` as a fallback. That works for the development fixture but not for the contest package: the injected source tree may contain no README, `SOURCE_ROOT` must remain untouched, and `work/code/` is not included in the real submission.

The submission therefore needs a self-contained requirement document whose location and semantics do not vary with the injected source tree. The existing `work/references/design/` remains reserved for harness engineering references; `work/design/README.md` has a different role as the active contest design contract.

## Goals / Non-Goals

**Goals:**

- Make `work/design/README.md` a required, version-controlled submission asset and the sole runtime requirement source.
- Allow source discovery and execution when `SOURCE_ROOT` contains no README.
- Preserve `SOURCE_ROOT` as a read-only external input.
- Eliminate formal runtime and packaging dependence on `work/code/`.
- Produce deterministic evidence identifying the design contract used by a run.
- Fail early and explicitly when the submission's preloaded design contract is invalid.

**Non-Goals:**

- Generating or updating the design README during a contest run.
- Copying a README from `SOURCE_ROOT` or `work/code/` at runtime.
- Defining how contest requirements are authored before they are committed to `work/design/README.md`.
- Changing the semantics of the migration, repair, or verification stages beyond their input source.
- Moving harness engineering documents out of `work/docs/` or `work/references/design/`.

## Decisions

### 1. Use one fixed authoritative requirement path

All formal runtime consumers will read `work/design/README.md`. The runner resolves this path relative to the repository/workspace root, validates it before source analysis, and passes the resolved path through the runtime contract and task packet.

This is preferred over a configurable candidate list because the submission has exactly one required contract and deterministic failure is safer than silently selecting another document. Role-specific subdirectories and manifests are unnecessary because this design has one preloaded document, not a runtime snapshot workflow.

### 2. Remove fallback behavior rather than retaining compatibility

`SOURCE_ROOT/README*` and `work/code/README.md` will not be fallback requirement sources. A README under `SOURCE_ROOT`, if present, is ordinary source-project documentation and cannot override or augment the submitted design contract. `work/code/` remains usable by local test fixtures only through explicit test setup, never through production fallback logic.

Retaining fallback compatibility was rejected because it would preserve environment-dependent behavior and could hide an invalid submission package.

### 3. Decouple source discovery from README presence

Project-root resolution will score candidates using actual C/C++ translation units, recognized build metadata, test/source structure, and containment under the supplied input root. README presence will not be a usability requirement or selection signal. If discovery cannot identify one defensible project root, execution will stop with a diagnostic report instead of guessing.

This keeps requirement selection deterministic while still allowing nonstandard source layouts to be inferred from filesystem evidence and source analysis.

### 4. Enforce a read-only SOURCE_ROOT boundary

The harness will treat resolved paths under `SOURCE_ROOT` as input-only. Generated Rust projects, task packets, reports, traces, and repair artifacts remain under the established writable `work/output`, `work/logs`, `work/result`, `logs`, or `result` destinations. Tests will verify that a run does not create, update, or delete files in the injected source tree.

Filesystem permissions remain the strongest contest-environment enforcement; application checks and tests provide defense in depth.

### 5. Validate and identify the design contract at preflight

Preflight will require `work/design/README.md` to be a readable, non-empty regular file. The runner will compute a SHA-256 digest and record the canonical design path and digest in runtime evidence. Downstream stages consume the already selected path; they do not perform independent candidate searches.

The digest is runtime evidence, not a pre-generated manifest. This avoids another submission artifact that could become stale while still detecting which exact bytes governed a run.

### 6. Treat package independence as a release gate

Tests and submission validation will run with `work/code/` absent and with a README-free `SOURCE_ROOT`. A repository scan will reject production configuration, runtime, rules, skills, and subagent contracts that name `work/code/README.md` or require `SOURCE_ROOT/README*`. Test-only fixture references may remain where explicitly scoped and must not be imported by production execution.

## Risks / Trade-offs

- [The preloaded README becomes stale relative to the intended contest requirement] → Keep it version-controlled, validate it during submission checks, and expose its digest in run evidence.
- [Removing README path hints weakens discovery for unusual source layouts] → Base discovery on translation units, build metadata, and structural evidence; block ambiguous layouts with candidate diagnostics.
- [A hidden consumer continues reading a source or fixture README] → Centralize the selected design path in the runtime contract and add repository scans plus README-free end-to-end tests.
- [A relative link in the preloaded README points at unavailable content] → Require the committed README to be self-contained for normative requirements; linked material cannot be required for runtime interpretation unless it is also submitted at a stable path.
- [Read-only behavior is difficult to guarantee on permissive filesystems] → Run mutation-detection tests and rely on contest filesystem permissions as the final enforcement layer.

## Migration Plan

1. Add and populate `work/design/README.md` as a committed submission asset.
2. Introduce the fixed design-input contract and preflight validation while recording path and digest evidence.
3. Change task-packet construction and all downstream consumers to use the selected design path.
4. Remove README requirements and scoring from source-root resolution.
5. Remove production fallback references to `work/code/README.md` and `SOURCE_ROOT/README*` across configuration, rules, skills, agents, and documentation.
6. Update unit, smoke, negative, cross-platform, and packaging tests for a README-free source tree and absent `work/code/`.
7. Run the submission validation in a package-shaped copy before adopting the new contract.

Rollback requires reverting the runner, resolver, configuration, and documentation together because the old and new input contracts are intentionally incompatible.

## Open Questions

None. The authoritative path, source mutability boundary, fallback policy, and submission contents are fixed by the contest constraints.
