#!/usr/bin/env python3
"""
booksource_tool.py — CLI for creating and converting 香色闺阁 book sources.

Subcommands:
  encrypt     JSON -> XBS (XXTEA encryption)
  decrypt     XBS -> JSON (XXTEA decryption)
  convert     Convert between 香色闺阁 and Legado formats
  merge       Add/merge sources into an existing collection
  validate    Validate a source file's structure
  inspect     Print metadata about an XBS/JSON source file
  template    Generate a template JSON file

Stdlib-only. Python 3.10+.
"""
import argparse
import json
import os
import sys
import time

# Fix Windows console encoding for Chinese output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        pass

from _common import (
    XXTEA_KEY,
    json_to_xbs,
    xbs_to_json,
    XIANGSE_REQUIRED_ACTIONS,
    XIANGSE_OPTIONAL_ACTIONS,
    KNOWN_PARSER_IDS,
    KNOWN_RESPONSE_FORMATS,
    XIANGSE_SOURCE_TYPES,
    css_to_xpath,
    xpath_to_css,
    needs_conversion_warning,
)


# ── I/O helpers ─────────────────────────────────────────────────────────────

def _read_bytes(path: str) -> bytes:
    with open(path, 'rb') as f:
        return f.read()


def _write_bytes(path: str, data: bytes):
    with open(path, 'wb') as f:
        f.write(data)


def _read_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_json(path: str, data, pretty: bool = True):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2 if pretty else None)


def _load_json_or_xbs(path: str) -> tuple[dict, str]:
    """Load a JSON or XBS file, return (parsed_dict, format_name)."""
    raw = _read_bytes(path)
    # Try JSON first
    try:
        return json.loads(raw.decode('utf-8')), 'json'
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass
    # Try XBS decryption
    try:
        decrypted = xbs_to_json(raw, XXTEA_KEY)
        return json.loads(decrypted.decode('utf-8')), 'xbs'
    except Exception as e:
        raise ValueError(f"Unable to parse {path}: not valid JSON or XBS ({e})")


def _is_xiangse_format(data: dict) -> bool:
    """Heuristic: 香色闺阁 format has sourceName-keyed top-level entries."""
    if not data:
        return False
    key = next(iter(data))
    entry = data[key]
    return isinstance(entry, dict) and 'sourceName' in entry and 'sourceUrl' in entry


def _is_legado_format(data: dict) -> bool:
    """Heuristic: Legado format has bookSourceName top-level field."""
    return 'bookSourceName' in data and 'bookSourceUrl' in data


# ── Subcommand: encrypt ────────────────────────────────────────────────────

def cmd_encrypt(args):
    json_bytes = _read_bytes(args.input)
    # Validate JSON
    try:
        json.loads(json_bytes.decode('utf-8'))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON — {e}", file=sys.stderr)
        sys.exit(1)

    xbs_bytes = json_to_xbs(json_bytes, args.key)
    if args.output:
        _write_bytes(args.output, xbs_bytes)
        print(f"Encrypted {args.input} -> {args.output}")
        print(f"  JSON: {len(json_bytes)} bytes -> XBS: {len(xbs_bytes)} bytes")
    else:
        sys.stdout.buffer.write(xbs_bytes)


# ── Subcommand: decrypt ────────────────────────────────────────────────────

