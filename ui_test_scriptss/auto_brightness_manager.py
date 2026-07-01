#!/usr/bin/env python3
"""
HarmonyOS 自动调节亮度管理脚本（CLI 调度器）

API: settings_api.query_auto_brightness / set_auto_brightness

用法:
  python auto_brightness_manager.py --mode query
  python auto_brightness_manager.py --mode on
  python auto_brightness_manager.py --mode off
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_auto_brightness, set_auto_brightness


def main():
    print("=" * 55)
    print("  HarmonyOS 自动调节亮度管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 自动调节亮度管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query'],
                        help='on(打开) / off(关闭) / query(查询)')
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_auto_brightness()
        status_str = {'on': '已开启', 'off': '已关闭'}.get(status, str(status))
        print(f"\n  >>> 自动调节亮度: {status_str} <<<")
    else:
        desired = args.mode
        success, new_status = set_auto_brightness(desired)
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> 自动调节亮度已{'开启' if desired == 'on' else '关闭'} <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")


if __name__ == '__main__':
    main()
