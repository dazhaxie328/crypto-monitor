#!/bin/bash
# Solana Meme 币监控启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/solana_meme_monitor.py"
PID_FILE="$SCRIPT_DIR/.meme_monitor.pid"
LOG_FILE="$HOME/.crypto-monitor/solana_meme.log"

mkdir -p "$HOME/.crypto-monitor"

case "$1" in
    start)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "Solana Meme 监控已在运行 (PID: $PID)"
                exit 1
            fi
        fi
        
        echo "启动 Solana Meme 币监控..."
        nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        echo "✅ 监控已启动 (PID: $!)"
        echo "日志: $LOG_FILE"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "✅ 监控已停止"
            else
                echo "监控未运行"
                rm -f "$PID_FILE"
            fi
        else
            echo "监控未运行"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p "$PID" > /dev/null 2>&1; then
                echo "✅ Solana Meme 监控运行中 (PID: $PID)"
                tail -5 "$LOG_FILE"
            else
                echo "❌ 监控未运行"
            fi
        else
            echo "❌ 监控未运行"
        fi
        ;;
    log)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "用法: $0 {start|stop|status|log}"
        exit 1
        ;;
esac