def cmd_decrypt(args):
    xbs_bytes = _read_bytes(args.input)
    try:
        json_bytes = xbs_to_json(xbs_bytes, args.key)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate result is valid JSON
    try:
        parsed = json.loads(json_bytes.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Warning: Decrypted data is not valid UTF-8 JSON ({e})", file=sys.stderr)
        parsed = None

    if args.output:
        if parsed is not None and args.pretty:
            _write_json(args.output, parsed)
        else:
            _write_bytes(args.output, json_bytes)
        print(f"Decrypted {args.input} -> {args.output}")
        print(f"  XBS: {len(xbs_bytes)} bytes -> JSON: {len(json_bytes)} bytes")
    else:
        if parsed is not None and args.pretty:
            json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
            print()
        else:
            sys.stdout.buffer.write(json_bytes)


# ── Subcommand: validate ───────────────────────────────────────────────────

def _validate_entry(name: str, entry: dict) -> list[str]:
    """Validate a single 香色闺阁 source entry. Returns list of issues."""
    issues = []

    # Check sourceName matches key
    if entry.get('sourceName') != name:
        issues.append(f"Key mismatch: '{name}' != sourceName '{entry.get('sourceName')}'")

    # Check required actions
    for action in XIANGSE_REQUIRED_ACTIONS:
        if action not in entry:
            issues.append(f"Missing required action: '{action}'")
        elif not isinstance(entry[action], dict):
            issues.append(f"Action '{action}' is not a dict")
        else:
            act = entry[action]
            if act.get('parserID') not in KNOWN_PARSER_IDS:
                issues.append(f"Action '{action}': unknown parserID '{act.get('parserID')}'")
            if act.get('responseFormatType') and act['responseFormatType'] not in KNOWN_RESPONSE_FORMATS:
                issues.append(f"Action '{action}': unknown responseFormatType '{act['responseFormatType']}'")

    # Check sourceType
    st = entry.get('sourceType', 'novel')
    if st not in XIANGSE_SOURCE_TYPES:
        issues.append(f"Unknown sourceType '{st}'")

    # Check enable field
    enable = entry.get('enable')
    if enable not in (0, 1):
        issues.append(f"enable should be 0 or 1, got '{enable}'")

    # Check URL
    if not entry.get('sourceUrl'):
        issues.append("Missing sourceUrl")

    return issues


def cmd_validate(args):
    try:
        data, fmt = _load_json_or_xbs(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    all_issues = []
    if _is_xiangse_format(data):
        for name, entry in data.items():
            if not isinstance(entry, dict) or 'sourceName' not in entry:
                continue
            issues = _validate_entry(name, entry)
            if issues:
                all_issues.append((name, issues))
                for iss in issues:
                    print(f"  [{name}] {iss}")
    else:
        print("Not a recognized 香色闺阁 format (no sourceName-keyed entries found).")

    if not all_issues:
        print(f"[OK] {args.input}: No issues found ({len(data)} source(s))")
    else:
        print(f"[ERR] {args.input}: {len(all_issues)} source(s) with issues")
        sys.exit(1)


# ── Subcommand: inspect ────────────────────────────────────────────────────

def cmd_inspect(args):
    try:
        data, fmt = _load_json_or_xbs(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if _is_xiangse_format(data):
        sources = []
        for name, entry in data.items():
            if not isinstance(entry, dict) or 'sourceName' not in entry:
                continue
            sources.append(entry)

        print(f"File: {args.input}  ({fmt})")
        print(f"Total sources: {len(sources)}")
        print()

        # Count by type
        type_counts = {}
        for s in sources:
            t = s.get('sourceType', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        if type_counts:
            print("By type:")
            for t, c in sorted(type_counts.items()):
                print(f"  {t}: {c}")
            print()

        # Check for missing required actions
        missing = 0
        for s in sources:
            for act in XIANGSE_REQUIRED_ACTIONS:
                if act not in s:
                    missing += 1
                    break
        print(f"Sources missing required actions: {missing}")

        # List sources (first 20)
        print()
        print("Sources:")
        for i, s in enumerate(sources):
            if i >= 20 and not args.all:
                remaining = len(sources) - 20
                print(f"  ... and {remaining} more (use --all to show all)")
                break
            name = s.get('sourceName', '?')
            st = s.get('sourceType', '?')
            url = s.get('sourceUrl', '?')[:50]
            enabled = '[+]' if s.get('enable') == 1 else '[-]'
            print(f"  {enabled} [{st:6s}] {name:30s} {url}")

    elif _is_legado_format(data):
        print(f"File: {args.input}  (Legado format)")
        print(f"Name: {data.get('bookSourceName', '?')}")
        print(f"URL:  {data.get('bookSourceUrl', '?')}")
        print(f"Type: {data.get('bookSourceType', '?')}")
        print(f"Enabled: {data.get('enabled', '?')}")
    else:
        print("Unknown format — printing top-level keys:")
        print(list(data.keys())[:20])


# ── Subcommand: template ───────────────────────────────────────────────────

def _make_timestamp() -> str:
    return str(int(time.time()))


def cmd_template(args):
    ts = _make_timestamp()
    url = args.url.rstrip('/')

    if args.format == 'xiangse':
        template = {
            args.name: {
                "sourceName": args.name,
                "sourceUrl": url,
                "sourceType": "novel",
                "enable": 1,
                "httpHeaders": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": url + "/"
                },
                "desc": f"{args.name} - 免费小说",
                "weight": "9999",
                "miniAppVersion": "2.0",
                "lastModifyTime": ts,
                "loginUrl": "",
                "shudanList": {},
                "searchShudan": {"actionID": "searchShudan", "parserID": "DOM"},
                "relatedWord": {"actionID": "relatedWord", "parserID": "DOM"},
                "shupingList": {"actionID": "shupingList", "parserID": "DOM"},
                "shupingHome": {"actionID": "shupingHome", "parserID": "DOM"},
                "shudanDetail": {"actionID": "shudanDetail", "parserID": "DOM"},
                "bookDetail": {
                    "actionID": "bookDetail",
                    "parserID": "DOM",
                    "host": url,
                    "httpHeaders": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": url + "/"
                    },
                    "responseFormatType": "html",
                    "requestInfo": "%@result",
                    "validConfig": "",
                    "bookName": "//meta[@property='og:novel:book_name']/@content",
                    "author": "//meta[@property='og:novel:author']/@content",
                    "cover": "//meta[@property='og:image']/@content",
                    "cat": "//meta[@property='og:novel:category']/@content",
                    "desc": "//meta[@property='og:description']/@content",
                    "status": "//meta[@property='og:novel:status']/@content",
                    "lastChapterTitle": "//meta[@property='og:novel:latest_chapter_name']/@content",
                    "wordCount": ""
                },
                "chapterList": {
                    "actionID": "chapterList",
                    "parserID": "DOM",
                    "host": url,
                    "httpHeaders": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": url + "/"
                    },
                    "responseFormatType": "html",
                    "requestInfo": "%@result",
                    "validConfig": "",
                    "list": "",
                    "title": "",
                    "url": ""
                },
                "chapterContent": {
                    "actionID": "chapterContent",
                    "parserID": "DOM",
                    "host": url,
                    "httpHeaders": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": url + "/"
                    },
                    "responseFormatType": "html",
                    "requestInfo": "%@result",
                    "validConfig": "",
                    "content": "",
                    "replaceRegex": ""
                },
                "bookWorld": {
                    "browse": {
                        "actionID": "browse",
                        "parserID": "DOM",
                        "host": url,
                        "httpHeaders": {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": url + "/"
                        },
                        "responseFormatType": "html",
                        "requestInfo": "",
                        "validConfig": "",
                        "list": "",
                        "bookName": "",
                        "detailUrl": "",
                        "cover": ""
                    }
                }
            }
        }
    else:  # legado
        template = {
            "bookSourceName": args.name,
            "bookSourceUrl": url,
            "bookSourceGroup": "精选",
            "bookSourceType": 0,
            "bookUrlPattern": "",
            "enabled": True,
            "enabledExplore": True,
            "enabledCookieJar": True,
            "customOrder": 0,
            "header": json.dumps({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": url + "/"
            }, ensure_ascii=False),
            "exploreUrl": "",
            "ruleExplore": {
                "bookList": "",
                "name": "",
                "bookUrl": "",
                "coverUrl": "",
                "author": "",
                "kind": "",
                "intro": "",
                "lastChapter": ""
            },
            "ruleBookInfo": {
                "name": "",
                "author": "",
                "kind": "",
                "intro": "",
                "coverUrl": "",
                "lastChapter": "",
                "status": ""
            },
            "ruleToc": {
                "chapterList": "",
                "chapterName": "",
                "chapterUrl": ""
            },
            "ruleContent": {
                "content": "",
                "replaceRegex": ""
            }
        }

    if args.output:
        _write_json(args.output, template)
        print(f"Template written to {args.output}")
    else:
        json.dump(template, sys.stdout, ensure_ascii=False, indent=2)
        print()


