#!/bin/bash
# 测试本地文件夹监听

echo "📁 Testing local folder watch..."
echo ""
echo "Create/place files in: ./inputs/"
echo "Press Ctrl+C to exit"
echo ""

# 创建输入目录
mkdir -p ./inputs

# 监听变化 (使用 fswatch 或 inotifywait)
# macOS
if command -v fswatch &> /dev/null; then
    echo "Using fswatch (macOS)..."
    fswatch -o ./inputs | while read -r; do
        echo "📝 Change detected! Running fetcher..."
        python3 scripts/fetcher.py
    done
# Linux
elif command -v inotifywait &> /dev/null; then
    echo "Using inotifywait (Linux)..."
    inotifywait -m -e create -e modify ./inputs | while read -r; do
        echo "📝 Change detected! Running fetcher..."
        python3 scripts/fetcher.py
    done
else
    echo "⚠️ No file watcher found (fswatch/inotifywait)"
    echo "Please install:"
    echo "  macOS: brew install fswatch"
    echo "  Linux: sudo apt install inotify-tools"
    echo ""
    echo "Manual test: put a file in ./inputs and run:"
    echo "  python3 scripts/fetcher.py"
fi
