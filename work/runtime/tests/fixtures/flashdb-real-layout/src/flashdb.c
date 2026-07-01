typedef enum fdb_status {
    FDB_OK = 0,
    FDB_ERROR = 1
} fdb_status_t;
typedef int (*fdb_write_fn)(const char *key, int value);
typedef struct fdb_backend { int capacity; fdb_write_fn write; } fdb_backend_t;

static int write_count;

static int backend_is_valid(fdb_backend_t *backend) {
    return backend && backend->write;
}

fdb_status_t fdb_kv_set(fdb_backend_t *backend, const char *key, int value) {
    if (!backend_is_valid(backend)) return FDB_ERROR;
    write_count++;
    return backend->write(key, value) == 0 ? FDB_OK : FDB_ERROR;
}
