#!/usr/bin/env python3
"""
HarmonyOS 个人热点状态查询脚本（CLI 调度器）

API: settings_api.query_personal_hotspot

用法:
  python query_personal_hotspot_state.py
"""

from hdc_utils import find_hdc, check_device
from settings_api import query_personal_hotspot


def main():
    print("=" * 55)
    print("  HarmonyOS 个人热点开关状态查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    status = query_personal_hotspot()

    print("\n" + "-" * 55)
    if status == 'on':
        print("  >>> 个人热点: 已开启 (ON) <<<")
    elif status == 'off':
        print("  >>> 个人热点: 已关闭 (OFF) <<<")
    else:
        print(f"  >>> 个人热点: 状态未知 ({status}) <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
