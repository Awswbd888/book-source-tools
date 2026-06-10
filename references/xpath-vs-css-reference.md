# XPath ↔ CSS-like 选择器对照

## 基本模式

| 语义 | 香色闺阁 (XPath) | Legado (CSS-like) |
|------|-------------------|-------------------|
| 标签选择 | `//div` | `div` |
| ID 选择 | `//*[@id='content']` | `#content` |
| Class 选择 | `//*[contains(@class,'book')]` | `.book` |
| 带 class 的标签 | `//div[contains(@class,'book')]` | `div.book` |
| 属性选择 | `//meta[@property='og:novel:book_name']` | `meta[property=og:novel:book_name]` |
| 提取属性 | `//a/@href` | `a@href` |
| 提取文本 | `//a/text()` | `a@text` |
| 提取 HTML | `//div[@id='content']` | `#content@html` |
| 后代选择 | `//div//a` | `div a` |
| 子元素 | `//div/a` | `div>a` |
| 降级选择 | `//img/@_src \| //img/@src` | `img.lazyload@_src\|\|img@src` |

## 详细对照

### 书籍详情 (bookDetail / ruleBookInfo)

| 字段 | 香色闺阁 (XPath) | Legado (CSS-like) |
|------|-------------------|-------------------|
| 书名 | `//meta[@property='og:novel:book_name']/@content` | `meta[property=og:novel:book_name]@content` |
| 作者 | `//meta[@property='og:novel:author']/@content` | `meta[property=og:novel:author]@content` |
| 封面 | `//meta[@property='og:image']/@content` | `meta[property=og:image]@content` |
| 分类 | `//meta[@property='og:novel:category']/@content` | `meta[property=og:novel:category]@content` |
| 简介 | `//meta[@property='og:description']/@content` | `meta[property=og:description]@content` |
| 状态 | `//meta[@property='og:novel:status']/@content` | `meta[property=og:novel:status]@content` |
| 最新章节 | `//meta[@property='og:novel:latest_chapter_name']/@content` | `meta[property=og:novel:latest_chapter_name]@content` |

### 章节列表 (chapterList / ruleToc)

| 字段 | 香色闺阁 (XPath) | Legado (CSS-like) |
|------|-------------------|-------------------|
| 列表容器 | `//ol[@class='BCsectionTwo-top']/li` | `ol.BCsectionTwo-top li` |
| 章节名 | `.//a/text()` | `a@text` |
| 章节链接 | `.//a/@href` | `a@href` |

### 正文 (chapterContent / ruleContent)

| 字段 | 香色闺阁 (XPath) | Legado (CSS-like) |
|------|-------------------|-------------------|
| 正文 | `//div[@id='C0NTENT']/div/p/text()` | `#C0NTENT@html` |

## 复杂 XPath（无 CSS 等价）

以下 XPath 无法直接转换为 CSS-like 选择器，会保留原样并给出警告：

- 含 `position()` 的：`//li[position()=1]`
- 含 `starts-with()` 的：`//a[starts-with(@href, '/book/')]`
- 含 `and`/`or` 的：`//div[@class='a' and @id='b']`
- 深度路径：`//div[@id='a']/div/p/text()`
- 含 `not()` 的：`//div[not(@class='hidden')]`

## 转换规则

### XPath → CSS-like（香色→Legado）

```
//tag[@id='x']/tag      →  tag#x tag
//tag[@class='x']       →  tag.x
//tag/@attr             →  tag@attr
//tag/text()            →  tag@text
.//tag/text()           →  tag@text
.//tag/@href            →  tag@href
//tag                   →  tag
```

### CSS-like → XPath（Legado→香色）

```
tag#id                  →  //tag[@id='id']
tag.class               →  //tag[contains(@class,'class')]
tag[attr=val]@target    →  //tag[@attr='val']/@target
tag@text                →  //tag/text()
tag@attr                →  //tag/@attr
tag                     →  //tag
tag1 tag2               →  //tag1/tag2
```
