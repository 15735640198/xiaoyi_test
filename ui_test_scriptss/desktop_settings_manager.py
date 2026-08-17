#!/usr/bin/env python3
"""
HarmonyOS 桌面设置脚本（CLI 调度器）

API: settings_api.query_desktop_setting(item)
     settings_api.set_desktop_setting(item, desired)
     settings_api.set_desktop_layout(layout_name)

用法:
  python desktop_settings_manager.py                     # 查询全部
  python desktop_settings_manager.py --item swipe_down   # 查询单项
  python desktop_settings_manager.py --item swipe_down --action on    # 开启
  python desktop_settings_manager.py --item swipe_down --action off   # 关闭
  python desktop_settings_manager.py --set-layout 标准   # 设置桌面布局
"""

import argparse
from hdc_utils import find_hdc, check_device
from settings_api import query_desktop_setting, set_desktop_setting, set_desktop_layout

ITEMS = [
    ('swipe_down',  '桌面下滑', '桌面下滑打开小艺搜索'),
    ('swipe_up',    '桌面上滑', '桌面上滑打开应用中心'),
    ('layout',      '桌面布局', '桌面布局模式（标准/紧凑）'),
    ('auto_align',  '自动对齐', '删除应用后自动补齐空位'),
    ('lock_layout', '锁定布局', '开启后桌面元素无法移动或移除'),
]
# set_desktop_setting 仅支持 toggle 项（layout 用 set_desktop_layout 单独处理）
TOGGLE_ITEMS = [k for k, _, _ in ITEMS if k != 'layout']


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 桌面设置')
    parser.add_argument('--item', default=None,
                        choices=[k for k, _, _ in ITEMS],
                        help='功能项 (不指定则查询全部)')
    parser.add_argument('--action', default=None,
                        choices=['on', 'off'],
                        help='开关操作: on(开启) / off(关闭)，仅对 toggle 项有效')
    parser.add_argument('--set-layout', default=None,
                        choices=['标准', '紧凑'],
                        help='设置桌面布局模式')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 桌面设置")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}\n")

    # 设置布局模式
    if args.set_layout:
        success, new_layout = set_desktop_layout(args.set_layout)
        if success:
            print(f"  >>> 桌面布局已设置为: {new_layout} <<<\n")
        else:
            print(f"  >>> 设置失败，当前布局: {new_layout} <<<\n")
        return

    # 设置开关模式
    if args.action:
        if args.item not in TOGGLE_ITEMS:
            print(f"  >>> {args.item} 不支持开关操作 <<<\n")
            return
        success, new_status = set_desktop_setting(args.item, args.action)
        label = dict((k, v) for k, v, _ in ITEMS)[args.item]
        if success:
            print(f"  >>> {label} 已{'开启' if args.action == 'on' else '关闭'} <<<\n")
        else:
            print(f"  >>> 操作失败，当前状态: {new_status} <<<\n")
        return

    # 查询模式
    items = [row for row in ITEMS if row[0] == args.item] if args.item else ITEMS

    for key, label, desc in items:
        val = query_desktop_setting(key)
        print(f"  {label} ({desc}): {val}")

    print()


if __name__ == '__main__':
    main()
