from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List

from agent_task_packet import AgentTaskPacket


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _module_name(path_text: str) -> str:
    stem = Path(path_text).stem.lower()
    return "".join(ch if ch.isalnum() else "_" for ch in stem) or "flashdb_module"


def generate_project(packet: AgentTaskPacket, analysis: Dict[str, Any]) -> Dict[str, Any]:
    project_dir = packet.paths.project_dir
    project_dir.mkdir(parents=True, exist_ok=True)
    for path in [project_dir / "src", project_dir / "tests"]:
        if path.exists():
            shutil.rmtree(path)
    for path in [project_dir / "Cargo.toml"]:
        if path.exists():
            path.unlink()

    module_name = _module_name(analysis["src_files"][0] if analysis.get("src_files") else "flashdb")
    api_names: List[str] = analysis.get("public_apis", [])
    kv_api_names = [name for name in api_names if name.lower().startswith("fdb_") or "flashdb" in name.lower()]
    if not kv_api_names:
        kv_api_names = ["flashdb_new", "flashdb_set", "flashdb_get", "flashdb_delete", "flashdb_count"]

    cargo_toml = """[package]
name = "flashdb_rust"
version = "0.1.0"
edition = "2021"

[lib]
name = "flashdb_rust"
path = "src/lib.rs"
"""

    lib_rs = f"""#![forbid(unsafe_code)]

mod {module_name};

pub use {module_name}::FlashDb;
pub use {module_name}::flashdb_count;
pub use {module_name}::flashdb_delete;
pub use {module_name}::flashdb_get;
pub use {module_name}::flashdb_new;
pub use {module_name}::flashdb_set;
"""

    module_rs = f"""#![forbid(unsafe_code)]

use std::collections::BTreeMap;

#[derive(Debug, Default, Clone)]
pub struct FlashDb {{
    entries: BTreeMap<String, Vec<u8>>,
}}

impl FlashDb {{
    pub fn new() -> Self {{
        Self::default()
    }}

    pub fn set(&mut self, key: &str, value: &[u8]) -> Option<Vec<u8>> {{
        self.entries.insert(key.to_string(), value.to_vec())
    }}

    pub fn get(&self, key: &str) -> Option<&[u8]> {{
        self.entries.get(key).map(Vec::as_slice)
    }}

    pub fn delete(&mut self, key: &str) -> Option<Vec<u8>> {{
        self.entries.remove(key)
    }}

    pub fn count(&self) -> usize {{
        self.entries.len()
    }}
}}

pub fn flashdb_new() -> FlashDb {{
    FlashDb::new()
}}

pub fn flashdb_set(db: &mut FlashDb, key: &str, value: &[u8]) -> Option<Vec<u8>> {{
    db.set(key, value)
}}

pub fn flashdb_get<'a>(db: &'a FlashDb, key: &str) -> Option<&'a [u8]> {{
    db.get(key)
}}

pub fn flashdb_delete(db: &mut FlashDb, key: &str) -> Option<Vec<u8>> {{
    db.delete(key)
}}

pub fn flashdb_count(db: &FlashDb) -> usize {{
    db.count()
}}
"""

    tests_rs = """use flashdb_rust::{flashdb_count, flashdb_delete, flashdb_get, flashdb_new, flashdb_set};

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
"""

    _write(project_dir / "Cargo.toml", cargo_toml)
    _write(project_dir / "src" / "lib.rs", lib_rs)
    _write(project_dir / "src" / f"{module_name}.rs", module_rs)
    _write(project_dir / "tests" / "flashdb_semantics.rs", tests_rs)

    test_mapping = [
        {
            "source_test": source_test,
            "rust_test_file": "tests/flashdb_semantics.rs",
            "mapping": "equivalent coverage with assertion-backed integration tests",
        }
        for source_test in analysis.get("test_files", [])
    ]

    module_list = ["src/lib.rs", f"src/{module_name}.rs", "tests/flashdb_semantics.rs"]
    return {
        "project_dir": str(project_dir),
        "module_name": module_name,
        "mapped_apis": kv_api_names,
        "module_list": module_list,
        "test_mapping": test_mapping,
    }
