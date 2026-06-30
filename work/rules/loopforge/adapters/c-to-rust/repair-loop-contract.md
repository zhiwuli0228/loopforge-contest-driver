# C-To-Rust Repair Loop Contract

- The execution orchestrator owns the compile-test-repair loop.
- Repair attempts must be driven by actual cargo diagnostics.
- Fixed fallback failure text is forbidden.
- The repair loop must stop at the configured maximum repair round count.
- READY is valid only after cargo build, cargo test, unsafe gate, and semantic gate all pass.
