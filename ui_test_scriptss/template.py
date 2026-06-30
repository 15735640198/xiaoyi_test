#!/usr/bin/env python3
"""
HarmonyOS 设置操作脚本模板（CLI 调度器）

脚本只负责: 命令行参数解析 → 调用 settings_api → 输出结果
业务逻辑全在 settings_api.py 中

使用方法:
  1. 复制本文件，改名为 query_<feature>_state.py 或 <feature>_manager.py
  2. 在 settings_api.py 中添加对应的 API 函数（封装导航路径/形态等参数）
  3. 本文件只改 import 和 main 中的调用

用法:
  python template.py --mode query
  python template.py --mode on
  python template.py --mode off
"""

import argparse
from hdc_utils import find_hdc, check_device
from settings_api import query_setting, toggle_setting

# CONFIG — 与 settings_api 中的参数保持一致
ENTRY = '关怀和无障碍'
TARGET = '放大手势'
FORM = 'text_value'
SCROLL = 4
TEXT_ON = '已开启'
TEXT_OFF = '已关闭'
THIRD_LEVEL_TOGGLE = '放大手势'


def main():
    parser = argparse.ArgumentParser(description=f'HarmonyOS {TARGET} 管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query'],
                        help='on(打开) / off(关闭) / query(查询)')
    args = parser.parse_args()

    print("=" * 55)
    print(f"  HarmonyOS {TARGET} 管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_setting(ENTRY, TARGET, FORM, SCROLL, TEXT_ON, TEXT_OFF)
        status_str = {'on': '已开启', 'off': '已关闭'}.get(status, str(status))
        print(f"\n  >>> {TARGET}: {status_str} <<<")
    else:
        desired = args.mode
        success, new_status = toggle_setting(
            ENTRY, TARGET, FORM, desired, SCROLL,
            THIRD_LEVEL_TOGGLE, TEXT_ON, TEXT_OFF)
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> {TARGET} 已{'开启' if desired == 'on' else '关闭'} <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")


if __name__ == '__main__':
    main()
