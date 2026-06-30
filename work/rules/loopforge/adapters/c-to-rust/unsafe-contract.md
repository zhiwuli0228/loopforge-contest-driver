# C-To-Rust Unsafe Contract

- Prefer safe Rust.
- Unsafe usage must be exceptional, localized, and documented.
- Unsafe ratio must be lower than 10%.
- Prefer `#![forbid(unsafe_code)]` when the migrated module does not require unsafe boundaries.
- The ratio report must be written to `work/logs/trace/c-to-rust/unsafe-ratio.json`.
