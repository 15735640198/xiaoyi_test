#!/usr/bin/env python3
"""
HarmonyOS 字体大小和字体粗细管理脚本（CLI 调度器）

API: settings_api.query_font_size / set_font_size
     settings_api.query_font_weight / set_font_weight

用法:
  python font_size_manager.py --mode query
  python font_size_manager.py --mode set-size --value 标准
  python font_size_manager.py --mode set-weight --value 最粗
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_font_size, set_font_size,
    query_font_weight, set_font_weight,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 字体大小和字体粗细管理')
    parser.add_argument('--mode', required=True,
                        choices=['query', 'set-size', 'set-weight'],
                        help='query(查询) / set-size(设置字体大小) / set-weight(设置字体粗细)')
    parser.add_argument('--value', default=None,
                        help='set-size: 小/标准/大/超大  set-weight: 最细/标准/最粗')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 字体大小和字体粗细管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        size = query_font_size()
        weight = query_font_weight()
        print(f"\n  >>> 字体大小: {size} <<<")
        print(f"  >>> 字体粗细: {weight} <<<")

    elif args.mode == 'set-size':
        if not args.value:
            print("\n  >>> set-size 模式需要 --value (小/标准/大/超大) <<<")
            return
        success, new_val = set_font_size(args.value)
        if success:
            print(f"\n  >>> 字体大小已设置为: {new_val} <<<")
        else:
            print(f"\n  >>> 设置失败，当前字体大小: {new_val} <<<")

    elif args.mode == 'set-weight':
        if not args.value:
            print("\n  >>> set-weight 模式需要 --value (最细/标准/最粗) <<<")
            return
        success, new_val = set_font_weight(args.value)
        if success:
            print(f"\n  >>> 字体粗细已设置为: {new_val} <<<")
        else:
            print(f"\n  >>> 设置失败，当前字体粗细: {new_val} <<<")


if __name__ == '__main__':
    main()
