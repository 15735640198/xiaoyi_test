#!/usr/bin/env python3
"""
HarmonyOS 时区管理脚本（CLI 调度器）

API: settings_api.query_auto_timezone / set_auto_timezone / query_timezone / set_timezone

用法:
  python timezone_manager.py --mode query           # 查询自动时区开关和当前时区
  python timezone_manager.py --mode auto-on         # 打开自动时区
  python timezone_manager.py --mode auto-off        # 关闭自动时区
  python timezone_manager.py --mode set --tz "中国标准时间"  # 设置时区
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_auto_timezone, set_auto_timezone,
    query_timezone, set_timezone,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 时区管理')
    parser.add_argument('--mode', required=True,
                        choices=['query', 'auto-on', 'auto-off', 'set'],
                        help='query(查询) / auto-on(打开自动时区) / auto-off(关闭自动时区) / set(设置时区)')
    parser.add_argument('--tz', default=None,
                        help='时区关键词 (mode=set 时必须，如 "中国标准时间" 或 "GMT+08:00")')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 时区管理")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        auto = query_auto_timezone()
        auto_str = {'on': '已开启', 'off': '已关闭'}.get(auto, str(auto))
        print(f"\n  自动时区: {auto_str}")
        tz = query_timezone()
        if tz:
            print(f"  当前时区: {tz}")
        else:
            print(f"  当前时区: 获取失败")
    elif args.mode == 'auto-on':
        success, new_status = set_auto_timezone('on')
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> 自动时区已开启 <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")
    elif args.mode == 'auto-off':
        success, new_status = set_auto_timezone('off')
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> 自动时区已关闭 <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")
    elif args.mode == 'set':
        if not args.tz:
            print("\n  >>> 错误: mode=set 需要指定 --tz 参数 <<<")
            sys.exit(1)
        success, msg = set_timezone(args.tz)
        if success:
            print(f"\n  >>> {msg} <<<")
        else:
            print(f"\n  >>> 设置失败: {msg} <<<")


if __name__ == '__main__':
    main()
