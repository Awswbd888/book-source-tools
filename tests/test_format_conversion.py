"""
test_format_conversion.py — Legado <-> 香色闺阁 conversion tests.
"""
import json
import os
import sys

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from _common import (
    css_to_xpath, xpath_to_css,
    needs_conversion_warning,
)


# ── Selector conversion tests ──────────────────────────────────────────────

class TestXPathToCSS:
    """XPath -> CSS-like selector conversion."""

    def test_meta_og(self):
        xpath = "//meta[@property='og:novel:book_name']/@content"
        expected = "meta[property=og:novel:book_name]@content"
        assert xpath_to_css(xpath) == expected

    def test_meta_og_author(self):
        xpath = "//meta[@property='og:novel:author']/@content"
        expected = "meta[property=og:novel:author]@content"
        assert xpath_to_css(xpath) == expected

    def test_class_child(self):
        xpath = "//ol[@class='BCsectionTwo-top']/li"
        expected = "ol[class=BCsectionTwo-top] li"
        assert xpath_to_css(xpath) == expected

    def test_relative_text(self):
        assert xpath_to_css(".//a/text()") == "a@text"

    def test_relative_href(self):
        assert xpath_to_css(".//a/@href") == "a@href"

    def test_tag_text(self):
        assert xpath_to_css("//h1/text()") == "h1@text"

    def test_tag_attr(self):
        assert xpath_to_css("//img/@src") == "img@src"

    def test_simple_tag(self):
        assert xpath_to_css("//div") == "div"

    def test_id_selector(self):
        assert xpath_to_css("//*[@id='content']") == "#content"
        assert xpath_to_css("//div[@id='main']") == "div#main"

    def test_class_selector(self):
        assert xpath_to_css("//*[contains(@class,'book')]") == ".book"
        assert xpath_to_css("//div[contains(@class,'list')]") == "div.list"

    def test_complex_xpath_unchanged(self):
        """Complex XPath that can't be converted should return as-is."""
        xpath = "//div[@id='C0NTENT']/div/p/text()"
        result = xpath_to_css(xpath)
        assert result == xpath  # unchanged

    def test_position_xpath_unchanged(self):
        xpath = "//li[position()=1]"
        assert xpath_to_css(xpath) == xpath

    def test_empty(self):
        assert xpath_to_css("") == ""


class TestCSSToXPath:
    """CSS-like -> XPath selector conversion."""

    def test_meta_og(self):
        css = "meta[property=og:novel:book_name]@content"
        expected = "//meta[@property=\"og:novel:book_name\"]/@content"
        assert css_to_xpath(css) == expected

    def test_class_child(self):
        css = "ol[class=BCsectionTwo-top] li"
        expected = "//ol[@class=\"BCsectionTwo-top\"]/li"
        assert css_to_xpath(css) == expected

    def test_tag_text(self):
        assert css_to_xpath("h1@text") == "//h1/text()"

    def test_tag_attr(self):
        assert css_to_xpath("a@href") == "//a/@href"
        assert css_to_xpath("img@src") == "//img/@src"

    def test_tag_only(self):
        assert css_to_xpath("div") == "//div"

    def test_id(self):
        assert css_to_xpath("#content") == "//*[@id=\"content\"]"
        assert css_to_xpath("div#main") == "//div[@id=\"main\"]"

    def test_class(self):
        assert css_to_xpath(".book") == "//*[contains(@class,\"book\")]"
        assert css_to_xpath("div.list") == "//div[contains(@class,\"list\")]"

    def test_tag_html(self):
        assert css_to_xpath("#content@html") == "//*[@id=\"content\"]"

    def test_empty(self):
        assert css_to_xpath("") == ""


