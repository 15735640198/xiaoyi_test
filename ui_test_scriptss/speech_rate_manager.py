#!/usr/bin/env python3
"""
HarmonyOS 朗读速度管理脚本（CLI 调度器）

API: settings_api.query_speech_rate / set_speech_rate

用法:
  python speech_rate_manager.py --mode query
  python speech_rate_manager.py --mode set --value 50
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_speech_rate, set_speech_rate


def main():
    print("=" * 55)
    print("  HarmonyOS 朗读速度管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 朗读速度管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    parser.add_argument('--value', type=int, default=None,
                        help='朗读速度值 (0-100)，--mode set 时必填')
    args = parser.parse_args()

    if args.mode == 'set' and args.value is None:
        parser.error('--mode set 需要 --value 参数')
    if args.value is not None and not 0 <= args.value <= 100:
        parser.error('--value 范围: 0-100')

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_speech_rate()
        print("\n" + "-" * 55)
        if status is None:
            print("  >>> 未找到「朗读速度」入口 <<<")
        elif status == 'unknown':
            print("  >>> 朗读速度: 状态未知 <<<")
        else:
            print(f"  >>> 朗读速度: {status} <<<")
        print("-" * 55)
    else:
        success, new_val = set_speech_rate(args.value)
        print("\n" + "-" * 55)
        if success:
            print(f"  >>> 朗读速度设置成功: {new_val} <<<")
        else:
            print(f"  >>> 朗读速度设置失败: {new_val} <<<")
        print("-" * 55)


if __name__ == '__main__':
    main()
