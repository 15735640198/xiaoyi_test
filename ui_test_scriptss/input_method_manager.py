#!/usr/bin/env python3
"""
HarmonyOS 输入法管理（CLI 调度器）

API: settings_api.query_default_input_method

用法:
  python input_method_manager.py --mode query
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import query_default_input_method


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 输入法管理')
    parser.add_argument('--mode', required=True, choices=['query'],
                        help='query=查询默认输入法')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 输入法管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    print("\n" + "-" * 55)
    if args.mode == 'query':
        im = query_default_input_method()
        if im:
            print(f"  >>> 默认输入法: {im} <<<")
        else:
            print("  >>> 未找到输入法设置入口 <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
