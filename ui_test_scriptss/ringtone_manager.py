#!/usr/bin/env python3
"""
HarmonyOS 铃声管理脚本（CLI 调度器）

API: settings_api.query_ringtone / set_ringtone_default
     settings_api.query_message_ringtone
     settings_api.query_notification_ringtone

用法:
  python ringtone_manager.py --mode query              查询来电铃声
  python ringtone_manager.py --mode set                设置来电铃声为默认
  python ringtone_manager.py --mode query-message      查询信息铃声
  python ringtone_manager.py --mode query-notification 查询通知铃声

注: 闹钟铃声不在「设置」中，时钟 App (com.huawei.hmos.clock) 使用自定义渲染，
    uitest 无法捕获其布局，因此不支持查询。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_ringtone,
    set_ringtone_default,
    query_message_ringtone,
    query_notification_ringtone,
)


def _print_call_ringtone(result, title='来电铃声'):
    """打印来电铃声查询/设置结果（支持双卡）"""
    print("\n" + "-" * 55)
    if result is None:
        print(f"  >>> 未找到「{title}」入口 <<<")
    else:
        for sim_key, info in result.items():
            label = {'sim1': '卡 1', 'sim2': '卡 2', 'default': title}.get(sim_key, sim_key)
            name = info.get('name', '未知')
            is_default = info.get('is_default', False)
            if name is None:
                print(f"  {label}: 未找到铃声")
            elif is_default:
                print(f"  {label}: {name} (已是默认)")
            else:
                print(f"  {label}: {name} (非默认)")
    print("-" * 55)


def _print_simple_ringtone(result, title):
    """打印信息/通知铃声查询结果"""
    print("\n" + "-" * 55)
    if result is None:
        print(f"  >>> 未找到「{title}」入口 <<<")
    else:
        name = result.get('name', '未知')
        is_default = result.get('is_default', False)
        if name is None:
            print(f"  {title}: 未找到铃声")
        elif is_default:
            print(f"  {title}: {name} (已是默认)")
        else:
            print(f"  {title}: {name} (非默认)")
    print("-" * 55)


def main():
    print("=" * 55)
    print("  HarmonyOS 铃声管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 铃声管理')
    parser.add_argument('--mode', required=True, choices=[
        'query', 'set',
        'query-message', 'query-notification',
    ])
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        result = query_ringtone()
        _print_call_ringtone(result, '来电铃声')

    elif args.mode == 'set':
        success, results = set_ringtone_default()
        print("\n" + "-" * 55)
        if results is None:
            print("  >>> 未找到「来电铃声」入口 <<<")
        else:
            for sim_key, info in results.items():
                label = {'sim1': '卡 1', 'sim2': '卡 2', 'default': '来电铃声'}.get(sim_key, sim_key)
                name = info.get('name', '未知')
                is_default = info.get('is_default', False)
                if name is None:
                    print(f"  {label}: 设置失败（未找到默认铃声）")
                elif is_default:
                    print(f"  {label}: 已设置为默认 ({name})")
                else:
                    print(f"  {label}: 设置失败 ({name})")
            print(f"\n  总体: {'成功' if success else '部分失败'}")
        print("-" * 55)

    elif args.mode == 'query-message':
        result = query_message_ringtone()
        _print_simple_ringtone(result, '信息铃声')

    elif args.mode == 'query-notification':
        result = query_notification_ringtone()
        _print_simple_ringtone(result, '通知铃声')


if __name__ == '__main__':
    main()
