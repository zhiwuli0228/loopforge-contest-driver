# Semantic Audit Report

- passed: `True`

```json
{
  "passed": true,
  "checks": [
    {
      "name": "cargo_manifest",
      "passed": true,
      "detail": "Cargo.toml exists"
    },
    {
      "name": "non_empty_crate",
      "passed": true,
      "detail": "crate contains non-trivial Rust source and tests"
    },
    {
      "name": "no_placeholders",
      "passed": true,
      "detail": "Rust source does not contain placeholder macros"
    },
    {
      "name": "assertive_tests",
      "passed": true,
      "detail": "each Rust test file contains assertions",
      "assert_count": 30
    },
    {
      "name": "api_mapping",
      "passed": true,
      "detail": "every mapped source API is called by generated Rust tests",
      "mapped_apis": [
        "flashdb_new",
        "flashdb_set",
        "flashdb_get",
        "flashdb_delete",
        "flashdb_count"
      ],
      "unsupported_apis": []
    },
    {
      "name": "test_mapping_gate",
      "passed": true,
      "detail": "semantic gate is backed by explicit source-to-Rust test mappings",
      "mapped_source_tests": 1,
      "source_test_count": 1,
      "rust_test_functions": 7
    },
    {
      "name": "semantic_claim_gate",
      "passed": true,
      "detail": "semantic equivalence requires an explicit positive claim backed by generated evidence",
      "semantic_equivalence_claim": "positive_semantic_claim"
    },
    {
      "name": "verification_dependency",
      "passed": true,
      "detail": "semantic gate requires successful cargo build and cargo test first"
    },
    {
      "name": "semantic_invariant_extraction",
      "passed": true,
      "detail": "source behavior produced semantic invariants",
      "invariant_count": 7
    },
    {
      "name": "semantic_invariant_tests",
      "passed": true,
      "detail": "all required invariant-derived scenarios are present and executed by cargo test",
      "required": [
        "capacity_boundary",
        "delete_head_middle_tail",
        "delete_not_found_preserves_state",
        "lookup_not_found",
        "reset_after_mutation",
        "update_existing_does_not_increment_count"
      ],
      "covered": [
        "capacity_boundary",
        "delete_head_middle_tail",
        "delete_not_found_preserves_state",
        "lookup_not_found",
        "reset_after_mutation",
        "update_existing_does_not_increment_count"
      ]
    },
    {
      "name": "repair_loop_resolved",
      "passed": true,
      "detail": "repair loop has no unresolved failures",
      "unresolved_failures": []
    }
  ],
  "failing_checks": [],
  "unresolved_failures": []
}
```
