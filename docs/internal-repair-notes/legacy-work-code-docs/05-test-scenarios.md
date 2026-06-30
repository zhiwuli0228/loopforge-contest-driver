# Test Scenarios

## Required Verification

Configured verification commands are read from `loopforge.config.yaml`.

Target commands remain:

- `cargo fmt --check`
- `cargo clippy --all-targets --all-features -- -D warnings`
- `cargo test --all`

## Minimum Rust Regression Coverage

The Rust project should add tests that cover at least:

### KVDB

- initialize a file-backed KV database;
- set and get string KV values;
- set and get blob KV values;
- delete KV values and confirm lookup failure;
- reset to default KV state if defaults are modeled;
- reopen the database and confirm persistence;
- exercise overwrite and GC-sensitive update scenarios.

### TSDB

- initialize a file-backed TSDB with a deterministic time callback;
- append records and iterate in forward order;
- iterate by exact time and by time range;
- count records by status and time range;
- update status and verify counts change accordingly;
- clean the database and confirm subsequent iteration is empty;
- reopen the database and confirm persisted records remain queryable.

## Source-of-Truth References

Behavioral expectations should be cross-checked against:

- `code/FlashDB/tests/fdb_kvdb_tc.c`
- `code/FlashDB/tests/fdb_tsdb_tc.c`
- `code/FlashDB/docs/api.md`
- `code/FlashDB/docs/configuration.md`

## Degraded Verification Policy

If the Rust project is not yet complete enough to run all Cargo checks, record the gap explicitly in:

`code/.loopforge/consistency/06-verification-report.md`

Acceptable degraded reasons include:

- Rust workspace not yet bootstrapped;
- API subset migrated but test harness incomplete;
- storage compatibility layer still under construction.

Unacceptable degraded reasons include:

- using placeholder `sum.c`-style requirements unrelated to FlashDB;
- claiming FlashDB parity without KVDB and TSDB regression evidence.
