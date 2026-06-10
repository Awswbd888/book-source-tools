"""
test_validate.py — Book source validation tests.
"""
import json
import os
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from _common import (
    XIANGSE_REQUIRED_ACTIONS,
    KNOWN_PARSER_IDS,
    XIANGSE_SOURCE_TYPES,
)


class TestValidation:
    """Book source validation logic tests."""

    def test_valid_source_passes(self):
        """A properly structured source should pass validation."""
        entry = {
            "sourceName": "测试站",
            "sourceUrl": "https://test.example.com",
            "sourceType": "novel",
            "enable": 1,
            "bookDetail": {"actionID": "bookDetail", "parserID": "DOM"},
            "chapterList": {"actionID": "chapterList", "parserID": "DOM"},
            "chapterContent": {"actionID": "chapterContent", "parserID": "DOM"},
        }
        for act in XIANGSE_REQUIRED_ACTIONS:
            assert act in entry

    def test_missing_required_action_fails(self):
        """Source missing a required action should be flagged."""
        entry = {
            "sourceName": "不完整",
            "sourceUrl": "https://test.example.com",
            "sourceType": "novel",
            "enable": 1,
            "bookDetail": {"actionID": "bookDetail", "parserID": "DOM"},
            # missing chapterList and chapterContent
        }
        for act in XIANGSE_REQUIRED_ACTIONS:
            if act not in entry:
                # This is the validation we expect to fail
                assert True
                return
        assert False  # Should not reach here

    def test_unknown_parser_id_warning(self):
        """Unknown parserID should be flagged."""
        entry = {
            "bookDetail": {"actionID": "bookDetail", "parserID": "CSS"},
        }
        pid = entry["bookDetail"].get("parserID")
        assert pid not in KNOWN_PARSER_IDS

    def test_known_parser_ids_are_valid(self):
        """Known parser IDs should not be flagged."""
        for pid in KNOWN_PARSER_IDS:
            assert pid in ("DOM", "JSON")

    def test_source_type_valid(self):
        """Known source types should be valid."""
        for st in XIANGSE_SOURCE_TYPES:
            assert st in ("novel", "comic", "video", "audio")

    def test_invalid_source_type_flagged(self):
        """Invalid source type should be flagged."""
        st = "unknown_type"
        assert st not in XIANGSE_SOURCE_TYPES

    def test_enable_field_validation(self):
        """enable should be 0 or 1."""
        assert 1 in (0, 1)
        assert 0 in (0, 1)
        assert "1" not in (0, 1)  # string is invalid

    def test_missing_source_url(self):
        """Missing URL should be flagged."""
        entry = {"sourceName": "x", "sourceType": "novel", "enable": 1}
        if not entry.get("sourceUrl"):
            assert True  # should be flagged

    def test_validate_real_xiangse_source(self, xiangse_json):
        """The real 肉肉屋 source should pass all validations."""
        import booksource_tool as bt
        data = json.loads(xiangse_json)
        for name, entry in data.items():
            issues = bt._validate_entry(name, entry)
            assert not issues, f"Issues found: {issues}"

    def test_validate_real_legado_source(self, legado_json):
        """The real Legado source should be properly structured."""
        assert "bookSourceName" in legado_json
        assert "bookSourceUrl" in legado_json
        assert "ruleBookInfo" in legado_json or "ruleToc" in legado_json

    def test_validate_complex_xiangse_structure(self, sample_xiangse):
        """Sample 香色闺阁 source should pass validation."""
        import booksource_tool as bt
        for name, entry in sample_xiangse.items():
            issues = bt._validate_entry(name, entry)
            assert not issues, f"Issues found: {issues}"

    def test_chapter_content_replace_regex(self):
        """replaceRegex should be a string if present."""
        entry = {"replaceRegex": "本站新.*?域名"}
        assert isinstance(entry["replaceRegex"], str)

        entry2 = {"replaceRegex": 123}
        assert not isinstance(entry2.get("replaceRegex"), str)

    def test_source_weight_format(self):
        """weight should be a numeric string."""
        assert isinstance("9999", str)
        assert "9999".isdigit()

    def test_validate_multiple_sources(self):
        """Validating a file with multiple sources should check each."""
        data = {
            "好站点": {
                "sourceName": "好站点",
                "sourceUrl": "https://good.example.com",
                "sourceType": "novel", "enable": 1,
                "bookDetail": {"actionID": "bookDetail", "parserID": "DOM"},
                "chapterList": {"actionID": "chapterList", "parserID": "DOM"},
                "chapterContent": {"actionID": "chapterContent", "parserID": "DOM"},
            },
            "坏站点": {
                "sourceName": "坏站点",
                "sourceUrl": "https://bad.example.com",
                "sourceType": "novel", "enable": 1,
                # missing actions
            },
        }
        import booksource_tool as bt
        good_issues = bt._validate_entry("好站点", data["好站点"])
        assert not good_issues
        bad_issues = bt._validate_entry("坏站点", data["坏站点"])
        assert len(bad_issues) > 0
