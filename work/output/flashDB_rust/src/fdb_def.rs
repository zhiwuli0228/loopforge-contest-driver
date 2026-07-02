#![forbid(unsafe_code)]

pub const _FDB_DEF_H_: &str = "_FDB_DEF_H_";
pub const FDB_SW_VERSION: &str = "FDB_SW_VERSION";
pub const FDB_SW_VERSION_NUM: &str = "FDB_SW_VERSION_NUM";
pub const FDB_KV_NAME_MAX: &str = "FDB_KV_NAME_MAX";
pub const FDB_KV_CACHE_TABLE_SIZE: &str = "FDB_KV_CACHE_TABLE_SIZE";
pub const FDB_SECTOR_CACHE_TABLE_SIZE: &str = "FDB_SECTOR_CACHE_TABLE_SIZE";
pub const FDB_KV_USING_CACHE: &str = "FDB_KV_USING_CACHE";
pub const FDB_USING_FILE_MODE: &str = "FDB_USING_FILE_MODE";
pub const FDB_FILE_CACHE_TABLE_SIZE: &str = "FDB_FILE_CACHE_TABLE_SIZE";
pub const FDB_WRITE_GRAN: &str = "FDB_WRITE_GRAN";
pub const FDB_PRINT: &str = "FDB_PRINT";
pub const FDB_LOG_PREFIX1: &str = "FDB_LOG_PREFIX1";
pub const FDB_LOG_PREFIX2: &str = "FDB_LOG_PREFIX2";
pub const FDB_LOG_PREFIX: &str = "FDB_LOG_PREFIX";
pub const FDB_DEBUG: &str = "FDB_DEBUG";
pub const FDB_INFO: &str = "FDB_INFO";
pub const FDB_ASSERT: &str = "FDB_ASSERT";
pub const FDB_KVDB_CTRL_SET_SEC_SIZE: &str = "FDB_KVDB_CTRL_SET_SEC_SIZE";
pub const FDB_KVDB_CTRL_GET_SEC_SIZE: &str = "FDB_KVDB_CTRL_GET_SEC_SIZE";
pub const FDB_KVDB_CTRL_SET_LOCK: &str = "FDB_KVDB_CTRL_SET_LOCK";
pub const FDB_KVDB_CTRL_SET_UNLOCK: &str = "FDB_KVDB_CTRL_SET_UNLOCK";
pub const FDB_KVDB_CTRL_SET_FILE_MODE: &str = "FDB_KVDB_CTRL_SET_FILE_MODE";
pub const FDB_KVDB_CTRL_SET_MAX_SIZE: &str = "FDB_KVDB_CTRL_SET_MAX_SIZE";
pub const FDB_KVDB_CTRL_SET_NOT_FORMAT: &str = "FDB_KVDB_CTRL_SET_NOT_FORMAT";
pub const FDB_TSDB_CTRL_SET_SEC_SIZE: &str = "FDB_TSDB_CTRL_SET_SEC_SIZE";
pub const FDB_TSDB_CTRL_GET_SEC_SIZE: &str = "FDB_TSDB_CTRL_GET_SEC_SIZE";
pub const FDB_TSDB_CTRL_SET_LOCK: &str = "FDB_TSDB_CTRL_SET_LOCK";
pub const FDB_TSDB_CTRL_SET_UNLOCK: &str = "FDB_TSDB_CTRL_SET_UNLOCK";
pub const FDB_TSDB_CTRL_SET_ROLLOVER: &str = "FDB_TSDB_CTRL_SET_ROLLOVER";
pub const FDB_TSDB_CTRL_GET_ROLLOVER: &str = "FDB_TSDB_CTRL_GET_ROLLOVER";
pub const FDB_TSDB_CTRL_GET_LAST_TIME: &str = "FDB_TSDB_CTRL_GET_LAST_TIME";
pub const FDB_TSDB_CTRL_SET_FILE_MODE: &str = "FDB_TSDB_CTRL_SET_FILE_MODE";
pub const FDB_TSDB_CTRL_SET_MAX_SIZE: &str = "FDB_TSDB_CTRL_SET_MAX_SIZE";
pub const FDB_TSDB_CTRL_SET_NOT_FORMAT: &str = "FDB_TSDB_CTRL_SET_NOT_FORMAT";
pub const FDB_KV_STATUS_NUM: &str = "FDB_KV_STATUS_NUM";
pub const FDB_TSL_STATUS_NUM: &str = "FDB_TSL_STATUS_NUM";
pub const FDB_SECTOR_STORE_STATUS_NUM: &str = "FDB_SECTOR_STORE_STATUS_NUM";
pub const FDB_SECTOR_DIRTY_STATUS_NUM: &str = "FDB_SECTOR_DIRTY_STATUS_NUM";

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FdbDefaultKvNode {
    pub key: String,
    pub value: usize,
    pub value_len: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FdbDefaultKv {
    pub kvs: FdbDefaultKvNode,
    pub num: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FdbKvIterator {
    pub curr_kv: usize,
    pub iterated_cnt: u32,
    pub iterated_obj_bytes: usize,
    pub iterated_value_bytes: usize,
    pub sector_addr: u32,
    pub traversed_len: u32,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct TsdbSecInfo {
    pub check_ok: bool,
    pub status: usize,
    pub addr: u32,
    pub magic: u32,
    pub start_time: usize,
    pub end_time: usize,
    pub end_idx: u32,
    pub end_info_stat: [usize; 2],
    pub remain: usize,
    pub empty_idx: u32,
    pub empty_data: u32,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct KvCacheNode {
    pub name_crc: u32,
    pub active: u32,
    pub addr: u32,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FdbKvdb {
    pub parent: usize,
    pub default_kvs: FdbDefaultKv,
    pub gc_request: usize,
    pub in_recovery_check: usize,
    pub cur_kv: usize,
    pub cur_sector: usize,
    pub last_is_complete_del: bool,
    pub ver_num: u32,
    pub user_data: usize,
}

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct FdbTsdb {
    pub parent: usize,
    pub cur_sec: TsdbSecInfo,
    pub last_time: usize,
    pub get_time: usize,
    pub max_len: usize,
    pub rollover: usize,
    pub user_data: usize,
}
