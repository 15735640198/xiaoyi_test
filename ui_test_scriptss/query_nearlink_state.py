#!/usr/bin/env python3
"""
HarmonyOS 星闪开关状态查询脚本（CLI 调度器）

API: settings_api.query_nearlink

用法:
  python query_nearlink_state.py
"""

from hdc_utils import find_hdc, check_device
from settings_api import query_nearlink


def main():
    print("=" * 55)
    print("  HarmonyOS 星闪开关状态查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    status = query_nearlink()

    print("\n" + "-" * 55)
    if status == 'on':
        print("  >>> 星闪: 已开启 (ON) <<<")
    elif status == 'off':
        print("  >>> 星闪: 已关闭 (OFF) <<<")
    elif status and status.startswith('unknown'):
        print(f"  >>> 星闪: 状态未知 {status} <<<")
    elif status is None:
        print("  >>> 未找到「星闪」入口 <<<")
    else:
        print(f"  >>> 星闪: {status} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
