"""
conftest.py — Pytest fixtures for book-source-tools tests.

Fixtures reference existing files at D:\AI\ and provide sample data.
"""
import json
import os
import pytest

# ── Path fixtures ───────────────────────────────────────────────────────────

FIXTURES_DIR = r"D:\AI"
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def xiangse_json_path():
    return os.path.join(FIXTURES_DIR, "021best_xiangse.json")


@pytest.fixture(scope="session")
def legado_json_path():
    return os.path.join(FIXTURES_DIR, "021best_booksource.json")


@pytest.fixture(scope="session")
def xbs_path():
    return os.path.join(FIXTURES_DIR, "021best_rourouwu.xbs")


@pytest.fixture(scope="session")
def xiangse_json(xiangse_json_path):
    with open(xiangse_json_path, 'rb') as f:
        return f.read()


@pytest.fixture(scope="session")
def legado_json(legado_json_path):
    with open(legado_json_path, 'rb') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def xbs_bytes(xbs_path):
    with open(xbs_path, 'rb') as f:
        return f.read()


# ── Sample data fixtures ───────────────────────────────────────────────────

SAMPLE_XIANGSE_SOURCE = {
    "测试书源": {
        "sourceName": "测试书源",
        "sourceUrl": "https://test.example.com",
        "sourceType": "novel",
        "enable": 1,
        "httpHeaders": {"User-Agent": "TestAgent"},
        "desc": "测试用",
        "weight": "1",
        "miniAppVersion": "2.0",
        "lastModifyTime": "1749600000",
        "bookDetail": {
            "actionID": "bookDetail",
            "parserID": "DOM",
            "host": "https://test.example.com",
            "httpHeaders": {"User-Agent": "TestAgent"},
            "responseFormatType": "html",
            "requestInfo": "%@result",
            "bookName": "//h1/text()",
            "author": "//span[@class='author']/text()",
        },
        "chapterList": {
            "actionID": "chapterList",
            "parserID": "DOM",
            "host": "https://test.example.com",
            "httpHeaders": {"User-Agent": "TestAgent"},
            "responseFormatType": "html",
            "requestInfo": "%@result",
            "list": "//ul[@class='chapters']/li",
            "title": ".//a/text()",
            "url": ".//a/@href",
        },
        "chapterContent": {
            "actionID": "chapterContent",
            "parserID": "DOM",
            "host": "https://test.example.com",
            "httpHeaders": {"User-Agent": "TestAgent"},
            "responseFormatType": "html",
            "requestInfo": "%@result",
            "content": "//div[@id='content']/text()",
            "replaceRegex": "",
        },
    }
}


SAMPLE_LEGADO_SOURCE = {
    "bookSourceName": "测试Legado",
    "bookSourceUrl": "https://legado.example.com",
    "bookSourceGroup": "测试",
    "bookSourceType": 0,
    "enabled": True,
    "enabledExplore": True,
    "enabledCookieJar": True,
    "customOrder": 0,
    "header": '{"User-Agent": "TestAgent"}',
    "ruleBookInfo": {
        "name": "meta[property=og:novel:book_name]@content",
        "author": "meta[property=og:novel:author]@content",
    },
    "ruleToc": {
        "chapterList": "ul.chapters li",
        "chapterName": "a@text",
        "chapterUrl": "a@href",
    },
    "ruleContent": {
        "content": "#content@text",
    },
}


@pytest.fixture
def sample_xiangse():
    return dict(SAMPLE_XIANGSE_SOURCE)


@pytest.fixture
def sample_legado():
    return dict(SAMPLE_LEGADO_SOURCE)
