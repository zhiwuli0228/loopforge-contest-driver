use flashdb_rust::{flashdb_count, flashdb_delete, flashdb_get, flashdb_new, flashdb_set};

#[test]
fn stores_and_reads_values() {
    let mut db = flashdb_new();
    assert_eq!(flashdb_count(&db), 0);
    assert!(flashdb_set(&mut db, "device", b"loopforge").is_none());
    assert_eq!(flashdb_get(&db, "device"), Some(&b"loopforge"[..]));
    assert_eq!(flashdb_count(&db), 1);
}

#[test]
fn replacing_a_key_returns_the_previous_value() {
    let mut db = flashdb_new();
    assert!(flashdb_set(&mut db, "mode", b"c").is_none());
    let previous = flashdb_set(&mut db, "mode", b"rust");
    assert_eq!(previous, Some(b"c".to_vec()));
    assert_eq!(flashdb_get(&db, "mode"), Some(&b"rust"[..]));
}

#[test]
fn deleting_a_key_removes_it_from_the_store() {
    let mut db = flashdb_new();
    assert!(flashdb_set(&mut db, "temp", b"42").is_none());
    assert_eq!(flashdb_delete(&mut db, "temp"), Some(b"42".to_vec()));
    assert_eq!(flashdb_get(&db, "temp"), None);
    assert_eq!(flashdb_count(&db), 0);
}
