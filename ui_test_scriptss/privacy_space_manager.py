#!/usr/bin/env python3
"""
HarmonyOS 隐私空间状态查询脚本（CLI 调度器）

API: settings_api.query_privacy_space

用法:
  python privacy_space_manager.py --mode query

注意: 仅支持查询隐私空间是否已设置。
      开启/关闭隐私空间需设置单独锁屏密码（安全认证），无法通过脚本自动化。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_privacy_space


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 隐私空间状态查询')
    parser.add_argument('--mode', required=True, choices=['query'],
                        help='query(查询隐私空间状态)')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 隐私空间状态查询")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_privacy_space()
        status_map = {
            'not_setup': '未设置',
            'setup': '已设置',
            'unknown': '未知',
        }
        status_str = status_map.get(status, str(status))
        print(f"\n  >>> 隐私空间: {status_str} <<<")
        if status == 'not_setup':
            print("  提示: 开启隐私空间需设置单独锁屏密码，请在 设置 > 隐私和安全 > 隐私空间 中手动开启")


if __name__ == '__main__':
    main()
