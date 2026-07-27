#!/usr/bin/env python3
"""
HarmonyOS 应用联网管理脚本（CLI 调度器）

API: settings_api.query_app_network_access / set_app_network_access

用法:
  # 查询应用联网状态
  python app_network_manager.py --mode query --app 备忘录

  # 设置移动数据联网开关
  python app_network_manager.py --mode set --app 备忘录 --type mobile_data --value off
  python app_network_manager.py --mode set --app 备忘录 --type mobile_data --value on

  # 设置 WLAN 联网开关
  python app_network_manager.py --mode set --app 备忘录 --type wlan --value off
  python app_network_manager.py --mode set --app 备忘录 --type wlan --value on
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_app_network_access, set_app_network_access


def main():
    print("=" * 55)
    print("  HarmonyOS 应用联网管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 应用联网管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    parser.add_argument('--app', required=True, help='应用名称（如 备忘录）')
    parser.add_argument('--type', default=None, choices=['mobile_data', 'wlan'],
                        help='联网类型（set 模式必需）')
    parser.add_argument('--value', default=None, choices=['on', 'off'],
                        help='目标状态（set 模式必需）')
    args = parser.parse_args()

    if args.mode == 'set' and (not args.type or not args.value):
        parser.error('--mode set 需要 --type 和 --value')

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")
    print(f"  应用: {args.app}")

    if args.mode == 'query':
        result = query_app_network_access(args.app)
        print("\n" + "-" * 55)
        if result is None:
            print("  >>> 未找到「应用联网」入口 <<<")
        else:
            md = result.get('mobile_data', 'unknown')
            wlan = result.get('wlan', 'unknown')
            md_str = '开启' if md == 'on' else '关闭' if md == 'off' else '未知'
            wlan_str = '开启' if wlan == 'on' else '关闭' if wlan == 'off' else '未知'
            print(f"  移动数据: {md_str}")
            print(f"  WLAN:     {wlan_str}")
        print("-" * 55)
    else:
        type_label = '移动数据' if args.type == 'mobile_data' else 'WLAN'
        success, new_status = set_app_network_access(args.app, args.type, args.value)
        print("\n" + "-" * 55)
        if new_status is None:
            print(f"  >>> 未找到应用「{args.app}」或「应用联网」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭' if new_status == 'off' else '未知'
            action = '开启' if args.value == 'on' else '关闭'
            if success:
                print(f"  {args.app} - {type_label}: 已{action} ({state})")
            else:
                print(f"  {args.app} - {type_label}: 操作失败 (当前: {state})")
        print("-" * 55)


if __name__ == '__main__':
    main()
