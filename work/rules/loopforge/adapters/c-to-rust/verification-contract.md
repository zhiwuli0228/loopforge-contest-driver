# C-To-Rust Verification Contract

Run inside the runtime-derived Rust output project:

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

- `work/result/output.md`
- `work/result/issues/00-summary.md`
- `work/logs/trace/c-to-rust/06-verification-report.md`
- `work/logs/trace/c-to-rust/unsafe-ratio.json`
