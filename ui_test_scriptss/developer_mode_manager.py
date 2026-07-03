#!/usr/bin/env python3
"""
HarmonyOS 开发者模式管理脚本（CLI 调度器）

API: settings_api.query_developer_mode / set_developer_mode

用法:
  python developer_mode_manager.py --mode query
  python developer_mode_manager.py --mode on
  python developer_mode_manager.py --mode off
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_developer_mode, set_developer_mode


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 开发者模式管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query'],
                        help='on(开启) / off(关闭) / query(查询)')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 开发者模式管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_developer_mode()
        if status == 'on':
            print("\n  >>> 开发者模式: 已开启 (ON) <<<")
        else:
            print("\n  >>> 开发者模式: 未开启 (OFF) <<<")
    else:
        desired = args.mode
        success, new_status = set_developer_mode(desired)
        if success:
            if desired == 'on':
                print("\n  >>> 开发者模式已开启 <<<")
            else:
                print("\n  >>> 开发者模式已关闭 <<<")
        else:
            new_str = {'on': '已开启', 'off': '未开启'}.get(new_status, str(new_status))
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")


if __name__ == '__main__':
    main()
