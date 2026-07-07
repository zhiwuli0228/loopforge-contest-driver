## 1. Legacy inventory and archive scaffold

- [x] 1.1 Inventory all retained C2Rust assets and in-repo references across `work/skills/`, `work/profiles/`, `work/subagent/`, `work/rules/`, `work/runtime/`, scripts, and authoritative consistency docs.
- [x] 1.2 Create the `work/archived/c-to-rust/` archive root with subdirectories for skills, profiles, rules, subagents, and runtime helpers.
- [x] 1.3 Decide which old paths require README/stub compatibility pointers versus full relocation with no preserved executable entrypoint.

## 2. Migrate legacy asset families

- [x] 2.1 Move legacy C2Rust skills and related profile/stage/guard files into the archive namespace and mark them non-default.
- [x] 2.2 Move legacy C2Rust subagents, adapter rules, and runtime helper scripts into the archive namespace while preserving traceable historical access.
- [x] 2.3 Add archive-facing README, manifest, or pointer files wherever preserved user-visible paths need to explain the new location and non-default status.

## 3. Clean default consistency entrypoints

- [x] 3.1 Update authoritative consistency skills, profiles, runners, and scripts so their default execution chain no longer resolves to `c-to-rust` or `c2r` paths.
- [x] 3.2 Remove legacy trace namespaces such as `logs/trace/c-to-rust` from authoritative consistency runtime/report outputs and align remaining defaults to the consistency paths.
- [x] 3.3 Update any authoritative docs or driver instructions that still present archived C2Rust assets as active dependencies of the default workflow.

## 4. Validation and completion checks

- [x] 4.1 Add focused validation that fails when authoritative consistency entrypoints still reference archived C2Rust skills, profiles, stages, guards, subagents, runtime helpers, or trace namespaces.
- [x] 4.2 Run a default consistency-check smoke path to confirm the authoritative workflow remains usable after legacy isolation.
- [x] 4.3 Verify archived assets remain discoverable for historical inspection without being exposed as default consistency-check entrypoints.
