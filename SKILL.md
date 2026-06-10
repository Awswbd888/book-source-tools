---
name: book-source-tools
description: "Create, convert, and manage Chinese novel-reading app book sources (书源). Encrypt/decrypt 香色闺阁 XBS format, convert between 香色闺阁 and Legado formats, merge sources, analyze websites for XPath/CSS selectors, and generate templates."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [书源, 香色闺阁, XBS, XXTEA, legado, 转换, novel, reading-app, book-source, selector]
    category: productivity
---

# Book Source Tools (书源工具)

Create, convert, and manage book sources (书源) for Chinese novel reading apps.

**支持的格式：**
- **香色闺阁** — iOS 阅读器，使用 XBS 格式（XXTEA 加密的 JSON），XPath 选择器
- **Legado（阅读）** — Android 阅读器，使用纯 JSON，CSS-like 选择器

## 快速使用

```bash
# JSON -> XBS 加密
python scripts/booksource_tool.py encrypt input.json output.xbs

# XBS -> JSON 解密
python scripts/booksource_tool.py decrypt input.xbs output.json

# 格式转换（香色闺阁 -> Legado）
python scripts/booksource_tool.py convert input.json --to legado output.json

# 格式转换（Legado -> 香色闺阁）
python scripts/booksource_tool.py convert input.json --to xiangse output.json

# 查询书源元信息
python scripts/booksource_tool.py inspect source.xbs

# 合并新书源到已有集合
python scripts/booksource_tool.py merge new_source.json --into collection.xbs

# 校验书源结构
python scripts/booksource_tool.py validate source.json

# 生成模板
python scripts/booksource_tool.py template --name "站点名" --url "https://example.com"
```

## 子命令速查

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `encrypt` | JSON → XBS | JSON 文件 | XBS 文件 |
| `decrypt` | XBS → JSON | XBS 文件 | JSON 文件 |
| `convert` | 格式互转 | JSON/XBS | JSON |
| `merge` | 合并书源 | JSON/XBS | JSON/XBS |
| `validate` | 校验结构 | JSON/XBS | — |
| `inspect` | 元信息查询 | JSON/XBS | — |
| `template` | 生成模板 | — | JSON |

## 制作书源流程

1. **分析网站** — 用浏览器打开一个小说详情页，查看 HTML 结构
2. **确定选择器** — 找到书名、作者、封面、章节列表、正文的 XPath
3. **生成模板** — `template --name "站点" --url "https://..." > source.json`
4. **填写字段** — 编辑 JSON，填入分析得到的 XPath
5. **校验** — `validate source.json`
6. **加密** — `encrypt source.json source.xbs`
7. **导入测试** — 在香色闺阁中导入 source.xbs 验证

## 格式对比

| 特性 | 香色闺阁 | Legado |
|------|---------|--------|
| 选择器 | XPath | CSS-like |
| 存储格式 | XBS (XXTEA加密) | JSON (明文) |
| 多源文件 | 单 JSON 含多源 | 单文件单源 |
| 元数据结构 | 源码名为顶层键 | 扁平 JSON |

## 选择器速查

**XPath (香色闺阁)：**
- `//meta[@property='og:novel:book_name']/@content` — OG meta 标签
- `//div[@class='list']/li` — class 选择
- `.//a/text()` — 相对路径文本
- `.//a/@href` — 相对路径链接

**CSS-like (Legado)：**
- `meta[property=og:novel:book_name]@content` — 属性选择
- `div.list li` — class 选择
- `a@text` — 提取文本
- `a@href` — 提取链接

## 常见问题

1. **GBK 编码错误** — Windows 终端运行需设置 `PYTHONIOENCODING=utf-8`
2. **XXTEA 解密失败** — 文件可能损坏或使用了不同的密钥
3. **搜索触发验证码** — 有些网站搜索需要验证码，bookSource 中可以不配搜索
4. **选择器不匹配** — 先用浏览器 DevTools 验证 XPath 确实能匹配到元素

## 相关文件

- `scripts/booksource_tool.py` — CLI 主工具
- `scripts/_common.py` — 共享库（加解密、选择器转换）
- `templates/` — JSON 模板
- `references/` — 格式和选择器参考文档

## 技术细节

- XBS = XXTEA 加密的 JSON，密钥固定为 "覆盖满金源漫"（16 字节 UTF-8）
- 加密流程：JSON → 4 字节对齐填充 → 末尾附加原始长度(uint32 LE) → XXTEA 加密
- 无外部依赖，仅使用 Python 标准库
