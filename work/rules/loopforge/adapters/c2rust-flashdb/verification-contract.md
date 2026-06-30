# C2Rust FlashDB Verification Contract

Run inside `flashDB_rust`:

```bash
cargo build
cargo test
```

READY gate policy:

- `cargo build` must pass
- `cargo test` must pass
- unsafe gate must pass
- semantic gate must pass
- repair loop gate must pass
- test mapping gate must pass

Required final files:

- `result/output.md`
- `result/issues/00-summary.md`
- `logs/trace/c2rust/06-verification-report.md`
- `logs/trace/c2rust/unsafe-ratio.json`
