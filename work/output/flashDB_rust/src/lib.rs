#![forbid(unsafe_code)]

pub mod fdb;
pub mod fdb_file;
pub mod fdb_kvdb;
pub mod fdb_tsdb;
pub mod fdb_utils;
pub mod fdb_low_lvl;
pub mod flashdb;
pub mod fdb_cfg_template;
pub mod fdb_def;
pub mod ports;

pub use fdb_kvdb::find_kv_cb;
pub use fdb_kvdb::fdb_kv_to_blob;
pub use fdb_kvdb::write_kv_hdr;
pub use fdb_kvdb::alloc_kv_cb;
pub use fdb_kvdb::new_kv_ex;
pub use fdb_kvdb::check_oldest_addr_cb;
pub use fdb_kvdb::fdb_kv_iterator_init;
pub use fdb_tsdb::tsl_append;
pub use fdb_tsdb::fdb_tsl_to_blob;
pub use fdb_utils::fdb_blob_make;

pub fn generated_module_count() -> usize {
    10
}