# ── Subcommand: convert (Legado <-> 香色闺阁) ─────────────────────────────

def _convert_xiangse_to_legado(data: dict, name: str | None = None, key: str = '') -> dict:
    """Convert a single 香色闺阁 entry to Legado format."""
    entry = data if name is None else data[name]

    header_dict = entry.get('httpHeaders', {})
    # Also check bookDetail headers which may have more specific ones
    bd_headers = entry.get('bookDetail', {}).get('httpHeaders', {})
    merged_headers = {**header_dict, **bd_headers}

    legado = {
        "bookSourceName": entry.get('sourceName', name or key),
        "bookSourceUrl": entry.get('sourceUrl', ''),
        "bookSourceGroup": entry.get('sourceGroup', ''),
        "bookSourceType": 0,
        "enabled": entry.get('enable') == 1,
        "enabledExplore": True,
        "enabledCookieJar": True,
        "customOrder": int(entry.get('weight', 0)) if str(entry.get('weight', '0')).isdigit() else 0,
        "header": json.dumps(merged_headers, ensure_ascii=False) if merged_headers else "",
    }

    # RuleBookInfo
    bd = entry.get('bookDetail', {})
    if bd:
        legado["ruleBookInfo"] = {
            "name": xpath_to_css(bd.get('bookName', '')),
            "author": xpath_to_css(bd.get('author', '')),
            "kind": xpath_to_css(bd.get('cat', '')),
            "intro": xpath_to_css(bd.get('desc', '')),
            "coverUrl": xpath_to_css(bd.get('cover', '')),
            "lastChapter": xpath_to_css(bd.get('lastChapterTitle', '')),
            "status": xpath_to_css(bd.get('status', '')),
            "wordCount": xpath_to_css(bd.get('wordCount', '')),
        }
        # Remove empty fields
        legado["ruleBookInfo"] = {k: v for k, v in legado["ruleBookInfo"].items() if v}

    # RuleToc
    cl = entry.get('chapterList', {})
    if cl:
        legado["ruleToc"] = {
            "chapterList": xpath_to_css(cl.get('list', '')),
            "chapterName": xpath_to_css(cl.get('title', '')),
            "chapterUrl": xpath_to_css(cl.get('url', '')),
        }
        legado["ruleToc"] = {k: v for k, v in legado["ruleToc"].items() if v}

    # RuleContent
    cc = entry.get('chapterContent', {})
    if cc:
        legado["ruleContent"] = {
            "content": xpath_to_css(cc.get('content', '')),
            "replaceRegex": cc.get('replaceRegex', ''),
        }
        legado["ruleContent"] = {k: v for k, v in legado["ruleContent"].items() if v}

    # ExploreUrl from bookWorld.browse
    bw = entry.get('bookWorld', {})
    browse = bw.get('browse', {})
    if browse and browse.get('requestInfo'):
        ri = browse['requestInfo']
        # Try to extract URL pattern from @js: code
        if ri.startswith('@js:'):
            legado["exploreUrl"] = _js_to_explore_url(ri, entry.get('sourceUrl', ''))
        else:
            legado["exploreUrl"] = ri
    else:
        legado["exploreUrl"] = ""

    return legado


