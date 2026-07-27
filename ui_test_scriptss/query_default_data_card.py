#!/usr/bin/env python3
"""
HarmonyOS 默认数据卡管理脚本（CLI 调度器）

API: settings_api.query_default_data_card / set_default_data_card

用法:
  # 查询
  python query_default_data_card.py --mode query

  # 设置为卡1
  python query_default_data_card.py --mode set --card 1

  # 设置为卡2
  python query_default_data_card.py --mode set --card 2
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_default_data_card, set_default_data_card


def main():
    print("=" * 55)
    print("  HarmonyOS 默认数据卡管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 默认数据卡管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    parser.add_argument('--card', default=None, choices=['1', '2'],
                        help='目标卡号（set 模式必需）')
    args = parser.parse_args()

    if args.mode == 'set' and not args.card:
        parser.error('--mode set 需要 --card 1 或 --card 2')

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_default_data_card()
        print("\n" + "-" * 55)
        if status is None:
            print("  >>> 未找到「默认移动数据」入口 <<<")
        elif status == 'unknown':
            print("  >>> 默认数据卡: 状态未知 <<<")
        else:
            print(f"  默认数据卡: {status}")
        print("-" * 55)
    else:
        success, new_status = set_default_data_card(args.card)
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「默认移动数据」入口 <<<")
        elif success:
            print(f"  默认数据卡: 已切换到 {new_status}")
        else:
            print(f"  默认数据卡: 切换失败 (当前: {new_status})")
        print("-" * 55)


if __name__ == '__main__':
    main()
