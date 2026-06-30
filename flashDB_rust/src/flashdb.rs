#![forbid(unsafe_code)]

pub const FLASHDB_H: &str = "FLASHDB_H";

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FlashdbRecord {
    pub key: String,
    pub value: String,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FlashdbHandle {
    pub records: Vec<FlashdbRecord>,
    pub count: usize,
}

pub fn flashdb_new(db: &mut FlashdbHandle) {
    // Derived from src/flashdb.c
    db.count = 0;
}

pub fn flashdb_set(db: &mut FlashdbHandle, key: &str, value: &str) -> i32 {
    // Derived from src/flashdb.c
    for item in db.records.iter_mut().take(db.count) {
        if item.key == key {
            item.value = value.to_string();
            return 0;
        }
    }
    if db.count >= 16 {
        return -1;
    }
    let mut new_item = FlashdbRecord::default();
    new_item.key = key.to_string();
    new_item.value = value.to_string();
    db.records.push(new_item);
    db.count += 1;
    0
}

pub fn flashdb_get(db: &FlashdbHandle, key: &str) -> Option<String> {
    // Derived from src/flashdb.c
    for item in db.records.iter().take(db.count) {
        if item.key == key {
            return Some(item.value.clone());
        }
    }
    None
}

pub fn flashdb_delete(db: &mut FlashdbHandle, key: &str) -> i32 {
    // Derived from src/flashdb.c
    for index in 0..db.count {
        if db.records[index].key == key {
            db.records.remove(index);
            db.count -= 1;
            return 0;
        }
    }
    -1
}

pub fn flashdb_count(db: &FlashdbHandle) -> usize {
    // Derived from src/flashdb.c
    db.count
}
