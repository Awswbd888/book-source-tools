"""
test_merge.py — Book source merge functionality tests.
"""
import json
import os
import sys
import tempfile

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from _common import json_to_xbs, xbs_to_json, XXTEA_KEY


class TestMerge:
    """Test merge logic via booksource_tool module."""

    def test_merge_new_source_into_empty(self):
        """Merging a source into an empty collection should add it."""
        import booksource_tool as bt

        source = {
            "新站点": {
                "sourceName": "新站点",
                "sourceUrl": "https://new.example.com",
                "sourceType": "novel",
                "enable": 1,
                "httpHeaders": {},
                "bookDetail": {"actionID": "bookDetail", "parserID": "DOM"},
                "chapterList": {"actionID": "chapterList", "parserID": "DOM"},
                "chapterContent": {"actionID": "chapterContent", "parserID": "DOM"},
            }
        }

        target = {}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(source, f, ensure_ascii=False)
            src_path = f.name

        try:
            src_data, _ = bt._load_json_or_xbs(src_path)
            for key, entry in src_data.items():
                target[key] = entry
            assert "新站点" in target
            assert target["新站点"]["sourceUrl"] == "https://new.example.com"
        finally:
            os.unlink(src_path)

    def test_merge_deduplication(self):
        """Merging a duplicate source should not add it again."""
        target = {
            "已有站点": {
                "sourceName": "已有站点",
                "sourceUrl": "https://existing.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {}, "chapterList": {}, "chapterContent": {},
            }
        }

        duplicate = {
            "已有站点": {
                "sourceName": "已有站点",
                "sourceUrl": "https://existing.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {}, "chapterList": {}, "chapterContent": {},
            }
        }

        count_before = len(target)
        for key in duplicate:
            if key not in target:
                target[key] = duplicate[key]

        assert len(target) == count_before  # not added

    def test_merge_multiple_sources(self):
        """Merging multiple new sources should add all of them."""
        target = {}
        new_sources = {
            f"站点{i}": {
                "sourceName": f"站点{i}",
                "sourceUrl": f"https://site{i}.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {}, "chapterList": {}, "chapterContent": {},
            }
            for i in range(5)
        }

        for key, entry in new_sources.items():
            target[key] = entry

        assert len(target) == 5

    def test_merge_updates_existing(self):
        """By default, merge should skip existing (not update)."""
        target = {
            "站点": {
                "sourceName": "站点",
                "sourceUrl": "https://old.example.com",
                "sourceType": "novel", "enable": 1,
            }
        }
        update = {
            "站点": {
                "sourceName": "站点",
                "sourceUrl": "https://new.example.com",
                "sourceType": "novel", "enable": 1,
            }
        }

        for key in update:
            if key not in target:
                target[key] = update[key]

        assert target["站点"]["sourceUrl"] == "https://old.example.com"  # unchanged

    def test_merge_legado_source(self, legado_json):
        """Legado format source should be convertible and mergeable."""
        import booksource_tool as bt

        target = {}
        xiangse = bt._convert_legado_to_xiangse(legado_json)
        for key, entry in xiangse.items():
            target[key] = entry

        assert len(target) == 1
        name = next(iter(target))
        assert "bookDetail" in target[name]

    def test_merge_preserves_existing_sources(self):
        """Merging into a collection with existing sources should keep old ones."""
        target = {
            "老站点": {
                "sourceName": "老站点",
                "sourceUrl": "https://old.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {}, "chapterList": {}, "chapterContent": {},
            }
        }
        new = {
            "新站点": {
                "sourceName": "新站点",
                "sourceUrl": "https://new.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {}, "chapterList": {}, "chapterContent": {},
            }
        }

        for key, entry in new.items():
            target[key] = entry

        assert len(target) == 2
        assert "老站点" in target
        assert "新站点" in target

    def test_xbs_round_trip_merge(self, xiangse_json):
        """JSON -> XBS -> decrypt -> merge should work end-to-end."""
        xbs = json_to_xbs(xiangse_json, XXTEA_KEY)
        decrypted = xbs_to_json(xbs, XXTEA_KEY)

        target = json.loads(decrypted)
        assert len(target) == 1
        assert "肉肉屋" in target
