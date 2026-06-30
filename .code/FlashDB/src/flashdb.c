#include "flashdb.h"

#include <stddef.h>
#include <string.h>

void flashdb_new(struct flashdb_handle *db) {
    db->count = 0;
}

int flashdb_set(struct flashdb_handle *db, const char *key, const char *value) {
    for (size_t i = 0; i < db->count; ++i) {
        if (strcmp(db->records[i].key, key) == 0) {
            db->records[i].value = value;
            return 0;
        }
    }
    if (db->count >= 16) {
        return -1;
    }
    db->records[db->count].key = key;
    db->records[db->count].value = value;
    db->count += 1;
    return 0;
}

const char *flashdb_get(const struct flashdb_handle *db, const char *key) {
    for (size_t i = 0; i < db->count; ++i) {
        if (strcmp(db->records[i].key, key) == 0) {
            return db->records[i].value;
        }
    }
    return NULL;
}

int flashdb_delete(struct flashdb_handle *db, const char *key) {
    for (size_t i = 0; i < db->count; ++i) {
        if (strcmp(db->records[i].key, key) == 0) {
            for (size_t j = i; j + 1 < db->count; ++j) {
                db->records[j] = db->records[j + 1];
            }
            db->count -= 1;
            return 0;
        }
    }
    return -1;
}

size_t flashdb_count(const struct flashdb_handle *db) {
    return db->count;
}
