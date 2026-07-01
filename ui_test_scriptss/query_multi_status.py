#!/usr/bin/env python3
"""
HarmonyOS 综合状态查询脚本（CLI 调度器）

查询: 省电模式、自动亮度、自动旋转保持、电子书模式、三键导航、手势导航

用法:
  python query_multi_status.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from hdc_utils import find_hdc, check_device
from settings_api import (
    query_power_saving,
    query_auto_brightness,
    query_ebook_mode,
    query_navigation_mode,
)


def fmt_on_off(status, label):
    """格式化 on/off 状态输出"""
    if status == 'on':
        return f"  >>> {label}: 已开启 (ON) <<<"
    elif status == 'off':
        return f"  >>> {label}: 已关闭 (OFF) <<<"
    elif status is None:
        return f"  >>> {label}: 未找到入口 <<<"
    elif status and status.startswith('unknown'):
        return f"  >>> {label}: 状态未知 {status} <<<"
    else:
        return f"  >>> {label}: {status} <<<"


def main():
    print("=" * 55)
    print("  HarmonyOS 综合状态查询")
    print("=" * 55)

    find_hdc()
    device = check_device()
    print(f"  设备: {device}")

    results = []

    # 1. 省电模式
    print("\n[1/5] 查询省电模式...")
    status = query_power_saving()
    results.append(fmt_on_off(status, '省电模式'))

    # 2. 自动亮度
    print("[2/5] 查询自动调节亮度...")
    status = query_auto_brightness()
    results.append(fmt_on_off(status, '自动调节亮度'))

    # 3. 自动旋转保持 (仅在控制中心，不在设置 App)
    results.append("  >>> 自动旋转保持: 不适用 (仅控制中心可设置，设置 App 无此入口) <<<")

    # 4. 电子书模式
    print("[3/5] 查询电子书模式...")
    status = query_ebook_mode()
    results.append(fmt_on_off(status, '电子书模式'))

    # 5. 系统导航模式 (三键导航 + 手势导航)
    print("[4/5] 查询系统导航模式...")
    nav_mode = query_navigation_mode()
    if nav_mode == '三键导航':
        results.append("  >>> 三键导航: 已启用 (当前导航方式) <<<")
        results.append("  >>> 手势导航: 未启用 <<<")
    elif nav_mode == '手势导航':
        results.append("  >>> 三键导航: 未启用 <<<")
        results.append("  >>> 手势导航: 已启用 (当前导航方式) <<<")
    elif nav_mode is None:
        results.append("  >>> 三键导航: 未找到入口 <<<")
        results.append("  >>> 手势导航: 未找到入口 <<<")
    else:
        results.append(f"  >>> 三键导航: 状态未知 <<<")
        results.append(f"  >>> 手势导航: 状态未知 <<<")

    print("[5/5] 查询完成")
    print("\n" + "-" * 55)
    for line in results:
        print(line)
    print("-" * 55)


if __name__ == '__main__':
    main()
