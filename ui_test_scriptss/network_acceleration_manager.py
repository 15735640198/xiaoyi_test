#!/usr/bin/env python3
"""
HarmonyOS 网络加速管理（CLI 调度器）

API: settings_api.query_network_acceleration / set_network_acceleration

用法:
  python network_acceleration_manager.py --mode query
  python network_acceleration_manager.py --mode on
  python network_acceleration_manager.py --mode off
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import query_network_acceleration, set_network_acceleration


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 网络加速管理')
    parser.add_argument('--mode', required=True, choices=['on', 'off', 'query'],
                        help='query=查询, on=开启, off=关闭')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 网络加速管理")
    print("  (允许使用移动数据加速网络)")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    print("\n" + "-" * 55)
    if args.mode == 'query':
        status = query_network_acceleration()
        if status == 'on':
            print("  >>> 网络加速: 已开启 (ON) <<<")
        elif status == 'off':
            print("  >>> 网络加速: 已关闭 (OFF) <<<")
        elif status is None:
            print("  >>> 未找到网络加速入口 <<<")
        else:
            print(f"  >>> 网络加速: 状态未知 {status} <<<")
    else:
        success, new_status = set_network_acceleration(args.mode)
        if success:
            print(f"  >>> 操作成功: 网络加速 → {new_status} <<<")
        else:
            print(f"  >>> 操作失败: 当前状态 {new_status} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
