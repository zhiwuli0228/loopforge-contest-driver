# Verification Rules

## Verification Source

Verification commands must come from `loopforge.config.yaml`.

The agent must not invent verification commands as the source of truth.

## Preferred Verification Commands

When configured, preferred checks include:

1. `cargo fmt --check`
2. `cargo clippy --all-targets --all-features -- -D warnings`
3. `cargo test --all`
4. project-specific regression tests
5. compatibility cross-check commands for migration tasks

## Compatibility Verification

For migration tasks, verification should prioritize semantic equivalence.

Recommended evidence:

1. original C tests still pass;
2. migrated target-stack tests pass;
3. cross-check output is equivalent when available;
4. CLI output or golden files match when applicable;
5. property or fuzz tests are preserved when available.

## Degraded Verification

If the environment lacks required toolchains, external libraries, or test data, record degraded verification.

The verification report must include:

1. command attempted;
2. working directory;
3. exit code;
4. stdout/stderr summary;
5. reason for failure;
6. whether the failure is code-related or environment-related;
7. next recommended command.
