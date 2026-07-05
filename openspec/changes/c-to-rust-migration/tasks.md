# Implementation Tasks

## Batch 1: Foundational Data Types and Constants

关联 capability: foundational-types
关联 spec: specs/foundational-types/spec.md
C 源文件: inc/fdb_def.h, inc/fdb_low_lvl.h, inc/fdb_cfg_template.h
Rust 目标文件: src/fdb_def.rs, src/fdb_low_lvl.rs, src/fdb_cfg_template.rs
依赖 batch: 无

### 实现
- [x] 1.1 定义 FdbError enum (repr i32, discriminants 0-8) — REQ-foundational-types-001
- [x] 1.2 定义 FdbKvStatus enum (6 variants, Unused=0..ErrHdr=5) — REQ-foundational-types-003
- [x] 1.3 定义 FdbTslStatus enum (6 variants, Unused=0..UserStatus2=5) — REQ-foundational-types-003
- [x] 1.4 定义 FdbSectorStoreStatus enum (4 variants, Unused=0..Full=3) — REQ-foundational-types-003
- [x] 1.5 定义 FdbSectorDirtyStatus enum (4 variants, Unused=0..Gc=3) — REQ-foundational-types-003
- [x] 1.6 定义 FdbDbType enum (Kv=0, Ts=1)
- [x] 1.7 定义 FdbKv struct with #[repr(C)] — REQ-foundational-types-002
- [x] 1.8 定义 FdbTsl struct with #[repr(C)]
- [x] 1.9 定义 FdbBlob struct (Vec<u8> based)
- [x] 1.10 定义 FdbKvIterator struct
- [x] 1.11 定义 KvdbSecInfo struct with #[repr(C)]
- [x] 1.12 定义 TsdbSecInfo struct with #[repr(C)]
- [x] 1.13 定义 KvCacheNode struct
- [x] 1.14 定义 FdbDefaultKv/FdbDefaultKvNode structs
- [x] 1.15 定义 FdbDb struct (base database type) — REQ-foundational-types-002
- [x] 1.16 定义 FdbKvdb struct (KVDB with composition over FdbDb)
- [x] 1.17 定义 FdbTsdb struct (TSDB with composition over FdbDb)
- [x] 1.18 定义 FdbTime type alias (i64)
- [x] 1.19 定义 FdbGetTime 回调类型
- [x] 1.20 定义 FdbTslCb 回调类型
- [x] 1.21 定义常量: FDB_KV_NAME_MAX(64), FDB_KV_CACHE_TABLE_SIZE(64), FDB_SECTOR_CACHE_TABLE_SIZE(8), FDB_FILE_CACHE_TABLE_SIZE(2)
- [x] 1.22 定义 fdb_status_table_size const fn — 支持所有 FDB_WRITE_GRAN 值
- [x] 1.23 定义 fdb_wg_align / fdb_align / fdb_wg_align_down / fdb_align_down const fns
- [x] 1.24 定义 FDB_BYTE_ERASED(0xFF), FDB_BYTE_WRITTEN(0x00), FDB_DATA_UNUSED, FDB_FAILED_ADDR
- [x] 1.25 定义 FDB_WRITE_GRAN, FDB_SW_VERSION 等编译时常量
- [x] 1.26 定义 FDB_SECTOR_STORE_STATUS_NUM(4), FDB_SECTOR_DIRTY_STATUS_NUM(4), FDB_STORE_STATUS_TABLE_SIZE, FDB_DIRTY_STATUS_TABLE_SIZE

### 单元测试
- [x] 1.T1 #[test] fn test_default_structs — 覆盖场景: 所有 struct 实现 Default trait, 默认值合理
- [ ] 1.T2 #[test] fn test_fdb_error_discriminants — 覆盖场景: FdbError::NoErr as i32 == 0, 所有枚举 discriminant 与 C 一致
- [ ] 1.T3 #[test] fn test_kv_status_default_is_unused — 覆盖场景: FdbKvStatus::default() == FdbKvStatus::Unused, discriminant == 0

### 验证
- [x] 1.V1 cargo build 通过
- [x] 1.V2 cargo test 通过

---

## Batch 2: CRC32 Checksum Computation

关联 capability: crc32-computation
关联 spec: specs/crc32-computation/spec.md
C 源文件: src/fdb_utils.c (fdb_calc_crc32 at line 77)
Rust 目标文件: src/fdb_utils.rs
依赖 batch: 无

### 实现
- [x] 2.1 实现 CRC32_TABLE (256-entry static lookup table, 与 C crc32_table[] 一致) — REQ-crc32-computation-002
- [x] 2.2 实现 fn fdb_calc_crc32(init_crc: u32, buf: &[u8]) -> u32 — REQ-crc32-computation-001, REQ-crc32-computation-003

### 单元测试
- [x] 2.T1 #[test] fn test_crc32_known_values — 覆盖场景: "123456789" => 0xCBF43926 (已知答案测试)
- [x] 2.T2 #[test] fn test_crc32_empty — 覆盖场景: 空 buffer 返回 0x00000000
- [x] 2.T3 #[test] fn test_crc32_incremental — 覆盖场景: 增量计算与一次性计算等价

### 验证
- [x] 2.V1 cargo build 通过
- [x] 2.V2 cargo test crc32 通过

---

## Batch 3: Flash Status Table Management

关联 capability: flash-status-table
关联 spec: specs/flash-status-table/spec.md
C 源文件: src/fdb_utils.c (lines 91-218)
Rust 目标文件: src/fdb_utils.rs
依赖 batch: 1

