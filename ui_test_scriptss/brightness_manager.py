#!/usr/bin/env python3
"""
HarmonyOS 屏幕亮度查询脚本（CLI 调度器）

API: settings_api.query_brightness

用法:
  python brightness_manager.py --mode query
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_brightness


def main():
    print("=" * 55)
    print("  HarmonyOS 屏幕亮度查询")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 屏幕亮度查询')
    parser.add_argument('--mode', required=True,
                        choices=['query'],
                        help='query(查询亮度百分比)')
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        percent = query_brightness()
        if percent is not None:
            print(f"\n  >>> 屏幕亮度: {percent}% <<<")
        else:
            print("\n  >>> 查询失败 <<<")


if __name__ == '__main__':
    main()
