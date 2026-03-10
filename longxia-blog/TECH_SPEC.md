# 龙虾博客 - 技术方案文档

## 1. 系统概述

**目标**：自动抓取新闻、生成摘要、调用 TTS 生成语音播报，发布到 RSS 播客平台。

**核心技术栈**：
- 新闻抓取：RSS + URL 爬虫 + 本地文件监听
- 内容处理：LLM (MiniMax) 摘要 + 口语化改写
- 语音生成：阿里云 qianwen TTS
- 发布分发：RSS Feed + Webhook

---

## 2. 新闻源模块

### 2.1 支持的来源

| 类型 | 实现方式 | 依赖 |
|------|----------|------|
| RSS 订阅 | feedparser 解析 RSS/Atom | feedparser |
| URL 抓取 | requests + BeautifulSoup 提取正文 | requests, bs4 |
| 本地文件夹 | pathlib 监听目录，读取所有文字格式 | 无额外依赖 |

### 2.2 本地文件支持格式

自动根据扩展名选择解析方式：

| 格式 | 扩展名 | 解析方式 |
|------|--------|----------|
| 纯文本 | .txt | 直接读取 |
| Markdown | .md | 直接读取 |
| HTML | .html, .htm | BeautifulSoup 提取正文 |
| JSON | .json | json.loads |
| YAML | .yaml, .yml | pyyaml 解析 |
| PDF | .pdf | pdfplumber (可选) |
| Word | .docx | python-docx (可选) |
| EPUB | .epub | ebooklib (可选) |

### 2.3 配置示例 (sources.yaml)

```yaml
rss:
  - url: "https://www.36kr.com/feed/"
    name: "36氪"
    enabled: true
  - url: "https://www.huxiu.com/rss/"
    name: "虎嗅"
    enabled: true

urls:
  - url: "https://example.com/article"
    name: "文章名"
    enabled: false

local:
  - path: "./inputs"
    enabled: true
    recursive: true
    auto_process: true
```

---

## 3. 内容处理模块

### 3.1 处理流程

```
原始文章 → LLM 摘要 → 关键字提取 → 质量筛选 → 口语化改写 → 播客稿件
```

### 3.2 LLM 摘要 (MiniMax API)

**调用接口**：
- API: `https://api.minimaxi.com/v1/text/chatcompletion_v2`
- Model: `MiniMax-M2.1`
- 用途：从长文章提取关键信息

**Prompt 模板**：
```
请阅读以下文章，然后按要求处理:

文章标题: {title}
文章内容: {content}

请按以下格式输出:
1. 一句话总结这篇文章的主要内容
2. 提取 3 个关键字
3. 判断这篇文章是否值得做成播客 (yes/no)

输出格式:
SUMMARY: <一句话总结>
KEYWORDS: <关键字1>, <关键字2>, <关键字3>
WORTH_IT: <yes/no>
```

### 3.3 口语化改写

将书面文章改写为播客主播的自然口语表达：

**Prompt 模板**：
```
请把以下文章改写成播客主播的口语化稿件:

原文标题: {title}
原文摘要: {summary}

要求:
- 使用自然的口语表达，像主播在说话
- 长度控制在 300-500 字
- 可以适当加入过渡词和感叹词
- 保持信息的准确性和完整性
```

### 3.4 质量筛选

基于 LLM 返回的 `WORTH_IT` 字段过滤，只处理有价值的文章。

---

## 4. TTS 生成模块

### 4.1 阿里云 qianwen TTS

**接口信息**：
- API: `https://dashscope.aliyuncs.com/api/v1/services/audio/t2a/generation`
- Model: `cosyvoice-v1`
- 价格: ¥2-3 / 1M 字符

### 4.2 可用声音

| voice_id | 名称 | 性别 |
|----------|------|------|
| xiaoyun | 小云 | 女 |
| xiaogang | 小刚 | 男 |
| ruoxi | 若曦 | 女 |

### 4.3 参数配置 (voices.yaml)

```yaml
voices:
  xiaoyun:
    name: "小云"
    gender: "female"
  xiaogang:
    name: "小刚"
    gender: "male"

current: "xiaoyun"
speed: 1.0      # 语速 0.5-2.0
volume: 1.0     # 音量 0.1-1.0
pitch: 1.0      # 音调 0.5-2.0
```

### 4.4 输出格式

- 格式: MP3
- 采样率: 32000 Hz

### 4.5 错误处理

- API 超时: 120s
- 失败重试: 最多 3 次
- 失败记录日志，跳过该条继续处理下一条

---

## 5. 发布模块

### 5.1 RSS Feed 生成

生成符合 Apple Podcasts 标准的 RSS 2.0：

