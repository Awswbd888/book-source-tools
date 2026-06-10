# 解析器与响应类型参考

## parserID（解析器类型）

| 值 | 说明 | 适用场景 |
|-----|------|---------|
| `DOM` | 使用 XPath 解析 HTML | 大多数小说、漫画网站 |
| `JSON` | 解析 JSON 响应 | API 接口类网站 |

## responseFormatType（响应格式）

| 值 | 说明 |
|-----|------|
| `html` | HTML 文档（默认，与 DOM 解析器配合） |
| `json` | JSON 响应（与 JSON 解析器配合） |
| `text` | 纯文本 |

## 常用配置

### 基本小说站（HTML + XPath）

```json
{
  "actionID": "bookDetail",
  "parserID": "DOM",
  "responseFormatType": "html",
  "requestInfo": "%@result"
}
```

### JSON API 站

```json
{
  "actionID": "bookDetail",
  "parserID": "JSON",
  "responseFormatType": "json",
  "requestInfo": "%@result"
}
```

## requestInfo 格式详解

### `%@result` — 直接使用结果

最常见的格式，直接将传进来的 URL 作为请求地址。

### `%@keyWord` — 搜索关键词

搜索时使用，替换为用户的搜索关键词。

### `@js:return ...;` — JavaScript 代码

用 JS 处理 URL，支持以下变量：
- `result` — 传入的 URL 或搜索结果
- `config.host` — 书源的 `sourceUrl`
- `params.pageIndex` — 当前页码（从 1 开始）
- `params.keyWord` — 搜索关键词

示例 — 在 URL 后追加 `/catalog/`：
```javascript
@js:
return result + 'catalog/';
```

示例 — 构造分类浏览 URL：
```javascript
@js:
return config.host + '/category/0/' + params.pageIndex + '.html';
```

## 常见站点结构

### OG Meta 标签站

许多小说站使用 Open Graph 协议在 meta 标签中提供书籍信息：

```html
<meta property="og:novel:book_name" content="书名">
<meta property="og:novel:author" content="作者">
<meta property="og:novel:category" content="分类">
<meta property="og:novel:description" content="简介">
<meta property="og:novel:status" content="连载">
<meta property="og:novel:latest_chapter_name" content="最新章节名">
<meta property="og:image" content="封面URL">
```

对应的 XPath：
```
//meta[@property='og:novel:book_name']/@content
```

### 常见目录结构

```
<ol class="BCsectionTwo-top">
  <li><a href="/book/123/1.html">第一章</a></li>
  <li><a href="/book/123/2.html">第二章</a></li>
</ol>
```

对应的 chapterList 配置：
```json
{
  "list": "//ol[@class='BCsectionTwo-top']/li",
  "title": ".//a/text()",
  "url": ".//a/@href"
}
```

### 常见正文结构

```html
<div id="C0NTENT">
  <div><p>正文第一段</p></div>
  <div><p>正文第二段</p></div>
</div>
```

对应的 chapterContent 配置：
```json
{
  "content": "//div[@id='C0NTENT']/div/p/text()",
  "replaceRegex": "本站新.*?域名"
}
```
