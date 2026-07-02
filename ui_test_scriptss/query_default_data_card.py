#!/usr/bin/env python3
"""
HarmonyOS 默认数据卡查询脚本（CLI 调度器）

API: settings_api.query_default_data_card

用法:
  python query_default_data_card.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import query_default_data_card


def main():
    print("=" * 55)
    print("  HarmonyOS 默认数据卡查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    status = query_default_data_card()

    print("\n" + "-" * 55)
    if status is None:
        print("  >>> 未找到「默认移动数据」入口 <<<")
    elif status == 'unknown':
        print("  >>> 默认数据卡: 状态未知 <<<")
    else:
        print(f"  >>> 默认数据卡: {status} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
