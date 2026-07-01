#!/usr/bin/env python3
"""
HarmonyOS 锁屏方式管理脚本（CLI 调度器）

API: settings_api.query_lock_screen_method

用法:
  python lockscreen_method_manager.py --mode query

注意: 设置锁屏密码（图案/PIN/密码）涉及安全验证，无法自动化。
      录入指纹/人脸需物理交互，同样无法自动化。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_lock_screen_method


def main():
    print("=" * 55)
    print("  HarmonyOS 锁屏方式管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 锁屏方式管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'set':
        print("\n" + "-" * 55)
        print("  设置锁屏密码（图案/PIN/密码）涉及安全验证，")
        print("  无法通过 uitest 自动化。")
        print("  录入指纹/人脸需物理交互（触摸传感器/摄像头），")
        print("  同样无法自动化。")
        print("\n  请手动操作: 设置 > 生物识别和密码")
        print("-" * 55)
        return

    result = query_lock_screen_method()

    print("\n" + "-" * 55)
    if result is None:
        print("  >>> 未找到「生物识别和密码」入口 <<<")
    else:
        face = result.get('face', 'unknown')
        if face == 'enrolled':
            print("  人脸识别: 已录入")
        elif face == 'not_enrolled':
            print("  人脸识别: 未录入")
        else:
            print("  人脸识别: 未知")

        fp = result.get('fingerprint', 'unknown')
        if fp == 'enrolled':
            print("  指纹:     已录入")
        elif fp == 'not_enrolled':
            print("  指纹:     未录入")
        else:
            print("  指纹:     未知")

        pwd = result.get('lock_password', 'unknown')
        if pwd == 'set':
            print("  锁屏密码: 已设置（因生物特征已录入）")
        else:
            print("  锁屏密码: 无法自动判断（需进入安全验证页面）")

        print("  密码类型: 无法自动查询（图案/PIN/密码需安全验证）")
    print("-" * 55)


if __name__ == '__main__':
    main()
