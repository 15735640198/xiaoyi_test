#!/usr/bin/env python3
"""
HarmonyOS 应用流量使用量查询脚本（CLI 调度器）

API: settings_api.query_app_data_usage

用法:
  # 查询最近30天流量（默认）
  python app_data_usage_manager.py --app 应用市场

  # 查询最近24小时流量
  python app_data_usage_manager.py --app 应用市场 --period 24h
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_app_data_usage


def main():
    print("=" * 55)
    print("  HarmonyOS 应用流量使用量查询")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 应用流量使用量查询')
    parser.add_argument('--app', required=True, help='应用名称（如 应用市场）')
    parser.add_argument('--period', default='30d', choices=['30d', '24h'],
                        help='时间周期: 30d(最近30天) 或 24h(最近24小时)')
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")
    print(f"  应用: {args.app}")
    print(f"  周期: {'最近30天' if args.period == '30d' else '最近24小时'}")

    result = query_app_data_usage(args.app, args.period)

    print("\n" + "-" * 55)
    if result is None:
        print(f"  >>> 未找到应用「{args.app}」的流量数据 <<<")
    else:
        usage = result.get('usage', '未知')
        period_label = result.get('period', '未知')
        print(f"  应用: {result.get('app', args.app)}")
        print(f"  周期: {period_label}")
        print(f"  已使用: {usage}")
    print("-" * 55)


if __name__ == '__main__':
    main()
