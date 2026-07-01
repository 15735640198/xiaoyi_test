#!/usr/bin/env python3
"""
HarmonyOS 开发者模式状态查询脚本（CLI 调度器）

API: settings_api.query_developer_mode

用法:
  python query_developer_mode_state.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_developer_mode


def main():
    print("=" * 55)
    print("  HarmonyOS 开发者模式状态查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    status = query_developer_mode()

    print("\n" + "-" * 55)
    if status == 'on':
        print("  >>> 开发者模式: 已开启 (ON) <<<")
    else:
        print("  >>> 开发者模式: 未开启 (OFF) <<<")
        print("  提示: 在 设置 > 系统 > 关于手机 中连续点击版本号 7 次可开启")
    print("-" * 55)


if __name__ == '__main__':
    main()
