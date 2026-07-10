#!/usr/bin/env python3
"""
HarmonyOS 响铃时振动管理脚本（CLI 调度器）

API: settings_api.query_ring_vibration / set_ring_vibration

用法:
  python ring_vibration_manager.py --mode query
  python ring_vibration_manager.py --mode on
  python ring_vibration_manager.py --mode off
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_ring_vibration, set_ring_vibration


def main():
    print("=" * 55)
    print("  HarmonyOS 响铃时振动管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 响铃时振动管理')
    parser.add_argument('--mode', required=True, choices=['query', 'on', 'off'])
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_ring_vibration()
        print("\n" + "-" * 55)
        if status is None:
            print("  >>> 未找到「响铃时振动」入口 <<<")
        else:
            state = '开启' if status == 'on' else '关闭' if status == 'off' else '未知'
            print(f"  响铃时振动: {state}")
        print("-" * 55)
    else:
        desired = 'on' if args.mode == 'on' else 'off'
        success, new_status = set_ring_vibration(desired)
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「响铃时振动」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭' if new_status == 'off' else '未知'
            action = '开启' if desired == 'on' else '关闭'
            if success:
                print(f"  响铃时振动: 已{action} ({state})")
            else:
                print(f"  响铃时振动: 操作失败 (当前: {state})")
        print("-" * 55)


if __name__ == '__main__':
    main()
