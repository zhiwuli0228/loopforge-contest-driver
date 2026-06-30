#ifndef FLASHDB_H
#define FLASHDB_H

#include <stddef.h>

struct flashdb_record {
    const char *key;
    const char *value;
};

struct flashdb_handle {
    struct flashdb_record records[16];
    size_t count;
};

void flashdb_new(struct flashdb_handle *db);
int flashdb_set(struct flashdb_handle *db, const char *key, const char *value);
const char *flashdb_get(const struct flashdb_handle *db, const char *key);
int flashdb_delete(struct flashdb_handle *db, const char *key);
size_t flashdb_count(const struct flashdb_handle *db);

#endif
