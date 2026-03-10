---
name: longxia-blog
description: AI 新闻播客系统 - 自动抓取新闻、生成摘要、调用 TTS 生成语音播报，发布到 RSS 播客平台。
---

# 龙虾博客 Skill

AI 新闻播客系统，自动抓取新闻、生成摘要、调用 TTS 生成语音播报。

## 功能

- **多新闻源支持**: RSS 订阅、URL 抓取、本地文件夹
- **LLM 摘要**: 自动提取关键信息，口语化改写
- **TTS 生成**: 调用阿里云 qianwen 生成语音
- **发布分发**: RSS Feed、Webhook 通知、文件归档

## 命令

```bash
# 每日任务 (cron 调用)
python3 scripts/run_daily.sh

# 测试本地文件夹监听
python3 scripts/test_local_watch.sh

# 单独运行模块
python3 scripts/fetcher.py --source rss
python3 scripts/processor.py --input draft.md
python3 scripts/tts.py --input script.md
python3 scripts/publisher.py --episode 2026-03-10-001
```

## 配置

- `config/sources.yaml` - 新闻源配置
- `config/voices.yaml` - TTS 声音配置  
- `config/publish.yaml` - 发布配置

## 环境变量

- `QIANAWEN_API_KEY` - 阿里云 qianwen API Key
- `MINIMAX_API_KEY` - MiniMax API Key (用于摘要)
