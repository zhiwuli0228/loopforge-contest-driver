# FlashDB Local Fallback

This local fallback source tree exists so the execution orchestrator can self-check and exercise the FlashDB migration flow during repository development.

Scope:

- `src/flashdb.c` and `src/flashdb.h` define a small key/value-store flavored FlashDB subset.
- `tests/test_flashdb.c` lists the primary semantic scenarios that the Rust migration must preserve.

Acceptance for the fallback flow:

- generate `flashDB_rust/`
- pass `cargo build`
- pass `cargo test`
- keep unsafe usage below 10%
- pass the semantic equivalence gate
