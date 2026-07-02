#![forbid(unsafe_code)]

pub const FDB_LOG_TAG: &str = "FDB_LOG_TAG";
pub const FDB_LOG_PREFIX2: &str = "FDB_LOG_PREFIX2";
pub const SECTOR_MAGIC_WORD: &str = "SECTOR_MAGIC_WORD";
pub const KV_MAGIC_WORD: &str = "KV_MAGIC_WORD";
pub const GC_MIN_EMPTY_SEC_NUM: &str = "GC_MIN_EMPTY_SEC_NUM";
pub const FDB_SEC_REMAIN_THRESHOLD: &str = "FDB_SEC_REMAIN_THRESHOLD";
pub const FDB_GC_EMPTY_SEC_THRESHOLD: &str = "FDB_GC_EMPTY_SEC_THRESHOLD";
pub const FDB_STR_KV_VALUE_MAX_SIZE: &str = "FDB_STR_KV_VALUE_MAX_SIZE";
pub const SECTOR_NOT_COMBINED: &str = "SECTOR_NOT_COMBINED";
pub const SECTOR_COMBINED: &str = "SECTOR_COMBINED";
pub const FAILED_ADDR: &str = "FAILED_ADDR";
pub const KV_STATUS_TABLE_SIZE: &str = "KV_STATUS_TABLE_SIZE";
pub const SECTOR_NUM: &str = "SECTOR_NUM";
pub const SECTOR_HDR_DATA_SIZE: &str = "SECTOR_HDR_DATA_SIZE";
pub const SECTOR_STORE_OFFSET: &str = "SECTOR_STORE_OFFSET";
pub const SECTOR_DIRTY_OFFSET: &str = "SECTOR_DIRTY_OFFSET";
pub const SECTOR_MAGIC_OFFSET: &str = "SECTOR_MAGIC_OFFSET";
pub const KV_HDR_DATA_SIZE: &str = "KV_HDR_DATA_SIZE";
pub const KV_MAGIC_OFFSET: &str = "KV_MAGIC_OFFSET";
pub const KV_LEN_OFFSET: &str = "KV_LEN_OFFSET";
pub const KV_NAME_LEN_OFFSET: &str = "KV_NAME_LEN_OFFSET";
pub const db_name: &str = "db_name";
pub const db_init_ok: &str = "db_init_ok";
pub const db_sec_size: &str = "db_sec_size";
pub const db_max_size: &str = "db_max_size";
pub const db_oldest_addr: &str = "db_oldest_addr";
pub const db_lock: &str = "db_lock";
pub const db_unlock: &str = "db_unlock";
pub const VER_NUM_KV_NAME: &str = "VER_NUM_KV_NAME";
pub const __is_print: &str = "__is_print";

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct KvHdrData {
    pub magic: u32,
    pub len: u32,
    pub crc32: u32,
    pub name_len: u32,
    pub value_len: u32,
    pub padding: [u32; 4],
    pub endif: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct AllocKvCbArgs {
    pub db: usize,
    pub kv_size: usize,
    pub empty_kv: u32,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct GcCbArgs {
    pub db: usize,
    pub setting_free_size: usize,
    pub last_gc_sec_addr: usize,
}

pub fn find_kv_cb(kv: usize, arg1: &mut (), arg2: &mut ()) -> usize {
    // Derived from src/fdb_kvdb.c
    const char *key = arg1;
    bool *find_ok = arg2;
    size_t key_len = strlen(key);
    if (key_len ! = kv.name_len) { return false;
    } if (kv.crc_is_ok && kv.status = = FDB_KV_WRITE && !strncmp(kv.name, key, key_len)) { *find_ok = true;
    true; } return false
}

pub fn fdb_kv_to_blob(kv: usize, blob: usize) -> usize {
    // Derived from src/fdb_kvdb.c
    blob.saved.meta_addr = kv.addr.start.clone();
    blob.saved.addr = kv.addr.value.clone();
    blob.saved.len = kv.value_len;
    blob
}

pub fn write_kv_hdr(db: usize, addr: u32, kv_hdr: usize) -> usize {
    // Derived from src/fdb_kvdb.c
    fdb_err_t result = FDB_NO_ERR;
    result = _fdb_write_status((fdb_db_t)db, addr, kv_hdr.status_table, FDB_KV_STATUS_NUM, FDB_KV_PRE_WRITE, false);
    if (result ! = FDB_NO_ERR) { return result;
    } result = _fdb_flash_write((fdb_db_t)db, addr + KV_MAGIC_OFFSET, &kv_hdr.magic, sizeof(struct kv_hdr_data) - KV_MAGIC_OFFSET, false);
    result
}

pub fn alloc_kv_cb(sector: usize, arg1: &mut (), arg2: &mut ()) -> usize {
    // Derived from src/fdb_kvdb.c
    struct alloc_kv_cb_args *arg = arg1;
    if (sector.check_ok && sector.remain > arg.kv_size + FDB_SEC_REMAIN_THRESHOLD && ((sector.status.dirty = = FDB_SECTOR_DIRTY_FALSE) || (sector.status.dirty == FDB_SECTOR_DIRTY_TRUE && !arg.db.gc_request))) { *(arg.empty_kv) = sector.empty_kv;
    true; } return false
}

pub fn new_kv_ex(db: usize, sector: usize, key_len: usize, buf_len: usize) -> u32 {
    // Derived from src/fdb_kvdb.c
    size_t kv_len = KV_HDR_DATA_SIZE + FDB_WG_ALIGN(key_len) + FDB_WG_ALIGN(buf_len);
    new_kv(db, sector, kv_len)
}

pub fn check_oldest_addr_cb(sector: usize, arg1: &mut (), arg2: &mut ()) -> usize {
    // Derived from src/fdb_kvdb.c
    uint32_t *sector_oldest_addr = (uint32_t *) arg1;
    fdb_sector_store_status_t *last_sector_status = (fdb_sector_store_status_t *)arg2;
    if (*last_sector_status = = FDB_SECTOR_STORE_EMPTY && (sector.status.store == FDB_SECTOR_STORE_FULL || sector.status.store == FDB_SECTOR_STORE_USING)) { *sector_oldest_addr = sector.addr;
    } *last_sector_status = sector.status.store.clone();
    false
}

pub fn fdb_kv_iterator_init(db: usize, itr: usize) -> usize {
    // Derived from src/fdb_kvdb.c
    itr.curr_kv.addr.start = 0;
    itr.iterated_cnt = 0;
    itr.iterated_obj_bytes = 0;
    itr.iterated_value_bytes = 0;
    itr.traversed_len = 0;
    itr.sector_addr = db_oldest_addr(db);
    itr
}
