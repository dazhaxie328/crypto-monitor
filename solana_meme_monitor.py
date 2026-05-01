#!/usr/bin/env python3
"""
Solana Meme 币专项监控脚本
监控热门 Solana meme 币的链上异动
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
import os

# ============ Solana Meme 币配置 ============
SOLANA_MEME_CONFIG = {
    # 热门 Solana meme 币列表
    "watchlist": [
        "bonk",
        "dogwifhat",
        "official-trump",
        "pudgy-penguins",
        "fartcoin",
        "popcat",
        "goatseus-maximus",
        "pepe",
        "shiba-inu",
        "floki"
    ],
    
    # 异动阈值
    "price_alert_threshold": 3.0,      # 价格变动 > 3% 告警
    "volume_alert_threshold": 50.0,    # 交易量变动 > 50% 告警
    "whale_transaction": 100000,       # 大额交易阈值（美元）
    
    # 检查间隔
    "check_interval": 60,  # 1分钟
    
    # API
    "coingecko_api": "https://api.coingecko.com/api/v3",
    "solscan_api": "https://public-api.solscan.io",
    
    # 推送
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    
    # 存储
    "data_file": Path.home() / "crypto-monitor" / "solana_meme_data.json",
}


class SolanaMemeMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "SolanaMemeMonitor/1.0"
        })
        self.previous_data = {}
        self.load_data()
    
    def load_data(self):
        """加载历史数据"""
        if SOLANA_MEME_CONFIG["data_file"].exists():
            try:
                with open(SOLANA_MEME_CONFIG["data_file"], "r") as f:
                    self.previous_data = json.load(f)
            except:
                self.previous_data = {}
    
    def save_data(self):
        """保存数据"""
        try:
            with open(SOLANA_MEME_CONFIG["data_file"], "w") as f:
                json.dump(self.previous_data, f, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_meme_prices(self):
        """获取 meme 币价格"""
        ids = ",".join(SOLANA_MEME_CONFIG["watchlist"])
        url = f"{SOLANA_MEME_CONFIG['coingecko_api']}/simple/price"
        params = {
            "ids": ids,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"获取价格失败: {e}")
            return {}
    
    def get_meme_details(self):
        """获取 meme 币详细信息"""
        url = f"{SOLANA_MEME_CONFIG['coingecko_api']}/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": ",".join(SOLANA_MEME_CONFIG["watchlist"]),
            "order": "market_cap_desc",
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"获取详情失败: {e}")
            return []
    
    def detect_anomalies(self, current_data):
        """检测异动"""
        alerts = []
        
        for coin_id, data in current_data.items():
            prev = self.previous_data.get(coin_id, {})
            
            # 价格异动
            price_change = data.get("usd_24h_change", 0)
            if abs(price_change) >= SOLANA_MEME_CONFIG["price_alert_threshold"]:
                direction = "🟢 暴涨" if price_change > 0 else "🔴 暴跌"
                alerts.append({
                    "type": "price",
                    "coin": coin_id.upper(),
                    "message": f"{direction} {abs(price_change):.2f}%",
                    "severity": "high" if abs(price_change) >= 10 else "medium"
                })
            
            # 交易量异动
            current_vol = data.get("usd_24h_vol", 0)
            prev_vol = prev.get("volume", 0)
            if prev_vol > 0:
                vol_change = ((current_vol - prev_vol) / prev_vol) * 100
                if vol_change >= SOLANA_MEME_CONFIG["volume_alert_threshold"]:
                    alerts.append({
                        "type": "volume",
                        "coin": coin_id.upper(),
                        "message": f"📊 交易量暴增 {vol_change:.0f}%",
                        "severity": "high"
                    })
            
            # 更新历史数据
            self.previous_data[coin_id] = {
                "price": data.get("usd", 0),
                "volume": current_vol,
                "market_cap": data.get("usd_market_cap", 0),
                "timestamp": datetime.now().isoformat()
            }
        
        return alerts
    
    def send_telegram(self, message):
        """发送 Telegram 通知"""
        token = SOLANA_MEME_CONFIG["telegram_bot_token"]
        chat_id = SOLANA_MEME_CONFIG["telegram_chat_id"]
        
        if not token or not chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except:
            return False
    
    def format_alert(self, alerts):
        """格式化告警消息"""
        if not alerts:
            return None
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "🚨 <b>Solana Meme 币异动告警</b>",
            f"⏰ {now}",
            ""
        ]
        
        for alert in alerts:
            icon = "🔴" if alert["severity"] == "high" else "🟡"
            lines.append(f"{icon} <b>{alert['coin']}</b>")
            lines.append(f"   {alert['message']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def print_status(self, coins):
        """打印状态"""
        print("\n" + "=" * 70)
        print("🐸 Solana Meme 币实时监控")
        print("=" * 70)
        print(f"{'币种':<12} {'价格':<15} {'24h涨跌':<12} {'交易量':<15} {'市值':<15}")
        print("-" * 70)
        
        for coin in coins[:10]:
            symbol = coin.get("symbol", "").upper()
            price = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h", 0)
            volume = coin.get("total_volume", 0)
            mcap = coin.get("market_cap", 0)
            
            change_icon = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            
            print(f"{symbol:<12} ${price:<14.8f} {change_icon}{change:>8.2f}%  ${volume/1e6:>10.1f}M  ${mcap/1e6:>10.1f}M")
        
        print("=" * 70 + "\n")
    
    def run_once(self):
        """执行一次检查"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 检查 Solana Meme 币...")
        
        # 获取详细数据
        coins = self.get_meme_details()
        if not coins:
            print("获取数据失败")
            return
        
        # 获取价格数据用于异动检测
        price_data = self.get_meme_prices()
        
        # 检测异动
        alerts = self.detect_anomalies(price_data)
        
        if alerts:
            message = self.format_alert(alerts)
            print(message)
            self.send_telegram(message)
        else:
            print("✅ 未检测到异动")
        
        # 打印状态
        self.print_status(coins)
        
        # 保存数据
        self.save_data()
    
    def run(self):
        """持续运行"""
        print("🚀 Solana Meme 币监控启动")
        print(f"监控列表: {', '.join(SOLANA_MEME_CONFIG['watchlist'])}")
        print(f"检查间隔: {SOLANA_MEME_CONFIG['check_interval']} 秒")
        print("=" * 50)
        
        try:
            while True:
                self.run_once()
                time.sleep(SOLANA_MEME_CONFIG["check_interval"])
        except KeyboardInterrupt:
            print("\n监控已停止")
            self.save_data()


if __name__ == "__main__":
    monitor = SolanaMemeMonitor()
    monitor.run()
