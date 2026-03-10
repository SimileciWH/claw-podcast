#!/bin/bash
# 龙虾博客 - 每日任务入口

echo "========================================"
echo "🦞 龙虾博客 - 每日任务"
echo "========================================"
echo ""

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查环境变量
if [ -z "$MINIMAX_API_KEY" ]; then
    echo "❌ Error: MINIMAX_API_KEY not set"
    exit 1
fi

if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "❌ Error: DASHSCOPE_API_KEY not set"
    exit 1
fi

# Step 1: 新闻抓取
echo "📥 Step 1: Fetching news..."
python3 scripts/fetcher.py
if [ $? -ne 0 ]; then
    echo "❌ Fetcher failed!"
    exit 1
fi
echo ""

# Step 2: 内容处理 (LLM 摘要)
echo "✍️ Step 2: Processing content..."
python3 scripts/processor.py
if [ $? -ne 0 ]; then
    echo "❌ Processor failed!"
    exit 1
fi
echo ""

# Step 3: TTS 生成
echo "🎙️ Step 3: Generating TTS..."
python3 scripts/tts.py
if [ $? -ne 0 ]; then
    echo "❌ TTS failed!"
    exit 1
fi
echo ""

# Step 4: 发布
echo "🚀 Step 4: Publishing..."
python3 scripts/publisher.py
if [ $? -ne 0 ]; then
    echo "❌ Publisher failed!"
    exit 1
fi
echo ""

echo "✅ Daily task completed!"
echo "📁 Output: ./output/"