### 实现
- [x] 3.1 实现 fn fdb_set_status(status_table: &mut [u8], status_num: usize, status_index: usize) -> usize — REQ-flash-status-table-001
- [ ] 3.2 修复 fdb_get_status 完整实现，匹配 C 的字节/位扫描逻辑 — REQ-flash-status-table-002
- [x] 3.3 实现 fn fdb_write_status(flash: &mut dyn FlashStorage, addr: u32, status_table: &mut [u8], status_num: usize, status_index: usize) -> Result<(), FdbError> — REQ-flash-status-table-003
- [x] 3.4 实现 fn fdb_read_status(flash: &dyn FlashStorage, addr: u32, status_table: &mut [u8], total_num: usize) -> Result<usize, FdbError>
- [x] 3.5 实现 fn fdb_continue_ff_addr(flash: &dyn FlashStorage, start: u32, end: u32) -> Result<u32, FdbError> — REQ-flash-status-table-004
- [ ] 3.6 添加 FDB_WRITE_GRAN 可变性支持: 当前硬编码 WRITE_GRAN=1; 需要支持 parametrized/test-time 配置(通过 feature flag 或 const generic)

### 单元测试
- [x] 3.T1 #[test] fn test_fdb_set_status — 覆盖场景: 基本 status 设置，非零 byte_index
- [ ] 3.T2 #[test] fn test_status_table_all_gran — 覆盖场景: WRITE_GRAN ∈ {1, 8, 32, 64, 128, 256} 下 set/get round-trip 正确 (REQ-TEST-003)
- [ ] 3.T3 #[test] fn test_get_status_erased_table — 覆盖场景: 全 0xFF 的 status table 返回 0 (UNUSED)
- [ ] 3.T4 #[test] fn test_get_status_full_table — 覆盖场景: 全写入的 status table 返回 status_num-1
- [ ] 3.T5 #[test] fn test_continue_ff_addr_boundary — 覆盖场景: 全擦除范围返回对齐的起始地址, 全写入范围返回 end (REQ-TEST-004)

### 验证
- [x] 3.V1 cargo build 通过
- [x] 3.V2 cargo test 通过

---

## Batch 4: Blob Data Abstraction

关联 capability: blob-abstraction
关联 spec: specs/blob-abstraction/spec.md
C 源文件: src/fdb_utils.c (lines 221-254)
Rust 目标文件: src/fdb_utils.rs
依赖 batch: 1

### 实现
- [x] 4.1 实现 fn fdb_blob_make(buf: Vec<u8>) -> FdbBlob — REQ-blob-abstraction-001
- [x] 4.2 实现 fn fdb_blob_read(blob: &mut FdbBlob, flash: &dyn FlashStorage) -> usize — REQ-blob-abstraction-002
- [x] 4.3 实现 FdbBlob::new(buf: Vec<u8>) -> Self 构造函数

### 单元测试
- [x] 4.T1 #[test] fn test_blob_make — 覆盖场景: 正常 buffer 创建 blob, size/buf 正确
- [ ] 4.T2 #[test] fn test_blob_read_empty — 覆盖场景: size=0 或 saved_len=0 时不执行 flash 读取
- [ ] 4.T3 #[test] fn test_blob_read_truncation — 覆盖场景: blob.size < saved_len 时只读取 blob.size 字节不溢出
- [ ] 4.T4 #[test] fn test_blob_make_empty_buffer — 覆盖场景: 空 Vec 创建 blob, size==0

### 验证
- [x] 4.V1 cargo build 通过
- [x] 4.V2 cargo test 通过

---

## Batch 5: File-based Storage Backend

关联 capability: file-storage-backend
关联 spec: specs/file-storage-backend/spec.md
C 源文件: src/fdb_file.c (all 317 lines)
Rust 目标文件: src/fdb_file.rs
依赖 batch: 1

