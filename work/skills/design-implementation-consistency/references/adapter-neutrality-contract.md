# Adapter-Neutral Contract

Adapter-neutral invariants:

- The stage graph is always `dic-00` through `dic-09`.
- Design and implementation models keep the same artifact paths regardless of adapter.
- Drift and risk outputs keep the same schemas and report locations regardless of adapter.
- Final statuses do not change between Java and Generic execution.

Java-specific behavior is limited to:

- language detection
- framework and source pattern detection
- verification command preference selection

Generic fallback behavior:

- keeps the same stage outputs
- keeps the same guard boundaries
- emits the same final report paths
- may report reduced extraction fidelity, but not a different contract shape
