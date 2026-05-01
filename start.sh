#!/bin/bash
# 加密货币异动监控 - 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/monitor.py"
CONFIG_FILE="$SCRIPT_DIR/config.json"
DATA_DIR="$HOME/.crypto-monitor"

# 创建数据目录
mkdir -p "$DATA_DIR"

# 检查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "错误: Python3 未安装"
    exit 1
fi

# 检查 requests 库
if ! python3 -c "import requests" 2>/dev/null; then
    echo "安装 requests 库..."
    pip3 install requests -q
fi

# 设置环境变量
if [ -f "$CONFIG_FILE" ]; then
    export TELEGRAM_BOT_TOKEN=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('telegram_bot_token', ''))")
    export TELEGRAM_CHAT_ID=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('telegram_chat_id', ''))")
fi

echo "=========================================="
echo "🚀 加密货币异动监控系统"
echo "=========================================="
echo "配置文件: $CONFIG_FILE"
echo "数据目录: $DATA_DIR"
echo "启动时间: $(date)"
echo "=========================================="
echo ""

# 运行监控脚本
python3 "$PYTHON_SCRIPT"