### 实现
- [ ] 5.1 实现 fn get_db_file_path(dir: &str, name: &str, sec_addr: u32, sec_size: u32) -> String — REQ-file-storage-backend-001
- [ ] 5.2 实现 FileCache struct (LRU, FDB_FILE_CACHE_TABLE_SIZE=2 slots)
- [ ] 5.3 实现 fn get_file_from_cache(db: &FdbDb, sec_addr: u32) -> Option<usize>
- [ ] 5.4 实现 fn update_file_cache(db: &mut FdbDb, sec_addr: u32, file: std::fs::File)
- [ ] 5.5 实现 fn open_db_file(db: &mut FdbDb, sec_addr: u32, clean: bool) -> Result<std::fs::File, FdbError> — REQ-file-storage-backend-002
- [ ] 5.6 实现 fn fdb_file_read(db: &mut FdbDb, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError> — REQ-file-storage-backend-004
- [ ] 5.7 实现 fn fdb_file_write(db: &mut FdbDb, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError> — REQ-file-storage-backend-004
- [ ] 5.8 实现 fn fdb_file_erase(db: &mut FdbDb, addr: u32, size: usize) -> Result<(), FdbError> — REQ-file-storage-backend-003
- [ ] 5.9 实现 fn close_all_files(db: &mut FdbDb) — 用于 deinit 清理

### 单元测试
- [ ] 5.T1 #[test] fn test_get_db_file_path — 覆盖场景: dir/name.fdb.2 路径构建，sector index = addr/sec_size
- [ ] 5.T2 #[test] fn test_file_cache_lru_eviction — 覆盖场景: 2-slot cache 满时最旧文件被驱逐 (REQ-TEST-005)
- [ ] 5.T3 #[test] fn test_file_read_write_in_temp_dir — 覆盖场景: 临时目录中创建文件、写入、读取、验证数据
- [ ] 5.T4 #[test] fn test_file_erase_fills_ff — 覆盖场景: erase 后所有字节为 0xFF
- [ ] 5.T5 #[test] fn test_open_clean_truncates_and_fills — 覆盖场景: clean=true 时 truncate 到 sec_size 并填充 0xFF

### 验证
- [ ] 5.V1 cargo build 通过
- [ ] 5.V2 cargo test file 通过

---

## Batch 6: Flash I/O Dispatch Layer

关联 capability: flash-io-dispatch
关联 spec: specs/flash-io-dispatch/spec.md
C 源文件: src/fdb_utils.c (lines 257-350)
Rust 目标文件: src/fdb_utils.rs, src/ports.rs
依赖 batch: 1, 5

### 实现
- [x] 6.1 定义 FlashStorage trait (read/erase/write 方法) — REQ-flash-io-dispatch-001/002/003
- [x] 6.2 实现 RamFlash struct (Vec<u8> backed, AND-semantics write, 0xFF erase)
- [x] 6.3 实现 fn fdb_flash_read(flash: &dyn FlashStorage, addr: u32, buf: &mut [u8], size: usize) -> Result<(), FdbError> — REQ-flash-io-dispatch-001
- [x] 6.4 实现 fn fdb_flash_erase(flash: &mut dyn FlashStorage, addr: u32, size: usize) -> Result<(), FdbError> — REQ-flash-io-dispatch-002
- [x] 6.5 实现 fn fdb_flash_write(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError> — REQ-flash-io-dispatch-003
- [x] 6.6 实现 fn fdb_flash_write_align(flash: &mut dyn FlashStorage, addr: u32, buf: &[u8], size: usize) -> Result<(), FdbError> — REQ-flash-io-dispatch-004
- [ ] 6.7 实现 FileFlash struct (std::fs::File backed, 实现 FlashStorage trait, 使用 fdb_file.rs 的函数)

### 单元测试
- [x] 6.T1 #[test] fn test_ram_flash_read_write — 覆盖场景: RamFlash 读写验证, 初始 0xFF, 写入后数据正确
- [x] 6.T2 #[test] fn test_ram_flash_erase — 覆盖场景: erase 后所有字节恢复 0xFF
- [ ] 6.T3 #[test] fn test_flash_write_align_padding — 覆盖场景: WRITE_GRAN=32 时 3 字节数据 padding 为 4 字节写入
- [ ] 6.T4 #[test] fn test_flash_read_write_errors — 覆盖场景: 地址越界返回 ReadErr/WriteErr

### 验证
- [x] 6.V1 cargo build 通过
- [x] 6.V2 cargo test flash 通过

---

## Batch 7: Database Lifecycle Management

关联 capability: database-lifecycle
关联 spec: specs/database-lifecycle/spec.md
C 源文件: src/fdb.c (all 157 lines)
Rust 目标文件: src/fdb.rs
依赖 batch: 1, 6

### 实现
- [x] 7.1 实现 fn fdb_init_ex(db: &mut FdbDb, name: &str, path: &str, db_type: FdbDbType) -> Result<(), FdbError> — REQ-database-lifecycle-001/002/003
- [x] 7.2 实现 fn fdb_init_finish(db: &mut FdbDb, result: FdbError) — REQ-database-lifecycle-004
- [x] 7.3 实现 fn fdb_deinit(db: &mut FdbDb) — REQ-database-lifecycle-005
- [x] 7.4 实现 fn fdb_db_path(db: &FdbDb) -> &str
- [x] 7.5 实现 fn fdb_kvdb_init(kvdb: &mut FdbKvdb, name: &str, path: &str) -> Result<(), FdbError>
- [x] 7.6 实现 fn fdb_kvdb_deinit(kvdb: &mut FdbKvdb)
- [x] 7.7 实现 fn fdb_tsdb_init(tsdb: &mut FdbTsdb, name: &str, path: &str, max_len: usize) -> Result<(), FdbError>
- [x] 7.8 实现 fn fdb_tsdb_deinit(tsdb: &mut FdbTsdb)
- [ ] 7.9 添加 one-time 日志消息 (static AtomicBool 替代 C 的 static bool log_is_show)

### 单元测试
- [x] 7.T1 #[test] fn test_kvdb_init_deinit — 覆盖场景: 正常 init/deinit 周期, init_ok flag 正确
- [x] 7.T2 #[test] fn test_tsdb_init_deinit — 覆盖场景: TSDB 正常 init/deinit
- [x] 7.T3 #[test] fn test_db_init_rejects_non_power_of_two_sec_size — 覆盖场景: sec_size=5000 返回 InitFailed (REQ-TEST-006)
- [x] 7.T4 #[test] fn test_db_init_rejects_single_sector — 覆盖场景: 单 sector 返回 InitFailed (REQ-TEST-007)
- [ ] 7.T5 #[test] fn test_init_idempotent — 覆盖场景: init_ok=true 时第二次 init_ex 立即返回 Ok (REQ-TEST-013)
- [ ] 7.T6 #[test] fn test_init_requires_two_sectors — 覆盖场景: max_size/sec_size >= 2 验证

### 验证
- [x] 7.V1 cargo build 通过
- [x] 7.V2 cargo test init 通过

---

## Batch 8: KVDB Sector Management

关联 capability: kvdb-sector-management
关联 spec: specs/kvdb-sector-management/spec.md
C 源文件: src/fdb_kvdb.c (lines 416-508, 769-950, 1069-1182)
Rust 目标文件: src/fdb_kvdb.rs
依赖 batch: 1, 6, 3, 7

### 实现
- [ ] 8.1 定义 SECTOR_HDR_DATA_SIZE 和 sector_hdr_data struct (12 字节 header)
- [ ] 8.2 定义 SECTOR_MAGIC_WORD(0x30424446), KV_MAGIC_WORD(0x32424446) 常量
- [ ] 8.3 实现 fn format_sector(kvdb: &mut FdbKvdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-sector-management-001
- [ ] 8.4 实现 fn read_sector_info(kvdb: &FdbKvdb, sec: &mut KvdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-sector-management-002
- [ ] 8.5 实现 fn update_sec_status(kvdb: &mut FdbKvdb, sec: &mut KvdbSecInfo, new_status: FdbSectorStoreStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-sector-management-003
- [ ] 8.6 实现 fn get_next_sector_addr(kvdb: &FdbKvdb, cur_addr: u32) -> u32
- [ ] 8.7 实现 fn alloc_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError> — REQ-kvdb-sector-management-004
- [ ] 8.8 实现 fn new_kv(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>
- [ ] 8.9 实现 fn new_kv_ex(kvdb: &mut FdbKvdb, kv_len: u32, value_len: u32, flash: &mut dyn FlashStorage) -> Result<u32, FdbError>
- [ ] 8.10 实现 fn sector_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKvdb, u32) -> bool, flash: &dyn FlashStorage)
- [ ] 8.11 实现 fn find_next_kv_addr(kvdb: &FdbKvdb, sec: &KvdbSecInfo, flash: &dyn FlashStorage) -> u32
- [ ] 8.12 实现 fn get_next_kv_addr(kvdb: &FdbKvdb, sec: &KvdbSecInfo, kv: &FdbKv, flash: &dyn FlashStorage) -> u32

### 单元测试
- [ ] 8.T1 #[test] fn test_format_sector_writes_magic — 覆盖场景: format 后 sector 头部包含 0x30424446 magic word
- [ ] 8.T2 #[test] fn test_read_sector_info_valid_magic — 覆盖场景: 有效 magic 的 sector check_ok=true
- [ ] 8.T3 #[test] fn test_read_sector_info_bad_magic — 覆盖场景: 无效 magic 的 sector check_ok=false
- [ ] 8.T4 #[test] fn test_update_sec_status_transitions — 覆盖场景: EMPTY->USING->FULL 状态转换
- [ ] 8.T5 #[test] fn test_alloc_kv_finds_using_sector — 覆盖场景: alloc 在 USING sector 中分配空间，remain 减少
- [ ] 8.T6 #[test] fn test_get_next_sector_addr_wraps — 覆盖场景: sector 地址环绕计算

### 验证
- [ ] 8.V1 cargo build 通过
- [ ] 8.V2 cargo test sector 通过

---

## Batch 9: TSDB Sector Layout and Initialization

关联 capability: tsdb-sector-layout
关联 spec: specs/tsdb-sector-layout/spec.md
C 源文件: src/fdb_tsdb.c (lines 147-389, 950-1095)
Rust 目标文件: src/fdb_tsdb.rs
依赖 batch: 1, 6, 3, 7

### 实现
- [ ] 9.1 定义 TSL_MAGIC_WORD(0x33424446) 常量
- [ ] 9.2 定义 LOG_IDX_DATA_SIZE 常量和 log_idx_data struct
- [ ] 9.3 实现 fn tsdb_read_sector_info(tsdb: &FdbTsdb, sec: &mut TsdbSecInfo, flash: &dyn FlashStorage) -> Result<(), FdbError> — REQ-tsdb-sector-layout-002
- [ ] 9.4 实现 fn tsdb_format_sector(tsdb: &FdbTsdb, addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 9.5 实现 fn tsdb_get_next_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32 — REQ-tsdb-sector-layout-003
- [ ] 9.6 实现 fn tsdb_get_last_sector_addr(tsdb: &FdbTsdb, cur_addr: u32) -> u32
- [ ] 9.7 实现 fn tsdb_sector_iterator(tsdb: &FdbTsdb, cb: fn(u32) -> bool, flash: &dyn FlashStorage)
- [ ] 9.8 实现 fn check_sec_hdr_cb(tsdb: &FdbTsdb, addr: u32, flash: &dyn FlashStorage) -> bool
- [ ] 9.9 实现 fn fdb_tsdb_init 完整版 (sector scan, oldest/current detection, last_time 恢复) — REQ-tsdb-sector-layout-001
- [ ] 9.10 实现 fn fdb_tsdb_deinit 完整版 (file handle cleanup)

### 单元测试
- [ ] 9.T1 #[test] fn test_tsdb_format_sector_writes_magic — 覆盖场景: TSDB sector format 后 0x33424446 magic
- [ ] 9.T2 #[test] fn test_tsdb_read_sector_info_dual_end_info — 覆盖场景: 双 end_info slot, 一个有效一个 0xFF
- [ ] 9.T3 #[test] fn test_tsdb_get_next_sector_addr_wraps — 覆盖场景: 最后 sector 后 wraparound 到 0
- [ ] 9.T4 #[test] fn test_tsdb_init_fresh_db — 覆盖场景: 全新空目录 init 后所有 sector 格式化, cur_sec 指向第一个 sector

### 验证
- [ ] 9.V1 cargo build 通过
- [ ] 9.V2 cargo test tsdb_init 通过

---

## Batch 10: KV CRUD Operations

关联 capability: kv-crud
关联 spec: specs/kv-crud/spec.md
C 源文件: src/fdb_kvdb.c (lines 585-950, 1184-1490)
Rust 目标文件: src/fdb_kvdb.rs
依赖 batch: 1, 6, 3, 2, 4, 7, 8

### 实现
- [ ] 10.1 实现 fn find_kv(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool — 先查 cache 再全扫描
- [ ] 10.2 实现 fn find_kv_no_cache(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool
- [ ] 10.3 实现 fn get_kv(kvdb: &FdbKvdb, kv_addr: u32, blob: &mut FdbBlob, flash: &dyn FlashStorage) -> Result<usize, FdbError>
- [ ] 10.4 实现 fn write_kv_hdr(kvdb: &FdbKvdb, addr: u32, kv: &FdbKv, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kv-crud-005 (CRC32 覆盖 name+value)
- [ ] 10.5 实现 fn create_kv_blob(kvdb: &mut FdbKvdb, kv: &FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 10.6 实现 fn del_kv(kvdb: &mut FdbKvdb, key: &str, old_kv: Option<&FdbKv>, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kv-crud-003 (PRE_DELETE -> DELETED)
- [ ] 10.7 实现 fn set_kv(kvdb: &mut FdbKvdb, key: &str, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kv-crud-001 (2-phase update)
- [ ] 10.8 实现 fn fdb_kv_set(kvdb: &mut FdbKvdb, key: &str, value: &str, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 10.9 实现 fn fdb_kv_get(kvdb: &FdbKvdb, key: &str, flash: &dyn FlashStorage) -> Option<String> — REQ-kv-crud-002
- [ ] 10.10 实现 fn fdb_kv_set_blob(kvdb: &mut FdbKvdb, key: &str, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 10.11 实现 fn fdb_kv_get_blob(kvdb: &FdbKvdb, key: &str, blob: &mut FdbBlob, flash: &dyn FlashStorage) -> usize — REQ-kv-crud-004
- [ ] 10.12 实现 fn fdb_kv_del(kvdb: &mut FdbKvdb, key: &str, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 10.13 实现 fn fdb_kv_get_obj(kvdb: &FdbKvdb, key: &str, flash: &dyn FlashStorage) -> Option<FdbKv>
- [ ] 10.14 实现 fn fdb_kv_to_blob(kv: &FdbKv, blob: &mut FdbBlob) — 设置 blob.saved_len/saved_addr 元数据
- [ ] 10.15 实现 fn fdb_kv_set_default(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 10.16 实现 KV cache: lookup_kv_cache, update_kv_cache, remove_kv_cache

### 单元测试
- [ ] 10.T1 #[test] fn test_set_and_get_kv — 覆盖场景: set 后 get 可查询到正确值
- [ ] 10.T2 #[test] fn test_set_overwrites_existing_kv — 覆盖场景: set 同名 key 覆盖旧值（2-phase delete + create）
- [ ] 10.T3 #[test] fn test_del_kv — 覆盖场景: delete 后 get 返回 None
- [ ] 10.T4 #[test] fn test_kv_name_too_long — 覆盖场景: 超过 64 字节的 key 名返回 KvNameErr
- [ ] 10.T5 #[test] fn test_kv_get_blob_truncation — 覆盖场景: blob buffer 小于存储值时截断不溢出
- [ ] 10.T6 #[test] fn test_crc32_on_read — 覆盖场景: 写入后读取验证 CRC32, 损坏的 CRC 导致读取失败
- [ ] 10.T7 #[test] fn test_set_default_kv — 覆盖场景: set_default 恢复默认 KV 值

### 验证
- [ ] 10.V1 cargo build 通过
- [ ] 10.V2 cargo test kv_crud 通过

---

## Batch 11: KVDB Iteration

关联 capability: kvdb-iteration
关联 spec: specs/kvdb-iteration/spec.md
C 源文件: src/fdb_kvdb.c (lines 576-585, 1468-1660)
Rust 目标文件: src/fdb_kvdb.rs
依赖 batch: 1, 6, 8, 10

### 实现
- [ ] 11.1 实现 fn kv_iterator(kvdb: &FdbKvdb, cb: fn(&FdbKv, &FdbBlob) -> bool, flash: &dyn FlashStorage) — REQ-kvdb-iteration-003
- [ ] 11.2 完善 fn fdb_kv_iterator_init(kvdb: &FdbKvdb) -> FdbKvIterator — REQ-kvdb-iteration-001
- [ ] 11.3 实现 fn fdb_kv_iterate 完整版 (sector traversal, KV read, 统计跟踪) — REQ-kvdb-iteration-002
- [ ] 11.4 实现 fn fdb_kv_print(kvdb: &FdbKvdb) — debug/diagnostic 输出
- [ ] 11.5 完善 fn find_kv_no_cache(kvdb: &FdbKvdb, key: &str, kv: &mut FdbKv, flash: &dyn FlashStorage) -> bool — REQ-kvdb-iteration-004

### 单元测试
- [ ] 11.T1 #[test] fn test_kv_iterator_init — 覆盖场景: iterator 从 oldest_addr 开始, sector_addr 正确
- [ ] 11.T2 #[test] fn test_kv_iterate_empty_db — 覆盖场景: 空数据库首次 iterate 返回 false
- [ ] 11.T3 #[test] fn test_kv_iterate_skips_deleted — 覆盖场景: DELETED/ERR_HDR 状态的 KV 被跳过
- [ ] 11.T4 #[test] fn test_kv_iterate_multi_sector — 覆盖场景: 多 sector 的 KV 按地址顺序遍历

### 验证
- [ ] 11.V1 cargo build 通过
- [ ] 11.V2 cargo test iterate 通过

---

## Batch 12: TSL Append and Storage

关联 capability: tsl-append
关联 spec: specs/tsl-append/spec.md
C 源文件: src/fdb_tsdb.c (lines 147-555)
Rust 目标文件: src/fdb_tsdb.rs
依赖 batch: 1, 6, 3, 4, 7, 9

### 实现
- [ ] 12.1 实现 fn read_tsl(tsdb: &FdbTsdb, addr: u32, tsl: &mut FdbTsl, flash: &dyn FlashStorage) -> Result<(), FdbError>
- [ ] 12.2 实现 fn write_tsl(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-tsl-append-002 (3-phase write)
- [ ] 12.3 实现 fn tsdb_update_sec_status(tsdb: &mut FdbTsdb, sec: &mut TsdbSecInfo, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-tsl-append-003
- [ ] 12.4 实现 fn tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-tsl-append-001
- [ ] 12.5 实现 fn fdb_tsl_append(tsdb: &mut FdbTsdb, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — auto-timestamp
- [ ] 12.6 实现 fn fdb_tsl_append_with_ts(tsdb: &mut FdbTsdb, blob: &FdbBlob, timestamp: FdbTime, flash: &mut dyn FlashStorage) -> Result<(), FdbError>

### 单元测试
- [ ] 12.T1 #[test] fn test_tsl_append_basic — 覆盖场景: 单个 TSL append, timestamp 写入, 查询可见
- [ ] 12.T2 #[test] fn test_tsl_append_monotonic_timestamp — 覆盖场景: timestamp <= last_time 返回 WriteErr
- [ ] 12.T3 #[test] fn test_tsl_append_sector_full_transition — 覆盖场景: sector 满时触发 end_info 写入, 切换到下一个 sector
- [ ] 12.T4 #[test] fn test_tsl_append_rollover — 覆盖场景: rollover=true 时环形覆盖最旧 sector
- [ ] 12.T5 #[test] fn test_tsl_index_data_grow_opposite — 覆盖场景: index 从 sector top 向下, data 从 sector bottom 向上

### 验证
- [ ] 12.V1 cargo build 通过
- [ ] 12.V2 cargo test tsl_append 通过

---

## Batch 13: TSL Iteration and Query

关联 capability: tsl-iteration-query
关联 spec: specs/tsl-iteration-query/spec.md
C 源文件: src/fdb_tsdb.c (lines 192-227, 556-810)
Rust 目标文件: src/fdb_tsdb.rs
依赖 batch: 1, 6, 9

### 实现
- [ ] 13.1 实现 fn get_next_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, flash: &dyn FlashStorage) -> u32
- [ ] 13.2 实现 fn get_last_tsl_addr(tsdb: &FdbTsdb, cur_addr: u32, sec: &TsdbSecInfo, flash: &dyn FlashStorage) -> u32
- [ ] 13.3 实现 fn search_start_tsl_addr(tsdb: &FdbTsdb, sec: &TsdbSecInfo, from: FdbTime, to: FdbTime, flash: &dyn FlashStorage) -> Option<u32> — REQ-tsl-iteration-query-005 (二分搜索)
- [ ] 13.4 实现 fn fdb_tsl_iter(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage) — REQ-tsl-iteration-query-001
- [ ] 13.5 实现 fn fdb_tsl_iter_reverse(tsdb: &FdbTsdb, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage) — REQ-tsl-iteration-query-002
- [ ] 13.6 实现 fn fdb_tsl_iter_by_time(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, cb: FdbTslCb, cb_arg: usize, flash: &dyn FlashStorage) — REQ-tsl-iteration-query-003
- [ ] 13.7 实现 fn fdb_tsl_query_count(tsdb: &FdbTsdb, from: FdbTime, to: FdbTime, status: FdbTslStatus, flash: &dyn FlashStorage) -> usize — REQ-tsl-iteration-query-004

### 单元测试
- [ ] 13.T1 #[test] fn test_tsl_iter_forward — 覆盖场景: 前向遍历所有 TSL 按时间顺序
- [ ] 13.T2 #[test] fn test_tsl_iter_reverse — 覆盖场景: 反向遍历跨 sector 边界 (REQ-TEST-011)
- [ ] 13.T3 #[test] fn test_tsl_iter_by_time_forward — 覆盖场景: from<=to 时间范围查询, 前向顺序
- [ ] 13.T4 #[test] fn test_tsl_iter_by_time_reverse — 覆盖场景: from>to 时间范围查询, 反向顺序
- [ ] 13.T5 #[test] fn test_tsl_query_count_with_status — 覆盖场景: 按 status 和时间范围计数
- [ ] 13.T6 #[test] fn test_binary_search_single_tsl — 覆盖场景: 单 TSL sector 中二分搜索 (REQ-TEST-012)
- [ ] 13.T7 #[test] fn test_tsl_iter_empty_db — 覆盖场景: 空数据库各遍历函数返回/不回调

### 验证
- [ ] 13.V1 cargo build 通过
- [ ] 13.V2 cargo test tsl_iter 通过

---

## Batch 14: KVDB Garbage Collection

关联 capability: kvdb-garbage-collection
关联 spec: specs/kvdb-garbage-collection/spec.md
C 源文件: src/fdb_kvdb.c (lines 1006-1182)
Rust 目标文件: src/fdb_kvdb.rs
依赖 batch: 8, 10, 11

### 实现
- [ ] 14.1 实现 fn move_kv(kvdb: &mut FdbKvdb, from_addr: u32, to_addr: u32, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-garbage-collection-003
- [ ] 14.2 实现 fn gc_check_cb(kvdb: &FdbKvdb, addr: u32, flash: &dyn FlashStorage) -> bool
- [ ] 14.3 实现 fn do_gc(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-garbage-collection-001
- [ ] 14.4 实现 fn gc_collect(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 14.5 实现 fn gc_collect_by_free_size(kvdb: &mut FdbKvdb, size: usize, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-garbage-collection-002
- [ ] 14.6 GC 触发逻辑: alloc_kv 失败时设置 gc_request, set_kv 后触发 do_gc

### 单元测试
- [ ] 14.T1 #[test] fn test_gc_moves_valid_kvs — 覆盖场景: dirty sector 中有效 KV 移动到新 sector, 旧 sector 格式化
- [ ] 14.T2 #[test] fn test_gc_all_kvs_deleted — 覆盖场景: 全部 KV 已删除的 sector 直接格式化不移动
- [ ] 14.T3 #[test] fn test_gc_collect_by_free_size — 覆盖场景: 按目标 free size 收集, 直到满足或 dirty sector 耗尽
- [ ] 14.T4 #[test] fn test_gc_dirty_gc_recovery — 覆盖场景: DIRTY_GC sector 恢复, 继续移动有效 KV (REQ-kvdb-garbage-collection-004)

### 验证
- [ ] 14.V1 cargo build 通过
- [ ] 14.V2 cargo test gc 通过

---

## Batch 15: KVDB Crash Recovery and Integrity

关联 capability: kvdb-recovery
关联 spec: specs/kvdb-recovery/spec.md
C 源文件: src/fdb_kvdb.c (lines 1563-1895)
Rust 目标文件: src/fdb_kvdb.rs
依赖 batch: 8, 10, 14, 11

### 实现
- [ ] 15.1 实现 fn check_sec_hdr_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool — REQ-kvdb-recovery-003
- [ ] 15.2 实现 fn check_and_recovery_kv_cb(kvdb: &mut FdbKvdb, kv: &mut FdbKv, blob: &FdbBlob, flash: &mut dyn FlashStorage) -> bool — REQ-kvdb-recovery-002
- [ ] 15.3 实现 fn check_and_recovery_gc_cb(kvdb: &mut FdbKvdb, sec_addr: u32, flash: &mut dyn FlashStorage) -> bool — REQ-kvdb-recovery-005
- [ ] 15.4 实现 fn fdb_kv_load(kvdb: &mut FdbKvdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — 完整 KVDB 加载(recovery + scan) — REQ-kvdb-recovery-001
- [ ] 15.5 完善 fn fdb_kvdb_init 完整版 (调用 fdb_kv_load, 处理 sector 初始化)
- [ ] 15.6 实现 fn fdb_kvdb_check(kvdb: &FdbKvdb, flash: &dyn FlashStorage) -> Result<(), FdbError> — REQ-kvdb-recovery-004
- [ ] 15.7 实现 fn fdb_kvdb_control(kvdb: &mut FdbKvdb, cmd: u32, arg: usize) — 运行时配置
- [ ] 15.8 实现 kv_auto_update (标记为 deferred feature, 当前 stub 或 compile_error)

### 单元测试
- [ ] 15.T1 #[test] fn test_recovery_pre_write_to_err_hdr — 覆盖场景: PRE_WRITE KV 恢复标记为 ERR_HDR (REQ-TEST-008)
- [ ] 15.T2 #[test] fn test_recovery_pre_delete_move — 覆盖场景: PRE_DELETE KV 移动到新 sector 保留数据 (REQ-TEST-009)
- [ ] 15.T3 #[test] fn test_recovery_resume_gc — 覆盖场景: DIRTY_GC 检测后恢复 GC (REQ-TEST-010)
- [ ] 15.T4 #[test] fn test_recovery_bad_sector_auto_format — 覆盖场景: 坏 magic sector 自动格式化(not_formatable=false)
- [ ] 15.T5 #[test] fn test_kvdb_check_valid_db — 覆盖场景: 有效数据库 check 返回 Ok
- [ ] 15.T6 #[test] fn test_init_idempotent — 覆盖场景: 已 init 数据库二次 init 不重跑 recovery (REQ-TEST-013)

### 验证
- [ ] 15.V1 cargo build 通过
- [ ] 15.V2 cargo test recovery 通过

---

## Batch 16: TSL Status Management and Cleanup

关联 capability: tsl-status-cleanup
关联 spec: specs/tsl-status-cleanup/spec.md
C 源文件: src/fdb_tsdb.c (lines 816-1092)
Rust 目标文件: src/fdb_tsdb.rs
依赖 batch: 12, 9

### 实现
- [ ] 16.1 实现 fn fdb_tsl_set_status(tsdb: &mut FdbTsdb, tsl: &mut FdbTsl, status: FdbTslStatus, flash: &mut dyn FlashStorage) -> Result<(), FdbError> — REQ-tsl-status-cleanup-001
- [ ] 16.2 实现 fn tsl_format_all(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage) -> Result<(), FdbError>
- [ ] 16.3 实现 fn fdb_tsl_clean(tsdb: &mut FdbTsdb, flash: &mut dyn FlashStorage) — REQ-tsl-status-cleanup-002
- [ ] 16.4 完善 fn fdb_tsl_to_blob(tsl: &FdbTsl, blob: &mut FdbBlob) — 设置 blob.saved_addr = tsl.addr_log — REQ-tsl-status-cleanup-003
- [ ] 16.5 实现 fn fdb_tsdb_control(tsdb: &mut FdbTsdb, cmd: u32, arg: usize) — REQ-tsl-status-cleanup-004

### 单元测试
- [ ] 16.T1 #[test] fn test_tsl_set_status_to_user — 覆盖场景: WRITE -> USER_STATUS1 状态转换
- [ ] 16.T2 #[test] fn test_tsl_set_status_to_deleted — 覆盖场景: WRITE -> DELETED 状态转换
- [ ] 16.T3 #[test] fn test_tsl_clean_irreversible — 覆盖场景: clean 后所有 sector 为 EMPTY, last_time=0, 数据不可恢复
- [ ] 16.T4 #[test] fn test_tsl_to_blob_sets_metadata — 覆盖场景: blob 的 saved_addr/saved_len 指向 TSL 的 addr_log/log_len
- [ ] 16.T5 #[test] fn test_tsdb_control_set_rollover — 覆盖场景: control cmd 设置 rollover flag

### 验证
- [ ] 16.V1 cargo build 通过
- [ ] 16.V2 cargo test tsl_status 通过

---

## Batch 17: Test Migration and Integration

关联 capability: test-migration
关联 spec: specs/test-migration/spec.md
C 源文件: tests/fdb_kvdb_tc.c, tests/fdb_tsdb_tc.c
Rust 目标文件: tests/kvdb_tests.rs, tests/tsdb_tests.rs
依赖 batch: 1-16

### KVDB Test Migration
- [ ] 17.1 实现 #[test] fn test_kvdb_init — REQ-TEST-MAP: test_fdb_kvdb_init
- [ ] 17.2 实现 #[test] fn test_kvdb_init_by_8_sectors — REQ-TEST-MAP: test_fdb_kvdb_init_by_8_sectors
- [ ] 17.3 实现 #[test] fn test_kvdb_init_by_sector_num — REQ-TEST-MAP: test_fdb_kvdb_init_by_sector_num
- [ ] 17.4 实现 #[test] fn test_kvdb_init_check — REQ-TEST-MAP: test_fdb_kvdb_init_check
- [ ] 17.5 实现 #[test] fn test_kvdb_deinit — REQ-TEST-MAP: test_fdb_kvdb_deinit
- [ ] 17.6 实现 #[test] fn test_kvdb_create_kv_blob — REQ-TEST-MAP: test_fdb_create_kv_blob
- [ ] 17.7 实现 #[test] fn test_kvdb_change_kv_blob — REQ-TEST-MAP: test_fdb_change_kv_blob
- [ ] 17.8 实现 #[test] fn test_kvdb_del_kv_blob — REQ-TEST-MAP: test_fdb_del_kv_blob
- [ ] 17.9 实现 #[test] fn test_kvdb_create_kv — REQ-TEST-MAP: test_fdb_create_kv
- [ ] 17.10 实现 #[test] fn test_kvdb_change_kv — REQ-TEST-MAP: test_fdb_change_kv
- [ ] 17.11 实现 #[test] fn test_kvdb_del_kv — REQ-TEST-MAP: test_fdb_del_kv
- [ ] 17.12 实现 #[test] fn test_kvdb_gc — REQ-TEST-MAP: test_fdb_gc
- [ ] 17.13 实现 #[test] fn test_kvdb_gc2 — REQ-TEST-MAP: test_fdb_gc2
- [ ] 17.14 实现 #[test] fn test_kvdb_set_default — REQ-TEST-MAP: test_fdb_kvdb_set_default
- [ ] 17.15 实现 #[test] fn test_kvdb_scale_up — REQ-TEST-MAP: test_fdb_scale_up
- [ ] 17.16 实现 test helper: save_fdb_by_kvs / check_fdb_by_kvs / test_fdb_by_kvs
- [ ] 17.17 实现 setup_kvdb() / teardown_kvdb() helper

### TSDB Test Migration
- [ ] 17.18 实现 #[test] fn test_tsdb_init_ex — REQ-TEST-MAP: test_fdb_tsdb_init_ex
- [ ] 17.19 实现 #[test] fn test_tsdb_deinit — REQ-TEST-MAP: test_fdb_tsdb_deinit
- [ ] 17.20 实现 #[test] fn test_tsl_append — REQ-TEST-MAP: test_fdb_tsl_append
- [ ] 17.21 实现 #[test] fn test_tsl_iter — REQ-TEST-MAP: test_fdb_tsl_iter
- [ ] 17.22 实现 #[test] fn test_tsl_iter_by_time — REQ-TEST-MAP: test_fdb_tsl_iter_by_time
- [ ] 17.23 实现 #[test] fn test_tsl_iter_by_time_1 — REQ-TEST-MAP: test_fdb_tsl_iter_by_time_1
- [ ] 17.24 实现 #[test] fn test_tsl_query_count — REQ-TEST-MAP: test_fdb_tsl_query_count
- [ ] 17.25 实现 #[test] fn test_tsl_set_status — REQ-TEST-MAP: test_fdb_tsl_set_status
- [ ] 17.26 实现 #[test] fn test_tsl_clean — REQ-TEST-MAP: test_fdb_tsl_clean
- [ ] 17.27 实现 #[test] fn test_tsl_sector_bound — REQ-TEST-MAP: test_fdb_tsl_sector_bound_test
- [ ] 17.28 实现 #[test] fn test_tsl_github_issue_249 — REQ-TEST-MAP: test_fdb_github_issue_249
- [ ] 17.29 实现 test helper: test_tsdb_data_by_time
- [ ] 17.30 实现 setup_tsdb() / teardown_tsdb() helper

### 验证
- [ ] 17.V1 cargo build 通过
- [ ] 17.V2 cargo test kvdb 通过 (所有 KVDB 测试)
- [ ] 17.V3 cargo test tsdb 通过 (所有 TSDB 测试)
- [ ] 17.V4 cargo test 全部通过 (24 个 C 测试对应 + 新增单元测试)
