#!/usr/bin/env python3
"""
HarmonyOS 热点管理脚本（CLI 调度器）

API: settings_api.query_personal_hotspot / set_personal_hotspot
     settings_api.query_hotspot_connected_devices
     settings_api.query_hotspot_ap_band
     settings_api.query_usb_tethering / set_usb_tethering
     settings_api.query_hotspot_config / set_hotspot_name / set_hotspot_password

用法:
  # 热点开关
  python hotspot_config_manager.py --mode query-switch
  python hotspot_config_manager.py --mode on
  python hotspot_config_manager.py --mode off

  # 已连接设备
  python hotspot_config_manager.py --mode query-devices

  # AP 频段
  python hotspot_config_manager.py --mode query-band

  # USB 共享网络
  python hotspot_config_manager.py --mode query-usb
  python hotspot_config_manager.py --mode usb-on
  python hotspot_config_manager.py --mode usb-off

  # 热点配置
  python hotspot_config_manager.py --mode query-config
  python hotspot_config_manager.py --mode set --name MyHotspot
  python hotspot_config_manager.py --mode set --password abc12345
  python hotspot_config_manager.py --mode set --name MyHotspot --password abc12345

注意: 加密方式在 HarmonyOS 中固定为 WPA2-PSK，不可配置。
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_personal_hotspot,
    set_personal_hotspot,
    query_hotspot_connected_devices,
    query_hotspot_ap_band,
    query_usb_tethering,
    set_usb_tethering,
    query_hotspot_config,
    set_hotspot_name,
    set_hotspot_password,
)


def _print_toggle(title, status):
    """打印开关状态"""
    print("\n" + "-" * 55)
    if status is None:
        print(f"  >>> 未找到「{title}」入口 <<<")
    else:
        state = '开启' if status == 'on' else '关闭' if status == 'off' else '未知'
        print(f"  {title}: {state}")
    print("-" * 55)


def _print_value(title, value):
    """打印文本值"""
    print("\n" + "-" * 55)
    if value is None:
        print(f"  >>> 未找到「{title}」入口 <<<")
    else:
        print(f"  {title}: {value}")
    print("-" * 55)


def main():
    print("=" * 55)
    print("  HarmonyOS 热点管理")
    print("=" * 55)

    parser = argparse.ArgumentParser(description='HarmonyOS 热点管理')
    parser.add_argument('--mode', required=True, choices=[
        'query-switch', 'on', 'off',
        'query-devices',
        'query-band',
        'query-usb', 'usb-on', 'usb-off',
        'query-config', 'set',
    ])
    parser.add_argument('--name', default=None, help='热点名称')
    parser.add_argument('--password', default=None, help='热点密码')
    args = parser.parse_args()

    if args.mode == 'set' and not args.name and not args.password:
        parser.error('--mode set 需要至少指定 --name 或 --password')

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    # ── 热点开关 ──
    if args.mode == 'query-switch':
        status = query_personal_hotspot()
        _print_toggle('个人热点', status)

    elif args.mode == 'on':
        success, new_status = set_personal_hotspot('on')
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「个人热点」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭'
            if success:
                print(f"  个人热点: 已开启 ({state})")
            else:
                print(f"  个人热点: 操作失败 (当前: {state})")
        print("-" * 55)

    elif args.mode == 'off':
        success, new_status = set_personal_hotspot('off')
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「个人热点」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭'
            if success:
                print(f"  个人热点: 已关闭 ({state})")
            else:
                print(f"  个人热点: 操作失败 (当前: {state})")
        print("-" * 55)

    # ── 已连接设备 ──
    elif args.mode == 'query-devices':
        value = query_hotspot_connected_devices()
        _print_value('已连接设备', value)

    # ── AP 频段 ──
    elif args.mode == 'query-band':
        value = query_hotspot_ap_band()
        _print_value('AP 频段', value)

    # ── USB 共享网络 ──
    elif args.mode == 'query-usb':
        status = query_usb_tethering()
        _print_toggle('USB 共享网络', status)

    elif args.mode == 'usb-on':
        success, new_status = set_usb_tethering('on')
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「USB 共享网络」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭'
            if success:
                print(f"  USB 共享网络: 已开启 ({state})")
                print("  ⚠ 开启后 USB 调试连接会断开，需重新插拔 USB 恢复")
            else:
                print(f"  USB 共享网络: 操作失败 (当前: {state})")
        print("-" * 55)

    elif args.mode == 'usb-off':
        success, new_status = set_usb_tethering('off')
        print("\n" + "-" * 55)
        if new_status is None:
            print("  >>> 未找到「USB 共享网络」入口 <<<")
        else:
            state = '开启' if new_status == 'on' else '关闭'
            if success:
                print(f"  USB 共享网络: 已关闭 ({state})")
            else:
                print(f"  USB 共享网络: 操作失败 (当前: {state})")
        print("-" * 55)

    # ── 热点配置（名称/密码）──
    elif args.mode == 'query-config':
        result = query_hotspot_config()
        print("\n" + "-" * 55)
        if result is None:
            print("  >>> 未找到「个人热点」入口 <<<")
        else:
            print(f"  热点名称: {result.get('name', '未知')}")
            print(f"  密码:     {result.get('password', '未知')}")
            print(f"  加密方式: {result.get('encryption', '未知')}")
        print("-" * 55)

    elif args.mode == 'set':
        if args.name:
            success, new_name = set_hotspot_name(args.name)
            print("\n" + "-" * 55)
            if success:
                print(f"  热点名称设置成功: {new_name}")
            else:
                print(f"  热点名称设置失败: {new_name}")
            print("-" * 55)

        if args.password:
            success, new_pwd = set_hotspot_password(args.password)
            print("\n" + "-" * 55)
            if success:
                print(f"  热点密码设置成功: {new_pwd}")
            else:
                print(f"  热点密码设置失败: {new_pwd}")
            print("-" * 55)


if __name__ == '__main__':
    main()
