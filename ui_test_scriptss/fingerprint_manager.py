#!/usr/bin/env python3
"""
HarmonyOS 指纹状态查询脚本（CLI 调度器）

API: settings_api.query_fingerprint

用法:
  python fingerprint_manager.py --mode query

注意: 仅支持查询指纹录入状态。
      录入指纹需先设置锁屏密码 + 物理指纹传感器交互，无法通过脚本自动化。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_fingerprint


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 指纹状态查询')
    parser.add_argument('--mode', required=True, choices=['query'],
                        help='query(查询指纹录入状态)')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 指纹状态查询")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_fingerprint()
        status_map = {
            'enrolled': '已录入',
            'not_enrolled': '未录入',
            'unknown': '未知',
        }
        status_str = status_map.get(status, str(status))
        print(f"\n  >>> 指纹状态: {status_str} <<<")
        if status == 'not_enrolled':
            print("  提示: 录入指纹需先设置锁屏密码，然后在设置 > 生物识别和密码 > 指纹中手动录入")


if __name__ == '__main__':
    main()
