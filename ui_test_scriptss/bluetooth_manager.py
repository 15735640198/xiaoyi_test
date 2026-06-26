#!/usr/bin/env python3
"""
HarmonyOS 蓝牙设备管理脚本

支持三种模式:
  connect     — 连接指定蓝牙设备
  disconnect  — 断开指定蓝牙设备
  query       — 查询指定蓝牙设备的连接状态

用法:
  python bluetooth_manager.py --mode connect    --Bluetooth_name "3A华为智慧屏 SE65"
  python bluetooth_manager.py --mode disconnect --Bluetooth_name "3A华为智慧屏 SE65"
  python bluetooth_manager.py --mode query      --Bluetooth_name "3A华为智慧屏 SE65"

导航路径: 设置 > 星闪和蓝牙 > 已配对设备 / 其他设备
"""

import subprocess
import json
import os
import re
import sys
import time
import tempfile
import argparse

# ── 配置 ──────────────────────────────────────────────
SETTINGS_BUNDLE = 'com.huawei.hmos.settings'
SETTINGS_ABILITY = 'com.huawei.hmos.settings.MainAbility'
TEXT_BT_ENTRY = '星闪和蓝牙'       # 设置主页中蓝牙入口的文本
TEXT_BT_LABEL = '蓝牙'              # 蓝牙开关旁边的标签文本
TEXT_CONNECTED = '已连接'
TEXT_PAIRED_HEADER = '已配对设备'
TEXT_OTHER_HEADER = '其他设备'

NAV_WAIT = 2.5          # 页面跳转等待
DUMP_WAIT = 1.0         # dumpLayout 后等待
OP_TIMEOUT = 30         # 连接/断开操作超时秒数
MAX_SCROLL = 5          # 最多滑动查找次数

# hdc 路径（自动搜索）
HDC_COMMON_PATHS = [
    r'D:\lzs\devecostudio-windows-6.1.1.280\DevEco Studio\sdk',
    os.path.expandvars(r'%LOCALAPPDATA%\Huawei\DevEcoStudio\sdk'),
    r'C:\Program Files\Huawei\DevEco Studio\sdk',
]
# ─────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════
#  通用工具函数
# ══════════════════════════════════════════════════════

_HDC = None


def find_hdc():
    """查找 hdc 可执行文件"""
    global _HDC
    try:
        r = subprocess.run(['hdc', 'version'], capture_output=True, text=True, timeout=5)
        if 'Ver:' in r.stdout:
            _HDC = 'hdc'
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    for sdk_dir in HDC_COMMON_PATHS:
        if not os.path.isdir(sdk_dir):
            continue
        for root, dirs, files in os.walk(sdk_dir):
            if 'hdc.exe' in files:
                _HDC = os.path.join(root, 'hdc.exe')
                return
            depth = root.replace(sdk_dir, '').count(os.sep)
            if depth > 4:
                dirs.clear()
    _HDC = 'hdc'  # fallback


