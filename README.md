# Book Source Tools (书源工具)

香色闺阁书源制作与转换工具集。

## 概述

针对 iOS 小说阅读器 **香色闺阁** 的书源制作工具，支持：

- **书源制作** — 分析网站结构，生成 XPath 选择器，创建书源 JSON
- **格式转换** — JSON ↔ XBS (XXTEA 加密/解密)，香色闺阁 ↔ Legado 互转
- **合并管理** — 将新书源合并到现有的 sourceModelList.xbs
- **校验检查** — 验证书源结构完整性

## 技术要点

- XBS 格式：XXTEA 加密的 JSON，密钥为固定 16 字节
- 香色闺阁使用 XPath 选择器，Legado 使用 CSS-like 选择器
- Python 标准库实现，无外部依赖

## 项目状态

计划阶段 — 详见 [plan.md](plan.md)
