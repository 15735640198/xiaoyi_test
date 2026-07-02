#!/usr/bin/env python3
"""
HarmonyOS SIM 卡管理（CLI 调度器）

API: settings_api.query_sim_status / query_sim_carrier / query_sim_enabled / set_sim_enabled

用法:
  python sim_card_manager.py --mode status          # 双卡状态 + 运营商
  python sim_card_manager.py --mode carrier          # 运营商归属
  python sim_card_manager.py --mode enabled --card "卡 1"   # 查询使用状态
  python sim_card_manager.py --mode on --card "卡 1"        # 启用
  python sim_card_manager.py --mode off --card "卡 2"       # 禁用
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import (
    query_sim_status, query_sim_carrier,
    query_sim_enabled, set_sim_enabled,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS SIM 卡管理')
    parser.add_argument('--mode', required=True,
                        choices=['status', 'carrier', 'enabled', 'on', 'off'],
                        help='status=双卡状态, carrier=运营商, enabled=查询使用状态, on/off=启用/禁用')
    parser.add_argument('--card', default='卡 1', help='SIM 卡 (卡 1/卡 2), 默认卡 1')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS SIM 卡管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    print("\n" + "-" * 55)

    if args.mode == 'status':
        result = query_sim_status()
        if not result:
            print("  >>> 未找到 SIM 卡管理入口 <<<")
        else:
            for card, val in result.items():
                print(f"  >>> {card}: {val} <<<")
    elif args.mode == 'carrier':
        result = query_sim_carrier()
        if not result:
            print("  >>> 未找到 SIM 卡管理入口 <<<")
        else:
            for card, val in result.items():
                if val:
                    print(f"  >>> {card} 运营商: {val} <<<")
                else:
                    print(f"  >>> {card}: 未插卡 <<<")
    elif args.mode == 'enabled':
        status = query_sim_enabled(args.card)
        if status == 'on':
            print(f"  >>> {args.card}: 已启用 (ON) <<<")
        elif status == 'off':
            print(f"  >>> {args.card}: 已禁用 (OFF) <<<")
        elif status is None:
            print(f"  >>> 未找到 {args.card} 入口 <<<")
        else:
            print(f"  >>> {args.card}: 状态未知 {status} <<<")
    elif args.mode in ('on', 'off'):
        success, new_status = set_sim_enabled(args.card, args.mode)
        if success:
            print(f"  >>> 操作成功: {args.card} → {new_status} <<<")
        else:
            print(f"  >>> 操作失败: {args.card} 当前状态 {new_status} <<<")

    print("-" * 55)


if __name__ == '__main__':
    main()
