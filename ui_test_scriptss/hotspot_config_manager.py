#!/usr/bin/env python3
"""
HarmonyOS 热点配置管理脚本（CLI 调度器）

API: settings_api.query_hotspot_config / set_hotspot_name / set_hotspot_password

用法:
  python hotspot_config_manager.py --mode query
  python hotspot_config_manager.py --mode set --name MyHotspot
  python hotspot_config_manager.py --mode set --password abc12345
  python hotspot_config_manager.py --mode set --name MyHotspot --password abc12345

注意: 加密方式在 HarmonyOS 中固定为 WPA2-PSK，不可配置。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_hotspot_config, set_hotspot_name, set_hotspot_password


def main():
    print("=" * 55)
    print("  HarmonyOS 热点配置管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 热点配置管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    parser.add_argument('--name', default=None, help='热点名称')
    parser.add_argument('--password', default=None, help='热点密码')
    args = parser.parse_args()

    if args.mode == 'set' and not args.name and not args.password:
        parser.error('--mode set 需要至少指定 --name 或 --password')

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        result = query_hotspot_config()
        print("\n" + "-" * 55)
        if result is None:
            print("  >>> 未找到「个人热点」入口 <<<")
        else:
            print(f"  热点名称: {result.get('name', '未知')}")
            print(f"  密码:     {result.get('password', '未知')}")
            print(f"  加密方式: {result.get('encryption', '未知')}")
        print("-" * 55)
    else:
        if args.name:
            success, new_name = set_hotspot_name(args.name)
            print("\n" + "-" * 55)
            if success:
                print(f"  热点名称设置成功: {new_name}")
            else:
                print(f"  热点名称设置失败: {new_name}")
            print("-" * 55)

        if args.password:
            success, new_pwd = set_hotspot_password(args.password)
            print("\n" + "-" * 55)
            if success:
                print(f"  热点密码设置成功: {new_pwd}")
            else:
                print(f"  热点密码设置失败: {new_pwd}")
            print("-" * 55)

        if not args.name and not args.password:
            print("\n  加密方式在 HarmonyOS 中固定为 WPA2-PSK，不可配置。")


if __name__ == '__main__':
    main()