class TestSelectorRoundTrip:
    """XPath -> CSS -> XPath should be consistent."""

    def test_meta_og_round_trip(self):
        xpath = "//meta[@property='og:novel:book_name']/@content"
        css = xpath_to_css(xpath)
        back = css_to_xpath(css)
        # Check semantic equivalence (quotes may be ' or ", both valid XPath)
        assert back.replace('"', "'") == xpath

    def test_class_child_round_trip(self):
        xpath = "//ol[@class='BCsectionTwo-top']/li"
        css = xpath_to_css(xpath)
        back = css_to_xpath(css)
        assert back.replace('"', "'") == xpath

    def test_relative_text_round_trip(self):
        xpath = ".//a/text()"
        css = xpath_to_css(xpath)
        back = css_to_xpath(css)
        # Note: .// and // are semantically equivalent for absolute paths
        assert back == "//a/text()" or back == xpath


class TestConversionWarning:
    """Warning detection for complex selectors."""

    def test_position_warning(self):
        w = needs_conversion_warning("//li[position()=1]", "css")
        assert w is not None

    def test_starts_with_warning(self):
        w = needs_conversion_warning("//a[starts-with(@href, '/book/')]", "css")
        assert w is not None

    def test_simple_ok(self):
        w = needs_conversion_warning("//meta/@content", "css")
        assert w is None

    def test_contains_warning_xiangse(self):
        w = needs_conversion_warning("//div[@class='a']//img", "css")
        # This could be flagged if has "contains" in it
        assert w is None  # Simple attribute match, no contains()


# ── Full conversion tests (using booksource_tool) ──────────────────────────

class TestFullConversion:
    """End-to-end format conversion tests using the CLI module."""

    def test_xiangse_to_legado_structure(self, xiangse_json):
        """Converting 香色闺阁 to Legado produces valid Legado structure."""
        import booksource_tool as bt
        data = json.loads(xiangse_json)
        # Grab first source
        name = next(iter(data))
        legado = bt._convert_xiangse_to_legado(data, name=name)
        assert "bookSourceName" in legado
        assert "bookSourceUrl" in legado
        assert "ruleBookInfo" in legado
        assert "ruleToc" in legado
        assert "ruleContent" in legado

    def test_xiangse_to_legado_fields_preserved(self, xiangse_json):
        """Key fields should survive conversion."""
        import booksource_tool as bt
        data = json.loads(xiangse_json)
        name = next(iter(data))
        orig = data[name]
        legado = bt._convert_xiangse_to_legado(data, name=name)
        assert legado["bookSourceName"] == orig["sourceName"]
        assert legado["bookSourceUrl"] == orig["sourceUrl"]

    def test_legado_to_xiangse_structure(self, legado_json):
        """Converting Legado to 香色闺阁 produces valid structure."""
        import booksource_tool as bt
        xiangse = bt._convert_legado_to_xiangse(legado_json)
        name = next(iter(xiangse))
        entry = xiangse[name]
        assert entry["sourceName"] == legado_json["bookSourceName"]
        assert entry["sourceUrl"] == legado_json["bookSourceUrl"]
        assert "bookDetail" in entry
        assert "chapterList" in entry
        assert "chapterContent" in entry

    def test_legado_headers_parsed(self, legado_json):
        """Legado's JSON string headers should be properly expanded."""
        import booksource_tool as bt
        xiangse = bt._convert_legado_to_xiangse(legado_json)
        name = next(iter(xiangse))
        entry = xiangse[name]
        assert "httpHeaders" in entry
        assert len(entry["httpHeaders"]) > 0

    def test_xiangse_to_legado_round_trip(self, xiangse_json):
        """Convert 香色闺阁 -> Legado -> 香色闺阁, key fields preserved."""
        import booksource_tool as bt
        data = json.loads(xiangse_json)
        name = next(iter(data))
        orig = data[name]

        legado = bt._convert_xiangse_to_legado(data, name=name)
        back = bt._convert_legado_to_xiangse(legado)
        back_entry = back[next(iter(back))]

        assert back_entry["sourceName"] == orig["sourceName"]
        assert back_entry["sourceUrl"] == orig["sourceUrl"]
