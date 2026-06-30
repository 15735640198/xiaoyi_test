#!/usr/bin/env python3
"""
HarmonyOS 放大手势状态查询脚本（CLI 调度器）

API: settings_api.query_zoom_gesture

用法:
  python query_zoom_gesture_state.py
"""

from hdc_utils import find_hdc, check_device
from settings_api import query_zoom_gesture


def main():
    print("=" * 55)
    print("  HarmonyOS 放大手势开关状态查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    status = query_zoom_gesture()

    print("\n" + "-" * 55)
    if status == 'on':
        print("  >>> 放大手势: 已开启 (ON) <<<")
    elif status == 'off':
        print("  >>> 放大手势: 已关闭 (OFF) <<<")
    elif status and status.startswith('unknown'):
        print(f"  >>> 放大手势: 状态未知 {status} <<<")
    elif status is None:
        print("  >>> 未找到「放大手势」入口 <<<")
    else:
        print(f"  >>> 放大手势: {status} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
