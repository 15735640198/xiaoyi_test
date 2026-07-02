#!/usr/bin/env python3
"""
HarmonyOS 系统语言管理（CLI 调度器）

API: settings_api.query_system_language / add_system_language

用法:
  python language_manager.py --mode query
  python language_manager.py --mode add --language "英语"
"""

import sys
import argparse

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import query_system_language, add_system_language


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 系统语言管理')
    parser.add_argument('--mode', required=True, choices=['query', 'add'],
                        help='query=查询当前语言, add=添加语言')
    parser.add_argument('--language', default=None,
                        help='要添加的语言中文名 (如 "英语", "繁体中文")')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 系统语言管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    print("\n" + "-" * 55)
    if args.mode == 'query':
        lang = query_system_language()
        if lang:
            print(f"  >>> 当前系统语言: {lang} <<<")
        else:
            print("  >>> 未找到语言设置入口 <<<")
    elif args.mode == 'add':
        if not args.language:
            print("  >>> 错误: 需要指定 --language 参数 <<<")
        else:
            success, message = add_system_language(args.language)
            if success:
                print(f"  >>> {message} <<<")
                print("  注意: 添加后需手动在语言列表中拖拽排序来设为默认")
            else:
                print(f"  >>> 失败: {message} <<<")
    print("-" * 55)


if __name__ == '__main__':
    main()
