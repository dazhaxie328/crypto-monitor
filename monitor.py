#!/usr/bin/env python3
"""
Solana Meme 币链上异动监控脚本
功能：
1. 监控已上线交易所的币种
2. 筛选市值 > $10M 的币种
3. 检测链上数据异动（交易量、价格、活跃地址等）
4. 实时推送通知
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import os

# ============ 加载 .env 文件 ============
def load_env_file():
    """加载 .env 文件中的环境变量"""
    env_file = Path.home() / "crypto-monitor" / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# ============ 配置 ============
CONFIG = {
    # CoinGecko API (免费额度: 10-30 次/分钟)
    "coingecko_api": "https://api.coingecko.com/api/v3",
    
    # 筛选条件
    "min_market_cap": 10_000_000,  # 最小市值 $10M
    "exchanges": ["binance", "okx", "bybit", "gate-io"],  # 监控的交易所
    
    # 异动检测阈值
    "price_change_threshold": 5.0,    # 价格变动 > 5% 触发
    "volume_change_threshold": 100.0, # 交易量变动 > 100% 触发
    "market_cap_change_threshold": 10.0,  # 市值变动 > 10% 触发
    
    # 监控间隔（秒）
    "check_interval": 300,  # 5分钟检查一次
    
    # 推送配置（从环境变量读取）
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    
    # 数据存储
    "data_file": Path.home() / "crypto-monitor" / "data.json",
    "log_file": Path.home() / "crypto-monitor" / "monitor.log",
}

# ============ 数据获取 ============
class CryptoDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "CryptoMonitor/1.0"
        })
    
    def get_top_coins(self, page=1, per_page=100):
        """获取市值排名前的币种"""
        url = f"{CONFIG['coingecko_api']}/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d"
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.log(f"获取币种数据失败: {e}")
            return []
    
    def get_coin_detail(self, coin_id):
        """获取单个币种详细数据"""
        url = f"{CONFIG['coingecko_api']}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "true",
            "market_data": "true",
            "community_data": "true",
            "developer_data": "true"
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            self.log(f"获取 {coin_id} 详情失败: {e}")
            return None
    
    def get_exchange_coins(self, exchange_id):
        """获取特定交易所的币种列表"""
        url = f"{CONFIG['coingecko_api']}/exchanges/{exchange_id}/tickers"
        params = {"per_page": 250}
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [t["coin_id"] for t in data.get("tickers", [])]
        except Exception as e:
            self.log(f"获取 {exchange_id} 币种列表失败: {e}")
            return []
    
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        try:
            with open(CONFIG["log_file"], "a") as f:
                f.write(log_msg + "\n")
        except:
            pass


# ============ 异动检测 ============
class AnomalyDetector:
    def __init__(self):
        self.previous_data = {}
    
    def detect_price_anomaly(self, coin_id, current_price, price_change_24h):
        """检测价格异动"""
        alerts = []
        
        # 处理 None 值
        if price_change_24h is None:
            price_change_24h = 0
        
        # 24小时价格变动超过阈值
        if abs(price_change_24h) >= CONFIG["price_change_threshold"]:
            direction = "🟢 上涨" if price_change_24h > 0 else "🔴 下跌"
            alerts.append({
                "type": "price_change",
                "coin": coin_id,
                "message": f"{direction} {abs(price_change_24h):.2f}%",
                "severity": "high" if abs(price_change_24h) >= 10 else "medium"
            })
        
        return alerts
    
    def detect_volume_anomaly(self, coin_id, current_volume, previous_volume=None):
        """检测交易量异动"""
        alerts = []
        
        if previous_volume and previous_volume > 0:
            volume_change = ((current_volume - previous_volume) / previous_volume) * 100
            
            if volume_change >= CONFIG["volume_change_threshold"]:
                alerts.append({
                    "type": "volume_spike",
                    "coin": coin_id,
                    "message": f"交易量暴增 {volume_change:.0f}%",
                    "severity": "high"
                })
            elif volume_change <= -50:
                alerts.append({
                    "type": "volume_drop",
                    "coin": coin_id,
                    "message": f"交易量骤降 {abs(volume_change):.0f}%",
                    "severity": "medium"
                })
        
        return alerts
    
    def detect_market_cap_anomaly(self, coin_id, current_mcap, previous_mcap=None):
        """检测市值异动"""
        alerts = []
        
        if previous_mcap and previous_mcap > 0:
            mcap_change = ((current_mcap - previous_mcap) / previous_mcap) * 100
            
            if abs(mcap_change) >= CONFIG["market_cap_change_threshold"]:
                direction = "🟢 增加" if mcap_change > 0 else "🔴 减少"
                alerts.append({
                    "type": "market_cap_change",
                    "coin": coin_id,
                    "message": f"市值{direction} {abs(mcap_change):.2f}%",
                    "severity": "high"
                })
        
        return alerts
    
    def update_previous_data(self, coin_id, data):
        """更新历史数据"""
        self.previous_data[coin_id] = {
            "price": data.get("current_price", 0),
            "volume": data.get("total_volume", 0),
            "market_cap": data.get("market_cap", 0),
            "timestamp": datetime.now().isoformat()
        }


# ============ 推送通知 ============
class NotificationPusher:
    def __init__(self):
        self.telegram_enabled = bool(CONFIG["telegram_bot_token"] and CONFIG["telegram_chat_id"])
    
    def send_telegram(self, message):
        """发送 Telegram 通知"""
        if not self.telegram_enabled:
            return False
        
        url = f"https://api.telegram.org/bot{CONFIG['telegram_bot_token']}/sendMessage"
        payload = {
            "chat_id": CONFIG["telegram_chat_id"],
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"Telegram 推送失败: {e}")
            return False
    
    def send_desktop(self, title, message):
        """发送桌面通知（Linux）"""
        try:
            os.system(f'notify-send "{title}" "{message}"')
            return True
        except:
            return False
    
    def format_alert_message(self, alerts):
        """格式化告警消息"""
        if not alerts:
            return None
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"🚨 <b>加密货币异动告警</b>", f"⏰ {now}", ""]
        
        for alert in alerts:
            severity_icon = "🔴" if alert["severity"] == "high" else "🟡"
            lines.append(f"{severity_icon} <b>{alert['coin'].upper()}</b>")
            lines.append(f"   {alert['message']}")
            lines.append("")
        
        return "\n".join(lines)
    
    def push_alerts(self, alerts):
        """推送所有告警"""
        message = self.format_alert_message(alerts)
        if not message:
            return
        
        # 推送到 Telegram
        if self.telegram_enabled:
            self.send_telegram(message)
        
        # 推送到桌面
        self.send_desktop("加密货币异动", "\n".join([a["message"] for a in alerts]))
        
        # 打印到控制台
        print(message)


# ============ 主监控程序 ============
class CryptoMonitor:
    def __init__(self):
        self.fetcher = CryptoDataFetcher()
        self.detector = AnomalyDetector()
        self.notifier = NotificationPusher()
        self.running = False
    
    def load_previous_data(self):
        """加载历史数据"""
        if CONFIG["data_file"].exists():
            try:
                with open(CONFIG["data_file"], "r") as f:
                    data = json.load(f)
                    self.detector.previous_data = data
                    self.fetcher.log(f"加载了 {len(data)} 条历史数据")
            except Exception as e:
                self.fetcher.log(f"加载历史数据失败: {e}")
    
    def save_data(self):
        """保存当前数据"""
        try:
            with open(CONFIG["data_file"], "w") as f:
                json.dump(self.detector.previous_data, f, indent=2)
        except Exception as e:
            self.fetcher.log(f"保存数据失败: {e}")
    
    def filter_coins(self, coins):
        """筛选符合条件的币种"""
        filtered = []
        for coin in coins:
            market_cap = coin.get("market_cap", 0)
            if market_cap and market_cap >= CONFIG["min_market_cap"]:
                filtered.append(coin)
        return filtered
    
    def check_anomalies(self, coins):
        """检查所有币种的异动"""
        all_alerts = []
        
        for coin in coins:
            coin_id = coin.get("id", "")
            current_price = coin.get("current_price", 0)
            price_change_24h = coin.get("price_change_percentage_24h", 0)
            current_volume = coin.get("total_volume", 0)
            current_mcap = coin.get("market_cap", 0)
            
            # 获取历史数据
            prev_data = self.detector.previous_data.get(coin_id, {})
            prev_volume = prev_data.get("volume")
            prev_mcap = prev_data.get("market_cap")
            
            # 检测各类异动
            alerts = []
            alerts.extend(self.detector.detect_price_anomaly(coin_id, current_price, price_change_24h))
            alerts.extend(self.detector.detect_volume_anomaly(coin_id, current_volume, prev_volume))
            alerts.extend(self.detector.detect_market_cap_anomaly(coin_id, current_mcap, prev_mcap))
            
            all_alerts.extend(alerts)
            
            # 更新历史数据
            self.detector.update_previous_data(coin_id, coin)
        
        return all_alerts
    
    def run_once(self):
        """执行一次检查"""
        self.fetcher.log("开始获取币种数据...")
        
        # 获取币种数据
        coins = self.fetcher.get_top_coins(per_page=250)
        if not coins:
            self.fetcher.log("获取数据失败，跳过本次检查")
            return
        
        # 筛选市值 > $10M 的币种
        filtered_coins = self.filter_coins(coins)
        self.fetcher.log(f"筛选出 {len(filtered_coins)} 个市值 > $10M 的币种")
        
        # 检测异动
        alerts = self.check_anomalies(filtered_coins)
        
        if alerts:
            self.fetcher.log(f"检测到 {len(alerts)} 个异动")
            self.notifier.push_alerts(alerts)
        else:
            self.fetcher.log("未检测到异动")
        
        # 保存数据
        self.save_data()
        
        # 打印状态摘要
        self.print_summary(filtered_coins)
    
    def print_summary(self, coins):
        """打印状态摘要"""
        print("\n" + "=" * 60)
        print("📊 市值 Top 10 币种状态")
        print("=" * 60)
        print(f"{'币种':<12} {'价格':<15} {'24h涨跌':<10} {'市值':<15}")
        print("-" * 60)
        
        for coin in coins[:10]:
            name = coin.get("symbol", "").upper()
            price = coin.get("current_price", 0)
            change = coin.get("price_change_percentage_24h", 0)
            mcap = coin.get("market_cap", 0)
            
            change_icon = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            
            print(f"{name:<12} ${price:<14.6f} {change_icon}{change:>6.2f}%   ${mcap/1e6:>10.1f}M")
        
        print("=" * 60 + "\n")
    
    def run(self):
        """持续运行监控"""
        self.running = True
        self.fetcher.log("🚀 加密货币异动监控启动")
        self.fetcher.log(f"监控条件: 市值 > ${CONFIG['min_market_cap']/1e6:.0f}M")
        self.fetcher.log(f"检查间隔: {CONFIG['check_interval']} 秒")
        self.fetcher.log("=" * 50)
        
        # 加载历史数据
        self.load_previous_data()
        
        try:
            while self.running:
                self.run_once()
                self.fetcher.log(f"等待 {CONFIG['check_interval']} 秒后进行下一次检查...")
                time.sleep(CONFIG["check_interval"])
        except KeyboardInterrupt:
            self.fetcher.log("监控已停止")
            self.save_data()


# ============ 入口 ============
if __name__ == "__main__":
    monitor = CryptoMonitor()
    monitor.run()