def _js_to_explore_url(js_code: str, base_url: str) -> str:
    """Convert @js: requestInfo to Legado exploreUrl template (best effort)."""
    code = js_code.replace('@js:', '').strip()
    # Common pattern: return config.host + '/category/0/' + params.pageIndex + '.html';
    # -> /category/0/{{page}}.html
    code = code.replace('return ', '').rstrip(';').strip()

    # Replace config.host with base_url or relative
    if 'config.host' in code:
        code = code.replace('config.host', '').replace('+ +', '+').strip("+ ")

    # Replace params.pageIndex with {{page}}
    code = code.replace('params.pageIndex', '{{page}}')

    # Strip string concatenation artifacts
    code = code.replace("'", '').replace('"', '').replace('+', '').strip()

    # If result is just a URL path, combine with base_url
    if code.startswith('/'):
        return code
    elif code.startswith('http'):
        return code
    else:
        return code


def _explore_url_to_js(explore_url: str, base_url: str) -> str:
    """Convert Legado exploreUrl to @js: requestInfo format."""
    if not explore_url:
        return ""
    if '{{page}}' in explore_url:
        url_template = explore_url.replace('{{page}}', "' + params.pageIndex + '")
        return f"@js:\nreturn '{url_template}';"
    return explore_url


def _convert_legado_to_xiangse(data: dict) -> dict:
    """Convert a single Legado source entry to 香色闺阁 format."""
    name = data.get('bookSourceName', 'Unknown')
    url = data.get('bookSourceUrl', '')

    # Parse headers
    try:
        headers = json.loads(data.get('header', '{}'))
    except (json.JSONDecodeError, TypeError):
        headers = {}

    if not headers:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": url + "/"
        }

    xiangse = {
        name: {
            "sourceName": name,
            "sourceUrl": url,
            "sourceType": "novel",
            "enable": 1 if data.get('enabled', True) else 0,
            "httpHeaders": dict(headers),
            "desc": f"{name} - 免费小说",
            "weight": str(data.get('customOrder', 0)),
            "miniAppVersion": "2.0",
            "lastModifyTime": str(int(time.time())),
            "loginUrl": "",
            "shudanList": {},
            "searchShudan": {"actionID": "searchShudan", "parserID": "DOM"},
            "relatedWord": {"actionID": "relatedWord", "parserID": "DOM"},
            "shupingList": {"actionID": "shupingList", "parserID": "DOM"},
            "shupingHome": {"actionID": "shupingHome", "parserID": "DOM"},
            "shudanDetail": {"actionID": "shudanDetail", "parserID": "DOM"},
        }
    }

    entry = xiangse[name]

    # RuleBookInfo -> bookDetail
    rbi = data.get('ruleBookInfo', {})
    if rbi:
        entry["bookDetail"] = {
            "actionID": "bookDetail",
            "parserID": "DOM",
            "host": url,
            "httpHeaders": dict(headers),
            "responseFormatType": "html",
            "requestInfo": "%@result",
            "validConfig": "",
            "bookName": css_to_xpath(rbi.get('name', '')),
            "author": css_to_xpath(rbi.get('author', '')),
            "cover": css_to_xpath(rbi.get('coverUrl', '')),
            "cat": css_to_xpath(rbi.get('kind', '')),
            "desc": css_to_xpath(rbi.get('intro', '')),
            "status": css_to_xpath(rbi.get('status', '')),
            "lastChapterTitle": css_to_xpath(rbi.get('lastChapter', '')),
            "wordCount": css_to_xpath(rbi.get('wordCount', '')),
        }
    else:
        entry["bookDetail"] = {
            "actionID": "bookDetail", "parserID": "DOM",
            "host": url, "httpHeaders": dict(headers),
            "responseFormatType": "html", "requestInfo": "%@result",
            "bookName": "", "author": "", "cover": "",
            "cat": "", "desc": "", "status": "", "lastChapterTitle": "",
        }

    # RuleToc -> chapterList
    rt = data.get('ruleToc', {})
    if rt:
        entry["chapterList"] = {
            "actionID": "chapterList", "parserID": "DOM",
            "host": url, "httpHeaders": dict(headers),
            "responseFormatType": "html", "requestInfo": "%@result",
            "validConfig": "",
            "list": css_to_xpath(rt.get('chapterList', '')),
            "title": css_to_xpath(rt.get('chapterName', '')),
            "url": css_to_xpath(rt.get('chapterUrl', '')),
        }
    else:
        entry["chapterList"] = {
            "actionID": "chapterList", "parserID": "DOM",
            "host": url, "httpHeaders": dict(headers),
            "responseFormatType": "html", "requestInfo": "%@result",
            "list": "", "title": "", "url": "",
        }

    # RuleContent -> chapterContent
    rc = data.get('ruleContent', {})
    if rc:
        entry["chapterContent"] = {
            "actionID": "chapterContent", "parserID": "DOM",
            "host": url, "httpHeaders": dict(headers),
            "responseFormatType": "html", "requestInfo": "%@result",
            "validConfig": "",
            "content": css_to_xpath(rc.get('content', '')),
            "replaceRegex": rc.get('replaceRegex', ''),
        }
    else:
        entry["chapterContent"] = {
            "actionID": "chapterContent", "parserID": "DOM",
            "host": url, "httpHeaders": dict(headers),
            "responseFormatType": "html", "requestInfo": "%@result",
            "content": "", "replaceRegex": "",
        }

    # ExploreUrl -> bookWorld.browse
    eu = data.get('exploreUrl', '')
    if eu:
        entry["bookWorld"] = {
            "browse": {
                "actionID": "browse", "parserID": "DOM",
                "host": url, "httpHeaders": dict(headers),
                "responseFormatType": "html",
                "requestInfo": _explore_url_to_js(eu, url),
                "validConfig": "",
                "list": "", "bookName": "", "detailUrl": "", "cover": "",
            }
        }

    return xiangse


