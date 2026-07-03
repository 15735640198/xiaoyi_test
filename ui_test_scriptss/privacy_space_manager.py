#!/usr/bin/env python3
"""
HarmonyOS 隐私空间管理脚本（CLI 调度器）

API: settings_api.query_privacy_space / set_privacy_space

用法:
  python privacy_space_manager.py --mode query                                          # 查询隐私空间状态
  python privacy_space_manager.py --mode setup --main-pwd 233333 --space-pwd 244444     # 开启隐私空间
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_privacy_space, set_privacy_space


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 隐私空间管理')
    parser.add_argument('--mode', required=True,
                        choices=['query', 'setup'],
                        help='query(查询状态) / setup(开启隐私空间)')
    parser.add_argument('--main-pwd', default=None,
                        help='主空间锁屏密码（mode=setup 时必须）')
    parser.add_argument('--space-pwd', default=None,
                        help='隐私空间密码，必须与主空间密码不同（mode=setup 时必须）')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 隐私空间管理")
    print("=" * 55)

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
    elif args.mode == 'setup':
        if not args.main_pwd or not args.space_pwd:
            print("\n  >>> 错误: mode=setup 需要 --main-pwd 和 --space-pwd 参数 <<<")
            sys.exit(1)
        success, msg = set_privacy_space(args.main_pwd, args.space_pwd)
        if success:
            print(f"\n  >>> {msg} <<<")
        else:
            print(f"\n  >>> {msg} <<<")


if __name__ == '__main__':
    main()
