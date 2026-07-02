#!/usr/bin/env python3
"""
HarmonyOS WLAN 下自动下载开关管理（CLI 调度器）

API: settings_api.query_wlan_auto_download / set_wlan_auto_download

用法:
  python wlan_auto_download_manager.py --mode query
  python wlan_auto_download_manager.py --mode on
  python wlan_auto_download_manager.py --mode off
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import query_wlan_auto_download, set_wlan_auto_download


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS WLAN 下自动下载开关管理')
    parser.add_argument('--mode', required=True, choices=['on', 'off', 'query'],
                        help='query=查询, on=开启, off=关闭')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS WLAN 下自动下载开关管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_wlan_auto_download()
        print("\n" + "-" * 55)
        if status == 'on':
            print("  >>> WLAN 下自动下载: 已开启 (ON) <<<")
        elif status == 'off':
            print("  >>> WLAN 下自动下载: 已关闭 (OFF) <<<")
        elif status is None:
            print("  >>> 未找到「WLAN 下自动下载」入口 <<<")
        else:
            print(f"  >>> WLAN 下自动下载: 状态未知 {status} <<<")
        print("-" * 55)
    else:
        success, new_status = set_wlan_auto_download(args.mode)
        print("\n" + "-" * 55)
        if success:
            print(f"  >>> 操作成功: WLAN 下自动下载 → {new_status} <<<")
        else:
            print(f"  >>> 操作失败: 当前状态 {new_status} <<<")
        print("-" * 55)


if __name__ == '__main__':
    main()
