#!/bin/bash
# 加密货币监控管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_menu() {
    echo ""
    echo "=========================================="
    echo "🚀 加密货币监控系统"
    echo "=========================================="
    echo "1. 启动全币种监控"
    echo "2. 启动 Solana Meme 监控"
    echo "3. 启动全部监控"
    echo "4. 停止全部监控"
    echo "5. 查看状态"
    echo "6. 查看日志"
    echo "7. 测试 API 连接"
    echo "8. 配置 Telegram 推送"
    echo "0. 退出"
    echo "=========================================="
    echo -n "请选择: "
}

start_all_monitor() {
    echo "启动全币种监控..."
    "$SCRIPT_DIR/service.sh" start
}

start_meme_monitor() {
    echo "启动 Solana Meme 监控..."
    "$SCRIPT_DIR/meme_service.sh" start
}

start_all() {
    start_all_monitor
    echo ""
    start_meme_monitor
}

stop_all() {
    echo "停止全币种监控..."
    "$SCRIPT_DIR/service.sh" stop
    echo ""
    echo "停止 Solana Meme 监控..."
    "$SCRIPT_DIR/meme_service.sh" stop
}

show_status() {
    echo "全币种监控状态:"
    "$SCRIPT_DIR/service.sh" status
    echo ""
    echo "Solana Meme 监控状态:"
    "$SCRIPT_DIR/meme_service.sh" status
}

show_logs() {
    echo "选择日志:"
    echo "1. 全币种监控日志"
    echo "2. Solana Meme 监控日志"
    echo -n "请选择: "
    read choice
    
    case $choice in
        1) "$SCRIPT_DIR/service.sh" log ;;
        2) "$SCRIPT_DIR/meme_service.sh" log ;;
        *) echo "无效选择" ;;
    esac
}

test_api() {
    echo "测试 CoinGecko API..."
    python3 -c "
import requests
try:
    resp = requests.get('https://api.coingecko.com/api/v3/ping', timeout=10)
    if resp.status_code == 200:
        print('✅ API 连接正常')
    else:
        print(f'❌ API 返回状态码: {resp.status_code}')
except Exception as e:
    print(f'❌ API 连接失败: {e}')
"
}

setup_telegram() {
    echo "=========================================="
    echo "📱 Telegram 推送配置"
    echo "=========================================="
    echo ""
    echo "步骤 1: 创建 Bot"
    echo "  1. 在 Telegram 搜索 @BotFather"
    echo "  2. 发送 /newbot"
    echo "  3. 按提示创建 Bot"
    echo "  4. 获取 Bot Token"
    echo ""
    echo "步骤 2: 获取 Chat ID"
    echo "  1. 搜索你创建的 Bot"
    echo "  2. 发送任意消息"
    echo "  3. 访问: https://api.telegram.org/bot<TOKEN>/getUpdates"
    echo "  4. 找到 chat.id 字段"
    echo ""
    echo -n "请输入 Bot Token (留空跳过): "
    read bot_token
    echo -n "请输入 Chat ID (留空跳过): "
    read chat_id
    
    if [ -n "$bot_token" ] && [ -n "$chat_id" ]; then
        # 更新配置文件
        python3 -c "
import json
config_file = '$SCRIPT_DIR/config.json'
try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    config['telegram_bot_token'] = '$bot_token'
    config['telegram_chat_id'] = '$chat_id'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    print('✅ Telegram 配置已保存')
except Exception as e:
    print(f'❌ 保存配置失败: {e}')
"
        
        # 设置环境变量
        export TELEGRAM_BOT_TOKEN="$bot_token"
        export TELEGRAM_CHAT_ID="$chat_id"
        
        # 测试推送
        echo "测试 Telegram 推送..."
        python3 -c "
import requests
token = '$bot_token'
chat_id = '$chat_id'
url = f'https://api.telegram.org/bot{token}/sendMessage'
payload = {
    'chat_id': chat_id,
    'text': '✅ 加密货币监控系统已连接',
    'parse_mode': 'HTML'
}
try:
    resp = requests.post(url, json=payload, timeout=10)
    if resp.status_code == 200:
        print('✅ Telegram 推送测试成功')
    else:
        print(f'❌ 推送失败: {resp.text}')
except Exception as e:
    print(f'❌ 推送失败: {e}')
"
    else
        echo "跳过 Telegram 配置"
    fi
}

# 主循环
while true; do
    show_menu
    read choice
    
    case $choice in
        1) start_all_monitor ;;
        2) start_meme_monitor ;;
        3) start_all ;;
        4) stop_all ;;
        5) show_status ;;
        6) show_logs ;;
        7) test_api ;;
        8) setup_telegram ;;
        0) echo "退出"; exit 0 ;;
        *) echo "无效选择" ;;
    esac
    
    echo ""
    echo "按 Enter 继续..."
    read
done
