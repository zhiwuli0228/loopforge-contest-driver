#![forbid(unsafe_code)]

pub mod flashdb;

pub use flashdb::flashdb_new;
pub use flashdb::flashdb_set;
pub use flashdb::flashdb_get;
pub use flashdb::flashdb_delete;
pub use flashdb::flashdb_count;

pub fn generated_module_count() -> usize {
    1
}
