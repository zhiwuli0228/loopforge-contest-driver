#![forbid(unsafe_code)]

use std::collections::BTreeMap;

#[derive(Debug, Default, Clone)]
pub struct FlashDb {
    entries: BTreeMap<String, Vec<u8>>,
}

impl FlashDb {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn set(&mut self, key: &str, value: &[u8]) -> Option<Vec<u8>> {
        self.entries.insert(key.to_string(), value.to_vec())
    }

    pub fn get(&self, key: &str) -> Option<&[u8]> {
        self.entries.get(key).map(Vec::as_slice)
    }

    pub fn delete(&mut self, key: &str) -> Option<Vec<u8>> {
        self.entries.remove(key)
    }

    pub fn count(&self) -> usize {
        self.entries.len()
    }
}

pub fn flashdb_new() -> FlashDb {
    FlashDb::new()
}

pub fn flashdb_set(db: &mut FlashDb, key: &str, value: &[u8]) -> Option<Vec<u8>> {
    db.set(key, value)
}

pub fn flashdb_get<'a>(db: &'a FlashDb, key: &str) -> Option<&'a [u8]> {
    db.get(key)
}

pub fn flashdb_delete(db: &mut FlashDb, key: &str) -> Option<Vec<u8>> {
    db.delete(key)
}

pub fn flashdb_count(db: &FlashDb) -> usize {
    db.count()
}
