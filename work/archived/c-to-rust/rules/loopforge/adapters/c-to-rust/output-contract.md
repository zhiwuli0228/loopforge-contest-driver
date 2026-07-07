# C-To-Rust Output Contract

The generated Rust project must be located at a runtime-derived repository-root output directory:

- `<runtime-derived-output-project>/Cargo.toml`
- `<runtime-derived-output-project>/src/`
- `<runtime-derived-output-project>/tests/`

Do not place the generated Rust project under `SOURCE_ROOT` or any runtime-artifact directory.

Output quality gates:

- the crate must contain real Rust implementation code
- empty crates are forbidden
- generated tests must contain assertions
- `todo!()` and `unimplemented!()` are forbidden
