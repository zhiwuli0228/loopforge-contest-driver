# Language Adapter Layer

This package converts repository-specific source evidence into the shared
`work.core.implementation_model` contract.

Rules:

- `java` is the default adapter when Java project detection succeeds.
- `generic` is the fallback adapter when Java detection fails or is incomplete.
- All adapters must emit canonical implementation objects with:
  - shared neutral kinds
  - implementation evidence
  - adapter provenance via `adapter_id`
  - optional adapter-specific metadata only under `extensions`
- Shared stage artifacts and report paths remain unchanged regardless of adapter.