def run_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, encoding='utf-8', errors='replace')
        return (r.stdout or '') + (r.stderr or '')
    except FileNotFoundError:
        print(f"[ERROR] 命令不存在: {cmd[0]}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        return ''


def hdc_shell(*args, timeout=30):
    return run_cmd([_HDC, 'shell', *list(args)], timeout)


def dump_layout():
    """获取当前页面控件树 JSON"""
    output = hdc_shell('uitest', 'dumpLayout')
    time.sleep(DUMP_WAIT)
    m = re.search(r'saved to:\s*(/\S+\.json)', output)
    remote = m.group(1) if m else '/data/local/tmp/layout.json'
    local = os.path.join(tempfile.gettempdir(), 'hm_layout.json')
    run_cmd([_HDC, 'file', 'recv', remote, local], timeout=15)
    with open(local, 'r', encoding='utf-8') as f:
        return json.load(f)


def attr(comp, key, default=''):
    """从 attributes 字典读取属性"""
    a = comp.get('attributes')
    return a.get(key, default) if a else comp.get(key, default)


def get_text(comp):
    return attr(comp, 'text', '') or attr(comp, 'description', '') or ''


def find_components(node, predicate, results=None):
    if results is None:
        results = []
    if isinstance(node, dict):
        if predicate(node):
            results.append(node)
        for c in node.get('children', []):
            find_components(c, predicate, results)
    elif isinstance(node, list):
        for item in node:
            find_components(item, predicate, results)
    return results


def find_by_text(node, text):
    return find_components(node, lambda c: text in get_text(c))


def find_by_exact_text(node, text):
    """精确匹配文本（用于查找按钮，避免"配对"匹配到"已配对设备"）"""
    return find_components(node, lambda c: get_text(c).strip() == text)


def find_button(node, text):
    """
    查找按钮文本：子串匹配但排除含"设备"的长文本
    例如 find_button(layout, '配对') 能匹配 "配对" 但不会匹配 "已配对设备"
    """
    return find_components(node, lambda c: (
        text in get_text(c) and
        '设备' not in get_text(c) and
        len(get_text(c).strip()) <= 5
    ))


def find_toggles(node):
    return find_components(node,
        lambda c: attr(c, 'type', '').lower() in ('toggle', 'switch'))


def parse_bounds(bounds):
    if isinstance(bounds, str):
        nums = re.findall(r'\d+', bounds)
        if len(nums) >= 4:
            return ((int(nums[0]) + int(nums[2])) // 2,
                    (int(nums[1]) + int(nums[3])) // 2)
    elif isinstance(bounds, list) and len(bounds) == 4:
        return ((bounds[0] + bounds[2]) // 2, (bounds[1] + bounds[3]) // 2)
    return None


def distance(p1, p2):
    if not p1 or not p2:
        return float('inf')
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def click_at(x, y, wait=NAV_WAIT):
    hdc_shell('uitest', 'uiInput', 'click', str(x), str(y))
    time.sleep(wait)


def click_by_text(layout, text, wait=NAV_WAIT):
    comps = find_by_text(layout, text)
    if not comps:
        return False
    center = parse_bounds(attr(comps[0], 'bounds'))
    if not center:
        return False
    click_at(center[0], center[1], wait)
    return True


def go_back(wait=1.5):
    """返回键"""
    hdc_shell('uitest', 'uiInput', 'keyEvent', 'Back')
    time.sleep(wait)


def swipe_up(distance=1200, wait=1.5):
    hdc_shell('uitest', 'uiInput', 'swipe', '660', '1900', '660', str(1900 - distance))
    time.sleep(wait)


# ══════════════════════════════════════════════════════
#  蓝牙专用函数
# ══════════════════════════════════════════════════════

def open_bluetooth_settings():
    """启动设置应用并导航到「星闪和蓝牙」页面"""
    # 启动设置
    hdc_shell('aa', 'start', '-a', SETTINGS_ABILITY, '-b', SETTINGS_BUNDLE)
    time.sleep(3)

    # 检查是否已经在蓝牙页面（已有"已配对设备"或"其他设备"文本）
    layout = dump_layout()
    if find_by_text(layout, TEXT_PAIRED_HEADER) or find_by_text(layout, TEXT_OTHER_HEADER):
        print("  已在蓝牙设置页面")
    else:
        # 需要从设置主页点击进入
        if not click_by_text(layout, TEXT_BT_ENTRY):
            for _ in range(3):
                swipe_up()
                layout = dump_layout()
                if click_by_text(layout, TEXT_BT_ENTRY):
                    break
            else:
                print("[FAIL] 未找到「星闪和蓝牙」入口")
                return False

    # 等待设备列表加载（等待"已配对设备"或"其他设备"出现）
    print("  等待设备列表加载...")
    for i in range(10):
        layout = dump_layout()
        if find_by_text(layout, TEXT_PAIRED_HEADER) or find_by_text(layout, TEXT_OTHER_HEADER):
            break
        time.sleep(1)
    # 额外等待设备扫描完成，确保设备名称已填充
    print("  等待设备扫描完成...")
    time.sleep(5)
    return True


def is_bluetooth_enabled(layout):
    """检查蓝牙开关是否已开启"""
    toggles = find_toggles(layout)
    bt_label_comps = find_by_text(layout, TEXT_BT_LABEL)

    if not bt_label_comps or not toggles:
        return False

    # 找到「蓝牙」标签旁边的 Toggle
    label_center = parse_bounds(attr(bt_label_comps[0], 'bounds'))
    if not label_center:
        return False

    nearest = min(toggles,
        key=lambda t: distance(label_center, parse_bounds(attr(t, 'bounds'))))
    val = attr(nearest, 'checked', '')
    return val == 'true' or val is True


def ensure_bluetooth_on(layout):
    """确保蓝牙已开启"""
    if is_bluetooth_enabled(layout):
        return True

    print("  蓝牙未开启，正在开启...")
    toggles = find_toggles(layout)
    bt_label_comps = find_by_text(layout, TEXT_BT_LABEL)
    if bt_label_comps and toggles:
        label_center = parse_bounds(attr(bt_label_comps[0], 'bounds'))
        nearest = min(toggles,
            key=lambda t: distance(label_center, parse_bounds(attr(t, 'bounds'))))
        center = parse_bounds(attr(nearest, 'bounds'))
        if center:
            click_at(center[0], center[1])
            time.sleep(3)
            return True
    return False


def find_device_in_layout(layout, device_name):
    """
    在当前布局中查找设备
    返回设备名称所在的组件，或 None
    """
    comps = find_by_text(layout, device_name)
    if not comps:
        return None
    # 排除标题/header（如"已配对设备"包含设备名片段的情况）
    for c in comps:
        t = get_text(c)
        if t == device_name or (device_name in t and '设备' not in t):
            return c
    return comps[0]


def get_device_status(layout, device_name):
    """
    获取设备连接状态
    返回: 'connected' | 'disconnected' | None
    """
    device_comp = find_device_in_layout(layout, device_name)
    if not device_comp:
        return None

    device_center = parse_bounds(attr(device_comp, 'bounds'))
    if not device_center:
        return None

    # 查找附近的"已连接"文本
    connected_comps = find_by_text(layout, TEXT_CONNECTED)
    for comp in connected_comps:
        comp_center = parse_bounds(attr(comp, 'bounds'))
        if not comp_center:
            continue
        # 判断是否在同一行附近（y 距离小，x 距离不大）
        dy = abs(comp_center[1] - device_center[1])
        dx = abs(comp_center[0] - device_center[0])
        if dy < 80 and dx < 1000:
            return 'connected'

    return 'disconnected'


def scroll_and_find_device(device_name):
    """
    滑动查找设备
    返回找到设备时的 layout，或 None
    """
    for i in range(MAX_SCROLL + 1):
        layout = dump_layout()
        found = find_device_in_layout(layout, device_name)
        if found:
            print(f"  找到设备 '{device_name}'")
            return layout
        if i < MAX_SCROLL:
            print(f"  当前页面未找到，滑动查找... ({i+1}/{MAX_SCROLL})")
            swipe_up(distance=800, wait=2.5)
            time.sleep(2)  # 滑动后等待列表刷新
    return None


def click_device(layout, device_name):
    """
    点击指定设备
    查找设备名文本后，向上找最近的可点击父级组件，点击其中心
    （设备名 Text 通常 clickable=false，真正可点击的是父级 Row）
    """
    comp = find_device_in_layout(layout, device_name)
    if not comp:
        return False

    # 如果组件本身不可点击，尝试在控件树中找最近的可点击祖先
    # 由于 find_components 返回的节点没有父指针，这里用坐标范围匹配：
    # 找所有 clickable=true 且 bounds 包含设备名中心点的组件
    text_center = parse_bounds(attr(comp, 'bounds'))
    if not text_center:
        return False

    clickables = find_components(layout, lambda c: attr(c, 'clickable') == 'true')
    best = None
    best_area = float('inf')
    for c in clickables:
        cb = parse_bounds(attr(c, 'bounds'))
        if not cb:
            continue
        # 检查设备名中心是否在可点击组件范围内
        # cb = (cx, cy), 但我们需要完整的 bounds 来判断包含关系
        raw_bounds = attr(c, 'bounds', '')
        if isinstance(raw_bounds, str):
            nums = re.findall(r'\d+', raw_bounds)
            if len(nums) >= 4:
                left, top, right, bottom = int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3])
                if left <= text_center[0] <= right and top <= text_center[1] <= bottom:
                    area = (right - left) * (bottom - top)
                    # 选面积最小的可点击组件（最精确的）
                    if area < best_area:
                        best_area = area
                        best = cb

    target = best if best else text_center
    print(f"  -> 点击设备 '{device_name}' at ({target[0]}, {target[1]})")
    click_at(target[0], target[1], wait=1.0)
    return True


def wait_for_status(device_name, target_status, timeout=OP_TIMEOUT):
    """
    等待设备状态变化
    target_status: 'connected' 或 'disconnected'
    轮询期间自动处理弹窗（配对确认、配对结果通知等）
    每种按钮只点击一次，避免重复点击同一个弹窗
    """
    clicked_buttons = set()
    elapsed = 0
    while elapsed < timeout:
        time.sleep(2)
        elapsed += 2
        layout = dump_layout()

        # 处理可能出现的弹窗（每种只点一次）
        for btn_text in ['配对', '确定', '知道了']:
            if btn_text in clicked_buttons:
                continue
            comps = find_button(layout, btn_text)
            if comps:
                center = parse_bounds(attr(comps[0], 'bounds'))
                if center:
                    print(f"  -> 轮询中检测到弹窗，点击「{btn_text}」")
                    click_at(center[0], center[1], wait=2.0)
                    clicked_buttons.add(btn_text)
                    time.sleep(1)
                    break

        # 检查设备状态
        layout = dump_layout()
        status = get_device_status(layout, device_name)
        if status == target_status:
            return True
    return False


def dismiss_dialog_if_any(preferred_buttons=None):
    """
    检测并处理弹窗
    preferred_buttons: 优先查找的按钮文本列表，按优先级排列
    返回点击的按钮文本，或 None
    """
    if preferred_buttons is None:
        preferred_buttons = ['确定', '取消', '断开', '知道了']
    layout = dump_layout()
    for btn_text in preferred_buttons:
        comps = find_button(layout, btn_text)
        if comps:
            center = parse_bounds(attr(comps[0], 'bounds'))
            if center:
                print(f"  -> 检测到弹窗，点击「{btn_text}」")
                click_at(center[0], center[1], wait=1.0)
                return btn_text
    return None


def handle_pairing_dialog(timeout=10):
    """
    处理配对弹窗: 查找并点击「配对」按钮
    返回 True 如果点了配对，False 如果没检测到弹窗
    """
    print(f"  等待配对弹窗（超时 {timeout}s）...")
    elapsed = 0
    while elapsed < timeout:
        time.sleep(1)
        elapsed += 1
        layout = dump_layout()
        # 优先找「配对」按钮（精确匹配，避免匹配到"已配对设备"）
        for btn_text in ['配对', '确定']:
            comps = find_button(layout, btn_text)
            if comps:
                center = parse_bounds(attr(comps[0], 'bounds'))
                if center:
                    print(f"  -> 检测到配对弹窗，点击「{btn_text}」")
                    click_at(center[0], center[1], wait=1.0)
                    return True
    print("  未检测到配对弹窗（可能是已配对设备，直接连接中）")
    return False


# ══════════════════════════════════════════════════════
#  三种操作模式
# ══════════════════════════════════════════════════════

def query_mode(device_name):
    """查询模式: 查询设备连接状态"""
    print("\n[QUERY] 查询蓝牙设备状态")
    print(f"  设备名称: {device_name}")

    # 导航到蓝牙页面
    if not open_bluetooth_settings():
        return False

    # 检查蓝牙开关
    layout = dump_layout()
    if not is_bluetooth_enabled(layout):
        print(f"\n  >>> 蓝牙未开启，设备 '{device_name}' 未连接 <<<")
        return True

    # 查找设备
    layout = scroll_and_find_device(device_name)
    if not layout:
        print(f"\n  >>> 未找到设备 '{device_name}' <<<")
        print("  可能原因: 设备未配对且不在附近、设备名称不匹配")
        return False

    # 获取状态
    status = get_device_status(layout, device_name)
    print("\n" + "-" * 50)
    if status == 'connected':
        print(f"  >>> 设备 '{device_name}': 已连接 <<<")
    elif status == 'disconnected':
        print(f"  >>> 设备 '{device_name}': 未连接 <<<")
    else:
        print(f"  >>> 设备 '{device_name}': 状态未知 <<<")
    print("-" * 50)
    return True


def connect_mode(device_name):
    """连接模式: 连接指定蓝牙设备"""
    print("\n[CONNECT] 连接蓝牙设备")
    print(f"  设备名称: {device_name}")

    # 导航到蓝牙页面
    if not open_bluetooth_settings():
        return False

    # 确保蓝牙已开启
    layout = dump_layout()
    if not ensure_bluetooth_on(layout):
        print("[FAIL] 无法开启蓝牙")
        return False
    layout = dump_layout()

    # 查找设备
    layout = scroll_and_find_device(device_name)
    if not layout:
        print(f"[FAIL] 未找到设备 '{device_name}'")
        print("  可能原因: 设备未配对且不在附近、设备名称不匹配")
        return False

    # 检查当前状态
    status = get_device_status(layout, device_name)
    if status == 'connected':
        print(f"  设备 '{device_name}' 已处于连接状态")
        print("\n  >>> 连接成功（已连接）<<<")
        return True

    # 点击设备发起连接
    print(f"  设备当前状态: {status}，正在发起连接...")
    click_device(layout, device_name)

    # 等待并处理配对弹窗（新设备配对时会弹出「配对」按钮）
    handle_pairing_dialog(timeout=10)

    # 等待连接结果
    print(f"  等待连接完成（超时 {OP_TIMEOUT}s）...")
    if wait_for_status(device_name, 'connected', OP_TIMEOUT):
        print(f"\n  >>> 连接成功 <<<")
        return True

    # 检查是否有错误弹窗（如配对失败）
    dialog = dismiss_dialog_if_any(preferred_buttons=['确定', '知道了'])
    if dialog:
        print(f"\n  >>> 连接失败: 出现弹窗「{dialog}」<<<")
    else:
        # 最后再检查一次状态
        layout = dump_layout()
        status = get_device_status(layout, device_name)
        if status == 'connected':
            print(f"\n  >>> 连接成功 <<<")
            return True
        print(f"\n  >>> 连接超时，当前状态: {status or '未知'} <<<")
    return False


def disconnect_mode(device_name):
    """断开模式: 断开指定蓝牙设备"""
    print("\n[DISCONNECT] 断开蓝牙设备")
    print(f"  设备名称: {device_name}")

    # 导航到蓝牙页面
    if not open_bluetooth_settings():
        return False

    # 检查蓝牙开关
    layout = dump_layout()
    if not is_bluetooth_enabled(layout):
        print(f"  蓝牙未开启，设备 '{device_name}' 自然未连接")
        print("\n  >>> 断开成功（蓝牙已关闭）<<<")
        return True

    # 查找设备
    layout = scroll_and_find_device(device_name)
    if not layout:
        print(f"[FAIL] 未找到设备 '{device_name}'")
        return False

    # 检查当前状态
    status = get_device_status(layout, device_name)
    if status == 'disconnected':
        print(f"  设备 '{device_name}' 已处于断开状态")
        print("\n  >>> 断开成功（已断开）<<<")
        return True

    if status != 'connected':
        print(f"  设备状态未知，尝试点击设备...")
    else:
        print(f"  设备当前已连接，正在断开...")

    # 点击设备发起断开
    click_device(layout, device_name)

    # 检查是否有确认弹窗（断开连接确认）
    time.sleep(1.5)
    dismiss_dialog_if_any(preferred_buttons=['确定', '断开', '知道了'])

    # 等待断开结果
    print(f"  等待断开完成（超时 {OP_TIMEOUT}s）...")
    if wait_for_status(device_name, 'disconnected', OP_TIMEOUT):
        print(f"\n  >>> 断开成功 <<<")
        return True

    # 最后再检查一次
    layout = dump_layout()
    status = get_device_status(layout, device_name)
    if status == 'disconnected':
        print(f"\n  >>> 断开成功 <<<")
        return True
    print(f"\n  >>> 断开超时，当前状态: {status or '未知'} <<<")
    return False


# ══════════════════════════════════════════════════════
#  主函数
# ══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='HarmonyOS 蓝牙设备管理脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python bluetooth_manager.py --mode connect    --Bluetooth_name "3A华为智慧屏 SE65"
  python bluetooth_manager.py --mode disconnect --Bluetooth_name "3A华为智慧屏 SE65"
  python bluetooth_manager.py --mode query      --Bluetooth_name "3A华为智慧屏 SE65"
        """)
    parser.add_argument('--mode', required=True,
                        choices=['connect', 'disconnect', 'query'],
                        help='操作模式: connect(连接) / disconnect(断开) / query(查询)')
    parser.add_argument('--Bluetooth_name', required=True,
                        help='蓝牙设备名称')

    args = parser.parse_args()

    print("=" * 55)
    print("  HarmonyOS 蓝牙设备管理")
    print(f"  模式: {args.mode}  |  设备: {args.Bluetooth_name}")
    print("=" * 55)

    # 查找 hdc
    find_hdc()
    print(f"  hdc: {_HDC}")

    # 检查设备连接
    list_output = run_cmd([_HDC, 'list', 'targets'], timeout=10)
    devices = [d.strip() for d in list_output.strip().splitlines()
               if d.strip() and 'Empty' not in d]
    if not devices:
        print("[ERROR] 未检测到已连接的设备")
        sys.exit(1)
    print(f"  设备: {devices[0]}")

    # 唤醒屏幕
    hdc_shell('uitest', 'uiInput', 'keyEvent', 'Power')
    time.sleep(0.5)
    hdc_shell('uitest', 'uiInput', 'keyEvent', 'Power')
    time.sleep(1)

    # 执行对应模式
    if args.mode == 'connect':
        success = connect_mode(args.Bluetooth_name)
    elif args.mode == 'disconnect':
        success = disconnect_mode(args.Bluetooth_name)
    else:
        success = query_mode(args.Bluetooth_name)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
