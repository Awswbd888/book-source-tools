# 书源制作与转换 Skill — 实施计划

## 背景

用户使用香色闺阁（iOS 小说阅读器），需要一套工具来：
1. 制作新书源（分析网站结构 → 生成 XPath 选择器 → 生成 JSON）
2. 格式转换（JSON ↔ XBS 加解密，香色闺阁 ↔ Legado 互转）
3. 合并书源（将新书源添加到现有的 sourceModelList.xbs）

已存在的资产：
- `D:\AI\json2xbs.py` — 纯 Python XXTEA 加密（仅 JSON→XBS，无解密）
- `D:\AI\021best_xiangse.json` — 香色闺阁格式书源样例
- `D:\AI\021best_booksource.json` — 同一网站 Legado 格式
- `D:\AI\021best_rourouwu.xbs` — 编译后的 XBS
- `D:\AI\sourceModelList.xbs` — 12MB 含 1463 个书源
- `D:\AI\sourceModelList_decrypted.json` — 解密后的参考文件

XBS 格式：JSON → 4字节填充 → 末尾附加原始长度(uint32 LE) → XXTEA 加密（密钥: UTF-8 "覆盖满金源漫"）

---

## 目录结构

```
hermes-agent/skills/productivity/book-source-tools/
├── SKILL.md                        # 主 skill 定义
├── scripts/
│   ├── _common.py                  # 共享库：XXTEA 加解密、选择器转换、字段映射
│   └── booksource_tool.py          # CLI 入口：encrypt/decrypt/convert/merge/validate/inspect/template
├── templates/
│   ├── template_xiangse.json       # 香色闺阁模板（含占位符）
│   └── template_legado.json        # Legado 模板（含占位符）
├── references/
│   ├── xiangse-json-reference.md   # 香色闺阁字段完整参考
│   ├── legado-format-reference.md  # Legado 字段完整参考
│   ├── xpath-vs-css-reference.md   # 选择器语法对照表
│   └── parser-types-reference.md   # parserID / 响应类型参考
└── tests/
    ├── conftest.py                 # pytest fixtures
    ├── test_encrypt_decrypt.py     # 加解密往返测试
    ├── test_format_conversion.py   # 格式转换测试
    ├── test_merge.py               # 合并去重测试
    └── test_validate.py            # 校验逻辑测试
```

---

## 实施步骤

### Phase 1: 核心库 (`_common.py` + `booksource_tool.py`)

| # | 内容 | 文件 |
|---|------|------|
| 1.1 | 从 json2xbs.py 移植 `xxtea_encrypt` + 新建 `xxtea_decrypt` | `_common.py` |
| 1.2 | 实现 `encrypt` / `decrypt` 子命令 | `booksource_tool.py` |
| 1.3 | 实现 `validate`（JSON 结构校验） | `booksource_tool.py` |
| 1.4 | 实现 `inspect`（解密后列出书源元信息） | `booksource_tool.py` |
| 1.5 | 实现 `template`（生成模板 JSON） | `booksource_tool.py` |
| 1.6 | 验证：`encrypt 021best_xiangse.json test.xbs` → `decrypt test.xbs out.json` → diff 应为空 | 手动测试 |

### Phase 2: 格式转换

| # | 内容 | 文件 |
|---|------|------|
| 2.1 | CSS 选择器 ↔ XPath 转换函数 | `_common.py` |
| 2.2 | 字段映射表（两种格式对应关系） | `_common.py` |
| 2.3 | 实现 `convert` 子命令（legado↔xiangse），处理头部结构差异、JS代码与模板URL的映射 | `booksource_tool.py` |
| 2.4 | 测试：转换 021best_xiangse.json → Legado 格式，与 021best_booksource.json 做结构对比 | 手动测试 |

### Phase 3: 合并功能

| # | 内容 | 文件 |
|---|------|------|
| 3.1 | 实现 `merge` 子命令（解密→解析→去重→合并→加密） | `booksource_tool.py` |
| 3.2 | 测试：合并 021best_rourouwu.xbs 到 sourceModelList.xbs | 手动测试 |

### Phase 4: 参考文档与模板

| # | 内容 | 文件 |
|---|------|------|
| 4.1 | 香色闺阁字段完整参考（动作结构、XPath 提取器、bookWorld 配置） | `references/xiangse-json-reference.md` |
| 4.2 | Legado 字段完整参考（扁平结构、{{page}} 模板、header 字符串格式） | `references/legado-format-reference.md` |
| 4.3 | 选择器语法对照表（XPath ↔ CSS-like 常见模式） | `references/xpath-vs-css-reference.md` |
| 4.4 | parserID/响应类型说明 | `references/parser-types-reference.md` |
| 4.5 | 两个模板 JSON 文件（含占位符） | `templates/*.json` |

### Phase 5: SKILL.md

| # | 内容 |
|---|------|
| 5.1 | 编写 SKILL.md：YAML frontmatter + 速查表 + 格式说明 + 逐步教程 + 选择器参考 + 常见陷阱 + 一键配方 |

### Phase 6: 测试

| # | 内容 |
|---|------|
| 6.1 | pytest fixtures（样本书源 JSON、加密 XBS 字节） |
| 6.2 | 加解密往返测试、格式转换测试、合并去重测试、校验测试 |

---

## 关键设计决策

1. **无外部依赖** — 仅用 Python 标准库，无 pip 依赖
2. **复用已有文件** — 不复制 json2xbs.py 等，测试通过路径引用
3. **降级友好** — 选择器转换对复杂 XPath（含 position()/starts-with 等）给出警告而非静默失败
4. **大文件处理** — 合并操作分步进行，不将整个 sourceModelList.xbs 解密后全放内存
5. **加密密钥** — 硬编码在 `_common.py` 中，同时支持 `--key` 参数覆盖

## 验证方法

- 往返测试：加密后再解密应得到原始 JSON（忽略键顺序）
- 结构对比：`convert` 后的输出应与现有参考文件结构一致
- 手动验证：生成的 XBS 文件可用香色闺阁 App 导入
- `pytest` 执行全部单元测试
