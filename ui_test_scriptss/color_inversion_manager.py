#!/usr/bin/env python3
"""
HarmonyOS 颜色反转管理脚本（CLI 调度器）

API: settings_api.query_color_inversion / set_color_inversion

用法:
  python color_inversion_manager.py --mode query
  python color_inversion_manager.py --mode on
  python color_inversion_manager.py --mode off
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_color_inversion, set_color_inversion


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 颜色反转管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query'],
                        help='on(打开) / off(关闭) / query(查询)')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 颜色反转管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_color_inversion()
        status_str = {'on': '已开启', 'off': '已关闭'}.get(status, str(status))
        print(f"\n  >>> 颜色反转: {status_str} <<<")
    else:
        success, new_status = set_color_inversion(args.mode)
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> 颜色反转已{'开启' if args.mode == 'on' else '关闭'} <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")


if __name__ == '__main__':
    main()
