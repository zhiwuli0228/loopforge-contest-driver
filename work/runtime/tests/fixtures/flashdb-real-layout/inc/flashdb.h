#ifndef FLASHDB_H
#define FLASHDB_H

typedef enum fdb_status {
    FDB_OK = 0,
    FDB_ERROR = 1
} fdb_status_t;

typedef int (*fdb_write_fn)(const char *key, int value);

typedef struct fdb_backend {
    int capacity;
    fdb_write_fn write;
} fdb_backend_t;

fdb_status_t fdb_kv_set(fdb_backend_t *backend, const char *key, int value);

#endif
