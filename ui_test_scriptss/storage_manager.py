#!/usr/bin/env python3
"""
HarmonyOS 存储空间查询脚本（CLI 调度器）

API: settings_api.query_storage

用法:
  python storage_manager.py --mode query
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_storage


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 存储空间查询')
    parser.add_argument('--mode', required=True, choices=['query'],
                        help='query(查询存储使用情况)')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 存储空间查询")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        result = query_storage()
        if not result:
            print("\n  >>> 查询失败 <<<")
            return

        print(f"\n  使用率: {result['usage_rate'] or '未知'}")
        print(f"  已使用: {result['used'] or '未知'}")
        print(f"  总大小: {result['total'] or '未知'}")

        if result['apps']:
            print(f"\n  应用占用 TOP {len(result['apps'])}:")
            for i, app in enumerate(result['apps'], 1):
                print(f"    {i}. {app['name']}: {app['size']}")
        else:
            print("\n  应用占用: 无数据")


if __name__ == '__main__':
    main()
