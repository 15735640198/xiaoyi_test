#!/usr/bin/env python3
"""
HarmonyOS 来电铃声管理脚本（CLI 调度器）

API: settings_api.query_ringtone / set_ringtone_default

用法:
  python ringtone_manager.py --mode query
  python ringtone_manager.py --mode set
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import query_ringtone, set_ringtone_default


def main():
    print("=" * 55)
    print("  HarmonyOS 来电铃声管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 来电铃声管理')
    parser.add_argument('--mode', required=True, choices=['query', 'set'])
    args = parser.parse_args()

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        result = query_ringtone()
        print("\n" + "-" * 55)
        if result is None:
            print("  >>> 未找到「来电铃声」入口 <<<")
        else:
            for sim_key, info in result.items():
                label = {'sim1': '卡 1', 'sim2': '卡 2', 'default': '来电铃声'}.get(sim_key, sim_key)
                name = info.get('name', '未知')
                is_default = info.get('is_default', False)
                if name is None:
                    print(f"  {label}: 未找到铃声")
                elif is_default:
                    print(f"  {label}: {name} (已是默认)")
                else:
                    print(f"  {label}: {name} (非默认)")
        print("-" * 55)
    else:
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


if __name__ == '__main__':
    main()
