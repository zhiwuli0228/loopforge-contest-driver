# Behavior Baseline

## Product Model

FlashDB provides two storage modes:

1. KVDB: a key-value database with string and blob values.
2. TSDB: a time-series database with timestamped log records and mutable record status.

## KVDB Baseline

Based on `code/FlashDB/docs/api.md` and `code/FlashDB/tests/fdb_kvdb_tc.c`, the Rust migration must preserve at least these behaviors:

- `fdb_kvdb_init` initializes a database instance against a named storage location.
- `fdb_kv_set` inserts a new KV when the key does not exist.
- `fdb_kv_set` overwrites an existing KV when the key already exists.
- `fdb_kv_set_blob` stores arbitrary binary values through the blob abstraction.
- `fdb_kv_get` returns the string value for an existing key and a null-like failure for a missing key.
- `fdb_kv_get_blob` reads previously written blob data into caller-owned storage.
- `fdb_kv_del` marks a KV as deleted so later reads fail.
- `fdb_kv_set_default` resets the KV store to its initial default state.
- iterator APIs can traverse stored KVs and expose metadata needed for blob conversion.

Important internal behavior exposed by tests:

- KV overwrite is modeled as delete-then-add, which affects space consumption.
- KV deletion does not immediately reclaim capacity.
- GC can move live KV entries across sectors while preserving logical values.
- scale-up behavior keeps old data valid after database size expansion.

## TSDB Baseline

Based on `code/FlashDB/docs/api.md` and `code/FlashDB/tests/fdb_tsdb_tc.c`, the Rust migration must preserve at least these behaviors:

- `fdb_tsdb_init` initializes a time-series database with a timestamp callback.
- `fdb_tsl_append` appends log records in time order.
- `fdb_tsl_iter` traverses all records.
- `fdb_tsl_iter_reverse` traverses records in reverse order.
- `fdb_tsl_iter_by_time` traverses records within a time range and supports reverse traversal when `from > to`.
- `fdb_tsl_query_count` counts records by time range and status.
- `fdb_tsl_set_status` updates record status in the allowed progression order.
- `fdb_tsl_clean` clears logical content so later iteration returns no records.

Important behavior exposed by tests:

- TSDB time values come from the configured callback, not from wall clock assumptions inside the database.
- Time-range iteration is sensitive to sector boundaries and off-by-one edges.
- Large appended blobs must survive restart and later counting queries.

## Restart and Persistence Baseline

Both KVDB and TSDB tests simulate reboot by deinit + init. The Rust migration must define and preserve a restart model where:

- committed data remains readable after re-open;
- deleted or cleaned data remains deleted or cleaned after re-open;
- metadata needed for iteration and counting survives re-open.
