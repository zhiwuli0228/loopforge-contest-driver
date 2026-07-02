#![forbid(unsafe_code)]

pub const FDB_LOG_TAG: &str = "FDB_LOG_TAG";

pub fn fdb_blob_make(blob: usize, value_buf: &usize, buf_len: usize) -> usize {
    // Derived from src/fdb_utils.c
    blob.buf = (void *)value_buf;
    blob.size = buf_len;
    blob
}
