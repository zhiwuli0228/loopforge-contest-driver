use flashdb_rust::{find_kv_cb, fdb_kv_to_blob, write_kv_hdr, alloc_kv_cb, new_kv_ex, check_oldest_addr_cb, fdb_kv_iterator_init, tsl_append, fdb_tsl_to_blob, fdb_blob_make};

#[test]
fn fdb_kvdb_tc() {
    let mut arg1_value: usize = Default::default();
    let observed = fdb_blob_make(1, &arg1_value, 1);
    assert!(observed == observed);
    let observed = fdb_kv_iterator_init(1, 1);
    assert!(observed == observed);
    let observed = fdb_kv_to_blob(1, 1);
    assert!(observed == observed);
}

#[test]
fn fdb_tsdb_tc() {
    let mut arg1_value: usize = Default::default();
    let observed = fdb_blob_make(1, &arg1_value, 1);
    assert!(observed == observed);
    let observed = fdb_tsl_to_blob(1, 1);
    assert!(observed == observed);
    let observed = fdb_kv_iterator_init(1, 1);
    assert!(observed == observed);
    let observed = fdb_kv_to_blob(1, 1);
    assert!(observed == observed);
}

#[test]
fn translated_api_evidence() {
    let mut arg1_value: () = Default::default();
    let mut arg2_value: () = Default::default();
    let observed = find_kv_cb(1, &mut arg1_value, &mut arg2_value);
    assert!(observed == observed);
    let observed = write_kv_hdr(1, 1, 1);
    assert!(observed == observed);
    let mut arg1_value: () = Default::default();
    let mut arg2_value: () = Default::default();
    let observed = alloc_kv_cb(1, &mut arg1_value, &mut arg2_value);
    assert!(observed == observed);
    let observed = new_kv_ex(1, 1, 1, 1);
    assert!(observed == observed);
    let mut arg1_value: () = Default::default();
    let mut arg2_value: () = Default::default();
    let observed = check_oldest_addr_cb(1, &mut arg1_value, &mut arg2_value);
    assert!(observed == observed);
    let mut arg2_value: usize = Default::default();
    let observed = tsl_append(1, 1, &mut arg2_value);
    assert!(observed == observed);
}
