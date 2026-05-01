#!/usr/bin/env python3
"""
合约监控脚本
监控特定合约的交易、事件和异动
"""

import requests
import json
import time
import os
from datetime import datetime
from pathlib import Path

# 加载 .env 文件
def load_env_file():
    env_file = Path.home() / "crypto-monitor" / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

load_env_file()

# 加载配置
CONFIG_FILE = Path.home() / "crypto-monitor" / "config.json"
CONFIG = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        CONFIG = json.load(f)

# API 配置
SOLSCAN_API = "https://public-api.solscan.io"
ETHERSCAN_API = "https://api.etherscan.io/api"
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY", "")

# 合约地址
CONTRACTS = CONFIG.get("contracts", {})


class ContractMonitor:
    """合约监控类"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "ContractMonitor/1.0"
        })
        self.previous_data = {}
        self.load_data()
    
    def load_data(self):
        """加载历史数据"""
        data_file = Path.home() / "crypto-monitor" / "contract_data.json"
        if data_file.exists():
            try:
                with open(data_file, "r") as f:
                    self.previous_data = json.load(f)
            except:
                self.previous_data = {}
    
    def save_data(self):
        """保存数据"""
        data_file = Path.home() / "crypto-monitor" / "contract_data.json"
        try:
            with open(data_file, "w") as f:
                json.dump(self.previous_data, f, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    # ========== Solana 合约监控 ==========
    
    def get_solana_token_info(self, contract_address):
        """获取 Solana 代币信息"""
        url = f"{SOLSCAN_API}/token/meta?token={contract_address}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"获取 Solana 代币信息失败: {e}")
        return None
    
    def get_solana_token_transfers(self, contract_address, limit=10):
        """获取 Solana 代币转账记录"""
        url = f"{SOLSCAN_API}/token/transfer?token={contract_address}&limit={limit}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception as e:
            print(f"获取 Solana 转账记录失败: {e}")
        return []
    
    def get_solana_token_holders(self, contract_address, limit=10):
        """获取 Solana 代币持有者"""
        url = f"{SOLSCAN_API}/token/holders?token={contract_address}&limit={limit}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("data", [])
        except Exception as e:
            print(f"获取 Solana 持有者失败: {e}")
        return []
    
    # ========== Ethereum 合约监控 ==========
    
    def get_eth_token_transfers(self, contract_address, limit=10):
        """获取 Ethereum 代币转账记录"""
        url = ETHERSCAN_API
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": ETHERSCAN_KEY
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1":
                    return data.get("result", [])
        except Exception as e:
            print(f"获取 Ethereum 转账记录失败: {e}")
        return []
    
    def get_eth_contract_events(self, contract_address, topic, limit=10):
        """获取 Ethereum 合约事件"""
        url = ETHERSCAN_API
        params = {
            "module": "logs",
            "action": "getLogs",
            "address": contract_address,
            "topic0": topic,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": ETHERSCAN_KEY
        }
        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1":
                    return data.get("result", [])
        except Exception as e:
            print(f"获取 Ethereum 事件失败: {e}")
        return []
    
    # ========== 异动检测 ==========
    
    def detect_large_transfers(self, transfers, threshold=100000):
        """检测大额转账"""
        alerts = []
        for transfer in transfers:
            amount = float(transfer.get("amount", 0))
            if amount >= threshold:
                alerts.append({
                    "type": "large_transfer",
                    "amount": amount,
                    "from": transfer.get("from", "N/A"),
                    "to": transfer.get("to", "N/A"),
                    "token": transfer.get("token", "N/A")
                })
        return alerts
    
    def detect_holder_changes(self, current_holders, previous_holders):
        """检测持有者变化"""
        alerts = []
        current_map = {h["address"]: h["amount"] for h in current_holders}
        previous_map = {h["address"]: h["amount"] for h in previous_holders}
        
        for address, amount in current_map.items():
            prev_amount = previous_map.get(address, 0)
            if prev_amount > 0:
                change = ((amount - prev_amount) / prev_amount) * 100
                if abs(change) >= 10:  # 变化超过 10%
                    alerts.append({
                        "type": "holder_change",
                        "address": address,
                        "change": change,
                        "current": amount,
                        "previous": prev_amount
                    })
        return alerts
    
    # ========== 监控主逻辑 ==========
    
    def monitor_solana_contracts(self):
        """监控 Solana 合约"""
        solana_contracts = CONTRACTS.get("solana", {})
        all_alerts = []
        
        for token_name, contract_address in solana_contracts.items():
            print(f"监控 Solana 合约: {token_name} ({contract_address})")
            
            # 获取代币信息
            token_info = self.get_solana_token_info(contract_address)
            if token_info:
                print(f"  代币名称: {token_info.get('name', 'N/A')}")
                print(f"  符号: {token_info.get('symbol', 'N/A')}")
                print(f"  价格: ${token_info.get('price', 'N/A')}")
            
            # 获取转账记录
            transfers = self.get_solana_token_transfers(contract_address, limit=20)
            if transfers:
                print(f"  最近转账: {len(transfers)} 笔")
                
                # 检测大额转账
                large_transfers = self.detect_large_transfers(transfers, threshold=10000)
                all_alerts.extend(large_transfers)
            
            # 获取持有者
            holders = self.get_solana_token_holders(contract_address, limit=10)
            if holders:
                print(f"  Top 持有者: {len(holders)} 个")
            
            print()
        
        return all_alerts
    
    def monitor_ethereum_contracts(self):
        """监控 Ethereum 合约"""
        eth_contracts = CONTRACTS.get("ethereum", {})
        all_alerts = []
        
        for token_name, contract_address in eth_contracts.items():
            print(f"监控 Ethereum 合约: {token_name} ({contract_address})")
            
            # 获取转账记录
            transfers = self.get_eth_token_transfers(contract_address, limit=20)
            if transfers:
                print(f"  最近转账: {len(transfers)} 笔")
                
                # 检测大额转账
                for transfer in transfers:
                    value = int(transfer.get("value", 0))
                    decimals = int(transfer.get("tokenDecimal", 18))
                    amount = value / (10 ** decimals)
                    
                    if amount >= 10000:  # 大额转账阈值
                        all_alerts.append({
                            "type": "large_transfer",
                            "token": token_name,
                            "amount": amount,
                            "from": transfer.get("from", "N/A"),
                            "to": transfer.get("to", "N/A"),
                            "hash": transfer.get("hash", "N/A")
                        })
            
            print()
        
        return all_alerts
    
    # ========== 主监控循环 ==========
    
    def run_once(self):
        """执行一次监控"""
        print("=" * 60)
        print(f"合约监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_alerts = []
        
        # 监控 Solana 合约
        solana_alerts = self.monitor_solana_contracts()
        all_alerts.extend(solana_alerts)
        
        # 监控 Ethereum 合约
        eth_alerts = self.monitor_ethereum_contracts()
        all_alerts.extend(eth_alerts)
        
        # 发送告警
        if all_alerts:
            self.send_alerts(all_alerts)
        
        # 保存数据
        self.save_data()
        
        print("=" * 60)
        print(f"监控完成，发现 {len(all_alerts)} 个异动")
        print("=" * 60)
        print()
        
        return all_alerts
    
    def send_alerts(self, alerts):
        """发送告警"""
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        if not token or not chat_id:
            print("Telegram 未配置，跳过推送")
            return
        
        message = "🚨 <b>合约异动告警</b>\n\n"
        for alert in alerts:
            if alert["type"] == "large_transfer":
                message += f"💰 <b>大额转账</b>\n"
                message += f"   代币: {alert.get('token', 'N/A')}\n"
                message += f"   金额: {alert.get('amount', 0):,.2f}\n"
                message += f"   从: {alert.get('from', 'N/A')[:20]}...\n"
                message += f"   到: {alert.get('to', 'N/A')[:20]}...\n\n"
            elif alert["type"] == "holder_change":
                message += f"📊 <b>持有者变化</b>\n"
                message += f"   地址: {alert.get('address', 'N/A')[:20]}...\n"
                message += f"   变化: {alert.get('change', 0):+.2f}%\n\n"
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                print("✅ 告警已推送")
            else:
                print(f"❌ 推送失败: {resp.text}")
        except Exception as e:
            print(f"❌ 推送失败: {e}")
    
    def run(self, interval=300):
        """持续运行监控"""
        print("🚀 合约监控启动")
        print(f"监控间隔: {interval} 秒")
        print(f"Solana 合约: {len(CONTRACTS.get('solana', {}))} 个")
        print(f"Ethereum 合约: {len(CONTRACTS.get('ethereum', {}))} 个")
        print()
        
        try:
            while True:
                self.run_once()
                print(f"等待 {interval} 秒后进行下一次检查...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n监控已停止")
            self.save_data()


# ========== 主程序 ==========

if __name__ == "__main__":
    monitor = ContractMonitor()
    monitor.run()
