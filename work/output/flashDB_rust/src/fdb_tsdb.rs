#![forbid(unsafe_code)]

pub const FDB_LOG_TAG: &str = "FDB_LOG_TAG";
pub const FDB_LOG_PREFIX2: &str = "FDB_LOG_PREFIX2";
pub const SECTOR_MAGIC_WORD: &str = "SECTOR_MAGIC_WORD";
pub const TSL_STATUS_TABLE_SIZE: &str = "TSL_STATUS_TABLE_SIZE";
pub const TSL_UINT32_ALIGN_SIZE: &str = "TSL_UINT32_ALIGN_SIZE";
pub const TSL_TIME_ALIGN_SIZE: &str = "TSL_TIME_ALIGN_SIZE";
pub const SECTOR_HDR_PADDING_SIZE: &str = "SECTOR_HDR_PADDING_SIZE";
pub const _TSL_FDBTIME_SIZE: &str = "_TSL_FDBTIME_SIZE";
pub const LOG_IDX_BASE_SIZE: &str = "LOG_IDX_BASE_SIZE";
pub const LOG_IDX_PADDING_SIZE: &str = "LOG_IDX_PADDING_SIZE";
pub const SECTOR_HDR_DATA_SIZE: &str = "SECTOR_HDR_DATA_SIZE";
pub const LOG_IDX_DATA_SIZE: &str = "LOG_IDX_DATA_SIZE";
pub const LOG_IDX_TS_OFFSET: &str = "LOG_IDX_TS_OFFSET";
pub const SECTOR_MAGIC_OFFSET: &str = "SECTOR_MAGIC_OFFSET";
pub const SECTOR_START_TIME_OFFSET: &str = "SECTOR_START_TIME_OFFSET";
pub const SECTOR_END0_TIME_OFFSET: &str = "SECTOR_END0_TIME_OFFSET";
pub const SECTOR_END0_IDX_OFFSET: &str = "SECTOR_END0_IDX_OFFSET";
pub const SECTOR_END0_STATUS_OFFSET: &str = "SECTOR_END0_STATUS_OFFSET";
pub const SECTOR_END1_TIME_OFFSET: &str = "SECTOR_END1_TIME_OFFSET";
pub const SECTOR_END1_IDX_OFFSET: &str = "SECTOR_END1_IDX_OFFSET";
pub const SECTOR_END1_STATUS_OFFSET: &str = "SECTOR_END1_STATUS_OFFSET";
pub const FAILED_ADDR: &str = "FAILED_ADDR";
pub const db_name: &str = "db_name";
pub const db_init_ok: &str = "db_init_ok";
pub const db_sec_size: &str = "db_sec_size";
pub const db_max_size: &str = "db_max_size";
pub const db_oldest_addr: &str = "db_oldest_addr";
pub const db_lock: &str = "db_lock";
pub const db_unlock: &str = "db_unlock";
pub const _FDB_WRITE_STATUS: &str = "_FDB_WRITE_STATUS";
pub const FLASH_WRITE: &str = "FLASH_WRITE";

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct LogIdxData {
    pub time: usize,
    pub log_len: u32,
    pub log_addr: u32,
    pub endif: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct QueryCountArgs {
    pub status: usize,
    pub count: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct CheckSecHdrCbArgs {
    pub db: usize,
    pub check_failed: bool,
    pub empty_num: usize,
    pub empty_addr: u32,
}

pub fn tsl_append(db: usize, blob: usize, timestamp: &mut usize) -> usize {
    // Derived from src/fdb_tsdb.c
    fdb_err_t result = FDB_NO_ERR;
    fdb_time_t cur_time = timestamp == NULL ? db.get_time() : *timestamp;
    if (blob.size ! = FDB_TSDB_FIXED_BLOB_SIZE) { FDB_INFO("Error: blob size (%zu) must equal FDB_TSDB_FIXED_BLOB_SIZE (%d)\n", blob.size, FDB_TSDB_FIXED_BLOB_SIZE);
    FDB_WRITE_ERR; } if(blob.size > db.max_len) { FDB_INFO("Warning: append length (%" PRIdMAX ") is more than the db.max_len (%" PRIdMAX ").This tsl will be dropped.\n", (intmax_t)blob.size, (intmax_t)(db.max_len)); return FDB_WRITE_ERR; } if (cur_time <= db.last_time) { FDB_INFO("Warning: current timestamp (%" PRIdMAX ") is less than or equal to the last save timestamp (%" PRIdMAX ").This tsl will be dropped.\n", (intmax_t )cur_time, (intmax_t )(db.last_time)); return FDB_WRITE_ERR; } result = update_sec_status(db, &db.cur_sec, blob, cur_time); if (result != FDB_NO_ERR) { FDB_INFO("Error: update the sector status failed (%d)", result); return result; } result = write_tsl(db, blob, cur_time); if (result != FDB_NO_ERR) { FDB_INFO("Error: write tsl failed (%d)", result); return result; } db.cur_sec.end_idx = db.cur_sec.empty_idx; db.cur_sec.end_time = cur_time; db.cur_sec.empty_idx += LOG_IDX_DATA_SIZE; db.cur_sec.empty_data -= FDB_WG_ALIGN(blob.size); db.cur_sec.remain -= LOG_IDX_DATA_SIZE + FDB_WG_ALIGN(blob.size); db.last_time = cur_time; return result
}

pub fn fdb_tsl_to_blob(tsl: usize, blob: usize) -> usize {
    // Derived from src/fdb_tsdb.c
    blob.saved.addr = tsl.addr.log.clone();
    blob.saved.meta_addr = tsl.addr.index.clone();
    blob.saved.len = tsl.log_len;
    blob
}
