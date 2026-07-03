#!/usr/bin/env python3
"""
HarmonyOS 指纹与锁屏密码管理脚本（CLI 调度器）

API: settings_api.query_fingerprint / set_lock_screen_password

用法:
  python fingerprint_manager.py --mode query                              # 查询指纹录入状态
  python fingerprint_manager.py --mode set-password --password 233333     # 设置锁屏密码

注意: 录入指纹需物理指纹传感器交互，无法通过脚本自动化。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_fingerprint, set_lock_screen_password


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 指纹与锁屏密码管理')
    parser.add_argument('--mode', required=True,
                        choices=['query', 'set-password'],
                        help='query(查询指纹状态) / set-password(设置锁屏密码)')
    parser.add_argument('--password', default=None,
                        help='锁屏密码（mode=set-password 时必须）')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 指纹与锁屏密码管理")
    print("=" * 55)

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
            print("  提示: 录入指纹需物理传感器交互，请在设置 > 生物识别和密码 > 指纹中手动录入")
    elif args.mode == 'set-password':
        if not args.password:
            print("\n  >>> 错误: mode=set-password 需要指定 --password 参数 <<<")
            sys.exit(1)
        success, msg = set_lock_screen_password(args.password)
        if success:
            print(f"\n  >>> {msg} <<<")
        else:
            print(f"\n  >>> {msg} <<<")


if __name__ == '__main__':
    main()
