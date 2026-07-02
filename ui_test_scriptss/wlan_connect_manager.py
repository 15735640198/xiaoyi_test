#!/usr/bin/env python3
"""
HarmonyOS WiFi 连接管理（CLI 调度器）

API: settings_api.connect_wlan

用法:
  python wlan_connect_manager.py --ssid "WiFi名称" --password "密码"
  python wlan_connect_manager.py --ssid "开放WiFi"
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import connect_wlan


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS WiFi 连接管理')
    parser.add_argument('--ssid', required=True, help='WiFi 名称')
    parser.add_argument('--password', default=None, help='WiFi 密码 (开放网络可不填)')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS WiFi 连接管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")
    print(f"  目标WiFi: {args.ssid}")

    success, message = connect_wlan(args.ssid, args.password)

    print("\n" + "-" * 55)
    if success:
        print(f"  >>> 连接成功: {args.ssid} ({message}) <<<")
    else:
        print(f"  >>> 连接失败: {message} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
