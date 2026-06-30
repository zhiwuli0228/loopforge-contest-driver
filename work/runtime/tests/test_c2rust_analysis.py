import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from c2rust_analysis import PROTOTYPE_RE, _iter_definitions, _parseable_c, _split_signature


class CAnalysisParsingTests(unittest.TestCase):
    def test_comments_and_macros_are_not_functions(self):
        source = """/* Copyright (c) 2020 */
#define TRACE(...) log(__VA_ARGS__)
int real_api(int value) { return value; }
"""
        definitions = _iter_definitions(_parseable_c(source))
        self.assertEqual([item[1] for item in definitions], ["real_api"])

    def test_header_prototype_and_c_definition_share_name(self):
        header = "fdb_err_t fdb_kvdb_init(fdb_kvdb_t db, const char *name);"
        source = """fdb_err_t fdb_kvdb_init(fdb_kvdb_t db,
            const char *name)
        { return FDB_NO_ERR; }
        """
        prototypes = []
        for prefix, params in PROTOTYPE_RE.findall(_parseable_c(header)):
            signature = _split_signature(prefix)
            if signature:
                prototypes.append(signature[1])
        definitions = [item[1] for item in _iter_definitions(_parseable_c(source))]
        self.assertEqual(prototypes, ["fdb_kvdb_init"])
        self.assertEqual(definitions, ["fdb_kvdb_init"])

    def test_url_inside_string_is_not_treated_as_comment(self):
        source = '''void finish(void) {
            log("https://example.invalid/path");
        }
        void next_api(void) { return; }
        '''
        definitions = [item[1] for item in _iter_definitions(_parseable_c(source))]
        self.assertEqual(definitions, ["finish", "next_api"])


if __name__ == "__main__":
    unittest.main()
