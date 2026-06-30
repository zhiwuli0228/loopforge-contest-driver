#![forbid(unsafe_code)]

mod flashdb;

pub use flashdb::FlashDb;
pub use flashdb::flashdb_count;
pub use flashdb::flashdb_delete;
pub use flashdb::flashdb_get;
pub use flashdb::flashdb_new;
pub use flashdb::flashdb_set;
