#!/usr/bin/env python3
"""
HarmonyOS NFC 与默认付款应用管理脚本（CLI 调度器）

API: settings_api.query_nfc / set_nfc
     settings_api.query_default_payment_app / set_default_payment_app

用法:
  python nfc_manager.py --mode query
  python nfc_manager.py --mode on
  python nfc_manager.py --mode off
  python nfc_manager.py --mode query-app
  python nfc_manager.py --mode set-app --app "华为钱包"
"""

import sys
import argparse
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from hdc_utils import find_hdc, check_device
from settings_api import (
    query_nfc, set_nfc,
    query_default_payment_app, set_default_payment_app,
)


def main():
    parser = argparse.ArgumentParser(description='HarmonyOS NFC 与默认付款应用管理')
    parser.add_argument('--mode', required=True,
                        choices=['on', 'off', 'query', 'query-app', 'set-app'],
                        help='on/off(开关NFC) / query(查询NFC) / query-app(查询付款应用) / set-app(设置付款应用)')
    parser.add_argument('--app', default=None,
                        help='付款应用名称 (mode=set-app 时，如 "华为钱包")')
    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS NFC 与默认付款应用管理")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    if args.mode == 'query':
        status = query_nfc()
        status_str = {'on': '已开启', 'off': '已关闭'}.get(status, str(status))
        print(f"\n  >>> NFC: {status_str} <<<")

    elif args.mode in ('on', 'off'):
        success, new_status = set_nfc(args.mode)
        new_str = {'on': '已开启', 'off': '已关闭'}.get(new_status, str(new_status))
        if success:
            print(f"\n  >>> NFC 已{'开启' if args.mode == 'on' else '关闭'} <<<")
        else:
            print(f"\n  >>> 操作失败，当前状态: {new_str} <<<")

    elif args.mode == 'query-app':
        app = query_default_payment_app()
        if app:
            print(f"\n  >>> 默认付款应用: {app} <<<")
        else:
            print("\n  >>> 查询失败 <<<")

    elif args.mode == 'set-app':
        if not args.app:
            print("\n  >>> set-app 模式需要 --app 参数 <<<")
            return
        success, msg = set_default_payment_app(args.app)
        if success:
            print(f"\n  >>> {msg} <<<")
        else:
            print(f"\n  >>> 设置失败: {msg} <<<")


if __name__ == '__main__':
    main()
