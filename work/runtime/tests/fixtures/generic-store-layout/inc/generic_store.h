#ifndef GENERIC_STORE_H
#define GENERIC_STORE_H

typedef enum gst_status {
    GST_OK = 0,
    GST_ERROR = 1
} gst_status_t;

typedef int (*gst_write_fn)(const char *key, int value);

typedef struct gst_backend {
    int capacity;
    gst_write_fn write;
} gst_backend_t;

gst_status_t gst_kv_set(gst_backend_t *backend, const char *key, int value);

#endif
