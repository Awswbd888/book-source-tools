# Legado (阅读) 书源 JSON 字段参考

## 顶层结构

```json
{
  "bookSourceName": "站点名称",
  "bookSourceUrl": "https://example.com",
  "bookSourceGroup": "精选",
  "bookSourceType": 0,
  "bookUrlPattern": "",
  "enabled": true,
  "enabledExplore": true,
  "enabledCookieJar": true,
  "customOrder": 0,
  "header": "{\n  \"User-Agent\": \"...\",\n  \"Referer\": \"...\"\n}",
  "exploreUrl": "全部::/category/0/{{page}}.html\n分类名::/category/1/{{page}}.html",
  "ruleExplore": { ... },
  "ruleBookInfo": { ... },
  "ruleToc": { ... },
  "ruleContent": { ... }
}
```

## 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `bookSourceName` | string | 书源名称 |
| `bookSourceUrl` | string | 网站主页 URL |
| `bookSourceGroup` | string | 分组标签 |
| `bookSourceType` | int | 0=小说, 1=有声, 2=漫画, 3=视频, 4=音频 |
| `bookUrlPattern` | string | 书籍详情页 URL 正则 |
| `enabled` | bool | 是否启用 |
| `enabledExplore` | bool | 是否启用发现 |
| `enabledCookieJar` | bool | 是否启用 Cookie |
| `customOrder` | int | 自定义排序 |
| `header` | string | JSON 字符串格式的 HTTP 请求头 |

## header 格式

HTTP 请求头存储为**单行 JSON 字符串**：

```json
"header": "{\n  \"User-Agent\": \"Mozilla/5.0 ...\",\n  \"Referer\": \"https://example.com/\"\n}"
```

## exploreUrl — 发现 URL

使用 `{{page}}` 作为页码占位符，每行一个分类：

```
全部::/category/0/{{page}}.html
都市小说::/category/2/{{page}}.html
玄幻小说::/category/3/{{page}}.html
```

格式：`分类名::URL模板`

## 选择器语法

Legado 使用 **CSS-like 选择器**，非标准 CSS：

| 语法 | 说明 | 示例 |
|------|------|------|
| `tag` | 标签选择 | `div` |
| `tag.class` | 带 class 的标签 | `div.book_name` |
| `.class` | class 选择 | `.book_list` |
| `tag#id` | ID 选择 | `div#content` |
| `#id` | ID 选择 | `#content` |
| `tag[attr=val]` | 属性选择 | `meta[property=og:novel:book_name]` |
| `tag@attr` | 提取属性 | `a@href` |
| `tag@text` | 提取文本 | `a@text` |
| `tag@html` | 提取内部 HTML | `#content@html` |
| `tag1 tag2` | 后代选择 | `ol li` |
| `tag1>tag2` | 子元素选择 | `div>p` |
| `tag1@attr||tag2@attr` | 降级（取第一个非空） | `img.lazyload@_src||img@src` |

注意：`@text` 是提取文本内容，不是提取 `text` 属性。`@html` 是提取内部 HTML。

## ruleBookInfo — 书籍详情规则

| 字段 | 说明 |
|------|------|
| `name` | 书名 |
| `author` | 作者 |
| `kind` | 分类 |
| `intro` | 简介 |
| `coverUrl` | 封面 URL |
| `lastChapter` | 最新章节名 |
| `status` | 状态 |

## ruleToc — 目录规则

| 字段 | 说明 |
|------|------|
| `chapterList` | 章节列表容器 |
| `chapterName` | 章节标题 |
| `chapterUrl` | 章节链接 |

## ruleContent — 正文规则

| 字段 | 说明 |
|------|------|
| `content` | 正文内容选择器 |
| `replaceRegex` | 替换正则 |

## ruleExplore — 发现页规则

| 字段 | 说明 |
|------|------|
| `bookList` | 书籍列表容器 |
| `name` | 书名 |
| `bookUrl` | 详情页链接 |
| `coverUrl` | 封面 URL |
| `author` | 作者 |
| `kind` | 分类 |
| `intro` | 简介 |
| `lastChapter` | 最新章节 |
