"""
_common.py — Shared constants and primitives for book-source-tools.

Single source of truth for:
- XXTEA key, encrypt, and decrypt
- XBS container format (pack/unpack)
- Field mapping tables for Legado <-> 香色闺阁 conversion
- Selector conversion helpers (XPath <-> CSS-like)
- Validation constants

Stdlib-only. Python 3.10+.
"""
import struct
import json

# ── XXTEA ───────────────────────────────────────────────────────────────────

XXTEA_KEY = bytes([
    0xe5, 0x87, 0xbc, 0xe8, 0xa4, 0x86, 0xe6, 0xbb,
    0xbf, 0xe9, 0x87, 0x91, 0xe6, 0xba, 0xa1, 0xe5,
])
"""Fixed XXTEA key used by 香色闺阁 (UTF-8: "覆盖满金源漫")."""

_DELTA = 0x9E3779B9


def xxtea_encrypt(data: bytes, key: bytes = XXTEA_KEY) -> bytes:
    """XXTEA encryption. Returns encrypted bytes."""
    if not data:
        return b''

    data_len = len(data)
    pad_len = (4 - data_len % 4) % 4
    if pad_len:
        data = data + b'\x00' * pad_len

    v = list(struct.unpack('<' + 'I' * (len(data) // 4), data))
    k = list(struct.unpack('<' + 'I' * (len(key) // 4), key[:16]))

    n = len(v) - 1
    if n < 1:
        return data

    z = v[n]
    y = v[0]
    q = 6 + 52 // (n + 1)
    p = 0

    while q > 0:
        q -= 1
        p = (p + _DELTA) & 0xFFFFFFFF
        e = (p >> 2) & 3
        for i in range(n + 1):
            y = v[(i + 1) % (n + 1)]
            mx = ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((p ^ y) + (k[(i & 3) ^ e] ^ z)))
            v[i] = (v[i] + mx) & 0xFFFFFFFF
            z = v[i]

    return struct.pack('<' + 'I' * (n + 1), *v)


def xxtea_decrypt(data: bytes, key: bytes = XXTEA_KEY) -> bytes:
    """XXTEA decryption. Inverse of xxtea_encrypt."""
    if not data:
        return b''
    if len(data) % 4 != 0:
        raise ValueError("Ciphertext length must be a multiple of 4")
    if len(data) < 8:
        # Too short for XXTEA to operate (need at least 2 uint32 words)
        return data

    v = list(struct.unpack('<' + 'I' * (len(data) // 4), data))
    k = list(struct.unpack('<' + 'I' * (len(key) // 4), key[:16]))

    n = len(v) - 1
    if n < 1:
        # Not enough data for meaningful XXTEA rounds; return as-is
        return data

    q = 6 + 52 // (n + 1)
    s = (q * _DELTA) & 0xFFFFFFFF
    y = v[0]

    while s != 0:
        e = (s >> 2) & 3
        for i in range(n, -1, -1):
            z = v[i - 1] if i > 0 else v[n]
            mx = ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((s ^ y) + (k[(i & 3) ^ e] ^ z)))
            v[i] = (v[i] - mx) & 0xFFFFFFFF
            y = v[i]
        s = (s - _DELTA) & 0xFFFFFFFF

    return struct.pack('<' + 'I' * (n + 1), *v)


# ── XBS container format ────────────────────────────────────────────────────

def json_to_xbs(json_bytes: bytes, key: bytes = XXTEA_KEY) -> bytes:
    """Encode JSON bytes into XBS format: pad → append length → encrypt."""
    buffer_len = len(json_bytes)
    pad_len = (4 - buffer_len % 4) % 4
    if pad_len:
        json_bytes = json_bytes + b'\x00' * pad_len
    json_bytes += struct.pack('<I', buffer_len)
    return xxtea_encrypt(json_bytes, key)


def xbs_to_json(xbs_bytes: bytes, key: bytes = XXTEA_KEY) -> bytes:
    """Decode XBS bytes back to original JSON bytes: decrypt → read length → truncate."""
    decrypted = xxtea_decrypt(xbs_bytes, key)
    if len(decrypted) < 4:
        raise ValueError("Decrypted data too short (no length suffix)")
    original_len = struct.unpack('<I', decrypted[-4:])[0]
    if original_len > len(decrypted) - 4:
        raise ValueError(
            f"Original length {original_len} exceeds decrypted payload "
            f"({len(decrypted) - 4} bytes). File may be corrupted."
        )
    return decrypted[:original_len]


# ── Validation / schema constants ───────────────────────────────────────────

XIANGSE_REQUIRED_ACTIONS = frozenset({"bookDetail", "chapterList", "chapterContent"})
"""Actions that every valid 香色闺阁 novel source must define."""

XIANGSE_OPTIONAL_ACTIONS = frozenset({
    "searchShudan", "relatedWord", "shupingList",
    "shupingHome", "shudanDetail", "bookWorld",
})
KNOWN_PARSER_IDS = frozenset({"DOM", "JSON"})
KNOWN_RESPONSE_FORMATS = frozenset({"html", "json", "text"})

XIANGSE_SOURCE_TYPES = {
    "novel": 0, "comic": 1, "video": 2, "audio": 3,
}


# ── Field mapping: Legado <-> 香色闺阁 ──────────────────────────────────────

# How Legado rule fields map to 香色闺阁 bookDetail fields
LEGADO_BOOKINFO_TO_XIANGSE = {
    "name": "bookName",
    "author": "author",
    "kind": "cat",
    "intro": "desc",
    "coverUrl": "cover",
    "lastChapter": "lastChapterTitle",
    "status": "status",
    "wordCount": "wordCount",
}
XIANGSE_TO_LEGADO_BOOKINFO = {v: k for k, v in LEGADO_BOOKINFO_TO_XIANGSE.items()}

# Chapter list field mapping
LEGADO_TOC_TO_XIANGSE = {
    "chapterList": "list",
    "chapterName": "title",
    "chapterUrl": "url",
}
XIANGSE_TO_LEGADO_TOC = {v: k for k, v in LEGADO_TOC_TO_XIANGSE.items()}

# Content field mapping
LEGADO_CONTENT_TO_XIANGSE = {
    "content": "content",
    "replaceRegex": "replaceRegex",
}

# Explore/browse field mapping
LEGADO_EXPLORE_TO_XIANGSE = {
    "bookList": "list",
    "name": "bookName",
    "bookUrl": "detailUrl",
    "coverUrl": "cover",
    "author": "author",
    "kind": "cat",
    "intro": "desc",
    "lastChapter": "lastChapter",
}

# Top-level field name mapping (Legado -> 香色闺阁)
LEGADO_TOP_TO_XIANGSE = {
    "bookSourceName": "sourceName",
    "bookSourceUrl": "sourceUrl",
    "bookSourceGroup": "sourceGroup",
    "bookSourceType": "sourceType",
    "enabled": "enable",
    "customOrder": "weight",
    "header": "_header_json",
    "exploreUrl": "_exploreUrl",
}
XIANGSE_TO_LEGADO_TOP = {v: k for k, v in LEGADO_TOP_TO_XIANGSE.items()}


# ── Selector conversion helpers ──────────────────────────────────────────────

import re

# Common CSS-like selector patterns and their XPath equivalents
_CSS_TO_XPATH_RULES = [
    # tag#id -> //tag[@id='id']
    (re.compile(r'^(\w+)#([\w-]+)$'),       r'//\1[@id="\2"]'),
    (re.compile(r'^#([\w-]+)$'),             r'//*[@id="\1"]'),
    # tag.class -> //tag[contains(@class,'class')]
    (re.compile(r'^(\w+)\.([\w-]+)$'),       r'//\1[contains(@class,"\2")]'),
    (re.compile(r'^\.([\w-]+)$'),            r'//*[contains(@class,"\1")]'),
    # tag[attr=val]@target -> //tag[@attr='val']/@target  (Legado style)
    (re.compile(r"^(\w+)\[(\w+)=([\"']?)([^\"'\]]+?)\3\]@(\w+)$"), r'//\1[@\2="\4"]/@\5'),
    # tag[attr=val] -> //tag[@attr='val']
    (re.compile(r"^(\w+)\[(\w+)=([\"']?)([^\"'\]]+?)\3\]$"),      r'//\1[@\2="\4"]'),
    # Specific @pseudo-attribute patterns (MUST be before generic @attr)
    # tag@text -> //tag/text()
    (re.compile(r'^(\w+)@text$'),            r'//\1/text()'),
    (re.compile(r'^@text$'),                 r'//*/text()'),
    # tag@html -> //tag (Legado inner HTML)
    (re.compile(r'^(\w+)@html$'),            r'//\1'),
    (re.compile(r'^@html$'),                 r'//*'),
    # #id@html -> //*[@id='id']  (element with id, inner HTML)
    (re.compile(r'^#([\w-]+)@html$'),        r'//*[@id="\1"]'),
    # tag@attr -> //tag/@attr  (generic, after specific patterns like @text, @html)
    (re.compile(r'^(\w+)@(\w+)$'),           r'//\1/@\2'),
    (re.compile(r'^@(\w+)$'),                r'//*/@\1'),
    # pure tag -> //tag
    (re.compile(r'^(\w+)$'),                 r'//\1'),
]


def css_to_xpath(selector: str) -> str:
    """Convert a simple CSS-like selector to XPath (best effort).

    Handles the subset of selectors used by Legado book sources.
    Falls back to the original selector with a warning for complex cases.
    """
    selector = selector.strip()
    if not selector:
        return selector

    # Handle || (fallback chain) recursively
    if '||' in selector:
        return '||'.join(css_to_xpath(s.strip()) for s in selector.split('||'))

    # Handle comma-separated alternatives
    if ',' in selector:
        return ' | '.join(css_to_xpath(s.strip()) for s in selector.split(','))

    # Handle child combinator
    if '>' in selector:
        parts = selector.split('>')
        return '/'.join(css_to_xpath(p.strip()).lstrip('/') for p in parts)

    # Handle descendant combinator (space) — keep // on first part, use / separator
    if ' ' in selector and not selector.startswith('.'):
        parts = selector.split()
        converted = [css_to_xpath(p.strip()) for p in parts]
        result = converted[0]
        for c in converted[1:]:
            result += '/' + c.lstrip('/')
        return result

    for pattern, replacement in _CSS_TO_XPATH_RULES:
        m = pattern.match(selector)
        if m:
            return m.expand(replacement)

    return selector  # fallback, no conversion


_XPATH_TO_CSS_RULES = [
    # .//tag/text() -> tag@text
    (re.compile(r'^\.//(\w+)/text\(\)$'),   r'\1@text'),
    # .//tag/@attr -> tag@attr
    (re.compile(r'^\.//(\w+)/@(\w+)$'),     r'\1@\2'),
    # //tag/text() -> tag@text
    (re.compile(r'^//(\w+)/text\(\)$'),     r'\1@text'),
    # //tag/@attr -> tag@attr
    (re.compile(r'^//(\w+)/@(\w+)$'),       r'\1@\2'),
    # //*/text() -> @text
    (re.compile(r'^//\*/text\(\)$'),        r'@text'),
    # //*[@id='id'] -> #id
    (re.compile(r'^//\*\[@id=([\'"])([\w-]+)\1\]$'), r'#\2'),
    # //tag[@id='id'] -> tag#id
    (re.compile(r"^//(\w+)\[@id=([\"'])([\w-]+)\2\]$"), r'\1#\3'),
    # //tag[contains(@class,'class')] -> tag.class
    (re.compile(r"^//(\w+)\[contains\(@class,\s*([\"'])([\w-]+)\2\)\]$"), r'\1.\3'),
    # //*[contains(@class,'class')] -> .class
    (re.compile(r"^//\*\[contains\(@class,\s*([\"'])([\w-]+)\1\)\]$"),   r'.\2'),
    # //tag[@attr='val.with.colons']/child -> tag[attr=val.with.colons] child
    (re.compile(r"^//(\w+)\[@(\w+)=([\"'])([^\"']+?)\3\]/(\w+)$"), r'\1[\2=\4] \5'),
    # //tag[@attr='val']//child -> tag[attr=val] child
    (re.compile(r"^//(\w+)\[@(\w+)=([\"'])([^\"']+?)\3\]//(\w+)$"), r'\1[\2=\4] \5'),
    # //tag[@attr='val']/@target -> tag[attr=val]@target
    (re.compile(r"^//(\w+)\[@(\w+)=([\"'])([^\"']+?)\3\]/@(\w+)$"), r'\1[\2=\4]@\5'),
    # //tag[@attr='val.with.colons'] -> tag[attr=val.with.colons]
    (re.compile(r"^//(\w+)\[@(\w+)=([\"'])([^\"']+?)\3\]$"),     r'\1[\2=\4]'),
    # //tag/child - two-level XPath with no predicate
    (re.compile(r'^//(\w+)/(\w+)$'),         r'\1 \2'),
    # .//tag -> tag  (after more specific .// patterns)
    (re.compile(r'^\.//(\w+)$'),             r'\1'),
    # //tag -> tag
    (re.compile(r'^//(\w+)$'),               r'\1'),
    # //tag1//tag2 -> tag1 tag2
    (re.compile(r'^//(\w+)//(\w+)$'),        r'\1 \2'),
]


def xpath_to_css(xpath: str) -> str:
    """Convert a simple XPath selector to CSS-like (best effort).

    Handles the common subset used by 香色闺阁 book sources.
    Complex expressions (position(), starts-with, multiple predicates)
    are returned as-is with a warning embedded.
    """
    xpath = xpath.strip()
    if not xpath:
        return xpath

    # Handle || fallback chain
    if '||' in xpath:
        return '||'.join(xpath_to_css(s.strip()) for s in xpath.split('||'))

    for pattern, replacement in _XPATH_TO_CSS_RULES:
        m = pattern.match(xpath)
        if m:
            return m.expand(replacement)

    # If we couldn't convert (complex XPath), return as-is
    # The caller should detect this and warn
    return xpath


def needs_conversion_warning(selector: str, target_format: str) -> str | None:
    """Return a warning string if the selector may not convert cleanly, else None."""
    if target_format == "css" and any(kw in selector for kw in ["position()", "starts-with", "contains", "and ", "or ", "not("]):
        return f"Complex XPath may not have CSS equivalent: {selector}"
    if target_format == "xpath" and '||' in selector:
        return f"CSS fallback chain converted to XPath '||': {selector} (verify manually)"
    return None
