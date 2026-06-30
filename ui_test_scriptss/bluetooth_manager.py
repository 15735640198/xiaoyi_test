#!/usr/bin/env python3
"""
HarmonyOS 蓝牙设备管理脚本（CLI 调度器）

API: settings_api.query_bluetooth / query_bluetooth_device
     settings_api.connect_bluetooth / disconnect_bluetooth

用法:
  python bluetooth_manager.py --mode query      --Bluetooth_name "设备名"
  python bluetooth_manager.py --mode connect    --Bluetooth_name "设备名"
  python bluetooth_manager.py --mode disconnect --Bluetooth_name "设备名"
"""

import argparse
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_bluetooth, query_bluetooth_device,
    connect_bluetooth, disconnect_bluetooth,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS 蓝牙设备管理')
    parser.add_argument('--mode', required=True,
                        choices=['connect', 'disconnect', 'query'],
                        help='connect(连接) / disconnect(断开) / query(查询)')
    parser.add_argument('--Bluetooth_name', required=True,
                        help='蓝牙设备名称')
    args = parser.parse_args()

    print("=" * 50)
    print("  HarmonyOS 蓝牙设备管理")
    print(f"  模式: {args.mode}  设备: {args.Bluetooth_name}")
    print("=" * 50)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        bt_status = query_bluetooth()
        if bt_status == 'off':
            print("\n  >>> 蓝牙: 已关闭 <<<")
            return
        status = query_bluetooth_device(args.Bluetooth_name)
        print(f"\n  >>> '{args.Bluetooth_name}': {status} <<<")

    elif args.mode == 'connect':
        success, status = connect_bluetooth(args.Bluetooth_name)
        if success:
            print(f"\n  >>> '{args.Bluetooth_name}' 连接成功 <<<")
        else:
            print(f"\n  >>> '{args.Bluetooth_name}' 连接失败 ({status}) <<<")

    elif args.mode == 'disconnect':
        success, status = disconnect_bluetooth(args.Bluetooth_name)
        if success:
            print(f"\n  >>> '{args.Bluetooth_name}' 断开成功 <<<")
        else:
            print(f"\n  >>> '{args.Bluetooth_name}' 断开失败 ({status}) <<<")


if __name__ == '__main__':
    main()
