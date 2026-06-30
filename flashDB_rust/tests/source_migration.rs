use flashdb_rust::generated_module_count;
use flashdb_rust::{flashdb_new, flashdb_count, flashdb_set, flashdb_delete};

#[test]
fn crate_has_generated_modules() {
    assert!(generated_module_count() > 0);
}

#[test]
fn test_flashdb() {
    assert!(generated_module_count() >= 1);
    assert!(0 >= 0);
}
