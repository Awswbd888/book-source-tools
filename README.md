# Book Source Tools (书源工具)

> 香色闺阁书源制作、转换与管理工具集 | CLI tools for Chinese novel-reading app book sources

[![tests](https://img.shields.io/badge/tests-69%20passed-brightgreen)](#)
[![python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 概述

针对 iOS 小说阅读器 **香色闺阁** 和 Android 阅读器 **Legado（阅读）** 的书源全生命周期管理工具。

### 功能

- **🔐 XBS 加解密** — JSON 与 XBS（XXTEA 加密）格式互转
- **🔄 格式转换** — 香色闺阁（XPath）↔ Legado（CSS-like）互相转换
- **📦 书源合并** — 将新书源合并到现有的 `sourceModelList.xbs`
- **✅ 结构校验** — 检查书源 JSON 结构完整性
- **🔍 元信息查询** — 查看 XBS/JSON 文件中的书源详情
- **📋 模板生成** — 快速生成新书源的 JSON 模板

---

## 快速开始

### 环境要求

- Python 3.10+
- 无任何第三方依赖（仅用标准库）

### 安装

```bash
git clone https://github.com/Awswbd888/book-source-tools.git
cd book-source-tools/scripts
```

### 使用示例

**XBS 加解密：**
```bash
# JSON → XBS 加密
python booksource_tool.py encrypt source.json source.xbs

# XBS → JSON 解密
python booksource_tool.py decrypt source.xbs source.json
```

**格式转换：**
```bash
# 香色闺阁 → Legado
python booksource_tool.py convert xiangse_source.json --to legado legado_source.json

# Legado → 香色闺阁
python booksource_tool.py convert legado_source.json --to xiangse xiangse_source.json
```

**合并与校验：**
```bash
# 合并新书源到已有集合
python booksource_tool.py merge new_source.xbs --into sourceModelList.xbs

# 校验书源结构
python booksource_tool.py validate source.json

# 查看书源元信息
python booksource_tool.py inspect source.xbs --all

# 生成模板
python booksource_tool.py template --name "我的书源" --url "https://example.com" template.json
```

---

## 命令行参考

| 命令 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `encrypt` | JSON → XBS 加密 | JSON 文件 | XBS 文件 |
| `decrypt` | XBS → JSON 解密 | XBS 文件 | JSON 文件 |
| `convert` | 香色闺阁 ↔ Legado | JSON/XBS | JSON |
| `merge` | 合并书源 | JSON/XBS | JSON/XBS |
| `validate` | 校验结构 | JSON/XBS | — |
| `inspect` | 元信息查询 | JSON/XBS | — |
| `template` | 生成模板 | — | JSON |

详细用法见 [SKILL.md](SKILL.md)。

---

## 制作书源流程

1. **分析网站** — 用浏览器 DevTools 查看小说详情页的 HTML 结构
2. **确定选择器** — 找到书名、作者、章节列表、正文的 XPath
3. **生成模板** — `python booksource_tool.py template --name "站点名" --url "https://..." > source.json`
4. **填入选择器** — 编辑 JSON，将分析得到的 XPath 填入对应字段
5. **校验** — `python booksource_tool.py validate source.json`
6. **加密** — `python booksource_tool.py encrypt source.json source.xbs`
7. **导入测试** — 在香色闺阁中导入 `source.xbs` 验证

---

## 格式说明

### 香色闺阁

iOS 阅读器，使用 `.xbs` 格式（XXTEA 加密的 JSON）。选择器使用 **XPath** 语法。

```json
{
  "站点名": {
    "sourceName": "站点名",
    "sourceUrl": "https://example.com",
    "bookDetail": {
      "bookName": "//meta[@property='og:novel:book_name']/@content",
      "author": "//meta[@property='og:novel:author']/@content"
    }
  }
}
```

### Legado（阅读）

Android 阅读器，使用纯 JSON 格式。选择器使用 **CSS-like** 语法。

```json
{
  "bookSourceName": "站点名",
  "bookSourceUrl": "https://example.com",
  "ruleBookInfo": {
    "name": "meta[property=og:novel:book_name]@content",
    "author": "meta[property=og:novel:author]@content"
  }
}
```

### 选择器对照

| 语义 | 香色闺阁 (XPath) | Legado (CSS-like) |
|------|-------------------|-------------------|
| 提取属性 | `//meta/@content` | `meta@content` |
| 提取文本 | `//a/text()` | `a@text` |
| ID 选择 | `//*[@id='content']` | `#content` |
| Class 选择 | `//div[contains(@class,'list')]` | `div.list` |
| 属性选择 | `//meta[@property='og:title']` | `meta[property=og:title]` |

---

## 项目结构

```
├── SKILL.md                      # Skill 文档（面向 Claude Code 用户）
├── scripts/
│   ├── booksource_tool.py        # CLI 主工具（7个子命令）
│   └── _common.py                # 核心库（加解密、选择器转换）
├── templates/                    # JSON 模板
├── references/                   # 格式与选择器参考文档
├── tests/                        # pytest 测试（69/69 通过）
└── examples/                     # 书源示例文件
```

---

## 技术细节

- **XBS 格式**：XXTEA 加密的 JSON。加密流程：JSON → 4字节对齐填充 → 末尾附加原始长度(uint32 LE) → XXTEA 加密
- **加密密钥**：固定 16 字节（UTF-8 编码的"覆盖满金源漫"）
- **无外部依赖**：仅使用 Python 标准库
- **跨平台**：Windows / macOS / Linux
- **Windows 用户**：终端可能出现 GBK 编码问题，设置环境变量 `PYTHONIOENCODING=utf-8` 即可

---

## 许可证

MIT
