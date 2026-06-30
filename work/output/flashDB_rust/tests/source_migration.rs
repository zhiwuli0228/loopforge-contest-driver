use flashdb_rust::{flashdb_new, flashdb_set, flashdb_get, flashdb_delete, flashdb_count};

#[test]
fn test_flashdb() {
    let mut db = flashdb_rust::flashdb::FlashdbHandle::default();
    flashdb_new(&mut db);
    assert_eq!(flashdb_set(&mut db, "alpha", "one"), 0);
    assert_eq!(flashdb_count(&db), 1);
    assert_eq!(flashdb_get(&db, "alpha"), Some("one".to_string()));
    assert_eq!(flashdb_set(&mut db, "alpha", "two"), 0);
    assert_eq!(flashdb_get(&db, "alpha"), Some("two".to_string()));
    assert_eq!(flashdb_delete(&mut db, "alpha"), 0);
    assert_eq!(flashdb_count(&db), 0);
    assert_eq!(flashdb_get(&db, "alpha"), None);
}