def cmd_convert(args):
    data, fmt = _load_json_or_xbs(args.input)

    if args.from_fmt == 'auto':
        if _is_legado_format(data):
            src_fmt = 'legado'
        elif _is_xiangse_format(data):
            src_fmt = 'xiangse'
        else:
            print("Error: Cannot auto-detect format. Use --from legado|xiangse", file=sys.stderr)
            sys.exit(1)
    else:
        src_fmt = args.from_fmt

    if src_fmt == args.to_fmt:
        print("Source and target formats are the same — copying as-is.")
        if args.output:
            _write_json(args.output, data)
        else:
            json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
            print()
        return

    if src_fmt == 'xiangse' and args.to_fmt == 'legado':
        result = {}
        results = []
        for name, entry in data.items():
            if not isinstance(entry, dict) or 'sourceName' not in entry:
                continue
            legado = _convert_xiangse_to_legado(data, name=name, key=name)
            results.append(legado)
        if len(results) == 1:
            result = results[0]
        else:
            result = results
        out_fmt = 'legado'

    elif src_fmt == 'legado' and args.to_fmt == 'xiangse':
        result = _convert_legado_to_xiangse(data)
        out_fmt = 'xiangse'
    else:
        print(f"Error: Unsupported conversion {src_fmt} -> {args.to_fmt}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        _write_json(args.output, result)
        print(f"Converted {args.input} -> {args.output}  ({src_fmt} -> {out_fmt})")
    else:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()


# ── Subcommand: merge ──────────────────────────────────────────────────────

def cmd_merge(args):
    # Load target collection
    if args.into and os.path.exists(args.into):
        target_data, target_fmt = _load_json_or_xbs(args.into)
        if not _is_xiangse_format(target_data):
            print(f"Error: Target {args.into} is not 香色闺阁 format", file=sys.stderr)
            sys.exit(1)
    else:
        target_data = {}
        target_fmt = 'json'
        print(f"Creating new collection -> {args.into or 'stdout'}")

    # Load and merge sources
    added = 0
    skipped = 0
    updated = 0
    warnings = []

    for src_path in args.sources:
        try:
            src_data, src_fmt_s = _load_json_or_xbs(src_path)
        except ValueError as e:
            warnings.append(f"{src_path}: {e}")
            continue

        if _is_legado_format(src_data):
            # Convert legado to xiangse format
            src_data = _convert_legado_to_xiangse(src_data)
        elif _is_xiangse_format(src_data):
            pass  # already in xiangse format
        else:
            warnings.append(f"{src_path}: Unrecognized format, skipping")
            continue

        for key, entry in src_data.items():
            if not isinstance(entry, dict) or 'sourceName' not in entry:
                continue
            if key in target_data:
                skipped += 1
            else:
                target_data[key] = entry
                added += 1

    # Output
    if args.output:
        out_path = args.output
    elif args.into and args.in_place:
        out_path = args.into
    else:
        out_path = args.into if args.into else None

    if out_path:
        if out_path.endswith('.xbs') or target_fmt == 'xbs':
            json_bytes = json.dumps(target_data, ensure_ascii=False).encode('utf-8')
            xbs_bytes = json_to_xbs(json_bytes, args.key)
            _write_bytes(out_path, xbs_bytes)
        else:
            _write_json(out_path, target_data)
        print(f"Merged -> {out_path}")
    else:
        json.dump(target_data, sys.stdout, ensure_ascii=False, indent=2)
        print()

    print(f"Added: {added}, Skipped (duplicate): {skipped}, Updated: {updated}")
    for w in warnings:
        print(f"Warning: {w}", file=sys.stderr)


# ── Main CLI ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Book source tools for 香色闺阁 / Legado",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--key', help="XXTEA key bytes (default: 覆盖满金源漫)",
                        type=lambda s: s.encode('utf-8') if len(s) == 16 else bytes(eval(s)))

    sub = parser.add_subparsers(dest='command', required=True)

    # encrypt
    p = sub.add_parser('encrypt', help='JSON -> XBS (XXTEA encryption)')
    p.add_argument('input', help='Input JSON file')
    p.add_argument('output', nargs='?', help='Output XBS file (default: stdout)')

    # decrypt
    p = sub.add_parser('decrypt', help='XBS -> JSON (XXTEA decryption)')
    p.add_argument('input', help='Input XBS file')
    p.add_argument('output', nargs='?', help='Output JSON file (default: stdout)')
    p.add_argument('--pretty', action='store_true', default=True, help='Pretty-print JSON output')

    # validate
    p = sub.add_parser('validate', help='Validate a source file\'s structure')
    p.add_argument('input', help='Input JSON or XBS file')

    # inspect
    p = sub.add_parser('inspect', help='Print metadata about a source file')
    p.add_argument('input', help='Input JSON or XBS file')
    p.add_argument('--all', action='store_true', help='Show all sources (default: first 20)')

    # template
    p = sub.add_parser('template', help='Generate a template JSON file')
    p.add_argument('--name', default='MySource', help='Source name')
    p.add_argument('--url', default='https://example.com', help='Source URL')
    p.add_argument('--format', dest='format', default='xiangse', choices=['xiangse', 'legado'],
                   help='Template format')
    p.add_argument('output', nargs='?', help='Output file (default: stdout)')

    # convert
    p = sub.add_parser('convert', help='Convert between 香色闺阁 and Legado formats')
    p.add_argument('input', help='Input JSON or XBS file')
    p.add_argument('output', nargs='?', help='Output JSON file (default: stdout)')
    p.add_argument('--from', dest='from_fmt', default='auto',
                   choices=['auto', 'legado', 'xiangse'], help='Source format')
    p.add_argument('--to', dest='to_fmt', required=True,
                   choices=['legado', 'xiangse'], help='Target format')

    # merge
    p = sub.add_parser('merge', help='Merge sources into a collection')
    p.add_argument('sources', nargs='+', help='Source files to merge (JSON or XBS)')
    p.add_argument('--into', help='Target collection file (creates if not exists)')
    p.add_argument('--output', help='Output file (default: update --into)')
    p.add_argument('--in-place', action='store_true', help='Update --into file in-place')

    args = parser.parse_args()
    if args.key is None:
        args.key = XXTEA_KEY

    # Dispatch
    cmds = {
        'encrypt': cmd_encrypt,
        'decrypt': cmd_decrypt,
        'validate': cmd_validate,
        'inspect': cmd_inspect,
        'template': cmd_template,
        'convert': cmd_convert,
        'merge': cmd_merge,
    }
    cmds[args.command](args)


if __name__ == '__main__':
    main()
