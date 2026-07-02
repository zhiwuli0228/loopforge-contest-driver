void assert(int value);
int gst_kv_set(void *backend, const char *key, int value);

void test_kv_set(void) {
    assert(gst_kv_set((void *) 0, "key", 1) != 0);
}
