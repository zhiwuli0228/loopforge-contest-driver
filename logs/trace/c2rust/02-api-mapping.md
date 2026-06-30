# API Mapping

- support_level: `flashdb-kv-template`

## C API To Rust Mapping

- `flashdb_count` -> `flashdb_rust::flashdb_count` or `FlashDb` method
- `flashdb_delete` -> `flashdb_rust::flashdb_delete` or `FlashDb` method
- `flashdb_get` -> `flashdb_rust::flashdb_get` or `FlashDb` method
- `flashdb_new` -> `flashdb_rust::flashdb_new` or `FlashDb` method
- `flashdb_set` -> `flashdb_rust::flashdb_set` or `FlashDb` method

## Strategy

- Data model: in-memory ordered key/value store.
- Error handling: `Option` and total functions for the fallback template.
- Ownership: owned `String` keys and `Vec<u8>` values with borrowed reads.
- Unsafe: `#![forbid(unsafe_code)]` in generated modules.
