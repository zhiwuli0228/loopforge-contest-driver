# C2Rust FlashDB Output Contract

The generated Rust project must be located at repository root:

- `flashDB_rust/Cargo.toml`
- `flashDB_rust/src/`
- `flashDB_rust/tests/`

Do not place the generated Rust project under `SOURCE_ROOT` or any runtime-artifact directory.

Output quality gates:

- the crate must contain real Rust implementation code
- empty crates are forbidden
- generated tests must contain assertions
- `todo!()` and `unimplemented!()` are forbidden
