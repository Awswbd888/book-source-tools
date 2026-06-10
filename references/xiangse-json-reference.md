# 香色闺阁 JSON 字段参考

## 顶层结构

```json
{
  "站点名称": {
    "sourceName": "站点名称",
    "sourceUrl": "https://example.com",
    "sourceType": "novel",
    "enable": 1,
    "httpHeaders": { ... },
    "desc": "描述",
    "weight": "9999",
    "miniAppVersion": "2.0",
    "lastModifyTime": "1749600000",
    "loginUrl": "",
    "searchBook": { ... },
    "searchShudan": { ... },
    "relatedWord": { ... },
    "shupingList": { ... },
    "shupingHome": { ... },
    "shudanDetail": { ... },
    "shudanList": {},
    "bookDetail": { ... },
    "chapterList": { ... },
    "chapterContent": { ... },
    "bookWorld": { ... }
  }
}
```

## 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `sourceName` | string | 书源名称，与顶层键一致 |
| `sourceUrl` | string | 网站主页 URL |
| `sourceType` | string | `novel` / `comic` / `video` / `audio` |
| `enable` | int | 1=启用, 0=禁用 |
| `httpHeaders` | object | 全局 HTTP 请求头（User-Agent, Referer 等） |
| `desc` | string | 描述文字 |
| `weight` | string | 排序权重（越大越靠前） |
| `miniAppVersion` | string | 支持的最低版本，通常 "2.0" |
| `lastModifyTime` | string | Unix 时间戳 |
| `loginUrl` | string | 登录 URL（可空） |
| `shudanList` | object | 书单列表配置（可空） |

## 动作结构（Action）

每个动作（bookDetail, chapterList, chapterContent, browse 等）使用统一的结构：

| 字段 | 说明 |
|------|------|
| `actionID` | 动作标识，与键名一致 |
| `parserID` | 解析器类型：`DOM` (HTML解析) / `JSON` (JSON解析) |
| `host` | 请求域名 |
| `httpHeaders` | 该动作专属的 HTTP 请求头 |
| `responseFormatType` | 响应格式：`html` / `json` / `text` |
| `requestInfo` | URL 模板：`%@result` 表示直接使用结果，`@js:\nreturn ...;` 用 JS 处理 URL |
| `validConfig` | 有效性校验（通常为空） |

## bookDetail — 书籍详情

| 字段 | 说明 | XPath 示例 |
|------|------|-----------|
| `bookName` | 书名 | `//meta[@property='og:novel:book_name']/@content` |
| `author` | 作者 | `//meta[@property='og:novel:author']/@content` |
| `cover` | 封面图 | `//meta[@property='og:image']/@content` |
| `cat` | 分类 | `//meta[@property='og:novel:category']/@content` |
| `desc` | 简介 | `//meta[@property='og:description']/@content` |
| `status` | 状态 | `//meta[@property='og:novel:status']/@content` |
| `lastChapterTitle` | 最新章节名 | `//meta[@property='og:novel:latest_chapter_name']/@content` |
| `wordCount` | 字数（可空） | |

## chapterList — 章节列表

| 字段 | 说明 |
|------|------|
| `list` | 章节列表容器 XPath |
| `title` | 章节标题 XPath（相对于 list 的每个元素） |
| `url` | 章节链接 XPath（相对于 list 的每个元素） |

## chapterContent — 正文内容

| 字段 | 说明 |
|------|------|
| `content` | 正文内容 XPath |
| `replaceRegex` | 内容清洗正则表达式（匹配的内容会被移除） |

## bookWorld.browse — 浏览发现

| 字段 | 说明 |
|------|------|
| `requestInfo` | URL 模板，可包含 JS 代码处理分页 |
| `list` | 书籍列表容器 XPath |
| `bookName` | 书名 XPath |
| `detailUrl` | 详情页链接 XPath |
| `cover` | 封面图 XPath |
| `moreKey` | 分类筛选 JSON 配置 |

## requestInfo 格式

- `%@result` — 直接使用传入的 URL
- `%@keyWord` — 搜索关键词占位符
- `%@pageIndex` — 页码占位符
- `@js:\nreturn ...;` — JavaScript 代码，用于拼接 URL：

```javascript
@js:
return result + 'catalog/';
```

```javascript
@js:
return config.host + '/category/0/' + params.pageIndex + '.html';
```

其中 `result` 是传入的 URL，`config.host` 是 sourceUrl，`params.pageIndex` 是页码。

## 选择器说明

- 使用标准 XPath 语法
- 相对于当前 HTML 文档
- `//` 表示后代选择，`/` 表示子元素选择
- `.//` 表示相对当前节点的后代选择
- `@` 用于选取属性
- `text()` 用于选取文本节点
