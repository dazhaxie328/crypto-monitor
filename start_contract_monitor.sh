#!/bin/bash
# 合约监控启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/contract_monitor.py"

# 检查虚拟环境
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# 检查 .env 文件
ENV_FILE="$HOME/crypto-monitor/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "错误: 未找到 .env 文件"
    exit 1
fi

echo "=========================================="
echo "📝 合约监控系统"
echo "=========================================="
echo "启动时间: $(date)"
echo "按 Ctrl+C 停止"
echo "=========================================="

python3 "$PYTHON_SCRIPT"
