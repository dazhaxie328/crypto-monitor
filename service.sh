#!/bin/bash
# 后台运行监控脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.monitor.pid"
LOG_FILE="$HOME/.crypto-monitor/monitor.log"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "监控已在运行中 (PID: $PID)"
            return 1
        fi
    fi
    
    echo "启动监控..."
    nohup "$SCRIPT_DIR/start.sh" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "✅ 监控已启动 (PID: $!)"
    echo "日志文件: $LOG_FILE"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "停止监控 (PID: $PID)..."
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
}

status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ 监控运行中 (PID: $PID)"
            echo "日志文件: $LOG_FILE"
            echo "最近日志:"
            tail -5 "$LOG_FILE"
        else
            echo "❌ 监控未运行"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ 监控未运行"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    log)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|log}"
        exit 1
        ;;
esac
