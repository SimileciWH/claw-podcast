# 龙虾博客 - AI 新闻播客系统

自动抓取新闻、生成摘要、调用 TTS 生成语音播报，发布到 RSS 播客平台。

## 功能

- **多新闻源支持**: RSS 订阅、URL 抓取、本地文件夹
- **LLM 摘要**: 自动提取关键信息，口语化改写
- **TTS 生成**: 调用阿里云 qianwen 生成语音
- **发布分发**: RSS Feed、Webhook 通知、文件归档

## 使用方法

```bash
# 每日任务
python3 scripts/run_daily.sh

# 监听本地文件夹
python3 scripts/test_local_watch.sh

# 单独运行某个模块
python3 scripts/fetcher.py
python3 scripts/processor.py
python3 scripts/tts.py
python3 scripts/publisher.py
```

## 配置

- `config/sources.yaml` - 新闻源配置
- `config/voices.yaml` - TTS 声音配置
- `config/publish.yaml` - 发布配置

## 输出

- `output/episodes/YYYY-MM-DD/` - 每日生成的音频
- `output/rss.xml` - RSS Feed
