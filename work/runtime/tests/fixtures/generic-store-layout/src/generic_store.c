typedef enum gst_status {
    GST_OK = 0,
    GST_ERROR = 1
} gst_status_t;
typedef int (*gst_write_fn)(const char *key, int value);
typedef struct gst_backend { int capacity; gst_write_fn write; } gst_backend_t;

static int write_count;

static int backend_is_valid(gst_backend_t *backend) {
    return backend && backend->write;
}

gst_status_t gst_kv_set(gst_backend_t *backend, const char *key, int value) {
    if (!backend_is_valid(backend)) return GST_ERROR;
    write_count++;
    return backend->write(key, value) == 0 ? GST_OK : GST_ERROR;
}