**必要字段**：
- title: 播客名称
- description: 播客描述
- link: 网站链接
- itunes:author: 作者
- itunes:image: 封面图
- enclosure: 音频文件 URL + 类型 + 大小

**每期 Episode 字段**：
- title: 标题
- description: 描述
- pubDate: 发布日期
- enclosure: 音频文件
- guid: 唯一标识

### 5.2 文件管理

```
output/
└── episodes/
    └── 2026-03-10/
        └── episode_001.mp3
```

- 按日期归档
- 保留最近 30 期
- 命名规则: `{date}_{index}.mp3`

### 5.3 Webhook 通知

生成完成后 POST 到指定 URL：

```json
{
  "event": "episode_published",
  "timestamp": "2026-03-10T14:00:00Z",
  "data": {
    "episode_count": 3,
    "rss_url": "https://example.com/rss.xml"
  }
}
```

### 5.4 播客平台对接

| 平台 | 对接方式 |
|------|----------|
| Apple Podcasts | 提交 RSS URL |
| Spotify | 提交 RSS URL |
| 小宇宙 | 提交 RSS URL |
| 其他 | 访问 RSS 即可订阅 |

---

## 6. 定时任务

### 6.1 每日任务流程

```
Cron (每天 8:00)
    ↓
1. 新闻抓取 (fetcher.py)
    ↓
2. LLM 摘要处理 (processor.py)
    ↓
3. TTS 生成 (tts.py)
    ↓
4. 发布 + 通知 (publisher.py)
```

### 6.2 本地文件夹监听 (可选)

使用 fswatch (macOS) 或 inotifywait (Linux) 监听文件夹变化，有新文件自动触发处理。

---

## 7. 数据流图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           新闻源                                     │
├──────────────┬──────────────────┬──────────────────────────────────┤
│   RSS 订阅    │   URL 抓取       │        本地文件夹                │
│  (feedparser)│ (requests+bs4)   │       (pathlib)                  │
└──────┬───────┴────────┬─────────┴──────────────┬──────────────────┘
       │                 │                         │
       └─────────────────┼─────────────────────────┘
                         ↓
              ┌─────────────────────┐
              │     原始文章数据     │
              │   (JSON 草稿)       │
              └──────────┬──────────┘
                         ↓
       ┌─────────────────────────────────────────┐
       │            内容处理模块                   │
       ├─────────────────────────────────────────┤
       │  1. LLM 摘要 (MiniMax)                  │
       │  2. 关键字提取                           │
       │  3. 质量筛选                             │
       │  4. 口语化改写                           │
       └──────────┬──────────────────────────────┘
                  ↓
       ┌─────────────────────────────────────────┐
       │          播客稿件 (.txt)                 │
       └──────────┬──────────────────────────────┘
                  ↓
       ┌─────────────────────────────────────────┐
       │          TTS 生成模块                   │
       │     (qianwen cosyvoice-v1)              │
       └──────────┬──────────────────────────────┘
                  ↓
       ┌─────────────────────────────────────────┐
       │          音频文件 (.mp3)                │
       └──────────┬──────────────────────────────┘
                  ↓
       ┌─────────────────────────────────────────┐
       │          发布模块                        │
       ├─────────────────────────────────────────┤
       │  1. RSS Feed 生成                       │
       │  2. 文件归档                            │
       │  3. Webhook 通知                        │
       └─────────────────────────────────────────┘
```

---

## 8. 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| MINIMAX_API_KEY | MiniMax API Key (摘要) | ✅ |
| DASHSCOPE_API_KEY | 阿里云 API Key (TTS) | ✅ |

---

## 9. 依赖列表

```
feedparser>=6.0.0      # RSS 解析
requests>=2.28.0       # HTTP 请求
beautifulsoup4>=4.11.0 # 网页解析
lxml>=4.9.0            # XML/HTML 解析器
pyyaml>=6.0            # YAML 配置

# 可选
pdfplumber>=0.9.0      # PDF 解析
python-docx>=0.8.11    # Word 解析
ebooklib>=0.18         # EPUB 解析
```

---

## 10. 实施计划

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| Phase 1 | 基础框架搭建 + 新闻抓取 (含本地) | 1-2h |
| Phase 2 | LLM 摘要 + 口语化改写 | 1h |
| Phase 3 | qianwen TTS 集成 | 30min |
| Phase 4 | RSS Feed 生成 + 文件管理 | 1h |
| Phase 5 | Webhook 通知 + 定时任务 | 30min |

---

## 11. 后续扩展

- [ ] 多语言支持 (英文新闻)
- [ ] 多声音混搭 (男声/女声交替)
- [ ] 背景音乐混音
- [ ] 视频生成 (配合图片)
- [ ] 社交媒体自动发布 (Twitter/X)
