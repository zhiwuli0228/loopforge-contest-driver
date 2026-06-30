use flashdb_rust::*;
use flashdb_rust::flashdb::FlashdbHandle;

#[test]
fn test_reset_after_mutation() {
    let mut db = FlashdbHandle::default();
    flashdb_set(&mut db, "old", "value");
    flashdb_new(&mut db);
    assert_eq!(flashdb_set(&mut db, "new", "value"), 0);
    assert_eq!(flashdb_get(&db, "new"), Some("value".to_string()));
    assert_eq!(flashdb_get(&db, "old"), None);
}

#[test]
fn test_capacity_boundary() {
    let mut db = FlashdbHandle::default();
    for i in 0..16 {
        let key = format!("key-{i}");
        assert_eq!(flashdb_set(&mut db, &key, "value"), 0);
    }
    assert_ne!(flashdb_set(&mut db, "overflow", "value"), 0);
    assert_eq!(flashdb_count(&db), 16);
    assert_eq!(flashdb_get(&db, "key-0"), Some("value".to_string()));
}

#[test]
fn test_lookup_not_found() {
    let mut db = FlashdbHandle::default();
    assert_eq!(flashdb_get(&db, "missing"), None);
    flashdb_set(&mut db, "present", "value");
    assert_eq!(flashdb_get(&db, "missing"), None);
}

#[test]
fn test_delete_not_found_preserves_state() {
    let mut db = FlashdbHandle::default();
    flashdb_set(&mut db, "present", "value");
    assert_ne!(flashdb_delete(&mut db, "missing"), 0);
    assert_eq!(flashdb_get(&db, "present"), Some("value".to_string()));
    assert_eq!(flashdb_count(&db), 1);
}

#[test]
fn test_delete_head_middle_tail() {
    let mut db = FlashdbHandle::default();
    flashdb_set(&mut db, "head", "1");
    flashdb_set(&mut db, "middle", "2");
    flashdb_set(&mut db, "tail", "3");
    assert_eq!(flashdb_delete(&mut db, "head"), 0);
    assert_eq!(flashdb_get(&db, "middle"), Some("2".to_string()));
    assert_eq!(flashdb_delete(&mut db, "middle"), 0);
    assert_eq!(flashdb_get(&db, "tail"), Some("3".to_string()));
    assert_eq!(flashdb_delete(&mut db, "tail"), 0);
    assert_eq!(flashdb_count(&db), 0);
}

#[test]
fn test_update_existing_does_not_increment_count() {
    let mut db = FlashdbHandle::default();
    assert_eq!(flashdb_set(&mut db, "key", "one"), 0);
    assert_eq!(flashdb_set(&mut db, "key", "two"), 0);
    assert_eq!(flashdb_get(&db, "key"), Some("two".to_string()));
    assert_eq!(flashdb_count(&db), 1);
}
