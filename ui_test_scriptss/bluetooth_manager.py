#!/usr/bin/env python3
"""
HarmonyOS 蓝牙管理脚本（CLI 调度器）

API: settings_api.query_bluetooth / set_bluetooth
     settings_api.query_bluetooth_device
     settings_api.connect_bluetooth / disconnect_bluetooth

用法:
  python bluetooth_manager.py --mode on
  python bluetooth_manager.py --mode off
  python bluetooth_manager.py --mode query
  python bluetooth_manager.py --mode query      --Bluetooth_name "设备名"
  python bluetooth_manager.py --mode connect    --Bluetooth_name "设备名"
  python bluetooth_manager.py --mode disconnect --Bluetooth_name "设备名"
"""

import argparse
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_bluetooth, set_bluetooth,
    query_bluetooth_device,
    connect_bluetooth, disconnect_bluetooth,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 蓝牙管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query', 'connect', 'disconnect'],
                        help='on(打开) / off(关闭) / query(查询) / connect(连接) / disconnect(断开)')
    parser.add_argument('--Bluetooth_name', default=None,
                        help='蓝牙设备名称 (connect/disconnect/查询设备状态时需要)')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 蓝牙管理")
    print(f"  模式: {args.mode}" + (f"  设备: {args.Bluetooth_name}" if args.Bluetooth_name else ""))
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode in ('on', 'off'):
        success, new_status = set_bluetooth(args.mode)
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> 蓝牙已{'开启' if args.mode == 'on' else '关闭'} <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")

    elif args.mode == 'query':
        bt_status = query_bluetooth()
        if bt_status == 'off':
            print("\n  >>> 蓝牙: 已关闭 <<<")
            return
        if not args.Bluetooth_name:
            status_str = {'on': '已开启'}.get(bt_status, str(bt_status))
            print(f"\n  >>> 蓝牙: {status_str} <<<")
            return
        status = query_bluetooth_device(args.Bluetooth_name)
        print(f"\n  >>> '{args.Bluetooth_name}': {status} <<<")

    elif args.mode == 'connect':
        if not args.Bluetooth_name:
            print("\n  >>> connect 模式需要 --Bluetooth_name <<<")
            return
        success, status = connect_bluetooth(args.Bluetooth_name)
        if success:
            print(f"\n  >>> '{args.Bluetooth_name}' 连接成功 <<<")
        else:
            print(f"\n  >>> '{args.Bluetooth_name}' 连接失败 ({status}) <<<")

    elif args.mode == 'disconnect':
        if not args.Bluetooth_name:
            print("\n  >>> disconnect 模式需要 --Bluetooth_name <<<")
            return
        success, status = disconnect_bluetooth(args.Bluetooth_name)
        if success:
            print(f"\n  >>> '{args.Bluetooth_name}' 断开成功 <<<")
        else:
            print(f"\n  >>> '{args.Bluetooth_name}' 断开失败 ({status}) <<<")


if __name__ == '__main__':
    main()
