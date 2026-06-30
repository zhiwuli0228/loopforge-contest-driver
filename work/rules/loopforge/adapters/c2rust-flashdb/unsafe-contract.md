# C2Rust FlashDB Unsafe Contract

- Prefer safe Rust.
- Unsafe usage must be exceptional, localized, and documented.
- Unsafe ratio must be lower than 10%.
- Prefer `#![forbid(unsafe_code)]` when the migrated module does not require unsafe boundaries.
- The ratio report must be written to `logs/trace/c2rust/unsafe-ratio.json`.
