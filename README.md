# 加密货币异动监控系统

实时监控已上线交易所、市值大于 $10M 的币种，检测链上数据异动并推送通知。

## 功能特性

- ✅ 监控 CoinGecko 上所有币种
- ✅ 筛选市值 > $10M 的币种
- ✅ 检测价格异动（24h 涨跌 > 5%）
- ✅ 检测交易量异动（暴增 > 100%）
- ✅ 检测市值异动（变动 > 10%）
- ✅ **Solana Meme 币专项监控**
- ✅ Telegram 推送通知
- ✅ 桌面通知（Linux）
- ✅ 数据持久化存储
- ✅ 日志记录

## 快速开始

### 1. 安装依赖

```bash
pip3 install requests
```

### 2. 配置 Telegram 推送（可选）

运行管理脚本进行配置：

```bash
./manage.sh
# 选择 8. 配置 Telegram 推送
```

或手动编辑 `config.json`：

```json
{
    "telegram_bot_token": "你的 Bot Token",
    "telegram_chat_id": "你的 Chat ID"
}
```

### 3. 运行监控

```bash
# 交互式管理
./manage.sh

# 或直接启动
./start.sh                    # 全币种监控
./meme_service.sh start       # Solana Meme 监控
```

## 文件说明

```
crypto-monitor/
├── monitor.py              # 全币种监控主脚本
├── solana_meme_monitor.py  # Solana Meme 币专项监控
├── config.json             # 配置文件
├── manage.sh               # 交互式管理脚本
├── start.sh                # 全币种监控启动脚本
├── service.sh              # 全币种监控服务管理
├── meme_service.sh         # Solana Meme 监控服务管理
├── test.sh                 # 测试脚本
└── README.md               # 说明文档
```

## 监控币种

### 全币种监控
- 市值 > $10M 的所有币种
- 每 5 分钟检查一次

### Solana Meme 币监控
热门 Solana meme 币：
- BONK
- WIF (dogwifhat)
- TRUMP
- PENGU (Pudgy Penguins)
- FARTCOIN
- POPCAT
- GOAT
- PEPE
- SHIB
- FLOKI

## 告警规则

| 类型 | 阈值 | 严重程度 |
|------|------|----------|
| 价格异动 | 24h 涨跌 > 5% | 中 |
| 价格异动 | 24h 涨跌 > 10% | 高 |
| 交易量异动 | 暴增 > 100% | 高 |
| 交易量异动 | 骤降 > 50% | 中 |
| 市值异动 | 变动 > 10% | 高 |

## 配置说明

编辑 `config.json` 修改配置：

```json
{
    "min_market_cap": 10000000,        // 最小市值（美元）
    "price_change_threshold": 5.0,     // 价格变动阈值（%）
    "volume_change_threshold": 100.0,  // 交易量变动阈值（%）
    "market_cap_change_threshold": 10.0, // 市值变动阈值（%）
    "check_interval": 300              // 检查间隔（秒）
}
```

## 数据存储

监控数据存储在 `~/.crypto-monitor/` 目录：

- `data.json` - 全币种历史数据
- `solana_meme_data.json` - Solana Meme 币数据
- `monitor.log` - 全币种监控日志
- `solana_meme.log` - Solana Meme 监控日志

## Telegram 配置

### 获取 Bot Token

1. 在 Telegram 搜索 @BotFather
2. 发送 `/newbot`
3. 按提示创建 Bot
4. 获取 Bot Token

### 获取 Chat ID

1. 搜索你创建的 Bot
2. 发送任意消息
3. 访问：`https://api.telegram.org/bot<你的Token>/getUpdates`
4. 找到 `chat.id` 字段

## 服务管理

```bash
# 全币种监控
./service.sh start    # 启动
./service.sh stop     # 停止
./service.sh status   # 状态
./service.sh log      # 查看日志

# Solana Meme 监控
./meme_service.sh start    # 启动
./meme_service.sh stop     # 停止
./meme_service.sh status   # 状态
./meme_service.sh log      # 查看日志
```

## 后台运行

```bash
# 启动全部监控
./manage.sh
# 选择 3. 启动全部监控

# 或手动启动
nohup ./start.sh > /dev/null 2>&1 &
nohup python3 solana_meme_monitor.py > /dev/null 2>&1 &
```

## 注意事项

1. CoinGecko 免费 API 有频率限制（10-30 次/分钟）
2. 默认每 5 分钟检查一次，可根据需要调整
3. Telegram 推送需要配置 Bot Token 和 Chat ID
4. 首次运行无历史数据，不会触发异动告警
5. 数据会持续积累，检测会越来越准确

## 扩展功能

如需添加更多功能，可以：

1. 添加更多数据源（如 CoinMarketCap、DeFiLlama）
2. 添加更多异动检测规则
3. 添加邮件/钉钉/企业微信推送
4. 添加 Web 界面展示数据
5. 添加历史数据分析和图表

## License

MIT
