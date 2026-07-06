#!/usr/bin/env python3
"""
HarmonyOS 日期和时间管理脚本（CLI 调度器）

API: settings_api.query_auto_timezone / set_auto_timezone
     settings_api.query_timezone / set_timezone
     settings_api.query_time_format / set_time_format
     settings_api.query_date / query_time / set_time

用法:
  python timezone_manager.py --mode query              # 查询全部状态
  python timezone_manager.py --mode auto-on            # 打开自动时区
  python timezone_manager.py --mode auto-off           # 关闭自动时区
  python timezone_manager.py --mode set --tz "中国标准时间"      # 设置时区
  python timezone_manager.py --mode set-format --value 24        # 设置24小时制
  python timezone_manager.py --mode set-format --value 12        # 设置12小时制
  python timezone_manager.py --mode set-time --time 15:30        # 设置时间
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_auto_timezone, set_auto_timezone,
    query_timezone, set_timezone,
    query_time_format, set_time_format,
    query_date, query_time, set_time,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 日期和时间管理')
    parser.add_argument('--mode', required=True,
                        choices=['query', 'auto-on', 'auto-off', 'set',
                                 'set-format', 'set-time'],
                        help='query(查询) / auto-on(自动时区开) / auto-off(自动时区关) / '
                             'set(设置时区) / set-format(设置时间制式) / set-time(设置时间)')
    parser.add_argument('--tz', default=None,
                        help='时区关键词 (mode=set 时，如 "中国标准时间")')
    parser.add_argument('--value', default=None,
                        help='时间制式 (mode=set-format 时，24 或 12)')
    parser.add_argument('--time', default=None,
                        help='时间 (mode=set-time 时，格式 HH:MM 如 15:30)')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 日期和时间管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        auto = query_auto_timezone()
        auto_str = {'on': '已开启', 'off': '已关闭'}.get(auto, str(auto))
        print(f"\n  自动时区: {auto_str}")

        fmt = query_time_format()
        print(f"  时间制式: {fmt}")

        tz = query_timezone()
        if tz:
            print(f"  当前时区: {tz}")

        date = query_date()
        if date:
            print(f"  当前日期: {date}")

        tm = query_time()
        if tm:
            print(f"  当前时间: {tm}")

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

    elif args.mode == 'set-format':
        if not args.value:
            print("\n  >>> 错误: mode=set-format 需要指定 --value (24 或 12) <<<")
            sys.exit(1)
        success, new_fmt = set_time_format(args.value)
        if success:
            print(f"\n  >>> 时间制式已设置为: {new_fmt} <<<")
        else:
            print(f"\n  >>> 设置失败，当前: {new_fmt} <<<")

    elif args.mode == 'set-time':
        if not args.time:
            print("\n  >>> 错误: mode=set-time 需要指定 --time (格式 HH:MM) <<<")
            sys.exit(1)
        try:
            parts = args.time.split(':')
            hour, minute = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            print("\n  >>> 错误: 时间格式不正确，应为 HH:MM (如 15:30) <<<")
            sys.exit(1)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            print("\n  >>> 错误: 时间范围不正确 (小时 0-23, 分钟 0-59) <<<")
            sys.exit(1)
        success, msg = set_time(hour, minute)
        if success:
            print(f"\n  >>> {msg} <<<")
        else:
            print(f"\n  >>> 设置失败: {msg} <<<")


if __name__ == '__main__':
    main()
