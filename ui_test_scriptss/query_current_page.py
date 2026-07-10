#!/usr/bin/env python3
"""
HarmonyOS 查询当前设置页面标题脚本（CLI 调度器）

API: settings_api.query_current_settings_page

用法:
  python query_current_page.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_current_settings_page


def main():
    print("=" * 55)
    print("  HarmonyOS 当前设置页面查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    title = query_current_settings_page()

    print("\n" + "-" * 55)
    if title is None:
        print("  >>> 当前不在设置App中 <<<")
    else:
        print(f"  当前页面: {title}")
    print("-" * 55)


if __name__ == '__main__':
    main()
