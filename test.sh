#!/bin/bash
# 测试单次检查

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/monitor.py"

# 创建测试脚本
cat > /tmp/test_monitor.py << 'EOF'
#!/usr/bin/env python3
"""测试监控功能"""

import sys
sys.path.insert(0, '/home/enovo/crypto-monitor')

from monitor import CryptoDataFetcher, AnomalyDetector

def test():
    print("测试 CoinGecko API 连接...")
    fetcher = CryptoDataFetcher()
    
    # 测试获取币种数据
    coins = fetcher.get_top_coins(per_page=10)
    if coins:
        print(f"✅ 成功获取 {len(coins)} 个币种数据")
        print("\nTop 5 币种:")
        for i, coin in enumerate(coins[:5], 1):
            print(f"{i}. {coin['symbol'].upper()} - ${coin.get('current_price', 0):.6f} - 市值: ${coin.get('market_cap', 0)/1e6:.1f}M")
    else:
        print("❌ 获取数据失败")
        return
    
    # 测试异动检测
    print("\n测试异动检测...")
    detector = AnomalyDetector()
    
    for coin in coins[:3]:
        alerts = detector.detect_price_anomaly(
            coin['id'],
            coin.get('current_price', 0),
            coin.get('price_change_percentage_24h', 0)
        )
        if alerts:
            print(f"⚠️  {coin['symbol'].upper()}: {alerts[0]['message']}")
        else:
            print(f"✅ {coin['symbol'].upper()}: 无异动")
    
    print("\n测试完成!")

if __name__ == "__main__":
    test()
EOF

python3 /tmp/test_monitor.py
